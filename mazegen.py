from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from maze_files.maze_definitions import Maze
from maze_files.dfs_maze_generator import dfs_maze_generator
from maze_files.bfs_shortest_path_solver import bfs_shortest_path_solver

try:
    from maze_files.multiple_path_maze import multiple_path_maze
except Exception:
    multiple_path_maze = None

try:
    from maze_files.forty_two_marking import forty_two_marking
except Exception:
    forty_two_marking = None


@dataclass(slots=True)
class ConfigGen:
    """Maze generation settings."""
    width: int
    height: int
    entry: tuple[int, int]
    exit: tuple[int, int]
    seed: int = 0
    perfect: bool = True
    marking_42: bool = True


class MazeGenerator:
    """High-level maze generator and solver."""
    def __init__(self, cfg: ConfigGen) -> None:
        """Bind generator to a configuration."""
        self.cfg = cfg
        self._maze: Optional[Maze] = None
        self._path: Optional[list[tuple[int, int]]] = None
        self._forbidden: set[tuple[int, int]] = set()

    @property
    def maze(self) -> Maze:
        """Return the generated maze."""
        if self._maze is None:
            raise RuntimeError(
                "Maze not generated yer. Please call generate() function"
                "first.")
        return self._maze

    @property
    def grid(self) -> list[list[int]]:
        """Shortcut for maze.grid."""
        return self.maze.grid

    @property
    def forbidden_cells(self) -> set[tuple[int, int]]:
        """Forbidden cells (copy)."""
        return set(self._forbidden)

    @property
    def path(self) -> list[tuple[int, int]]:
        """Last solved path."""
        if self._path is None:
            raise RuntimeError("Maze path is not solved yet.")

    @property
    def generate(self) -> Maze:
        """Generate and store a new maze."""
        cfg = self.cfg

        # Fresh maze: every cell starts with mask=15 (all walls closed).
        self._maze = Maze(cfg.height, cfg.width, cfg.entry, cfg.exit)

        # Reset derived state from any previous run.
        self._path = None
        self._forbidden = set()

        # Compute "42" forbidden cells only when requested and available.
        if cfg.marking_42 and forty_two_marking is not None:
            self._forbidden = set(forty_two_marking(self._maze))

        # DFS generation mutates maze.grid in-place.
        dfs_maze_generator(self._maze, self._forbidden, cfg.seed)
        if not cfg.perfect:
            if multiple_path_maze is None:
                raise RuntimeError(
                    "Config Perfect=False but multiple_path_maze() was not "
                    "found. Expected maze_files/multiple_path_maze.py to "
                    "define multiple_path maze.")
            multiple_path_maze(self._maze)

        return self._maze

    def solve_maze_path(self) -> list[tuple[int, int]]:
        """Solve maze using BFS."""
        self._path = bfs_shortest_path_solver(self.maze)
        return list(self._path)

    def coords_to_directions(
            self,
            coords: Optional[Iterable[tuple[int, int]]] = None,) -> str:
        """Convert coordinates to a N/E/S/W direction string."""
        if coords is None:
            coords_list = self.path
        else:
            coords_list = list(coords)

        # Need at least 2 points to produce a move.
        if len(coords_list) < 2:
            return ""

        out: list[str] = []

        # Walk pairwise: (p0,p1), (p1,p2), ...
        for (x1, y1), (x2, y2) in zip(coords_list, coords_list[1:]):
            dx = x2 - x1
            dy = y2 - y1
            if dx == 0 and dy == -1:
                out.append("N")
            elif dx == 1 and dy == 0:
                out.append("E")
            elif dx == 0 and dy == 1:
                out.append("S")
            elif dx == -1 and dy == 0:
                out.append("W")
            else:
                raise ValueError(f"Non-adjacent step in path for coordinates: "
                                 f"{(x1, y1)} and {(x2,  y2)}")
        return "".join(out)
