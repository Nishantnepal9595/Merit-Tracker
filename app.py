import streamlit as st
import json
import os
import random
import pandas as pd
import pytz
import hashlib
from datetime import datetime, timedelta

# --- MOBILE UI OPTIMIZATION & CONFIG ---
st.set_page_config(page_title="Merit Tracker Pro", page_icon="📈", layout="wide")
hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

DB_FILE = "database.json"
CONFIG_FILE = "config.json"
NEPAL_TZ = pytz.timezone('Asia/Kathmandu')
ANTI_CHEAT_SALT = "Strict_Audit_2026_Nepal_Secret_Key" # The secret password for the wax seal

def get_nepal_time(): return datetime.now(NEPAL_TZ)
def get_nepal_date_str(): return str(get_nepal_time().date())
def get_current_season(): return get_nepal_time().strftime("%Y-%m") 

# --- ANTI-CHEAT HASHING ENGINE ---
def generate_signature(data):
    """Creates a cryptographic wax seal based on core stats."""
    raw_string = f"{data.get('balance', 0)}_{data.get('lifetime_exp', 0)}_{data.get('streak', 0)}_{ANTI_CHEAT_SALT}"
    return hashlib.sha256(raw_string.encode()).hexdigest()

# --- VIRTUAL COLLECTIBLES DICTIONARY ---
VIRTUAL_ITEMS = {
    "Common": ["Bronze Study Coin", "Digital Coffee Cup", "Focus Token"],
    "Rare": ["Silver Calculator", "Audit Ledger Page", "The 5AM Club Badge"],
    "Epic": ["Golden Gavel", "Einstein's Pen", "The Pomodoro Crown"],
    "Legendary": ["Diamond Play Button", "The Auditor's Seal", "Aura of Absolute Discipline"]
}

ITEM_PRICES = {
    "Bronze Study Coin": 50, "Digital Coffee Cup": 50, "Focus Token": 50,
    "Silver Calculator": 200, "Audit Ledger Page": 200, "The 5AM Club Badge": 200,
    "Golden Gavel": 1000, "Einstein's Pen": 1000, "The Pomodoro Crown": 1000,
    "Diamond Play Button": 5000, "The Auditor's Seal": 5000, "Aura of Absolute Discipline": 5000
}

# --- DEFAULT DATA SCHEMA ---
def get_default_data():
    base_data = {
        "balance": 0, 
        "lifetime_exp": 0, 
        "seasonal_exp": 0,
        "current_season": get_current_season(),
        "streak": 0, 
        "last_login": str(get_nepal_time().date() - timedelta(days=1)),
        "daily_tasks_date": get_nepal_date_str(),
        "completed_dailies": [],
        "history": [], 
        "daily_earnings": {}, 
        "screen_time_log": {}, 
        "screen_time_points_awarded": {}, 
        "baseline_screen_time": None, 
        "inventory": [], 
        "unlocked_achievements": [],
        "tampered": False, # Anti-Cheat Flag
        "signature": "",   # The saved wax seal
        "override_tracker": { 
            "date": get_nepal_date_str(), "daily_count": 0,
            "month": get_current_season(), "monthly_count": 0
        },
        "shop_items": { 
            "1x Sausage": 10, "Plate of Momo": 25, "Evening Out": 150, "Guilt-Free YouTube (1hr)": 50, 
            "Cafe Study": 50, "Junk Food": 60, "Chocolate": 60, "New Book or Clothing": 300
        },
        "custom_tasks": { 
            "Morning": {"Woke up BEFORE 5:30 AM": 2, "Morning Brush": 1, "Took a Bath": 2},
            "Evening": {"Dinner at home": 2, "Evening Brush": 1, "Sleep by 10 PM": 2},
            "Chores": {"Chores / Laundry": 3},
            "Penalties": {
                "Sleep after 10:30 PM": -5, "Woke up AFTER 6:00 AM": -1, "No Bath for 2 Days": -5, 
                "Phone in bed": -3, "Phone face-up on desk": -2, "TikTok/Shorts > 30 mins": -3, "Screen meal": -1
            }
        }
    }
    base_data["signature"] = generate_signature(base_data)
    return base_data

# --- DATABASE MANAGEMENT ---
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    return {"users": {}}

def save_db(db):
    with open(DB_FILE, "w") as f: json.dump(db, f)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f: return json.load(f)
    return {"remembered_user": None}

def save_config(config):
    with open(CONFIG_FILE, "w") as f: json.dump(config, f)

