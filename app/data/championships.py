"""
Championship history data.

Contains hardcoded championship mappings from 1950-2024 to avoid rate-limiting
Jolpica with 150+ historical queries. These are updated dynamically for recent
years by the stats service at runtime.

These are module-level mutable objects — services can update them in place.
"""

# World Drivers' Championship wins by driver ID
GLOBAL_WDC_MAP = {
    'michael_schumacher': 7, 'hamilton': 7, 'fangio': 5, 'prost': 4,
    'vettel': 4, 'brabham': 3, 'stewart': 3, 'lauda': 3, 'piquet': 3,
    'senna': 3, 'max_verstappen': 4, 'ascari': 2, 'clark': 2, 'hill': 2,
    'emerson_fittipaldi': 2, 'hakkinen': 2, 'alonso': 2, 'farina': 1,
    'hawthorn': 1, 'phil_hill': 1, 'surtees': 1, 'hulme': 1, 'rindt': 1,
    'andretti': 1, 'scheckter': 1, 'jones': 1, 'keke_rosberg': 1,
    'mansell': 1, 'damon_hill': 1, 'villeneuve': 1, 'raikkonen': 1,
    'button': 1, 'nico_rosberg': 1
}

# World Constructors' Championship wins by constructor ID
GLOBAL_WCC_MAP = {
    'ferrari': 16, 'williams': 9, 'mclaren': 8, 'mercedes': 8,
    'lotus': 7, 'red_bull': 6, 'cooper': 2, 'brabham': 2, 'renault': 2,
    'vanwall': 1, 'brm': 1, 'matra': 1, 'tyrrell': 1, 'benetton': 1,
    'brawn': 1
}

# Drivers' Championship wins grouped by the constructor the winning driver raced for
GLOBAL_DRIVER_WCC_MAP = {
    'ferrari': 15, 'mclaren': 12, 'mercedes': 9, 'williams': 7,
    'red_bull': 7, 'lotus': 6, 'brabham': 4, 'alfaromeo': 2,
    'maserati': 2, 'cooper': 2, 'renault': 2, 'benetton': 2,
    'tyrrell': 2, 'brm': 1, 'matra': 1, 'brawn': 1
}

# Tracks which years have already been dynamically fetched
# to prevent duplicate updates across requests
UPDATED_YEARS = set()
