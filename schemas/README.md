# JSON Schema snapshots — Core 0.1

This directory contains generated JSON Schema snapshots for the six root serialized contracts:

- `DomainSpec`
- `GenerationPlan`
- `LayoutCandidate`
- `ValidationResult`
- `GenerationConfig`
- `DomainData`

Regenerate them with:

```bash
python -m domain_generator.schema_export
```

The files target JSON Schema Draft 2020-12 and are generated from the Pydantic v2 models with aliases enabled.

Important boundary: JSON Schema captures the structural constraints expressible by Pydantic's schema generator. Cross-field checks implemented by `model_validator` (for example exact grid divisibility, aggregate validation state, or canonical `DomainData` field requirements) still require validation by the Python contract model/Core. The committed snapshots are therefore interchange/documentation schemas, not a replacement for Core validation.
