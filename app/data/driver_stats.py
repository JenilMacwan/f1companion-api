"""
Driver career baseline statistics.

Hardcoded career stats for all drivers on the current grid up to end of 2025.
Current-year stats are fetched dynamically by the stats service and added
on top of these baselines.
"""

DRIVER_BASE_STATS = {
    "albon": {"total_races": 132, "total_pole": 0, "total_wins": 0, "total_podiums": 2, "career_points": 308.0, "total_seasons": 6},
    "alonso": {"total_races": 428, "total_pole": 22, "total_wins": 32, "total_podiums": 106, "career_points": 2380.0, "total_seasons": 22},
    "antonelli": {"total_races": 24, "total_pole": 0, "total_wins": 0, "total_podiums": 3, "career_points": 135.0, "total_seasons": 1},
    "bearman": {"total_races": 27, "total_pole": 0, "total_wins": 0, "total_podiums": 0, "career_points": 46.0, "total_seasons": 2},
    "bortoleto": {"total_races": 24, "total_pole": 0, "total_wins": 0, "total_podiums": 0, "career_points": 19.0, "total_seasons": 1},
    "bottas": {"total_races": 247, "total_pole": 20, "total_wins": 10, "total_podiums": 67, "career_points": 1788.0, "total_seasons": 12},
    "colapinto": {"total_races": 27, "total_pole": 0, "total_wins": 0, "total_podiums": 0, "career_points": 5.0, "total_seasons": 2},
    "jak_crawford": {"total_races": 0, "total_pole": 0, "total_wins": 0, "total_podiums": 0, "career_points": 0.0, "total_seasons": 0},
    "gasly": {"total_races": 178, "total_pole": 0, "total_wins": 1, "total_podiums": 5, "career_points": 446.0, "total_seasons": 9},
    "hadjar": {"total_races": 24, "total_pole": 0, "total_wins": 0, "total_podiums": 1, "career_points": 50.0, "total_seasons": 1},
    "hamilton": {"total_races": 380, "total_pole": 104, "total_wins": 105, "total_podiums": 202, "career_points": 4955.5, "total_seasons": 19},
    "hulkenberg": {"total_races": 254, "total_pole": 1, "total_wins": 0, "total_podiums": 1, "career_points": 614.0, "total_seasons": 14},
    "lawson": {"total_races": 35, "total_pole": 0, "total_wins": 0, "total_podiums": 0, "career_points": 44.0, "total_seasons": 3},
    "leclerc": {"total_races": 173, "total_pole": 27, "total_wins": 8, "total_podiums": 50, "career_points": 1588.0, "total_seasons": 8},
    "arvid_lindblad": {"total_races": 0, "total_pole": 0, "total_wins": 0, "total_podiums": 0, "career_points": 0.0, "total_seasons": 0},
    "norris": {"total_races": 152, "total_pole": 16, "total_wins": 11, "total_podiums": 44, "career_points": 1344.0, "total_seasons": 7},
    "ocon": {"total_races": 180, "total_pole": 0, "total_wins": 1, "total_podiums": 4, "career_points": 474.0, "total_seasons": 9},
    "piastri": {"total_races": 70, "total_pole": 6, "total_wins": 9, "total_podiums": 26, "career_points": 728.0, "total_seasons": 3},
    "perez": {"total_races": 283, "total_pole": 3, "total_wins": 6, "total_podiums": 39, "career_points": 1585.0, "total_seasons": 14},
    "russell": {"total_races": 152, "total_pole": 8, "total_wins": 5, "total_podiums": 24, "career_points": 953.0, "total_seasons": 7},
    "sainz": {"total_races": 232, "total_pole": 6, "total_wins": 4, "total_podiums": 29, "career_points": 1257.5, "total_seasons": 11},
    "stroll": {"total_races": 191, "total_pole": 1, "total_wins": 0, "total_podiums": 3, "career_points": 315.0, "total_seasons": 9},
    "max_verstappen": {"total_races": 233, "total_pole": 48, "total_wins": 71, "total_podiums": 127, "career_points": 3301.5, "total_seasons": 11}
}
