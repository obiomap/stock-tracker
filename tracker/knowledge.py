"""
Knowledge base for new traders.
Each entry: title, category, summary, sections, quick_tips, related topics.
"""

CATEGORIES = ["Indicators", "Patterns", "Sectors", "Concepts", "Platforms", "Risk Management"]

KNOWLEDGE_BASE: dict[str, dict] = {

    # ── INDICATORS ────────────────────────────────────────────────────────────
    "rsi": {
        "title": "RSI -- Relative Strength Index",
        "category": "Indicators",
        "summary": (
            "RSI measures how fast a stock is rising or falling on a 0-100 scale. "
            "It tells you whether the stock is overbought (likely to pull back) or "
            "oversold (likely to bounce). Developed by J. Welles Wilder in 1978."
        ),
        "sections": [
            {
                "heading": "How it's calculated",
                "content": (
                    "RSI compares average gains to average losses over 14 trading days.\n"
                    "  RSI = 100 - (100 / (1 + RS))  where RS = avg gain / avg loss.\n"
                    "A stock that gains every single day would have RSI near 100; one that "
                    "loses every day would have RSI near 0."
                ),
            },
            {
                "heading": "Key levels to know",
                "content": (
                    "  > 70 -- Overbought: buyers may be exhausted; pullback is possible.\n"
                    "  < 30 -- Oversold: sellers may be exhausted; bounce is possible.\n"
                    "  50 -- Midline: crossing above is bullish, crossing below is bearish.\n"
                    "Note: a stock can stay overbought for weeks in a strong uptrend -- "
                    "RSI alone is not a sell signal."
                ),
            },
            {
                "heading": "RSI divergence",
                "content": (
                    "Divergence is one of RSI's most powerful signals:\n"
                    "  Bearish divergence: price makes a new high but RSI makes a lower high.\n"
                    "    -> momentum is weakening even though price looks strong.\n"
                    "  Bullish divergence: price makes a new low but RSI makes a higher low.\n"
                    "    -> selling pressure is easing; reversal may be near."
                ),
            },
            {
                "heading": "How this app uses RSI",
                "content": (
                    "The dashboard colors RSI red when > 70 (overbought), green when < 30 "
                    "(oversold). Alerts fire when RSI crosses these thresholds. "
                    "RSI is also a feature in the ML prediction model."
                ),
            },
        ],
        "quick_tips": [
            "RSI below 30 doesn't mean 'buy now' -- confirm with price action or volume first.",
            "In strong bull trends, RSI stays 50-80; in bear trends it stays 20-50.",
            "Use RSI on daily charts for swing trades; hourly for short-term moves.",
            "RSI works best when combined with a trend indicator like MACD or moving averages.",
        ],
        "related": ["macd", "bollinger", "moving_averages", "patterns_divergence"],
    },

    "macd": {
        "title": "MACD -- Moving Average Convergence Divergence",
        "category": "Indicators",
        "summary": (
            "MACD tracks the relationship between two exponential moving averages "
            "to reveal trend direction, momentum, and potential reversal points. "
            "It's one of the most widely used momentum indicators."
        ),
        "sections": [
            {
                "heading": "The three components",
                "content": (
                    "  MACD Line: 12-day EMA minus 26-day EMA.\n"
                    "  Signal Line: 9-day EMA of the MACD line (smoother).\n"
                    "  Histogram: MACD Line minus Signal Line (shows momentum speed).\n\n"
                    "When MACD is above zero, the short-term trend is above the long-term "
                    "trend -- bullish. Below zero means the opposite."
                ),
            },
            {
                "heading": "The crossover signal",
                "content": (
                    "  Bullish crossover: MACD line crosses above the signal line.\n"
                    "    -> Short-term momentum accelerating upward.\n"
                    "  Bearish crossover: MACD line crosses below the signal line.\n"
                    "    -> Short-term momentum turning downward.\n\n"
                    "Crossovers near the zero line are stronger signals than those far from it."
                ),
            },
            {
                "heading": "Histogram bars",
                "content": (
                    "Growing histogram bars = momentum is accelerating in that direction.\n"
                    "Shrinking bars = momentum is fading (often happens before a crossover).\n"
                    "Watch for histogram bars shrinking while price continues -- "
                    "that's a warning that the move may be running out of steam."
                ),
            },
        ],
        "quick_tips": [
            "MACD lags price -- it confirms trends rather than predicts them.",
            "Works best in trending markets; generates false signals in choppy sideways action.",
            "A crossover above zero is stronger than a crossover below zero.",
            "Combine MACD with RSI: both bullish = higher conviction trade.",
        ],
        "related": ["rsi", "moving_averages", "volume"],
    },

    "bollinger": {
        "title": "Bollinger Bands",
        "category": "Indicators",
        "summary": (
            "Bollinger Bands wrap a 20-day moving average with upper and lower bands "
            "set 2 standard deviations away. They expand during volatile periods and "
            "contract during quiet ones -- making them a dynamic measure of 'normal' price range."
        ),
        "sections": [
            {
                "heading": "Band structure",
                "content": (
                    "  Middle band: 20-day simple moving average (MA20).\n"
                    "  Upper band: MA20 + (2 x standard deviation).\n"
                    "  Lower band: MA20 - (2 x standard deviation).\n\n"
                    "About 95% of price action occurs within the bands under normal conditions."
                ),
            },
            {
                "heading": "Mean reversion signals",
                "content": (
                    "  Price at upper band: overbought in the short term; may revert to middle.\n"
                    "  Price at lower band: oversold; may bounce back toward middle.\n"
                    "  Price touching a band is not a buy/sell signal by itself -- "
                    "in strong trends, price can 'walk the band' for days."
                ),
            },
            {
                "heading": "The squeeze -- breakout warning",
                "content": (
                    "When the bands get very narrow (a 'squeeze'), volatility is compressed. "
                    "A squeeze typically precedes a large move -- but direction is not guaranteed. "
                    "Watch for the first big candle after a squeeze to indicate direction."
                ),
            },
            {
                "heading": "BB %B in this app",
                "content": (
                    "This app shows BB %B (percent bandwidth): 0 = lower band, 1 = upper band, "
                    "0.5 = middle. Values near 0 suggest oversold; near 1 suggest overbought. "
                    "The ML model uses %B as a feature."
                ),
            },
        ],
        "quick_tips": [
            "The squeeze is your friend -- wait for it, then trade the breakout.",
            "Use Bollinger Bands on 20-day daily charts for swing trades.",
            "Don't short just because price hits the upper band in a strong uptrend.",
            "Combine with RSI: band touch + extreme RSI = higher probability reversal.",
        ],
        "related": ["rsi", "macd", "volume", "patterns_squeeze"],
    },

    "moving_averages": {
        "title": "Moving Averages (MA20, MA50, MA200)",
        "category": "Indicators",
        "summary": (
            "Moving averages smooth out price noise and show trend direction. "
            "The 20, 50, and 200-day MAs are the most watched by institutional investors -- "
            "making them self-fulfilling support and resistance levels."
        ),
        "sections": [
            {
                "heading": "What each MA represents",
                "content": (
                    "  MA20 (20-day): short-term trend -- where is the stock going this month?\n"
                    "  MA50 (50-day): medium-term trend -- the 'health' of a stock's momentum.\n"
                    "  MA200 (200-day): long-term trend -- the line institutional investors use\n"
                    "    to decide if a stock is in a bull or bear phase."
                ),
            },
            {
                "heading": "Price vs MA -- simple signals",
                "content": (
                    "  Price > MA200: stock is in a long-term uptrend (bullish bias).\n"
                    "  Price < MA200: stock is in a long-term downtrend (bearish bias).\n"
                    "  Price crossing MA50 from below: medium-term bullish signal.\n"
                    "  Price bouncing off MA50: the MA acted as support -- continuation signal."
                ),
            },
            {
                "heading": "Golden Cross & Death Cross",
                "content": (
                    "  Golden Cross: MA50 crosses above MA200.\n"
                    "    -> One of the most bullish signals; triggers major institutional buying.\n"
                    "  Death Cross: MA50 crosses below MA200.\n"
                    "    -> Major bearish signal; often leads to sustained selling pressure."
                ),
            },
        ],
        "quick_tips": [
            "The MA200 is the most important line on any chart -- know where it is.",
            "In uptrends, MAs act as support (price bounces up). In downtrends, they act as resistance.",
            "When MA20 > MA50 > MA200, all trends are aligned bullish -- high conviction.",
            "Avoid buying stocks far above their MA200; mean reversion risk is high.",
        ],
        "related": ["macd", "patterns_golden_cross", "rsi"],
    },

    "volume": {
        "title": "Volume Analysis",
        "category": "Indicators",
        "summary": (
            "Volume is the number of shares traded in a day. It confirms the conviction "
            "behind price moves: a big price move on high volume is far more meaningful "
            "than the same move on low volume. Volume is often called 'the fuel' of price action."
        ),
        "sections": [
            {
                "heading": "Volume confirms trends",
                "content": (
                    "  Rising price + rising volume: strong uptrend -- institutions are buying.\n"
                    "  Rising price + falling volume: weak uptrend -- buying is losing steam.\n"
                    "  Falling price + rising volume: strong selling -- get out or wait.\n"
                    "  Falling price + falling volume: weak selling -- may consolidate and reverse."
                ),
            },
            {
                "heading": "Volume spikes",
                "content": (
                    "A spike of 2x or more the average daily volume signals something significant:\n"
                    "  Spike up on news: institutional buying -- often continues short-term.\n"
                    "  Spike on a down day: capitulation -- sellers exhausted, possible bottom.\n"
                    "  Spike with no news: insider activity or algorithmic trigger -- watch closely."
                ),
            },
            {
                "heading": "How this app uses volume",
                "content": (
                    "Volume spikes (2x avg) trigger alerts. The volume ratio (today vs 20-day avg) "
                    "appears in the dashboard. The ML model uses volume ratio to detect "
                    "unusual institutional activity before earnings or breakouts."
                ),
            },
        ],
        "quick_tips": [
            "Never trust a breakout to new highs on low volume -- it often fails.",
            "Huge volume at the end of a long downtrend = climax selling = potential bottom.",
            "Pre-market and after-hours volume confirms earnings reaction direction.",
            "Compare volume to 20-day average, not just yesterday's volume.",
        ],
        "related": ["patterns_breakout", "macd", "rsi"],
    },

    # ── PATTERNS ──────────────────────────────────────────────────────────────
    "patterns_earnings_drift": {
        "title": "Pre-Earnings Drift",
        "category": "Patterns",
        "summary": (
            "Stocks often drift upward in the 2-5 days before earnings as traders "
            "bet on a positive surprise. This 'pre-earnings drift' is one of the "
            "most well-documented anomalies in market research."
        ),
        "sections": [
            {
                "heading": "Why it happens",
                "content": (
                    "Analysts and informed traders buy in advance of expected beats.\n"
                    "Options market makers hedge by buying the underlying stock.\n"
                    "Retail FOMO kicks in as earnings approach and media coverage increases.\n"
                    "Result: stocks with strong recent momentum tend to drift up 1-3% in the days before earnings."
                ),
            },
            {
                "heading": "The earnings reaction",
                "content": (
                    "After earnings are announced, the stock reacts to:\n"
                    "  1. The actual numbers vs analyst estimates (EPS and revenue).\n"
                    "  2. Forward guidance -- what management says about the future.\n"
                    "  3. Market conditions on the day (risk-on vs risk-off).\n\n"
                    "A beat with weak guidance often sells off. A miss with strong guidance may rally."
                ),
            },
            {
                "heading": "Historical reaction in this app",
                "content": (
                    "For each stock in your watchlist, this app calculates the average "
                    "next-day price move following past earnings. A stock with an avg reaction "
                    "of +6% has historically jumped 6% after earnings -- useful context "
                    "for sizing risk around that event."
                ),
            },
        ],
        "quick_tips": [
            "Never hold through earnings unless you understand the risk -- gap-downs of 20%+ happen.",
            "Implied volatility (options price) spikes before earnings and collapses after (IV crush).",
            "The avg historical reaction is a guide, not a guarantee -- every quarter is different.",
            "Consider reducing position size before earnings, not increasing it.",
        ],
        "related": ["volume", "patterns_gap", "concepts_eps"],
    },

    "patterns_golden_cross": {
        "title": "Golden Cross & Death Cross",
        "category": "Patterns",
        "summary": (
            "A Golden Cross occurs when the 50-day MA crosses above the 200-day MA -- "
            "a major bullish signal. The opposite, the Death Cross, is a major bearish signal. "
            "These crossovers trigger large institutional buy/sell programs."
        ),
        "sections": [
            {
                "heading": "Golden Cross",
                "content": (
                    "Conditions: MA50 crosses above MA200.\n"
                    "Meaning: the medium-term trend is now stronger than the long-term trend.\n"
                    "What happens: pension funds and quant strategies that were avoiding the stock\n"
                    "  start buying. This often creates a sustained rally.\n"
                    "Best after: a prolonged downtrend followed by base-building consolidation."
                ),
            },
            {
                "heading": "Death Cross",
                "content": (
                    "Conditions: MA50 crosses below MA200.\n"
                    "Meaning: the medium-term trend has weakened below the long-term trend.\n"
                    "What happens: institutional selling accelerates. Momentum traders short the stock.\n"
                    "Caveat: the death cross is a lagging signal -- stock may have already fallen 20%+ "
                    "before the cross occurs."
                ),
            },
            {
                "heading": "False crossovers",
                "content": (
                    "In choppy markets, the MAs can cross back and forth, creating false signals. "
                    "Always confirm with:\n"
                    "  - High volume on the breakout\n"
                    "  - RSI above 50 for golden cross (below 50 for death cross)\n"
                    "  - Positive sector and market context"
                ),
            },
        ],
        "quick_tips": [
            "Golden cross on SPY means the broad market is in a bull phase -- great tailwind.",
            "Don't blindly buy a golden cross -- wait for a pullback to the MA50 for better entry.",
            "Death crosses on individual stocks often come during earnings-driven breakdowns.",
            "Index golden crosses (SPY, QQQ) are more reliable than individual stock ones.",
        ],
        "related": ["moving_averages", "volume", "patterns_breakout"],
    },

    "patterns_breakout": {
        "title": "Breakouts & Breakdowns",
        "category": "Patterns",
        "summary": (
            "A breakout is when price moves above a resistance level -- a price ceiling the stock "
            "has failed to break through multiple times. A breakdown is the opposite. "
            "High-volume breakouts are among the highest probability setups in trading."
        ),
        "sections": [
            {
                "heading": "What creates resistance levels",
                "content": (
                    "  Previous highs: sellers who bought at the top want to 'get out even.'\n"
                    "  Round numbers ($100, $500): psychological anchors -- large options positions cluster here.\n"
                    "  Moving averages: MA50 and MA200 act as dynamic resistance in downtrends.\n"
                    "  52-week highs: many institutional mandates require stocks at new highs."
                ),
            },
            {
                "heading": "Valid vs false breakout",
                "content": (
                    "Valid breakout signs:\n"
                    "  - Price closes above resistance (not just touches and retreats)\n"
                    "  - Volume is 1.5x or more the 20-day average on breakout day\n"
                    "  - Breakout happens in a healthy market (SPY not in downtrend)\n\n"
                    "False breakout (fakeout):\n"
                    "  - Breaks above resistance on low volume, then closes back below\n"
                    "  - Often a trap for retail buyers; institutions sell into the move"
                ),
            },
        ],
        "quick_tips": [
            "The best breakouts are from long, tight consolidation bases (4+ weeks).",
            "A stock breaking to all-time highs has zero overhead resistance -- can run far.",
            "After a breakout, the old resistance level becomes new support.",
            "If a breakout fails quickly, exit -- false breakouts often reverse hard.",
        ],
        "related": ["volume", "moving_averages", "patterns_golden_cross"],
    },

    "patterns_gap": {
        "title": "Gap Up & Gap Down",
        "category": "Patterns",
        "summary": (
            "A gap occurs when a stock opens significantly higher or lower than its previous close, "
            "leaving an empty space on the chart. Gaps often happen after earnings or major news, "
            "and their behavior afterward follows identifiable patterns."
        ),
        "sections": [
            {
                "heading": "Types of gaps",
                "content": (
                    "  Breakaway gap: stock gaps out of a base on high volume -- continuation likely.\n"
                    "  Exhaustion gap: stock gaps after a long move -- trend may be ending.\n"
                    "  Earnings gap: price jumps on earnings results -- most common in this app.\n"
                    "  Common gap: fills quickly; usually not significant."
                ),
            },
            {
                "heading": "Gap fill",
                "content": (
                    "Over 70% of gaps eventually 'fill' -- price returns to the pre-gap level.\n"
                    "  Earnings gaps down: painful but often partially fill over 1-4 weeks.\n"
                    "  Earnings gaps up: strong gaps on great guidance often don't fill for months.\n"
                    "Institutional traders often buy gap-fills as low-risk entries."
                ),
            },
        ],
        "quick_tips": [
            "Never chase a gap-up open -- wait for the first 30 min to see if it holds.",
            "Gap-downs on earnings with guidance cuts are more dangerous than pure misses.",
            "A stock that gaps up and keeps climbing through the day is very strong.",
            "Gaps on no news are more suspicious -- check for insider trades.",
        ],
        "related": ["patterns_earnings_drift", "volume", "concepts_eps"],
    },

    # ── CONCEPTS ──────────────────────────────────────────────────────────────
    "concepts_bull_bear": {
        "title": "Bull Market vs Bear Market",
        "category": "Concepts",
        "summary": (
            "A bull market is a sustained period of rising stock prices (typically +20% from lows). "
            "A bear market is a sustained decline of 20%+ from recent highs. "
            "Understanding which market you're in changes everything about how you trade."
        ),
        "sections": [
            {
                "heading": "Bull market characteristics",
                "content": (
                    "  - SPY and QQQ making higher highs and higher lows.\n"
                    "  - Most stocks above their 200-day moving average.\n"
                    "  - Investor sentiment is confident; news is mostly positive.\n"
                    "  - Growth stocks and risk assets outperform.\n"
                    "  - Average bull market lasts ~3.8 years and gains ~150%."
                ),
            },
            {
                "heading": "Bear market characteristics",
                "content": (
                    "  - SPY down 20%+ from its recent peak.\n"
                    "  - Most stocks below their 200-day moving average.\n"
                    "  - Defensive sectors (healthcare, utilities, consumer staples) outperform.\n"
                    "  - Cash, bonds, and gold tend to hold value better.\n"
                    "  - Average bear market lasts ~1.4 years and loses ~36%."
                ),
            },
            {
                "heading": "Trading strategy changes",
                "content": (
                    "In a bull market:\n"
                    "  Buy dips, hold longer, use breakout setups.\n\n"
                    "In a bear market:\n"
                    "  Reduce size, take profits faster, consider defensive sectors or cash.\n"
                    "  'Don't fight the tape' -- avoid buying falling stocks hoping for a bottom."
                ),
            },
        ],
        "quick_tips": [
            "Check SPY vs its MA200 first every morning -- it sets the context for all other trades.",
            "Bull market corrections (10-20% drops) are buying opportunities, not exits.",
            "In bear markets, even good companies fall -- the tide lifts/sinks all boats.",
            "Bear markets end on bad news being ignored. Bull markets end on good news being ignored.",
        ],
        "related": ["moving_averages", "concepts_market_cap", "risk_diversification"],
    },

    "concepts_market_cap": {
        "title": "Market Capitalization",
        "category": "Concepts",
        "summary": (
            "Market cap = share price x total shares outstanding. It's the total market value "
            "of a company. Market cap determines which index a stock belongs to, how much "
            "volatility to expect, and the type of investor it attracts."
        ),
        "sections": [
            {
                "heading": "Cap tiers",
                "content": (
                    "  Mega cap  (> $200B):  Apple, Microsoft, NVDA. Most stable.\n"
                    "  Large cap ($10B-$200B): established companies, index members.\n"
                    "  Mid cap   ($2B-$10B):  growing companies, more volatile than large.\n"
                    "  Small cap ($300M-$2B): high growth potential, high risk.\n"
                    "  Micro cap (< $300M):   speculative, often illiquid, very volatile."
                ),
            },
            {
                "heading": "Why it matters for trading",
                "content": (
                    "  Small caps move faster but are riskier -- institutional money avoids them.\n"
                    "  Large caps have tighter bid-ask spreads and better liquidity.\n"
                    "  Index inclusion forces passive funds to buy -- huge demand event.\n"
                    "  A stock growing into the next cap tier is a powerful long-term catalyst."
                ),
            },
        ],
        "quick_tips": [
            "NVDA joining the Dow Jones caused massive index-fund buying -- an example of index effect.",
            "Small cap stocks lead bull markets early but fall harder in bear markets.",
            "Market cap tells you size, not quality -- a $1B company can be great or terrible.",
            "Dilution (new share issuance) increases shares outstanding -- watch for it.",
        ],
        "related": ["concepts_bull_bear", "concepts_pe_ratio"],
    },

    "concepts_pe_ratio": {
        "title": "P/E Ratio -- Price-to-Earnings",
        "category": "Concepts",
        "summary": (
            "P/E = Share Price / Earnings Per Share. It tells you how much investors are "
            "willing to pay for each dollar of profit. A high P/E means investors expect "
            "strong future growth; a low P/E means growth is expected to be slow."
        ),
        "sections": [
            {
                "heading": "Interpreting P/E",
                "content": (
                    "  S&P 500 avg P/E: ~20-25x (fair value range).\n"
                    "  < 15x: potentially undervalued or slow-growth industry.\n"
                    "  15-25x: roughly market average -- reasonable for most companies.\n"
                    "  > 40x: high growth expected; valuation depends on future earnings.\n"
                    "  Negative P/E: company is unprofitable (common in early-stage tech/biotech)."
                ),
            },
            {
                "heading": "P/E limitations",
                "content": (
                    "  Backward-looking: uses trailing 12-month earnings.\n"
                    "  Forward P/E uses estimated next-year earnings -- more useful for growth stocks.\n"
                    "  Two companies can have the same P/E but very different growth rates.\n"
                    "  Always compare P/E to industry peers, not the whole market."
                ),
            },
            {
                "heading": "PEG ratio -- the better metric",
                "content": (
                    "PEG = P/E / Expected Earnings Growth Rate.\n"
                    "  PEG < 1: potentially undervalued relative to growth.\n"
                    "  PEG = 1: fairly valued.\n"
                    "  PEG > 2: expensive relative to growth expectations.\n"
                    "NVDA had a P/E of 60 but a PEG of 1.2 during peak AI growth -- actually 'cheap'."
                ),
            },
        ],
        "quick_tips": [
            "High P/E stocks (50x+) are priced for perfection -- any miss causes violent drops.",
            "Low P/E value stocks can stay cheap for years if growth doesn't materialize.",
            "Use P/E to compare companies within the same sector, not across sectors.",
            "Tech companies have naturally higher P/E than banks or utilities -- that's normal.",
        ],
        "related": ["concepts_eps", "concepts_market_cap", "concepts_bull_bear"],
    },

    "concepts_eps": {
        "title": "EPS -- Earnings Per Share & Earnings Reports",
        "category": "Concepts",
        "summary": (
            "EPS = Net Income / Shares Outstanding. It's the most watched number in every "
            "quarterly earnings report. Whether a company beats or misses EPS estimates -- "
            "and what they say about the future -- drives some of the largest single-day stock moves."
        ),
        "sections": [
            {
                "heading": "What an earnings report contains",
                "content": (
                    "  Revenue: total sales -- is the business growing?\n"
                    "  EPS: profit per share -- is it profitable?\n"
                    "  Guidance: what management expects next quarter/year -- often more important\n"
                    "    than the current quarter's numbers.\n"
                    "  Margins: gross and operating margin -- is profitability improving?\n"
                    "  Key metrics: MAU, ARR, units shipped -- varies by industry."
                ),
            },
            {
                "heading": "Beat vs miss",
                "content": (
                    "  Beat: actual EPS > analyst consensus estimate.\n"
                    "    -> Usually causes gap-up; size depends on guidance and margins.\n"
                    "  Miss: actual EPS < analyst consensus estimate.\n"
                    "    -> Usually causes gap-down; severity depends on guidance.\n"
                    "  In-line: meets estimates exactly -- often disappointing if priced for a beat."
                ),
            },
            {
                "heading": "Guidance is king",
                "content": (
                    "A company can beat earnings but guide lower and the stock falls 15%.\n"
                    "It can miss earnings but raise guidance and the stock jumps 10%.\n"
                    "Always read the press release for management's outlook, "
                    "not just the headline EPS number."
                ),
            },
        ],
        "quick_tips": [
            "Look at the whisper number (unofficial estimate) vs official consensus -- the gap matters.",
            "Stocks often sell off on great earnings if 'good news was already priced in.'",
            "Small caps with first profitable quarter often see explosive moves.",
            "Earnings dates for your watchlist appear in this app's earnings panel.",
        ],
        "related": ["patterns_earnings_drift", "concepts_pe_ratio", "patterns_gap"],
    },

    "concepts_short_selling": {
        "title": "Short Selling",
        "category": "Concepts",
        "summary": (
            "Short selling is borrowing shares and selling them, hoping to buy them back cheaper later. "
            "It's how traders profit from falling prices. Understanding it helps you read sentiment "
            "indicators and recognize short squeeze setups."
        ),
        "sections": [
            {
                "heading": "How it works",
                "content": (
                    "  1. Borrow shares from your broker.\n"
                    "  2. Sell them at current price ($100).\n"
                    "  3. Wait for price to fall.\n"
                    "  4. Buy them back at lower price ($80) -- 'covering' the short.\n"
                    "  5. Return shares to broker. Profit = $20 per share.\n\n"
                    "Risk: if price rises, losses are theoretically unlimited."
                ),
            },
            {
                "heading": "Short squeeze",
                "content": (
                    "When a heavily shorted stock rises sharply, short sellers are forced to "
                    "buy to limit losses -- driving the price even higher. This cascading effect "
                    "is a 'short squeeze.'\n\n"
                    "GameStop (GME) in 2021 is the most famous example -- rose 1,700% in weeks "
                    "as short sellers were squeezed by retail traders coordinating on Reddit."
                ),
            },
            {
                "heading": "Short interest as a signal",
                "content": (
                    "Short Interest = shares sold short / total float.\n"
                    "  > 20%: heavily shorted -- potential squeeze candidate if bullish catalyst arrives.\n"
                    "  < 5%: lightly shorted -- market broadly agrees with the bullish thesis.\n"
                    "Days to Cover = shares short / avg daily volume.\n"
                    "  > 5 days: squeeze potential is higher if stock moves against shorts."
                ),
            },
        ],
        "quick_tips": [
            "Never short a stock just because it 'seems too expensive' -- expensive can get more expensive.",
            "Short squeezes are violent and fast -- dangerous to fight if you're short.",
            "High short interest + positive catalyst = potential explosive move up.",
            "Most retail traders should avoid shorting -- risk is asymmetric and complex.",
        ],
        "related": ["concepts_bull_bear", "volume", "patterns_breakout"],
    },

    # ── RISK MANAGEMENT ───────────────────────────────────────────────────────
    "risk_position_sizing": {
        "title": "Position Sizing",
        "category": "Risk Management",
        "summary": (
            "Position sizing determines how much of your portfolio you put into a single trade. "
            "It's arguably the most important risk management decision. Even a great strategy "
            "fails if positions are sized too large."
        ),
        "sections": [
            {
                "heading": "The 1-2% rule",
                "content": (
                    "Risk no more than 1-2% of your total portfolio on any single trade.\n\n"
                    "Example: $10,000 portfolio. Max risk = $100-200 per trade.\n"
                    "If you buy AAPL at $300 with a stop-loss at $290 ($10 risk per share),\n"
                    "you can buy 10-20 shares -- not more.\n\n"
                    "This ensures a string of 10 losses only costs you 10-20%, not everything."
                ),
            },
            {
                "heading": "Adjusting for conviction",
                "content": (
                    "Not all ideas are equal. Size positions by confidence:\n"
                    "  High conviction (multiple signals aligned): up to 2% risk.\n"
                    "  Medium conviction (1-2 signals): 1% risk.\n"
                    "  Low conviction / speculative: 0.5% risk.\n\n"
                    "Never put more than 10-15% of your portfolio in one stock."
                ),
            },
            {
                "heading": "Before earnings rule",
                "content": (
                    "Earnings can gap a stock 15-25% overnight. Consider cutting position "
                    "size by 50% before earnings unless you've specifically analyzed the setup. "
                    "The few extra percent of gain is rarely worth the tail risk."
                ),
            },
        ],
        "quick_tips": [
            "Pros obsess over how much to risk, not just whether to buy.",
            "You can be right 40% of the time and make money with good position sizing.",
            "Overconfidence = oversizing = one trade wiping out months of gains.",
            "After a losing streak, reduce size -- protect capital first, recover second.",
        ],
        "related": ["risk_stop_loss", "risk_diversification", "risk_reward"],
    },

    "risk_stop_loss": {
        "title": "Stop Loss Orders",
        "category": "Risk Management",
        "summary": (
            "A stop-loss is a pre-set exit price that automatically sells your position "
            "if the stock falls to that level. It removes emotion from losing trades "
            "and protects your capital from catastrophic losses."
        ),
        "sections": [
            {
                "heading": "Types of stop-loss",
                "content": (
                    "  Hard stop: a market order triggers when price hits your level.\n"
                    "    Guaranteed exit but may fill worse in fast markets.\n"
                    "  Mental stop: you commit to exiting manually at a level.\n"
                    "    Requires discipline -- emotion often delays the sell.\n"
                    "  Trailing stop: stop moves up as price rises (e.g. 8% below peak).\n"
                    "    Locks in profits while letting winners run."
                ),
            },
            {
                "heading": "Where to place a stop",
                "content": (
                    "  Below a key support level (recent swing low).\n"
                    "  Below a major moving average (MA50 for swing trades, MA200 for long-term).\n"
                    "  A fixed percentage below entry (7-10% is common for growth stocks).\n\n"
                    "Don't place a stop at round numbers ($100, $200) -- that's where everyone "
                    "puts them; institutions often 'stop hunt' to that level before reversing."
                ),
            },
            {
                "heading": "The psychology of stops",
                "content": (
                    "Most losses that become catastrophic started as 'I'll wait for it to come back.'\n"
                    "A 50% loss requires a 100% gain to break even.\n"
                    "Set your stop when you enter -- not after the stock has moved against you."
                ),
            },
        ],
        "quick_tips": [
            "If a stop gets hit, don't immediately re-enter -- let the trade prove itself.",
            "Moving your stop further away to avoid being stopped out is almost always wrong.",
            "Paper trading with stops builds the discipline to use them in real trades.",
            "The best traders lose small and win big -- stops make that possible.",
        ],
        "related": ["risk_position_sizing", "risk_reward", "risk_diversification"],
    },

    "risk_diversification": {
        "title": "Diversification",
        "category": "Risk Management",
        "summary": (
            "Diversification spreads your capital across multiple uncorrelated assets to reduce "
            "the impact of any single loss. It doesn't eliminate risk, but it smooths returns "
            "and prevents one bad bet from ruining your portfolio."
        ),
        "sections": [
            {
                "heading": "Diversification across stocks",
                "content": (
                    "  Hold 10-20 stocks across different sectors.\n"
                    "  Avoid putting >15% in one stock, >30% in one sector.\n"
                    "  AI and tech stocks are highly correlated -- owning 10 AI stocks\n"
                    "    is NOT diversification; they often all fall together."
                ),
            },
            {
                "heading": "Diversification across asset classes",
                "content": (
                    "  Stocks + Bonds: bonds often rise when stocks fall.\n"
                    "  Stocks + Gold: gold is a hedge against systemic risk.\n"
                    "  ETFs (SPY, QQQ, XLK): instant sector diversification in one ticker.\n"
                    "  Geographic: US + international = less exposure to US-specific risk."
                ),
            },
            {
                "heading": "Over-diversification",
                "content": (
                    "Owning 50+ individual stocks is effectively an expensive index fund.\n"
                    "You won't beat the market with that many positions, but you'll pay more in fees.\n"
                    "Concentrate on your highest-conviction ideas -- diversify enough to survive "
                    "any single stock disaster, not so much that nothing matters."
                ),
            },
        ],
        "quick_tips": [
            "The first ETF you buy (SPY or QQQ) instantly gives you 100-500 stock exposure.",
            "Correlation is the enemy of diversification -- check if your stocks move together.",
            "Sector ETFs in this app (XLK, XLV, XLF) let you bet on sectors without stock risk.",
            "Annual rebalancing keeps allocation percentages from drifting due to winners growing.",
        ],
        "related": ["risk_position_sizing", "risk_stop_loss", "concepts_bull_bear"],
    },

    "risk_reward": {
        "title": "Risk/Reward Ratio",
        "category": "Risk Management",
        "summary": (
            "The risk/reward ratio compares your potential loss (if wrong) to your potential "
            "gain (if right). Professional traders require at least 1:2 -- willing to risk $1 "
            "only if the reward potential is $2 or more."
        ),
        "sections": [
            {
                "heading": "Calculating risk/reward",
                "content": (
                    "  Entry: $100. Stop loss: $95. Target: $115.\n"
                    "  Risk = $5 (5%). Reward = $15 (15%). Ratio = 1:3.\n\n"
                    "With a 1:3 ratio and 40% win rate:\n"
                    "  4 wins x $15 = $60. 6 losses x $5 = $30. Net: +$30.\n"
                    "Even losing more than you win, you're profitable."
                ),
            },
            {
                "heading": "How to find high R/R setups",
                "content": (
                    "  Buy near support (stop just below) with resistance far above.\n"
                    "  Buy breakouts from tight bases -- stop is tight, target is the next level.\n"
                    "  Avoid 'chasing' stocks that have already moved 20% -- risk is high, reward low.\n"
                    "  Pre-earnings drift: defined risk (exit before earnings) with 2-3% upside."
                ),
            },
        ],
        "quick_tips": [
            "If you can't see a 1:2 risk/reward setup, don't take the trade.",
            "Your target should be set before you enter, not adjusted upward when price rises.",
            "Partial profit-taking at 1:1 removes risk while letting remainder run.",
            "Bad trades often have poor R/R -- low reward for high risk. Discipline fixes this.",
        ],
        "related": ["risk_stop_loss", "risk_position_sizing", "risk_diversification"],
    },

    # ── SECTOR GUIDES ─────────────────────────────────────────────────────────
    "sector_ai": {
        "title": "AI & Machine Learning Sector",
        "category": "Sectors",
        "summary": (
            "The AI sector is the highest-growth area in the market, driven by the buildout "
            "of foundation models, AI infrastructure, and enterprise adoption. "
            "It's also the most volatile -- valuations are extreme and sentiment shifts fast."
        ),
        "sections": [
            {
                "heading": "What drives AI stocks",
                "content": (
                    "  GPU and cloud compute demand: NVDA earnings are the sector's heartbeat.\n"
                    "  Foundation model releases: GPT-5, Gemini Ultra, Claude 4 announcements move stocks.\n"
                    "  Enterprise AI spending: CIOs allocating budget signals real adoption.\n"
                    "  Regulation: EU AI Act, US executive orders create compliance risk.\n"
                    "  Export controls: US chip restrictions on China are a recurring risk for NVDA/AMD."
                ),
            },
            {
                "heading": "Layers of the AI stack",
                "content": (
                    "  Infrastructure: NVDA (chips), MSFT/AMZN/GOOGL (cloud compute).\n"
                    "  Models: MSFT (OpenAI), GOOGL (Gemini), META (LLaMA), AMZN (Bedrock).\n"
                    "  Applications: PLTR (enterprise), SOUN (voice), AI (C3.ai), CRM (Salesforce AI).\n\n"
                    "Infrastructure is safest (real revenue today). Applications are highest risk/reward."
                ),
            },
            {
                "heading": "Risks specific to AI",
                "content": (
                    "  Valuation: many AI stocks trade at 50-100x earnings -- any slowdown causes big drops.\n"
                    "  Competition: open-source models (LLaMA) could commoditize the AI stack.\n"
                    "  Concentration: 5 stocks (NVDA, MSFT, GOOGL, META, AMZN) = 80% of AI exposure.\n"
                    "  Hype cycles: AI was called 'overhyped' in 2024 before NVDA doubled again."
                ),
            },
        ],
        "quick_tips": [
            "NVDA earnings are the single most important catalyst for the entire AI sector.",
            "The infrastructure layer (chips, cloud) has real revenue; application layer has promises.",
            "AI sector correlates highly -- when NVDA falls 10%, most AI stocks fall with it.",
            "Watch Microsoft's Azure growth rate -- it's the most reliable AI adoption indicator.",
        ],
        "related": ["sector_semiconductors", "sector_technology", "concepts_pe_ratio"],
    },

    "sector_quantum": {
        "title": "Quantum Computing Sector",
        "category": "Sectors",
        "summary": (
            "Quantum computing is a pre-commercial technology that uses quantum mechanical effects "
            "to solve problems impossible for classical computers. Stocks in this space are highly "
            "speculative -- most companies have minimal revenue and depend on research contracts."
        ),
        "sections": [
            {
                "heading": "How quantum computing works (simply)",
                "content": (
                    "Classical computers use bits (0 or 1). Quantum computers use qubits, "
                    "which can be 0, 1, or both simultaneously (superposition). "
                    "This lets them process exponentially more combinations at once -- "
                    "making them theoretically ideal for cryptography, drug discovery, and optimization."
                ),
            },
            {
                "heading": "Current state of the technology",
                "content": (
                    "  We are in the 'NISQ era' -- Noisy Intermediate-Scale Quantum.\n"
                    "  Current machines (100-1000 qubits) are too error-prone for commercial advantage.\n"
                    "  Fault-tolerant quantum computing (millions of logical qubits) is 5-15 years away.\n"
                    "  Google's 'Willow' chip in 2024 solved a specific benchmark faster -- not yet practical."
                ),
            },
            {
                "heading": "Trading quantum stocks",
                "content": (
                    "  IONQ, RGTI, QUBT are speculative micro/small caps -- extreme volatility.\n"
                    "  IBM and GOOGL have quantum divisions but it's a tiny part of revenue.\n"
                    "  These stocks move on headlines (government contracts, research papers).\n"
                    "  Keep position sizes very small (max 1-2% of portfolio) given the risk."
                ),
            },
        ],
        "quick_tips": [
            "Treat quantum stocks as speculative bets, not investments -- size accordingly.",
            "A government or enterprise contract announcement can double a quantum stock in a day.",
            "IONQ is the most liquid pure-play quantum stock; tightest spreads for trading.",
            "Google and IBM are safer ways to get quantum exposure with much lower risk.",
        ],
        "related": ["sector_ai", "sector_technology", "risk_position_sizing"],
    },

    "sector_etfs": {
        "title": "ETFs for New Traders",
        "category": "Sectors",
        "summary": (
            "ETFs (Exchange-Traded Funds) are baskets of stocks that trade like a single share. "
            "They're the ideal starting point for new traders -- instant diversification, "
            "low cost, and easy to understand. Most professional investors use them."
        ),
        "sections": [
            {
                "heading": "Why ETFs first",
                "content": (
                    "  SPY (S&P 500) has beaten most active fund managers over 10+ year periods.\n"
                    "  One share of QQQ gives you exposure to Apple, Microsoft, NVDA, Amazon, and 96 more.\n"
                    "  Expense ratios are low: SPY charges 0.095%/year vs 1%+ for active funds.\n"
                    "  Less research required: you're betting on the sector, not one company."
                ),
            },
            {
                "heading": "Key ETFs in this app",
                "content": (
                    "  SPY: follow this daily -- it's the market's pulse.\n"
                    "  QQQ: tech-heavy; a proxy for innovation and growth sentiment.\n"
                    "  XLK: pure technology sector -- AAPL and MSFT are ~40% of it.\n"
                    "  XLV: healthcare -- defensive in bear markets.\n"
                    "  ARKK: high-risk/reward disruptive tech -- extremely volatile.\n"
                    "  SOXX: semiconductors -- best way to play the AI chip theme broadly."
                ),
            },
            {
                "heading": "Sector rotation using ETFs",
                "content": (
                    "Professional investors move money between sector ETFs based on the economic cycle:\n"
                    "  Early recovery: XLY (consumer), XLK (tech) lead.\n"
                    "  Mid expansion: XLI (industrials), XLF (financials) lead.\n"
                    "  Late cycle: XLE (energy), XLV (healthcare) hold up best.\n"
                    "  Recession: XLV, XLP (staples), and cash outperform."
                ),
            },
        ],
        "quick_tips": [
            "Start with SPY -- understand how the market moves before individual stocks.",
            "Dollar-cost averaging (buying fixed amounts regularly) into ETFs beats most active strategies.",
            "Leveraged ETFs (3x) decay over time -- only for short-term trades, never buy-and-hold.",
            "Check the ETF's top holdings -- XLK is 40% Apple+Microsoft, so it's concentrated.",
        ],
        "related": ["concepts_bull_bear", "risk_diversification", "sector_ai"],
    },

    # ── PLATFORMS ─────────────────────────────────────────────────────────────
    "platforms_overview": {
        "title": "Choosing a Trading Platform",
        "category": "Platforms",
        "summary": (
            "Your broker is your gateway to the markets. Different platforms suit different "
            "traders: beginners need simplicity, active traders need speed and tools, "
            "long-term investors need low fees and good research. Here's how the major ones compare."
        ),
        "sections": [
            {
                "heading": "Robinhood -- best for beginners",
                "content": (
                    "  Pros: zero commissions, clean app, fractional shares ($1 minimum),\n"
                    "    instant deposits up to $1,000, crypto trading included.\n"
                    "  Cons: limited research tools, no mutual funds, basic charting,\n"
                    "    payment for order flow means slightly worse fill prices.\n"
                    "  Best for: first-time investors, small accounts, simple buy-and-hold.\n"
                    "  Sign up: https://robinhood.com"
                ),
            },
            {
                "heading": "Fidelity -- best overall for most investors",
                "content": (
                    "  Pros: no commissions, excellent research (own analysts + 3rd party),\n"
                    "    fractional shares, excellent retirement accounts (IRA, 401k rollover),\n"
                    "    no payment for order flow = better fills, 24/7 customer support.\n"
                    "  Cons: app is less sleek than Robinhood, options UI is dated.\n"
                    "  Best for: long-term investors, retirement savings, serious traders.\n"
                    "  Sign up: https://www.fidelity.com"
                ),
            },
            {
                "heading": "Schwab/thinkorswim -- best for active traders",
                "content": (
                    "  Pros: thinkorswim platform is professional-grade, powerful charting,\n"
                    "    paper trading (practice with fake money), extensive options tools,\n"
                    "    excellent education resources, no commissions on stocks/ETFs.\n"
                    "  Cons: thinkorswim can be overwhelming for beginners.\n"
                    "  Best for: options traders, technical analysts, active day traders.\n"
                    "  Sign up: https://www.schwab.com | thinkorswim: https://www.schwab.com/trading/thinkorswim"
                ),
            },
            {
                "heading": "Interactive Brokers (IBKR) -- best for professionals",
                "content": (
                    "  Pros: access to 150+ global markets, lowest margin rates (5-6% vs 8-12%),\n"
                    "    fractional shares, professional tools, best for large accounts.\n"
                    "  Cons: complex interface, $0 stock trades but per-share options fees.\n"
                    "  Best for: experienced traders, international investing, large portfolios.\n"
                    "  Sign up: https://www.interactivebrokers.com"
                ),
            },
            {
                "heading": "Webull -- best free technical analysis",
                "content": (
                    "  Pros: free advanced charting, extended hours trading, paper trading,\n"
                    "    more technical indicators than Robinhood, no commissions.\n"
                    "  Cons: Chinese-owned (data privacy concern for some), less intuitive.\n"
                    "  Best for: technically-minded beginners who want more than Robinhood offers.\n"
                    "  Sign up: https://www.webull.com"
                ),
            },
        ],
        "quick_tips": [
            "Start with Robinhood or Fidelity -- you can always transfer your account later.",
            "Check if the platform offers paper trading to practice before risking real money.",
            "All major brokers are SIPC-insured up to $500,000 -- your money is protected.",
            "You can have multiple brokerage accounts -- many investors use Fidelity for long-term and Schwab for trading.",
        ],
        "related": ["platforms_robinhood", "platforms_fidelity", "platforms_schwab", "platforms_webull", "platforms_ibkr", "platforms_register", "concepts_buy_and_hold"],
    },

    "platforms_robinhood": {
        "title": "Robinhood -- Beginner's Guide",
        "category": "Platforms",
        "summary": (
            "Robinhood democratized investing by eliminating trading commissions in 2013. "
            "It's the most popular app for first-time investors. Here's everything you need "
            "to know to start trading on Robinhood safely."
        ),
        "sections": [
            {
                "heading": "Account types available",
                "content": (
                    "  Individual Taxable: standard account, no contribution limits.\n"
                    "  Roth IRA: tax-free growth, contribute up to $7,000/year (2024).\n"
                    "  Traditional IRA: tax-deductible contributions, taxed on withdrawal.\n"
                    "  Robinhood Gold ($5/month): 5% APY on uninvested cash, bigger instant deposits,\n"
                    "    margin trading, Level 2 Nasdaq data."
                ),
            },
            {
                "heading": "Key features",
                "content": (
                    "  Fractional shares: buy $1 of Apple, Amazon, or any stock -- no need for full share price.\n"
                    "  Options trading: available after approval (answer questions about experience).\n"
                    "  Crypto: Bitcoin, Ethereum, Dogecoin, and 15+ other coins.\n"
                    "  Recurring investments: auto-buy on a schedule (weekly, monthly).\n"
                    "  Cash card: debit card that rounds up purchases into stock."
                ),
            },
            {
                "heading": "Robinhood Gold -- is it worth it?",
                "content": (
                    "At $5/month ($50/year):\n"
                    "  5% APY on uninvested cash (on first $50,000) = $250/year on $5,000 cash.\n"
                    "  Bigger instant deposit limits (up to $50,000 vs $1,000 free).\n"
                    "  Margin borrowing at ~6% -- use with extreme caution.\n"
                    "  Worth it if: you keep significant cash in the account OR need larger instant deposits."
                ),
            },
            {
                "heading": "Robinhood limitations to know",
                "content": (
                    "  No mutual funds: can't buy Vanguard VTSAX -- ETF equivalents exist (VTI).\n"
                    "  Payment for order flow: Robinhood sells your order to market makers,\n"
                    "    which may result in slightly worse prices vs Fidelity.\n"
                    "  Customer service: primarily in-app chat; no phone support on free tier.\n"
                    "  2021 GameStop controversy: restricted buying during squeeze -- controversial."
                ),
            },
        ],
        "quick_tips": [
            "Enable 2-factor authentication immediately -- your account holds real money.",
            "Use recurring investments ($25/week into SPY) to build wealth automatically.",
            "Robinhood's 'most popular' lists are sentiment indicators, not buy recommendations.",
            "Download your tax documents (1099) each February -- you need them for filing.",
        ],
        "related": ["platforms_register", "platforms_overview", "concepts_buy_and_hold"],
    },

    "platforms_register": {
        "title": "How to Open a Brokerage Account",
        "category": "Platforms",
        "summary": (
            "Opening a brokerage account takes about 10-15 minutes online. You'll need a few "
            "documents and some basic personal information. Here's the step-by-step process "
            "for any major US broker (Robinhood, Fidelity, Schwab, etc.)."
        ),
        "sections": [
            {
                "heading": "What you need before you start",
                "content": (
                    "  Social Security Number (SSN) or ITIN: required by law (tax reporting).\n"
                    "  Government-issued ID: driver's license or passport.\n"
                    "  Bank account: routing and account number to fund your account.\n"
                    "  Email address and phone number: for account security.\n"
                    "  Employment info: employer name, job title, annual income (approximate is fine).\n"
                    "  You must be 18+ years old (some platforms have custodial accounts for minors)."
                ),
            },
            {
                "heading": "Step-by-step registration",
                "content": (
                    "  1. Download the app or go to the broker's website.\n"
                    "  2. Click 'Sign Up' -- enter email, create a strong password.\n"
                    "  3. Personal info: full legal name, date of birth, address.\n"
                    "  4. SSN: used for tax reporting, not a credit check.\n"
                    "  5. Employment: income, employer, investment experience questions.\n"
                    "  6. Identity verification: upload ID photo (automated, usually instant).\n"
                    "  7. Agree to terms and conditions (read the important disclosures).\n"
                    "  8. Link bank account: instant verification via Plaid, or manual routing/account numbers.\n"
                    "  9. Fund your account: initial deposit (as low as $1 on Robinhood).\n"
                    " 10. Wait for approval: usually instant to 1 business day."
                ),
            },
            {
                "heading": "Account approval levels (options)",
                "content": (
                    "Standard stock trading is approved immediately for everyone.\n"
                    "Options trading requires approval based on experience answers:\n"
                    "  Level 1: covered calls (lowest risk).\n"
                    "  Level 2: buying calls and puts (most beginners get this).\n"
                    "  Level 3: spreads (intermediate).\n"
                    "  Level 4: naked options (highest risk, rarely approved for new accounts).\n\n"
                    "Tip: answer the experience questions honestly -- options are risky and not for beginners."
                ),
            },
            {
                "heading": "First steps after account opens",
                "content": (
                    "  1. Enable 2-factor authentication (Google Authenticator or SMS).\n"
                    "  2. Set a strong, unique password -- use a password manager.\n"
                    "  3. Fund the account -- transfers take 1-3 days to fully clear.\n"
                    "  4. Explore before buying -- use paper trading if available.\n"
                    "  5. Start small -- your first trade should be an amount you can afford to lose entirely."
                ),
            },
        ],
        "quick_tips": [
            "Use a Roth IRA if you're under 50 and expect income to grow -- tax-free growth is powerful.",
            "Don't link your primary checking account -- use a separate savings account for investing.",
            "SIPC insurance covers up to $500,000 ($250,000 cash) if your broker fails -- you're protected.",
            "Your SSN is safe -- all US brokers are regulated by FINRA and the SEC.",
        ],
        "related": ["platforms_overview", "platforms_robinhood", "concepts_buy_and_hold"],
    },

    "platforms_fidelity": {
        "title": "Fidelity -- Best Overall Broker",
        "category": "Platforms",
        "summary": (
            "Fidelity is widely regarded as the best all-around broker for most investors. "
            "No commissions, no payment for order flow, excellent research, and best-in-class "
            "retirement account support. Sign up at https://www.fidelity.com"
        ),
        "sections": [
            {
                "heading": "Account types",
                "content": (
                    "  Individual brokerage: taxable account, no contribution limits.\n"
                    "  Roth IRA: tax-free growth, $7,000/year limit (2024), $8,000 if age 50+.\n"
                    "  Traditional IRA: tax-deductible contributions, taxed on withdrawal.\n"
                    "  401(k) rollover IRA: move old employer 401(k) into Fidelity.\n"
                    "  HSA: triple tax advantage if you have a high-deductible health plan.\n"
                    "  529 college savings, custodial accounts (UGMA/UTMA) for minors."
                ),
            },
            {
                "heading": "Why Fidelity beats Robinhood for serious investors",
                "content": (
                    "  No PFOF: Fidelity doesn't sell your orders to market makers --\n"
                    "    studies show ~$8 better execution per 100 shares vs Robinhood.\n"
                    "  Research depth: Fidelity's own analysts + Morningstar, Argus, S&P -- all free.\n"
                    "  Fractional shares: buy as little as $1 of any S&P 500 stock.\n"
                    "  $0 commissions on stocks and ETFs; $0.65/contract on options.\n"
                    "  Zero-expense index funds: FZROX (0.00% fee) beats even Vanguard's VOO.\n"
                    "  24/7 live customer service via phone and chat."
                ),
            },
            {
                "heading": "Active Trader Pro (free desktop app)",
                "content": (
                    "Free desktop platform for active traders:\n"
                    "  Advanced charting with 100+ technical indicators.\n"
                    "  Real-time streaming quotes and news alerts.\n"
                    "  Multi-leg options order entry and analysis.\n"
                    "  Download: https://www.fidelity.com/trading/advanced-trading-tools/active-trader-pro\n\n"
                    "The mobile app is great for monitoring; Active Trader Pro is for serious trading."
                ),
            },
            {
                "heading": "Fidelity's zero-expense index funds",
                "content": (
                    "4 funds with 0.00% expense ratio -- the cheapest funds in existence:\n"
                    "  FZROX: Total US Market (equivalent to VTI, but free).\n"
                    "  FZILX: Total International Market.\n"
                    "  FZIPX: Extended US Market (small/mid-cap).\n"
                    "  FZILX + FZROX together cover ~99% of global investable assets at zero cost.\n\n"
                    "Note: these are Fidelity-exclusive -- you can't transfer them to another broker."
                ),
            },
        ],
        "quick_tips": [
            "Open a Roth IRA at Fidelity -- even $50/month now grows tax-free for decades.",
            "FZROX in your IRA is the ultimate set-it-and-forget-it: 0% fee, total US market exposure.",
            "Fidelity's research ratings are free for all account holders -- always check before buying.",
            "Set up automatic investments on the 1st and 15th to dollar-cost average effortlessly.",
        ],
        "related": ["platforms_overview", "platforms_register", "concepts_buy_and_hold", "sector_etfs"],
    },

    "platforms_schwab": {
        "title": "Charles Schwab & thinkorswim -- Best for Active Traders",
        "category": "Platforms",
        "summary": (
            "Charles Schwab acquired TD Ameritrade in 2020 and inherited its legendary thinkorswim "
            "platform -- the most powerful free trading platform available to retail traders. "
            "Sign up: https://www.schwab.com | thinkorswim: https://www.schwab.com/trading/thinkorswim"
        ),
        "sections": [
            {
                "heading": "Schwab web vs thinkorswim -- which to use",
                "content": (
                    "Schwab runs two separate interfaces:\n\n"
                    "  Schwab.com (web): clean, simple -- for ETF investing and IRA management.\n"
                    "  thinkorswim (TOS): professional-grade desktop/mobile -- for active trading.\n\n"
                    "Use Schwab.com for: buying ETFs, IRA contributions, account overview.\n"
                    "Use thinkorswim for: options, technical analysis, charting, active trading."
                ),
            },
            {
                "heading": "thinkorswim features",
                "content": (
                    "  Paper trading: trade $100,000 of fake money with real market data.\n"
                    "    Best paper trading platform in the industry -- use for 3-6 months first.\n"
                    "  thinkScript: write custom indicators and automated stock scanners.\n"
                    "  Options analysis: P&L curve visualizer, probability cones, risk graph.\n"
                    "  Advanced charting: all major indicators + fully custom ones, drawing tools.\n"
                    "  Market scanner: screen thousands of stocks in real time by any criteria.\n"
                    "  'On Demand' replay: replay any historical trading day to practice with real past data."
                ),
            },
            {
                "heading": "Costs and account types",
                "content": (
                    "  $0 commissions on stocks and ETFs.\n"
                    "  Options: $0.65/contract (free to open spreads on Schwab).\n"
                    "  No account minimums to open.\n"
                    "  Individual brokerage, Roth IRA, Traditional IRA, SEP IRA, Rollover IRA.\n"
                    "  Schwab Intelligent Portfolios: free robo-advisor (auto-rebalancing) with $5,000 minimum.\n"
                    "  Schwab Bank: attached checking with unlimited worldwide ATM fee refunds."
                ),
            },
            {
                "heading": "thinkorswim mobile",
                "content": (
                    "The thinkorswim mobile app carries most desktop features:\n"
                    "  Full charting with all indicators.\n"
                    "  Options trading with full Greeks display (Delta, Theta, Gamma, Vega).\n"
                    "  Paper trading mode available on mobile.\n"
                    "  Available on iOS and Android.\n\n"
                    "Schwab also has a separate simpler 'Schwab Mobile' app for basic account management."
                ),
            },
        ],
        "quick_tips": [
            "Start in thinkorswim paper trading -- it's the best free simulator available anywhere.",
            "thinkScript lets you build scans like 'stocks crossing above 50-day MA today' for free.",
            "Schwab's phone support is 24/7 with US-based reps -- exceptional for a large broker.",
            "Schwab Intelligent Portfolios auto-rebalances your ETF allocation for free at $5,000+.",
        ],
        "related": ["platforms_overview", "platforms_register", "concepts_options_greeks", "concepts_day_trading"],
    },

    "platforms_webull": {
        "title": "Webull -- Best Free Technical Analysis App",
        "category": "Platforms",
        "summary": (
            "Webull offers free advanced charting and Level 2 order book data that cost money "
            "on most other platforms. Ideal for technically-minded traders who want more than "
            "Robinhood but don't need thinkorswim's full complexity. "
            "Sign up: https://www.webull.com"
        ),
        "sections": [
            {
                "heading": "What makes Webull stand out",
                "content": (
                    "  Free Level 2 quotes: see the full bid/ask order book -- usually costs $30+/month.\n"
                    "  Advanced charting: 50+ technical indicators at no cost.\n"
                    "  Extended hours: pre-market 4am-9:30am ET and after-hours 4pm-8pm ET.\n"
                    "  Paper trading: unlimited practice account with real market data.\n"
                    "  Desktop app: full-featured platform similar to thinkorswim but simpler.\n"
                    "  Options trading: available after standard approval process."
                ),
            },
            {
                "heading": "Webull vs Robinhood -- when to choose Webull",
                "content": (
                    "Choose Webull if you:\n"
                    "  - Want free Level 2 order book depth data.\n"
                    "  - Use more than basic moving averages (RSI, MACD, Bollinger Bands, etc.).\n"
                    "  - Trade extended hours frequently.\n"
                    "  - Want paper trading to practice before real money.\n\n"
                    "Stick with Robinhood if you:\n"
                    "  - Want a simpler, more polished mobile experience.\n"
                    "  - Prefer a better Roth IRA / retirement account interface.\n"
                    "  - Just buy and hold ETFs without needing advanced charts."
                ),
            },
            {
                "heading": "Account types",
                "content": (
                    "  Individual brokerage: taxable account.\n"
                    "  Roth IRA and Traditional IRA: fully supported.\n"
                    "  Cash account: no margin, no PDT rule -- ideal for smaller accounts.\n"
                    "  Margin account: borrow against holdings (use with caution).\n\n"
                    "Webull is US-registered and regulated by FINRA and the SEC.\n"
                    "Accounts are SIPC-insured up to $500,000."
                ),
            },
            {
                "heading": "Ownership and privacy note",
                "content": (
                    "Webull is owned by Fumi Technology, a Chinese company.\n"
                    "  US user data is stored on US servers and subject to US law.\n"
                    "  Some traders avoid Chinese-owned financial apps on principle.\n"
                    "  Alternative: Schwab thinkorswim offers similar tools with no ownership concerns."
                ),
            },
        ],
        "quick_tips": [
            "Enable free Level 2 quotes in Webull settings -- it's the single best free feature.",
            "Use Webull's paper trading for 30 days before risking real money on technical setups.",
            "The desktop app has significantly more features than the mobile app -- use it for analysis.",
            "Webull's 'Hot List' shows trending stocks by search volume -- useful for finding momentum plays.",
        ],
        "related": ["platforms_overview", "platforms_register", "concepts_day_trading", "concepts_options_greeks"],
    },

    "platforms_ibkr": {
        "title": "Interactive Brokers (IBKR) -- Best for Professionals",
        "category": "Platforms",
        "summary": (
            "Interactive Brokers is the preferred broker for professional traders and institutions. "
            "Access to 150+ global markets, the lowest margin rates in the industry, and the most "
            "sophisticated tools available. IBKR Lite is commission-free for casual investors. "
            "Sign up: https://www.interactivebrokers.com | Lite tier: https://www.interactivebrokers.com/en/trading/ibkr-lite.php"
        ),
        "sections": [
            {
                "heading": "IBKR Lite vs IBKR Pro -- which to choose",
                "content": (
                    "IBKR Lite (free tier):\n"
                    "  $0 commissions on US stocks and ETFs.\n"
                    "  Uses payment for order flow (like Robinhood).\n"
                    "  Good for casual investors who want IBKR's research without complexity.\n\n"
                    "IBKR Pro (professional tier):\n"
                    "  $0 or $0.005/share -- automatically uses whichever is cheaper for your order.\n"
                    "  No PFOF: 'Smart Routing' finds the best price across all exchanges.\n"
                    "  Access to all global markets and professional-grade data feeds.\n"
                    "  Best for active traders placing large orders (1,000+ shares)."
                ),
            },
            {
                "heading": "Global market access -- IBKR's biggest advantage",
                "content": (
                    "IBKR provides access to markets most US brokers don't offer:\n"
                    "  US: stocks, options, futures, forex, bonds, ETFs, mutual funds.\n"
                    "  Europe: London, Frankfurt, Paris, Amsterdam, Zurich, Milan.\n"
                    "  Asia: Tokyo, Hong Kong, Singapore, Sydney.\n"
                    "  Forex: 24 currencies at institutional spreads.\n"
                    "  Crypto: Bitcoin and Ethereum through regulated custodians.\n"
                    "  Precious metals: gold and silver spot trading.\n\n"
                    "If you need to buy international stocks directly (not US-listed ADRs), IBKR is essentially the only retail option."
                ),
            },
            {
                "heading": "Margin rates -- IBKR's second biggest advantage",
                "content": (
                    "IBKR charges the lowest margin rates in the US retail industry:\n"
                    "  IBKR Pro: ~5.8% annual (2024).\n"
                    "  Robinhood Gold: ~6.5%.\n"
                    "  Fidelity: ~9.25-12% depending on balance.\n"
                    "  Schwab: ~9.5-12%.\n\n"
                    "On $50,000 borrowed: IBKR saves $1,500-$3,000/year vs major competitors.\n"
                    "Only matters if you use margin -- beginners should avoid margin entirely."
                ),
            },
            {
                "heading": "Trader Workstation (TWS) -- IBKR's platform",
                "content": (
                    "TWS is IBKR's flagship desktop platform:\n"
                    "  Highly customizable with a steep learning curve -- extremely powerful.\n"
                    "  Portfolio analytics, risk dashboard, volatility surface lab.\n"
                    "  IBKR GlobalAnalyst: compare stocks across countries on normalized metrics.\n"
                    "  Paper trading: full demo account with real market data.\n\n"
                    "For beginners: use IBKR's simpler 'Client Portal' web interface instead of TWS.\n"
                    "IBKR Mobile app is solid for monitoring and placing basic trades on the go."
                ),
            },
        ],
        "quick_tips": [
            "Start with IBKR Lite -- $0 commissions with access to IBKR's world-class research.",
            "IBKR's margin rates make it the only rational choice for traders who regularly use leverage.",
            "Use IBKR's paper trading in TWS to practice options strategies with real market data.",
            "No minimum deposit and no monthly fees on Lite -- no reason not to open an account alongside your main broker.",
        ],
        "related": ["platforms_overview", "platforms_register", "concepts_options_greeks", "concepts_day_trading"],
    },

    # ── NEW CONCEPTS ──────────────────────────────────────────────────────────
    "concepts_options_greeks": {
        "title": "Options Greeks -- Delta, Gamma, Theta, Vega, Rho",
        "category": "Concepts",
        "summary": (
            "Options Greeks measure how an option's price responds to different factors: "
            "stock price movement (Delta, Gamma), time passing (Theta), volatility (Vega), "
            "and interest rates (Rho). Understanding Greeks is essential before trading options "
            "and explains market behavior around earnings, squeezes, and Fed rate decisions. "
            "Learn more at: https://www.investopedia.com/trading/using-the-greeks-to-understand-options/"
        ),
        "sections": [
            {
                "heading": "What is an option?",
                "content": (
                    "An option is a contract giving the right (not obligation) to buy or sell "
                    "100 shares at a set price (strike) before a set date (expiration).\n\n"
                    "  Call option: right to BUY 100 shares. Profits if stock goes UP.\n"
                    "  Put option: right to SELL 100 shares. Profits if stock goes DOWN.\n\n"
                    "Options cost a 'premium' -- this is what Greeks help you understand and predict.\n"
                    "Each option contract controls 100 shares, so multiply all Greek values by 100."
                ),
            },
            {
                "heading": "Delta (Δ) -- price sensitivity",
                "content": (
                    "Delta measures how much the option price moves per $1 move in the stock.\n\n"
                    "  Call delta: 0 to 1.0.\n"
                    "    Delta 0.50: option gains $0.50 when stock rises $1 ($50 per contract).\n"
                    "    Delta 0.80: option gains $0.80 (deep in-the-money, moves like the stock).\n"
                    "    Delta 0.10: option barely moves (far out-of-the-money lottery ticket).\n\n"
                    "  Put delta: -1.0 to 0.\n"
                    "    Delta -0.40: put gains $0.40 per $1 drop in the stock.\n\n"
                    "Delta also approximates the probability the option expires in-the-money:\n"
                    "  Delta 0.70 call = ~70% chance the call is profitable at expiration.\n"
                    "  Delta 0.30 call = ~30% chance -- cheap but unlikely to pay off.\n\n"
                    "Rule of thumb: buy delta 0.40-0.70 for reasonable leverage; avoid < 0.20."
                ),
            },
            {
                "heading": "Theta (Θ) -- time decay (the enemy of buyers)",
                "content": (
                    "Theta measures how much value an option loses each day due to time passing alone.\n\n"
                    "  Theta -0.05: option loses $5/day per contract (100 x $0.05).\n"
                    "  Theta accelerates exponentially in the last 30 days before expiration.\n"
                    "  At expiration, an out-of-the-money option is worth exactly $0.\n\n"
                    "Theta works AGAINST option buyers and FOR option sellers:\n"
                    "  Buyers: the stock must move fast enough and far enough to overcome daily decay.\n"
                    "  Sellers (writers): collect premium and profit from time passing.\n\n"
                    "This is why experienced traders often SELL options (covered calls, cash-secured puts)\n"
                    "rather than buy them -- time is on the seller's side."
                ),
            },
            {
                "heading": "Gamma (Γ) -- rate of change of delta",
                "content": (
                    "Gamma measures how fast delta itself changes as the stock price moves.\n\n"
                    "  High gamma: delta changes rapidly -- options become very price-sensitive.\n"
                    "  Gamma is highest for at-the-money options near expiration.\n\n"
                    "Gamma squeeze (real market phenomenon):\n"
                    "  As a stock rises, call sellers (usually market makers) must buy more shares\n"
                    "    to hedge their short call exposure (called 'delta hedging').\n"
                    "  Those forced stock purchases push the price higher.\n"
                    "  Higher price creates more in-the-money calls, requiring more hedging.\n"
                    "  A self-reinforcing loop -- GameStop (GME) in January 2021 was a textbook gamma squeeze.\n\n"
                    "For options buyers: gamma helps you when you're right -- gains accelerate.\n"
                    "For options sellers: gamma hurts you when wrong -- losses accelerate."
                ),
            },
            {
                "heading": "Vega (ν) -- volatility sensitivity",
                "content": (
                    "Vega measures how much the option price changes per 1% change in implied volatility (IV).\n\n"
                    "  Vega 0.10: a 1% rise in IV adds $0.10 ($10 per contract) to the option price.\n"
                    "  Options get MORE expensive as IV rises -- buyers pay more, sellers collect more.\n\n"
                    "IV crush (the most expensive lesson for option buyers):\n"
                    "  Before earnings: IV spikes as traders speculate on the outcome.\n"
                    "  After earnings: IV collapses immediately regardless of the move.\n"
                    "  A stock can beat earnings and rise 5%, but IV drops so sharply that\n"
                    "    call buyers STILL lose money because vega crushed their option value.\n\n"
                    "How to check IV: Look for 'IV Rank' or 'IV Percentile' on your broker.\n"
                    "  IV Rank > 50: IV is high relative to its history -- consider selling options.\n"
                    "  IV Rank < 30: IV is low -- buying options is relatively cheaper."
                ),
            },
            {
                "heading": "Rho (ρ) -- interest rate sensitivity",
                "content": (
                    "Rho measures how much the option price changes per 1% change in interest rates.\n\n"
                    "  Call options: positive Rho (calls gain value when rates rise).\n"
                    "  Put options: negative Rho (puts lose value when rates rise).\n\n"
                    "Rho is the least important Greek for short-term options (expires < 3 months)\n"
                    "because small rate changes don't move the price much.\n\n"
                    "Rho matters for:\n"
                    "  LEAPS (options expiring 1-2 years out): Rho effect compounds over time.\n"
                    "  Fed rate decision days: a surprise 0.50% rate hike can noticeably move\n"
                    "    long-dated options prices even if the stock itself barely moves.\n\n"
                    "Most retail traders can ignore Rho unless trading LEAPS."
                ),
            },
            {
                "heading": "Reading Greeks together -- practical example",
                "content": (
                    "Scenario: You buy 1 call on AAPL ($180 stock, $185 strike, 30 days out).\n"
                    "  Premium: $2.50 ($250 per contract).\n"
                    "  Delta: 0.35 -- gains $35/day per $1 rise in AAPL.\n"
                    "  Theta: -0.08 -- loses $8/day from time decay alone.\n"
                    "  Gamma: 0.04 -- delta rises by 0.04 for each $1 AAPL rises.\n"
                    "  Vega: 0.12 -- gains $12 per 1% IV increase.\n\n"
                    "Day 1: AAPL rises $2. Gain = 2 x $35 = $70. Theta cost = -$8. Net: +$62.\n"
                    "Day 5 (AAPL flat): Theta cost alone = 5 x -$8 = -$40. Option now worth $210.\n"
                    "Earnings tomorrow: IV spikes 20%. Vega gain = 20 x $12 = +$240 -- premium surges.\n"
                    "After earnings (stock beats but IV crushes): IV drops 25%, vega = -$300.\n"
                    "  Even if AAPL rose $3, the IV crush more than wipes out the delta gain.\n\n"
                    "Takeaway: Delta gets you in; Theta and Vega determine if you actually profit."
                ),
            },
        ],
        "quick_tips": [
            "Never buy options right before earnings without understanding IV crush -- it destroys premiums.",
            "Delta 0.30 calls are lottery tickets; delta 0.70 calls behave much closer to owning the stock.",
            "Theta is why selling covered calls on stocks you own generates steady income.",
            "Check IV Rank before buying options -- buying when IV is already high means you overpay.",
            "Start with paper trading options for 60 days -- real options can go to zero in a week.",
        ],
        "related": ["patterns_earnings_drift", "volume", "risk_position_sizing", "platforms_schwab", "platforms_ibkr"],
    },

    "concepts_day_trading": {
        "title": "Day Trading -- What You Must Know First",
        "category": "Concepts",
        "summary": (
            "Day trading means buying and selling the same stock within the same trading day. "
            "Studies show 70-90% of day traders lose money over time. "
            "Before you try it, understand the rules, the odds, and the alternatives."
        ),
        "sections": [
            {
                "heading": "The Pattern Day Trader (PDT) rule",
                "content": (
                    "US law classifies you as a Pattern Day Trader if you make 4+ day trades\n"
                    "in a 5-business-day period in a margin account.\n\n"
                    "  Once flagged: you MUST maintain $25,000 in your account at all times.\n"
                    "  Below $25,000: account is frozen for 90 days or until you deposit more.\n\n"
                    "Workarounds if you have < $25,000:\n"
                    "  - Use a cash account (no margin) -- no PDT rule applies, but trades settle in T+1.\n"
                    "  - Limit yourself to 3 day trades per 5-day window.\n"
                    "  - Use an offshore broker (higher risk, less regulation).\n"
                    "  - Swing trade instead (hold overnight)."
                ),
            },
            {
                "heading": "The real odds of day trading",
                "content": (
                    "Studies from Taiwan, Brazil, and the EU consistently find:\n"
                    "  - Only 1-3% of day traders are consistently profitable year over year.\n"
                    "  - The average day trader underperforms just holding SPY by 6-8%/year.\n"
                    "  - Most profits go to high-frequency trading firms with microsecond advantages.\n\n"
                    "You're competing against:\n"
                    "  - Algorithms that react in microseconds.\n"
                    "  - Market makers who see order flow before you.\n"
                    "  - Professional traders with 10,000+ hours of experience."
                ),
            },
            {
                "heading": "Tax implications of day trading",
                "content": (
                    "  Short-term capital gains (held < 1 year): taxed as ORDINARY INCOME.\n"
                    "    At a 22% tax bracket, every $1,000 profit costs $220 in taxes.\n"
                    "  Long-term gains (held > 1 year): 0%, 15%, or 20% -- much lower.\n"
                    "  Wash sale rule: you can't claim a loss if you rebuy the same stock within 30 days.\n"
                    "  Frequent traders may need to pay quarterly estimated taxes."
                ),
            },
            {
                "heading": "When day trading makes sense",
                "content": (
                    "Day trading CAN work with:\n"
                    "  - Strict risk management ($100 max loss per trade).\n"
                    "  - A defined edge (specific setup, not gut feeling).\n"
                    "  - A simulator first -- 6+ months of paper trading before real money.\n"
                    "  - Acceptance that most months will be negative while learning.\n\n"
                    "Better alternatives for most people:\n"
                    "  Swing trading (2-10 day holds), ETF investing, or dividend stocks."
                ),
            },
        ],
        "quick_tips": [
            "Paper trade for 6 months first -- if you can't profit on paper, don't use real money.",
            "The PDT rule doesn't apply to accounts over $25,000 or cash accounts.",
            "Your biggest day trading cost is taxes, not commissions -- factor them into every trade.",
            "Most successful day traders focus on 1-2 setups only, not every opportunity.",
        ],
        "related": ["concepts_buy_and_hold", "risk_position_sizing", "risk_stop_loss", "platforms_overview"],
    },

    "concepts_buy_and_hold": {
        "title": "Buy and Hold -- The Simple Path to Wealth",
        "category": "Concepts",
        "summary": (
            "Buy and hold is the strategy of purchasing stocks or ETFs and holding them for years "
            "regardless of short-term market swings. Warren Buffett calls it the only strategy "
            "most people need. Historically, it outperforms the vast majority of active traders."
        ),
        "sections": [
            {
                "heading": "Why it works",
                "content": (
                    "The US stock market has returned ~10% per year on average since 1926.\n"
                    "  $10,000 invested in SPY in 2004 = ~$65,000 today (including dividends).\n"
                    "  $10,000 invested in Apple in 2004 = ~$2,000,000+ today.\n\n"
                    "The math of compounding:\n"
                    "  $500/month invested at 10%/year = $1,000,000 in 30 years.\n"
                    "  The same $500/month as active trading (8% avg return) = $600,000.\n"
                    "  Boredom and consistency beat excitement and trading."
                ),
            },
            {
                "heading": "Dollar-Cost Averaging (DCA)",
                "content": (
                    "DCA means investing a fixed amount on a regular schedule (weekly/monthly)\n"
                    "regardless of whether the market is up or down.\n\n"
                    "  Market at all-time high? Buy anyway -- you can't time the top.\n"
                    "  Market crashed 20%? Buy more -- you're getting a discount.\n\n"
                    "DCA removes the emotional decision of 'when to buy' and naturally\n"
                    "buys more shares when prices are low, fewer when prices are high."
                ),
            },
            {
                "heading": "What to buy and hold",
                "content": (
                    "  Best choice for most people:\n"
                    "    SPY or VOO (S&P 500 ETF) -- instant exposure to 500 biggest US companies.\n"
                    "    QQQ (Nasdaq 100) -- tech-heavy, higher growth potential, more volatile.\n"
                    "    VTI (Total US market) -- even broader than S&P 500.\n\n"
                    "  For individual stocks:\n"
                    "    Choose companies with strong competitive moats (AAPL, MSFT, GOOGL, AMZN).\n"
                    "    Only buy companies you understand and believe in long-term.\n"
                    "    Reinvest dividends for compounding."
                ),
            },
            {
                "heading": "The tax advantage of holding",
                "content": (
                    "  Hold > 1 year: long-term capital gains tax rate (0%, 15%, or 20%).\n"
                    "  Hold < 1 year: short-term rate = same as your income tax (22-37%).\n"
                    "  In a Roth IRA: gains are COMPLETELY TAX-FREE forever.\n\n"
                    "Example: $10,000 profit.\n"
                    "  Day trader at 24% bracket: pays $2,400.\n"
                    "  Buy-and-hold investor (15% LTCG): pays $1,500.\n"
                    "  Roth IRA holder: pays $0."
                ),
            },
        ],
        "quick_tips": [
            "Set up automatic monthly investments -- remove the decision entirely.",
            "Don't check your portfolio every day -- quarterly is enough for long-term holds.",
            "'Time in the market beats timing the market' -- missing the 10 best days cuts returns in half.",
            "Reinvest dividends automatically -- compound growth is most powerful with reinvestment.",
        ],
        "related": ["sector_etfs", "concepts_day_trading", "platforms_register", "risk_diversification"],
    },

    "risk_avoid_mistakes": {
        "title": "Avoiding Unnecessary Risk -- The Beginner's Survival Guide",
        "category": "Risk Management",
        "summary": (
            "Most beginner losses come from a small number of repeated mistakes. "
            "Understanding these traps before you start can save you thousands of dollars. "
            "The goal in your first year is not to get rich -- it's to survive and learn."
        ),
        "sections": [
            {
                "heading": "The 5 biggest beginner mistakes",
                "content": (
                    "  1. FOMO buying: chasing a stock that's already up 50% -- you missed the move.\n"
                    "     Fix: set watchlists and wait for pullbacks to moving averages.\n\n"
                    "  2. No stop-loss: hoping a losing trade comes back -- it often doesn't.\n"
                    "     Fix: set a stop-loss before you enter every trade, no exceptions.\n\n"
                    "  3. Overconcentration: putting 50%+ of your account in one stock.\n"
                    "     Fix: no single stock > 15% of portfolio.\n\n"
                    "  4. Using margin before you're ready: borrowing amplifies both gains AND losses.\n"
                    "     Fix: trade with cash only until you're consistently profitable.\n\n"
                    "  5. Trading earnings without a plan: binary events cause 20%+ gaps overnight.\n"
                    "     Fix: either reduce position before earnings or understand the risk explicitly."
                ),
            },
            {
                "heading": "Margin trading -- the biggest risk amplifier",
                "content": (
                    "Margin lets you borrow money from your broker to buy more stock than you own.\n\n"
                    "  Example: $5,000 account + $5,000 margin = $10,000 buying power.\n"
                    "  A 25% drop wipes out your entire $5,000 while you still owe the $5,000 loan.\n"
                    "  Margin calls: if account drops below maintenance level, broker FORCES you to sell.\n"
                    "  Margin interest: you pay 6-12% annually on borrowed money.\n\n"
                    "Rule: Do NOT use margin until you've been profitable for at least 1 year without it."
                ),
            },
            {
                "heading": "Emotional trading traps",
                "content": (
                    "  Revenge trading: doubling down after a loss to 'make it back quickly.'\n"
                    "    -> This is gambling, not trading. Walk away after a big loss.\n\n"
                    "  Anchoring: refusing to sell because 'it was at $50 and I need it to come back.'\n"
                    "    -> The stock doesn't know what you paid. Sell if the thesis is broken.\n\n"
                    "  Overtrading: making 20 trades a day when 2 good ones would be better.\n"
                    "    -> Each trade has transaction costs and tax implications; less is often more."
                ),
            },
            {
                "heading": "Only invest what you can afford to lose",
                "content": (
                    "This is not a cliche -- it's the foundation of rational decision-making.\n\n"
                    "  Emergency fund first: keep 3-6 months of expenses in CASH before investing.\n"
                    "  High-interest debt first: paying off 20% credit card debt beats any stock return.\n"
                    "  Never invest rent money, bill money, or borrowed money in volatile stocks.\n"
                    "  Speculative positions (penny stocks, crypto): max 5-10% of investable assets.\n\n"
                    "When you invest money you can't afford to lose, fear causes bad decisions at the worst times."
                ),
            },
            {
                "heading": "Red flags -- scams and pump-and-dumps",
                "content": (
                    "  Guaranteed returns: no investment is guaranteed. If someone promises it, run.\n"
                    "  Social media 'tips': stock recommendations on Reddit/Twitter/TikTok often\n"
                    "    come from people who already own it and want you to drive the price up.\n"
                    "  Penny stock promotions: unsolicited emails/texts about a 'hot stock'\n"
                    "    are almost always pump-and-dump schemes.\n"
                    "  'Act now' pressure: legitimate investments don't require immediate decisions.\n"
                    "  Unregistered platforms: only use FINRA/SEC-registered brokers."
                ),
            },
        ],
        "quick_tips": [
            "If a stock is already trending on social media, you're probably too late.",
            "The urge to 'do something' is your biggest enemy -- sitting in cash IS a position.",
            "Keep a trading journal -- write why you entered every trade and review losses honestly.",
            "Never invest in a company you can't explain in 2 sentences.",
        ],
        "related": ["risk_position_sizing", "risk_stop_loss", "concepts_day_trading", "risk_diversification"],
    },

    "sector_healthcare": {
        "title": "Healthcare & Biotech Sector",
        "category": "Sectors",
        "summary": (
            "Healthcare is a defensive sector -- people need medicine regardless of the economy. "
            "Biotech is a high-risk sub-sector where FDA trial results can move stocks 50%+ in a day. "
            "The GLP-1 obesity drug wave (Ozempic, Zepbound) is the sector's biggest current theme."
        ),
        "sections": [
            {
                "heading": "Healthcare sub-sectors",
                "content": (
                    "  Large pharma (JNJ, PFE, MRK): diversified drug portfolios, stable dividends.\n"
                    "  Biotech (MRNA, REGN, AMGN): fewer products, massive upside/downside on trials.\n"
                    "  Health insurers (UNH, CVS): benefit from aging population and ACA.\n"
                    "  Medical devices (MDT, SYK, ISRG): recurring procedure revenue.\n"
                    "  Specialty pharma (LLY, ABBV): focused on high-margin blockbuster drugs."
                ),
            },
            {
                "heading": "FDA catalyst events",
                "content": (
                    "The FDA approval calendar is more important than earnings for biotech stocks.\n"
                    "  PDUFA date: FDA deadline to approve/reject a drug application.\n"
                    "  Phase 3 trial results: the largest catalyst for clinical-stage biotechs.\n"
                    "  Stock reaction: approval = +30-100%; rejection = -50-80%.\n"
                    "Never hold through an FDA decision without understanding the risk."
                ),
            },
        ],
        "quick_tips": [
            "LLY (Eli Lilly) is the most important healthcare stock right now -- GLP-1 obesity drugs.",
            "XLV ETF gives healthcare exposure without FDA binary event risk.",
            "Healthcare stocks often hold up during market corrections -- good for balance.",
            "Drug patent expiration ('patent cliff') is a major risk for established pharma companies.",
        ],
        "related": ["sector_etfs", "patterns_gap", "risk_position_sizing"],
    },
}


def get_topic(key: str) -> dict | None:
    return KNOWLEDGE_BASE.get(key.lower().replace(" ", "_").replace("-", "_"))


def list_by_category() -> dict[str, list[tuple[str, str]]]:
    result: dict[str, list] = {c: [] for c in CATEGORIES}
    for key, entry in KNOWLEDGE_BASE.items():
        cat = entry.get("category", "Concepts")
        if cat in result:
            result[cat].append((key, entry["title"]))
    return result


def search(query: str) -> list[tuple[str, str]]:
    q = query.lower()
    matches = []
    for key, entry in KNOWLEDGE_BASE.items():
        text = (
            entry["title"] + " " + entry["summary"] + " " +
            " ".join(s["content"] for s in entry["sections"])
        ).lower()
        if q in text:
            matches.append((key, entry["title"]))
    return matches

