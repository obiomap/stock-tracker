"""
predictor.py -- Signal generation and ML prediction engine.

Architecture:
  - Rule engine:   weighted directional signals from 22+ technical indicators
  - ML ensemble:   multi-timeframe RF + ET + HistGBM trained for 3d / 5d / 10d
  - Final blend:   35% rules / 65% ML
  - High-confidence flag: all 3 timeframes agree at ≥70% probability
  - Per-symbol accuracy weighting from historical predictions_log
"""
import warnings
from datetime import datetime
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
ADV_MODEL_PATH      = Path(__file__).parent.parent / "models" / "advanced_model.pkl"

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

# Interaction features derived from base features at train/predict time
_INTERACTION_NAMES = {
    "rsi_vol_quality",    # RSI direction × volume_ratio — directional momentum quality
    "mom_obv_agreement",  # momentum_5d × obv_roc_5d — price-volume consensus
    "macd_rsi_alignment", # sign(macd_hist) × sign(rsi-50) — dual confirmation
    "trend_vol_strength", # (adx/50) × volume_ratio — trending + elevated activity
}

# V1 backward-compat feature list (for loading old saved models pre-upgrade)
_V1_FEATURE_COLS = [
    "rsi", "macd_hist", "volume_ratio", "bb_pband",
    "momentum_5d", "momentum_20d",
]


# ── Interaction features ──────────────────────────────────────────────────────

def _add_interaction_features(
        X_imp: np.ndarray, base_cols: list[str]
) -> tuple[np.ndarray, list[str]]:
    """
    Compute cross-product features from an already-imputed base matrix.
    Called identically at training time and inference time so shapes always match.
    Returns (X_augmented, augmented_col_names).
    """
    def _idx(col: str) -> int:
        return base_cols.index(col) if col in base_cols else -1

    rsi_i = _idx("rsi");       vol_i = _idx("volume_ratio")
    mom_i = _idx("momentum_5d"); obv_i = _idx("obv_roc_5d")
    mh_i  = _idx("macd_hist"); adx_i = _idx("adx")

    extras: list[np.ndarray] = []
    extra_names: list[str]   = []

    # RSI direction × volume (high when RSI is directional AND vol confirms)
    if rsi_i >= 0 and vol_i >= 0:
        rsi_norm = (X_imp[:, rsi_i] - 50.0) / 50.0
        extras.append((rsi_norm * X_imp[:, vol_i]).reshape(-1, 1))
        extra_names.append("rsi_vol_quality")

    # momentum_5d × obv_roc_5d (positive = price & volume agree on direction)
    if mom_i >= 0 and obv_i >= 0:
        m = np.clip(X_imp[:, mom_i] / 10.0, -3.0, 3.0)
        o = np.clip(X_imp[:, obv_i] / 10.0, -3.0, 3.0)
        extras.append((m * o).reshape(-1, 1))
        extra_names.append("mom_obv_agreement")

    # sign(macd_hist) × sign(rsi-50) → +1 / 0 / −1 dual confirmation
    if mh_i >= 0 and rsi_i >= 0:
        alignment = np.sign(X_imp[:, mh_i]) * np.sign(X_imp[:, rsi_i] - 50.0)
        extras.append(alignment.reshape(-1, 1))
        extra_names.append("macd_rsi_alignment")

    # (adx/50) × volume_ratio (trending hard AND volume elevated)
    if adx_i >= 0 and vol_i >= 0:
        adx_norm = np.clip(X_imp[:, adx_i] / 50.0, 0.0, 2.0)
        extras.append((adx_norm * X_imp[:, vol_i]).reshape(-1, 1))
        extra_names.append("trend_vol_strength")

    if extras:
        return np.concatenate([X_imp] + extras, axis=1), list(base_cols) + extra_names
    return X_imp, list(base_cols)


def _load_model():
    """Load legacy model bundle and scaler. Returns (bundle, scaler) or (None, None)."""
    try:
        import joblib
        if MODEL_PATH.exists() and SCALER_PATH.exists():
            bundle = joblib.load(MODEL_PATH)
            scaler = joblib.load(SCALER_PATH)
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


def _load_advanced_model() -> Optional[dict]:
    """Load the multi-timeframe advanced model bundle or None."""
    try:
        import joblib
        if ADV_MODEL_PATH.exists():
            return joblib.load(ADV_MODEL_PATH)
    except Exception:
        pass
    return None


# ── Training helpers ──────────────────────────────────────────────────────────

