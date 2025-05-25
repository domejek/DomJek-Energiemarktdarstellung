# aFRR Leistungspreis-Prognosemodell

Dieses Python-Skript prognostiziert und optimiert Gebotspreise für den deutschen Regelenergiemarkt (aFRR, automatische Frequenzreserve). Es nutzt Machine Learning, um optimale Strategien für maximale Erlöse zu entwickeln.

## Features

- **Datenintegration:** Kombiniert Marktdaten (aFRR-Auktionen, Last, Wetter, Spotpreise) oder generiert realistische Beispieldaten.
- **Feature Engineering:** Automatische Erstellung von Zeitreihen- und Markt-Features.
- **Modelltraining:** Vergleich verschiedener ML-Modelle (Random Forest, Gradient Boosting, XGBoost, Ridge, Linear Regression).
- **Preisprognose:** Vorhersage der Clearing-Preise für die nächsten Stunden.
- **Gebotsoptimierung:** Optimiert die Gebotsstrategie für maximalen erwarteten Ertrag.
- **Backtesting:** Bewertung der Strategie auf historischen Daten.
- **Berichtserstellung:** Visualisierung der wichtigsten Modellmetriken und Feature-Importances.

## Installation

Folgende Python-Pakete werden benötigt:

- numpy
- pandas
- scikit-learn
- xgboost
- scipy
- matplotlib
- seaborn

Installation mit pip:

```bash
pip install numpy pandas scikit-learn xgboost scipy matplotlib seaborn
```

## Nutzung

Das Skript kann direkt ausgeführt werden:

```bash
python affr.py
```

**Ablauf:**
1. Lädt Marktdaten (aus Dateien oder generiert Beispieldaten).
2. Trainiert ML-Modelle und wählt das beste Modell.
3. Prognostiziert die Clearing-Preise für die nächsten 24 Stunden.
4. Optimiert die Gebotsstrategie.
5. Erstellt einen Bericht mit Visualisierungen.
6. Optional: Führt ein Backtesting durch und zeigt die Ergebnisse an.

## Beispiel-Ausgabe

- Optimale Gebotsstrategie (Ausschnitt als DataFrame)
- Zusammenfassung der Strategie (Durchschnittlicher Gebotspreis, Marge, Zuschlagswahrscheinlichkeit)
- Backtest-Ergebnisse (Tageserlöse, Erfolgsquote)

## Anpassung

- Eigene Marktdaten können über die Methode `load_market_data()` eingebunden werden. Erwartet werden CSV-Dateien mit einer Spalte `datetime`.
- Modellparameter und Kapazität können über das `config`-Dictionary angepasst werden.

## Hinweise

- Das Modell ist für Demonstrationszwecke konzipiert und kann für produktive Anwendungen weiter angepasst werden.
- Die Zuschlagswahrscheinlichkeit basiert auf einer vereinfachten logistischen Funktion.

## Lizenz

MIT License

---

**Autor:** domjek  
**Stand:** Juni 2024
