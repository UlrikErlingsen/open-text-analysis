# Synced from signal-hub/signal-theme/signal_theme.py. Edit it there, then run scripts/sync_theme.py.
"""Shared look for every *Signal app. One import replaces the pasted <style> block.

    import signal_theme as sig
    st.set_page_config(**sig.page_config("worth"))
    sig.apply("worth")
    sig.sidebar_brand("worth")
    sig.masthead("worth", ["Local-first", "Explainable", "Open source"])
    sig.hero("worth", eyebrow="FROM ROWS TO RELATIONSHIPS", title="Customer value,", em="without the black box.",
             body="...", pills=["Excel, CSV & JSON", "No account required"])
    sig.note("warn", "**Use estimates wisely.** ...")
    sig.footer("worth", __version__, "Customer-value estimates, not future truth")

Design: Organic system (cream ground, dark warm sidebar, pill controls, soft circles),
Figtree throughout with ExtraBold headings. One accent per app family.
"""

from __future__ import annotations

from html import escape
from pathlib import Path

import streamlit as st

# ── Core tokens (Organic) ────────────────────────────────────────────────────
CORE = {
    "bg": "#f5ead8",
    "surface": "#ebddc5",
    "paper": "#f9f4ed",      # neutral-100: cards, metrics
    "text": "#201e1d",
    "muted": "#645c50",      # neutral-700
    "soft": "#a19786",       # neutral-500
    "line": "rgba(32,30,29,.16)",
    "sidebar": "#2e2b25",    # neutral-900
    "sidebar_text": "#f9f4ed",
    "sidebar_muted": "#c0b6a5",
    "warn_bg": "#fff2eb", "warn_text": "#643312",
    "info_bg": "#f0fae1", "info_text": "#3d472b",
}

# ── Families: 200 light fill · 300 tint on dark · 600 base · 700 text · 800 deep ──
FAMILIES = {
    "brand":    {"label": "Brand",    "200": "#ffe1d0", "300": "#ffc6a5", "600": "#b2622d", "700": "#8c491a", "800": "#643312"},
    "market":   {"label": "Market",   "200": "#e1eecc", "300": "#ccdbb2", "600": "#728157", "700": "#56633f", "800": "#3d472b"},
    "customer": {"label": "Customer", "200": "#f5e2ea", "300": "#edc8d8", "600": "#aa5d83", "700": "#894166", "800": "#622d48"},
    "research": {"label": "Research", "200": "#f2e6d7", "300": "#e7d0b2", "600": "#a06f1f", "700": "#805300", "800": "#5b3a00"},
    "decide":   {"label": "Decide",   "200": "#daeaf7", "300": "#b9d9f1", "600": "#4f80a2", "700": "#326384", "800": "#134766"},
}

# key: (prefix, family, repo, tagline)
APPS = {
    "track":      ("Track", "brand", "brand-tracking", "Is the brand moving, or is the tracker just noisy?"),
    "position":   ("Position", "brand", "brand-positioning", "See where brands stand"),
    "prospect":   ("Prospect", "market", "b2b-prospecting", "Norwegian B2B prospecting from open Brønnøysund data"),
    "listen":     ("Listen", "market", "media-listening", "Norwegian media and social listening"),
    "influence":  ("Influence", "market", "influencer-campaigns", "Which creators delivered, and was every post labelled properly?"),
    "season":     ("Season", "market", "marketing-calendar", "The Norwegian marketing year, worked backwards"),
    "adopt":      ("Adopt", "market", "adoption-forecasting", "Know when the market will follow"),
    "worth":      ("Worth", "customer", "customer-value-analytics", "Find the customers, value, and moves that matter"),
    "segment":    ("Segment", "customer", "customer-segmentation", "Find the groups worth understanding"),
    "trace":      ("Trace", "customer", "journey-path-analysis", "Where do journeys flow, stall, and end?"),
    "recommend":  ("Recommend", "customer", "recommender-evaluation", "Compare recommendation policies before the live test"),
    "choice":     ("Choice", "research", "conjoint-analysis", "Know what customers actually value"),
    "driver":     ("Driver", "research", "survey-driver-analysis", "See what moves with satisfaction and what to test next"),
    "measure":    ("Measure", "research", "measurement-validation", "Is this score measuring what you think it is?"),
    "text":       ("Text", "research", "open-text-analysis", "What are people actually saying, and does the pattern hold?"),
    "tag":        ("Tag", "research", "pricing-analysis", "What price range is supported, and how does profit move?"),
    "experiment": ("Experiment", "decide", "experiment-analysis", "Did the treatment cause a change worth acting on?"),
    "gate":       ("Gate", "decide", "launch-decision-gate", "Know when the evidence deserves the next investment"),
    "alloc":      ("Alloc", "decide", "marketing-mix-allocation", "Put the next budget where it works hardest"),
}