def _train_bundle(X_raw: np.ndarray, y: np.ndarray,
                  base_cols: list[str]) -> dict:
    """
    Train RF + ET + HistGBM on one target window.
    Returns a self-contained bundle with embedded imputer and scaler.
    Walk-forward split (80/20) gives out-of-sample accuracy and
    high-confidence (≥70% prob) precision on the held-out 20%.
    """
    from sklearn.ensemble import (
        RandomForestClassifier, ExtraTreesClassifier,
        HistGradientBoostingClassifier,
    )
    from sklearn.preprocessing import StandardScaler
    from sklearn.impute import SimpleImputer

    imputer = SimpleImputer(strategy="median")
    X_imp   = imputer.fit_transform(X_raw)
    X_aug, aug_cols = _add_interaction_features(X_imp, base_cols)

    split      = int(len(X_aug) * 0.80)
    X_tr, X_te = X_aug[:split], X_aug[split:]
    y_tr, y_te = y[:split],     y[split:]

    scaler    = StandardScaler()
    X_tr_s    = scaler.fit_transform(X_tr)
    X_te_s    = scaler.transform(X_te)

    rf = RandomForestClassifier(
        n_estimators=300, max_depth=8, min_samples_leaf=8,
        max_features="sqrt", random_state=42, n_jobs=-1,
    )
    rf.fit(X_tr_s, y_tr)

    et = ExtraTreesClassifier(
        n_estimators=300, max_depth=8, min_samples_leaf=8,
        max_features="sqrt", random_state=43, n_jobs=-1,
    )
    et.fit(X_tr_s, y_tr)

    hgbm = HistGradientBoostingClassifier(
        max_iter=300, max_depth=6, min_samples_leaf=10,
        learning_rate=0.04, l2_regularization=0.1, random_state=44,
    )
    hgbm.fit(X_tr_s, y_tr)

    # Out-of-sample evaluation
    if len(y_te) > 0:
        p_rf   = rf.predict_proba(X_te_s)[:, 1]
        p_et   = et.predict_proba(X_te_s)[:, 1]
        p_hgbm = hgbm.predict_proba(X_te_s)[:, 1]
        blended = p_rf * 0.30 + p_et * 0.30 + p_hgbm * 0.40
        oos_acc = float(((blended >= 0.50).astype(int) == y_te).mean())
        # Precision at ≥70% threshold (the "high-confidence" regime)
        bull_mask = blended >= 0.70
        bear_mask = blended <= 0.30
        hc_n      = int(bull_mask.sum() + bear_mask.sum())
        if hc_n > 0:
            correct = (int(y_te[bull_mask].sum()) +
                       int((1 - y_te[bear_mask]).sum()))
            hc_precision = float(correct / hc_n)
        else:
            hc_precision = 0.0
    else:
        oos_acc = hc_precision = 0.0
        hc_n    = 0

    fi = {}
    for i, col in enumerate(aug_cols):
        fi[col] = round(
            float(rf.feature_importances_[i] * 0.5 +
                  et.feature_importances_[i] * 0.5), 4
        )

    return {
        "rf": rf, "et": et, "hgbm": hgbm,
        "imputer":           imputer,
        "scaler":            scaler,
        "base_feature_cols": list(base_cols),
        "feature_cols":      aug_cols,
        "feature_importance": fi,
        "n_samples":         int(len(y)),
        "n_train":           int(split),
        "oos_accuracy":      round(oos_acc,      3),
        "hc_precision":      round(hc_precision, 3),
        "hc_n":              hc_n,
    }


# ── Training ──────────────────────────────────────────────────────────────────

