"""
Subscriber signup web server (HTTPS).
Run via: python main.py serve
"""
from flask import Flask, request, redirect, Response
from . import database as db
from . import config as cfg_mod
from . import knowledge as kb_mod
from . import sectors as sec_mod
from . import social as social_mod

# ── CSS color maps ────────────────────────────────────────────────────────────

_SECTOR_CSS = {
    "AI & Machine Learning": "#c026d3",
    "Technology":            "#0891b2",
    "Semiconductors":        "#ca8a04",
    "Healthcare & Biotech":  "#16a34a",
    "Quantum Computing":     "#7c3aed",
    "ETFs":                  "#475569",
    "Financials":            "#b45309",
    "Energy & Clean Energy": "#ea580c",
    "Consumer":              "#0284c7",
    "Real Estate":           "#0ea5e9",
    "Industrials":           "#f97316",
    "Cybersecurity":          "#e11d48",
    "Fintech":                "#0d9488",
    "Commodities & Bonds":    "#a16207",
    "Penny Stocks":           "#dc2626",
    "Cryptocurrency":         "#d97706",
    "Asian Markets":          "#ef4444",
    "European Markets":       "#3b82f6",
    "Nigerian Exchange (NGX)":"#16a34a",
    "General":                "#64748b",
}

_CAT_COLORS = {
    "Indicators":      "#0ea5e9",
    "Patterns":        "#f59e0b",
    "Sectors":         "#a855f7",
    "Concepts":        "#64748b",
    "Risk Management": "#ef4444",
}

