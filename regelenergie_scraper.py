"""
Regelenergie Data Scraper mit Selenium
Automatisierter Download von CSV-Daten von netztransparenz.de

Installation:
pip install selenium pandas webdriver-manager

Autor: DomJek
Version: 2.0
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
from datetime import datetime, timedelta
from pathlib import Path
import os


class NetztransparenzScraper:
    """
    Automatisierter Scraper für netztransparenz.de mit Selenium
    """

    def __init__(self, headless=True, download_dir=None):
        """
        Initialisiert den Scraper

        Parameters:
        -----------
        headless : bool
            Browser im Hintergrund ausführen
        download_dir : str
            Verzeichnis für Downloads (Standard: ./downloads)
        """
        self.download_dir = Path(download_dir or './downloads').absolute()
        self.download_dir.mkdir(parents=True, exist_ok=True)

        # Chrome Optionen
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')

        # Download-Einstellungen
        prefs = {
            "download.default_directory": str(self.download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)

        # WebDriver initialisieren
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_page_load_timeout(30)

        print(f"✅ Browser initialisiert (Headless: {headless})")
        print(f"📁 Download-Verzeichnis: {self.download_dir}")

    def navigate_to_page(self):
        """
        Navigiert zur Regelleistungs-Seite
        """
        url = "https://www.netztransparenz.de/de-de/Regelenergie/Daten-Regelreserve/Aktivierte-Regelleistung"
        print(f"🌐 Navigiere zu: {url}")
        self.driver.get(url)
        time.sleep(3)  # Warte auf Seitenladung

    def set_date_range(self, start_date, end_date, section='prl'):
        """
        Setzt den Datumsbereich für den Download

        Parameters:
        -----------
        start_date : datetime
            Startdatum
        end_date : datetime
            Enddatum
        section : str
            'prl' für k*Delta f oder 'affr' für aFRR
        """
        print(f"📅 Setze Zeitraum: {start_date.date()} bis {end_date.date()}")

        try:
            # Die IDs der Datumsfelder variieren je nach Sektion
            # Beispiel-IDs (müssen ggf. angepasst werden):
            if section == 'prl':
                start_id = "dnn_ctr2969_View_RadDatePickerFrom_dateInput"
                end_id = "dnn_ctr2969_View_RadDatePickerTo_dateInput"
                download_button_id = "dnn_ctr2969_View_btnDownloadGridCsv"
            else:  # affr
                start_id = "dnn_ctr2113_View_RadDatePickerFrom_dateInput"
                end_id = "dnn_ctr2113_View_RadDatePickerTo_dateInput"
                download_button_id = "dnn_ctr2113_View_btnDownloadGridCsv"

            # Start-Datum setzen
            start_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, start_id))
            )
            start_field.clear()
            start_field.send_keys(start_date.strftime('%d.%m.%Y'))

            # End-Datum setzen
            end_field = self.driver.find_element(By.ID, end_id)
            end_field.clear()
            end_field.send_keys(end_date.strftime('%d.%m.%Y'))

            time.sleep(1)

            return download_button_id

        except Exception as e:
            print(f"❌ Fehler beim Setzen des Datumsbereichs: {e}")
            return None

    def download_csv(self, section='prl', start_date=None, end_date=None):
        """
        Lädt CSV-Datei herunter

        Parameters:
        -----------
        section : str
            'prl' für k*Delta f oder 'affr' für aFRR
        start_date : datetime
            Startdatum (Standard: vor 7 Tagen)
        end_date : datetime
            Enddatum (Standard: heute)

        Returns:
        --------
        str: Pfad zur heruntergeladenen Datei
        """
        if start_date is None:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)

        self.navigate_to_page()

        # Scrolle zur entsprechenden Sektion
        section_mapping = {
            'prl': 'k*Delta f (PRL)',
            'affr': 'Aktivierte aFRR (SRL)'
        }

        print(f"📊 Lade Daten für: {section_mapping.get(section, section)}")

        # Datum setzen
        download_button_id = self.set_date_range(start_date, end_date, section)

        if not download_button_id:
            return None

        try:
            # CSV Download Button klicken
            download_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, download_button_id))
            )

            print("⬇️  Starte Download...")
            download_button.click()

            # Warte auf Download
            time.sleep(5)

            # Finde die neueste heruntergeladene Datei
            files = list(self.download_dir.glob('*.csv'))
            if files:
                latest_file = max(files, key=os.path.getctime)
                print(f"✅ Download abgeschlossen: {latest_file.name}")
                return str(latest_file)
            else:
                print("❌ Keine CSV-Datei gefunden")
                return None

        except Exception as e:
            print(f"❌ Fehler beim Download: {e}")
            self.driver.save_screenshot(self.download_dir / 'error_screenshot.png')
            return None

    def download_all_data(self, start_date=None, end_date=None):
        """
        Lädt alle verfügbaren Datensätze herunter

        Returns:
        --------
        dict mit Pfaden zu den heruntergeladenen Dateien
        """
        if start_date is None:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)

        downloads = {}

        print("\n" + "=" * 60)
        print("📥 STARTE BATCH-DOWNLOAD")
        print("=" * 60 + "\n")

        # PRL Daten
        print("1️⃣  k*Delta f (PRL)")
        prl_file = self.download_csv('prl', start_date, end_date)
        if prl_file:
            downloads['prl'] = prl_file

        time.sleep(2)

        # aFRR Daten
        print("\n2️⃣  Aktivierte aFRR (SRL)")
        affr_file = self.download_csv('affr', start_date, end_date)
        if affr_file:
            downloads['affr'] = affr_file

        print("\n" + "=" * 60)
        print(f"✅ Downloads abgeschlossen: {len(downloads)} Dateien")
        print("=" * 60)

        return downloads

    def load_csv_to_dataframe(self, filepath):
        """
        Lädt eine heruntergeladene CSV in einen DataFrame

        Parameters:
        -----------
        filepath : str
            Pfad zur CSV-Datei

        Returns:
        --------
        pd.DataFrame
        """
        try:
            # CSV einlesen (Encoding und Separator müssen ggf. angepasst werden)
            df = pd.read_csv(
                filepath,
                sep=';',  # Typischerweise Semikolon
                encoding='utf-8-sig',  # oder 'latin1'
                decimal=',',  # Deutsche Dezimaltrennzeichen
                thousands='.'
            )

            print(f"✅ CSV geladen: {len(df)} Zeilen, {len(df.columns)} Spalten")
            return df

        except Exception as e:
            print(f"❌ Fehler beim Laden der CSV: {e}")
            return None

    def close(self):
        """
        Schließt den Browser
        """
        if self.driver:
            self.driver.quit()
            print("🔒 Browser geschlossen")


def process_regelenergie_data(prl_df, affr_df):
    """
    Verarbeitet und analysiert die geladenen Daten

    Parameters:
    -----------
    prl_df : pd.DataFrame
        PRL-Daten
    affr_df : pd.DataFrame
        aFRR-Daten

    Returns:
    --------
    dict mit Analyseergebnissen
    """
    results = {}

    if prl_df is not None:
        print("\n📊 PRL-Analyse:")
        print(f"  Zeitraum: {prl_df.index[0]} bis {prl_df.index[-1]}")
        print(f"  Datenpunkte: {len(prl_df)}")

        # Beispiel-Analysen
        numeric_cols = prl_df.select_dtypes(include=['float64', 'int64']).columns
        if len(numeric_cols) > 0:
            print(f"\n  Statistiken für {numeric_cols[0]}:")
            print(f"    - Mittelwert: {prl_df[numeric_cols[0]].mean():.2f}")
            print(f"    - Maximum: {prl_df[numeric_cols[0]].max():.2f}")
            print(f"    - Minimum: {prl_df[numeric_cols[0]].min():.2f}")

        results['prl'] = prl_df

    if affr_df is not None:
        print("\n⚡ aFRR-Analyse:")
        print(f"  Zeitraum: {affr_df.index[0]} bis {affr_df.index[-1]}")
        print(f"  Datenpunkte: {len(affr_df)}")

        numeric_cols = affr_df.select_dtypes(include=['float64', 'int64']).columns
        if len(numeric_cols) > 0:
            print(f"\n  Statistiken für {numeric_cols[0]}:")
            print(f"    - Mittelwert: {affr_df[numeric_cols[0]].mean():.2f}")
            print(f"    - Maximum: {affr_df[numeric_cols[0]].max():.2f}")

        results['affr'] = affr_df

    return results


# Hauptprogramm
if __name__ == "__main__":
    print("=" * 60)
    print("🔌 NETZTRANSPARENZ.DE REGELENERGIE SCRAPER")
    print("=" * 60)

    # Zeitraum definieren
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    print(f"\n📅 Zeitraum: {start_date.date()} bis {end_date.date()}")

    try:
        # Scraper initialisieren
        scraper = NetztransparenzScraper(headless=False)  # headless=True für Hintergrund

        # Alle Daten herunterladen
        downloads = scraper.download_all_data(start_date, end_date)

        # Daten laden und analysieren
        if downloads:
            print("\n" + "=" * 60)
            print("📈 DATENANALYSE")
            print("=" * 60)

            prl_df = None
            affr_df = None

            if 'prl' in downloads:
                prl_df = scraper.load_csv_to_dataframe(downloads['prl'])

            if 'affr' in downloads:
                affr_df = scraper.load_csv_to_dataframe(downloads['affr'])

            # Analysiere Daten
            results = process_regelenergie_data(prl_df, affr_df)

            print("\n✅ Analyse abgeschlossen!")

    except Exception as e:
        print(f"\n❌ Fehler: {e}")

    finally:
        # Browser schließen
        scraper.close()

    print("\n" + "=" * 60)
    print("FERTIG!")
    print("=" * 60)
    print("""
💡 NÄCHSTE SCHRITTE:

1. Die heruntergeladenen CSV-Dateien befinden sich in ./downloads/

2. Für automatische Visualisierung:
   → Integration mit matplotlib oder plotly
   → Dashboard mit Streamlit oder Dash

3. Für regelmäßige Updates:
   → Cronjob einrichten (Linux/Mac)
   → Task Scheduler (Windows)
   → Cloud-Lösung (AWS Lambda, etc.)

4. Für API-Integration:
   → Offizielle API prüfen: https://api-portal.netztransparenz.de/
   → REST-API Wrapper erstellen
""")