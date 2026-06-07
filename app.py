import streamlit as st
import json
import os
import math
import copy
import pandas as pd
import pytz
from collections import Counter
from datetime import datetime, timedelta, time

# ============================================================
# CONFIG & TIMEZONE
# ============================================================
st.set_page_config(page_title="The Personal Vault", page_icon="🛡️", layout="wide")

NEPAL_TZ = pytz.timezone('Asia/Kathmandu')
DB_FILE  = "local_database.json"

def get_now():       return datetime.now(NEPAL_TZ)
def get_today_str(): return str(get_now().date())
def is_saturday():   return get_now().weekday() == 5

# ============================================================
# MASTER CSS  —  Warm Dark Parchment Theme (readable)
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700;900&family=Crimson+Pro:ital,wght@0,300;0,400;0,600;1,300;1,400&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }

/* ── Background: warm light parchment ── */
html, body {
    background: #fdf8f0 !important;
}
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
section[data-testid="stSidebar"],
.main {
    background: #fdf8f0 !important;
    background-image:
        radial-gradient(ellipse 80% 50% at 20% 10%, rgba(201,168,76,0.08) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 90%, rgba(180,140,60,0.06) 0%, transparent 60%) !important;
    color: #2a2010;
    font-family: 'Crimson Pro', Georgia, serif;
}

#MainMenu, footer, header, .stDeployButton { visibility: hidden !important; }
.block-container { padding: 1.5rem 2.5rem 4rem !important; max-width: 1400px !important; }