ASSETS = Path(__file__).parent / "assets"


def app(key: str) -> dict:
    prefix, family, repo, tagline = APPS[key]
    return {"key": key, "prefix": prefix, "name": f"{prefix} Signal", "slug": f"{prefix}signal".lower(), "family": family,
            "fam": FAMILIES[family], "repo": repo, "tagline": tagline}


def mark_svg(key: str, size: int = 40) -> str:
    """The app mark (Lucide glyph on a family-colored circle), inlined from assets/marks/."""
    path = ASSETS / "marks" / f"{app(key)['slug']}-mark.svg"
    svg = path.read_text(encoding="utf-8")
    return svg.replace("<svg ", f'<svg width="{size}" height="{size}" aria-hidden="true" ', 1)


def page_config(key: str, title_suffix: str | None = None) -> dict:
    a = app(key)
    icon = ASSETS / "marks" / f"{a['slug']}-mark-64.png"
    return {"page_title": f"{a['name']} | {title_suffix or a['tagline']}",
            "page_icon": str(icon) if icon.exists() else "●", "layout": "wide"}


# ── Chart palette ────────────────────────────────────────────────────────────
def colorway(key: str) -> list[str]:
    """Categorical series: the app's own family first, then the other families, then neutral."""
    own = app(key)["family"]
    order = [own] + [f for f in FAMILIES if f != own]
    return [FAMILIES[f]["600"] for f in order] + [CORE["muted"]]


def sequential(key: str) -> list[str]:
    f = app(key)["fam"]
    return [f["200"], f["300"], f["600"], f["700"], f["800"]]


DIVERGING = [FAMILIES["decide"]["800"], FAMILIES["decide"]["600"], FAMILIES["decide"]["200"],
             CORE["paper"], FAMILIES["brand"]["200"], FAMILIES["brand"]["600"], FAMILIES["brand"]["800"]]

# Semantic chart roles — same in every app.
ROLES = {"estimate": CORE["text"], "interval": CORE["soft"], "threshold": FAMILIES["brand"]["600"],
         "zero": CORE["muted"], "highlight": None}  # highlight = family 600, set in apply()


def plotly_template(key: str):
    import plotly.graph_objects as go
    import plotly.io as pio

    t = go.layout.Template()
    t.layout = go.Layout(
        colorway=colorway(key),
        font=dict(family="Figtree, system-ui, sans-serif", size=14, color=CORE["text"]),
        title=dict(font=dict(size=18, weight=800), x=0, xanchor="left"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="rgba(32,30,29,.08)", zerolinecolor=CORE["soft"], linecolor=CORE["line"], ticks=""),
        yaxis=dict(gridcolor="rgba(32,30,29,.08)", zerolinecolor=CORE["soft"], linecolor=CORE["line"], ticks=""),
        legend=dict(orientation="h", y=-0.18, x=0, bgcolor="rgba(0,0,0,0)"),
        geo=dict(bgcolor="rgba(0,0,0,0)", lakecolor=CORE["bg"], landcolor=CORE["paper"]),
        colorscale=dict(sequential=sequential(key), diverging=DIVERGING),
        hoverlabel=dict(bgcolor=CORE["sidebar"], font=dict(color=CORE["paper"], family="Figtree")),
        margin=dict(l=8, r=8, t=48, b=8),
    )
    pio.templates["signal"] = t
    pio.templates[f"signal-{key}"] = t
    pio.templates.default = "signal"
    return t