_CSS = """
:root{
  --hero-bg:linear-gradient(135deg,#020617 0%,#0f172a 35%,#1e1b4b 65%,#2e1065 100%);
  --primary:#6366f1;--primary-dark:#4f46e5;--primary-light:#818cf8;
  --success:#10b981;--danger:#ef4444;--warn:#f59e0b;
  --bg:#f0f4ff;--card:#fff;--border:#e2e8f0;
  --text:#0f172a;--muted:#64748b;
  --radius:14px;--shadow:0 4px 24px rgba(0,0,0,.09);
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
     background:var(--bg);color:var(--text);line-height:1.6}
a{color:var(--primary);text-decoration:none}
a:hover{text-decoration:underline}

/* ── NAV ── */
.nav{position:sticky;top:0;z-index:100;display:flex;align-items:center;
     justify-content:space-between;padding:14px 32px;
     background:rgba(2,6,23,.95);backdrop-filter:blur(12px);
     border-bottom:1px solid rgba(255,255,255,.08)}
.nav-logo{color:#fff;font-weight:700;font-size:18px;display:flex;align-items:center;gap:8px}
.nav-logo span{font-size:22px}
.nav-links{display:flex;align-items:center;gap:20px}
.nav-links a{color:rgba(255,255,255,.75);font-size:14px;font-weight:500}
.nav-links a:hover{color:#fff;text-decoration:none}
.nav-cta{background:var(--primary);color:#fff !important;padding:8px 18px;
         border-radius:8px;font-size:13px !important}
.nav-cta:hover{background:var(--primary-dark) !important}

/* ── HERO ── */
.hero{background:var(--hero-bg);position:relative;padding:80px 32px 0;overflow:hidden;
      min-height:480px}
.hero::before{content:'';position:absolute;inset:0;pointer-events:none;
  background-image:linear-gradient(rgba(255,255,255,.025) 1px,transparent 1px),
                   linear-gradient(90deg,rgba(255,255,255,.025) 1px,transparent 1px);
  background-size:60px 60px}
.hero-inner{max-width:740px;margin:0 auto;text-align:center;position:relative;z-index:1}
.hero-badge{display:inline-flex;align-items:center;gap:8px;
            background:rgba(99,102,241,.2);border:1px solid rgba(99,102,241,.4);
            color:#a5b4fc;padding:6px 16px;border-radius:50px;
            font-size:13px;font-weight:600;margin-bottom:28px}
.hero h1{font-size:clamp(32px,5vw,54px);font-weight:800;color:#fff;line-height:1.15;
         margin-bottom:18px;letter-spacing:-.02em}
.hero h1 .accent{background:linear-gradient(90deg,#818cf8,#c084fc);
                  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                  background-clip:text}
.hero-sub{font-size:17px;color:rgba(255,255,255,.65);max-width:560px;
          margin:0 auto 32px;line-height:1.7}
.hero-cta{display:inline-block;background:linear-gradient(135deg,#6366f1,#8b5cf6);
          color:#fff;padding:16px 36px;border-radius:12px;font-size:16px;
          font-weight:700;box-shadow:0 8px 24px rgba(99,102,241,.45);
          transition:transform .2s,box-shadow .2s;margin-bottom:48px}
.hero-cta:hover{transform:translateY(-3px);box-shadow:0 12px 32px rgba(99,102,241,.55);
                text-decoration:none;color:#fff}

/* ── TICKER ── */
.ticker-wrap{overflow:hidden;background:rgba(255,255,255,.06);
             border-top:1px solid rgba(255,255,255,.1);padding:12px 0}
.ticker-track{display:flex;white-space:nowrap;
              animation:ticker 60s linear infinite}
.ticker-track:hover{animation-play-state:paused}
@keyframes ticker{0%{transform:translateX(0)}100%{transform:translateX(-50%)}}
.ticker-item{display:inline-flex;align-items:center;gap:8px;
             padding:4px 24px;font-size:13px;font-weight:600;color:#fff}
.ticker-sym{color:rgba(255,255,255,.9)}
.ticker-price{color:rgba(255,255,255,.7)}
.up{color:#4ade80}.down{color:#f87171}.flat{color:#94a3b8}
.ticker-sep{color:rgba(255,255,255,.2);margin:0 4px}

/* ── STATS BAR ── */
.stats{display:flex;justify-content:center;gap:0;background:#fff;
       border-bottom:1px solid var(--border)}
.stat{flex:1;max-width:160px;padding:20px 16px;text-align:center;
      border-right:1px solid var(--border);transition:background .15s}
.stat:last-child{border-right:none}
a.stat{text-decoration:none;cursor:pointer}
a.stat:hover{background:#f8fafc}
a.stat:hover .stat-num{opacity:.85}
.stat-num{font-size:26px;font-weight:800;color:var(--primary);line-height:1}
.stat-label{font-size:12px;color:var(--muted);margin-top:4px;font-weight:500}

/* ── MAIN CONTENT ── */
.main{max-width:1100px;margin:0 auto;padding:48px 24px}

/* ── SUBSCRIBE CARD ── */
.subscribe-card{background:var(--card);border-radius:20px;box-shadow:var(--shadow);
                padding:40px 44px;margin-bottom:40px;
                border:1px solid rgba(99,102,241,.12)}
.subscribe-card h2{font-size:24px;font-weight:700;margin-bottom:6px}
.subscribe-card .subtitle{color:var(--muted);font-size:15px;margin-bottom:28px}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}
@media(max-width:600px){.form-row{grid-template-columns:1fr}}
.field{margin-bottom:16px}
.field label{display:block;font-size:13px;font-weight:600;color:var(--text);margin-bottom:6px}
.field label .optional{color:var(--muted);font-weight:400;font-size:12px}
.field input,.field select{width:100%;padding:12px 14px;
  border:2px solid var(--border);border-radius:10px;font-size:15px;
  background:#fff;color:var(--text);transition:border-color .2s,box-shadow .2s}
.field input:focus,.field select:focus{
  border-color:var(--primary);outline:none;
  box-shadow:0 0 0 3px rgba(99,102,241,.12)}
.phone-row{display:grid;grid-template-columns:1fr 140px;gap:12px}
.sms-note{font-size:12px;color:var(--muted);margin-top:6px}

/* ── SECTOR STOCK PICKER ── */
.stock-picker{background:#f8fafc;border:1px solid var(--border);
              border-radius:12px;padding:16px;margin-bottom:20px}
.stock-picker-label{font-size:13px;font-weight:600;margin-bottom:12px;color:var(--text)}
.sector-group{margin-bottom:10px}
.sector-toggle{display:flex;align-items:center;gap:8px;cursor:pointer;
               padding:8px 10px;border-radius:8px;
               border:1px solid transparent;
               transition:background .15s,border-color .15s;user-select:none}
.sector-toggle:hover{background:rgba(99,102,241,.06);border-color:rgba(99,102,241,.15)}
.sector-name{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.5px}
.sector-count{font-size:11px;color:var(--muted);font-weight:500}
.sector-chevron{margin-left:auto;font-size:11px;color:var(--muted);
                display:inline-block;transition:transform .25s ease}
.sector-group.open .sector-chevron{transform:rotate(180deg)}
.sector-stocks{display:flex;flex-wrap:wrap;gap:6px;overflow:hidden;
               max-height:0;transition:max-height .3s ease,padding .2s ease;
               padding:0 4px}
.sector-group.open .sector-stocks{max-height:400px;padding:8px 4px 4px}
.stock-chip{display:inline-flex;align-items:center;gap:5px;
            padding:4px 10px;border-radius:20px;font-size:12px;font-weight:600;
            background:#fff;border:1.5px solid var(--border);cursor:pointer;
            transition:all .15s}
.stock-chip input[type=checkbox]{width:12px;height:12px;cursor:pointer}
.stock-chip:has(input:checked){border-color:var(--primary);background:#eef2ff}
.all-stocks{display:flex;align-items:center;gap:8px;padding:10px 0 0;
            font-size:13px;color:var(--muted);font-style:italic;cursor:pointer}

/* ── SUBMIT BUTTON ── */
.btn-submit{width:100%;padding:16px;border:none;border-radius:12px;font-size:16px;
            font-weight:700;color:#fff;cursor:pointer;
            background:linear-gradient(135deg,var(--primary),#8b5cf6);
            box-shadow:0 4px 16px rgba(99,102,241,.4);
            transition:transform .2s,box-shadow .2s}
.btn-submit:hover{transform:translateY(-2px);box-shadow:0 6px 24px rgba(99,102,241,.5)}
.btn-submit:active{transform:translateY(0)}
.privacy-note{text-align:center;font-size:12px;color:var(--muted);margin-top:12px}

/* ── FEATURES ── */
.features{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-bottom:40px}
@media(max-width:700px){.features{grid-template-columns:1fr}}
.feature-card{background:var(--card);border-radius:var(--radius);padding:28px 24px;
              box-shadow:var(--shadow);border:1px solid var(--border);
              transition:transform .2s}
.feature-card:hover{transform:translateY(-3px)}
.feature-icon{font-size:32px;margin-bottom:14px}
.feature-card h3{font-size:16px;font-weight:700;margin-bottom:8px}
.feature-card p{font-size:14px;color:var(--muted);line-height:1.6}

/* ── KNOWLEDGE PREVIEW ── */
.section-head{display:flex;justify-content:space-between;align-items:center;
              margin-bottom:20px}
.section-head h2{font-size:20px;font-weight:700}
.see-all{font-size:14px;color:var(--primary)}
.topics-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin-bottom:40px}
@media(max-width:600px){.topics-grid{grid-template-columns:1fr}}
.topic-card{background:var(--card);border-radius:var(--radius);padding:18px 20px;
            box-shadow:var(--shadow);border:1px solid var(--border);
            transition:all .15s;cursor:pointer}
.topic-card:hover{transform:translateY(-2px);border-color:var(--primary)}
.topic-cat{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;
           margin-bottom:6px}
.topic-card h4{font-size:15px;font-weight:700;margin-bottom:6px;color:var(--text)}
.topic-card p{font-size:13px;color:var(--muted);line-height:1.5}

/* ── SOCIAL SHARE ── */
.share-section{background:var(--card);border-radius:20px;padding:36px 44px;
               border:1px solid var(--border);box-shadow:var(--shadow);
               text-align:center;margin-bottom:40px}
.share-section h2{font-size:20px;font-weight:700;margin-bottom:8px}
.share-section p{color:var(--muted);font-size:15px;margin-bottom:24px}
.share-buttons{display:flex;justify-content:center;gap:12px;flex-wrap:wrap}
.share-btn{display:inline-flex;align-items:center;gap:8px;
           padding:11px 22px;border-radius:10px;font-size:14px;font-weight:600;
           transition:transform .15s,box-shadow .15s;border:none;cursor:pointer}
.share-btn:hover{transform:translateY(-2px);text-decoration:none}
.share-twitter{background:#000;color:#fff}
.share-twitter:hover{background:#111}
.share-linkedin{background:#0a66c2;color:#fff}
.share-facebook{background:#1877f2;color:#fff}
.share-copy{background:#f1f5f9;color:var(--text);border:1px solid var(--border)}

/* ── SUCCESS / ERROR PAGES ── */
.page-card{background:var(--card);border-radius:20px;box-shadow:var(--shadow);
           max-width:520px;margin:60px auto;padding:48px 40px;text-align:center;
           border:1px solid var(--border)}
.page-card .icon{font-size:56px;margin-bottom:16px}
.page-card h2{font-size:22px;font-weight:700;margin-bottom:12px}
.page-card p{color:var(--muted);margin-bottom:8px;line-height:1.6}
.btn-back{display:inline-block;margin-top:20px;padding:10px 24px;
          border-radius:10px;background:var(--primary);color:#fff;font-weight:600;
          font-size:14px}
.btn-back:hover{text-decoration:none;color:#fff;background:var(--primary-dark)}
.btn-danger{background:#ef4444}
.btn-danger:hover{background:#dc2626}

/* ── LEARN PAGES ── */
.learn-card{background:var(--card);border-radius:20px;box-shadow:var(--shadow);
            max-width:720px;margin:0 auto;padding:40px 44px;
            border:1px solid var(--border)}
.learn-breadcrumb{font-size:13px;color:var(--muted);margin-bottom:20px}
.learn-breadcrumb a{color:var(--primary)}
.cat-badge{display:inline-block;padding:4px 12px;border-radius:50px;
           font-size:12px;font-weight:700;margin-bottom:14px}
.learn-card h2{font-size:24px;font-weight:700;margin-bottom:10px;color:var(--text)}
.learn-card hr{border:none;border-top:1px solid var(--border);margin:20px 0}
.learn-section h3{font-size:15px;font-weight:700;margin-bottom:8px;color:var(--text)}
.learn-section p{color:#374151;line-height:1.75;font-size:15px;margin-bottom:8px}
.tips-box{background:#f0fdf4;border:1px solid #86efac;border-radius:12px;
          padding:18px 22px;margin:20px 0}
.tips-box .tips-head{font-weight:700;color:#16a34a;margin-bottom:8px}
.tips-box ul{margin:0;padding-left:20px;color:#374151;line-height:1.75}
.learn-topics-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-top:20px}
@media(max-width:580px){.learn-topics-grid{grid-template-columns:1fr}}

/* ── FOOTER ── */
.footer{text-align:center;padding:32px 24px;color:var(--muted);font-size:13px;
        border-top:1px solid var(--border);background:#fff;margin-top:20px}
.footer a{color:var(--muted)}

/* ══════════════════════════════════════════════════════
   ENHANCED VISUALS — animations, glassmorphism, glow
   ══════════════════════════════════════════════════════ */

/* Animated aurora hero background */
@keyframes hero-shift{
  0%{background-position:0% 50%}
  50%{background-position:100% 50%}
  100%{background-position:0% 50%}
}
.hero{
  background:linear-gradient(-45deg,#020617,#0f172a,#1e1b4b,#2e1065,#0d1b3e,#130a2a,#020617) !important;
  background-size:500% 500% !important;
  animation:hero-shift 18s ease infinite;
}

/* Glowing floating orbs */
.hero-orb{position:absolute;border-radius:50%;filter:blur(100px);pointer-events:none;z-index:0}
.orb-1{width:560px;height:560px;
  background:radial-gradient(circle at center,#6366f1 0%,transparent 70%);
  opacity:.14;top:-180px;left:-120px;
  animation:orb-drift 12s ease-in-out infinite}
.orb-2{width:420px;height:420px;
  background:radial-gradient(circle at center,#8b5cf6 0%,transparent 70%);
  opacity:.11;top:20px;right:-80px;
  animation:orb-drift 16s ease-in-out infinite reverse}
.orb-3{width:380px;height:380px;
  background:radial-gradient(circle at center,#06b6d4 0%,transparent 70%);
  opacity:.09;bottom:-80px;left:38%;
  animation:orb-drift 20s ease-in-out infinite 4s}
.orb-4{width:280px;height:280px;
  background:radial-gradient(circle at center,#f59e0b 0%,transparent 70%);
  opacity:.06;top:30%;right:20%;
  animation:orb-drift 14s ease-in-out infinite 2s reverse}
@keyframes orb-drift{
  0%,100%{transform:translate(0,0) scale(1)}
  25%{transform:translate(50px,-40px) scale(1.07)}
  50%{transform:translate(-20px,30px) scale(.96)}
  75%{transform:translate(30px,10px) scale(1.04)}
}

/* Shimmer on hero CTA button */
@keyframes shimmer{0%{background-position:-200% center}100%{background-position:200% center}}
.hero-cta{
  background:linear-gradient(90deg,#4f46e5 0%,#7c3aed 20%,#a78bfa 40%,#7c3aed 60%,#6366f1 80%,#4f46e5 100%) !important;
  background-size:200% auto !important;
  animation:shimmer 4s linear infinite;
}

/* Pulsing hero badge */
@keyframes badge-glow{
  0%,100%{box-shadow:0 0 0 0 rgba(99,102,241,.0),0 0 8px rgba(99,102,241,.2)}
  50%{box-shadow:0 0 0 6px rgba(99,102,241,.0),0 0 20px rgba(99,102,241,.4)}
}
.hero-badge{animation:badge-glow 3s ease-in-out infinite}

/* Floating feature icons */
@keyframes icon-float{0%,100%{transform:translateY(0)}50%{transform:translateY(-7px)}}
.feature-icon{display:inline-block;animation:icon-float 3s ease-in-out infinite;
  filter:drop-shadow(0 4px 8px rgba(99,102,241,.25))}
.feature-card:nth-child(2) .feature-icon{animation-delay:.8s}
.feature-card:nth-child(3) .feature-icon{animation-delay:1.6s}

/* Glassmorphism feature cards */
.feature-card{
  background:rgba(255,255,255,.82) !important;
  backdrop-filter:blur(20px);
  -webkit-backdrop-filter:blur(20px);
  border:1px solid rgba(99,102,241,.12) !important;
  transition:transform .25s,box-shadow .3s,border-color .25s !important;
}
.feature-card:hover{
  transform:translateY(-8px) !important;
  box-shadow:0 20px 48px rgba(99,102,241,.16) !important;
  border-color:rgba(99,102,241,.35) !important;
}

/* Gradient animated stat numbers */
@keyframes stat-shine{0%{background-position:0% 50%}100%{background-position:200% 50%}}
.stat-num{
  background:linear-gradient(90deg,var(--primary),#a78bfa,#06b6d4,var(--primary)) !important;
  background-size:200% auto !important;
  -webkit-background-clip:text !important;
  -webkit-text-fill-color:transparent !important;
  background-clip:text !important;
  animation:stat-shine 5s linear infinite;
}

/* Subscribe card breathing glow */
@keyframes card-breathe{
  0%,100%{box-shadow:0 4px 24px rgba(0,0,0,.09),0 0 0 0 rgba(99,102,241,.0)}
  50%{box-shadow:0 8px 40px rgba(0,0,0,.12),0 0 50px rgba(99,102,241,.10)}
}
.subscribe-card{animation:card-breathe 6s ease-in-out infinite}

/* Richer body background */
body{
  background:
    radial-gradient(ellipse 80% 60% at 20% 10%,rgba(99,102,241,.06) 0%,transparent 60%),
    radial-gradient(ellipse 60% 40% at 80% 80%,rgba(139,92,246,.05) 0%,transparent 60%),
    linear-gradient(180deg,#eef2ff 0%,#f0f4ff 60%,#e8f0fe 100%) !important;
  background-attachment:fixed !important;
  min-height:100vh;
}

/* Ticker edge fade */
.ticker-wrap{
  -webkit-mask-image:linear-gradient(90deg,transparent,#000 7%,#000 93%,transparent) !important;
  mask-image:linear-gradient(90deg,transparent,#000 7%,#000 93%,transparent) !important;
}

/* Glowing checked stock chips */
.stock-chip:has(input:checked){
  border-color:var(--primary) !important;
  background:linear-gradient(135deg,#eef2ff,#e0e7ff) !important;
  box-shadow:0 0 10px rgba(99,102,241,.22) !important;
}
.stock-chip{transition:all .2s !important}
.stock-chip:hover{transform:scale(1.05) !important;box-shadow:0 2px 8px rgba(0,0,0,.08) !important}

/* Gradient section heads */
.section-head h2{
  background:linear-gradient(135deg,var(--text) 30%,var(--primary));
  -webkit-background-clip:text;
  -webkit-text-fill-color:transparent;
  background-clip:text;
}

/* Nav logo subtle glow */
.nav-logo{filter:drop-shadow(0 0 12px rgba(99,102,241,.35))}

/* Learn page accent */
.hero h1{text-shadow:0 0 80px rgba(99,102,241,.2)}

/* ══════════════════════════════════════════════════════
   DARK THEME — midnight gradient background
   ══════════════════════════════════════════════════════ */

:root{
  --bg:#07091a;
  --card:rgba(255,255,255,.045);
  --border:rgba(255,255,255,.09);
  --text:#e2e8f0;
  --muted:#94a3b8;
  --shadow:0 4px 32px rgba(0,0,0,.5);
}

body{
  background:
    radial-gradient(ellipse 90% 55% at 8% 15%,rgba(99,102,241,.13) 0%,transparent 55%),
    radial-gradient(ellipse 70% 50% at 92% 75%,rgba(139,92,246,.10) 0%,transparent 55%),
    radial-gradient(ellipse 55% 35% at 50% 50%,rgba(6,182,212,.05) 0%,transparent 60%),
    linear-gradient(160deg,#05091a 0%,#0c0f2e 45%,#070c1d 100%) !important;
  color:var(--text) !important;
  background-attachment:fixed !important;
}

.stats{background:rgba(255,255,255,.025) !important;
       border-bottom:1px solid rgba(255,255,255,.07) !important}

.subscribe-card,.feature-card,.topic-card,.share-section,.page-card{
  background:rgba(255,255,255,.045) !important;
  border:1px solid rgba(255,255,255,.09) !important;
  backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);
}

.field input,.field select{
  background:rgba(255,255,255,.07) !important;
  border:1.5px solid rgba(255,255,255,.11) !important;
  color:var(--text) !important;
}
.field input::placeholder{color:rgba(255,255,255,.28) !important}
.field input:focus,.field select:focus{
  background:rgba(255,255,255,.10) !important;border-color:var(--primary) !important;
}
.field select option{background:#151929;color:#e2e8f0}

.stock-picker{background:rgba(255,255,255,.03) !important;
              border:1px solid rgba(255,255,255,.08) !important}
.sector-toggle:hover{background:rgba(255,255,255,.06) !important;
                     border-color:rgba(99,102,241,.35) !important}
.stock-chip{background:rgba(255,255,255,.06) !important;
            border-color:rgba(255,255,255,.11) !important;color:var(--text) !important}
.stock-chip:has(input:checked){
  background:rgba(99,102,241,.22) !important;border-color:var(--primary) !important;
  box-shadow:0 0 14px rgba(99,102,241,.35) !important;
}
.stock-picker-label{color:rgba(255,255,255,.85) !important}
.all-stocks,.sector-count,.sector-chevron{color:rgba(255,255,255,.38) !important}

.field label{color:rgba(255,255,255,.78) !important}
.subscribe-card h2{color:var(--text) !important}
.subscribe-card .subtitle,.privacy-note,.sms-note{color:var(--muted) !important}
.feature-card h3{color:var(--text) !important}
.feature-card p{color:var(--muted) !important}
.topic-card h4{color:var(--text) !important}
.topic-card p{color:var(--muted) !important}
.topic-card:hover{background:rgba(255,255,255,.08) !important;
                  border-color:rgba(99,102,241,.4) !important}
.share-section h2{color:var(--text) !important}
.share-section p{color:var(--muted) !important}
.share-copy{background:rgba(255,255,255,.08) !important;
            border:1px solid rgba(255,255,255,.12) !important;color:var(--text) !important}

.section-head h2{
  background:linear-gradient(135deg,#e2e8f0 20%,#818cf8) !important;
  -webkit-background-clip:text !important;-webkit-text-fill-color:transparent !important;
  background-clip:text !important;
}

.footer{background:rgba(0,0,0,.35) !important;
        border-top:1px solid rgba(255,255,255,.07) !important;color:var(--muted) !important}
.footer a{color:var(--muted) !important}

.learn-card{
  background:rgba(255,255,255,.045) !important;
  border:1px solid rgba(255,255,255,.09) !important;
  backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);
}
.learn-card h2{color:var(--text) !important}
.learn-breadcrumb{color:var(--muted) !important}
.learn-section h3{color:var(--text) !important}
.learn-section p{color:rgba(226,232,240,.78) !important}
.tips-box{background:rgba(16,185,129,.10) !important;border-color:rgba(16,185,129,.30) !important}
.tips-box ul{color:rgba(226,232,240,.82) !important}
.tips-box .tips-head{color:#34d399 !important}

@keyframes card-breathe{
  0%,100%{box-shadow:0 4px 40px rgba(0,0,0,.55),0 0 0 0 rgba(99,102,241,.0)}
  50%{box-shadow:0 8px 60px rgba(0,0,0,.65),0 0 60px rgba(99,102,241,.14)}
}

/* ── STOCKS OF THE WEEK ── */
.sotw-section,.watchout-section{margin-bottom:40px}
.sotw-grid,.watchout-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
@media(max-width:860px){.sotw-grid,.watchout-grid{grid-template-columns:1fr}}
.sotw-card,.watchout-card{
  background:rgba(255,255,255,.045);border:1px solid rgba(255,255,255,.09);
  backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
  border-radius:var(--radius);padding:20px 22px;box-shadow:var(--shadow);
}
.sotw-head,.watchout-head{
  font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.6px;
  margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid rgba(255,255,255,.08);
  color:rgba(255,255,255,.7);
}
.sotw-row,.earnings-row,.event-row{
  display:flex;align-items:center;gap:8px;
  padding:9px 0;border-bottom:1px solid rgba(255,255,255,.05);font-size:13px;
}
.sotw-row:last-child,.earnings-row:last-child,.event-row:last-child{border-bottom:none}
.sotw-sym,.earnings-sym{font-weight:700;color:#e2e8f0;min-width:50px;font-size:13px}
.sotw-price{color:rgba(255,255,255,.5);font-size:12px}
.sotw-chg{margin-left:auto;font-weight:700;font-size:12px}
.sotw-conf{font-size:11px;color:#818cf8;font-weight:600;margin-left:auto}
.sotw-rsi{font-size:11px;color:rgba(255,255,255,.4);margin-left:auto}
.sotw-vol{font-size:11px;color:#f59e0b;font-weight:600;margin-left:auto}
.sotw-empty{color:rgba(255,255,255,.25);font-size:13px;text-align:center;padding:18px 0;font-style:italic}
.sotw-sub{font-size:11px;color:rgba(255,255,255,.35)}
.earnings-date{color:rgba(255,255,255,.45);font-size:11px}
.earnings-days{font-weight:700;font-size:11px;margin-left:auto}
.earnings-days.soon{color:#f87171}
.earnings-days.week{color:#fcd34d}
.earnings-days.future{color:#94a3b8}
.earnings-reaction{font-size:11px;color:rgba(255,255,255,.4)}
.event-name{color:#e2e8f0;font-weight:600;font-size:13px}
.event-detail{color:rgba(255,255,255,.4);font-size:11px;margin-top:2px}
.event-impact{font-size:10px;padding:2px 8px;border-radius:50px;font-weight:700;margin-left:auto;white-space:nowrap}
.impact-high{background:rgba(239,68,68,.2);color:#fca5a5}
.impact-med{background:rgba(245,158,11,.2);color:#fcd34d}
.impact-low{background:rgba(99,102,241,.2);color:#a5b4fc}
.level-bar{height:3px;background:rgba(255,255,255,.1);border-radius:2px;margin-top:4px;overflow:hidden}
.level-fill{height:100%;border-radius:2px;transition:width .4s}

/* ── WATCHLIST TABLE ── */
.wl-section{margin-bottom:40px}
.wl-controls{display:flex;align-items:center;gap:10px;margin-bottom:14px;flex-wrap:wrap}
.wl-search{background:rgba(255,255,255,.07);border:1.5px solid rgba(255,255,255,.11);
           color:#e2e8f0;padding:8px 14px;border-radius:8px;font-size:13px;
           flex:1;max-width:340px;min-width:160px;transition:border-color .2s}
.wl-search::placeholder{color:rgba(255,255,255,.28)}
.wl-search:focus{outline:none;border-color:var(--primary);background:rgba(255,255,255,.10)}
.wl-btn{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.11);
        color:rgba(255,255,255,.65);padding:7px 14px;border-radius:8px;font-size:12px;
        cursor:pointer;font-weight:600;transition:all .15s}
.wl-btn:hover{background:rgba(255,255,255,.14);color:#fff;border-color:rgba(255,255,255,.22)}
.wl-ts{font-size:11px;color:rgba(255,255,255,.28);margin-left:auto}
.wl-wrap{overflow-x:auto;border-radius:12px;
         border:1px solid rgba(255,255,255,.09);
         background:rgba(255,255,255,.02)}
.wl-table{width:100%;border-collapse:collapse;font-size:13px;min-width:640px}
.wl-table thead th{padding:10px 14px;text-align:left;font-size:11px;font-weight:700;
                   text-transform:uppercase;letter-spacing:.6px;
                   color:rgba(255,255,255,.38);background:rgba(0,0,0,.28);
                   position:sticky;top:0;z-index:2;white-space:nowrap}
.wl-table thead th:not(:first-child){text-align:right}
.wl-sect-row td{padding:9px 14px;font-size:11px;font-weight:700;
                text-transform:uppercase;letter-spacing:.8px;
                background:rgba(0,0,0,.22);cursor:pointer;user-select:none;
                border-top:1px solid rgba(255,255,255,.05)}
.wl-sect-row:first-child td{border-top:none}
.wl-sect-toggle{display:flex;align-items:center;gap:8px}
.wl-sect-count{opacity:.38;font-size:10px;font-weight:500;margin-left:4px}
.wl-sect-chev{margin-left:auto;font-size:10px;opacity:.38;
              display:inline-block;transition:transform .22s}
.wl-sect-row.wl-open .wl-sect-chev{transform:rotate(180deg)}
.wl-row td{padding:8px 14px;border-bottom:1px solid rgba(255,255,255,.038)}
.wl-row:last-of-type td,.wl-row.wl-last td{border-bottom:none}
.wl-row:hover td{background:rgba(255,255,255,.04)}
.wl-row.wl-hidden{display:none}
.wl-sym{font-weight:700;color:#e2e8f0;white-space:nowrap}
.wl-price{color:#e2e8f0;text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.wl-chg{font-weight:700;text-align:right;white-space:nowrap}
.wl-vol{color:rgba(255,255,255,.42);text-align:right;font-size:12px}
.wl-rsi{text-align:right;font-size:12px;font-weight:600}
.wl-vs{text-align:right;font-size:12px;font-weight:600}
.wl-sig{text-align:right}
.wl-conf{text-align:right;color:rgba(255,255,255,.38);font-size:12px}
.wl-badge{display:inline-block;padding:2px 9px;border-radius:50px;font-size:11px;font-weight:700;white-space:nowrap}
.wl-bull{background:rgba(16,185,129,.2);color:#34d399}
.wl-bear{background:rgba(239,68,68,.2);color:#f87171}
.wl-neut{background:rgba(99,102,241,.14);color:#818cf8}
.wl-na{color:rgba(255,255,255,.22)}
@media(max-width:580px){.wl-search{width:100%}.wl-controls{flex-direction:column;align-items:flex-start}.wl-ts{margin-left:0}}

/* ── OPTIONS INTELLIGENCE ── */
.opt-section{margin-bottom:40px}
.opt-tabs{display:flex;gap:10px;margin-bottom:16px;flex-wrap:wrap}
.opt-tab{padding:8px 20px;border-radius:8px;font-size:13px;font-weight:700;
         border:1.5px solid rgba(255,255,255,.12);cursor:pointer;
         background:rgba(255,255,255,.045);color:rgba(255,255,255,.55);
         transition:all .18s}
.opt-tab.active-call{background:rgba(16,185,129,.18);border-color:#10b981;color:#34d399}
.opt-tab.active-put{background:rgba(239,68,68,.18);border-color:#ef4444;color:#f87171}
.opt-tab:hover{background:rgba(255,255,255,.09);color:#fff}
.opt-panel{display:none}
.opt-panel.active{display:block}
.opt-wrap{overflow-x:auto;border-radius:12px;border:1px solid rgba(255,255,255,.09);
          background:rgba(255,255,255,.02)}
.opt-table{width:100%;border-collapse:collapse;font-size:13px;min-width:720px}
.opt-table thead th{padding:10px 14px;text-align:left;font-size:11px;font-weight:700;
                    text-transform:uppercase;letter-spacing:.6px;
                    background:rgba(255,255,255,.04);color:rgba(255,255,255,.45);
                    white-space:nowrap}
.opt-table thead th:not(:first-child){text-align:right}
.opt-table tbody tr{border-bottom:1px solid rgba(255,255,255,.038)}
.opt-table tbody tr:last-child{border-bottom:none}
.opt-table tbody tr:hover td{background:rgba(255,255,255,.04)}
.opt-table td{padding:10px 14px;white-space:nowrap}
.opt-sym{font-weight:700;color:#e2e8f0}
.opt-badge-call{display:inline-block;padding:2px 8px;border-radius:5px;
                font-size:11px;font-weight:700;letter-spacing:.4px;
                background:rgba(16,185,129,.2);color:#34d399}
.opt-badge-put{display:inline-block;padding:2px 8px;border-radius:5px;
               font-size:11px;font-weight:700;letter-spacing:.4px;
               background:rgba(239,68,68,.2);color:#f87171}
.opt-score{font-weight:700}
.opt-score-hi{color:#34d399}
.opt-score-mid{color:#fbbf24}
.opt-score-lo{color:rgba(255,255,255,.42)}
.opt-reason{font-size:11px;color:rgba(255,255,255,.42);max-width:280px;
            white-space:normal;line-height:1.4}
.opt-empty{text-align:center;padding:28px;color:rgba(255,255,255,.28);font-style:italic}
.opt-disclaimer{margin-top:10px;font-size:11px;color:rgba(255,255,255,.3);text-align:center}
"""