# --- SESSION INITIALIZATION & ANTI-CHEAT CHECK ---
if 'logged_in' not in st.session_state:
    config = load_config()
    if config["remembered_user"]:
        st.session_state.logged_in = True
        st.session_state.username = config["remembered_user"]
    else:
        st.session_state.logged_in = False
        st.session_state.username = None

if st.session_state.logged_in:
    db = load_db()
    today_str = get_nepal_date_str()
    current_season = get_current_season()
    user_data = db["users"][st.session_state.username]["data"]
    
    defaults = get_default_data()
    for key in defaults:
        if key not in user_data: user_data[key] = defaults[key]
        
    # ANTI-CHEAT VALIDATION
    if not user_data.get("tampered", False):
        expected_sig = generate_signature(user_data)
        saved_sig = user_data.get("signature", "")
        # Only check if it's not a brand new un-hashed account
        if saved_sig and saved_sig != expected_sig:
            user_data["tampered"] = True 
            
    if user_data.get("daily_tasks_date") != today_str:
        user_data["completed_dailies"] = []
        user_data["daily_tasks_date"] = today_str
    
    if user_data.get("current_season") != current_season:
        user_data["seasonal_exp"] = 0
        user_data["current_season"] = current_season
        
    if user_data["override_tracker"].get("date") != today_str:
        user_data["override_tracker"]["date"] = today_str
        user_data["override_tracker"]["daily_count"] = 0
    if user_data["override_tracker"].get("month") != current_season:
        user_data["override_tracker"]["month"] = current_season
        user_data["override_tracker"]["monthly_count"] = 0
        
    db["users"][st.session_state.username]["data"] = user_data
    save_db(db)
    st.session_state.user_data = user_data

def save_user_data():
    # Generate a fresh seal before saving
    st.session_state.user_data["signature"] = generate_signature(st.session_state.user_data)
    db = load_db()
    db["users"][st.session_state.username]["data"] = st.session_state.user_data
    save_db(db)

# --- RANKING SYSTEM ---
RANKS = [
    ("Bronze III 🟤", 0, 200), ("Bronze II 🟤", 200, 500), ("Bronze I 🟤", 500, 1000),
    ("Silver III ⚪", 1000, 2000), ("Silver II ⚪", 2000, 3500), ("Silver I ⚪", 3500, 5000),
    ("Gold III 🟡", 5000, 7500), ("Gold II 🟡", 7500, 10000), ("Gold I 🟡", 10000, 15000),
    ("Diamond 💎", 15000, 999999)
]

def get_rank_info(exp):
    if st.session_state.user_data.get("tampered"): return ("⚠️ DISHONORED (Data Altered) ⚠️", 0, 999999)
    for r in RANKS:
        if exp >= r[1] and exp < r[2]: return r
    return RANKS[-1] 

# --- ACHIEVEMENT ENGINE ---
ACHIEVEMENTS = {
    "First Blood": {"desc": "Earn your first points", "req": lambda d: d["lifetime_exp"] > 0},
    "Consistent Cadet": {"desc": "Hit a 3-day streak", "req": lambda d: d["streak"] >= 3},
    "Iron Will": {"desc": "Hit a 7-day streak", "req": lambda d: d["streak"] >= 7},
    "Centurion": {"desc": "Earn 100 points in a single day", "req": lambda d: d["daily_earnings"].get(get_nepal_date_str(), 0) >= 100},
    "Collector": {"desc": "Find your first Virtual Relic", "req": lambda d: len(d["inventory"]) > 0},
    "Audit Manager": {"desc": "Reach 5,000 Lifetime EXP", "req": lambda d: d["lifetime_exp"] >= 5000}
}

def check_achievements():
    if st.session_state.user_data.get("tampered"): return # Cheaters get no achievements
    for ach, info in ACHIEVEMENTS.items():
        if ach not in st.session_state.user_data["unlocked_achievements"]:
            if info["req"](st.session_state.user_data):
                st.session_state.user_data["unlocked_achievements"].append(ach)
                st.toast(f"🏆 ACHIEVEMENT UNLOCKED: {ach}!")
                save_user_data()

