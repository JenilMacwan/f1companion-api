# 🏎️ F1 Companion API

A high-performance FastAPI middleware that aggregates and serves Formula 1 data — including schedules, standings, driver/constructor stats, live race countdowns with weather, and the latest F1 news.

Built to power the **F1 Companion** Flutter app.

---

## 🚀 Features

- 📅 **Season Schedule** — Full race calendar with all session times
- ⏱️ **Next Race Countdown** — Live countdown to the next session with real-time track weather
- 🧑‍✈️ **Drivers & Constructors** — Current 2026 season lineup
- 🏆 **Live Standings** — WDC (Driver) and WCC (Constructor) championship standings
- 🏟️ **Circuits** — Info on all 2026 circuits including track layout images
- 📊 **Race Results** — Results for any race by round and year (incl. qualifying and sprints)
- 🤝 **Teammate Head-to-Head** — Comprehensive stats comparing teammates across all sessions
- 🚩 **Race Control** — Live and historical race control messages (flags, safety cars, etc.) - Under Development
- 🧑‍✈️ **Driver Profiles & Stats** — Driver profile data along with career wins, podiums, poles, points, championships, and full race history
- 🔧 **Constructor Profiles & Stats** — Constructor profile data and all-time win/podium rates for any team
- 📰 **F1 News** — Latest headlines sourced from Sky Sports F1 RSS feed

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Framework | [FastAPI](https://fastapi.tiangolo.com/) |
| Server | [Uvicorn](https://www.uvicorn.org/) |
| F1 Data | [Jolpica Ergast API](https://api.jolpi.ca/) |
| Weather | [Open-Meteo](https://open-meteo.com/) |
| News | Sky Sports F1 RSS Feed via `feedparser` |

---

## 📦 Installation

**1. Clone the repository**
```bash
git clone https://github.com/JenilMacwan/f1companion-api.git
cd f1companion-api
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

---

## ▶️ Running the API

```bash
uvicorn app.main:app --host 127.0.0.1 --port 5000 --reload
```

The server starts at `http://127.0.0.1:5000`. Visit the root endpoint to see all available routes.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | API index & endpoint list |
| `GET` | `/health` | Health check |
| `GET` | `/schedule` | Full 2026 season calendar |
| `GET` | `/next_race` | Countdown, weather & next session info |
| `GET` | `/drivers` | All 2026 drivers |
| `GET` | `/constructors` | All 2026 constructors (teams) |
| `GET` | `/driver_standings` | Live WDC standings |
| `GET` | `/constructor_standings` | Live WCC standings |
| `GET` | `/teammate_h2h` | Comprehensive head-to-head stats for teammates |
| `GET` | `/circuits` | All 2026 circuit details |
| `GET` | `/race_results/{round}/{year}` | Race results for a specific round |
| `GET` | `/qualifying_results/{round}/{year}` | Qualifying results for a specific round |
| `GET` | `/sprint_results/{round}/{year}` | Sprint results for a specific round |
| `GET` | `/sprint_qualifying_results/{round}/{year}` | Sprint qualifying results for a specific round |
| `GET` | `/race_control` | Live and historical race control messages |
| `GET` | `/driver_profile` | Driver profiles & full career stats for all drivers |
| `GET` | `/constructor_stats` | All-time stats for all constructors |
| `GET` | `/constructor_profile` | Constructor profiles & history |
| `GET` | `/news` | Latest F1 news (top 10 articles) |

### Example Requests

```
GET /race_results/1/2025        → Results for Round 1 of 2025
GET /driver_profile/            → Profile and career stats of all drivers in current grid
GET /constructor_stats/         → Career Stats for all teams in current grid
GET /constructor_profile/       → Profile and history for all teams in current grid
```

---

## 🌦️ Weather Integration

The `/next_race` endpoint fetches **live weather** at the circuit location using the Open-Meteo API, returning the current temperature and condition (e.g., "Clear Sky", "Moderate Rain").

---

## 📁 Project Structure

```
f1companion-api/
│
├── app/
│   ├── main.py                  # Application entry point (minimal)
│   │
│   ├── core/                    # Application-wide infrastructure
│   │   ├── config.py            # API URLs, CORS settings
│   │   ├── constants.py         # Weather codes, track layouts, mappings
│   │   ├── http_client.py       # Shared HTTP client with connection pooling
│   │   └── logging.py           # Centralized logger
│   │
│   ├── routers/                 # API endpoint definitions (thin wrappers)
│   │   ├── system_router.py     # /, /health, /favicon.ico
│   │   ├── schedule_router.py   # /schedule
│   │   ├── race_router.py       # /next_race, /race_results
│   │   ├── driver_router.py     # /drivers, /driver_profile
│   │   ├── constructor_router.py# /constructors, /constructor_profile
│   │   ├── standings_router.py  # /driver_standings, /constructor_standings
│   │   ├── stats_router.py      # /constructor_stats
│   │   ├── circuit_router.py    # /circuits
│   │   ├── teammate_h2h_router.py # /teammate_h2h
│   │   ├── race_control_router.py # /race_control
│   │   └── news_router.py       # /news
│   │
│   ├── services/                # Business logic layer
│   │   ├── schedule_service.py  # Schedule fetching and formatting
│   │   ├── race_service.py      # Next race, countdown, race results
│   │   ├── round_results_service.py # Bulk cache manager for round results
│   │   ├── race_control_service.py # Race control messages fetching
│   │   ├── teammate_h2h_service.py # Teammate head-to-head comparison
│   │   ├── driver_service.py    # Driver information
│   │   ├── constructor_service.py # Constructor information
│   │   ├── standings_service.py # WDC and WCC standings
│   │   ├── weather_service.py   # Open-Meteo weather integration
│   │   ├── news_service.py      # RSS feed retrieval and parsing
│   │   └── stats_service.py     # Career stats and championship calculations
│   │
│   ├── data/                    # Static datasets
│   │   ├── championships.py     # WDC/WCC championship history
│   │   ├── driver_stats.py      # Driver career baselines
│   │   └── constructor_stats.py # Constructor career baselines
│   │
│   ├── utils/                   # Reusable helper functions
│   │   ├── flags.py             # Country flag emoji conversion
│   │   ├── datetime_utils.py    # Date/time parsing helpers
│   │   └── helpers.py           # General-purpose utilities
│   │
│   └── assets/
│       └── favicon/
│           └── f1_companion_icon.png
│
├── requirements.txt
├── vercel.json
├── .env
└── README.md
```

---

## 📄 Dependencies

```
fastapi
uvicorn
requests
python-dotenv
emoji-country-flag
feedparser
```

Install all with:
```bash
pip install -r requirements.txt
```

---

## 📝 License

This project is open-source. Data is sourced from [Jolpica Ergast](https://api.jolpi.ca/) and [Open-Meteo](https://open-meteo.com/) — please respect their respective usage policies.