# ── helpers ───────────────────────────────────────────────────────────────────

def _watchlist() -> list[str]:
    return cfg_mod.load_config().get("watchlist", [])


def _base_url() -> str:
    return "https://" + request.host


def _sector_css(sector: str) -> str:
    return _SECTOR_CSS.get(sector, "#64748b")


def _fmt_price(price, sym="") -> str:
    """Format a price with appropriate precision (handles micro-price crypto)."""
    if price is None:
        return "N/A"
    if sec_mod.is_crypto(sym) and price > 1000:
        return f"${price:,.0f}"
    if price >= 100:
        return f"${price:,.2f}"
    if price >= 1:
        return f"${price:.3f}"
    if price >= 0.01:
        return f"${price:.4f}"
    if price >= 0.0001:
        return f"${price:.6f}"
    # micro-price tokens: SHIB, BONK, PEPE, FLOKI, etc.
    return f"${price:.8f}"


def _ticker_html(stocks: list[dict]) -> str:
    """Build the animated ticker tape items (doubled for seamless loop)."""
    items = []
    for s in stocks:
        sym   = s.get("symbol", "")
        disp  = sec_mod.display_symbol(sym)
        price = s.get("price")
        chg   = s.get("change_pct") or 0
        if price is None:
            continue
        arrow = "&#9650;" if chg >= 0 else "&#9660;"
        cls   = "up" if chg >= 0 else "down"
        items.append(
            f'<span class="ticker-item">'
            f'<span class="ticker-sym">{disp}</span>'
            f'<span class="ticker-price">{_fmt_price(price, sym)}</span>'
            f'<span class="{cls}">{arrow} {abs(chg):.2f}%</span>'
            f'</span>'
            f'<span class="ticker-sep">|</span>'
        )
    if not items:
        items = ['<span class="ticker-item">Loading market data...</span>']
    combined = "".join(items)
    return combined + combined  # double for seamless loop


def _base_html(title: str, body: str, extra_head: str = "") -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{title} -- Stock Tracker</title>
  <meta name="description" content="Free AI-powered stock, crypto, and penny stock alerts via email and SMS.">
  <meta property="og:title" content="{title} -- Stock Tracker">
  <meta property="og:description" content="Get real-time signals for stocks, crypto, and penny shares — free.">
  <style>{_CSS}</style>
  {extra_head}
