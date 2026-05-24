"""
predictor.py -- Signal generation and ML prediction engine.

Architecture:
  - Rule engine:  weighted directional signals from 15+ technical indicators
  - ML ensemble: RandomForest + ExtraTrees + HistGradientBoosting (3-model blend)
  - Final blend: 35% rules / 65% ML (ML weighted higher when trained)
  - Features:    15 technical features, 3-day forward target
"""
import warnings
from pathlib import Path
from typing import Optional
import numpy as np
import pandas as pd
from . import indicators as ind

warnings.filterwarnings("ignore")

MODEL_PATH  = Path(__file__).parent.parent / "models" / "stock_model.pkl"
SCALER_PATH = Path(__file__).parent.parent / "models" / "scaler.pkl"

# 15-feature set used for ML training and inference
FEATURE_COLS = [
    # Oscillators
    "rsi", "macd_hist", "bb_pband",
    # Momentum
    "momentum_5d", "momentum_20d", "roc_10d",
    # New oscillators
    "stoch_rsi_k", "stoch_rsi_d", "williams_r",
    # Trend strength
    "adx",
    # Volume
    "volume_ratio", "obv_roc_5d",
    # Volatility (normalised)
    "atr_pct",
    # Price position vs MAs
    "price_vs_ma20_pct", "price_vs_ma50_pct",
]


# ── Model I/O ─────────────────────────────────────────────────────────────────

# Feature columns used by the v1 model (before the upgrade) -- kept for
# backward-compat so old saved models load correctly until the user retrains.
_V1_FEATURE_COLS = [
    "rsi", "macd_hist", "volume_ratio", "bb_pband",
    "momentum_5d", "momentum_20d",
]


def _load_model():
    """Load model bundle and scaler. Returns (bundle, scaler) or (None, None)."""
    try:
        import joblib
        if MODEL_PATH.exists() and SCALER_PATH.exists():
            bundle = joblib.load(MODEL_PATH)
            scaler = joblib.load(SCALER_PATH)
            # Support v1 format (bare RandomForest, not a bundle dict)
            if not isinstance(bundle, dict):
                bundle = {
                    "rf":                 bundle,
                    "et":                 None,
                    "hgbm":              None,
                    "imputer":           None,
                    "feature_cols":      _V1_FEATURE_COLS,
                    "feature_importance": {},
                }
            return bundle, scaler
    except Exception:
        pass
    return None, None


# ── Training ──────────────────────────────────────────────────────────────────

def train_model(all_hists: dict[str, pd.DataFrame]) -> tuple[bool, dict]:
    """
    Train a 3-model ensemble on pooled historical data.
    Returns (success, feature_importance_dict).
    """
    try:
        import joblib
        import warnings as _w
        # Suppress noisy sklearn/joblib parallel configuration warnings
        _w.filterwarnings("ignore", category=UserWarning, module="sklearn")
        from sklearn.ensemble import (
            RandomForestClassifier,
            ExtraTreesClassifier,
            HistGradientBoostingClassifier,
        )
        from sklearn.preprocessing import StandardScaler
        from sklearn.impute import SimpleImputer

        frames = []
        for symbol, hist in all_hists.items():
            if len(hist) < 80:
                continue
            enriched = ind.enrich(hist.copy())
            enriched = enriched.dropna(subset=["target"])
            available = [c for c in FEATURE_COLS if c in enriched.columns]
            frames.append(enriched[available + ["target"]])

        if not frames:
            return False, {}

        combined = pd.concat(frames, ignore_index=True)
        available_cols = [c for c in FEATURE_COLS if c in combined.columns]

        X_raw = combined[available_cols].values.astype(float)
        y     = combined["target"].values

        # Impute NaN (early rows without enough history)
        imputer = SimpleImputer(strategy="median")
        X_imp   = imputer.fit_transform(X_raw)

        # Scale for RF/ET (HistGBM doesn't need it but it won't hurt)
        scaler   = StandardScaler()
        X_scaled = scaler.fit_transform(X_imp)

        # -- Model 1: Random Forest -------------------------------------------
        rf = RandomForestClassifier(
            n_estimators=300, max_depth=8, min_samples_leaf=8,
            max_features="sqrt", random_state=42, n_jobs=-1,
        )
        rf.fit(X_scaled, y)

        # -- Model 2: Extra Trees (lower variance, high diversity) -------------
        et = ExtraTreesClassifier(
            n_estimators=300, max_depth=8, min_samples_leaf=8,
            max_features="sqrt", random_state=43, n_jobs=-1,
        )
        et.fit(X_scaled, y)

        # -- Model 3: Gradient Boosting (sequential, often best on tabular) ---
        hgbm = HistGradientBoostingClassifier(
            max_iter=300, max_depth=6, min_samples_leaf=10,
            learning_rate=0.04, l2_regularization=0.1, random_state=44,
        )
        hgbm.fit(X_scaled, y)

        # Feature importance: average of RF and ET (GBM importance is different scale)
        fi = {}
        for i, col in enumerate(available_cols):
            fi[col] = round(float(rf.feature_importances_[i] * 0.5 +
                                  et.feature_importances_[i] * 0.5), 4)

        bundle = {
            "rf":                 rf,
            "et":                 et,
            "hgbm":               hgbm,
            "imputer":            imputer,
            "feature_cols":       available_cols,
            "feature_importance": fi,
            "n_samples":          len(y),
            "n_stocks":           len(frames),
        }
        MODEL_PATH.parent.mkdir(exist_ok=True)
        joblib.dump(bundle, MODEL_PATH)
        joblib.dump(scaler, SCALER_PATH)
        return True, fi

    except Exception as e:
        print(f"Training failed: {e}")
        import traceback; traceback.print_exc()
        return False, {}


