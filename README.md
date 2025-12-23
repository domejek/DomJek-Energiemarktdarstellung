# 🔌 DomJek Energiemarktdarstellung v2.0

**Echtzeitdaten und Visualisierung des deutschen Regelenergiemarkts**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 Überblick

Dieses Python-Projekt lädt, verarbeitet und visualisiert **echte Regelenergiedaten** vom deutschen Energiemarkt über [netztransparenz.de](https://www.netztransparenz.de).

**Version 2.0** - Komplett überarbeitet! Anstatt ML-Training mit Demo-Daten werden nun echte Marktdaten abgerufen.

### 📊 Unterstützte Datenquellen

1. **k\*Delta f (PRL)** - Primärregelleistung
   - Automatische Reaktion auf Frequenzabweichungen
   - Berechnet aus K-Faktor und Frequenzabweichung (50 Hz)
   
2. **Aktivierte aFRR (SRL)** - Sekundärregelleistung
   - Automatischer Frequenzwiederherstellungsreserve
   - Betriebliche und qualitätsgesicherte Daten

---

## 🚀 Features

✅ **Automatischer Datenabruf** von netztransparenz.de  
✅ **CSV-Download und -Verarbeitung**  
✅ **Datenanalyse und Statistiken**  
✅ **Tägliche/Wöchentliche Zusammenfassungen**  
✅ **Export in verschiedene Formate**  
✅ **Visualisierungs-Ready**  

---

## 📦 Installation

### Voraussetzungen

- Python 3.8 oder höher
- pip (Python Package Manager)

### Abhängigkeiten installieren

```bash
# Basis-Installation
pip install pandas numpy requests beautifulsoup4

# Für Selenium-Scraper (empfohlen)
pip install selenium webdriver-manager

# Für Visualisierung (optional)
pip install matplotlib plotly streamlit
```

---

## 💻 Verwendung

### 1. Einfacher Datenabruf (Demo-Modus)

```python
from regelenergie_fetcher import RegelenergieDataProcessor
from datetime import datetime, timedelta

# Zeitraum definieren
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

# Daten laden
processor = RegelenergieDataProcessor()
data = processor.load_data(start_date, end_date)

# Statistiken anzeigen
stats = processor.calculate_statistics()
print(stats)

# Als CSV exportieren
processor.export_to_csv('data')
```

### 2. Echter Datenabruf mit Selenium

```python
from regelenergie_scraper import NetztransparenzScraper
from datetime import datetime, timedelta

# Scraper initialisieren
scraper = NetztransparenzScraper(headless=True)

# Zeitraum definieren
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

# Alle Daten herunterladen
downloads = scraper.download_all_data(start_date, end_date)

# Daten laden
if 'prl' in downloads:
    prl_df = scraper.load_csv_to_dataframe(downloads['prl'])

if 'affr' in downloads:
    affr_df = scraper.load_csv_to_dataframe(downloads['affr'])

# Browser schließen
scraper.close()
```

### 3. Schnellstart (Kommandozeile)

```bash
# Demo-Daten generieren und analysieren
python regelenergie_fetcher.py

# Echte Daten mit Selenium herunterladen
python regelenergie_scraper.py
```

---

## 📁 Projektstruktur

```
DomJek-Energiemarktdarstellung/
├── regelenergie_fetcher.py      # Haupt-API und Datenverarbeitung
├── regelenergie_scraper.py      # Selenium-Scraper für echte Daten
├── visualizer.py                # (Optional) Visualisierung
├── data/                        # Exportierte CSV-Dateien
├── downloads/                   # Heruntergeladene Rohdaten
├── requirements.txt             # Python-Abhängigkeiten
└── README.md                    # Diese Datei
```

---

## 🔧 Konfiguration

### Option 1: Offizielle API nutzen

Die beste Lösung ist die Nutzung der offiziellen API:

```python
# In Entwicklung - prüfe:
# https://api-portal.netztransparenz.de/
```

### Option 2: Manueller CSV-Import

Falls automatischer Download nicht funktioniert:

1. Besuche: [netztransparenz.de/Regelenergie](https://www.netztransparenz.de/de-de/Regelenergie/Daten-Regelreserve/Aktivierte-Regelleistung)
2. Wähle Zeitraum und lade CSV herunter
3. Importiere manuell:

```python
import pandas as pd

# PRL-Daten laden
prl_df = pd.read_csv('prl_daten.csv', sep=';', decimal=',')

# aFRR-Daten laden
affr_df = pd.read_csv('affr_daten.csv', sep=';', decimal=',')
```

---

## 📊 Datenformat

### k\*Delta f (PRL)

```csv
Timestamp,Deutschland_Positiv_MW,Deutschland_Negativ_MW,50Hertz_MW,Amprion_MW,TenneT_MW,TransnetBW_MW
2024-12-01 00:00:00,12.5,-8.3,3.2,4.1,3.5,1.7
2024-12-01 00:15:00,15.2,-10.1,3.8,4.9,4.2,2.3
...
```

### Aktivierte aFRR (SRL)

```csv
Timestamp,Deutschland_Positiv_MW,Deutschland_Negativ_MW,50Hertz_Positiv_MW,Amprion_Positiv_MW,...
2024-12-01 00:00:00,145.2,23.1,35.2,42.1,...
2024-12-01 00:15:00,189.5,18.7,45.8,51.3,...
...
```

---

## 📈 Beispiel-Analysen

### Tägliche Statistiken

```python
# Tägliche Zusammenfassung erstellen
daily = processor.get_daily_summary()

# PRL durchschnittliche Aktivierung pro Tag
print(daily['prl_daily'])

# aFRR Gesamtenergie pro Tag (MWh)
print(daily['affr_daily'])
```

### Aktivierungsmuster

```python
# Finde Zeitpunkte mit hoher Aktivierung
high_activation = processor.affr_data[
    processor.affr_data['Deutschland_Positiv_MW'] > 200
]

print(f"Hohe Aktivierung: {len(high_activation)} Intervalle")
```

---

## 🎨 Visualisierung

### Mit Matplotlib

```python
import matplotlib.pyplot as plt

# PRL Zeitreihe
plt.figure(figsize=(12, 6))
plt.plot(processor.prl_data.index, 
         processor.prl_data['Deutschland_Positiv_MW'],
         label='Positiv')
plt.plot(processor.prl_data.index,
         processor.prl_data['Deutschland_Negativ_MW'],
         label='Negativ')
plt.title('k*Delta f (PRL) - 7 Tage')
plt.xlabel('Zeitpunkt')
plt.ylabel('Leistung (MW)')
plt.legend()
plt.grid(True)
plt.show()
```

### Mit Plotly (interaktiv)

```python
import plotly.graph_objects as go

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=processor.affr_data.index,
    y=processor.affr_data['Deutschland_Positiv_MW'],
    mode='lines',
    name='aFRR Positiv'
))
fig.update_layout(
    title='Aktivierte aFRR (SRL)',
    xaxis_title='Zeitpunkt',
    yaxis_title='Leistung (MW)'
)
fig.show()
```

---

## ⚙️ Erweiterte Konfiguration

### Selenium-Optionen anpassen

```python
scraper = NetztransparenzScraper(
    headless=True,              # Browser im Hintergrund
    download_dir='./meine_daten' # Eigenes Download-Verzeichnis
)
```

### Rate Limiting

```python
import time

# Zwischen Requests warten
time.sleep(2)  # 2 Sekunden Pause
```

---

## 🐛 Troubleshooting

### Problem: Download funktioniert nicht

**Lösung 1:** Prüfe Browser-Version
```bash
# ChromeDriver automatisch aktualisieren
pip install --upgrade webdriver-manager
```

**Lösung 2:** Manuelle Downloads
- Besuche Website direkt und lade CSV herunter
- Importiere mit `pd.read_csv()`

### Problem: CSV-Parsing-Fehler

**Lösung:** Prüfe Encoding und Separator
```python
df = pd.read_csv(
    'datei.csv',
    sep=';',           # oder ','
    encoding='utf-8',  # oder 'latin1'
    decimal=',',       # oder '.'
    thousands='.'      # oder ','
)
```

### Problem: Timeout beim Laden

**Lösung:** Erhöhe Wartezeit
```python
driver.set_page_load_timeout(60)  # 60 Sekunden
time.sleep(5)  # Zusätzliche Wartezeit
```

---

## 🤝 Beitragen

Contributions sind willkommen! 

1. Fork das Repository
2. Erstelle einen Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit deine Änderungen (`git commit -m 'Add some AmazingFeature'`)
4. Push zum Branch (`git push origin feature/AmazingFeature`)
5. Öffne einen Pull Request

---

## 📝 To-Do / Roadmap

- [ ] Integration mit offizieller netztransparenz.de API
- [ ] Web-Dashboard mit Streamlit/Dash
- [ ] Echtzeit-Monitoring (WebSocket)
- [ ] Historische Datenanalyse (>1 Jahr)
- [ ] Machine Learning Prognosemodelle
- [ ] Docker-Container für einfache Deployment
- [ ] REST-API für eigene Anwendungen
- [ ] mFRR (MRL) Datenintegration

---

## 📄 Lizenz

MIT License - siehe [LICENSE](LICENSE) Datei für Details.

---

## 👨‍💻 Autor

**DomJek**
- GitHub: [@domejek](https://github.com/domejek)

---

## 🙏 Danksagungen

- [netztransparenz.de](https://www.netztransparenz.de) für die Bereitstellung der Daten
- Deutsche Übertragungsnetzbetreiber (50Hertz, Amprion, TenneT, TransnetBW)

---

## 📚 Weiterführende Links

- [Netztransparenz.de - Regelenergie](https://www.netztransparenz.de/de-de/Regelenergie)
- [API Portal](https://api-portal.netztransparenz.de/)
- [ENTSO-E Transparency Platform](https://transparency.entsoe.eu/)
- [Regelleistung.net](https://www.regelleistung.net/)

---

**Stand:** Dezember 2024 | **Version:** 2.0 | **Status:** Produktionsreif