def train_model(all_hists: dict[str, pd.DataFrame]) -> tuple[bool, dict]:
    """
    Train multi-timeframe ensemble (3d, 5d, 10d forward returns).
    Saves to ADV_MODEL_PATH + backward-compat MODEL_PATH / SCALER_PATH.
    Returns (success, feature_importance_3d).
    """
    try:
        import joblib
        import warnings as _w
        _w.filterwarnings("ignore", category=UserWarning, module="sklearn")

        frames_3d:  list[pd.DataFrame] = []
        frames_5d:  list[pd.DataFrame] = []
        frames_10d: list[pd.DataFrame] = []

        for symbol, hist in all_hists.items():
            if len(hist) < 80:
                continue
            enriched  = ind.enrich(hist.copy())
            available = [c for c in FEATURE_COLS if c in enriched.columns]
            if not available:
                continue

            df3 = enriched.dropna(subset=["target"])
            if len(df3) >= 30:
                frames_3d.append(df3[available + ["target"]])

            if "target_5d" in enriched.columns:
                df5 = enriched.dropna(subset=["target_5d"])
                if len(df5) >= 30:
                    frames_5d.append(df5[available + ["target_5d"]])

            if "target_10d" in enriched.columns:
                df10 = enriched.dropna(subset=["target_10d"])
                if len(df10) >= 30:
                    frames_10d.append(df10[available + ["target_10d"]])

        if not frames_3d:
            return False, {}

        def _build(frames, target_col):
            combined = pd.concat(frames, ignore_index=True)
            cols = [c for c in FEATURE_COLS if c in combined.columns]
            return combined[cols].values.astype(float), combined[target_col].values, cols

        print("[predictor] training 3d model...", flush=True)
        X3, y3, cols3 = _build(frames_3d, "target")
        b3d = _train_bundle(X3, y3, cols3)
        print(f"[predictor] 3d  OOS={b3d['oos_accuracy']:.1%}  "
              f"HC-precision={b3d['hc_precision']:.1%} (n={b3d['hc_n']})", flush=True)

        b5d = b10d = None
        if frames_5d:
            print("[predictor] training 5d model...", flush=True)
            X5, y5, cols5 = _build(frames_5d, "target_5d")
            b5d = _train_bundle(X5, y5, cols5)
            print(f"[predictor] 5d  OOS={b5d['oos_accuracy']:.1%}  "
                  f"HC-precision={b5d['hc_precision']:.1%} (n={b5d['hc_n']})", flush=True)

        if frames_10d:
            print("[predictor] training 10d model...", flush=True)
            X10, y10, cols10 = _build(frames_10d, "target_10d")
            b10d = _train_bundle(X10, y10, cols10)
            print(f"[predictor] 10d OOS={b10d['oos_accuracy']:.1%}  "
                  f"HC-precision={b10d['hc_precision']:.1%} (n={b10d['hc_n']})", flush=True)

        ADV_MODEL_PATH.parent.mkdir(exist_ok=True)
        adv = {
            "3d":        b3d,
            "5d":        b5d,
            "10d":       b10d,
            "trained_at": datetime.now().isoformat(),
            "n_stocks":  len(frames_3d),
        }
        joblib.dump(adv, ADV_MODEL_PATH)
        print(f"[predictor] advanced model saved — {len(frames_3d)} stocks", flush=True)

        # Backward-compat: also write to MODEL_PATH / SCALER_PATH
        legacy = {
            "rf":                b3d["rf"],
            "et":                b3d["et"],
            "hgbm":              b3d["hgbm"],
            "imputer":           b3d["imputer"],
            "feature_cols":      b3d["feature_cols"],
            "feature_importance": b3d["feature_importance"],
            "n_samples":         b3d["n_samples"],
            "n_stocks":          len(frames_3d),
        }
        joblib.dump(legacy,         MODEL_PATH)
        joblib.dump(b3d["scaler"],  SCALER_PATH)

        return True, b3d["feature_importance"]

    except Exception as e:
        print(f"Training failed: {e}")
        import traceback; traceback.print_exc()
        return False, {}


# ── Inference ─────────────────────────────────────────────────────────────────

def _predict_from_bundle(bundle: Optional[dict], features: dict) -> Optional[float]:
    """
    Predict from a self-contained bundle dict (with embedded imputer + scaler).
    Returns blended probability (0-1) or None on error.
    """
    if bundle is None:
        return None
    try:
        base_cols = bundle.get("base_feature_cols") or [
            c for c in bundle.get("feature_cols", FEATURE_COLS)
            if c not in _INTERACTION_NAMES
        ]
        vals    = [features.get(col, np.nan) for col in base_cols]
        X       = np.array(vals, dtype=float).reshape(1, -1)
        imputer = bundle.get("imputer")
        X_imp   = imputer.transform(X) if imputer else np.nan_to_num(X, nan=0.0)
        X_aug, _ = _add_interaction_features(X_imp, base_cols)
        scaler  = bundle.get("scaler")
        X_s     = scaler.transform(X_aug) if scaler else X_aug
        rf      = bundle["rf"]
        et      = bundle.get("et")
        hgbm    = bundle.get("hgbm")
        p_rf    = rf.predict_proba(X_s)[0][1]
        p_et    = et.predict_proba(X_s)[0][1]   if et   else p_rf
        p_hgbm  = hgbm.predict_proba(X_s)[0][1] if hgbm else p_rf
        return round(float(p_rf * 0.30 + p_et * 0.30 + p_hgbm * 0.40), 3)
    except Exception:
        return None


