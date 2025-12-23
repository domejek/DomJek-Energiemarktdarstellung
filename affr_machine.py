#!/usr/bin/env python3
"""
aFRR Leistungspreis-Prognosemodell für den deutschen Regelenergiemarkt
Entwickelt optimale Gebotspreise für maximalen Ertrag
"""

import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import warnings

warnings.filterwarnings('ignore')

# Machine Learning und Optimierung
try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.model_selection import TimeSeriesSplit, cross_val_score
    import xgboost as xgb
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from scipy.optimize import minimize, differential_evolution
    import matplotlib.pyplot as plt
    import seaborn as sns
except ImportError as e:
    print(f"Fehlende Abhängigkeiten: {e}")
    print("Installieren Sie: pip install scikit-learn xgboost scipy matplotlib seaborn")
    exit(1)

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class aFRRPricePredictor:
    """
    Prognosemodell für optimale aFRR Leistungspreise
    Berücksichtigt Marktdynamik, Konkurrenz und Ertragsmöglichkeiten
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialisierung des Prognosemodells

        Args:
            config: Konfiguration mit Modellparametern und Marktdaten
        """
        self.config = config
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        self.prediction_history = []
        self.market_data = None

        # Modellauswahl basierend auf Konfiguration
        self._initialize_models()

    def _initialize_models(self):
        """Initialisiert verschiedene ML-Modelle"""
        self.models = {
            'random_forest': RandomForestRegressor(
                n_estimators=100,
                max_depth=15,
                min_samples_split=5,
                random_state=42
            ),
            'gradient_boosting': GradientBoostingRegressor(
                n_estimators=100,
                max_depth=8,
                learning_rate=0.1,
                random_state=42
            ),
            'xgboost': xgb.XGBRegressor(
                n_estimators=100,
                max_depth=8,
                learning_rate=0.1,
                random_state=42
            ),
            'ridge': Ridge(alpha=1.0),
            'linear': LinearRegression()
        }

        # Scaler für Features
        self.scalers = {
            'standard': StandardScaler(),
            'minmax': MinMaxScaler()
        }

    def load_market_data(self, data_sources: Dict[str, str]) -> pd.DataFrame:
        """
        Lädt und kombiniert Marktdaten aus verschiedenen Quellen

        Args:
            data_sources: Dictionary mit Pfaden zu Datenquellen

        Returns:
            Kombinierter DataFrame mit allen Marktdaten
        """
        logger.info("Lade Marktdaten...")

        market_df = pd.DataFrame()

        try:
            # aFRR Auktionsdaten laden
            if 'afrr_auctions' in data_sources:
                afrr_data = pd.read_csv(data_sources['afrr_auctions'])
                afrr_data['datetime'] = pd.to_datetime(afrr_data['datetime'])
                market_df = afrr_data.copy()

            # Stromnachfrage/Last-Daten
            if 'load_data' in data_sources:
                load_data = pd.read_csv(data_sources['load_data'])
                load_data['datetime'] = pd.to_datetime(load_data['datetime'])
                market_df = market_df.merge(load_data, on='datetime', how='left')

            # Wetterdaten (Wind, Solar)
            if 'weather_data' in data_sources:
                weather_data = pd.read_csv(data_sources['weather_data'])
                weather_data['datetime'] = pd.to_datetime(weather_data['datetime'])
                market_df = market_df.merge(weather_data, on='datetime', how='left')

            # Spot-Marktpreise
            if 'spot_prices' in data_sources:
                spot_data = pd.read_csv(data_sources['spot_prices'])
                spot_data['datetime'] = pd.to_datetime(spot_data['datetime'])
                market_df = market_df.merge(spot_data, on='datetime', how='left')

        except Exception as e:
            logger.error(f"Fehler beim Laden der Marktdaten: {e}")
            # Fallback: Generiere Beispieldaten
            market_df = self._generate_sample_data()

        # Fallback falls keine Daten geladen wurden
        if market_df.empty or 'datetime' not in market_df.columns:
            logger.warning("Keine Marktdaten geladen, generiere Beispieldaten.")
            market_df = self._generate_sample_data()

        # Daten bereinigen und sortieren
        market_df = market_df.sort_values('datetime').reset_index(drop=True)
        market_df = self._clean_data(market_df)

        self.market_data = market_df
        logger.info(f"Marktdaten geladen: {len(market_df)} Datenpunkte")

        return market_df

    def _generate_sample_data(self) -> pd.DataFrame:
        """Generiert Beispiel-Marktdaten für Demonstration"""
        logger.info("Generiere Beispiel-Marktdaten...")

        # Zeitraum der letzten 12 Monate, 15-Minuten-Auflösung
        start_date = datetime.now() - timedelta(days=365)
        dates = pd.date_range(start_date, datetime.now(), freq='15T')

        np.random.seed(42)
        n_samples = len(dates)

        # Basis-Trends und saisonale Muster
        hour_of_day = dates.hour
        day_of_week = dates.dayofweek
        month = dates.month

        # Simulierte Marktdaten
        data = {
            'datetime': dates,
            'clearing_price_pos': np.random.lognormal(3, 0.8, n_samples) +
                                  10 * np.sin(2 * np.pi * hour_of_day / 24) +
                                  5 * (day_of_week < 5),  # Werktag-Effekt
            'clearing_price_neg': np.random.lognormal(2.5, 0.7, n_samples) +
                                  8 * np.sin(2 * np.pi * hour_of_day / 24),
            'demand_mw': 30000 + 15000 * np.sin(2 * np.pi * hour_of_day / 24) +
                         np.random.normal(0, 2000, n_samples),
            'wind_forecast_mw': np.maximum(0, 8000 + 6000 * np.random.normal(0, 1, n_samples)),
            'solar_forecast_mw': np.maximum(0, 4000 * np.maximum(0, np.sin(np.pi * (hour_of_day - 6) / 12)) +
                                            np.random.normal(0, 500, n_samples)),
            'spot_price_eur_mwh': 50 + 30 * np.sin(2 * np.pi * hour_of_day / 24) +
                                  np.random.normal(0, 15, n_samples),
            'reserve_demand_pos': np.random.exponential(500, n_samples),
            'reserve_demand_neg': np.random.exponential(400, n_samples),
            'marginal_price_pos': np.random.lognormal(4, 0.6, n_samples),
            'marginal_price_neg': np.random.lognormal(3.5, 0.5, n_samples)
        }

        return pd.DataFrame(data)

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Bereinigt und validiert Marktdaten"""
        # Fehlende Werte behandeln
        df = df.fillna(method='ffill').fillna(method='bfill')

        # Outlier entfernen (z.B. negative Preise über -1000 €/MWh)
        price_cols = [col for col in df.columns if 'price' in col.lower()]
        for col in price_cols:
            if col in df.columns:
                df[col] = df[col].clip(lower=-1000, upper=3000)

        # Zeitbasierte Features hinzufügen
        df = self._add_time_features(df)

        return df

    def _add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fügt zeitbasierte Features hinzu"""
        df['hour'] = df['datetime'].dt.hour
        df['day_of_week'] = df['datetime'].dt.dayofweek
        df['month'] = df['datetime'].dt.month
        df['quarter'] = df['datetime'].dt.quarter
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        df['is_peak_hour'] = ((df['hour'] >= 8) & (df['hour'] <= 20)).astype(int)

        # Saisonale Zyklen
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)

        return df

    def create_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """
        Erstellt Features für ML-Modelle

        Args:
            df: Eingangsdaten

        Returns:
            Feature DataFrame und Liste der Feature-Namen
        """
        feature_df = df.copy()

        # Lag-Features (historische Werte)
        lag_periods = [1, 2, 4, 8, 24, 96]  # 15min, 30min, 1h, 2h, 6h, 24h
        price_cols = ['clearing_price_pos', 'clearing_price_neg', 'marginal_price_pos', 'marginal_price_neg']

        for col in price_cols:
            if col in feature_df.columns:
                for lag in lag_periods:
                    feature_df[f'{col}_lag_{lag}'] = feature_df[col].shift(lag)

        # Rolling-Window Features
        windows = [4, 8, 24, 96]  # 1h, 2h, 6h, 24h
        for col in price_cols + ['demand_mw', 'wind_forecast_mw', 'solar_forecast_mw']:
            if col in feature_df.columns:
                for window in windows:
                    feature_df[f'{col}_mean_{window}'] = feature_df[col].rolling(window).mean()
                    feature_df[f'{col}_std_{window}'] = feature_df[col].rolling(window).std()
                    feature_df[f'{col}_min_{window}'] = feature_df[col].rolling(window).min()
                    feature_df[f'{col}_max_{window}'] = feature_df[col].rolling(window).max()

        # Markt-Spread Features
        if 'clearing_price_pos' in feature_df.columns and 'clearing_price_neg' in feature_df.columns:
            feature_df['price_spread'] = feature_df['clearing_price_pos'] - feature_df['clearing_price_neg']
            feature_df['price_ratio'] = feature_df['clearing_price_pos'] / (feature_df['clearing_price_neg'] + 1e-6)

        # Erneuerbaren-Anteil
        if all(col in feature_df.columns for col in ['wind_forecast_mw', 'solar_forecast_mw', 'demand_mw']):
            feature_df['renewable_share'] = (feature_df['wind_forecast_mw'] + feature_df['solar_forecast_mw']) / \
                                            feature_df['demand_mw']
            feature_df['renewable_surplus'] = feature_df['wind_forecast_mw'] + feature_df['solar_forecast_mw'] - \
                                              feature_df['demand_mw']

        # Residuallast
        if 'demand_mw' in feature_df.columns and 'wind_forecast_mw' in feature_df.columns:
            feature_df['residual_load'] = feature_df['demand_mw'] - feature_df['wind_forecast_mw'] - feature_df.get(
                'solar_forecast_mw', 0)

        # Feature-Liste erstellen (numerische Features)
        feature_cols = [col for col in feature_df.columns
                        if col not in ['datetime'] and
                        feature_df[col].dtype in ['int64', 'float64'] and
                        not col.startswith('clearing_price') and
                        not col.startswith('marginal_price')]

        # NaN-Werte entfernen
        feature_df = feature_df.dropna()

        logger.info(f"Features erstellt: {len(feature_cols)} Features, {len(feature_df)} Samples")

        return feature_df, feature_cols

    def train_models(self, df: pd.DataFrame, target_col: str = 'clearing_price_pos') -> Dict[str, Any]:
        """
        Trainiert alle Modelle für Preisprognose

        Args:
            df: Trainingsdaten
            target_col: Zielvariable

        Returns:
            Trainingsergebnisse und Metriken
        """
        logger.info(f"Trainiere Modelle für {target_col}...")

        # Features erstellen
        feature_df, feature_cols = self.create_features(df)

        if target_col not in feature_df.columns:
            raise ValueError(f"Zielvariable {target_col} nicht in Daten gefunden")

        # Train-Test Split (zeitbasiert)
        split_idx = int(len(feature_df) * 0.8)
        train_df = feature_df.iloc[:split_idx]
        test_df = feature_df.iloc[split_idx:]

        X_train = train_df[feature_cols]
        y_train = train_df[target_col]
        X_test = test_df[feature_cols]
        y_test = test_df[target_col]

        results = {}

        # Modelle trainieren und evaluieren
        for name, model in self.models.items():
            try:
                logger.info(f"Trainiere {name}...")

                # Feature Scaling für lineare Modelle
                if name in ['ridge', 'linear']:
                    scaler = self.scalers['standard']
                    X_train_scaled = scaler.fit_transform(X_train)
                    X_test_scaled = scaler.transform(X_test)

                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                else:
                    model.fit(X_train, y_train)
                    y_pred = model.predict(X_test)

                # Metriken berechnen
                mae = mean_absolute_error(y_test, y_pred)
                mse = mean_squared_error(y_test, y_pred)
                rmse = np.sqrt(mse)
                r2 = r2_score(y_test, y_pred)

                # Feature Importance (falls verfügbar)
                importance = None
                if hasattr(model, 'feature_importances_'):
                    importance = dict(zip(feature_cols, model.feature_importances_))
                elif hasattr(model, 'coef_'):
                    importance = dict(zip(feature_cols, np.abs(model.coef_)))

                results[name] = {
                    'model': model,
                    'mae': mae,
                    'rmse': rmse,
                    'r2': r2,
                    'feature_importance': importance,
                    'predictions': y_pred,
                    'actuals': y_test
                }

                logger.info(f"{name}: MAE={mae:.2f}, RMSE={rmse:.2f}, R²={r2:.3f}")

            except Exception as e:
                logger.error(f"Fehler beim Training von {name}: {e}")

        # Bestes Modell auswählen
        best_model_name = min(results.keys(), key=lambda x: results[x]['mae'])
        logger.info(f"Bestes Modell: {best_model_name}")

        return {
            'results': results,
            'best_model': best_model_name,
            'feature_cols': feature_cols,
            'target_col': target_col
        }

    def predict_prices(self, model_results: Dict[str, Any],
                       forecast_hours: int = 24) -> pd.DataFrame:
        """
        Prognostiziert Preise für die nächsten Stunden

        Args:
            model_results: Trainingsergebnisse
            forecast_hours: Anzahl Stunden für Prognose

        Returns:
            DataFrame mit Preisprognosen
        """
        best_model_name = model_results['best_model']
        best_model = model_results['results'][best_model_name]['model']
        feature_cols = model_results['feature_cols']

        # Letzte verfügbare Daten für Prognose
        latest_data = self.market_data.tail(96 * 7)  # Letzten 7 Tage

        predictions = []
        current_time = self.market_data['datetime'].max() + timedelta(minutes=15)

        for h in range(forecast_hours * 4):  # 15-Min Intervalle
            # Features für aktuellen Zeitpunkt erstellen
            forecast_time = current_time + timedelta(minutes=15 * h)

            # Basis-Features aus zeitlichen Informationen
            hour = forecast_time.hour
            day_of_week = forecast_time.dayofweek
            month = forecast_time.month

            # Dummy-Features erstellen (in Praxis: echte Vorhersagen)
            feature_dict = {
                'hour': hour,
                'day_of_week': day_of_week,
                'month': month,
                'is_weekend': int(day_of_week >= 5),
                'is_peak_hour': int(8 <= hour <= 20),
                'hour_sin': np.sin(2 * np.pi * hour / 24),
                'hour_cos': np.cos(2 * np.pi * hour / 24),
                'day_sin': np.sin(2 * np.pi * day_of_week / 7),
                'day_cos': np.cos(2 * np.pi * day_of_week / 7),
                'month_sin': np.sin(2 * np.pi * month / 12),
                'month_cos': np.cos(2 * np.pi * month / 12)
            }

            # Fülle fehlende Features mit Durchschnittswerten
            for col in feature_cols:
                if col not in feature_dict:
                    if col in self.market_data.columns:
                        feature_dict[col] = self.market_data[col].mean()
                    else:
                        feature_dict[col] = 0

            # Prognose erstellen
            feature_vector = np.array([feature_dict[col] for col in feature_cols]).reshape(1, -1)
            price_pred = best_model.predict(feature_vector)[0]

            predictions.append({
                'datetime': forecast_time,
                'predicted_price': max(0, price_pred),  # Negative Preise begrenzen
                'hour': hour,
                'confidence': self._calculate_confidence(model_results, feature_vector)
            })

        return pd.DataFrame(predictions)

    def _calculate_confidence(self, model_results: Dict[str, Any],
                              feature_vector: np.ndarray) -> float:
        """Berechnet Konfidenzintervall für Prognose"""
        # Vereinfachte Konfidenzberechnung basierend auf Modellvarianz
        best_model_name = model_results['best_model']
        mae = model_results['results'][best_model_name]['mae']

        # Konfidenz als Funktion des MAE (vereinfacht)
        confidence = max(0.5, 1 - (mae / 100))  # Annahme: MAE in €/MWh
        return confidence

    def optimize_bidding_strategy(self, price_forecast: pd.DataFrame,
                                  capacity_mw: float = 10.0) -> Dict[str, Any]:
        """
        Optimiert Gebotsstrategie für maximalen Ertrag

        Args:
            price_forecast: Preisprognosen
            capacity_mw: Verfügbare Kapazität in MW

        Returns:
            Optimale Gebotsstrategie
        """
        logger.info("Optimiere Gebotsstrategie...")

        def objective_function(bid_prices: np.ndarray) -> float:
            """Zielfunktion: Minimiere negativen erwarteten Ertrag"""
            total_revenue = 0

            for i, (_, row) in enumerate(price_forecast.iterrows()):
                if i >= len(bid_prices):
                    break

                bid_price = bid_prices[i]
                market_price = row['predicted_price']
                confidence = row['confidence']

                # Zuschlagswahrscheinlichkeit (vereinfachtes Modell)
                award_prob = self._calculate_award_probability(bid_price, market_price)

                # Erwarteter Ertrag für diese Periode
                expected_revenue = award_prob * bid_price * capacity_mw * 0.25  # 15-Min Perioden

                # Gewichtung mit Konfidenz
                total_revenue += expected_revenue * confidence

            return -total_revenue  # Minimierung = Maximierung des Ertrags

        # Optimierungsparameter
        n_periods = min(len(price_forecast), 96)  # Max. 24 Stunden

        # Grenzen für Gebotspreise (€/MW)
        bounds = [(0, 3000) for _ in range(n_periods)]

        # Startschätzung basierend auf Prognosen
        initial_guess = price_forecast['predicted_price'].head(n_periods).values * 0.9

        # Optimierung durchführen
        result = minimize(
            objective_function,
            initial_guess,
            method='L-BFGS-B',
            bounds=bounds,
            options={'maxiter': 1000}
        )

        if result.success:
            optimal_bids = result.x
            expected_revenue = -result.fun

            logger.info(f"Optimierung erfolgreich: Erwarteter Ertrag = {expected_revenue:.2f} €")
        else:
            logger.warning("Optimierung nicht konvergiert, verwende Fallback-Strategie")
            optimal_bids = price_forecast['predicted_price'].head(n_periods).values * 0.85
            expected_revenue = 0

        # Ergebnisse strukturieren
        strategy = pd.DataFrame({
            'datetime': price_forecast['datetime'].head(n_periods),
            'predicted_price': price_forecast['predicted_price'].head(n_periods),
            'optimal_bid': optimal_bids,
            'bid_markup': (optimal_bids / price_forecast['predicted_price'].head(n_periods) - 1) * 100,
            'award_probability': [self._calculate_award_probability(bid, pred)
                                  for bid, pred in zip(optimal_bids,
                                                       price_forecast['predicted_price'].head(n_periods))],
            'expected_revenue': [prob * bid * capacity_mw * 0.25
                                 for prob, bid in zip(
                    [self._calculate_award_probability(bid, pred)
                     for bid, pred in zip(optimal_bids,
                                          price_forecast['predicted_price'].head(n_periods))],
                    optimal_bids)]
        })

        return {
            'strategy': strategy,
            'total_expected_revenue': expected_revenue,
            'optimization_success': result.success,
            'capacity_mw': capacity_mw,
            'summary': {
                'avg_bid_price': np.mean(optimal_bids),
                'avg_markup': np.mean(strategy['bid_markup']),
                'avg_award_prob': np.mean(strategy['award_probability']),
                'total_periods': n_periods
            }
        }

    def _calculate_award_probability(self, bid_price: float, market_price: float) -> float:
        """
        Berechnet Zuschlagswahrscheinlichkeit basierend auf Gebotspreisen

        Args:
            bid_price: Gebotspreis
            market_price: Prognostizierter Marktpreis

        Returns:
            Wahrscheinlichkeit des Zuschlags (0-1)
        """
        # Vereinfachtes Modell: Logistische Funktion
        # In der Praxis: Basiert auf historischen Zuschlagsdaten

        if bid_price <= 0:
            return 0.0

        # Relative Position zum Marktpreis
        relative_price = bid_price / max(market_price, 1.0)

        # Logistische Funktion für Zuschlagswahrscheinlichkeit
        # Niedrigere Preise = höhere Wahrscheinlichkeit
        prob = 1 / (1 + np.exp(5 * (relative_price - 0.8)))

        return max(0.0, min(1.0, prob))

    def backtest_strategy(self, historical_data: pd.DataFrame,
                          lookback_days: int = 30) -> Dict[str, Any]:
        """
        Backtesting der Gebotsstrategie

        Args:
            historical_data: Historische Marktdaten
            lookback_days: Tage für rollende Prognose

        Returns:
            Backtesting-Ergebnisse
        """
        logger.info("Starte Backtesting...")

        results = []
        total_revenue = 0

        # Rolling Window Backtesting
        for i in range(lookback_days, len(historical_data) - 96, 96):  # Täglich
            # Trainingsdaten
            train_data = historical_data.iloc[i - lookback_days * 96:i]

            # Modell trainieren
            try:
                model_results = self.train_models(train_data, 'clearing_price_pos')

                # Prognose für nächsten Tag
                forecast = self.predict_prices(model_results, forecast_hours=24)

                # Strategie optimieren
                strategy = self.optimize_bidding_strategy(forecast)

                # Actual Preise für Evaluation
                actual_data = historical_data.iloc[i:i + 96]  # Nächste 24h

                # Performance berechnen
                daily_revenue = 0
                for j, (_, row) in enumerate(strategy['strategy'].iterrows()):
                    if j < len(actual_data):
                        actual_price = actual_data.iloc[j]['clearing_price_pos']
                        bid_price = row['optimal_bid']

                        # Zuschlag wenn Gebot unter Clearing Price
                        if bid_price <= actual_price:
                            daily_revenue += bid_price * 10 * 0.25  # 10 MW, 15min

                total_revenue += daily_revenue

                results.append({
                    'date': historical_data.iloc[i]['datetime'].date(),
                    'daily_revenue': daily_revenue,
                    'avg_bid_price': strategy['summary']['avg_bid_price'],
                    'avg_market_price': actual_data['clearing_price_pos'].mean()
                })

            except Exception as e:
                logger.error(f"Fehler im Backtesting für Tag {i}: {e}")

        # Zusammenfassung
        if results:
            results_df = pd.DataFrame(results)

            summary = {
                'total_revenue': total_revenue,
                'avg_daily_revenue': results_df['daily_revenue'].mean(),
                'revenue_std': results_df['daily_revenue'].std(),
                'profitable_days': (results_df['daily_revenue'] > 0).sum(),
                'total_days': len(results_df),
                'success_rate': (results_df['daily_revenue'] > 0).mean(),
                'results': results_df
            }

            logger.info(f"Backtesting abgeschlossen: {summary['total_revenue']:.2f}€ Gesamtertrag")
            return summary
        else:
            return {'error': 'Kein erfolgreiches Backtesting'}

    def generate_report(self, model_results: Dict[str, Any],
                        output_path: Optional[str] = None) -> None:
        """
        Erstellt einen einfachen Bericht über die Modellergebnisse.

        Args:
            model_results: Ergebnisse aus train_models
            output_path: Optionaler Dateipfad für den Bericht (PDF/PNG)
        """
        logger.info("Erstelle Modellbericht...")

        best_model_name = model_results['best_model']
        results = model_results['results'][best_model_name]
        feature_importance = results.get('feature_importance', {})
        y_pred = results.get('predictions', [])
        y_test = results.get('actuals', [])

        # Feature Importance Plot
        if feature_importance:
            fi = pd.Series(feature_importance).sort_values(ascending=False)
            plt.figure(figsize=(8, 4))
            fi.head(20).plot(kind='bar')
            plt.title(f'Feature Importance ({best_model_name})')
            plt.tight_layout()
            if output_path:
                plt.savefig(f"{output_path}_feature_importance.png")
            else:
                plt.show()
            plt.close()

        # Scatterplot: Prognose vs. Ist
        if len(y_pred) > 0 and len(y_test) > 0:
            plt.figure(figsize=(6, 6))
            plt.scatter(y_test, y_pred, alpha=0.3)
            plt.xlabel("Ist-Preis")
            plt.ylabel("Prognose-Preis")
            plt.title(f"Vorhersage vs. Ist ({best_model_name})")
            plt.plot([min(y_test), max(y_test)], [min(y_test), max(y_test)], 'r--')
            plt.tight_layout()
            if output_path:
                plt.savefig(f"{output_path}_scatter.png")
            else:
                plt.show()
            plt.close()

        logger.info(f"Modellbericht für {best_model_name} erstellt.")


# --- Hauptprogramm für Ausführung als Skript ---
if __name__ == "__main__":
    # Beispiel-Konfiguration
    config = {}

    predictor = aFRRPricePredictor(config)

    # Beispiel-Daten laden/generieren
    market_data = predictor.load_market_data({})  # Leeres Dict -> Beispieldaten

    # Modelle trainieren
    model_results = predictor.train_models(market_data, target_col='clearing_price_pos')

    # Preise prognostizieren
    forecast = predictor.predict_prices(model_results, forecast_hours=24)

    # Strategie optimieren
    strategy = predictor.optimize_bidding_strategy(forecast)

    # Bericht erzeugen
    predictor.generate_report(model_results)

    print("Optimale Gebotsstrategie (Ausschnitt):")
    print(strategy['strategy'].head())

    print("\nZusammenfassung:")
    print(strategy['summary'])

    # Optional: Backtest
    backtest = predictor.backtest_strategy(market_data, lookback_days=7)
    print("\nBacktest-Ergebnis (Ausschnitt):")
    if 'results' in backtest:
        print(backtest['results'].head())
    else:
        print(backtest)