# ── Inference ─────────────────────────────────────────────────────────────────

def _ml_predict(features: dict) -> Optional[float]:
    """Run the 3-model ensemble and return blended probability (0-1)."""
    bundle, scaler = _load_model()
    if bundle is None:
        return None
    try:
        feature_cols = bundle.get("feature_cols", FEATURE_COLS)
        vals = [features.get(col, np.nan) for col in feature_cols]
        X = np.array(vals, dtype=float).reshape(1, -1)

        # Impute
        imputer = bundle.get("imputer")
        if imputer is not None:
            X = imputer.transform(X)
        else:
            X = np.nan_to_num(X, nan=0.0)

        X_scaled = scaler.transform(X)

        rf   = bundle["rf"]
        et   = bundle.get("et")
        hgbm = bundle.get("hgbm")

        prob_rf   = rf.predict_proba(X_scaled)[0][1]
        prob_et   = et.predict_proba(X_scaled)[0][1]   if et   else prob_rf
        prob_hgbm = hgbm.predict_proba(X_scaled)[0][1] if hgbm else prob_rf

        # Blend: GBM slightly higher weight (generally best on tabular data)
        blended = prob_rf * 0.30 + prob_et * 0.30 + prob_hgbm * 0.40
        return round(float(blended), 3)
    except Exception:
        return None


def get_model_feature_importance() -> dict:
    """Return sorted feature importance from the trained model."""
    bundle, _ = _load_model()
    if bundle is None:
        return {}
    fi = bundle.get("feature_importance", {})
    return dict(sorted(fi.items(), key=lambda x: x[1], reverse=True))


def get_model_metadata() -> dict:
    """Return training metadata (n_samples, n_stocks, feature_cols)."""
    bundle, _ = _load_model()
    if bundle is None:
        return {}
    return {
        "n_samples":    bundle.get("n_samples", "?"),
        "n_stocks":     bundle.get("n_stocks", "?"),
        "feature_cols": bundle.get("feature_cols", []),
        "n_features":   len(bundle.get("feature_cols", [])),
    }


# ── Rule-based signal engine ──────────────────────────────────────────────────

