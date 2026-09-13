---
id: DESIGN-DOMAIN-BUNDLE-EXPORT-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
implemented: true
---

# DomainBundle Export v0.1

Этот документ фиксирует persisted boundary между готовым `DomainAssembly` и физическим bundle на filesystem. Exporter не генерирует и не изменяет semantic world state.

## 1. Public boundary

Каноническая функция v0.1:

```python
export_domain_bundle(
    assembly: DomainAssembly,
    output_dir: Path,
) -> ExportedDomainBundle
```

Exporter получает только `DomainAssembly` и target path. Он не принимает `DomainSpec`, `GenerationPlan`, `DomainCandidate`, RNG или renderer context.

`ExportedDomainBundle` является runtime result и содержит как минимум:

```python
root: Path
manifest: BundleManifest
```

## 2. Canonical bundle layout

```text
<output_dir>/
  domain.json
  manifest.json
  fields/
    elevation.npy
    water_depth.npy
    moisture.npy
    vegetation_density.npy
```

`preview/` и `debug/` не создаются exporter-ом v0.1. Они остаются optional non-canonical downstream artifacts.

Имя директории `output` не является частью contract. Target path всегда задаётся caller-ом.

## 3. Input request location is external

Exporter не знает и не хранит input request. В будущем CLI получает input path и output path как параметры, например:

```text
domain-generator generate request.json --output ./generated/map-01
```

Обязательная repository directory `input/` не является частью Core contract. GitHub Actions adapter может использовать собственную convention вроде `input/requests/`, но это orchestration policy outside Core.

## 4. Platform independence

Filesystem code использует `pathlib.Path`. Export semantics должны работать на поддерживаемых Python environments, включая Windows и POSIX systems, при установленных package dependencies.

Persisted paths внутри `DomainData` остаются relative POSIX-style paths (`fields/elevation.npy` и т. п.), поэтому bundle переносим между Windows и Linux.

## 5. Pre-write validation

До создания visible final bundle exporter обязан проверить:

```text
DomainData.fields.keys() == DomainAssembly.field_payloads.keys()
```

Для каждого field:

- descriptor path валиден и relative;
- payload является NumPy ndarray;
- exact shape совпадает с descriptor.shape;
- exact dtype совпадает с descriptor.dtype;
- duplicate normalized paths отсутствуют;
- field path не конфликтует с `domain.json` или `manifest.json`.

Implicit cast, resize, missing-field synthesis или silent repair запрещены.

## 6. domain.json serialization

`domain.json` сериализуется из `assembly.data` через Pydantic JSON-mode representation с aliases:

```python
assembly.data.model_dump(
    mode="json",
    by_alias=True,
    exclude_none=False,
)
```

Физический JSON:

- UTF-8;
- deterministic key ordering (`sort_keys=True`);
- `allow_nan=False`;
- human-readable `indent=2`;
- final newline.

`by_alias=True` обязателен, чтобы serialized contract использовал canonical aliases, например `RiverSegment` keys `from` и `to`.

## 7. Raster persistence

Каждый canonical raster записывается по `FieldDescriptor.path` через NumPy `.npy` format:

```python
numpy.save(path, payload, allow_pickle=False)
```

Exporter не хардкодит вторую независимую таблицу field paths и не изменяет arrays.

Canonical Core 0.1 rasters:

```text
elevation             float32 m
water_depth           float32 m
moisture              float32 normalized
vegetation_density    float32 normalized
```

## 8. BundleManifest v0.1

Exporter создаёт отдельный persisted typed contract `BundleManifest`.

Минимальная семантика:

```text
bundle_version: "0.1"
domain_data_version: "0.1"
domain_id: <DomainData.identity.id>
canonical_files:
  - path
    kind
    sha256
    size_bytes
    field_id?    # только для field payload
```

Canonical files в manifest:

- `domain.json`;
- все canonical field payload files.

`manifest.json` не включает hash самого себя, чтобы избежать рекурсивной зависимости.

SHA-256 формат:

```text
sha256:<lowercase-hex>
```

Manifest получает собственный generated JSON Schema snapshot для v0.1.

## 9. Manifest is transport integrity, not world identity

Hashes persisted files проверяют integrity конкретного bundle, но не заменяют semantic provenance внутри `DomainData`:

- spec fingerprint;
- plan fingerprint;
- generation config fingerprint;
- generator version;
- RNG version;
- accepted attempt index.

Semantic identity мира остаётся в `DomainData`.

## 10. Path safety

Exporter отклоняет:

- absolute persisted paths;
- `..` traversal;
- backslash-based persisted contract paths;
- duplicate normalized paths;
- collisions с reserved bundle files;
- попытку записать payload за пределами temporary bundle root.

Filesystem target `output_dir` может быть Windows или POSIX path; internal descriptor paths интерпретируются как relative POSIX paths внутри bundle.

## 11. Existing target semantics

v0.1 не поддерживает overwrite/force.

Если `output_dir` уже существует, exporter завершает работу с `DomainBundleExportError` до записи final bundle.

Atomic replacement существующего directory tree намеренно вынесен за scope v0.1.

## 12. Parent directory semantics

`output_dir.parent` должен уже существовать и быть directory.

Exporter создаёт только:

- temporary sibling directory;
- final bundle root через rename;
- internal bundle subdirectories (`fields/...`).

Он не создаёт произвольную цепочку отсутствующих parent directories.

## 13. Atomic visibility

Exporter пишет bundle в temporary sibling directory рядом с final target:

```text
.<target-name>.tmp-<implementation-generated-id>/
```

Порядок:

```text
validate assembly
  -> create temporary sibling
  -> write domain.json
  -> write fields/*.npy
  -> calculate persisted file hashes/sizes
  -> write manifest.json
  -> rename temporary directory -> output_dir
```

Final target становится видимым только после успешной записи canonical contents.

Temporary directory name является implementation detail и не входит в reproducibility contract.

## 14. Failure cleanup

При normal exception temporary directory удаляется best-effort.

Crash, `SIGKILL`, power loss или OS failure могут оставить temporary sibling directory. Она не считается completed DomainBundle и не должна автоматически подменять final target.

## 15. Determinism boundary

Два exports одного `DomainAssembly` одной поддерживаемой exporter/generator environment должны давать одинаковое содержимое canonical files и одинаковые manifest hashes.

Filesystem metadata не является canonical:

- timestamps;
- inode;
- ownership;
- platform permissions.

Byte-level stability `.npy` между произвольными будущими версиями NumPy/exporter не гарантируется вне exact supported version boundary. INV-009 остаётся применим.

## 16. Error boundary

`DomainBundleExportError` используется для ожидаемых export contract failures:

- invalid/incomplete field mapping;
- descriptor/payload mismatch;
- unsafe/colliding path;
- existing target;
- invalid parent;
- persistence failure до final rename;
- manifest contract failure.

Exporter не выполняет fallback, auto-fix, regeneration или reroll.

## 17. Out of scope v0.1

- ZIP/tar/compression;
- overwrite/`--force`;
- renderer;
- preview/debug generation;
- CLI parsing;
- GitHub artifact upload;
- cloud/object storage;
- input request directory convention;
- generation algorithms;
- semantic modification `DomainData`;
- packaging optional presentation artifacts into canonical manifest.

## 18. Next checkpoint

Implementation DomainBundle Export v0.1 принят и merged через PR #38. Следующий bounded design gate — `Technical Renderer v0.1`.
