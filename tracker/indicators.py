import pandas as pd
import numpy as np


# ── Core oscillators ──────────────────────────────────────────────────────────

def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def calculate_macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calculate_bollinger(close: pd.Series, period: int = 20, std: float = 2.0):
    sma = close.rolling(period).mean()
    sigma = close.rolling(period).std()
    upper = sma + std * sigma
    lower = sma - std * sigma
    pband = (close - lower) / (upper - lower).replace(0, np.nan)
    return upper, sma, lower, pband


# ── New indicators ────────────────────────────────────────────────────────────

def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average True Range -- Wilder smoothed volatility measure."""
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()


def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14):
    """
    Average Directional Index -- trend strength 0-100.
    Returns (adx, +DI, -DI). ADX > 25 = trending, < 20 = sideways.
    """
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    up_move = high.diff()
    down_move = -low.diff()

    pos_dm = pd.Series(
        np.where((up_move > down_move) & (up_move > 0), up_move, 0.0),
        index=high.index
    )
    neg_dm = pd.Series(
        np.where((down_move > up_move) & (down_move > 0), down_move, 0.0),
        index=high.index
    )

    atr_s = tr.ewm(span=period, adjust=False).mean()
    pos_di = 100 * pos_dm.ewm(span=period, adjust=False).mean() / atr_s
    neg_di = 100 * neg_dm.ewm(span=period, adjust=False).mean() / atr_s

    dx = 100 * (pos_di - neg_di).abs() / (pos_di + neg_di).replace(0, np.nan)
    adx = dx.ewm(span=period, adjust=False).mean()
    return adx, pos_di, neg_di


def calculate_stochastic_rsi(close: pd.Series, period: int = 14,
                              smooth_k: int = 3, smooth_d: int = 3):
    """
    Stochastic RSI -- more sensitive than plain RSI.
    K < 20 oversold, K > 80 overbought; K crossing D = signal.
    """
    rsi = calculate_rsi(close, period)
    rsi_min = rsi.rolling(period).min()
    rsi_max = rsi.rolling(period).max()
    stoch = (rsi - rsi_min) / (rsi_max - rsi_min).replace(0, np.nan)
    k = stoch.rolling(smooth_k).mean() * 100
    d = k.rolling(smooth_d).mean()
    return k, d


def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """On Balance Volume -- cumulative price-weighted volume trend."""
    direction = np.sign(close.diff()).fillna(0)
    return (volume * direction).cumsum()


def calculate_roc(close: pd.Series, period: int = 10) -> pd.Series:
    """Rate of Change -- % price change over N periods."""
    return (close - close.shift(period)) / close.shift(period) * 100


def calculate_williams_r(high: pd.Series, low: pd.Series, close: pd.Series,
                          period: int = 14) -> pd.Series:
    """Williams %R -- momentum oscillator, -100 to 0. < -80 oversold, > -20 overbought."""
    highest_high = high.rolling(period).max()
    lowest_low = low.rolling(period).min()
    return -100 * (highest_high - close) / (highest_high - lowest_low).replace(0, np.nan)


def detect_divergence(close: pd.Series, oscillator: pd.Series, lookback: int = 30) -> int:
    """
    Detect classic price/oscillator divergence.
    Returns:  1 = bullish (price lower low, oscillator higher low -- momentum not confirming)
             -1 = bearish (price higher high, oscillator lower high)
              0 = no divergence
    """
    if len(close) < lookback + 5:
        return 0
    try:
        rc = close.iloc[-lookback:]
        ro = oscillator.iloc[-lookback:]
        mid = lookback // 2

        p_low_prev  = rc.iloc[:mid].min()
        p_low_rec   = rc.iloc[mid:].min()
        o_low_prev  = ro.iloc[:mid].min()
        o_low_rec   = ro.iloc[mid:].min()

        # Bullish divergence: price lower, oscillator higher
        if p_low_rec < p_low_prev * 0.99 and o_low_rec > o_low_prev * 1.01:
            return 1

        p_high_prev = rc.iloc[:mid].max()
        p_high_rec  = rc.iloc[mid:].max()
        o_high_prev = ro.iloc[:mid].max()
        o_high_rec  = ro.iloc[mid:].max()

        # Bearish divergence: price higher, oscillator lower
        if p_high_rec > p_high_prev * 1.01 and o_high_rec < o_high_prev * 0.99:
            return -1
    except Exception:
        pass
    return 0


# ── Enrich / extract ──────────────────────────────────────────────────────────

def enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Add all technical indicators to an OHLCV DataFrame. Mutates in place."""
    close  = df["Close"]
    high   = df.get("High", close)
    low    = df.get("Low",  close)
    volume = df["Volume"]

    # -- Original indicators --------------------------------------------------
    df["rsi"]                        = calculate_rsi(close)
    df["macd"], df["macd_signal"], df["macd_hist"] = calculate_macd(close)
    _, _, _, df["bb_pband"]          = calculate_bollinger(close)

    df["ma20"]  = close.rolling(20).mean()
    df["ma50"]  = close.rolling(50).mean()
    df["ma200"] = close.rolling(200).mean()

    df["momentum_5d"]  = close.pct_change(5)  * 100
    df["momentum_20d"] = close.pct_change(20) * 100
    df["volume_ratio"] = volume / volume.rolling(20).mean()

    # -- New indicators -------------------------------------------------------
    atr = calculate_atr(high, low, close)
    df["atr"]     = atr
    df["atr_pct"] = (atr / close * 100)          # ATR as % of price (volatility-normalised)

    adx, pos_di, neg_di = calculate_adx(high, low, close)
    df["adx"]      = adx
    df["plus_di"]  = pos_di
    df["minus_di"] = neg_di

    df["stoch_rsi_k"], df["stoch_rsi_d"] = calculate_stochastic_rsi(close)

    obv = calculate_obv(close, volume)
    df["obv"]        = obv
    df["obv_roc_5d"] = obv.pct_change(5) * 100   # OBV momentum (accumulation/distribution)

    df["roc_10d"]    = calculate_roc(close, 10)
    df["williams_r"] = calculate_williams_r(high, low, close)

    # Normalised price position relative to key MAs
    df["price_vs_ma20_pct"] = (close - df["ma20"]) / df["ma20"] * 100
    df["price_vs_ma50_pct"] = (close - df["ma50"]) / df["ma50"] * 100

    # -- Training target: 3-day forward return (better signal/noise than 1d) --
    df["target"] = (close.shift(-3) > close).astype(int)

    # -- Sanitise: replace +/-inf with NaN so sklearn is happy -----------------
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].replace([np.inf, -np.inf], np.nan)

    return df