def _ml_predict_multi(features: dict) -> Optional[dict]:
    """
    Run multi-timeframe inference (3d / 5d / 10d).
    Returns a dict with per-timeframe probs, consensus, and high_confidence flag.
    Falls back to legacy single-model when advanced model not yet trained.
    High-confidence requires all 3 timeframes present AND all ≥70% (bull) / ≤30% (bear).
    """
    adv = _load_advanced_model()

    if adv is None:
        # Legacy fallback: use old MODEL_PATH + SCALER_PATH bundle
        bundle, scaler = _load_model()
        if bundle is None:
            return None
        try:
            fc   = bundle.get("feature_cols", FEATURE_COLS)
            base = [c for c in fc if c not in _INTERACTION_NAMES]
            vals = [features.get(c, np.nan) for c in base]
            X    = np.array(vals, dtype=float).reshape(1, -1)
            imp  = bundle.get("imputer")
            X_imp = imp.transform(X) if imp else np.nan_to_num(X, nan=0.0)
            X_aug, _ = _add_interaction_features(X_imp, base)
            X_s  = scaler.transform(X_aug)
            rf   = bundle["rf"]; et = bundle.get("et"); hgbm = bundle.get("hgbm")
            p    = (rf.predict_proba(X_s)[0][1] * 0.30 +
                    (et.predict_proba(X_s)[0][1]   if et   else rf.predict_proba(X_s)[0][1]) * 0.30 +
                    (hgbm.predict_proba(X_s)[0][1] if hgbm else rf.predict_proba(X_s)[0][1]) * 0.40)
            p = round(float(p), 3)
        except Exception:
            return None
        return {"prob_3d": p, "prob_5d": None, "prob_10d": None,
                "consensus_prob": p,
                "consensus_direction": "BULL" if p > 0.50 else "BEAR",
                "high_confidence": False, "multi_timeframe": False}

    prob_3d  = _predict_from_bundle(adv.get("3d"),  features)
    prob_5d  = _predict_from_bundle(adv.get("5d"),  features)
    prob_10d = _predict_from_bundle(adv.get("10d"), features)

    probs = [p for p in [prob_3d, prob_5d, prob_10d] if p is not None]
    if not probs:
        return None

    consensus_prob      = round(sum(probs) / len(probs), 3)
    dirs                = ["BULL" if p > 0.50 else "BEAR" for p in probs]
    consensus_direction = dirs[0] if len(set(dirs)) == 1 else "SPLIT"

    all_present = all(p is not None for p in [prob_3d, prob_5d, prob_10d])
    if all_present and consensus_direction == "BULL":
        high_confidence = min(probs) >= 0.70
    elif all_present and consensus_direction == "BEAR":
        high_confidence = max(probs) <= 0.30
    else:
        high_confidence = False

    return {
        "prob_3d":             prob_3d,
        "prob_5d":             prob_5d,
        "prob_10d":            prob_10d,
        "consensus_prob":      consensus_prob,
        "consensus_direction": consensus_direction,
        "high_confidence":     high_confidence,
        "multi_timeframe":     len(probs) == 3,
    }


def _ml_predict(features: dict) -> Optional[float]:
    """Backward-compatible: return blended consensus probability (0-1)."""
    result = _ml_predict_multi(features)
    return result["consensus_prob"] if result else None


def get_model_feature_importance() -> dict:
    """Return sorted feature importance from the trained model."""
    adv = _load_advanced_model()
    if adv and adv.get("3d"):
        fi = adv["3d"].get("feature_importance", {})
    else:
        bundle, _ = _load_model()
        if bundle is None:
            return {}
        fi = bundle.get("feature_importance", {})
    return dict(sorted(fi.items(), key=lambda x: x[1], reverse=True))