/* ── Body text — bright enough to actually read ── */
.stMarkdown p, .stMarkdown li {
    font-family: 'Crimson Pro', serif;
    font-size: 1.05rem;
    line-height: 1.75;
    color: #3a3020;
}
h1, h2, h3 { font-family: 'Cinzel', serif !important; color: #7a5a10 !important; }

/* ── Hero ── */
.vault-hero {
    text-align: center;
    padding: 2.5rem 2rem 1.8rem;
    position: relative;
    margin-bottom: 0.5rem;
}
.vault-hero::before {
    content: '';
    position: absolute;
    top: 0; left: 50%; transform: translateX(-50%);
    width: 320px; height: 1px;
    background: linear-gradient(90deg, transparent, #c9a84c, transparent);
}
.vault-hero::after {
    content: '';
    position: absolute;
    bottom: 0; left: 50%; transform: translateX(-50%);
    width: 520px; height: 1px;
    background: linear-gradient(90deg, transparent, #c9a84c66, transparent);
}
.vault-title {
    font-family: 'Cinzel', serif;
    font-size: 3rem;
    font-weight: 900;
    letter-spacing: 0.12em;
    background: linear-gradient(135deg, #f5e17a 0%, #c9a84c 40%, #e8c96a 70%, #b08830 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0; line-height: 1.1;
}
.vault-subtitle {
    font-family: 'Crimson Pro', serif;
    font-style: italic;
    font-size: 1.1rem;
    color: #6a5530;
    letter-spacing: 0.2em;
    margin-top: 0.4rem;
}
.vault-time {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.76rem;
    color: #7a6e52;
    letter-spacing: 0.15em;
    margin-top: 0.7rem;
    text-transform: uppercase;
}

/* ── Stat Cards ── */
.stat-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin: 1.5rem 0 2rem;
}
.stat-card {
    background: linear-gradient(135deg, #f5ead8 0%, #ede0c4 100%);
    border: 1px solid #d4c09a;
    border-top: 2px solid var(--accent, #c9a84c);
    border-radius: 6px;
    padding: 1.2rem 1.4rem 1rem;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(201,168,76,0.12);
}
.stat-icon { font-size: 1.5rem; margin-bottom: 0.3rem; display: block; }
.stat-label {
    font-family: 'Cinzel', serif;
    font-size: 0.58rem;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: #7a6e52;
    margin-bottom: 0.2rem;
}
.stat-value {
    font-family: 'Cinzel', serif;
    font-size: 1.7rem;
    font-weight: 700;
    color: var(--accent, #c9a84c);
    line-height: 1;
}
.stat-sub {
    font-family: 'Crimson Pro', serif;
    font-size: 0.82rem;
    color: #9a8050;
    margin-top: 0.2rem;
    font-style: italic;
}

/* ── Section Dividers ── */
.section-divider {
    display: flex; align-items: center; gap: 1rem;
    margin: 2rem 0 1.5rem;
}
.section-divider::before, .section-divider::after {
    content: ''; flex: 1; height: 1px;
    background: linear-gradient(90deg, transparent, #4a3e28, #4a3e28, transparent);
}
.section-title {
    font-family: 'Cinzel', serif;
    font-size: 0.68rem;
    letter-spacing: 0.35em;
    text-transform: uppercase;
    color: #c9a84c;
    white-space: nowrap;
}

/* ── Form styling ── */
.stForm {
    background: linear-gradient(160deg, #f8f0e0 0%, #f2e8d0 100%) !important;
    border: 1px solid #d4c09a !important;
    border-radius: 6px !important;
    padding: 1.5rem !important;
}
.form-section-head {
    font-family: 'Cinzel', serif;
    font-size: 0.63rem;
    letter-spacing: 0.4em;
    text-transform: uppercase;
    color: #c9a84c;
    padding: 0.4rem 0;
    border-bottom: 1px solid #3a3020;
    margin: 1.5rem 0 1rem;
}

/* ── Inputs ── */
.stNumberInput input, .stTextInput input, .stTimeInput input {
    background: #faf4e8 !important;
    border: 1px solid #d4c09a !important;
    border-radius: 3px !important;
    color: #2a2010 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.9rem !important;
}
.stNumberInput input:focus, .stTextInput input:focus {
    border-color: #c9a84c !important;
    box-shadow: 0 0 0 2px rgba(201,168,76,0.2) !important;
}
.stCheckbox label {
    color: #3a3020 !important;
    font-family: 'Crimson Pro', serif !important;
    font-size: 1.02rem !important;
}

/* ── Label text ── */
.stSelectbox label, .stNumberInput label, .stTextInput label,
.stTimeInput label, div[data-testid="stWidgetLabel"] p {
    font-family: 'Crimson Pro', serif !important;
    font-size: 0.97rem !important;
    color: #5a4a20 !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #f0e8d0 0%, #e8dcc0 100%) !important;
    border: 1px solid #5a4a28 !important;
    border-radius: 3px !important;
    color: #7a5a10 !important;
    font-family: 'Cinzel', serif !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    padding: 0.6rem 1rem !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #3a2e18 0%, #4a3a1a 100%) !important;
    border-color: #c9a84c !important;
    box-shadow: 0 0 18px rgba(201,168,76,0.18) !important;
    color: #f0dc88 !important;
    transform: translateY(-1px) !important;
}
[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #302412 0%, #45350e 50%, #302412 100%) !important;
    border: 1px solid #c9a84c !important;
    color: #f5e17a !important;
    font-size: 0.82rem !important;
    padding: 0.8rem 2rem !important;
    letter-spacing: 0.25em !important;
    box-shadow: 0 0 25px rgba(201,168,76,0.12) !important;
    margin-top: 1rem !important;
}
[data-testid="stFormSubmitButton"] > button:hover {
    background: linear-gradient(135deg, #45350e 0%, #60480f 50%, #45350e 100%) !important;
    box-shadow: 0 0 35px rgba(201,168,76,0.22) !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #3a3020 !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border: none !important;
    color: #7a6a48 !important;
    font-family: 'Cinzel', serif !important;
    font-size: 0.68rem !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    padding: 0.8rem 1.4rem !important;
    border-bottom: 2px solid transparent !important;
    transition: all 0.2s !important;
}
.stTabs [aria-selected="true"] {
    color: #c9a84c !important;
    border-bottom: 2px solid #c9a84c !important;
}
.stTabs [data-baseweb="tab"]:hover { color: #a08840 !important; }
.stTabs [data-baseweb="tab-panel"] { background: transparent !important; padding: 1.5rem 0 !important; }

/* ── Expander ── */
.stExpander {
    background: #f8f2e4 !important;
    border: 1px solid #d4c09a !important;
    border-radius: 4px !important;
}
.stExpander summary { color: #6a5530 !important; font-family: 'Cinzel', serif !important; font-size: 0.73rem !important; letter-spacing: 0.18em !important; }

/* ── Metric containers ── */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #f5ead8 0%, #ede0c4 100%) !important;
    border: 1px solid #d4c09a !important;
    border-top: 2px solid #c9a84c !important;
    border-radius: 4px !important;
    padding: 1rem !important;
}
[data-testid="stMetricLabel"] { font-family: 'Cinzel', serif !important; font-size: 0.58rem !important; letter-spacing: 0.2em !important; color: #7a6a48 !important; }
[data-testid="stMetricValue"] { font-family: 'Cinzel', serif !important; font-size: 1.5rem !important; color: #c9a84c !important; }

/* ── Alert boxes ── */
.stInfo {
    background: rgba(201,168,76,0.07) !important;
    border: 1px solid #4a3e28 !important;
    border-left: 3px solid #c9a84c !important;
    color: #cfc090 !important;
    font-family: 'Crimson Pro', serif !important;
    font-size: 1rem !important;
}
.stSuccess {
    background: rgba(80,160,80,0.1) !important;
    border: 1px solid #2a4a2a !important;
    border-left: 3px solid #5aaa5a !important;
    color: #9ada9a !important;
    font-family: 'Crimson Pro', serif !important;
}
.stError {
    background: rgba(200,70,70,0.1) !important;
    border: 1px solid #4a2020 !important;
    border-left: 3px solid #aa4a4a !important;
    color: #d49090 !important;
    font-family: 'Crimson Pro', serif !important;
}
.stWarning {
    background: rgba(200,150,40,0.1) !important;
    border: 1px solid #4a3010 !important;
    border-left: 3px solid #aa8030 !important;
    color: #d4b070 !important;
    font-family: 'Crimson Pro', serif !important;
}

/* ── Dataframe / Ledger ── */
.stDataFrame { border: 1px solid #d4c09a !important; border-radius: 4px !important; }
[data-testid="stDataFrame"] th {
    background: #221e16 !important;
    font-family: 'Cinzel', serif !important;
    font-size: 0.63rem !important;
    letter-spacing: 0.12em !important;
    color: #6a5530 !important;
    border-bottom: 1px solid #3a3020 !important;
}
[data-testid="stDataFrame"] td {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.8rem !important;
    color: #3a3020 !important;
    background: #f0e8d4 !important;
}

/* ── Shop item cards ── */
.shop-item {
    background: linear-gradient(160deg, #f8f0e0, #f0e8d0);
    border: 1px solid #d4c09a;
    border-radius: 6px;
    padding: 1rem 0.8rem 0.7rem;
    text-align: center;
    margin-bottom: 0.5rem;
    transition: all 0.2s;
}
.shop-item:hover { border-color: #6a5828; box-shadow: 0 4px 18px rgba(201,168,76,0.12); }
.shop-item-emoji { font-size: 2rem; display: block; margin-bottom: 0.35rem; line-height: 1; }
.shop-item-name {
    font-family: 'Crimson Pro', serif;
    font-size: 0.95rem;
    color: #d4c49a;
    display: block;
    margin-bottom: 0.25rem;
    font-weight: 600;
}
.shop-item-price {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: #c9a84c;
}

/* ── Tier badges ── */
.tier-badge {
    display: inline-block;
    font-family: 'Cinzel', serif;
    font-size: 0.6rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    padding: 0.2rem 0.8rem;
    border-radius: 2px;
    margin-bottom: 1rem;
}
.tier-1 { background: rgba(180,120,60,0.18); color: #c8906a; border: 1px solid #4a3020; }
.tier-2 { background: rgba(200,200,200,0.1);  color: #b0b0b0; border: 1px solid #404040; }
.tier-3 { background: rgba(60,200,110,0.1);   color: #60c880; border: 1px solid #1a4a28; }
.tier-4 { background: rgba(140,80,220,0.12);  color: #9860d0; border: 1px solid #30185a; }
.tier-5 { background: rgba(255,210,40,0.14);  color: #f5ca38; border: 1px solid #4a3a08; }

/* ── Achievement cards ── */
.ach-card {
    display: flex; align-items: flex-start; gap: 0.8rem;
    padding: 0.9rem 1rem;
    background: #f8f2e4;
    border: 1px solid #2a2418;
    border-radius: 5px;
    margin-bottom: 0.5rem;
    transition: all 0.2s;
}
.ach-card.unlocked { border-color: #4a3e24; background: linear-gradient(135deg, #221e12, #2a2416); }
.ach-card.unlocked:hover { border-color: #c9a84c; box-shadow: 0 2px 14px rgba(201,168,76,0.1); }
.ach-icon { font-size: 1.4rem; min-width: 2rem; }
.ach-name { font-family: 'Cinzel', serif; font-size: 0.72rem; letter-spacing: 0.1em; color: #6a5a38; display: block; margin-bottom: 0.15rem; }
.ach-card.unlocked .ach-name { color: #c9a84c; }
.ach-desc { font-family: 'Crimson Pro', serif; font-style: italic; font-size: 0.88rem; color: #5a5038; }
.ach-card.unlocked .ach-desc { color: #6a5530; }

/* ── Inventory items ── */
.inv-item {
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.7rem 1rem;
    background: #f8f2e4;
    border: 1px solid #2a2418;
    border-left: 3px solid #c9a84c;
    border-radius: 3px;
    margin-bottom: 0.4rem;
    font-family: 'Crimson Pro', serif;
    color: #d4c49a;
    font-size: 1rem;
}
.inv-count {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    background: rgba(201,168,76,0.12);
    color: #c9a84c;
    padding: 0.15rem 0.5rem;
    border-radius: 2px;
}

/* ── Ledger line items ── */
.ledger-group {
    border: 1px solid #d4c09a;
    border-radius: 6px;
    overflow: hidden;
    margin-bottom: 1rem;
}
.ledger-group-header {
    background: linear-gradient(135deg, #ede0c4, #e4d4b0);
    padding: 0.6rem 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #3a3020;
}
.ledger-group-date {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: #6a5530;
    letter-spacing: 0.1em;
}
.ledger-group-net {
    font-family: 'Cinzel', serif;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.05em;
}
.ledger-group-net.pos { color: #6ac878; }
.ledger-group-net.neg { color: #d47070; }
.ledger-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.45rem 1rem 0.45rem 1.4rem;
    border-bottom: 1px solid #272015;
    font-family: 'Crimson Pro', serif;
    font-size: 0.95rem;
}
.ledger-row:last-child { border-bottom: none; }
.ledger-row:hover { background: rgba(201,168,76,0.04); }
ledger-cat { color: #3a2a10; flex: 1; }
.ledger-pts {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    font-weight: 600;
    min-width: 64px;
    text-align: right;
}
.ledger-pts.earn  { color: #6ac878; }
.ledger-pts.pen   { color: #d47070; }
.ledger-pts.zero  { color: #5a5038; }
.ledger-pts.stars { color: #f5d060; }
.ledger-balance-row {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    gap: 0.6rem;
    padding: 0.4rem 1rem;
    background: #ede4cc;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: #7a6a48;
}
.ledger-balance-val { color: #c9a84c; font-weight: 600; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #f0e8d4; }
::-webkit-scrollbar-thumb { background: #3a3020; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #5a4a28; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# STATIC DATA
# ============================================================
REAL_FOODS = {
    "Wai Wai / Chatpate":    ("🍜", 15),
    "Samosa / Patties":      ("🥟", 20),
    "Plate of Momo":         ("🥣", 40),
    "Sausage":               ("🌭", 20),
    "Chowmein":              ("🍝", 50),
    "Junk Food / Chips":     ("🍟", 30),
    "Chocolate Bar":         ("🍫", 30),
    "Cold Coffee / Milkshake":("☕", 80),
    "Burger":                ("🍔", 120),
    "Pizza":                 ("🍕", 250),
    "Evening Out":           ("🌙", 400),
}

VIRTUAL_SHOP = {
    "Tier 1 (Cheap)": {
        "Wooden Desk Token":  ("🪵", 10),
        "Copper Calculator":  ("🔢", 25),
        "Paper Crown":        ("📄", 50),
    },
    "Tier 2 (Common)": {
        "Bronze Study Lamp":  ("🪔", 100),
        "Silver Bookmark":    ("🔖", 150),
        "Focus Potion":       ("🧪", 200),
    },
    "Tier 3 (Rare)": {
        "Golden Ledger":      ("📒", 500),
        "Emerald Highlighter":("💚", 750),
        "The 5AM Shield":     ("🛡️", 1000),
    },
    "Tier 4 (Epic)": {
        "Platinum Gavel":     ("⚖️", 2500),
        "Diamond Abacus":     ("💎", 3500),
        "Aura of Silence":    ("🧘", 5000),
    },
    "Tier 5 (Legendary)": {
        "The Auditor's Seal": ("🏛️", 7500),
        "Crown of the Grand Auditor": ("👑", 10000),
    },
}

TIER_CSS  = {"Tier 1 (Cheap)":"tier-1","Tier 2 (Common)":"tier-2","Tier 3 (Rare)":"tier-3","Tier 4 (Epic)":"tier-4","Tier 5 (Legendary)":"tier-5"}
TIER_ICONS= {"Tier 1 (Cheap)":"🪵","Tier 2 (Common)":"🥉","Tier 3 (Rare)":"💚","Tier 4 (Epic)":"💜","Tier 5 (Legendary)":"👑"}

ACHIEVEMENTS = {
    "Day One":          ("📜","Fill your first daily log."),
    "First Star":       ("⭐","Earn your first Super Star."),
    "Bookworm":         ("📚","Study for 5 hours in a day."),
    "Saturday Scholar": ("🎓","Study for 8 hours on a Saturday."),
    "Silent Monk":      ("🧘","Claim the Silence point 5 times."),
    "Early Riser":      ("🌅","Wake up before 5:30 AM 3 times."),
    "Clean Freak":      ("🧹","Maintain the room and bath routine for a week."),
    "Digital Detox":    ("📵","Use mobile for under 3 hours."),
    "Foodie":           ("🍜","Buy 3 real-life food items."),
    "Relic Hunter":     ("🏺","Buy a Tier 3 Virtual Item."),
    "Bronze Rank":      ("🥉","Reach 1,000 EXP."),
    "Gold Rank":        ("🥇","Reach 10,000 EXP."),
    "Audit Master":     ("💫","Earn 50 Super Stars."),
}

# ============================================================
# DATABASE
# ============================================================
def get_default_data():
    today = get_today_str()
    return {
        "admin_password": "admin",
        "balance": 0, "lifetime_exp": 0, "super_stars": 0, "streak": 0,
        "last_login": str(get_now().date() - timedelta(days=1)),
        "daily_logs": {}, "history": [], "inventory": [], "unlocked_achievements": [],
        "split_tasks": {"Bath": today, "Clean Room": today, "Laundry": today},
    }

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: data = json.load(f)
        data.setdefault("admin_password", "admin")
        data.setdefault("split_tasks", {"Bath": get_today_str(), "Clean Room": get_today_str(), "Laundry": get_today_str()})
        data.setdefault("unlocked_achievements", [])
        data.setdefault("inventory", [])
        # Backfill missing keys on old history entries
        for entry in data.get("history", []):
            entry.setdefault("net", entry.get("earned", 0) - entry.get("penalty", 0))
            entry.setdefault("earned", 0)
            entry.setdefault("penalty", 0)
            entry.setdefault("stars", 0)
            entry.setdefault("balance", 0)
            entry.setdefault("type", "transaction")
        return data
    return get_default_data()

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

if "user_data" not in st.session_state:
    st.session_state.user_data = load_db()
if "form_key" not in st.session_state:
    st.session_state.form_key = 0
d = st.session_state.user_data
def save_state(): save_db(st.session_state.user_data)

# ============================================================
# LEDGER  —  itemised per category
# ============================================================
def log_transaction(action: str, coins: int, stars: float = 0):
    """General ledger entry (shop purchases, manual adjustments)."""
    d["balance"]     += coins
    d["super_stars"] += stars
    if coins > 0: d["lifetime_exp"] += coins
    d["history"].insert(0, {
        "date":    get_now().strftime("%Y-%m-%d"),
        "time":    get_now().strftime("%H:%M"),
        "category": action,
        "earned":  coins if coins > 0 else 0,
        "penalty": abs(coins) if coins < 0 else 0,
        "net":     coins,
        "stars":   stars,
        "balance": d["balance"],
        "type":    "transaction",
    })
    save_state()

def log_daily_breakdown(date_str: str, breakdown: list, net: int, stars: float, balance_after: int):
    """
    breakdown = list of {"category": str, "earned": int, "penalty": int}
    Inserts each line into history so the ledger shows every item.
    """
    time_str = get_now().strftime("%H:%M")
    entries = []
    running = balance_after - net
    for item in breakdown:
        item_net   = item["earned"] - item["penalty"]
        running   += item_net
        entries.append({
            "date":     date_str,
            "time":     time_str,
            "category": item["category"],
            "earned":   item["earned"],
            "penalty":  item["penalty"],
            "net":      item_net,
            "stars":    item.get("stars", 0),
            "balance":  running,
            "type":     "daily_item",
            "log_date": date_str,
        })
    entries.insert(0, {
        "date": date_str, "time": time_str,
        "category": f"── Daily Log: {date_str} ──",
        "earned": 0, "penalty": 0, "net": net,
        "stars": stars, "balance": balance_after,
        "type": "daily_header", "log_date": date_str,
    })
    for e in reversed(entries):
        d["history"].insert(0, e)
    save_state()

def remove_today_history(date_str: str):
    """Remove all history rows belonging to today's log so resubmit is clean."""
    d["history"] = [h for h in d["history"] if h.get("log_date") != date_str]

# ============================================================
# RANK & HELPERS
# ============================================================
def get_rank(exp):
    if   exp >= 25000: return ("Ascendant Auditor","👑")
    elif exp >= 10000: return ("Grandmaster","💎")
    elif exp >= 5000:  return ("Expert","🟡")
    elif exp >= 1000:  return ("Professional","⚪")
    elif exp >= 250:   return ("Apprentice","🟤")
    else:              return ("Novice","📝")

def get_task_status(task_name, grace_days):
    last_date  = datetime.strptime(d["split_tasks"][task_name], "%Y-%m-%d").date()
    days_left  = ((last_date + timedelta(days=grace_days)) - get_now().date()).days
    if   days_left > 0:  return ("ok",      f"✦ Last done: {last_date} · Due in {days_left} day(s)")
    elif days_left == 0: return ("warn",    f"⚑ Last done: {last_date} · Due TODAY")
    else:                return ("overdue", f"✖ Was due {-days_left} day(s) ago — Penalty incoming!")

# ============================================================
# ACHIEVEMENT ENGINE
# ============================================================
def check_achievements():
    unlocked = d["unlocked_achievements"]
    def unlock(name):
        if name not in unlocked:
            unlocked.append(name)
            st.toast(f"{ACHIEVEMENTS[name][0]} Achievement Unlocked: {name}!")
    if len(d["daily_logs"]) > 0:   unlock("Day One")
    if d["super_stars"] >= 1:      unlock("First Star")
    if d["lifetime_exp"] >= 1000:  unlock("Bronze Rank")
    if d["lifetime_exp"] >= 10000: unlock("Gold Rank")
    if d["super_stars"] >= 50:     unlock("Audit Master")
    food_buys = sum(1 for h in d["history"] if h.get("category","").startswith("Bought ") and any(f in h.get("category","") for f in REAL_FOODS.keys()))
    if food_buys >= 3: unlock("Foodie")
    tier3 = {k for v in [VIRTUAL_SHOP["Tier 3 (Rare)"].keys()] for k in v}
    if any(i in tier3 for i in d["inventory"]): unlock("Relic Hunter")
    save_state()

# ============================================================
# HERO HEADER
# ============================================================
now = get_now()
rank_name, rank_icon = get_rank(d["lifetime_exp"])

st.markdown(f"""
<div class="vault-hero">
    <div class="vault-title">⚔ THE PERSONAL VAULT ⚔</div>
    <div class="vault-subtitle">Chronicle of Merit &amp; Discipline</div>
    <div class="vault-time">{now.strftime('%A, %B %d, %Y  ·  %I:%M %p')}  ·  Kathmandu, Nepal</div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="stat-grid">
    <div class="stat-card" style="--accent:#c9a84c">
        <span class="stat-icon">💰</span>
        <div class="stat-label">Coin Balance</div>
        <div class="stat-value">{d['balance']}</div>
        <div class="stat-sub">spending power</div>
    </div>
    <div class="stat-card" style="--accent:#88ccff">
        <span class="stat-icon">🌟</span>
        <div class="stat-label">Super Stars</div>
        <div class="stat-value">{round(d['super_stars'], 1)}</div>
        <div class="stat-sub">mastery tokens</div>
    </div>
    <div class="stat-card" style="--accent:#c8a0e8">
        <span class="stat-icon">{rank_icon}</span>
        <div class="stat-label">Current Rank</div>
        <div class="stat-value" style="font-size:1.05rem;padding-top:0.3rem">{rank_name}</div>
        <div class="stat-sub">{d['lifetime_exp']} lifetime EXP</div>
    </div>
    <div class="stat-card" style="--accent:#f09070">
        <span class="stat-icon">🔥</span>
        <div class="stat-label">Streak</div>
        <div class="stat-value">{d['streak']}</div>
        <div class="stat-sub">consecutive days</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# TUTORIAL
# ============================================================
with st.expander("📖  CODEX — Rules & Scoring System"):
    st.markdown("""
### Study Engine
- **3 pts per hour** of study.
- **Super Stars** for every hour *beyond* 5 hrs (weekdays) or 8 hrs (Saturdays).

### Digital Wellbeing
- Under 3 hrs mobile: **+5 pts** | Under 4 hrs: **+3 pts**
- Over 5 hrs: **−5 pts** · Over 6 hrs: **−5 pts per extra hour**
- Mobile in bed: **−5 pts** · Laptop entertainment > 0.5 hrs: **−5 pts/hr over**

### Wake & Sleep
- Wake by 5:30 AM: **+3 pts** | After 6:30 AM: **−5 pts/hr late**
- Sleep by 10:00 PM: **+3 pts** | After 10:30 PM: **−5 pts/hr late**

### Habits — Morning Brush +2 · Evening Brush +2 · Make Plan +2 · Silence +4

### Maintenance (Split-Day)
- **Bath** every 2 days · **Clean Room** every 2 days · **Laundry** every 3 days
- +3 pts within grace period · Miss deadline → **−5 pts**
""")

st.markdown('<div class="section-divider"><span class="section-title">✦ Daily Chronicle ✦</span></div>', unsafe_allow_html=True)

# ============================================================
# DAILY MASTER LOG FORM
# ============================================================
today = get_today_str()
if "last_log_result" in st.session_state:
    r = st.session_state.pop("last_log_result")
    net_col = "green" if r["net"] >= 0 else "red"
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #f5ead8, #ede0c4);
        border: 2px solid #c9a84c;
        border-radius: 6px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
        font-family: 'Cinzel', serif;
        text-align: center;
        box-shadow: 0 4px 20px rgba(201,168,76,0.25);
    ">
        <div style="font-size:1.8rem; margin-bottom:0.4rem;">⚔ Chronicle Sealed ⚔</div>
        <div style="display:flex; justify-content:center; gap:2rem; flex-wrap:wrap; margin-top:0.5rem;">
            <span style="color:#2a7a2a; font-size:1rem;">✦ Earned: +{r['earned']} pts</span>
            <span style="color:#aa3030; font-size:1rem;">✦ Penalties: -{r['penalty']} pts</span>
            <span style="color:{'#2a7a2a' if r['net']>=0 else '#aa3030'}; font-size:1.1rem; font-weight:700;">⚡ Net: {'+' if r['net']>=0 else ''}{r['net']} coins</span>
            <span style="color:#c9a84c; font-size:1rem;">⭐ Stars: +{r['stars']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

if today in d["daily_logs"]:
    st.info("⚔ Today's log is already sealed. Resubmit to recalculate all points.")

with st.form(f"daily_log_form_{st.session_state.form_key}"):
    st.markdown('<div class="form-section-head">I · Study Engine</div>', unsafe_allow_html=True)
    study_hrs = st.number_input("Total Study Hours — 3 pts per hour", min_value=0.0, max_value=24.0, step=0.5)

    st.markdown('<div class="form-section-head">II · Digital Wellbeing</div>', unsafe_allow_html=True)
    mob_col1, mob_col2 = st.columns([2, 1])
    with mob_col1:
        mobile_hrs  = st.number_input("Mobile Usage (total hours)", min_value=0.0, max_value=24.0, step=0.5)
        lap_ent_hrs = st.number_input("Laptop Entertainment (hours)", min_value=0.0, max_value=24.0, step=0.5)
    with mob_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        mobile_bed = st.checkbox("📵 Used mobile in bed? (−5 pts)")

    st.markdown('<div class="form-section-head">III · Wake &amp; Sleep</div>', unsafe_allow_html=True)
    tc1, tc2 = st.columns(2)
    with tc1: wake_time  = st.time_input("🌅 Wake Up Time",            value=time(5, 30))
    with tc2: sleep_time = st.time_input("🌙 Sleep Time (last night)",  value=time(22, 0))

    st.markdown('<div class="form-section-head">IV · Daily Habits</div>', unsafe_allow_html=True)
    hc1, hc2 = st.columns(2)
    with hc1:
        m_brush = st.checkbox("🪥 Morning Brush (+2 pts)")
        e_brush = st.checkbox("🪥 Evening Brush (+2 pts)")
    with hc2:
        plan   = st.checkbox("📋 Make Next Day Plan (+2 pts)")
        silent = st.checkbox("🧘 Remained Silent / Focused (+4 pts)")

    st.markdown('<div class="form-section-head">V · Maintenance Rites</div>', unsafe_allow_html=True)
    st.markdown("*Check if completed today. Unchecked = grace/penalty auto-calculated.*")
    for t_name, grace in [("Bath",2),("Clean Room",2),("Laundry",3)]:
        st_type, st_msg = get_task_status(t_name, grace)
        if st_type=="ok":       st.info(f"**{t_name}** (every {grace} days) — {st_msg}")
        elif st_type=="warn":   st.warning(f"**{t_name}** (every {grace} days) — {st_msg}")
        else:                   st.error(f"**{t_name}** (every {grace} days) — {st_msg}")
    bath_today    = st.checkbox("🛁 Took a Bath today")
    room_today    = st.checkbox("🧹 Cleaned my Room today")
    laundry_today = st.checkbox("👕 Did Laundry today")

    submit_log = st.form_submit_button("⚡  SEAL THE DAILY CHRONICLE")

if submit_log:
    # ── Rewind existing today log ──
    if today in d["daily_logs"]:
        old = d["daily_logs"][today]
        d["balance"]      -= old["net_points"]
        d["lifetime_exp"] -= max(0, old["net_points"])
        d["super_stars"]  -= old["stars"]
        d["split_tasks"]   = copy.deepcopy(old["previous_split_tasks"])
        remove_today_history(today)

    previous_split_tasks = copy.deepcopy(d["split_tasks"])
    breakdown = []

    # 1. Study
    threshold    = 8.0 if is_saturday() else 5.0
    earned_stars = 0.0
    if study_hrs > threshold:
        sp = int(threshold * 3); earned_stars = study_hrs - threshold
        breakdown.append({"category": f"📚 Study ({study_hrs}h — {sp} pts + ⭐{round(earned_stars,2)} stars)", "earned": sp, "penalty": 0, "stars": earned_stars})
    else:
        sp = int(study_hrs * 3)
        breakdown.append({"category": f"📚 Study ({study_hrs}h)", "earned": sp, "penalty": 0, "stars": 0})

    # 2. Mobile
    if mobile_hrs < 3:
        breakdown.append({"category":"📱 Mobile < 3hrs bonus","earned":5,"penalty":0})
    elif mobile_hrs < 4:
        breakdown.append({"category":"📱 Mobile < 4hrs bonus","earned":3,"penalty":0})
    elif mobile_hrs > 5:
        pen = 5 + (math.ceil(mobile_hrs - 6) * 5 if mobile_hrs > 6 else 0)
        breakdown.append({"category":f"📱 Mobile overuse ({mobile_hrs}h)","earned":0,"penalty":pen})
    else:
        breakdown.append({"category":f"📱 Mobile ({mobile_hrs}h) — neutral","earned":0,"penalty":0})
    if mobile_bed:
        breakdown.append({"category":"🛏️ Mobile in bed penalty","earned":0,"penalty":5})
    if lap_ent_hrs > 0.5:
        pen = math.ceil(lap_ent_hrs - 0.5) * 5
        breakdown.append({"category":f"💻 Laptop entertainment ({lap_ent_hrs}h)","earned":0,"penalty":pen})

    # 3. Wake / Sleep
    wake_f  = wake_time.hour  + wake_time.minute  / 60.0
    sleep_f = sleep_time.hour + sleep_time.minute / 60.0
    if sleep_f < 5.0: sleep_f += 24
    if wake_f <= 5.5:
        breakdown.append({"category":f"🌅 Early rise ({wake_time.strftime('%H:%M')})","earned":3,"penalty":0})
    elif wake_f > 6.5:
        pen = math.ceil(wake_f - 6.5) * 5
        breakdown.append({"category":f"🌅 Late rise ({wake_time.strftime('%H:%M')})","earned":0,"penalty":pen})
    else:
        breakdown.append({"category":f"🌅 Wake time ({wake_time.strftime('%H:%M')}) — neutral","earned":0,"penalty":0})
    if sleep_f <= 22.0:
        breakdown.append({"category":f"🌙 Early sleep ({sleep_time.strftime('%H:%M')})","earned":3,"penalty":0})
    elif sleep_f > 22.5:
        pen = math.ceil(sleep_f - 22.5) * 5
        breakdown.append({"category":f"🌙 Late sleep ({sleep_time.strftime('%H:%M')})","earned":0,"penalty":pen})
    else:
        breakdown.append({"category":f"🌙 Sleep ({sleep_time.strftime('%H:%M')}) — neutral","earned":0,"penalty":0})

    # 4. Habits
    if m_brush: breakdown.append({"category":"🪥 Morning Brush","earned":2,"penalty":0})
    if e_brush: breakdown.append({"category":"🪥 Evening Brush","earned":2,"penalty":0})
    if plan:    breakdown.append({"category":"📋 Next Day Plan","earned":2,"penalty":0})
    if silent:  breakdown.append({"category":"🧘 Silence / Focus","earned":4,"penalty":0})

    # 5. Maintenance
    for t_name, did_today, grace_days in [("Bath",bath_today,2),("Clean Room",room_today,2),("Laundry",laundry_today,3)]:
        last_dt = datetime.strptime(d["split_tasks"][t_name],"%Y-%m-%d").date()
        if did_today:
            d["split_tasks"][t_name] = today
            breakdown.append({"category":f"🧹 {t_name} ✓ done","earned":3,"penalty":0})
        else:
            days_since = (get_now().date() - last_dt).days
            if days_since <= grace_days:
                breakdown.append({"category":f"🧹 {t_name} (grace period)","earned":3,"penalty":0})
            else:
                breakdown.append({"category":f"🧹 {t_name} OVERDUE","earned":0,"penalty":5})

    # ── Totals ──
    total_earned  = sum(b["earned"]  for b in breakdown)
    total_penalty = sum(b["penalty"] for b in breakdown)
    net_points    = total_earned - total_penalty

    # ── Commit ──
    d["balance"]     += net_points
    d["super_stars"] += earned_stars
    if net_points > 0: d["lifetime_exp"] += net_points

    log_daily_breakdown(today, breakdown, net_points, earned_stars, d["balance"])
    d["daily_logs"][today] = {
        "net_points": net_points, "stars": earned_stars,
        "previous_split_tasks": previous_split_tasks,
    }

    last_date = datetime.strptime(d["last_login"],"%Y-%m-%d").date()
    if   get_now().date() - last_date == timedelta(days=1): d["streak"] += 1
    elif get_now().date() != last_date:                     d["streak"]  = 1
    d["last_login"] = today

    save_state(); check_achievements()
    st.session_state["last_log_result"] = {
        "earned": total_earned,
        "penalty": total_penalty,
        "net": net_points,
        "stars": round(earned_stars, 2),
    }
    st.session_state.form_key += 1
    st.rerun()

# ============================================================
# ITEMISED LEDGER  —  grouped by date, each category a row
# ============================================================
st.markdown('<div class="section-divider"><span class="section-title">✦ Account Statement ✦</span></div>', unsafe_allow_html=True)
with st.expander("🧾  STATEMENT OF ACCOUNT — Itemised Ledger"):
    if not d["history"]:
        st.markdown("<p style='color:#6a5a38;font-style:italic;text-align:center;padding:2rem'>No entries yet.</p>", unsafe_allow_html=True)
    else:
        from collections import defaultdict
        groups = defaultdict(list)
        for entry in d["history"]:
            groups[entry.get("date", "—")].append(entry)

        for date_key in sorted(groups.keys(), reverse=True):
            rows = groups[date_key]
            header = next((r for r in rows if r.get("type") == "daily_header"), None)
            # FIX: use .get("net", 0) to handle old entries missing the key
            net    = header["net"] if header else sum(r.get("net", 0) for r in rows)
            bal    = rows[0].get("balance", 0)
            net_cls = "pos" if net >= 0 else "neg"
            net_sign = "+" if net >= 0 else ""

            # Get a time string from the most recent row
            last_time = rows[0].get("time", "") if rows else ""

            items_html = ""
            for r in reversed(rows):
                if r.get("type") == "daily_header": continue
                e = r.get("earned", 0)
                p = r.get("penalty", 0)
                cat = r.get("category", "—")
                if e > 0 and p == 0:
                    pts_html = f'<span class="ledger-pts earn">+{e}</span>'
                elif p > 0 and e == 0:
                    pts_html = f'<span class="ledger-pts pen">−{p}</span>'
                elif e > 0 and p > 0:
                    pts_html = f'<span class="ledger-pts earn">+{e}</span> <span class="ledger-pts pen">−{p}</span>'
                else:
                    pts_html = f'<span class="ledger-pts zero">0</span>'
                star_bit = f' <span class="ledger-pts stars">⭐+{round(r.get("stars", 0), 2)}</span>' if r.get("stars", 0) > 0 else ""
                items_html += f'<div class="ledger-row"><span class="ledger-cat">{cat}</span>{pts_html}{star_bit}</div>'

            # Non-daily transactions (shop, manual)
            txn_rows = [r for r in rows if r.get("type") == "transaction"]
            for r in reversed(txn_rows):
                n = r.get("net", 0)
                pts_html = f'<span class="ledger-pts earn">+{n}</span>' if n >= 0 else f'<span class="ledger-pts pen">−{abs(n)}</span>'
                items_html += f'<div class="ledger-row"><span class="ledger-cat">{r.get("category", "—")}</span>{pts_html}</div>'

            st.markdown(f"""
<div class="ledger-group">
    <div class="ledger-group-header">
        <span class="ledger-group-date">📅 {date_key} · {last_time}</span>
        <span class="ledger-group-net {net_cls}">Net: {net_sign}{net} coins</span>
    </div>
    {items_html}
    <div class="ledger-balance-row">running balance → <span class="ledger-balance-val">💰 {bal}</span></div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# THE GRAND BAZAAR
# ============================================================
st.markdown('<div class="section-divider"><span class="section-title">✦ The Grand Bazaar ✦</span></div>', unsafe_allow_html=True)

tab_food, tab_virtual, tab_inv, tab_ach = st.tabs([
    "🍜  Nepali Foods", "🏺  Virtual Artifacts", "🎒  My Collection", "🏆  Achievements"
])

with tab_food:
    cols = st.columns(4)
    for idx, (item, (emoji, price)) in enumerate(REAL_FOODS.items()):
        with cols[idx % 4]:
            st.markdown(f"""
            <div class="shop-item">
                <span class="shop-item-emoji">{emoji}</span>
                <span class="shop-item-name">{item}</span>
                <span class="shop-item-price">💰 {price} coins</span>
            </div>""", unsafe_allow_html=True)
            # Count how many of this item already in inventory
            owned_count = d["inventory"].count(f"FOOD::{item}::{emoji}")
            if owned_count > 0:
                st.markdown(f"""
                <div style="text-align:center; margin-bottom:0.3rem;">
                    <span style="background:#2a7a2a; color:#fff; font-family:'Cinzel',serif;
                    font-size:0.65rem; padding:0.2rem 0.7rem; border-radius:10px;
                    letter-spacing:0.1em;">✓ ×{owned_count} in stash</span>
                </div>""", unsafe_allow_html=True)
            if st.button("Buy", key=f"f_{item}"):
                if d["balance"] >= price:
                    log_transaction(f"Bought {item}", -price)
                    d["inventory"].append(f"FOOD::{item}::{emoji}")
                    save_state()
                    check_achievements()
                    new_count = d["inventory"].count(f"FOOD::{item}::{emoji}")
                    st.toast(f"✦ {item} added! You now have ×{new_count} in stash {emoji}", icon="🛒")
                    st.rerun()
                else:
                    st.error(f"❌ Need {price - d['balance']} more coins!"))

with tab_virtual:
    for tier, items in VIRTUAL_SHOP.items():
        tier_css = TIER_CSS[tier]; tier_icon = TIER_ICONS[tier]
        st.markdown(f'<div><span class="tier-badge {tier_css}">{tier_icon} {tier}</span></div>', unsafe_allow_html=True)
        cols = st.columns(3)
        for idx, (item, (emoji, price)) in enumerate(items.items()):
            with cols[idx % 3]:
                owned = d["inventory"].count(item)
                owned_txt = f" · ×{owned} owned" if owned else ""
                st.markdown(f"""
                <div class="shop-item">
                    <span class="shop-item-emoji">{emoji}</span>
                    <span class="shop-item-name">{item}{'  ✅' if owned else ''}</span>
                    <span class="shop-item-price">💰 {price} coins{owned_txt}</span>
                </div>""", unsafe_allow_html=True)
                if owned > 0:
                    st.markdown(f"""
                    <div style="text-align:center; margin-bottom:0.3rem;">
                        <span style="background:#2a5a7a; color:#fff; font-family:'Cinzel',serif;
                        font-size:0.65rem; padding:0.2rem 0.7rem; border-radius:10px;
                        letter-spacing:0.1em;">✓ ×{owned} owned</span>
                    </div>""", unsafe_allow_html=True)
                if st.button("Acquire", key=f"v_{item}"):
                    if d["balance"] >= price:
                        d["inventory"].append(item)
                        log_transaction(f"Bought {item}", -price)
                        check_achievements()
                        st.balloons()
                        st.toast(f"✦ {item} acquired! {emoji}", icon="🏺")
                        st.rerun()
                    else:
                        st.error(f"❌ Need {price - d['balance']} more coins!")
        st.markdown("<br>", unsafe_allow_html=True)

with tab_inv:
    if not d["inventory"]:
        st.markdown("<p style='color:#6a5a38;font-style:italic;text-align:center;padding:3rem'>Your vault is empty. Start earning!</p>", unsafe_allow_html=True)
    else:
        # Split food vs virtual items
        food_items   = [i for i in d["inventory"] if i.startswith("FOOD::")]
        virtual_items = [i for i in d["inventory"] if not i.startswith("FOOD::")]

        # ── Food Stash ──
        if food_items:
            st.markdown("<div class='form-section-head'>🍜 Food Stash — Ready to Eat</div>", unsafe_allow_html=True)
            food_counts = Counter(food_items)
            all_virtual = {k:(e,p) for tier in VIRTUAL_SHOP.values() for k,(e,p) in tier.items()}
            for raw_item, count in food_counts.items():
                parts = raw_item.split("::")
                name  = parts[1] if len(parts) > 1 else raw_item
                emoji = parts[2] if len(parts) > 2 else "🍜"
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f'<div class="inv-item"><span>{emoji} {name}</span><span class="inv-count">×{count}</span></div>', unsafe_allow_html=True)
                with col2:
                    if st.button(f"Eat 🍽️", key=f"eat_{raw_item}"):
                        d["inventory"].remove(raw_item)
                        d["history"].insert(0, {
                            "date":     get_now().strftime("%Y-%m-%d"),
                            "time":     get_now().strftime("%H:%M"),
                            "category": f"🍽️ Ate {name}",
                            "earned":   0,
                            "penalty":  0,
                            "net":      0,
                            "stars":    0,
                            "balance":  d["balance"],
                            "type":     "transaction",
                        })
                        save_state()
                        check_achievements()
                        st.toast(f"✦ Enjoyed your {name}! {emoji}", icon="🍽️")
                        st.rerun()

        # ── Virtual Artifacts ──
        if virtual_items:
            st.markdown("<div class='form-section-head'>🏺 Virtual Artifacts</div>", unsafe_allow_html=True)
            counts = Counter(virtual_items)
            all_virtual = {k:(e,p) for tier in VIRTUAL_SHOP.values() for k,(e,p) in tier.items()}
            for item, count in counts.items():
                emoji = all_virtual.get(item, ("🏺", 0))[0]
                st.markdown(f'<div class="inv-item"><span>{emoji} {item}</span><span class="inv-count">×{count}</span></div>', unsafe_allow_html=True)

        if not food_items and not virtual_items:
            st.markdown("<p style='color:#6a5a38;font-style:italic;text-align:center;padding:3rem'>Your vault is empty. Start earning!</p>", unsafe_allow_html=True)

with tab_ach:
    unlocked_set   = set(d["unlocked_achievements"])
    unlocked_items = [(n,v) for n,v in ACHIEVEMENTS.items() if n in unlocked_set]
    locked_items   = [(n,v) for n,v in ACHIEVEMENTS.items() if n not in unlocked_set]
    if unlocked_items:
        st.markdown(f"<p style='font-family:Cinzel,serif;font-size:0.63rem;letter-spacing:0.25em;color:#c9a84c;margin-bottom:0.8rem'>UNLOCKED — {len(unlocked_items)}/{len(ACHIEVEMENTS)}</p>", unsafe_allow_html=True)
        cols = st.columns(2)
        for idx,(name,(icon,desc)) in enumerate(unlocked_items):
            with cols[idx%2]:
                st.markdown(f'<div class="ach-card unlocked"><span class="ach-icon">{icon}</span><div><span class="ach-name">{name}</span><span class="ach-desc">{desc}</span></div></div>', unsafe_allow_html=True)
    if locked_items:
        st.markdown(f"<p style='font-family:Cinzel,serif;font-size:0.63rem;letter-spacing:0.25em;color:#3a3020;margin:1.2rem 0 0.8rem'>LOCKED — {len(locked_items)} remaining</p>", unsafe_allow_html=True)
        cols = st.columns(2)
        for idx,(name,(icon,desc)) in enumerate(locked_items):
            with cols[idx%2]:
                st.markdown(f'<div class="ach-card"><span class="ach-icon" style="filter:grayscale(1);opacity:0.35">🔒</span><div><span class="ach-name">{name}</span><span class="ach-desc">{desc}</span></div></div>', unsafe_allow_html=True)

# ============================================================
# ADMIN PANEL
# ============================================================
st.markdown('<div class="section-divider"><span class="section-title">✦ Administration ✦</span></div>', unsafe_allow_html=True)
with st.expander("⚙️  SECURE ADMINISTRATION — Vault Master Controls"):

    st.markdown('<div class="form-section-head">Manual Coin Correction</div>', unsafe_allow_html=True)
    correction = st.number_input("Adjustment (+/−)", value=0, step=1, key="admin_corr")
    reason_txt = st.text_input("Reason — required", key="admin_reason")
    if st.button("⚡ Apply Override"):
        if not reason_txt.strip():
            st.error("A reason is required.")
        elif correction == 0:
            st.warning("⚠ Adjustment is 0 — nothing to apply.")
        else:
            log_transaction(f"MANUAL: {reason_txt}", correction)
            sign = "+" if correction > 0 else ""
            st.session_state["admin_toast"] = f"{sign}{correction} coins · {reason_txt}"
            st.rerun()

    if "admin_toast" in st.session_state:
        msg = st.session_state.pop("admin_toast")
        sign = "+" if not msg.startswith("-") else ""
        color = "#2a7a2a" if not msg.startswith("-") else "#aa3030"
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #f5ead8, #ede0c4);
            border: 2px solid {color};
            border-radius: 6px;
            padding: 1rem 1.5rem;
            margin: 0.5rem 0;
            font-family: 'Cinzel', serif;
            text-align: center;
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        ">
            <div style="font-size:1.3rem; color:{color}; font-weight:700;">
                ⚡ Override Applied
            </div>
            <div style="font-size:0.9rem; color:#3a2a10; margin-top:0.4rem;">
                {msg}
            </div>
            <div style="font-size:0.8rem; color:#7a6a48; margin-top:0.2rem;">
                New balance: 💰 {d['balance']} coins
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="form-section-head">🔄 Reset Today\'s Log Only</div>', unsafe_allow_html=True)
    st.markdown("<p style='color:#b0a07a;font-size:0.95rem'>Wipes <strong>only today's</strong> daily log entry and its coin/star effects. All previous days and inventory are untouched.</p>", unsafe_allow_html=True)
    if st.button("↩ Reset Today's Log"):
        if today in d["daily_logs"]:
            old = d["daily_logs"][today]
            d["balance"]      -= old["net_points"]
            d["lifetime_exp"] -= max(0, old["net_points"])
            d["super_stars"]  -= old["stars"]
            d["split_tasks"]   = copy.deepcopy(old["previous_split_tasks"])
            remove_today_history(today)
            del d["daily_logs"][today]
            save_state()
            st.success("Today's log has been reset. You can submit a fresh entry above.")
            st.rerun()
        else:
            st.info("No log found for today — nothing to reset.")

    st.markdown('<div class="form-section-head">Change Admin Password</div>', unsafe_allow_html=True)
    old_pw = st.text_input("Current Password", type="password", key="old_pw")
    new_pw = st.text_input("New Password",     type="password", key="new_pw")
    if st.button("🔑 Update Password"):
        if old_pw == d["admin_password"]:
            if new_pw: d["admin_password"] = new_pw; save_state(); st.success("Password updated.")
            else: st.error("New password cannot be empty.")
        else: st.error("Incorrect current password.")

    st.markdown('<div class="form-section-head" style="color:#aa5050;border-color:#3a1818">⚠ Danger Zone — Full Reset</div>', unsafe_allow_html=True)
    st.error("Permanently erases ALL data — coins, stars, history, inventory, streaks.")
    reset_pw = st.text_input("Admin Password to confirm", type="password", key="reset_pw")
    if st.button("💀 Destroy & Reset Everything"):
        if reset_pw == d["admin_password"]:
            st.session_state.user_data = get_default_data()
            save_db(st.session_state.user_data)
            st.warning("Vault wiped. A new chronicle begins.")
            st.rerun()
        elif reset_pw:
            st.error("Incorrect password — reset aborted.")