</head>
<body>
{body}
</body>
</html>"""


def _learn_base(title: str, body: str) -> str:
    return _base_html(
        title,
        f"""<nav class="nav">
  <div class="nav-logo"><span>&#x1F4C8;</span> Stock Tracker</div>
  <div class="nav-links">
    <a href="/">Alerts</a>
    <a href="/learn">Knowledge Base</a>
  </div>
</nav>
<div style="max-width:1100px;margin:0 auto;padding:40px 24px">
  {body}
</div>
<footer class="footer">&#x1F4C8; Stock Tracker &bull;
  <a href="/learn">Knowledge Base</a> &bull;
  <a href="/">Subscribe</a>
</footer>"""
    )


# ── application factory ───────────────────────────────────────────────────────

def create_app() -> Flask:
    _app = Flask(__name__)

    @_app.after_request
    def _security_headers(response: Response) -> Response:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"]    = "nosniff"
        response.headers["X-Frame-Options"]           = "DENY"
        response.headers["X-XSS-Protection"]          = "1; mode=block"
        response.headers["Referrer-Policy"]           = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"]   = (
            "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; "
            "form-action 'self'; img-src 'self' data:"
        )
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        return response

    # ── status / debug ────────────────────────────────────────────────────────

    @_app.route("/debug-options")
    def debug_options():
        import json as _json
        stocks = db.get_all_stocks()
        signals = [
            {"symbol": s["symbol"], "price": s.get("price"), "prediction": s.get("prediction"),
             "confidence": round(s.get("prediction_confidence") or 0, 3)}
            for s in stocks
            if s.get("prediction") in ("BULLISH", "BEARISH")
        ]
        signals.sort(key=lambda x: x["confidence"], reverse=True)
        opt_recs = db.get_option_recs(40)
        return Response(_json.dumps({
            "total_stocks": len(stocks),
            "bullish_bearish_signals": len(signals),
            "top_signals": signals[:30],
            "options_recs_in_db": len(opt_recs),
            "options_recs": opt_recs[:10],
        }, indent=2), mimetype="application/json")

    @_app.route("/option-chart.png")
    def option_chart_png():
        """
        Generate a payoff-at-expiry PNG chart for one option contract.
        Query params: t=CALL|PUT  k=strike  p=current_price  b=bid  a=ask
        Example: /option-chart.png?t=CALL&k=155&p=154.92&b=3.75&a=4.00
        """
        import io
        import matplotlib
        matplotlib.use("Agg")          # non-interactive, thread-safe
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        import numpy as np

        opt_type = request.args.get("t", "CALL").upper()
        try:
            strike  = float(request.args.get("k", 100))
            price   = float(request.args.get("p", 100))
            bid     = float(request.args.get("b", 1))
            ask     = float(request.args.get("a", 1))
        except (ValueError, TypeError):
            return Response("bad params", status=400)

        mid = (bid + ask) / 2 if bid > 0 and ask > 0 else max(bid, ask, 0.01)
        be  = strike + mid if opt_type == "CALL" else strike - mid

        # X-axis range
        x0 = min(strike * 0.84, be * 0.97, price * 0.93)
        x1 = max(strike * 1.16, be * 1.03, price * 1.07)
        pad = (x1 - x0) * 0.05
        x0 -= pad;  x1 += pad
        xs = np.linspace(x0, x1, 300)

        if opt_type == "CALL":
            ys = np.maximum(xs - strike, 0) - mid
        else:
            ys = np.maximum(strike - xs, 0) - mid

        # ── Figure ────────────────────────────────────────────────────────────
        fig, ax = plt.subplots(figsize=(5.2, 1.35), dpi=110)
        fig.patch.set_facecolor("#0f172a")
        ax.set_facecolor("#0f172a")

        # Fill zones
        ax.fill_between(xs, ys, 0, where=(ys >= 0),
                        color="#22c55e", alpha=0.18, linewidth=0)
        ax.fill_between(xs, ys, 0, where=(ys < 0),
                        color="#ef4444", alpha=0.13, linewidth=0)

        # Payoff curve
        col = "#16a34a" if opt_type == "CALL" else "#dc2626"
        ax.plot(xs, ys, color=col, linewidth=2, zorder=5)

        # Zero line
        ax.axhline(0, color="#334155", linewidth=0.8, zorder=2)

        # Vertical reference lines
        ax.axvline(strike, color="#f59e0b", linewidth=1.2,
                   linestyle="--", zorder=4, label=f"K ${strike:.0f}")
        ax.axvline(price,  color="#e2e8f0", linewidth=0.9,
                   linestyle=(0, (3, 5)), zorder=4, alpha=0.8,
                   label=f"Now ${price:.2f}")
        ax.axvline(be,     color=col,       linewidth=0.9,
                   linestyle=":",  zorder=4, alpha=0.65,
                   label=f"BE ${be:.2f}")

        # Axes styling
        for spine in ax.spines.values():
            spine.set_color("#334155")
        ax.tick_params(colors="#64748b", labelsize=7)
        ax.yaxis.set_tick_params(labelsize=7)

        # Y ticks: max loss, zero, one profit level
        y_ticks = [-mid, 0, mid * 2]
        y_labels = [f"-${mid:.2f}", "$0", f"+${mid*2:.2f}"]
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_labels, color="#64748b", fontsize=7)

        # X ticks: strike and current price
        x_tick_vals  = [strike]
        x_tick_lbls  = [f"K${strike:.0f}"]
        if abs(price - strike) / strike > 0.015:
            x_tick_vals.append(price)
            x_tick_lbls.append(f"${price:.2f}")
        ax.set_xticks(x_tick_vals)
        ax.set_xticklabels(x_tick_lbls, color="#94a3b8", fontsize=7)

        # Legend — compact, top corner
        leg = ax.legend(fontsize=7, loc="upper left" if opt_type == "CALL" else "upper right",
                        facecolor="#1e293b", edgecolor="#334155",
                        labelcolor="#94a3b8", framealpha=0.9,
                        handlelength=1.4, borderpad=0.5, labelspacing=0.3)

        ax.set_xlim(x0, x1)
        plt.tight_layout(pad=0.3)

        buf = io.BytesIO()
        plt.savefig(buf, format="png", facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)

        resp = Response(buf.read(), mimetype="image/png")
        resp.headers["Cache-Control"] = "public, max-age=3600"
        return resp

    @_app.route("/test-options-email")
    def test_options_email():
        """Force-send a test options alert email using current DB recs. Admin use only."""
        import json as _json
        from . import alerts as alert_mod
        config = cfg_mod.load_config()
        recs = db.get_option_recs(10)
        if not recs:
            return Response(_json.dumps({"status": "no_recs", "message": "No options recs in DB yet."}),
                            mimetype="application/json")
        # Convert DB field names (opt_type) to the alert builder's expected field name (type)
        for r in recs:
            r.setdefault("type", r.get("opt_type", ""))
            r.setdefault("last", r.get("last_price", 0))
        try:
            sent = alert_mod.send_options_alert(recs, config)
            return Response(_json.dumps({
                "status": "sent",
                "recs_included": len(recs),
                "subscribers_notified": sent,
                "symbols": sorted({r["symbol"] for r in recs}),
            }, indent=2), mimetype="application/json")
        except Exception as e:
            return Response(_json.dumps({"status": "error", "message": str(e)}),
                            mimetype="application/json")

    @_app.route("/test-alert-email")
    def test_alert_email():
        """Preview the subscriber alert email HTML using live DB data. Admin use only."""
        from . import alerts as alert_mod
        stocks   = db.get_all_stocks()
        earnings = db.get_upcoming_earnings()
        alerts_l = db.get_recent_alerts(20)
        html     = alert_mod.build_email_report(stocks, earnings, alerts_l)
        return Response(html, mimetype="text/html")

    @_app.route("/send-test-alert-email")
    def send_test_alert_email():
        """
        Send a test alert to the admin recipient via email AND SMS (if configured).
        Admin use only.
        """
        import json as _json
        from . import alerts as alert_mod
        from . import sms as sms_mod
        config   = cfg_mod.load_config()
        stocks   = db.get_all_stocks()
        earnings = db.get_upcoming_earnings()
        alerts_l = db.get_recent_alerts(20)
        subject  = "Stock Tracker — Test Alert"
        html     = alert_mod.build_email_report(stocks, earnings, alerts_l)
        sms_text = alert_mod.build_sms_summary(stocks)

        # Email to admin recipient
        recipient = config.get("email", {}).get("recipient", "")
        email_ok  = alert_mod.send_email(subject, html, config, recipient)

        # SMS to admin if a phone is set in config
        admin_phone   = config.get("admin_phone", "").strip()
        admin_carrier = config.get("admin_carrier", "").strip()
        sms_ok = False
        if admin_phone:
            sms_ok = sms_mod.send_sms(admin_phone, admin_carrier, sms_text, config)

        # Fan-out to all subscribers (email + SMS per their preferences)
        counts = alert_mod.notify_subscribers(subject, html, sms_text, set(), config)

        ai_sigs  = len([s for s in stocks if s.get("prediction") in ("BULLISH","BEARISH")
                        and (s.get("prediction_confidence") or 0) >= 0.50])
        movers   = min(10, len([s for s in stocks if s.get("change_pct") is not None]))
        extremes = len([s for s in stocks if s.get("rsi") is not None
                        and (s["rsi"] <= 30 or s["rsi"] >= 70)])

        return Response(_json.dumps({
            "email": {"status": "sent" if email_ok else "failed", "recipient": recipient},
            "sms":   {"status": "sent" if sms_ok else ("skipped — no admin_phone in config" if not admin_phone else "failed"),
                      "phone": admin_phone or None},
            "subscribers": {"email_sent": counts["email_sent"], "sms_sent": counts["sms_sent"]},
            "content": {"ai_signals": ai_sigs, "top_movers": movers, "tech_extremes": extremes},
            "sms_preview": sms_text,
        }, indent=2), mimetype="application/json")

    @_app.route("/status")
    def status():
        import json as _json
        config  = cfg_mod.load_config()
        stocks  = db.get_all_stocks()
        db_syms = {s["symbol"] for s in stocks}
        wl      = config.get("watchlist", [])
        missing = [s for s in wl if s not in db_syms]
        penny   = [s for s in stocks if (s.get("price") or 0) < 10 and not sec_mod.is_crypto(s["symbol"])]
        return Response(
            _json.dumps({
                "db_path": str(db.DB_PATH),
                "watchlist_count": len(wl),
                "total_stocks": len(stocks),
                "missing_from_db": missing,
                "penny_stocks": len(penny),
                "penny_symbols": [s["symbol"] for s in penny],
                "sample": [{k: s[k] for k in ("symbol","price","rsi","prediction") if k in s} for s in penny[:5]],
            }, indent=2),
            mimetype="application/json"
        )

    # ── main index ────────────────────────────────────────────────────────────

    @_app.route("/")
    def index():
        config      = cfg_mod.load_config()
        watchlist   = config.get("watchlist", [])
        stock_sectors = config.get("stock_sectors", {})
        all_db      = {s["symbol"]: s for s in db.get_all_stocks()}
        public_url  = config.get("social", {}).get("public_url", "")

        # -- ticker tape stocks
        ticker_stocks = [all_db[sym] for sym in watchlist if sym in all_db]
        ticker = _ticker_html(ticker_stocks)

        # -- stats
        n_stocks   = len(watchlist)
        n_sectors  = len({sec_mod.resolve_sector(s, stock_sectors) for s in watchlist})
        n_subs     = len(db.get_active_subscribers())
        n_alerts   = len(db.get_recent_alerts(999))
        n_topics   = len(kb_mod.KNOWLEDGE_BASE)
        twilio_on  = bool(config.get("sms", {}).get("twilio_sid"))

        # -- sector-grouped stock checkboxes
        grouped: dict[str, list[str]] = {}
        for sym in watchlist:
            sect = sec_mod.resolve_sector(sym, stock_sectors)
            grouped.setdefault(sect, []).append(sym)

        catalog_order = list(sec_mod.SECTOR_CATALOG.keys())
        def _skey(n): return (catalog_order.index(n) if n in catalog_order else 999, n)
        sorted_sects = sorted(grouped.keys(), key=_skey)

        sector_html = ""
        for sect in sorted_sects:
            color = _sector_css(sect)
            syms  = grouped[sect]
            chips = "".join(
                f'<label class="stock-chip" style="border-color:{color}20">'
                f'<input type="checkbox" name="stocks" value="{s}" checked>'
                f'<span>{sec_mod.display_symbol(s)}</span></label>'
                for s in sorted(syms)
            )
            sector_html += f"""
            <div class="sector-group open">
              <div class="sector-toggle">
                <span class="sector-name" style="color:{color}">{sect}</span>
                <span class="sector-count">({len(syms)})</span>
                <span class="sector-chevron">&#x25BE;</span>
              </div>
              <div class="sector-stocks">{chips}</div>
            </div>"""

        # -- carrier dropdown (SMS without Twilio)
        carrier_select = ""
        if not twilio_on:
            from . import sms as sms_mod_local
            opts = "".join(f'<option value="{c}">{c}</option>'
                           for c in sms_mod_local.CARRIER_GATEWAYS)
            carrier_select = f"""
            <div class="field" style="flex:0 0 140px">
              <label>Carrier <span class="optional">(SMS)</span></label>
              <select name="carrier">{opts}</select>
            </div>"""

        # -- stocks of the week data
        from datetime import datetime as _dt, timedelta as _td
        _now = _dt.now()
        _stocks_w_price = [s for s in all_db.values() if s.get("price")]
        _eq_stocks = [s for s in _stocks_w_price if not sec_mod.is_crypto(s["symbol"])]

        sotw_bullish = sorted(
            [s for s in _eq_stocks if s.get("prediction") in ("BULLISH", "UP") and s.get("prediction_confidence")],
            key=lambda x: x.get("prediction_confidence", 0), reverse=True
        )[:5]
        # fallback: if no BULLISH signals, show top signals by confidence (any direction)
        if not sotw_bullish:
            sotw_bullish = sorted(
                [s for s in _eq_stocks if s.get("prediction") and s.get("prediction_confidence")],
                key=lambda x: x.get("prediction_confidence", 0), reverse=True
            )[:5]
        sotw_bearish = sorted(
            [s for s in _eq_stocks if s.get("prediction") in ("BEARISH", "DOWN") and s.get("prediction_confidence")],
            key=lambda x: x.get("prediction_confidence", 0), reverse=True
        )[:2]
        sotw_movers = sorted(
            [s for s in _stocks_w_price if s.get("change_pct") is not None],
            key=lambda x: abs(x.get("change_pct", 0)), reverse=True
        )[:5]
        sotw_oversold = sorted(
            [s for s in _eq_stocks if s.get("rsi") and s.get("rsi") < 33],
            key=lambda x: x.get("rsi")
        )[:3]
        sotw_overbought = sorted(
            [s for s in _eq_stocks if s.get("rsi") and s.get("rsi") > 67],
            key=lambda x: -x.get("rsi")
        )[:3]
        sotw_volume = sorted(
            [s for s in _eq_stocks if s.get("volume") and s.get("avg_volume") and s["avg_volume"] > 50000],
            key=lambda x: x["volume"] / max(x["avg_volume"], 1), reverse=True
        )[:3]
        sotw_near_ma = [
            s for s in _eq_stocks
            if s.get("ma50") and s.get("price") and
            abs(s["price"] - s["ma50"]) / s["ma50"] < 0.015
        ][:4]

        # ── Penny stocks with potential ───────────────────────────────────────
        _penny_threshold = 10.0
        _penny_stocks = [
            s for s in _stocks_w_price
            if (s.get("price") or 0) < _penny_threshold
            and not sec_mod.is_crypto(s["symbol"])
        ]

        def _penny_score(s):
            score = 0
            if s.get("prediction") in ("BULLISH", "UP"):
                score += (s.get("prediction_confidence") or 0) * 40
            rsi = s.get("rsi") or 50
            if rsi < 35:
                score += (35 - rsi)           # oversold bonus
            elif rsi > 65:
                score -= (rsi - 65)           # overbought penalty
            vol = s.get("volume") or 0
            avg = s.get("avg_volume") or 1
            if avg > 0:
                score += min(vol / avg - 1, 3) * 5  # volume spike bonus (capped)
            chg = s.get("change_pct") or 0
            score += chg * 0.5                # positive momentum bonus
            return score

        # "Rising & Bullish" — top scored penny stocks (no change_pct gate so weekends work)
        penny_rising    = sorted(_penny_stocks, key=_penny_score, reverse=True)[:5]
        # "Oversold" — RSI < 45 (relaxed from 35 so at least a few always show)
        penny_oversold  = sorted(
            [s for s in _penny_stocks if (s.get("rsi") or 99) < 45],
            key=lambda x: x.get("rsi") or 99
        )[:5]
        # fallback: if nothing under 45, show lowest RSI stocks
        if not penny_oversold:
            penny_oversold = sorted(
                [s for s in _penny_stocks if s.get("rsi")],
                key=lambda x: x.get("rsi") or 99
            )[:5]
        # "Volume Spikes" — >1.2x avg, lowered from 1.5x; no minimum avg_volume gate
        penny_volume    = sorted(
            [s for s in _penny_stocks
             if (s.get("volume") or 0) > 0
             and (s.get("avg_volume") or 0) > 0
             and (s.get("volume") or 0) / max(s.get("avg_volume") or 1, 1) > 1.2],
            key=lambda x: (x.get("volume") or 0) / max(x.get("avg_volume") or 1, 1),
            reverse=True
        )[:5]
        # fallback: show highest relative-volume penny stocks
        if not penny_volume:
            penny_volume = sorted(
                [s for s in _penny_stocks if (s.get("avg_volume") or 0) > 0],
                key=lambda x: (x.get("volume") or 0) / max(x.get("avg_volume") or 1, 1),
                reverse=True
            )[:5]

        # upcoming earnings for What to Watch section
        upcoming_earnings_all = db.get_upcoming_earnings()

        # market context events
        _month, _day = _now.month, _now.day
        _first = _now.replace(day=1)
        _fri_off = (4 - _first.weekday()) % 7
        _third_fri = _first + _td(days=_fri_off + 14)
        _opex_days = (_third_fri.date() - _now.date()).days
        _market_events = []
        if _month in (4, 5):
            _market_events.append({"name": "Q1 2026 Earnings Season", "detail": "Companies reporting Jan–Mar results", "impact": "high"})
        elif _month in (7, 8):
            _market_events.append({"name": "Q2 2026 Earnings Season", "detail": "Companies reporting Apr–Jun results", "impact": "high"})
        elif _month in (10, 11):
            _market_events.append({"name": "Q3 2026 Earnings Season", "detail": "Companies reporting Jul–Sep results", "impact": "high"})
        elif _month in (1, 2):
            _market_events.append({"name": "Q4 / Full Year Earnings", "detail": "Annual results and forward guidance", "impact": "high"})
        if 0 <= _opex_days <= 10:
            _market_events.append({"name": f"Options Expiration (OPEX)", "detail": f"{_third_fri.strftime('%A %b %d')} — volatility typically spikes", "impact": "high"})
        if 1 <= _day <= 8:
            _market_events.append({"name": "Non-Farm Payrolls (NFP)", "detail": "Monthly jobs report — biggest single market mover", "impact": "high"})
        if 7 <= _day <= 16:
            _market_events.append({"name": "CPI Inflation Report", "detail": "Monthly consumer price data — moves bonds & equities", "impact": "high"})
        if 12 <= _day <= 20:
            _market_events.append({"name": "Retail Sales Data", "detail": "Consumer spending health indicator", "impact": "med"})
        _market_events.append({"name": "Weekly Jobless Claims", "detail": "Every Thursday 8:30am ET — labor market pulse", "impact": "low"})
        _market_events.append({"name": "Fed Officials Speaking", "detail": "Watch for rate guidance and policy hints", "impact": "med"})
        _market_events = _market_events[:5]

        # -- build SOTW html blocks
        def _chg_cls(pct): return "up" if (pct or 0) >= 0 else "down"
        def _chg_str(pct): return f"+{pct:.1f}%" if (pct or 0) >= 0 else f"{pct:.1f}%"

        def _sotw_row(s, extra=""):
            sym  = sec_mod.display_symbol(s["symbol"])
            pr   = _fmt_price(s.get("price"), s["symbol"])
            chg  = s.get("change_pct") or 0
            return (f'<div class="sotw-row">'
                    f'<span class="sotw-sym">{sym}</span>'
                    f'<span class="sotw-price">{pr}</span>'
                    f'<span class="{_chg_cls(chg)} sotw-chg">{_chg_str(chg)}</span>'
                    f'{extra}</div>')

        def _signal_badge(s):
            pred = s.get("prediction", "")
            conf = s.get("prediction_confidence", 0) or 0
            color = "up" if pred in ("BULLISH", "UP") else ("down" if pred in ("BEARISH", "DOWN") else "sotw-rsi")
            label = pred.title() if pred else "—"
            return f'<span class="{color} sotw-conf">{label} {conf*100:.0f}%</span>'

        bullish_rows = "".join(
            _sotw_row(s, _signal_badge(s))
            for s in sotw_bullish
        ) or f'<p class="sotw-empty">No signals yet — refresh in progress</p>'

        movers_rows = "".join(_sotw_row(s) for s in sotw_movers) or f'<p class="sotw-empty">No data yet</p>'

        _extremes = [
            *[_sotw_row(s, f'<span class="sotw-rsi up">RSI {s["rsi"]:.0f} ▲ oversold</span>') for s in sotw_oversold],
            *[_sotw_row(s, f'<span class="sotw-rsi down">RSI {s["rsi"]:.0f} ▼ overbought</span>') for s in sotw_overbought],
            *[_sotw_row(s, f'<span class="sotw-vol">Vol {s["volume"]/s["avg_volume"]:.1f}x avg</span>') for s in sotw_volume],
        ]
        extremes_rows = "".join(_extremes) or f'<p class="sotw-empty">No extremes detected</p>'

        # penny stocks html rows
        def _penny_row(s, extra=""):
            sym = sec_mod.display_symbol(s["symbol"])
            pr  = _fmt_price(s.get("price"), s["symbol"])
            chg = s.get("change_pct") or 0
            return (f'<div class="sotw-row penny-row">'
                    f'<span class="sotw-sym">{sym}</span>'
                    f'<span class="sotw-price">${pr}</span>'
                    f'<span class="{_chg_cls(chg)} sotw-chg">{_chg_str(chg)}</span>'
                    f'{extra}</div>')

        penny_rising_rows   = "".join(
            _penny_row(s, _signal_badge(s)) for s in penny_rising
        ) or '<p class="sotw-empty">No rising penny stocks right now</p>'
        penny_oversold_rows = "".join(
            _penny_row(s, f'<span class="sotw-rsi up">RSI {s["rsi"]:.0f}</span>') for s in penny_oversold
        ) or '<p class="sotw-empty">No oversold penny stocks</p>'
        penny_volume_rows   = "".join(
            _penny_row(s, f'<span class="sotw-vol">Vol {(s["volume"]/max(s["avg_volume"],1)):.1f}x</span>') for s in penny_volume
        ) or '<p class="sotw-empty">No volume spikes in penny stocks</p>'

        # earnings html
        def _days_cls(d):
            if d <= 3: return "soon"
            if d <= 7: return "week"
            return "future"

        def _reaction_span(e):
            r = e.get("avg_reaction_pct")
            if not r:
                return ""
            sign = "+" if r >= 0 else ""
            return f'<span class="earnings-reaction">avg {sign}{r:.1f}% move</span>'

        earnings_rows = "".join(
            '<div class="earnings-row">'
            + f'<span class="earnings-sym">{e["symbol"]}</span>'
            + f'<span class="earnings-date">{e["earnings_date"]}</span>'
            + _reaction_span(e)
            + f'<span class="earnings-days {_days_cls(e["days_until"])}">{e["days_until"]}d</span>'
            + '</div>'
            for e in upcoming_earnings_all[:7]
        ) or '<p class="sotw-empty">No upcoming earnings found</p>'

        # key levels html
        ma_rows = "".join(
            f'<div class="sotw-row">'
            f'<span class="sotw-sym">{sec_mod.display_symbol(s["symbol"])}</span>'
            f'<span class="sotw-price">{_fmt_price(s.get("price"), s["symbol"])}</span>'
            f'<span class="sotw-sub">near MA50 ${s["ma50"]:.2f}</span>'
            f'</div>'
            for s in sotw_near_ma
        ) or '<p class="sotw-empty">No stocks at key levels</p>'

        # overbought levels panel (pre-computed to avoid nested f-string issues)
        _ob_extra = ""
        if sotw_overbought:
            _ob_rows = "".join(
                '<div class="sotw-row">'
                + f'<span class="sotw-sym">{sec_mod.display_symbol(s["symbol"])}</span>'
                + f'<span class="sotw-price">{_fmt_price(s.get("price"), s["symbol"])}</span>'
                + f'<span class="sotw-rsi down">RSI {s["rsi"]:.0f} — extended</span>'
                + '</div>'
                for s in sotw_overbought[:2]
            )
            _ob_extra = (
                "<div style='margin-top:14px;padding-top:10px;"
                "border-top:1px solid rgba(255,255,255,.06)'>" + _ob_rows + "</div>"
            )

        # macro events html
        event_rows = "".join(
            f'<div class="event-row">'
            f'<div><div class="event-name">{e["name"]}</div>'
            f'<div class="event-detail">{e["detail"]}</div></div>'
            f'<span class="event-impact impact-{e["impact"]}">{e["impact"].upper()}</span>'
            f'</div>'
            for e in _market_events
        )

        # -- watchlist table
        wl_grouped: dict[str, list] = {}
        for sym in watchlist:
            s = all_db.get(sym)
            if not s or s.get("price") is None:
                continue
            sect = sec_mod.resolve_sector(sym, stock_sectors)
            wl_grouped.setdefault(sect, []).append(s)

        wl_rows = ""
        for sect in sorted(wl_grouped.keys(), key=_skey):
            color  = _sector_css(sect)
            syms_in_sect = sorted(wl_grouped[sect], key=lambda x: x["symbol"])
            sect_id = "".join(c if c.isalnum() else "_" for c in sect)

            wl_rows += (
                f'<tr class="wl-sect-row" data-sid="{sect_id}">'
                f'<td colspan="8"><div class="wl-sect-toggle">'
                f'<span style="color:{color}">{sect}</span>'
                f'<span class="wl-sect-count">({len(syms_in_sect)})</span>'
                f'<span class="wl-sect-chev">&#x25BE;</span>'
                f'</div></td></tr>'
            )
            for i, s in enumerate(syms_in_sect):
                sym   = s["symbol"]
                disp  = sec_mod.display_symbol(sym)
                price = s.get("price") or 0
                chg   = s.get("change_pct") or 0
                vol   = s.get("volume") or 0
                rsi   = s.get("rsi")
                ma50  = s.get("ma50")
                pred  = s.get("prediction") or "NEUTRAL"
                conf  = (s.get("prediction_confidence") or 0) * 100

                chg_cls = "up" if chg >= 0 else "down"
                chg_str = f"+{chg:.2f}%" if chg >= 0 else f"{chg:.2f}%"

                if vol >= 1_000_000:
                    vol_str = f"{vol/1_000_000:.1f}M"
                elif vol >= 1_000:
                    vol_str = f"{vol/1_000:.0f}K"
                else:
                    vol_str = str(vol) if vol else "—"

                rsi_str = f"{rsi:.0f}" if rsi else "—"
                rsi_cls = "down" if (rsi and rsi >= 70) else ("up" if (rsi and rsi <= 30) else "wl-na")

                if price and ma50:
                    vs_pct = (price - ma50) / ma50 * 100
                    vs_str = f"{vs_pct:+.1f}%"
                    vs_cls = "up" if vs_pct >= 0 else "down"
                else:
                    vs_str, vs_cls = "—", "wl-na"

                if pred in ("BULLISH", "UP"):
                    sig_cls, sig_label = "wl-bull", "Bullish"
                elif pred in ("BEARISH", "DOWN"):
                    sig_cls, sig_label = "wl-bear", "Bearish"
                else:
                    sig_cls, sig_label = "wl-neut", "Neutral"

                last_row = "wl-last" if i == len(syms_in_sect) - 1 else ""

                wl_rows += (
                    f'<tr class="wl-row wl-hidden {last_row}" data-sid="{sect_id}" '
                    f'data-sym="{sym.lower()}" data-sect="{sect.lower()}">'
                    f'<td class="wl-sym">{disp}</td>'
                    f'<td class="wl-price">{_fmt_price(price, sym)}</td>'
                    f'<td class="wl-chg {chg_cls}">{chg_str}</td>'
                    f'<td class="wl-vol">{vol_str}</td>'
                    f'<td class="wl-rsi {rsi_cls}">{rsi_str}</td>'
                    f'<td class="wl-vs {vs_cls}">{vs_str}</td>'
                    f'<td class="wl-sig"><span class="wl-badge {sig_cls}">{sig_label}</span></td>'
                    f'<td class="wl-conf">{conf:.0f}%</td>'
                    f'</tr>'
                )

        n_tracked = sum(len(v) for v in wl_grouped.values())
        from datetime import datetime as _wl_dt
        wl_last_refresh = "Updated " + _wl_dt.now().strftime("%H:%M UTC")
        if not wl_rows:
            wl_rows = '<tr><td colspan="8" style="text-align:center;padding:24px;color:rgba(255,255,255,.28);font-style:italic">Fetching live data — check back in a moment</td></tr>'

        # -- options intelligence section
        opt_recs = db.get_option_recs(40)
        call_recs = [r for r in opt_recs if r.get("opt_type") == "CALL"]
        put_recs  = [r for r in opt_recs if r.get("opt_type") == "PUT"]

        def _opt_rows(recs: list[dict], opt_type: str) -> str:
            if not recs:
                return f'<tr><td colspan="9" class="opt-empty">No {opt_type} recommendations yet — data refreshes every 5 minutes</td></tr>'
            rows = ""
            for r in recs:
                sym    = r.get("symbol", "")
                strike = r.get("strike") or 0
                expiry = r.get("expiry", "")[:10]
                days   = r.get("days_out") or 0
                bid    = r.get("bid") or 0
                ask    = r.get("ask") or 0
                last   = r.get("last_price") or 0
                iv_pct = (r.get("iv") or 0) * 100
                oi     = r.get("open_interest") or 0
                vol    = r.get("volume") or 0
                sc     = r.get("score") or 0
                reason = r.get("reason", "")
                cprice = r.get("current_price") or 0

                badge = (f'<span class="opt-badge-call">CALL</span>'
                         if opt_type == "CALL"
                         else f'<span class="opt-badge-put">PUT</span>')
                sc_cls = ("opt-score-hi" if sc >= 60
                          else "opt-score-mid" if sc >= 40
                          else "opt-score-lo")
                oi_str  = f"{oi:,}"
                vol_str = f"{vol:,}" if vol else "—"
                bid_ask = f"${bid:.2f} / ${ask:.2f}" if bid or ask else "—"
                last_str= f"${last:.2f}" if last else "—"
                days_str= f"{days}d" if days else "—"

                chart_url = (
                    f"/option-chart.png?t={opt_type}"
                    f"&k={strike}&p={cprice}&b={bid}&a={ask}"
                )
                rows += (
                    f'<tr>'
                    f'<td class="opt-sym">{sec_mod.display_symbol(sym)}</td>'
                    f'<td style="text-align:right">{badge}</td>'
                    f'<td style="text-align:right">${cprice:.2f}</td>'
                    f'<td style="text-align:right">${strike:.2f}</td>'
                    f'<td style="text-align:right">{expiry} <span style="color:rgba(255,255,255,.35)">({days_str})</span></td>'
                    f'<td style="text-align:right">{last_str}</td>'
                    f'<td style="text-align:right">{bid_ask}</td>'
                    f'<td style="text-align:right">{iv_pct:.0f}%</td>'
                    f'<td style="text-align:right">{oi_str}</td>'
                    f'<td style="text-align:right">{vol_str}</td>'
                    f'<td style="text-align:right"><span class="opt-score {sc_cls}">{sc:.0f}</span></td>'
                    f'<td class="opt-reason">{reason}</td>'
                    f'</tr>'
                    f'<tr style="background:rgba(0,0,0,.25)">'
                    f'<td colspan="12" style="padding:8px 14px 12px">'
                    f'<img src="{chart_url}" alt="Payoff chart" '
                    f'style="display:block;border-radius:6px;max-width:572px;height:auto"/>'
                    f'</td></tr>'
                )
            return rows

        col_heads = (
            '<th>Symbol</th>'
            '<th style="text-align:right">Type</th>'
            '<th style="text-align:right">Stock&nbsp;Price</th>'
            '<th style="text-align:right">Strike</th>'
            '<th style="text-align:right">Expiry</th>'
            '<th style="text-align:right">Last</th>'
            '<th style="text-align:right">Bid&nbsp;/&nbsp;Ask</th>'
            '<th style="text-align:right">IV</th>'
            '<th style="text-align:right">OI</th>'
            '<th style="text-align:right">Vol</th>'
            '<th style="text-align:right">Score</th>'
            '<th>Signal Reason</th>'
        )

        options_section_html = f"""
  <div class="opt-section" id="options">
    <div class="section-head" style="margin-bottom:16px">
      <h2>&#x1F4CA; Options Intelligence</h2>
      <span style="font-size:12px;color:rgba(255,255,255,.35)">
        Real-time call &amp; put recommendations &bull; refreshes every 5 min
      </span>
    </div>
    <div class="opt-tabs">
      <div class="opt-tab active-call" id="optTabCall" onclick="optSwitch('call')">
        &#x1F4C8; CALLS &mdash; {len(call_recs)} recommendations
      </div>
      <div class="opt-tab" id="optTabPut" onclick="optSwitch('put')">
        &#x1F4C9; PUTS &mdash; {len(put_recs)} recommendations
      </div>
    </div>
    <div class="opt-panel active" id="optPanelCall">
      <div class="opt-wrap">
        <table class="opt-table">
          <thead><tr>{col_heads}</tr></thead>
          <tbody>{_opt_rows(call_recs, "CALL")}</tbody>
        </table>
      </div>
    </div>
    <div class="opt-panel" id="optPanelPut">
      <div class="opt-wrap">
        <table class="opt-table">
          <thead><tr>{col_heads}</tr></thead>
          <tbody>{_opt_rows(put_recs, "PUT")}</tbody>
        </table>
      </div>
    </div>
    <p class="opt-disclaimer">
      &#x26A0;&#xFE0F; Options carry significant risk and can expire worthless.
      Score = liquidity + placement quality (0-100). Not financial advice. Do your own research.
    </p>
  </div>
