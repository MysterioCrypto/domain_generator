---
project: domain_generator
branch_role: administrative-entrypoint
active_development_branch: dev/0.2
historical_release_branch: release/0.1-prealpha
historical_release_commit: 9699c3d8079b8b9710d65eed60ff975158af0ad3
active_project_file: dev/0.2:PROJECT.md
active_working_context: dev/0.2:docs/CONTEXT.md
---

# Repository entry point

`main` больше не является источником истины о текущей generation semantics.

Код на этой ветке соответствует историческому Core 0.1 baseline. Текущая разработка ведётся в ветке, указанной в metadata выше.

Для восстановления проекта:

```text
dev/0.2:PROJECT.md
→ dev/0.2:docs/CONTEXT.md
→ relevant accepted design under dev/0.2:docs/design/
→ code/tests on the active branch
```

Core 0.1 сохранён отдельно в `release/0.1-prealpha` и не является release candidate. Он оставлен как историческая pre-alpha точка после visual audit, показавшего неприемлемые world-generation semantics.

Не продолжать работу из старого Core 0.1 roadmap или старого handoff без проверки active development branch.