def get_latest_indicators(df: pd.DataFrame) -> dict:
    """Enrich OHLCV history and return the most-recent bar's indicators."""
    enriched = enrich(df.copy())
    last = enriched.iloc[-1]

    def safe(val):
        return round(float(val), 4) if pd.notna(val) else None

    # Divergence -- computed from full series (not per-bar, needs lookback)
    rsi_div  = detect_divergence(enriched["Close"], enriched["rsi"],      lookback=30)
    macd_div = detect_divergence(enriched["Close"], enriched["macd_hist"], lookback=30)

    return {
        # Original
        "rsi":          safe(last.get("rsi")),
        "macd":         safe(last.get("macd")),
        "macd_signal":  safe(last.get("macd_signal")),
        "macd_hist":    safe(last.get("macd_hist")),
        "bb_pband":     safe(last.get("bb_pband")),
        "ma20":         safe(last.get("ma20")),
        "ma50":         safe(last.get("ma50")),
        "ma200":        safe(last.get("ma200")),
        "momentum_5d":  safe(last.get("momentum_5d")),
        "momentum_20d": safe(last.get("momentum_20d")),
        "volume_ratio": safe(last.get("volume_ratio")),
        # New
        "atr":              safe(last.get("atr")),
        "atr_pct":          safe(last.get("atr_pct")),
        "adx":              safe(last.get("adx")),
        "plus_di":          safe(last.get("plus_di")),
        "minus_di":         safe(last.get("minus_di")),
        "stoch_rsi_k":      safe(last.get("stoch_rsi_k")),
        "stoch_rsi_d":      safe(last.get("stoch_rsi_d")),
        "obv_roc_5d":       safe(last.get("obv_roc_5d")),
        "roc_10d":          safe(last.get("roc_10d")),
        "williams_r":       safe(last.get("williams_r")),
        "price_vs_ma20_pct":safe(last.get("price_vs_ma20_pct")),
        "price_vs_ma50_pct":safe(last.get("price_vs_ma50_pct")),
        # Scalars from full-series analysis
        "rsi_divergence":  float(rsi_div),
        "macd_divergence": float(macd_div),
        # Pass enriched df for any downstream use
        "enriched_df": enriched,
    }