"""

        # -- knowledge base preview (4 random-ish topics)
        preview_keys = ["rsi", "macd", "patterns_golden_cross", "risk_position_sizing"]
        topic_cards = ""
        for key in preview_keys:
            t = kb_mod.get_topic(key)
            if not t:
                continue
            cat   = t.get("category", "Concepts")
            color = _CAT_COLORS.get(cat, "#64748b")
            short = t["summary"][:90] + "..." if len(t["summary"]) > 90 else t["summary"]
            topic_cards += f"""
            <a href="/learn/{key}" style="text-decoration:none">
              <div class="topic-card">
                <div class="topic-cat" style="color:{color}">{cat}</div>
                <h4>{t['title']}</h4>
                <p>{short}</p>
              </div>
            </a>"""

        # -- social share buttons
        sub_url     = f"{_base_url()}"
        share_text  = f"Get free AI-powered stock + crypto alerts for {', '.join('$'+sec_mod.display_symbol(s) for s in watchlist[:5])} and more."
        tw_url = social_mod.twitter_intent_url(share_text, sub_url)
        li_url = social_mod.linkedin_share_url(sub_url, "Stock Tracker Alerts")
        fb_url = social_mod.facebook_share_url(sub_url)

        html = _base_html(
            "Stock Tracker Alerts",
            f"""
