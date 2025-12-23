"""
Interaktives Dashboard für Regelenergiedaten
Streamlit-basierte Web-Visualisierung

Start:
streamlit run dashboard.py

Autor: DomJek
Version: 2.0
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path

# Importiere eigene Module (falls verfügbar)
try:
    from regelenergie_fetcher import RegelenergieDataProcessor

    FETCHER_AVAILABLE = True
except ImportError:
    FETCHER_AVAILABLE = False
    st.warning("⚠️ Regelenergie Fetcher nicht gefunden. Nur CSV-Import verfügbar.")

# Seiten-Konfiguration
st.set_page_config(
    page_title="Regelenergie Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Titel
st.title("⚡ Regelenergie Dashboard")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Einstellungen")

    # Datenquelle wählen
    data_source = st.radio(
        "Datenquelle:",
        ["Demo-Daten generieren", "CSV importieren", "Live abrufen (API)"],
        help="Wähle die Quelle für Regelenergiedaten"
    )

    st.markdown("---")

    # Zeitraum wählen
    st.subheader("📅 Zeitraum")

    date_range = st.date_input(
        "Von - Bis",
        value=(
            datetime.now() - timedelta(days=7),
            datetime.now()
        ),
        max_value=datetime.now()
    )

    if len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = date_range[0]
        end_date = datetime.now()

    st.markdown("---")

    # Datentyp wählen
    st.subheader("📊 Anzeigen")
    show_prl = st.checkbox("k*Delta f (PRL)", value=True)
    show_affr = st.checkbox("Aktivierte aFRR (SRL)", value=True)

    st.markdown("---")

    # ÜNB Filter
    st.subheader("🔌 Übertragungsnetzbetreiber")
    show_gesamt = st.checkbox("Deutschland (Gesamt)", value=True)
    show_50hz = st.checkbox("50Hertz", value=False)
    show_amprion = st.checkbox("Amprion", value=False)
    show_tennet = st.checkbox("TenneT", value=False)
    show_transnet = st.checkbox("TransnetBW", value=False)


# Daten laden
@st.cache_data(ttl=3600)
def load_data(source, start, end):
    """Lädt Daten basierend auf gewählter Quelle"""

    if source == "Demo-Daten generieren":
        # Generiere Demo-Daten
        dates = pd.date_range(start=start, end=end, freq='15min')

        prl_data = pd.DataFrame({
            'Timestamp': dates,
            'Deutschland_Positiv_MW': np.random.normal(0, 20, len(dates)),
            'Deutschland_Negativ_MW': np.random.normal(0, 20, len(dates)),
            '50Hertz_MW': np.random.normal(0, 8, len(dates)),
            'Amprion_MW': np.random.normal(0, 10, len(dates)),
            'TenneT_MW': np.random.normal(0, 9, len(dates)),
            'TransnetBW_MW': np.random.normal(0, 7, len(dates))
        }).set_index('Timestamp')

        affr_data = pd.DataFrame({
            'Timestamp': dates,
            'Deutschland_Positiv_MW': np.random.exponential(50, len(dates)).clip(0, 800),
            'Deutschland_Negativ_MW': np.random.exponential(30, len(dates)).clip(0, 500),
            '50Hertz_Positiv_MW': np.random.exponential(15, len(dates)),
            'Amprion_Positiv_MW': np.random.exponential(18, len(dates)),
            'TenneT_Positiv_MW': np.random.exponential(16, len(dates)),
            'TransnetBW_Positiv_MW': np.random.exponential(12, len(dates))
        }).set_index('Timestamp')

        return prl_data, affr_data

    elif source == "CSV importieren":
        return None, None

    elif source == "Live abrufen (API)":
        if FETCHER_AVAILABLE:
            processor = RegelenergieDataProcessor()
            data = processor.load_data(start, end)
            return data['prl'], data['affr']
        else:
            st.error("Regelenergie Fetcher nicht verfügbar!")
            return None, None


# Lade Daten
with st.spinner('📥 Lade Daten...'):
    prl_data, affr_data = load_data(data_source, start_date, end_date)

# CSV Upload (falls gewählt)
if data_source == "CSV importieren":
    st.subheader("📁 CSV-Dateien hochladen")

    col1, col2 = st.columns(2)

    with col1:
        prl_file = st.file_uploader("PRL-Daten (CSV)", type=['csv'])
        if prl_file:
            prl_data = pd.read_csv(prl_file, sep=';', decimal=',', parse_dates=[0], index_col=0)
            st.success(f"✅ {len(prl_data)} PRL-Datensätze geladen")

    with col2:
        affr_file = st.file_uploader("aFRR-Daten (CSV)", type=['csv'])
        if affr_file:
            affr_data = pd.read_csv(affr_file, sep=';', decimal=',', parse_dates=[0], index_col=0)
            st.success(f"✅ {len(affr_data)} aFRR-Datensätze geladen")

# Hauptbereich
if prl_data is not None or affr_data is not None:

    # KPIs
    st.header("📈 Kennzahlen")

    kpi_cols = st.columns(4)

    if prl_data is not None and show_prl:
        with kpi_cols[0]:
            st.metric(
                "PRL Ø Positiv",
                f"{prl_data['Deutschland_Positiv_MW'].mean():.1f} MW",
                delta=f"{prl_data['Deutschland_Positiv_MW'].std():.1f} MW σ"
            )

        with kpi_cols[1]:
            st.metric(
                "PRL Maximum",
                f"{prl_data['Deutschland_Positiv_MW'].max():.1f} MW",
                delta=f"{prl_data['Deutschland_Negativ_MW'].min():.1f} MW (min)"
            )

    if affr_data is not None and show_affr:
        with kpi_cols[2]:
            st.metric(
                "aFRR Ø Aktivierung",
                f"{affr_data['Deutschland_Positiv_MW'].mean():.1f} MW",
                delta=f"{(affr_data['Deutschland_Positiv_MW'] > 0).sum() / len(affr_data) * 100:.1f}% aktiv"
            )

        with kpi_cols[3]:
            total_energy = affr_data['Deutschland_Positiv_MW'].sum() * 0.25  # MWh (15min-Intervalle)
            st.metric(
                "Gesamt Energie",
                f"{total_energy:.0f} MWh",
                delta=f"{affr_data['Deutschland_Positiv_MW'].max():.0f} MW (max)"
            )

    st.markdown("---")

    # Zeitreihen-Plots
    st.header("📊 Zeitreihen")

    # PRL Plot
    if prl_data is not None and show_prl:
        st.subheader("k*Delta f (PRL) - Primärregelleistung")

        fig_prl = go.Figure()

        if show_gesamt:
            fig_prl.add_trace(go.Scatter(
                x=prl_data.index,
                y=prl_data['Deutschland_Positiv_MW'],
                mode='lines',
                name='Deutschland Positiv',
                line=dict(color='green', width=2)
            ))
            fig_prl.add_trace(go.Scatter(
                x=prl_data.index,
                y=prl_data['Deutschland_Negativ_MW'],
                mode='lines',
                name='Deutschland Negativ',
                line=dict(color='red', width=2)
            ))

        if show_50hz:
            fig_prl.add_trace(go.Scatter(
                x=prl_data.index,
                y=prl_data['50Hertz_MW'],
                mode='lines',
                name='50Hertz',
                line=dict(dash='dash')
            ))

        if show_amprion:
            fig_prl.add_trace(go.Scatter(
                x=prl_data.index,
                y=prl_data['Amprion_MW'],
                mode='lines',
                name='Amprion',
                line=dict(dash='dash')
            ))

        if show_tennet:
            fig_prl.add_trace(go.Scatter(
                x=prl_data.index,
                y=prl_data['TenneT_MW'],
                mode='lines',
                name='TenneT',
                line=dict(dash='dash')
            ))

        if show_transnet:
            fig_prl.add_trace(go.Scatter(
                x=prl_data.index,
                y=prl_data['TransnetBW_MW'],
                mode='lines',
                name='TransnetBW',
                line=dict(dash='dash')
            ))

        fig_prl.update_layout(
            xaxis_title="Zeitpunkt",
            yaxis_title="Leistung (MW)",
            hovermode='x unified',
            height=500,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        st.plotly_chart(fig_prl, use_container_width=True)

    # aFRR Plot
    if affr_data is not None and show_affr:
        st.subheader("Aktivierte aFRR (SRL) - Sekundärregelleistung")

        fig_affr = go.Figure()

        if show_gesamt:
            fig_affr.add_trace(go.Scatter(
                x=affr_data.index,
                y=affr_data['Deutschland_Positiv_MW'],
                mode='lines',
                name='Deutschland Positiv',
                fill='tozeroy',
                line=dict(color='blue', width=2)
            ))

        if show_50hz and '50Hertz_Positiv_MW' in affr_data.columns:
            fig_affr.add_trace(go.Scatter(
                x=affr_data.index,
                y=affr_data['50Hertz_Positiv_MW'],
                mode='lines',
                name='50Hertz',
                line=dict(dash='dash')
            ))

        if show_amprion and 'Amprion_Positiv_MW' in affr_data.columns:
            fig_affr.add_trace(go.Scatter(
                x=affr_data.index,
                y=affr_data['Amprion_Positiv_MW'],
                mode='lines',
                name='Amprion',
                line=dict(dash='dash')
            ))

        fig_affr.update_layout(
            xaxis_title="Zeitpunkt",
            yaxis_title="Aktivierte Leistung (MW)",
            hovermode='x unified',
            height=500,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        st.plotly_chart(fig_affr, use_container_width=True)

    st.markdown("---")

    # Analysen
    st.header("🔬 Statistische Analysen")

    tab1, tab2, tab3 = st.tabs(["Verteilungen", "Tagesprofile", "Heatmap"])

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            if prl_data is not None and show_prl:
                st.subheader("PRL Verteilung")
                fig_hist_prl = px.histogram(
                    prl_data,
                    x='Deutschland_Positiv_MW',
                    nbins=50,
                    title="Häufigkeitsverteilung PRL"
                )
                st.plotly_chart(fig_hist_prl, use_container_width=True)

        with col2:
            if affr_data is not None and show_affr:
                st.subheader("aFRR Verteilung")
                fig_hist_affr = px.histogram(
                    affr_data,
                    x='Deutschland_Positiv_MW',
                    nbins=50,
                    title="Häufigkeitsverteilung aFRR"
                )
                st.plotly_chart(fig_hist_affr, use_container_width=True)

    with tab2:
        if prl_data is not None and show_prl:
            st.subheader("PRL Tagesprofil")

            # Durchschnittliches Tagesprofil
            prl_hourly = prl_data.groupby(prl_data.index.hour).mean()

            fig_daily = go.Figure()
            fig_daily.add_trace(go.Scatter(
                x=prl_hourly.index,
                y=prl_hourly['Deutschland_Positiv_MW'],
                mode='lines+markers',
                name='Ø Positiv',
                line=dict(color='green')
            ))
            fig_daily.add_trace(go.Scatter(
                x=prl_hourly.index,
                y=prl_hourly['Deutschland_Negativ_MW'],
                mode='lines+markers',
                name='Ø Negativ',
                line=dict(color='red')
            ))
            fig_daily.update_layout(
                xaxis_title="Stunde des Tages",
                yaxis_title="Durchschnittliche Leistung (MW)",
                xaxis=dict(tickmode='linear', tick0=0, dtick=2)
            )
            st.plotly_chart(fig_daily, use_container_width=True)

    with tab3:
        if affr_data is not None and show_affr:
            st.subheader("aFRR Aktivierungs-Heatmap")

            # Erstelle Pivot für Heatmap (Stunde x Wochentag)
            affr_data_copy = affr_data.copy()
            affr_data_copy['hour'] = affr_data_copy.index.hour
            affr_data_copy['weekday'] = affr_data_copy.index.dayofweek

            heatmap_data = affr_data_copy.pivot_table(
                values='Deutschland_Positiv_MW',
                index='weekday',
                columns='hour',
                aggfunc='mean'
            )

            fig_heatmap = px.imshow(
                heatmap_data,
                labels=dict(x="Stunde", y="Wochentag", color="MW"),
                y=['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'],
                aspect="auto",
                color_continuous_scale="YlOrRd"
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)

    st.markdown("---")

    # Daten-Export
    st.header("💾 Daten exportieren")

    col1, col2 = st.columns(2)

    with col1:
        if prl_data is not None and show_prl:
            csv_prl = prl_data.to_csv()
            st.download_button(
                label="📥 PRL als CSV",
                data=csv_prl,
                file_name=f"prl_data_{start_date}_{end_date}.csv",
                mime="text/csv"
            )

    with col2:
        if affr_data is not None and show_affr:
            csv_affr = affr_data.to_csv()
            st.download_button(
                label="📥 aFRR als CSV",
                data=csv_affr,
                file_name=f"affr_data_{start_date}_{end_date}.csv",
                mime="text/csv"
            )

else:
    st.info("👈 Bitte wähle eine Datenquelle in der Sidebar und lade Daten")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: gray;'>
        <p>DomJek Energiemarktdarstellung v2.0 | 
        Datenquelle: <a href='https://www.netztransparenz.de'>netztransparenz.de</a></p>
    </div>
""", unsafe_allow_html=True)