def _rule_signals(ind_data: dict, stock_snap: dict,
                  days_to_earnings: Optional[int]) -> list[dict]:
    """
    Generate a list of weighted directional signals from technical indicators.
    Each signal: {name, direction (+1 bull / -1 bear), weight (1-3)}
    """
    signals = []

    # Retrieve indicators
    rsi      = ind_data.get("rsi")
    price    = stock_snap.get("price", 0)
    ma50     = ind_data.get("ma50")
    ma200    = ind_data.get("ma200")
    macd     = ind_data.get("macd")
    macd_sig = ind_data.get("macd_signal")
    macd_hist= ind_data.get("macd_hist") or 0
    bb_pband = ind_data.get("bb_pband")
    vol_ratio= ind_data.get("volume_ratio")
    mom5     = ind_data.get("momentum_5d")
    mom20    = ind_data.get("momentum_20d")

    adx      = ind_data.get("adx")
    plus_di  = ind_data.get("plus_di")
    minus_di = ind_data.get("minus_di")
    stoch_k  = ind_data.get("stoch_rsi_k")
    stoch_d  = ind_data.get("stoch_rsi_d")
    will_r   = ind_data.get("williams_r")
    obv_roc  = ind_data.get("obv_roc_5d")
    rsi_div  = int(ind_data.get("rsi_divergence",  0) or 0)
    macd_div = int(ind_data.get("macd_divergence", 0) or 0)

    # Market regime detection
    trending       = adx is not None and adx > 25
    mean_reverting = adx is not None and adx < 20
    in_uptrend     = trending and (plus_di  or 0) > (minus_di or 0)
    in_downtrend   = trending and (minus_di or 0) > (plus_di  or 0)

    # ── 1. Divergence signals (highest quality -- work in any regime) ─────────
    if rsi_div == 1:
        signals.append({"name": "RSI Bullish Divergence",  "direction":  1, "weight": 3})
    elif rsi_div == -1:
        signals.append({"name": "RSI Bearish Divergence",  "direction": -1, "weight": 3})

    if macd_div == 1:
        signals.append({"name": "MACD Bullish Divergence", "direction":  1, "weight": 2})
    elif macd_div == -1:
        signals.append({"name": "MACD Bearish Divergence", "direction": -1, "weight": 2})

    # ── 2. ADX trend direction (only when clearly trending) ───────────────────
    if trending and plus_di is not None and minus_di is not None:
        if in_uptrend:
            signals.append({"name": f"ADX Uptrend (+DI>{minus_di:.0f})", "direction": 1, "weight": 2})
        else:
            signals.append({"name": f"ADX Downtrend (-DI>{plus_di:.0f})", "direction": -1, "weight": 2})

    # ── 3. Golden / Death cross ───────────────────────────────────────────────
    if ma50 and ma200:
        if ma50 > ma200:
            signals.append({"name": "Golden Cross (MA50>MA200)", "direction":  1, "weight": 2})
        else:
            signals.append({"name": "Death Cross (MA50<MA200)",  "direction": -1, "weight": 2})

    # ── 4. RSI (full strength; gated in mean-reverting market) ────────────────
    if rsi is not None:
        if rsi < 30:
            signals.append({"name": f"RSI Oversold ({rsi:.0f})",   "direction":  1, "weight": 2})
        elif rsi > 70:
            signals.append({"name": f"RSI Overbought ({rsi:.0f})", "direction": -1, "weight": 2})
        elif mean_reverting or not trending:
            # Weaker RSI signals only relevant in sideways markets
            if rsi > 60:
                signals.append({"name": f"RSI Bullish ({rsi:.0f})", "direction":  1, "weight": 1})
            elif rsi < 40:
                signals.append({"name": f"RSI Bearish ({rsi:.0f})", "direction": -1, "weight": 1})

    # ── 5. Stochastic RSI (crossover = stronger signal) ──────────────────────
    if stoch_k is not None and stoch_d is not None:
        if stoch_k < 20 and stoch_k > stoch_d:          # bullish crossover from oversold
            signals.append({"name": f"StochRSI Bull Cross ({stoch_k:.0f})", "direction":  1, "weight": 2})
        elif stoch_k > 80 and stoch_k < stoch_d:        # bearish crossover from overbought
            signals.append({"name": f"StochRSI Bear Cross ({stoch_k:.0f})", "direction": -1, "weight": 2})
        elif stoch_k < 15:
            signals.append({"name": f"StochRSI Oversold ({stoch_k:.0f})",   "direction":  1, "weight": 1})
        elif stoch_k > 85:
            signals.append({"name": f"StochRSI Overbought ({stoch_k:.0f})", "direction": -1, "weight": 1})

    # ── 6. Williams %R ────────────────────────────────────────────────────────
    if will_r is not None:
        if will_r < -90:
            signals.append({"name": f"Williams %R Oversold ({will_r:.0f})",   "direction":  1, "weight": 1})
        elif will_r > -10:
            signals.append({"name": f"Williams %R Overbought ({will_r:.0f})", "direction": -1, "weight": 1})

    # ── 7. MACD (histogram confirms strength) ─────────────────────────────────
    if macd is not None and macd_sig is not None:
        if macd > macd_sig:
            w = 2 if macd_hist > 0 else 1
            signals.append({"name": "MACD Bullish", "direction":  1, "weight": w})
        else:
            w = 2 if macd_hist < 0 else 1
            signals.append({"name": "MACD Bearish", "direction": -1, "weight": w})

    # ── 8. Price vs MAs ───────────────────────────────────────────────────────
    if price and ma50:
        direction = 1 if price > ma50 else -1
        signals.append({"name": f"Price {'>' if direction>0 else '<'} MA50",
                         "direction": direction, "weight": 1})

    if price and ma200:
        direction = 1 if price > ma200 else -1
        signals.append({"name": f"Price {'>' if direction>0 else '<'} MA200",
                         "direction": direction, "weight": 1})

    # ── 9. Bollinger Bands ────────────────────────────────────────────────────
    if bb_pband is not None:
        if bb_pband < 0.08:
            signals.append({"name": "Bollinger Lower Band",  "direction":  1, "weight": 1})
        elif bb_pband > 0.92:
            signals.append({"name": "Bollinger Upper Band",  "direction": -1, "weight": 1})

    # ── 10. OBV confirmation (volume backs the price move) ───────────────────
    if obv_roc is not None and (mom5 or 0) != 0:
        if obv_roc > 5 and mom5 and mom5 > 0:
            signals.append({"name": f"OBV Accumulation (+{obv_roc:.1f}%)", "direction":  1, "weight": 1})
        elif obv_roc < -5 and mom5 and mom5 < 0:
            signals.append({"name": f"OBV Distribution ({obv_roc:.1f}%)",  "direction": -1, "weight": 1})

    # ── 11. Volume spike ─────────────────────────────────────────────────────
    if vol_ratio is not None and vol_ratio > 2.0:
        dir_hint = 1 if (mom5 or 0) > 0 else -1
        signals.append({"name": f"Volume Spike ({vol_ratio:.1f}x)",
                         "direction": dir_hint, "weight": 1})

    # ── 12. Momentum ─────────────────────────────────────────────────────────
    if mom5 is not None:
        if mom5 > 5:
            signals.append({"name": f"Strong Momentum (+{mom5:.1f}%)",   "direction":  1, "weight": 2})
        elif mom5 > 3:
            signals.append({"name": f"Moderate Momentum (+{mom5:.1f}%)", "direction":  1, "weight": 1})
        elif mom5 < -5:
            signals.append({"name": f"Strong Selloff ({mom5:.1f}%)",     "direction": -1, "weight": 2})
        elif mom5 < -3:
            signals.append({"name": f"Moderate Selloff ({mom5:.1f}%)",   "direction": -1, "weight": 1})

    # ── 13. Pre-earnings drift ────────────────────────────────────────────────
    if days_to_earnings is not None and 0 <= days_to_earnings <= 5:
        signals.append({"name": f"Pre-Earnings ({days_to_earnings}d)", "direction": 1, "weight": 1})

    return signals