<nav class="nav">
  <div class="nav-logo"><span>&#x1F4C8;</span> Stock Tracker</div>
  <div class="nav-links">
    <a href="#watchlist">&#x1F4CA; Live Prices</a>
    <a href="#options">&#x1F4C8; Options</a>
    <a href="/learn">Knowledge Base</a>
    <a href="#subscribe" class="nav-cta">Get Alerts</a>
  </div>
</nav>

<!-- HERO -->
<div class="hero">
  <div class="hero-orb orb-1"></div>
  <div class="hero-orb orb-2"></div>
  <div class="hero-orb orb-3"></div>
  <div class="hero-orb orb-4"></div>
  <div class="hero-inner">
    <div class="hero-badge">&#x1F680; Now tracking Crypto &amp; Penny Stocks</div>
    <h1>Smarter alerts,<br><span class="accent">before the market moves</span></h1>
    <p class="hero-sub">
      AI-powered signals for stocks, crypto, and high-potential small caps &mdash;
      delivered free by <strong style="color:#fff">email</strong> and <strong style="color:#fff">SMS</strong>.
    </p>
    <a href="#subscribe" class="hero-cta">Get Free Alerts &darr;</a>
  </div>
  <div class="ticker-wrap">
    <div class="ticker-track">{ticker}</div>
  </div>
