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


def calculate_ema(close: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average."""
    return close.ewm(span=period, adjust=False).mean()


def calculate_cci(high: pd.Series, low: pd.Series, close: pd.Series,
                  period: int = 20) -> pd.Series:
    """Commodity Channel Index. >+100 overbought, <-100 oversold."""
    tp  = (high + low + close) / 3
    sma = tp.rolling(period).mean()
    mad = tp.rolling(period).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
    return (tp - sma) / (0.015 * mad.replace(0, np.nan))


def calculate_mfi(high: pd.Series, low: pd.Series, close: pd.Series,
                  volume: pd.Series, period: int = 14) -> pd.Series:
    """Money Flow Index -- volume-weighted RSI. <20 oversold, >80 overbought."""
    tp     = (high + low + close) / 3
    raw_mf = tp * volume
    delta  = tp.diff()
    pos_mf = raw_mf.where(delta > 0, 0.0).rolling(period).sum()
    neg_mf = raw_mf.where(delta <= 0, 0.0).rolling(period).sum()
    mfr    = pos_mf / neg_mf.replace(0, np.nan)
    return 100 - (100 / (1 + mfr))


def calculate_cmf(high: pd.Series, low: pd.Series, close: pd.Series,
                  volume: pd.Series, period: int = 20) -> pd.Series:
    """Chaikin Money Flow. >+0.15 accumulation, <-0.15 distribution."""
    clv = ((close - low) - (high - close)) / (high - low).replace(0, np.nan)
    return (clv * volume).rolling(period).sum() / volume.rolling(period).sum().replace(0, np.nan)


def calculate_supertrend(high: pd.Series, low: pd.Series, close: pd.Series,
                         period: int = 10, multiplier: float = 3.0) -> pd.Series:
    """Supertrend direction. +1.0 = bullish, -1.0 = bearish."""
    atr       = calculate_atr(high, low, close, period)
    hl2       = (high + low) / 2.0
    upper_raw = (hl2 + multiplier * atr).values
    lower_raw = (hl2 - multiplier * atr).values
    close_v   = close.values
    n         = len(close_v)

    f_upper   = upper_raw.copy()
    f_lower   = lower_raw.copy()
    direction = np.ones(n, dtype=float)

    for i in range(1, n):
        if np.isnan(upper_raw[i]) or np.isnan(lower_raw[i]):
            direction[i] = direction[i - 1]
            continue
        f_upper[i] = (upper_raw[i]
                      if upper_raw[i] < f_upper[i - 1] or close_v[i - 1] > f_upper[i - 1]
                      else f_upper[i - 1])
        f_lower[i] = (lower_raw[i]
                      if lower_raw[i] > f_lower[i - 1] or close_v[i - 1] < f_lower[i - 1]
                      else f_lower[i - 1])
        if direction[i - 1] == 1:
            direction[i] = -1.0 if close_v[i] < f_lower[i] else 1.0
        else:
            direction[i] =  1.0 if close_v[i] > f_upper[i] else -1.0

    return pd.Series(direction, index=close.index)


def calculate_ichimoku_signals(high: pd.Series, low: pd.Series, close: pd.Series):
    """
    Ichimoku Kinko Hyo cloud signals (Japanese origin, widely used across Asia).
    Returns (cloud_pos, tk_pos):
      cloud_pos: +1 above cloud, 0 inside, -1 below
      tk_pos:    +1 Tenkan > Kijun (bullish), -1 bearish
    """
    tenkan = (high.rolling(9).max()  + low.rolling(9).min())  / 2
    kijun  = (high.rolling(26).max() + low.rolling(26).min()) / 2
    span_a = (tenkan + kijun) / 2
    span_b = (high.rolling(52).max() + low.rolling(52).min()) / 2

    cloud_top    = pd.concat([span_a, span_b], axis=1).max(axis=1)
    cloud_bottom = pd.concat([span_a, span_b], axis=1).min(axis=1)
    cloud_pos    = ((close > cloud_top).astype(float) -
                    (close < cloud_bottom).astype(float))

    tk_pos = pd.Series(np.where(tenkan > kijun, 1.0, -1.0), index=close.index)
    return cloud_pos, tk_pos


def calculate_52w_levels(high: pd.Series, low: pd.Series, close: pd.Series):
    """
    Returns (pct_from_52w_high, pct_from_52w_low).
    pct_from_52w_high: % below 52-week high (0 = at the high, bullish breakout zone)
    pct_from_52w_low:  % above 52-week low  (0 = at the low, danger zone)
    """
    h52       = high.rolling(252, min_periods=50).max()
    l52       = low.rolling(252,  min_periods=50).min()
    from_high = ((h52 - close) / h52 * 100).clip(0, 100)
    from_low  = ((close - l52) / l52 * 100).clip(0, 200)
    return from_high, from_low


def calculate_vol_regime(atr_pct: pd.Series, lookback: int = 63) -> pd.Series:
    """ATR% percentile rank in its lookback window. 0=calmest, 1=most volatile."""
    def _rank(x: np.ndarray) -> float:
        return float((x[:-1] < x[-1]).sum()) / max(len(x) - 1, 1)
    return atr_pct.rolling(lookback, min_periods=20).apply(_rank, raw=True)


def calculate_fib_position(high: pd.Series, low: pd.Series, close: pd.Series,
                           lookback: int = 120) -> pd.Series:
    """
    Rolling price position within its N-day high-low range — a Fibonacci proximity proxy.
    Returns 0.0 at the N-day low and 1.0 at the N-day high.
    Key Fib zones from the bottom: 0.236, 0.382, 0.500, 0.618, 0.764.
    """
    rolling_high = high.rolling(lookback, min_periods=30).max()
    rolling_low  = low.rolling(lookback, min_periods=30).min()
    rng = (rolling_high - rolling_low).replace(0, np.nan)
    return (close - rolling_low) / rng


def get_fib_levels(high: pd.Series, low: pd.Series, close: pd.Series,
                   lookback: int = 120) -> dict:
    """
    Compute Fibonacci retracement levels from the recent swing high/low.

    Determines trend direction from price position in the range, then
    builds support (uptrend) or resistance (downtrend) retracement levels.

    Returns:
      swing_high, swing_low, trend ('up'/'down'), levels dict,
      nearest_level, nearest_dist_pct, position_pct,
      signal (1=at Fib support, -1=at Fib resistance, 0=neutral),
      signal_level (e.g. '61.8%').
    """
    FIB_RATIOS = [0.0, 0.236, 0.382, 0.500, 0.618, 0.786, 1.0]
    FIB_NAMES  = ["0%", "23.6%", "38.2%", "50%", "61.8%", "78.6%", "100%"]
    PROX_PCT   = 1.5   # within 1.5% of a level = "at" that level

    n = min(lookback, len(close))
    if n < 30:
        return {}

    swing_high = float(high.iloc[-n:].max())
    swing_low  = float(low.iloc[-n:].min())
    rng        = swing_high - swing_low
    if rng <= 0 or swing_low <= 0:
        return {}

    price   = float(close.iloc[-1])
    pos     = (price - swing_low) / rng          # 0.0=at low, 1.0=at high
    uptrend = pos >= 0.50                        # upper half of range = uptrend

    # Uptrend: count DOWN from swing_high (support levels)
    # Downtrend: count UP from swing_low (resistance levels)
    levels: dict[str, float] = {}
    for ratio, name in zip(FIB_RATIOS, FIB_NAMES):
        if uptrend:
            levels[name] = round(swing_high - ratio * rng, 4)
        else:
            levels[name] = round(swing_low  + ratio * rng, 4)

    nearest_name  = min(levels, key=lambda k: abs(levels[k] - price))
    nearest_price = levels[nearest_name]
    nearest_dist  = abs(price - nearest_price) / price * 100

    signal, signal_level = 0, ""
    key_levels = {"38.2%", "50%", "61.8%"}      # highest-confluence S/R zones

    if nearest_dist <= PROX_PCT and nearest_name in key_levels:
        signal       = 1  if uptrend else -1     # support bounce or resistance rejection
        signal_level = nearest_name

    return {
        "swing_high":       round(swing_high, 4),
        "swing_low":        round(swing_low, 4),
        "trend":            "up" if uptrend else "down",
        "levels":           levels,
        "nearest_level":    nearest_name,
        "nearest_price":    round(nearest_price, 4),
        "nearest_dist_pct": round(nearest_dist, 2),
        "signal":           signal,
        "signal_level":     signal_level,
        "position_pct":     round(pos * 100, 1),
    }


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

    # -- Fibonacci proximity (rolling 120-day) ------------------------------------
    fib_pos = calculate_fib_position(high, low, close, lookback=120)
    df["fib_pos_120d"] = fib_pos                      # 0.0=at 120d low, 1.0=at 120d high
    df["fib_dist_38"]  = (fib_pos - 0.382).abs()     # proximity to 38.2% retracement
    df["fib_dist_50"]  = (fib_pos - 0.500).abs()     # proximity to 50% midpoint
    df["fib_dist_62"]  = (fib_pos - 0.618).abs()     # proximity to 61.8% golden ratio

    # Normalised price position relative to key MAs
    df["price_vs_ma20_pct"] = (close - df["ma20"]) / df["ma20"] * 100
    df["price_vs_ma50_pct"] = (close - df["ma50"]) / df["ma50"] * 100

    # -- Enhanced: EMA crossover, oscillators, Ichimoku, Asian-market factors --
    ema9  = calculate_ema(close, 9)
    ema21 = calculate_ema(close, 21)
    df["ema9_ema21_diff"] = (ema9 - ema21) / close.replace(0, np.nan) * 100

    df["cci_20"] = calculate_cci(high, low, close, period=20)
    df["mfi_14"] = calculate_mfi(high, low, close, volume, period=14)
    df["cmf_20"] = calculate_cmf(high, low, close, volume, period=20)

    df["supertrend_dir"] = calculate_supertrend(high, low, close)

    cloud_pos, tk_pos = calculate_ichimoku_signals(high, low, close)
    df["ichimoku_cloud"] = cloud_pos   # +1 above, 0 inside, -1 below
    df["ichimoku_tk"]    = tk_pos      # +1 tenkan>kijun, -1 bearish

    h52, l52 = calculate_52w_levels(high, low, close)
    df["pct_from_52w_high"] = h52      # lower = nearer 52w high = bullish zone
    df["pct_from_52w_low"]  = l52      # lower = nearer 52w low  = danger zone

    df["vol_regime"] = calculate_vol_regime(df["atr_pct"])

    # Overnight gap (gap-up/down patterns matter especially for Asian markets)
    open_p = df.get("Open", close)
    df["gap_pct"] = ((open_p - close.shift(1)) /
                     close.shift(1).replace(0, np.nan) * 100)

    # -- Training targets: multi-timeframe forward returns --
    df["target"]    = (close.shift(-3)  > close).astype(int)
    df["target_5d"] = (close.shift(-5)  > close).astype(int)
    df["target_10d"]= (close.shift(-10) > close).astype(int)

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

    # Fibonacci -- full swing analysis at current price
    high_s   = enriched.get("High",  enriched["Close"])
    low_s    = enriched.get("Low",   enriched["Close"])
    fib_data = get_fib_levels(high_s, low_s, enriched["Close"])

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
        # Fibonacci proximity (per-bar rolling)
        "fib_pos_120d":  safe(last.get("fib_pos_120d")),
        "fib_dist_38":   safe(last.get("fib_dist_38")),
        "fib_dist_50":   safe(last.get("fib_dist_50")),
        "fib_dist_62":   safe(last.get("fib_dist_62")),
        # Enhanced indicators
        "ema9_ema21_diff":    safe(last.get("ema9_ema21_diff")),
        "cci_20":             safe(last.get("cci_20")),
        "mfi_14":             safe(last.get("mfi_14")),
        "cmf_20":             safe(last.get("cmf_20")),
        "supertrend_dir":     safe(last.get("supertrend_dir")),
        "ichimoku_cloud":     safe(last.get("ichimoku_cloud")),
        "ichimoku_tk":        safe(last.get("ichimoku_tk")),
        "pct_from_52w_high":  safe(last.get("pct_from_52w_high")),
        "pct_from_52w_low":   safe(last.get("pct_from_52w_low")),
        "vol_regime":         safe(last.get("vol_regime")),
        "gap_pct":            safe(last.get("gap_pct")),
        # Scalars from full-series analysis
        "rsi_divergence":  float(rsi_div),
        "macd_divergence": float(macd_div),
        # Fibonacci full swing analysis (not stored in DB; used by rule engine)
        "fib_levels":    fib_data,
        # Pass enriched df for any downstream use
        "enriched_df": enriched,
    }