# ── Main entry point ──────────────────────────────────────────────────────────

def generate_prediction(symbol: str, ind_data: dict, stock_snap: dict,
                         days_to_earnings: Optional[int]) -> dict:
    """
    Generate a final BULLISH / NEUTRAL / BEARISH prediction with confidence.
    Blends rule-based signals (35%) with ML ensemble probability (65%).
    """
    signals = _rule_signals(ind_data, stock_snap, days_to_earnings)

    if signals:
        total_weight   = sum(s["weight"] for s in signals)
        weighted_score = sum(s["direction"] * s["weight"] for s in signals) / total_weight
        # Confluence: how much do signals agree? (0=split, 1=all agree)
        bull_w = sum(s["weight"] for s in signals if s["direction"] > 0)
        bear_w = sum(s["weight"] for s in signals if s["direction"] < 0)
        confluence = abs(bull_w - bear_w) / total_weight
    else:
        weighted_score = 0.0
        confluence     = 0.0
        total_weight   = 0

    ml_prob = _ml_predict(ind_data)

    if ml_prob is not None:
        rule_prob    = (weighted_score + 1) / 2   # -1..1 -> 0..1
        combined_prob = rule_prob * 0.35 + ml_prob * 0.65
    else:
        combined_prob = (weighted_score + 1) / 2

    if combined_prob >= 0.60:
        signal = "BULLISH"
    elif combined_prob <= 0.40:
        signal = "BEARISH"
    else:
        signal = "NEUTRAL"

    # Confidence: distance from 0.5 scaled to 0-1
    confidence = min(abs(combined_prob - 0.5) * 2, 1.0)

    return {
        "symbol":        symbol,
        "signal":        signal,
        "confidence":    round(confidence, 2),
        "confluence":    round(confluence, 2),
        "combined_prob": round(combined_prob, 3),
        "rule_signals":  signals,
        "ml_probability":ml_prob,
        "ml_available":  ml_prob is not None,
        "n_signals":     len(signals),
        "total_weight":  total_weight,
    }