</div>

<!-- STATS -->
<div class="stats">
  <a href="#subscribe" class="stat"><div class="stat-num">{n_stocks}</div><div class="stat-label">Stocks &amp; Cryptos</div></a>
  <a href="#subscribe" class="stat"><div class="stat-num">{n_sectors}</div><div class="stat-label">Sectors</div></a>
  <div class="stat"><div class="stat-num">{n_subs}</div><div class="stat-label">Subscribers</div></div>
  <div class="stat"><div class="stat-num">{n_alerts}</div><div class="stat-label">Alerts Sent</div></div>
  <a href="/learn" class="stat"><div class="stat-num">{n_topics}</div><div class="stat-label">Learn Topics</div></a>
</div>

<!-- MAIN -->
<div class="main">

  <!-- SUBSCRIBE CARD -->
  <div class="subscribe-card" id="subscribe">
    <h2>&#x1F514; Start receiving alerts</h2>
    <p class="subtitle">Enter your email, phone, or both &mdash; alerts will be sent to whichever you provide.</p>

    <form method="POST" action="/subscribe" id="sub-form">
      <div class="form-row">
        <div class="field">
          <label>Email address <span class="optional" id="email-opt-label">(optional if you enter a phone)</span></label>
          <input type="email" name="email" id="sub-email" placeholder="you@example.com" autocomplete="email">
        </div>
        <div>
          <div class="field">
            <label>Phone number <span class="optional" id="phone-opt-label">(optional if you enter an email)</span></label>
            <div class="phone-row">
              <input type="tel" name="phone_number" id="sub-phone" placeholder="+1 555 123 4567" autocomplete="tel">
              {'<div>' + carrier_select + '</div>' if carrier_select else ''}
            </div>
          </div>
          {'<p class="sms-note">&#x2139;&#xFE0F; No Twilio configured &mdash; select your carrier to receive SMS via email gateway.</p>' if not twilio_on else '<p class="sms-note">&#x2705; Twilio configured &mdash; enter any number to receive SMS alerts.</p>'}
        </div>
      </div>
      <script>
      (function(){{
        var form  = document.getElementById('sub-form');
        var email = document.getElementById('sub-email');
        var phone = document.getElementById('sub-phone');
        var eOpt  = document.getElementById('email-opt-label');
        var pOpt  = document.getElementById('phone-opt-label');
        function update(){{
          var hasEmail = email.value.trim() !== '';
          var hasPhone = phone.value.trim() !== '';
          email.required = !hasPhone;
          phone.required = !hasEmail;
          eOpt.style.display = hasPhone ? 'inline' : 'none';
          pOpt.style.display = hasEmail ? 'inline' : 'none';
        }}
        email.addEventListener('input', update);
        phone.addEventListener('input', update);
        update();
      }})();
      </script>

      <div class="stock-picker">
        <div class="stock-picker-label">&#x2713; Stocks &amp; cryptos to track (all pre-selected)</div>
        {sector_html}
        <label class="all-stocks">
          <input type="checkbox" name="stocks" value="__ALL__">
          &nbsp; All current &amp; future additions
        </label>
      </div>

      <button type="submit" class="btn-submit">&#x1F680; Subscribe Free</button>
      <p class="privacy-note">
        &#x1F512; No spam, ever. Unsubscribe instantly via one link.
        <a href="/learn">Learn what the signals mean &rarr;</a>
      </p>
    </form>
  </div>

  <!-- FEATURES -->
  <div class="features">
    <div class="feature-card">
      <div class="feature-icon">&#x1F916;</div>
      <h3>AI Predictions</h3>
      <p>Random Forest ML blended with rule-based signals (RSI, MACD, Bollinger Bands, volume). Confidence-scored and updated every 5 minutes.</p>
    </div>
    <div class="feature-card">
      <div class="feature-icon">&#x26A1;</div>
      <h3>Instant Alerts</h3>
      <p>Price surges, RSI extremes, earnings in 3 days, volume spikes, and high-confidence ML signals — email and SMS the moment they fire.</p>
    </div>
    <div class="feature-card">
      <div class="feature-icon">&#x1F4DA;</div>
      <h3>Learn Investing</h3>
      <p>{n_topics} plain-English guides on indicators, patterns, sectors, risk management, options Greeks, trading platforms, and more.</p>
    </div>
  </div>

  <!-- STOCKS OF THE WEEK -->
  <div class="sotw-section">
    <div class="section-head" style="margin-bottom:16px">
      <h2>&#x1F525; Stocks of the Week</h2>
      <span style="font-size:12px;color:rgba(255,255,255,.35)">Updated with every data refresh</span>
    </div>
    <div class="sotw-grid">
      <div class="sotw-card">
        <div class="sotw-head">&#x1F916; AI Top Signals</div>
        {bullish_rows}
      </div>
      <div class="sotw-card">
        <div class="sotw-head">&#x26A1; Today's Top Movers</div>
        {movers_rows}
      </div>
      <div class="sotw-card">
        <div class="sotw-head">&#x1F4CA; Technical Extremes</div>
        {extremes_rows}
      </div>
    </div>
  </div>

  <!-- PENNY STOCKS WITH POTENTIAL -->
  <div class="sotw-section">
    <div class="section-head" style="margin-bottom:16px">
      <h2>&#x1F4B0; Penny Stocks with Potential</h2>
      <span style="font-size:12px;color:rgba(255,255,255,.35)">Price &lt; $10 &mdash; ranked by signal + RSI + volume</span>
    </div>
    <div class="sotw-grid">
      <div class="sotw-card">
        <div class="sotw-head">&#x1F4C8; Rising &amp; Bullish</div>
        {penny_rising_rows}
      </div>
      <div class="sotw-card">
        <div class="sotw-head">&#x1F7E2; Oversold (RSI &lt; 45)</div>
        {penny_oversold_rows}
      </div>
      <div class="sotw-card">
        <div class="sotw-head">&#x26A1; Volume Spikes</div>
        {penny_volume_rows}
      </div>
    </div>
  </div>

  <!-- WHAT TO WATCH THIS WEEK -->
  <div class="watchout-section">
    <div class="section-head" style="margin-bottom:16px">
      <h2>&#x1F4C5; What to Watch This Week</h2>
      <span style="font-size:12px;color:rgba(255,255,255,.35)">Earnings, levels &amp; macro events</span>
    </div>
    <div class="watchout-grid">
      <div class="watchout-card">
        <div class="watchout-head">&#x1F4B0; Upcoming Earnings</div>
        {earnings_rows}
      </div>
      <div class="watchout-card">
        <div class="watchout-head">&#x1F3AF; Key Technical Levels</div>
        {ma_rows}
        {_ob_extra}
      </div>
      <div class="watchout-card">
        <div class="watchout-head">&#x1F3DB; Market Events</div>
        {event_rows}
      </div>
    </div>
  </div>

  <!-- WATCHLIST TABLE -->
  <div class="wl-section" id="watchlist">
    <div class="section-head" style="margin-bottom:16px">
      <h2>&#x1F4CA; Live Watchlist</h2>
      <span style="font-size:12px;color:rgba(255,255,255,.35)">{n_tracked} stocks tracked &bull; refreshes every 5 min</span>
    </div>
    <div class="wl-controls">
      <input type="search" class="wl-search" id="wlSearch" placeholder="&#x1F50D; Filter symbol or sector&hellip;" autocomplete="off">
      <button class="wl-btn" id="wlExpandAll">Expand All</button>
      <button class="wl-btn" id="wlCollapseAll">Collapse All</button>
      <span class="wl-ts">{wl_last_refresh}</span>
    </div>
    <div class="wl-wrap">
      <table class="wl-table" id="wlTable">
        <thead>
          <tr>
            <th>Symbol</th>
            <th style="text-align:right">Price</th>
            <th style="text-align:right">Chg&nbsp;%</th>
            <th style="text-align:right">Volume</th>
            <th style="text-align:right">RSI</th>
            <th style="text-align:right">vs&nbsp;MA50</th>
            <th style="text-align:right">Signal</th>
            <th style="text-align:right">Conf</th>
          </tr>
        </thead>
        <tbody id="wlBody">
          {wl_rows}
        </tbody>
      </table>
    </div>
  </div>

  <!-- OPTIONS INTELLIGENCE -->
  {options_section_html}

  <!-- KNOWLEDGE PREVIEW -->
  <div class="section-head">
    <h2>&#x1F4DA; Start learning</h2>
    <a href="/learn" class="see-all">See all {n_topics} topics &rarr;</a>
  </div>
  <div class="topics-grid">
    {topic_cards}
  </div>

  <!-- SOCIAL SHARE -->
  <div class="share-section">
    <h2>&#x1F91D; Spread the word</h2>
    <p>Know someone who tracks stocks? Share this page and help them get free alerts.</p>
    <div class="share-buttons">
      <a href="{tw_url}" target="_blank" rel="noopener" class="share-btn share-twitter">
        &#x1D54F; Share on X / Twitter
      </a>
      <a href="{li_url}" target="_blank" rel="noopener" class="share-btn share-linkedin">
        in&nbsp; Share on LinkedIn
      </a>
      <a href="{fb_url}" target="_blank" rel="noopener" class="share-btn share-facebook">
        f&nbsp; Share on Facebook
      </a>
    </div>
  </div>

</div>

<footer class="footer">
  &#x1F4C8; Stock Tracker &bull;
  <a href="/learn">Knowledge Base</a> &bull;
  <a href="/unsubscribe">Unsubscribe</a> &bull;
  <a href="/learn/risk_diversification">Risk Disclaimer</a>
  &bull; Data via Yahoo Finance. Not financial advice.
</footer>

<script>
(function(){{
  // Subscribe form: sector collapse/expand toggle
  document.querySelectorAll('.sector-toggle').forEach(function(toggle){{
    toggle.addEventListener('click', function(){{
      var group = toggle.closest('.sector-group');
      group.classList.toggle('open');
    }});
  }});

  // ── Watchlist table ──────────────────────────────────────────────────
  function wlToggleSect(sectRow){{
    var sid  = sectRow.dataset.sid;
    var open = sectRow.classList.toggle('wl-open');
    document.querySelectorAll('.wl-row[data-sid="' + sid + '"]').forEach(function(r){{
      r.classList.toggle('wl-hidden', !open);
    }});
  }}

  // Click on sector header rows
  document.querySelectorAll('.wl-sect-row').forEach(function(row){{
    row.addEventListener('click', function(){{ wlToggleSect(row); }});
  }});

  // Expand All
  var wlExpBtn = document.getElementById('wlExpandAll');
  if(wlExpBtn) wlExpBtn.addEventListener('click', function(){{
    document.querySelectorAll('.wl-sect-row').forEach(function(r){{
      if(!r.classList.contains('wl-open')) wlToggleSect(r);
    }});
  }});

  // Collapse All
  var wlColBtn = document.getElementById('wlCollapseAll');
  if(wlColBtn) wlColBtn.addEventListener('click', function(){{
    document.querySelectorAll('.wl-sect-row').forEach(function(r){{
      if(r.classList.contains('wl-open')) wlToggleSect(r);
    }});
  }});

  // Search / filter
  var wlSearch = document.getElementById('wlSearch');
  if(wlSearch) wlSearch.addEventListener('input', function(){{
    var q = this.value.toLowerCase().trim();
    var sidsSeen = {{}};
    // Filter data rows
    document.querySelectorAll('.wl-row').forEach(function(r){{
      var sym  = (r.dataset.sym  || '').toLowerCase();
      var sect = (r.dataset.sect || '').toLowerCase();
      var match = !q || sym.includes(q) || sect.includes(q);
      r.style.display = match ? '' : 'none';
      if(match){{
        var sid = r.dataset.sid;
        sidsSeen[sid] = true;
      }}
    }});
    // Show/hide sector headers based on whether any rows match
    document.querySelectorAll('.wl-sect-row').forEach(function(r){{
      var sid = r.dataset.sid;
      if(q){{
        if(sidsSeen[sid]){{
          r.style.display = '';
          // Auto-expand matched sectors
          if(!r.classList.contains('wl-open')){{
            r.classList.add('wl-open');
          }}
          // Show matched rows
          document.querySelectorAll('.wl-row[data-sid="' + sid + '"]').forEach(function(dr){{
            if(dr.style.display !== 'none') dr.classList.remove('wl-hidden');
          }});
        }} else {{
          r.style.display = 'none';
        }}
      }} else {{
        r.style.display = '';
        // Restore hidden state for non-open sectors
        if(!r.classList.contains('wl-open')){{
          document.querySelectorAll('.wl-row[data-sid="' + sid + '"]').forEach(function(dr){{
            dr.classList.add('wl-hidden');
            dr.style.display = '';
          }});
        }}
      }}
    }});
  }});
}})();

}})();

