# Handoff: продолжение разработки `domain_generator`

Этот файл больше **не дублирует оперативное состояние проекта**.

Дублированный handoff однажды отстал от реальной development line и стал причиной неверного восстановления контекста. Поэтому текущая схема такая:

```text
PROJECT.md
→ docs/CONTEXT.md
→ relevant accepted design under docs/design/
→ code/tests
```

- `PROJECT.md` — устойчивая версия/архитектурная граница и active development line.
- `docs/CONTEXT.md` — rolling semantic context/backlog: что принято, что отвергнуто, почему и какой checkpoint следующий.
- `docs/CONTEXT.md` намеренно переписывается на значимых checkpoint'ах и не ведёт commit-by-commit историю.
- `docs/design/`, `docs/contracts/`, `docs/decisions/` остаются нормативными источниками semantics.
- Git/PR history используется для археологии, а не как основной handoff.

Не использовать старое содержимое этого файла или исторический Core 0.1 roadmap как источник текущей задачи.
