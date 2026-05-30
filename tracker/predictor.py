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

MODEL_PATH          = Path(__file__).parent.parent / "models" / "stock_model.pkl"
SCALER_PATH         = Path(__file__).parent.parent / "models" / "scaler.pkl"
UPTREND_MODEL_PATH  = Path(__file__).parent.parent / "models" / "uptrend_model.pkl"
UPTREND_SCALER_PATH = Path(__file__).parent.parent / "models" / "uptrend_scaler.pkl"

# Feature set used for ML training and inference (30 features)
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
    # Fibonacci proximity
    "fib_pos_120d", "fib_dist_38", "fib_dist_50", "fib_dist_62",
    # ── Enhanced: EMA, oscillators, Ichimoku, Asian-market factors ────────────
    "ema9_ema21_diff",    # EMA9 vs EMA21 crossover momentum
    "cci_20",             # Commodity Channel Index (cycles + extremes)
    "mfi_14",             # Money Flow Index (volume-weighted RSI)
    "cmf_20",             # Chaikin Money Flow (accumulation/distribution)
    "supertrend_dir",     # Supertrend direction (+1 bull / -1 bear)
    "ichimoku_cloud",     # Ichimoku cloud position (-1 below / 0 inside / +1 above)
    "ichimoku_tk",        # Tenkan vs Kijun (+1 bull / -1 bear)
    "pct_from_52w_high",  # % below 52-week high (0 = at breakout level)
    "pct_from_52w_low",   # % above 52-week low (0 = at danger level)
    "vol_regime",         # Volatility regime: ATR% percentile (0=calm, 1=volatile)
    "gap_pct",            # Overnight gap % (key pattern for Asian markets)
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


def _load_uptrend_model():
    """Load uptrend model bundle and scaler. Returns (bundle, scaler) or (None, None)."""
    try:
        import joblib
        if UPTREND_MODEL_PATH.exists() and UPTREND_SCALER_PATH.exists():
            bundle = joblib.load(UPTREND_MODEL_PATH)
            scaler = joblib.load(UPTREND_SCALER_PATH)
            return bundle, scaler
    except Exception:
        pass
    return None, None