// ── Options Intelligence tab switcher (global scope) ─────────────────────
window.optSwitch = function(tab) {{
  document.getElementById('optPanelCall').classList.toggle('active', tab === 'call');
  document.getElementById('optPanelPut').classList.toggle('active',  tab === 'put');
  var tc = document.getElementById('optTabCall');
  var tp = document.getElementById('optTabPut');
  if(tc) {{ tc.className = 'opt-tab' + (tab==='call' ? ' active-call' : ''); }}
  if(tp) {{ tp.className = 'opt-tab' + (tab==='put'  ? ' active-put'  : ''); }}
}};
</script>
"""
        )
        return Response(html, mimetype="text/html")

    # ── subscribe ─────────────────────────────────────────────────────────────

    @_app.route("/subscribe", methods=["POST"])
    def subscribe():
        import re as _re
        email   = (request.form.get("email") or "").strip().lower()
        phone   = (request.form.get("phone_number") or "").strip()
        carrier = (request.form.get("carrier") or "").strip()

        valid_email = bool(email and "@" in email and "." in email.split("@")[-1])
        valid_phone = bool(phone and _re.sub(r"\D", "", phone))

        if not valid_email and not valid_phone:
            return _simple_error("Please enter an email address, a phone number, or both.")

        # Phone-only subscribers get a synthetic placeholder so the DB UNIQUE
        # constraint is satisfied without sending them unwanted email.
        clean_phone = _re.sub(r"\D", "", phone)
        if not valid_email:
            email = f"sms+{clean_phone}@noemail.invalid"

        selected  = request.form.getlist("stocks")
        watchlist = _watchlist()
        if "__ALL__" in selected or not selected:
            stocks = []
        else:
            stocks = [s for s in selected if s in watchlist]

        token     = db.add_subscriber(email, stocks, phone_number=phone, carrier=carrier)
        unsub     = f"{_base_url()}/unsubscribe?token={token}"
        stock_str = ", ".join(sec_mod.display_symbol(s) for s in stocks) if stocks else "all stocks"

        # Build channel confirmation lines
        sms_only = email.endswith("@noemail.invalid")
        if sms_only:
            contact_line = f"<p>&#x1F4F1; SMS alerts will be sent to <strong>{phone}</strong>.</p>"
        elif phone:
            contact_line = (f"<p>&#x2709;&#xFE0F; Email alerts → <strong>{email}</strong></p>"
                            f"<p>&#x1F4F1; SMS alerts → <strong>{phone}</strong></p>")
        else:
            contact_line = f"<p>&#x2709;&#xFE0F; Email alerts will be sent to <strong>{email}</strong>.</p>"

        config  = cfg_mod.load_config()
        pub_url = config.get("social", {}).get("public_url", _base_url())
        tw_url  = social_mod.twitter_intent_url(
            f"Just subscribed to free AI stock alerts! Check it out:", pub_url)

        html = _base_html("Subscribed!", f"""
<div style="max-width:540px;margin:60px auto;padding:0 20px">
  <div class="page-card">
    <div class="icon">&#x2705;</div>
    <h2 style="color:#16a34a">You&rsquo;re subscribed!</h2>
    {contact_line}
    <p style="margin-top:8px">Tracking: <strong>{stock_str}</strong></p>
    <p style="margin-top:16px;font-size:13px;color:var(--muted)">
      Unsubscribe anytime:<br>
      <a href="{unsub}" style="word-break:break-all;font-size:12px">{unsub}</a>
    </p>
    <div style="margin-top:24px;display:flex;gap:12px;justify-content:center;flex-wrap:wrap">
      <a href="/" class="btn-back">&#x2190; Back</a>
      <a href="{tw_url}" target="_blank" class="btn-back" style="background:#000">
        &#x1D54F; Share on X
      </a>
      <a href="/learn" class="btn-back" style="background:var(--warn);color:#fff">
        &#x1F4DA; Start Learning
      </a>
    </div>
  </div>
</div>
<footer class="footer">&#x1F4C8; Stock Tracker &bull; <a href="/">Home</a></footer>
""")
        return Response(html, mimetype="text/html")

    # ── unsubscribe ───────────────────────────────────────────────────────────

    @_app.route("/unsubscribe", methods=["GET", "POST"])
    def unsubscribe():
        token = request.args.get("token") or request.form.get("token") or ""

        if request.method == "POST" and token:
            ok = db.remove_subscriber(token)
            if ok:
                html = _base_html("Unsubscribed", f"""
<div style="max-width:540px;margin:60px auto;padding:0 20px">
  <div class="page-card">
    <div class="icon">&#x1F44B;</div>
    <h2 style="color:var(--muted)">You&rsquo;ve been unsubscribed</h2>
    <p>You won&rsquo;t receive any more alerts.</p>
    <a href="/" class="btn-back">Subscribe again</a>
  </div>
</div>
<footer class="footer">&#x1F4C8; Stock Tracker &bull; <a href="/">Home</a></footer>
""")
                return Response(html, mimetype="text/html")
            return _simple_error("Invalid or expired unsubscribe link.")

        hidden      = f'<input type="hidden" name="token" value="{token}">' if token else ""
        token_field = "" if token else """
            <div class="field">
              <label>Your unsubscribe token <span class="optional">(from your alert email)</span></label>
              <input type="text" name="token" required placeholder="paste token here">
            </div>"""

        sub_info = ""
        if token:
            sub = db.get_subscriber_by_token(token)
            if sub:
                stocks = ", ".join(sec_mod.display_symbol(s) for s in sub["stocks"]) if sub["stocks"] else "all stocks"
                sub_info = f'<p style="color:var(--muted);margin-bottom:16px">Unsubscribing <strong>{sub["email"]}</strong> from <strong>{stocks}</strong>.</p>'

        html = _base_html("Unsubscribe", f"""
<div style="max-width:520px;margin:60px auto;padding:0 20px">
  <div class="page-card" style="text-align:left">
    <h2 style="margin-bottom:20px">Unsubscribe</h2>
    {sub_info}
    <form method="POST" action="/unsubscribe">
      {hidden}
      {token_field}
      <button type="submit" class="btn-submit btn-danger" style="margin-top:16px">
        Confirm Unsubscribe
      </button>
    </form>
    <p style="margin-top:16px;text-align:center">
      <a href="/" style="font-size:14px;color:var(--muted)">&larr; Back to signup</a>
    </p>
  </div>
</div>
<footer class="footer">&#x1F4C8; Stock Tracker &bull; <a href="/">Home</a></footer>
""")
        return Response(html, mimetype="text/html")

    # ── knowledge base index ──────────────────────────────────────────────────

    @_app.route("/learn")
    def learn_index():
        by_cat   = kb_mod.list_by_category()
        sections = ""

        for cat in kb_mod.CATEGORIES:
            entries = by_cat.get(cat, [])
            color   = _CAT_COLORS.get(cat, "#64748b")
            cards   = ""
            for key, title in entries:
                topic = kb_mod.KNOWLEDGE_BASE[key]
                short = topic["summary"][:100] + "..." if len(topic["summary"]) > 100 else topic["summary"]
                cards += f"""
                <a href="/learn/{key}" style="text-decoration:none">
                  <div class="topic-card">
                    <div style="font-weight:700;font-size:15px;color:var(--text);margin-bottom:6px">{title}</div>
                    <div style="font-size:13px;color:var(--muted);line-height:1.5">{short}</div>
                  </div>
                </a>"""
            sections += f"""
            <div style="margin-bottom:36px">
              <h3 style="font-size:16px;font-weight:700;color:{color};margin-bottom:14px;
                         display:flex;align-items:center;gap:8px">
                <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:{color}"></span>
                {cat}
              </h3>
              <div class="learn-topics-grid">{cards}</div>
            </div>"""

        body = f"""
        <div class="learn-card">
          <div class="learn-breadcrumb">
            <a href="/">&#x1F514; Alerts</a> &rsaquo; Knowledge Base
          </div>
          <h2>&#x1F4DA; Trading Knowledge Base</h2>
          <p style="color:var(--muted);margin:8px 0 28px;font-size:15px">
            Practical guides for new traders. Learn what the indicators in this app mean,
            how to manage risk, and what drives each sector.
          </p>
          {sections}
        </div>"""
        return Response(_learn_base("Knowledge Base", body), mimetype="text/html")

    @_app.route("/learn/<topic_key>")
    def learn_topic(topic_key):
        topic = kb_mod.get_topic(topic_key)
        if not topic:
            results = kb_mod.search(topic_key)
            suggestions = "".join(
                f'<li><a href="/learn/{k}">{t}</a></li>'
                for k, t in (results or [])[:5]
            )
            body = f"""
            <div class="learn-card">
              <div class="learn-breadcrumb"><a href="/learn">Knowledge Base</a></div>
              <h2>Topic not found: {topic_key}</h2>
              {"<ul style='margin-top:12px'>" + suggestions + "</ul>" if suggestions else ""}
              <a href="/learn" class="btn-back" style="display:inline-block;margin-top:20px">Browse all topics</a>
            </div>"""
            return Response(_learn_base("Not found", body), status=404, mimetype="text/html")

        cat      = topic.get("category", "Concepts")
        cat_color = _CAT_COLORS.get(cat, "#64748b")

        sections_html = ""
        for sec in topic["sections"]:
            lines = sec["content"].replace("\n  ", "<br>&nbsp;&nbsp;").replace("\n", "<br>")
            sections_html += f"""
            <div class="learn-section" style="margin-bottom:22px">
              <h3>{sec['heading']}</h3>
              <p>{lines}</p>
            </div>"""

        tips_html = ""
        if topic.get("quick_tips"):
            items = "".join(f'<li style="margin-bottom:6px">{t}</li>' for t in topic["quick_tips"])
            tips_html = f"""
            <div class="tips-box">
              <div class="tips-head">&#x2713; Quick Tips</div>
              <ul>{items}</ul>
            </div>"""

        related_html = ""
        if topic.get("related"):
            links = " &bull; ".join(
                f'<a href="/learn/{r}">'
                f'{kb_mod.KNOWLEDGE_BASE[r]["title"] if r in kb_mod.KNOWLEDGE_BASE else r}</a>'
                for r in topic["related"]
            )
            related_html = f'<p style="font-size:13px;color:var(--muted);margin-top:24px">Related: {links}</p>'

        body = f"""
        <div class="learn-card">
          <div class="learn-breadcrumb">
            <a href="/">&#x1F514; Alerts</a> &rsaquo;
            <a href="/learn">Knowledge Base</a> &rsaquo;
            {topic['title']}
          </div>
          <span class="cat-badge" style="background:{cat_color}22;color:{cat_color}">{cat}</span>
          <h2>{topic['title']}</h2>
          <p style="color:#374151;font-size:15px;line-height:1.75;margin:8px 0 20px">{topic['summary']}</p>
          <hr>
          {sections_html}
          {tips_html}
          {related_html}
          <div style="margin-top:28px;padding-top:20px;border-top:1px solid var(--border)">
            <a href="/learn" style="font-size:14px;color:var(--muted)">&larr; All topics</a>
          </div>
        </div>"""
        return Response(_learn_base(topic["title"], body), mimetype="text/html")

    # ── simple error helper ───────────────────────────────────────────────────

    def _simple_error(msg: str) -> Response:
        html = _base_html("Error", f"""
<div style="max-width:520px;margin:60px auto;padding:0 20px">
  <div class="page-card">
    <div class="icon">&#x26A0;</div>
    <h2>Something went wrong</h2>
    <p style="color:var(--danger)">{msg}</p>
    <a href="/" class="btn-back">&larr; Back</a>
  </div>
</div>
""")
        return Response(html, status=400, mimetype="text/html")

    return _app
