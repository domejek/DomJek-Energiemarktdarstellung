# 🔌 DomJek Energiemarktdarstellung v3.0

**Visualisierung des deutschen Regelenergiemarkts** — Angular 18 SPA + FastAPI Backend mit Echtdaten von regelleistung.net.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Angular 18](https://img.shields.io/badge/Angular-18-red.svg)](https://angular.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 Überblick

Web-App zur Visualisierung von Ausschreibungsdaten der deutschen Regelenergie:

- **FCR (PRL)** — Primärregelleistung, 6 Tender-Blöcke pro Tag (4h-Raster)
- **aFRR (SRL)** — Sekundärregelleistung, Energy-Markt (15-Min-Intervalle) und Capacity-Markt (4h-Blöcke)

**Datenquelle:** [regelleistung.net](https://www.regelleistung.net) — offizielle REST-API der deutschen Übertragungsnetzbetreiber.

---

## 🚀 Features

✅ **Live-Daten von regelleistung.net** (6 XLSX-Endpunkte, automatisch täglich abgerufen)  
✅ **Demo-Daten** als Fallback bei API-Problemen  
✅ **15-Min-Intervall** Darstellung für aFRR Energy  
✅ **TSO-Filter** (50Hertz, Amprion, TenneT, TransnetBW)  
✅ **Statistiken & KPIs** (Mittelwerte, Maxima, Standardabweichung)  
✅ **Analyse-Charts** (Verteilungen, Tagesprofile, Heatmaps)  
✅ **CSV-Download** der angezeigten Daten  
✅ **In-Memory-Caching** — kein erneuter API-Abruf bei Filter-Änderung  
✅ **Automatischer Fallback** auf Vortag wenn aktuelle Daten fehlen  

---

## 🏗️ Architektur

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────────────┐
│  Angular 18 SPA  │────▶│  FastAPI Backend │────▶│ regelleistung.net API│
│  (Port 4200)     │◀────│  (Port 8000)     │◀────│ (6 XLSX Endpoints)   │
└─────────────────┘     └─────────────────┘     └──────────────────────┘
         │                       │
         │                       ├── /api/energy/prl        — FCR Daten
         │                       ├── /api/energy/affr       — aFRR Daten
         │                       ├── /api/energy/statistics — Statistiken
         │                       ├── /api/energy/daily-summary — Tageswerte
         │                       └── /api/energy/upload     — CSV-Import
         │
    ┌────┴────┐
    │  Plotly  │
    │  Charts  │
    └─────────┘
```

---

## 📦 Installation

### Voraussetzungen

- Python 3.12+
- Node.js 20+ / npm
- Kein Selenium, kein Browser-Treiber nötig

### Schnellstart

```bash
git clone <repo-url>
cd DomJek-Energiemarktdarstellung

# Alles installieren + starten
./run.sh
```

Der `run.sh` installiert Backend- und Frontend-Dependencies automatisch.

### Manuelle Installation

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

---

## 💻 Verwendung

### Entwicklungsserver starten

```bash
./run.sh
```

Öffne http://localhost:4200 im Browser.

Standardmäßig werden **Live-Daten von regelleistung.net** geladen.
Umschalten auf Demo-Daten über die Sidebar: *Einstellungen → Datenquelle → Demo-Daten*.

### API-Endpunkte (direkt)

```bash
# PRL-Daten (FCR)
curl "http://localhost:8000/api/energy/prl?start=2026-05-23&end=2026-05-30&source=api"

# aFRR-Daten
curl "http://localhost:8000/api/energy/affr?start=2026-05-23&end=2026-05-30&source=api"

# Statistiken
curl "http://localhost:8000/api/energy/statistics?start=2026-05-23&end=2026-05-30&source=api"

# API-Dokumentation (Swagger UI)
open http://localhost:8000/docs
```

### Datenquellen (`source`-Parameter)

| Wert | Verhalten |
|---|---|
| `api` | Live-Daten von regelleistung.net (Default) |
| `demo` | Zufallsdaten (für Entwicklung/Tests) |
| `csv` | Manueller CSV-Import über UI |

---

## 🧪 Tests

```bash
# Backend (38 Tests)
python3 -m pytest tests/ -v

# Frontend (26 Tests)
cd frontend && npx ng test --watch=false --browsers=ChromeHeadless
```

---

## 📁 Projektstruktur

```
DomJek-Energiemarktdarstellung/
├── backend/
│   ├── main.py                        # FastAPI App
│   ├── requirements.txt               # Python-Abhängigkeiten
│   ├── routers/energy.py              # REST-Endpunkte
│   ├── services/
│   │   ├── energy_service.py          # Geschäftslogik (Demo + API)
│   │   └── regelleistung_api.py       # XLSX-Fetcher von regelleistung.net 🔥
│   └── models/schemas.py              # Pydantic-Modelle
├── frontend/
│   └── src/app/
│       ├── pages/dashboard/           # Hauptseite
│       ├── components/sidebar/        # Filter (Quelle, Datum, TSOs)
│       ├── components/charts/         # Plotly-Charts
│       ├── services/                  # FilterState + EnergyData
│       └── models/                    # TypeScript-Interfaces
├── tests/                             # Backend-Tests (pytest)
├── run.sh                             # Entwicklungs-Runner
└── README.md
```

---

## 🔌 Datenquellen im Detail

### regelleistung.net API (6 Endpoints)

| Endpoint | Produkt | Markt | Intervalle |
|---|---|---|---|
| `tenders/demands` | FCR | CAPACITY | 6 × 4h-Blöcke |
| `tenders/results/aggregated` | FCR | CAPACITY | 6 × 4h-Blöcke + Preise |
| `tenders/demands` | aFRR | CAPACITY | 12 × 4h-Blöcke (POS+NEG) |
| `tenders/results/aggregated` | aFRR | CAPACITY | 12 × 4h-Blöcke + Preise |
| `tenders/demands` | aFRR | ENERGY | 192 × 15min (POS+NEG) |
| `tenders/results/aggregated` | aFRR | ENERGY | 192 × 15min + Preise |

### API-Fallback-Logik

1. Versuche `deliveryDate=today`
2. Falls keine Daten: `deliveryDate=yesterday` (max. 7 Tage rückwärts)
3. Gelber Banner im UI bei Fallback: *"Daten vom YYYY-MM-DD"*
4. Falls alle API-Versuche fehlschlagen: Demo-Daten als Fallback

---

## 📊 Datenformat (API-Response)

### PRL (FCR) Record

```json
{
  "timestamp": "2026-05-29T00:00:00",
  "deutschland_positiv_mw": 584.0,
  "deutschland_negativ_mw": 584.0,
  "preis_eur_per_mw": 33.36
}
```

### aFRR Record

```json
{
  "timestamp": "2026-05-29T00:00:00",
  "deutschland_positiv_mw": 1911.0,
  "deutschland_negativ_mw": 1747.0,
  "energiepreis_positiv_eur_per_mwh": 15000.0,
  "energiepreis_negativ_eur_per_mwh": -15000.0,
  "angebotene_kapazitaet_positiv_mw": 1864.0,
  "angebotene_kapazitaet_negativ_mw": 2182.0
}
```

---

## 📝 To-Do / Roadmap

- [x] REST-API mit FastAPI
- [x] Angular 18 SPA mit Plotly-Charts
- [x] Live-Daten von regelleistung.net API
- [x] In-Memory-Caching
- [x] Fallback-Mechanismus (heute → gestern → Demo)
- [ ] mFRR (MRL) Datenintegration
- [ ] Historische Daten (>7 Tage) cachen/persistieren
- [ ] Docker-Container
- [ ] Echtzeit-WebSocket-Updates

---

## 👨‍💻 Autor

**DomJek** — [GitHub](https://github.com/domjek)

---

## 🙏 Danksagungen

- [regelleistung.net](https://www.regelleistung.net) für die offene REST-API
- Deutsche Übertragungsnetzbetreiber (50Hertz, Amprion, TenneT, TransnetBW)

---

## 📚 Links

- [Regelleistung.net API](https://www.regelleistung.net/apps/crds/api/v2/)
- [Swagger UI (lokal)](http://localhost:8000/docs)
- [ENTSO-E Transparency Platform](https://transparency.entsoe.eu/)