def template(key: str) -> str:
    """Per-app Plotly template name. Pass it to every figure (`template=sig.template(key)` in px calls, or
    `fig.update_layout(template=sig.template(key))`): the process-wide default set by apply() is shared by every
    session, so inside Signal Hub two apps open at once could otherwise borrow each other's colours."""
    import plotly.io as pio

    if f"signal-{key}" not in pio.templates:
        plotly_template(key)
    return f"signal-{key}"


def chart(app_key: str, fig, **kwargs):
    """Show a Plotly figure in the Signal look: the app's template, and theme=None so Streamlit's own chart theme
    does not replace Figtree and the palette. Other keyword arguments go to st.plotly_chart (key=, on_select=...);
    its return value (the selection state when on_select is set) is passed back."""
    fig.update_layout(template=template(app_key))
    kwargs.setdefault("theme", None)
    kwargs.setdefault("width", "stretch")
    return st.plotly_chart(fig, **kwargs)


def roles(key: str) -> dict:
    """Semantic chart colours for one app (ROLES with highlight = the app's family 600). Prefer this over ROLES."""
    return {**ROLES, "highlight": app(key)["fam"]["600"]}


# ── CSS ──────────────────────────────────────────────────────────────────────
def _css(key: str) -> str:
    f = app(key)["fam"]
    c = CORE
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Figtree:wght@400;600;700;800&display=swap');
:root {{
  --sg-bg:{c['bg']}; --sg-surface:{c['surface']}; --sg-paper:{c['paper']}; --sg-text:{c['text']};
  --sg-muted:{c['muted']}; --sg-line:{c['line']}; --sg-side:{c['sidebar']};
  --sg-a200:{f['200']}; --sg-a300:{f['300']}; --sg-a600:{f['600']}; --sg-a700:{f['700']}; --sg-a800:{f['800']};
  --sg-r:28px;
}}
html, body, .stApp, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6, .stApp p, .stApp li,
.stApp label, .stApp button, .stApp input, .stApp textarea, .stApp select, .stApp [data-baseweb], .stApp td, .stApp th,
[data-testid="stMarkdownContainer"], [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {{
  font-family:'Figtree',system-ui,sans-serif !important; }}
[data-testid="stAppViewContainer"] {{ background:var(--sg-bg); color:var(--sg-text); }}
[data-testid="stHeader"] {{ background:color-mix(in srgb, var(--sg-bg) 85%, transparent); }}
.block-container {{ max-width:1240px; padding-top:4.4rem; padding-bottom:4rem; }}
h1,h2,h3,h4 {{ color:var(--sg-text); font-weight:800 !important; letter-spacing:-.03em; }}
a {{ color:var(--sg-a700); }} a:hover {{ color:var(--sg-a800); }}
:focus-visible {{ outline:2px solid var(--sg-a600) !important; outline-offset:2px; }}
::selection {{ background:var(--sg-a200); }}

/* sidebar — dark, warm */
[data-testid="stSidebar"] {{ background:var(--sg-side); border-radius:0 var(--sg-r) var(--sg-r) 0; }}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,[data-testid="stSidebar"] label,[data-testid="stSidebar"] span {{ color:{c['sidebar_text']}; }}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] small,
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] small span {{ color:{c['sidebar_muted']} !important; }}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {{
  background:rgba(249,244,237,.06); border:1.5px dashed var(--sg-a600); border-radius:32px; }}
[data-testid="stSidebar"] :is(.stButton,.stDownloadButton,.stLinkButton,.stFormSubmitButton) button {{ background:rgba(249,244,237,.08); border:1px solid rgba(249,244,237,.22);
  border-radius:999px; color:{c['sidebar_text']} !important; }}
