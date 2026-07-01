"""
Constructor career baseline statistics.

Hardcoded career stats for all constructors on the current grid.
Includes merged lineage data (e.g., Alpine includes Renault history).
Current-year stats are fetched dynamically by the stats service.
"""

CONSTRUCTOR_BASE_STATS = {
    "ferrari": {"wcc": 16, "wdc": 15, "wins": 248, "entries": 1124, "podiums": 813},
    "mclaren": {"wcc": 10, "wdc": 12, "wins": 203, "entries": 995, "podiums": 522},
    "mercedes": {"wcc": 8, "wdc": 9, "wins": 134, "entries": 318, "podiums": 296},
    "red_bull": {"wcc": 6, "wdc": 7, "wins": 130, "entries": 383, "podiums": 281},
    "williams": {"wcc": 9, "wdc": 7, "wins": 114, "entries": 852, "podiums": 313},
    "alpine": {"wcc": 2, "wdc": 2, "wins": 35, "entries": 403, "podiums": 212},
    "aston_martin": {"wcc": 0, "wdc": 0, "wins": 1, "entries": 606, "podiums": 38},
    "haas": {"wcc": 0, "wdc": 0, "wins": 0, "entries": 182, "podiums": 0},
    "rb": {"wcc": 0, "wdc": 0, "wins": 2, "entries": 370, "podiums": 5},
    "audi": {"wcc": 0, "wdc": 0, "wins": 1, "entries": 614, "podiums": 27},
    "cadillac": {"wcc": 0, "wdc": 0, "wins": 0, "entries": 0, "podiums": 0}
}