def get_uptrend_probability(ind_data: dict) -> Optional[float]:
    """
    Return probability (0-100) that this stock will rally >=10% in 20 trading days.
    Uses the specialised GBM trained by the rally study on NVDA/TSLA/AAPL.
    The model CV AUC was inverted (<0.5), so we return 1-p to correct direction.
    """
    bundle, scaler = _load_uptrend_model()
    if bundle is None:
        return None
    try:
        gbm         = bundle["gbm"]
        imputer     = bundle["imputer"]
        feat_cols   = bundle["feature_cols"]
        vals = [ind_data.get(col, np.nan) for col in feat_cols]
        X = np.array(vals, dtype=float).reshape(1, -1)
        X = imputer.transform(X)
        X = scaler.transform(X)
        raw_prob = gbm.predict_proba(X)[0][1]
        # Invert because the CV AUC was 0.302 (inverted predictor)
        corrected = round((1.0 - raw_prob) * 100, 1)
        return corrected
    except Exception:
        return None


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
    # Enhanced indicators
    ich_cloud  = ind_data.get("ichimoku_cloud")
    ich_tk     = ind_data.get("ichimoku_tk")
    supertrend = ind_data.get("supertrend_dir")
    cci_val    = ind_data.get("cci_20")
    mfi_val    = ind_data.get("mfi_14")
    cmf_val    = ind_data.get("cmf_20")
    ema_diff   = ind_data.get("ema9_ema21_diff")
    h52_pct    = ind_data.get("pct_from_52w_high")
    l52_pct    = ind_data.get("pct_from_52w_low")
    gap_pct    = ind_data.get("gap_pct")

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

    # ── 14. Fibonacci retracement ─────────────────────────────────────────────
    fib = ind_data.get("fib_levels", {})
    if fib:
        fib_sig   = fib.get("signal", 0)
        fib_level = fib.get("signal_level", "")
        fib_dist  = fib.get("nearest_dist_pct", 100)
        fib_trend = fib.get("trend", "")
        fib_pos   = fib.get("position_pct", 50)

        if fib_sig == 1 and fib_level:
            # Price at a key Fib support in an uptrend → potential bounce
            w = 3 if fib_dist < 0.5 else 2
            signals.append({
                "name":      f"Fib {fib_level} Support ({fib_dist:.1f}% away)",
                "direction":  1,
                "weight":    w,
            })
        elif fib_sig == -1 and fib_level:
            # Price at a key Fib resistance in a downtrend → potential rejection
            w = 3 if fib_dist < 0.5 else 2
            signals.append({
                "name":      f"Fib {fib_level} Resistance ({fib_dist:.1f}% away)",
                "direction": -1,
                "weight":    w,
            })

        # Trend continuation: very high or very low in range
        if fib_trend == "up" and fib_pos > 80:
            signals.append({
                "name":      f"Above Fib 78.6% — Strong Uptrend",
                "direction":  1,
                "weight":    1,
            })
        elif fib_trend == "down" and fib_pos < 20:
            signals.append({
                "name":      f"Below Fib 23.6% — Strong Downtrend",
                "direction": -1,
                "weight":    1,
            })

    # ── 15. Ichimoku Cloud (Japanese origin; core to Asian market analysis) ───
    if ich_cloud is not None:
        if ich_cloud > 0:
            signals.append({"name": "Ichimoku Above Cloud",  "direction":  1, "weight": 2})
        elif ich_cloud < 0:
            signals.append({"name": "Ichimoku Below Cloud",  "direction": -1, "weight": 2})
    if ich_tk is not None:
        if ich_tk > 0:
            signals.append({"name": "Ichimoku TK Bullish",   "direction":  1, "weight": 1})
        else:
            signals.append({"name": "Ichimoku TK Bearish",   "direction": -1, "weight": 1})

    # ── 16. Supertrend ────────────────────────────────────────────────────────
    if supertrend is not None:
        if supertrend > 0:
            signals.append({"name": "Supertrend Bullish",    "direction":  1, "weight": 2})
        else:
            signals.append({"name": "Supertrend Bearish",    "direction": -1, "weight": 2})

    # ── 17. CCI -- commodity / cyclical moves ─────────────────────────────────
    if cci_val is not None:
        if cci_val < -100:
            signals.append({"name": f"CCI Oversold ({cci_val:.0f})",   "direction":  1, "weight": 1})
        elif cci_val > 100:
            signals.append({"name": f"CCI Overbought ({cci_val:.0f})", "direction": -1, "weight": 1})

    # ── 18. Money Flow Index (volume confirms price moves) ────────────────────
    if mfi_val is not None:
        if mfi_val < 20:
            signals.append({"name": f"MFI Oversold ({mfi_val:.0f})",   "direction":  1, "weight": 2})
        elif mfi_val > 80:
            signals.append({"name": f"MFI Overbought ({mfi_val:.0f})", "direction": -1, "weight": 1})

    # ── 19. Chaikin Money Flow (accumulation vs distribution) ─────────────────
    if cmf_val is not None:
        if cmf_val > 0.15:
            signals.append({"name": f"CMF Accumulation (+{cmf_val:.2f})", "direction":  1, "weight": 1})
        elif cmf_val < -0.15:
            signals.append({"name": f"CMF Distribution ({cmf_val:.2f})",  "direction": -1, "weight": 1})

    # ── 20. EMA9 / EMA21 crossover ────────────────────────────────────────────
    if ema_diff is not None:
        if ema_diff > 0.5:
            signals.append({"name": f"EMA9 > EMA21 (+{ema_diff:.1f}%)",  "direction":  1, "weight": 1})
        elif ema_diff < -0.5:
            signals.append({"name": f"EMA9 < EMA21 ({ema_diff:.1f}%)",   "direction": -1, "weight": 1})

    # ── 21. 52-week proximity (key psychological level for US + Asian retail) ─
    if h52_pct is not None and h52_pct < 3.0:
        signals.append({"name": f"Near 52w High ({h52_pct:.1f}% away)",  "direction":  1, "weight": 2})
    if l52_pct is not None and l52_pct < 5.0:
        signals.append({"name": f"Near 52w Low ({l52_pct:.1f}% away)",   "direction": -1, "weight": 2})

    # ── 22. Overnight gap (significant for Asian market open dynamics) ────────
    if gap_pct is not None and abs(gap_pct) > 1.5:
        dir_g = 1 if gap_pct > 0 else -1
        w_g   = 2 if abs(gap_pct) > 3.0 else 1
        signals.append({"name": f"Gap {'Up' if dir_g > 0 else 'Down'} ({gap_pct:+.1f}%)",
                         "direction": dir_g, "weight": w_g})

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
