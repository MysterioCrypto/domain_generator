from __future__ import annotations

from dataclasses import dataclass

from .contracts.geometry import PointGeometry
from .contracts.plan import GenerationPlan


@dataclass(frozen=True, slots=True)
class GridAdapter:
    width_km: float
    height_km: float
    cell_size_km: float
    rows: int
    columns: int

    @classmethod
    def from_plan(cls, plan: GenerationPlan) -> "GridAdapter":
        return cls(
            width_km=plan.domain.width_km,
            height_km=plan.domain.height_km,
            cell_size_km=plan.grid.cell_size_km,
            rows=plan.grid.rows,
            columns=plan.grid.columns,
        )

    def cell_center(self, row: int, column: int) -> PointGeometry:
        if isinstance(row, bool) or not isinstance(row, int):
            raise TypeError("row must be an integer")
        if isinstance(column, bool) or not isinstance(column, int):
            raise TypeError("column must be an integer")
        if not 0 <= row < self.rows:
            raise IndexError("row is outside grid")
        if not 0 <= column < self.columns:
            raise IndexError("column is outside grid")

        return PointGeometry(
            x_km=(column + 0.5) * self.cell_size_km,
            y_km=self.height_km - (row + 0.5) * self.cell_size_km,
        )