[data-testid="stSidebar"] :is(.stButton,.stDownloadButton,.stLinkButton,.stFormSubmitButton) button * {{ color:{c['sidebar_text']} !important; }}
[data-testid="stSidebar"] :is(.stButton,.stDownloadButton,.stLinkButton,.stFormSubmitButton) button:hover {{ background:rgba(249,244,237,.14); border-color:var(--sg-a300); }}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {{ background:{c['paper']}; border-color:transparent; }}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button * {{ color:{c['text']} !important; }}
[data-testid="stSidebar"] [role="radiogroup"] label {{ border-radius:999px; padding:.3rem .8rem; margin:0; }}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {{ background:rgba(249,244,237,.08); }}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{ background:var(--sg-a700); }}
[data-testid="stSidebar"] [data-testid="stExpander"] {{ background:rgba(249,244,237,.06); border-color:rgba(249,244,237,.18); }}
[data-testid="stSidebar"] [data-testid="stExpander"] summary, [data-testid="stSidebar"] [data-testid="stExpander"] summary * {{ color:{c['sidebar_text']} !important; }}
[data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stMarkdownContainer"] * {{ color:{c['sidebar_text']}; }}

/* st.navigation menu (multipage apps and Signal Hub) */
[data-testid="stSidebarNav"] a {{ border-radius:999px; }}
[data-testid="stSidebarNav"] a span {{ color:{c['sidebar_text']} !important; }}
[data-testid="stSidebarNav"] a:hover {{ background:rgba(249,244,237,.08); }}
[data-testid="stSidebarNav"] a[aria-current="page"] {{ background:var(--sg-a700); }}
[data-testid="stNavSectionHeader"] span, [data-testid="stSidebarNavSeparator"] {{ color:{c['sidebar_muted']} !important; }}

/* controls — pills */
.stButton > button, .stDownloadButton > button {{ border-radius:999px; font-weight:700; border:1px solid var(--sg-line);
  background:transparent; color:var(--sg-text); padding:.5rem 1.2rem; }}
.stButton > button:hover, .stDownloadButton > button:hover {{ background:rgba(32,30,29,.07); border-color:var(--sg-line); color:var(--sg-text); }}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {{ background:var(--sg-a600); color:{c['paper']}; border:0; }}
.stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover,
.stFormSubmitButton > button[kind="primary"]:hover {{ background:var(--sg-a700); color:{c['paper']}; }}
.stButton > button[kind="primary"]:active {{ background:var(--sg-a800); }}
[data-baseweb="select"] > div, [data-baseweb="input"], .stTextInput input, .stNumberInput input {{
  border-radius:999px !important; background:var(--sg-paper); }}
[data-baseweb="tag"] {{ background:var(--sg-a200) !important; color:var(--sg-a800) !important; border-radius:999px; }}

/* surfaces */
[data-testid="stMetric"] {{ background:var(--sg-paper); border-radius:var(--sg-r); padding:1rem 1.2rem; }}
[data-testid="stMetricValue"] {{ color:var(--sg-text); font-weight:800; letter-spacing:-.02em; }}
[data-testid="stMetricLabel"] p {{ color:var(--sg-muted); }}
[data-testid="stExpander"] {{ border-radius:var(--sg-r); border:1px solid var(--sg-line); background:var(--sg-paper); }}
[data-testid="stAlert"] {{ border-radius:var(--sg-r); border:0; }}
[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius:var(--sg-r); }}
[data-testid="stDataFrame"] {{ border-radius:16px; overflow:hidden; }}
.stTabs [data-baseweb="tab-list"] {{ gap:.4rem; }}
.stTabs [data-baseweb="tab"] {{ border-radius:999px; padding:.35rem 1rem; }}
.stTabs [aria-selected="true"] {{ background:var(--sg-a200); color:var(--sg-a800); }}
.stTabs [data-baseweb="tab-highlight"] {{ display:none; }}