def get_symbol_historical_accuracy(symbol: str, min_scored: int = 5) -> Optional[float]:
    """
    Look up the historical prediction accuracy for this symbol from the DB.
    Returns None if fewer than min_scored predictions have been scored yet.
    Uses the 30 most recent scored predictions to stay current.
    """
    try:
        from .database import get_connection
        with get_connection() as conn:
            rows = conn.execute("""
                SELECT was_correct FROM predictions_log
                WHERE symbol=? AND was_correct IS NOT NULL
                ORDER BY prediction_date DESC
                LIMIT 30
            """, (symbol,)).fetchall()
        if len(rows) < min_scored:
            return None
        return round(sum(r["was_correct"] for r in rows) / len(rows), 3)
    except Exception:
        return None


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
    """Return training metadata including multi-timeframe OOS accuracy."""
    adv = _load_advanced_model()
    if adv and adv.get("3d"):
        b3  = adv["3d"]
        b5  = adv.get("5d") or {}
        b10 = adv.get("10d") or {}
        return {
            "n_samples":         b3.get("n_samples", "?"),
            "n_stocks":          adv.get("n_stocks",  "?"),
            "feature_cols":      b3.get("feature_cols", []),
            "n_features":        len(b3.get("feature_cols", [])),
            "oos_accuracy_3d":   b3.get("oos_accuracy"),
            "hc_precision_3d":   b3.get("hc_precision"),
            "hc_n_3d":           b3.get("hc_n"),
            "oos_accuracy_5d":   b5.get("oos_accuracy"),
            "hc_precision_5d":   b5.get("hc_precision"),
            "oos_accuracy_10d":  b10.get("oos_accuracy"),
            "hc_precision_10d":  b10.get("hc_precision"),
            "trained_at":        adv.get("trained_at"),
            "multi_timeframe":   True,
        }
    bundle, _ = _load_model()
    if bundle is None:
        return {}
    return {
        "n_samples":       bundle.get("n_samples", "?"),
        "n_stocks":        bundle.get("n_stocks",  "?"),
        "feature_cols":    bundle.get("feature_cols", []),
        "n_features":      len(bundle.get("feature_cols", [])),
        "multi_timeframe": False,
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
                         days_to_earnings: Optional[int],
                         market_regime: float = 0.0) -> dict:
    """
    Generate BULLISH / NEUTRAL / BEARISH prediction with confidence.
    Blends rule-based signals (35%) with multi-timeframe ML ensemble (65%).

    market_regime: +1.0 = broad bull (SPY above MA20),
                   -1.0 = broad bear (SPY below MA20), 0 = neutral/unknown.

    high_confidence=True when all 3 timeframe models agree at ≥70% probability
    AND the symbol's historical accuracy (if ≥5 scored predictions) is ≥50%.
    """
    signals = _rule_signals(ind_data, stock_snap, days_to_earnings)

    if signals:
        total_weight   = sum(s["weight"] for s in signals)
        weighted_score = sum(s["direction"] * s["weight"] for s in signals) / total_weight
        bull_w     = sum(s["weight"] for s in signals if s["direction"] > 0)
        bear_w     = sum(s["weight"] for s in signals if s["direction"] < 0)
        confluence = abs(bull_w - bear_w) / total_weight
    else:
        weighted_score = 0.0
        confluence     = 0.0
        total_weight   = 0

    multi   = _ml_predict_multi(ind_data)
    ml_prob = multi["consensus_prob"] if multi else None

    if ml_prob is not None:
        rule_prob     = (weighted_score + 1) / 2
        combined_prob = rule_prob * 0.35 + ml_prob * 0.65
    else:
        combined_prob = (weighted_score + 1) / 2

    # Market regime nudge (capped ±5% so regime alone never flips a signal)
    if market_regime != 0.0:
        combined_prob = float(np.clip(combined_prob + market_regime * 0.05, 0.0, 1.0))

    if combined_prob >= 0.60:
        signal = "BULLISH"
    elif combined_prob <= 0.40:
        signal = "BEARISH"
    else:
        signal = "NEUTRAL"

    confidence = min(abs(combined_prob - 0.5) * 2, 1.0)

    # Confluence penalty: split indicators → cap confidence
    if confluence < 0.3 and total_weight > 0:
        confidence *= 0.7

    # Per-symbol historical accuracy: boost or penalise confidence
    sym_acc = get_symbol_historical_accuracy(symbol)
    if sym_acc is not None:
        if sym_acc > 0.60:
            confidence = min(confidence * (1.0 + (sym_acc - 0.60) * 0.5), 1.0)
        elif sym_acc < 0.45:
            confidence *= 0.80

    # High-confidence: all 3 timeframes agree at ≥70% AND symbol not historically poor
    high_confidence = bool(
        multi is not None and
        multi.get("high_confidence", False) and
        (sym_acc is None or sym_acc >= 0.50)
    )

    return {
        "symbol":           symbol,
        "signal":           signal,
        "confidence":       round(confidence, 2),
        "confluence":       round(confluence, 2),
        "combined_prob":    round(combined_prob, 3),
        "rule_signals":     signals,
        "ml_probability":   ml_prob,
        "ml_available":     ml_prob is not None,
        "n_signals":        len(signals),
        "total_weight":     total_weight,
        "market_regime":    market_regime,
        "high_confidence":  high_confidence,
        "multi_timeframe":  multi is not None and multi.get("multi_timeframe", False),
        "prob_3d":          multi["prob_3d"]   if multi else None,
        "prob_5d":          multi["prob_5d"]   if multi else None,
        "prob_10d":         multi["prob_10d"]  if multi else None,
        "symbol_accuracy":  sym_acc,
    }
