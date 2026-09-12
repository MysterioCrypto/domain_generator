from __future__ import annotations

from dataclasses import dataclass
from math import floor, isfinite

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

    def containing_cell(self, x_km: float, y_km: float) -> tuple[int, int]:
        """Return the cell containing a world-space point using canonical boundary ties.

        Internal vertical boundaries belong to the eastern cell. Internal horizontal
        boundaries belong to the northern cell. The outer north/east boundaries are
        clamped to the final in-domain cell.
        """
        if not isfinite(x_km) or not isfinite(y_km):
            raise ValueError("world point coordinates must be finite")
        if not 0.0 <= x_km <= self.width_km:
            raise ValueError("x_km is outside domain")
        if not 0.0 <= y_km <= self.height_km:
            raise ValueError("y_km is outside domain")

        column = min(self.columns - 1, int(floor(x_km / self.cell_size_km)))
        south_index = min(self.rows - 1, int(floor(y_km / self.cell_size_km)))
        row = self.rows - 1 - south_index
        return row, column
