# Codex integration

`domain_generator` ships a repository-scoped Codex skill for natural-language domain authoring and generation.

## Repository-local use

The canonical skill lives at:

```text
.codex/skills/domain-generator-authoring/SKILL.md
```

The repository also contains root `AGENTS.md` instructions. In Codex environments that discover repository instructions/skills, open the repository and ask for the generation task directly, for example:

```text
Сгенерируй регион 40×30 км: горный хребет на севере,
река идёт к югу, поселение находится возле реки.
```

The skill routes that intent through `GenerationRequest`, the real `PresetCatalog`, validation/compiler preflight, and the canonical `domain-generator generate` application boundary.

## Install as a user-level Codex skill

Codex's `$skill-installer` can install a skill from a GitHub directory URL. In Codex, request installation of:

```text
https://github.com/MysterioCrypto/domain_generator/tree/main/.codex/skills/domain-generator-authoring
```

For example:

```text
$skill-installer install https://github.com/MysterioCrypto/domain_generator/tree/main/.codex/skills/domain-generator-authoring
```

User-level skills are installed under `$CODEX_HOME/skills` (normally `~/.codex/skills`). Restart Codex after installation if the new skill is not discovered in the current session.

## What the skill does

The skill tells Codex to:

- use the repository's actual base `GenerationRequest` and `PresetCatalog` rather than inventing capabilities;
- preserve technical defaults unless the user's intent requires changing them;
- perform contract/registry/compiler validation before a successful generation;
- limit automatic technical repair to the initial draft plus at most two repair drafts;
- run semantic generation once after successful preflight;
- use `domain-generator generate` or the public Python application API;
- report generation failure instead of silently changing seed/constraints and rerolling;
- treat `technical-map.png` as diagnostic output, not as an autonomous aesthetic reroll signal.

Detailed provider-neutral authoring rules remain in:

```text
docs/skills/local-model-authoring-v0.1.md
```

## What is not installed

This packaging does not add an OpenAI API client, API key, `CodexHost`, MCP server, or provider dependency to procedural Core. Codex acts as the external interactive agent and calls the same public generator boundary used by other clients.

Programmatic Qwen/Ollama/other-model integration continues to use `LocalModelHost` and `Local Model Adapter v0.1` instead.