/* signal components */
.sg-lockup {{ display:flex; align-items:center; gap:.6rem; }}
.sg-name {{ font-weight:800; letter-spacing:-.035em; line-height:1; }}
.sg-side {{ padding:.25rem 0 1.1rem; }}
.sg-side .sg-name {{ color:{c['sidebar_text']}; font-size:1.35rem; }}
.sg-side .sg-name span {{ color:var(--sg-a300) !important; }}
.sg-side p {{ margin:.55rem 0 0 !important; color:{c['sidebar_muted']} !important; font-size:.82rem; line-height:1.4; }}
.sg-mast {{ display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:1rem;
  padding:.5rem 1.4rem .5rem .5rem; margin-bottom:1.5rem; background:var(--sg-paper); border-radius:999px; }}
.sg-mast .sg-name {{ font-size:1.6rem; color:var(--sg-text); }}
.sg-mast .sg-name span {{ color:var(--sg-a600); }}
.sg-kicker {{ margin-top:.3rem; color:var(--sg-muted); font-size:.68rem; font-weight:700; letter-spacing:.13em; text-transform:uppercase; }}
.sg-pills {{ display:flex; flex-wrap:wrap; gap:.45rem; }}
.sg-pill {{ white-space:nowrap; padding:.28rem .8rem; border-radius:999px; font-size:.78rem; background:var(--sg-a200); color:var(--sg-a800); }}
.sg-hero {{ position:relative; overflow:hidden; padding:clamp(1.8rem,4.5vw,3.6rem); margin-bottom:1.4rem;
  background:var(--sg-a800); border-radius:calc(var(--sg-r) * 1.6); }}