# --- AUTH UI ---
if not st.session_state.logged_in:
    st.title("🛡️ Merit Tracker RPG")
    tab1, tab2 = st.tabs(["Log In", "Create Account"])
    with tab1:
        login_user = st.text_input("Username", key="log_user")
        login_pass = st.text_input("Password", type="password", key="log_pass")
        remember = st.checkbox("Remember this device")
        if st.button("Log In", use_container_width=True):
            db = load_db()
            if login_user in db["users"] and db["users"][login_user]["password"] == login_pass:
                if remember: save_config({"remembered_user": login_user})
                st.session_state.logged_in = True
                st.session_state.username = login_user
                st.rerun()
            else: st.error("Invalid credentials.")
    with tab2:
        reg_user = st.text_input("Choose Username", key="reg_user")
        reg_pass = st.text_input("Choose Password", type="password", key="reg_pass")
        if st.button("Create Account", use_container_width=True):
            db = load_db()
            if reg_user in db["users"]: st.error("Username exists!")
            elif reg_user == "" or reg_pass == "": st.error("Fields cannot be empty.")
            else:
                db["users"][reg_user] = {"password": reg_pass, "data": get_default_data()}
                save_db(db)
                st.success("Account created! You can now log in.")
    st.stop()

# --- CORE LOGIC ENGINE ---
def add_points(amount, reason, bypass_cap=False):
    if st.session_state.user_data.get("tampered"):
        st.error("SYSTEM LOCKED. Data tampering detected. Profile reset required.")
        return 0

    today_str = get_nepal_date_str()
    if today_str not in st.session_state.user_data["daily_earnings"]:
        st.session_state.user_data["daily_earnings"][today_str] = 0

    actual_amount = amount
    if amount > 0 and not bypass_cap:
        current_earned = st.session_state.user_data["daily_earnings"].get(today_str, 0)
        if current_earned >= 100: 
            st.warning("🛑 Daily limit of 100 points reached!")
            return 0
        elif current_earned + amount > 100:
            actual_amount = 100 - current_earned
            st.warning(f"⚠️ Daily limit approaching! Only added {actual_amount} points.")
        st.session_state.user_data["daily_earnings"][today_str] += actual_amount
        st.session_state.user_data["lifetime_exp"] += actual_amount 
        st.session_state.user_data["seasonal_exp"] += actual_amount
    elif amount < 0:
        current_earned = st.session_state.user_data["daily_earnings"].get(today_str, 0)
        st.session_state.user_data["daily_earnings"][today_str] = max(0, current_earned + amount)

    st.session_state.user_data["balance"] += actual_amount
    
    if actual_amount != 0:
        now = get_nepal_time().strftime("%Y-%m-%d %I:%M %p")
        st.session_state.user_data["history"].insert(0, {"Time": now, "Action": reason, "Points": actual_amount})
        st.session_state.user_data["history"] = st.session_state.user_data["history"][:50] 
        check_achievements()
        save_user_data()
    return actual_amount

def claim_daily(task_name, points):
    if task_name in st.session_state.user_data["completed_dailies"]:
        st.warning(f"Hold up! You already claimed '{task_name}' today.")
    else:
        earned = add_points(points, task_name)
        if earned > 0 or points < 0: 
            st.session_state.user_data["completed_dailies"].append(task_name)
            save_user_data()
            if points > 0: st.success(f"Claimed: {task_name} (+{earned} pts)")
            else: st.error(f"Penalty: {task_name} ({points} pts)")

# --- UI DASHBOARD HEADER ---
col_title, col_logout = st.columns([8, 2])
with col_title:
    st.title(f"🛡️ {st.session_state.username}")
with col_logout:
    st.write("")
    if st.button("🚪 Log Out", use_container_width=True):
        save_config({"remembered_user": None})
        st.session_state.logged_in = False
        st.rerun()

# TAMPER LOCKOUT UI
if st.session_state.user_data.get("tampered"):
    st.error("🚨 CRITICAL ERROR: DATA TAMPERING DETECTED 🚨")
    st.warning("The cryptographic signature on your save file is broken. Your account is locked. Go to Settings to Reset Your Profile.")

rank_name, rank_min, rank_max = get_rank_info(st.session_state.user_data["lifetime_exp"])
progress_val = min(1.0, max(0.0, (st.session_state.user_data["lifetime_exp"] - rank_min) / (rank_max - rank_min))) if rank_max < 999999 else 1.0

