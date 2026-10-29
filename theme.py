"""MediGuide theme: dark/light base + 5 accent palettes, with a colour-wipe transition on every change."""
from .config import ACCENTS

PAL = {
    "Dark": dict(bg="#090b15", bg2="#121631", card="rgba(255,255,255,0.055)", border="rgba(255,255,255,0.11)",
                 text="#eceefb", muted="#a3a8c8", input="#171b38"),
    "Light": dict(bg="#f4f5fc", bg2="#e4e8fb", card="rgba(255,255,255,0.80)", border="rgba(20,25,70,0.12)",
                  text="#171a3a", muted="#5a6085", input="#ffffff"),
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
html, body, .stApp, button, input, textarea { font-family: 'Poppins', sans-serif; }
.stApp { color:__TEXT__; background-attachment: fixed;
  background:
    radial-gradient(1100px 600px at 8% -10%, __A1__38, transparent 60%),
    radial-gradient(900px 500px at 100% 0%, __A2__30, transparent 60%),
    radial-gradient(900px 600px at 50% 120%, __A3__2a, transparent 60%),
    linear-gradient(160deg, __BG__, __BG2__);
  transition: background .8s ease, color .6s ease; animation: themeIn___NAME__ .9s ease; }
@keyframes themeIn___NAME__ { from { opacity:.25; } to { opacity:1; } }
.wipe { position:fixed; inset:0; z-index:99999; pointer-events:none; opacity:0;
  background: linear-gradient(135deg, __A1__, __A2__, __A3__);
  animation: wipe___NAME__ 1.1s ease-in-out; }
@keyframes wipe___NAME__ { 0% { clip-path:circle(0% at 96% 4%); opacity:.9; }
  70% { opacity:.55; } 100% { clip-path:circle(160% at 96% 4%); opacity:0; } }
* { transition: background-color .5s ease, border-color .5s ease, color .4s ease; }
header[data-testid="stHeader"] { background: transparent; }
.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp p,.stApp li,.stApp label,
[data-testid="stMarkdownContainer"],[data-testid="stCaptionContainer"] { color:__TEXT__; }
[data-testid="stCaptionContainer"], [data-testid="stMetricLabel"] * { color:__MUTED__ !important; }
section[data-testid="stSidebar"] { background: linear-gradient(180deg, __BG2__, __BG__);
  border-right:1px solid __BORDER__; }
[data-testid="stVerticalBlock"] > div { animation: fadeUp .55s ease both; }
@keyframes fadeUp { from { opacity:0; transform:translateY(14px); } to { opacity:1; transform:none; } }
/* inputs */
[data-baseweb="input"] > div, [data-baseweb="select"] > div, [data-baseweb="base-input"], textarea,
[data-testid="stNumberInput"] input, [data-testid="stTextInput"] input { background:__INPUT__ !important;
  color:__TEXT__ !important; border-color:__BORDER__ !important; border-radius:12px !important; }
div[data-baseweb="popover"] ul, div[data-baseweb="popover"] li { background:__INPUT__ !important; color:__TEXT__ !important; }
[data-testid="stChatInput"] { background:__INPUT__; border-radius:16px; }
/* cards */
[data-testid="stMetric"], [data-testid="stExpander"], [data-testid="stForm"],
[data-testid="stVerticalBlockBorderWrapper"] { background:__CARD__; border:1px solid __BORDER__;
  border-radius:18px; backdrop-filter: blur(12px); }
[data-testid="stMetric"] { padding:16px 18px; transition: transform .3s ease, box-shadow .3s ease; }
[data-testid="stMetric"]:hover { transform: translateY(-5px); box-shadow:0 16px 36px __A1__40; }
[data-testid="stAlert"] { border-radius:14px; }
button[data-baseweb="tab"] { color:__MUTED__; }
button[data-baseweb="tab"][aria-selected="true"] { color:__A1__; }
[data-baseweb="tab-highlight"] { background:__A1__ !important; }
/* buttons */
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
  background: linear-gradient(120deg, __A1__, __A3__); color:#fff; border:0; border-radius:14px;
  padding:.6rem 1.3rem; font-weight:600; transition: transform .25s ease, box-shadow .25s ease, filter .25s ease; }