.sg-hero:before {{ content:""; position:absolute; width:340px; height:340px; right:-90px; top:-130px; border-radius:50%; background:var(--sg-a700); }}
.sg-hero:after {{ content:""; position:absolute; width:150px; height:150px; right:150px; bottom:-70px; border-radius:50%; background:var(--sg-a600); }}
.sg-hero > * {{ position:relative; z-index:1; }}
.sg-eyebrow {{ color:var(--sg-a300); font-size:.74rem; font-weight:700; letter-spacing:.16em; }}
.sg-hero h1 {{ color:{c['paper']} !important; font-size:clamp(2.4rem,5vw,4.4rem); line-height:1; margin:.7rem 0 1rem; max-width:900px; }}
.sg-hero h1 em {{ color:var(--sg-a300); font-style:normal; }}
.sg-hero p {{ color:var(--sg-a200); font-size:1.06rem; line-height:1.6; max-width:760px; }}
.sg-hero .sg-pill {{ background:rgba(249,244,237,.12); color:{c['paper']}; font-size:.82rem; padding:.38rem .9rem; }}
.sg-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:1rem; margin:1.2rem 0 1.5rem; }}
.sg-card {{ padding:1.3rem 1.4rem; background:var(--sg-paper); border-radius:var(--sg-r); }}
.sg-card b {{ color:var(--sg-a700); font-size:.72rem; letter-spacing:.12em; }}
.sg-card h3 {{ margin:.4rem 0 .5rem; font-size:1.25rem; }}
.sg-card p {{ color:var(--sg-muted); font-size:.92rem; line-height:1.55; margin:0; }}
.sg-title {{ font-size:clamp(1.7rem,3vw,2.3rem); line-height:1.08; font-weight:800; letter-spacing:-.03em; margin:.2rem 0 .6rem; }}
.sg-sub {{ font-size:1.02rem; color:var(--sg-muted); max-width:820px; margin-bottom:1.2rem; line-height:1.55; }}
.sg-note {{ display:flex; gap:.7rem; padding:1rem 1.3rem; border-radius:var(--sg-r); font-size:.95rem; line-height:1.55; margin:.6rem 0; }}
.sg-note.info {{ background:{c['info_bg']}; color:{c['info_text']}; }}
.sg-note.warn {{ background:{c['warn_bg']}; color:{c['warn_text']}; }}
.sg-note.boundary {{ background:var(--sg-paper); color:var(--sg-muted); }}
.sg-note.muted {{ padding:.2rem 0; background:transparent; color:var(--sg-muted); font-size:.82rem; }}
.sg-foot {{ margin-top:3.2rem; display:flex; flex-wrap:wrap; gap:.5rem; color:var(--sg-muted); font-size:.8rem; }}
.sg-foot i {{ color:var(--sg-a600); font-style:normal; }}
@media (max-width:760px) {{ .sg-mast .sg-pills {{ display:none; }} .sg-hero {{ border-radius:28px; }} .block-container {{ padding-top:3.5rem; }} }}
@media (prefers-reduced-motion:reduce) {{ * {{ scroll-behavior:auto !important; transition:none !important; }} }}
</style>"""


def apply(key: str, charts: bool = True) -> None:
    st.markdown(_css(key), unsafe_allow_html=True)
    ROLES["highlight"] = app(key)["fam"]["600"]
    if charts:
        try:
            plotly_template(key)
        except ImportError:
            pass


def _word(a: dict) -> str:
    return f'{escape(a["prefix"])} <span>Signal</span>'


def sidebar_brand(key: str, tagline: str | None = None) -> None:
    a = app(key)
    with st.sidebar:
        st.markdown(f'<div class="sg-side"><div class="sg-lockup">{mark_svg(key, 36)}<div class="sg-name">{_word(a)}</div></div>'
                    f'<p>{escape(tagline or a["tagline"])}</p></div>', unsafe_allow_html=True)


def masthead(key: str, promises: list[str], kicker: str | None = None) -> None:
    a = app(key)
    pills = "".join(f'<span class="sg-pill">{escape(p)}</span>' for p in promises)
    st.markdown(f'<div class="sg-mast"><div class="sg-lockup">{mark_svg(key, 52)}<div><div class="sg-name">{_word(a)}</div>'
                f'<div class="sg-kicker">{escape(kicker or "Signal · " + a["fam"]["label"])}</div></div></div>'
                f'<div class="sg-pills">{pills}</div></div>', unsafe_allow_html=True)


def hero(key: str, *, eyebrow: str, title: str, em: str = "", body: str = "", pills: list[str] | None = None) -> None:
    pills_html = "".join(f'<span class="sg-pill">{escape(p)}</span>' for p in (pills or []))
    st.markdown(f'<section class="sg-hero"><div class="sg-eyebrow">{escape(eyebrow)}</div>'
                f'<h1>{escape(title)}{"<br><em>" + escape(em) + "</em>" if em else ""}</h1>'
                f'{"<p>" + escape(body) + "</p>" if body else ""}<div class="sg-pills">{pills_html}</div></section>',
                unsafe_allow_html=True)


def cards(items: list[tuple[str, str, str]]) -> None:
    """items: (kicker, title, body)."""
    html = "".join(f'<div class="sg-card"><b>{escape(k)}</b><h3>{escape(t)}</h3><p>{escape(b)}</p></div>' for k, t, b in items)
    st.markdown(f'<div class="sg-grid">{html}</div>', unsafe_allow_html=True)


def header(kicker: str, title: str, subtitle: str = "") -> None:
    st.markdown(f'<div class="sg-kicker" style="color:var(--sg-a700)">{escape(kicker)}</div>'
                f'<div class="sg-title">{escape(title)}</div>'
                f'{"<div class=sg-sub>" + escape(subtitle) + "</div>" if subtitle else ""}', unsafe_allow_html=True)


def note(kind: str, markdown_text: str) -> None:
    """kind: info | warn | boundary | muted (small print). Supports **bold**, `code` and [links](https://...)."""
    import re
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escape(markdown_text))
    html = re.sub(r"`([^`]+)`", r"<code>\1</code>", html)
    html = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
                  r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', html)
    html = re.sub(r"\n{2,}", "<br><br>", html.strip()).replace("\n", " ")  # blank line = new paragraph
    st.markdown(f'<div class="sg-note {kind}"><div>{html}</div></div>', unsafe_allow_html=True)


def footer(key: str, version: str, line: str) -> None:
    a = app(key)
    parts = [f"{a['name']} v{version}", line, "Part of the Signal suite", "AGPL-3.0-or-later"]
    st.markdown('<div class="sg-foot">' + ' <i>●</i> '.join(escape(p) for p in parts) + '</div>', unsafe_allow_html=True)