st.markdown(f"**Rank:** {rank_name} | **Lifetime EXP:** {st.session_state.user_data['lifetime_exp']} / {rank_max if rank_max < 999999 else 'MAX'}")
st.progress(progress_val)
current_date = get_nepal_time().date()
st.caption(f"📅 **Season [{st.session_state.user_data['current_season']}] EXP:** {st.session_state.user_data['seasonal_exp']}  |  ⏳ {(datetime(2026, 12, 1).date() - current_date).days} Days to Dec 1, 2026")

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Coins", f"{st.session_state.user_data['balance']}")
col2.metric("🔥 Streak", f"{st.session_state.user_data['streak']}")
baseline = st.session_state.user_data.get("baseline_screen_time")
logs = st.session_state.user_data.get("screen_time_log", {})
avg_screen_time = sum(list(logs.values())[-7:]) / len(list(logs.values())[-7:]) if len(logs) > 0 else (baseline if baseline else 0.0)
col3.metric("📱 Scr Time", f"{avg_screen_time:.1f}h" if baseline else "Setup")
col4.metric("📈 Today", f"{st.session_state.user_data['daily_earnings'].get(today_str, 0)}/100")

# --- SCREEN TIME TRACKER ---
with st.expander("📱 Log Screen Time", expanded=(baseline is None)):
    if baseline is None:
        st.info("👋 Set your starting Screen Time baseline.")
        new_baseline = st.number_input("Starting daily screen time (Hours)", min_value=1.0, max_value=24.0, value=9.5, step=0.5)
        if st.button("Set Baseline"):
            st.session_state.user_data["baseline_screen_time"] = new_baseline
            save_user_data()
            st.rerun()
    else:
        st_col1, st_col2 = st.columns([2, 1])
        with st_col1:
            current_val = st.session_state.user_data["screen_time_log"].get(today_str, avg_screen_time)
            today_hours = st.number_input("Log Today's Hours (+3 pts/hr saved)", min_value=0.0, max_value=24.0, value=float(current_val), step=0.5)
        with st_col2:
            st.write("")
            st.write("")
            if st.button("Submit Time"):
                diff = avg_screen_time - today_hours
                new_points = int(diff * 3) 
                if today_str in st.session_state.user_data["screen_time_points_awarded"]:
                    old_points = st.session_state.user_data["screen_time_points_awarded"][today_str]
                    st.session_state.user_data["balance"] -= old_points
                    if old_points > 0:
                        st.session_state.user_data["daily_earnings"][today_str] = max(0, st.session_state.user_data["daily_earnings"].get(today_str,0) - old_points)
                earned = add_points(new_points, f"Screen Time ({today_hours}h)", bypass_cap=False)
                st.session_state.user_data["screen_time_log"][today_str] = today_hours
                st.session_state.user_data["screen_time_points_awarded"][today_str] = earned
                save_user_data()
                st.rerun()

# --- TASKS & STUDY ---
st.markdown("---")
earn_col1, earn_col2, earn_col3 = st.columns(3)
tasks = st.session_state.user_data["custom_tasks"]
with earn_col1:
    st.subheader("☀️ Morning")
    for task, pts in tasks.get("Morning", {}).items():
        if st.button(f"{task} [+{pts}]", key=task): claim_daily(task, pts)
with earn_col2:
    st.subheader("🌙 Evening")
    for task, pts in tasks.get("Evening", {}).items():
        if st.button(f"{task} [+{pts}]", key=task): claim_daily(task, pts)
with earn_col3:
    st.subheader("🧹 Chores")
    for task, pts in tasks.get("Chores", {}).items():
        if st.button(f"{task} [+{pts}]", key=task): claim_daily(task, pts)

with st.expander("⏱️ Deep Work & Pomodoro"):
    pomo_sessions = st.number_input("50-Min Pomodoros [+3]", min_value=0, max_value=10, value=0)
    lectures = st.number_input("Lectures [+2]", min_value=0, max_value=15, value=0)
    numericals = st.number_input("Numericals [+1]", min_value=0, max_value=50, value=0)
    if st.button("Log Study Session", use_container_width=True):
        earned = (pomo_sessions * 3) + (lectures * 2) + (numericals * 1)
        if earned > 0:
            add_points(earned, f"Study: {pomo_sessions}P, {lectures}L, {numericals}N")
            st.success("Study logged!")

st.markdown("---")
st.subheader("⚠️ Penalties")
pen_cols = st.columns(3)
col_idx = 0
for task, pts in tasks.get("Penalties", {}).items():
    with pen_cols[col_idx % 3]:
        if st.button(f"{task} [{pts}]", key=task): claim_daily(task, pts)
    col_idx += 1

# --- MYSTERY SHOP & GACHA ---
st.markdown("---")
if 'show_shop' not in st.session_state: st.session_state.show_shop = False
if st.button("🛒 OPEN RPG SHOP & GACHA", use_container_width