.stButton > button:hover, .stFormSubmitButton > button:hover, .stDownloadButton > button:hover {
  transform: translateY(-2px) scale(1.02); box-shadow:0 10px 26px __A1__66; filter:brightness(1.12); color:#fff; }
.stButton > button p, .stFormSubmitButton > button p, .stDownloadButton > button p { color:#fff !important; }
/* progress */
[data-testid="stProgress"] [role="progressbar"] > div, [data-testid="stProgress"] div[data-baseweb="progress-bar"] > div > div {
  background: linear-gradient(90deg, __A1__, __A2__, __A3__) !important; transition: width 1s ease; }
/* nav pills */
.st-key-nav div[role="radiogroup"] { gap:.5rem; flex-wrap:wrap; }
.st-key-nav div[role="radiogroup"] > label { background:__CARD__; border:1px solid __BORDER__; border-radius:999px;
  padding:.4rem 1.1rem; cursor:pointer; transition: transform .25s ease, box-shadow .25s ease; }
.st-key-nav div[role="radiogroup"] > label:hover { transform: translateY(-2px); }
.st-key-nav div[role="radiogroup"] > label > div:first-child { display:none; }
.st-key-nav div[role="radiogroup"] > label:has(input:checked) { background: linear-gradient(120deg, __A1__, __A3__);
  box-shadow:0 8px 22px __A1__55; }
.st-key-nav div[role="radiogroup"] > label:has(input:checked) p { color:#fff !important; }
/* custom blocks */
.hero { padding:30px 34px; border-radius:26px; margin-bottom:14px; border:1px solid __BORDER__;
  background: linear-gradient(135deg, __A1__30, __A2__22, __A3__30); background-size:200% 200%;
  animation: shift 9s ease infinite; }
@keyframes shift { 0%,100% { background-position:0% 50%; } 50% { background-position:100% 50%; } }
.hero h1 { margin:0; font-size:2.2rem; font-weight:700;
  background: linear-gradient(90deg, __A1__, __A2__, __A3__); -webkit-background-clip:text;
  -webkit-text-fill-color:transparent; }
.hero p { margin:.3rem 0 0; color:__MUTED__; }
.disclaimer { padding:10px 14px; border-radius:12px; font-size:.8rem; border:1px dashed __A2__;
  background:__A2__14; color:__TEXT__; }
.badge { display:inline-block; padding:.3rem .9rem; border-radius:999px; font-weight:700; color:#fff !important;
  letter-spacing:.05em; }
.badge.LOW { background:#16a34a; } .badge.MEDIUM { background:#d97706; }
.badge.HIGH { background:#dc2626; animation:pulse 1.6s infinite; } .badge.NA { background:#64748b; }
@keyframes pulse { 0% { box-shadow:0 0 0 0 #dc262688; } 100% { box-shadow:0 0 0 14px #dc262600; } }
.ring-wrap { text-align:center; }
.ring-bg { fill:none; stroke:__BORDER__; stroke-width:10; }
.ring-fg { fill:none; stroke-width:10; stroke-linecap:round; stroke-dasharray:339.3;
  transform:rotate(-90deg); transform-origin:60px 60px; animation: ringIn 1.5s ease-out both; }
@keyframes ringIn { from { stroke-dashoffset:339.3; } }
.ring-num { font-size:30px; font-weight:700; fill:__TEXT__; } .ring-sub { font-size:10px; fill:__MUTED__; }
.ring-label { font-weight:600; margin-top:-6px; } .ring-cap { color:__MUTED__; font-size:.8rem; }

.badge.LOW { background:#16a34a; } .badge.MEDIUM { background:#d97706; } .badge.HIGH { background:#ea580c; }
.badge.EMERGENCY { background:#dc2626; animation:pulse 1.2s infinite; font-size:1.1rem; }
.urgency-card { padding:22px 26px; border-radius:22px; border:1px solid __BORDER__; background:__CARD__;
  backdrop-filter: blur(12px); animation: fadeUp .6s ease both; }
.meter { display:flex; gap:6px; margin-top:12px; }
.meter div { flex:1; height:12px; border-radius:8px; background:__BORDER__; transition: all .6s ease; }
.meter div.on { box-shadow:0 0 14px currentColor; animation: grow .9s ease both; }
@keyframes grow { from { transform:scaleX(0); } to { transform:scaleX(1); } }
.safety { padding:12px 16px; border-radius:14px; border:1px solid #dc262699; background:#dc262618;
  color:__TEXT__; font-size:.88rem; margin-bottom:10px; }
.hero h1 { filter:drop-shadow(0 0 18px __A1__55); }
</style>
"""


def inject_css(mode: str, accent: str) -> str:
    p, (a1, a2, a3) = PAL.get(mode, PAL["Dark"]), ACCENTS.get(accent, next(iter(ACCENTS.values())))
    css = CSS.replace("__NAME__", f"{mode}_{accent}")
    for key, val in {**{k.upper(): v for k, v in p.items()}, "A1": a1, "A2": a2, "A3": a3}.items():
        css = css.replace(f"__{key}__", val)
    return css + '<div class="wipe"></div>'


def plotly_layout(mode: str) -> dict:
    p = PAL.get(mode, PAL["Dark"])
    return dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color=p["text"]),
                margin=dict(l=10, r=10, t=40, b=10), legend=dict(font=dict(color=p["text"])))
