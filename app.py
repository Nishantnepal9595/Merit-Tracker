import streamlit as st
import json
import os
import random
import pandas as pd
from datetime import date, datetime, timedelta

st.set_page_config(page_title="Merit Tracker Pro", page_icon="📈", layout="wide")

DB_FILE = "database.json"
CONFIG_FILE = "config.json"

# --- DEFAULT DATA SCHEMA ---
def get_default_data():
    today_str = str(date.today())
    return {
        "balance": 0, 
        "lifetime_exp": 0, # NEW: Tracks total points ever earned
        "streak": 0, 
        "last_login": str(date.today() - timedelta(days=1)),
        "daily_tasks_date": today_str,
        "completed_dailies": [],
        "history": [], 
        "daily_earnings": {}, 
        "screen_time_log": {}, 
        "screen_time_points_awarded": {}, 
        "baseline_screen_time": None, 
        "shop_items": { 
            "1x Sausage": 5, "Plate of Momo": 15, "Guilt-Free YouTube (1hr)": 20, 
            "Cafe Study": 25, "Junk Food": 30, "Chocolate": 30, "Evening Out": 15, "New Book": 60
        },
        "custom_tasks": { 
            "Morning": {"Woke up BEFORE 5:30 AM": 2, "Morning Brush": 1, "Took a Bath": 2},
            "Evening": {"Dinner at home": 2, "Evening Brush": 1, "Sleep by 10 PM": 2},
            "Chores": {"Chores / Laundry": 3},
            "Penalties": {"Sleep after 10:30 PM": -5, "Woke up AFTER 6:00 AM": -1, "No Bath for 2 Days": -5, "Phone in bed": -3}
        }
    }

# --- DATABASE MANAGEMENT ---
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {"users": {}}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"remembered_user": None}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

# --- SESSION INITIALIZATION ---
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
    today_str = str(date.today())
    user_data = db["users"][st.session_state.username]["data"]
    
    defaults = get_default_data()
    for key in defaults:
        if key not in user_data:
            user_data[key] = defaults[key]
            
    if user_data.get("daily_tasks_date") != today_str:
        user_data["completed_dailies"] = []
        user_data["daily_tasks_date"] = today_str
        db["users"][st.session_state.username]["data"] = user_data
        save_db(db)
    st.session_state.user_data = user_data

def save_user_data():
    db = load_db()
    db["users"][st.session_state.username]["data"] = st.session_state.user_data
    save_db(db)

# --- RANK SYSTEM ---
def get_rank(exp):
    if exp >= 5000: return "Managing Partner 🏛️"
    elif exp >= 2500: return "Audit Manager 📊"
    elif exp >= 1000: return "Senior Associate 💼"
    elif exp >= 250: return "Junior Associate 📝"
    else: return "Audit Intern ☕"

# --- AUTHENTICATION UI ---
if not st.session_state.logged_in:
    st.title("🛡️ The Merit Point System")
    st.markdown("---")
    tab1, tab2 = st.tabs(["Log In", "Create Account"])
    with tab1:
        st.subheader("Welcome Back")
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
            else: st.error("Invalid username or password.")
    with tab2:
        st.subheader("New Cadet Registration")
        reg_user = st.text_input("Choose Username", key="reg_user")
        reg_pass = st.text_input("Choose Password", type="password", key="reg_pass")
        if st.button("Create Account", use_container_width=True):
            db = load_db()
            if reg_user in db["users"]: st.error("Username already exists!")
            elif reg_user == "" or reg_pass == "": st.error("Fields cannot be empty.")
            else:
                db["users"][reg_user] = {"password": reg_pass, "data": get_default_data()}
                save_db(db)
                st.success("Account created! You can now log in.")
    st.stop()

# --- CORE LOGIC ENGINE ---
def add_points(amount, reason, bypass_cap=False):
    today_str = str(date.today())
    if today_str not in st.session_state.user_data["daily_earnings"]:
        st.session_state.user_data["daily_earnings"][today_str] = 0

    actual_amount = amount

    if amount > 0 and not bypass_cap:
        current_earned = st.session_state.user_data["daily_earnings"].get(today_str, 0)
        if current_earned >= 50:
            st.warning("🛑 Daily limit of 50 points reached!")
            return 0
        elif current_earned + amount > 50:
            actual_amount = 50 - current_earned
            st.warning(f"⚠️ Daily limit approaching! Only added {actual_amount} points.")
        st.session_state.user_data["daily_earnings"][today_str] += actual_amount
        st.session_state.user_data["lifetime_exp"] += actual_amount # ADD TO LIFETIME EXP
    elif amount < 0:
        current_earned = st.session_state.user_data["daily_earnings"].get(today_str, 0)
        st.session_state.user_data["daily_earnings"][today_str] = max(0, current_earned + amount)

    st.session_state.user_data["balance"] += actual_amount
    
    if actual_amount != 0:
        now = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        st.session_state.user_data["history"].insert(0, {"Time": now, "Action": reason, "Points": actual_amount})
        st.session_state.user_data["history"] = st.session_state.user_data["history"][:50] 
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

# --- STREAK LOGIC ---
today_str = str(date.today())
last_login_str = st.session_state.user_data["last_login"]
last_login_date = datetime.strptime(last_login_str, "%Y-%m-%d").date()

if today_str != last_login_str:
    if date.today() - last_login_date == timedelta(days=1): st.session_state.user_data["streak"] += 1
    else: st.session_state.user_data["streak"] = 1
    st.session_state.user_data["last_login"] = today_str
    save_user_data()

# --- CALCULATE SCREEN TIME AVERAGE ---
baseline = st.session_state.user_data.get("baseline_screen_time")
logs = st.session_state.user_data.get("screen_time_log", {})
if len(logs) > 0:
    recent_logs = list(logs.values())[-7:]
    avg_screen_time = sum(recent_logs) / len(recent_logs)
elif baseline is not None:
    avg_screen_time = baseline
else:
    avg_screen_time = 0.0 

# --- UI DASHBOARD HEADER ---
st.title(f"🛡️ {st.session_state.username}'s Tracker")
current_rank = get_rank(st.session_state.user_data.get("lifetime_exp", 0))
st.subheader(f"Current Rank: **{current_rank}** | Lifetime EXP: {st.session_state.user_data.get('lifetime_exp', 0)}")

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Wallet Balance", f"{st.session_state.user_data['balance']} pts")
col2.metric("🔥 Daily Streak", f"{st.session_state.user_data['streak']} Days")
if baseline is not None: col3.metric("📱 Wkly Avg Screen", f"{avg_screen_time:.1f} Hrs")
else: col3.metric("📱 Wkly Avg Screen", "Needs Setup")
today_earned = st.session_state.user_data['daily_earnings'].get(today_str, 0)
col4.metric("📈 Today's Earnings", f"{today_earned} / 50 Max")

with st.expander("📊 View 30-Day Activity Heatmap"):
    last_30_days = [(date.today() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(29, -1, -1)]
    chart_data = {"Date": [], "Points Earned": []}
    for d in last_30_days:
        chart_data["Date"].append(d)
        chart_data["Points Earned"].append(st.session_state.user_data["daily_earnings"].get(d, 0))
    st.bar_chart(pd.DataFrame(chart_data).set_index("Date"), color="#4CAF50")

st.markdown("---")

# --- SCREEN TIME ONBOARDING & TRACKER ---
st.header("📱 Screen Time Tracker")
if baseline is None:
    st.info("👋 Welcome! Set your starting Screen Time baseline.")
    new_baseline = st.number_input("My starting daily screen time (Hours)", min_value=1.0, max_value=24.0, value=9.5, step=0.5)
    if st.button("Set My Baseline"):
        st.session_state.user_data["baseline_screen_time"] = new_baseline
        save_user_data()
        st.rerun()
else:
    st_col1, st_col2 = st.columns([2, 1])
    with st_col1:
        current_val = st.session_state.user_data["screen_time_log"].get(today_str, avg_screen_time)
        today_hours = st.number_input("Log Today's Screen Time (Hours)", min_value=0.0, max_value=24.0, value=float(current_val), step=0.5)

    with st_col2:
        st.write("")
        st.write("")
        if st.button("Submit / Update Screen Time"):
            diff = avg_screen_time - today_hours
            new_points = int(diff * 3) 
            if today_str in st.session_state.user_data["screen_time_points_awarded"]:
                old_points = st.session_state.user_data["screen_time_points_awarded"][today_str]
                st.session_state.user_data["balance"] -= old_points
                if old_points > 0:
                    st.session_state.user_data["daily_earnings"][today_str] = max(0, st.session_state.user_data["daily_earnings"].get(today_str,0) - old_points)
            
            earned = add_points(new_points, f"Screen Time ({today_hours}h logged)", bypass_cap=False)
            st.session_state.user_data["screen_time_log"][today_str] = today_hours
            st.session_state.user_data["screen_time_points_awarded"][today_str] = earned
            save_user_data()
            st.rerun()

st.markdown("---")

# --- DYNAMIC TASK ENGINE & POMODORO ---
st.header("⚡ Tasks & Deep Work")
earn_col1, earn_col2, earn_col3 = st.columns(3)
tasks = st.session_state.user_data["custom_tasks"]

with earn_col1:
    st.subheader("☀️ Morning")
    for task, pts in tasks.get("Morning", {}).items():
        if st.button(f"{task} [+{pts}]"): claim_daily(task, pts)

with earn_col2:
    st.subheader("🌙 Evening")
    for task, pts in tasks.get("Evening", {}).items():
        if st.button(f"{task} [+{pts}]"): claim_daily(task, pts)

with earn_col3:
    st.subheader("⏱️ Pomodoro & Study")
    pomo_sessions = st.number_input("50-Min Deep Work Sessions [+3 pts each]", min_value=0, max_value=10, value=0)
    numericals = st.number_input("Numericals [+1]", min_value=0, max_value=50, value=0)
    if st.button("Log Study Session"):
        earned = (pomo_sessions * 3) + (numericals * 1)
        if earned > 0:
            add_points(earned, f"Study: {pomo_sessions} Pomodoros, {numericals} Num")
            st.success("Study logged!")

# --- DEMERITS ---
st.markdown("---")
st.subheader("⚠️ Penalties")
pen_cols = st.columns(4)
col_idx = 0
for task, pts in tasks.get("Penalties", {}).items():
    with pen_cols[col_idx % 4]:
        if st.button(f"{task} [{pts}]"): claim_daily(task, pts)
    col_idx += 1

# --- HIDDEN SHOP & MYSTERY BOX ---
st.markdown("---")
if 'show_shop' not in st.session_state: st.session_state.show_shop = False
if st.button("🛒 OPEN MERIT SHOP", use_container_width=True): st.session_state.show_shop = not st.session_state.show_shop

if st.session_state.show_shop:
    st.info(f"Wallet Balance: **{st.session_state.user_data['balance']} points**")
    
    # MYSTERY BOX GAMBLE
    if st.button("🎲 Buy Mystery Box (15 pts)", type="primary", use_container_width=True):
        if st.session_state.user_data["balance"] >= 15:
            add_points(-15, "Bought: Mystery Box", bypass_cap=True)
            roll = random.random()
            if roll < 0.05: # 5% Epic
                st.balloons()
                add_points(40, "Mystery Box: EPIC WIN", bypass_cap=True)
                st.success("🎉 EPIC WIN! You found 40 Points inside!")
            elif roll < 0.40: # 35% Rare
                st.success("✨ RARE WIN! You won a Cafe Study Session voucher!")
            else: # 60% Common
                add_points(5, "Mystery Box: Common Refund", bypass_cap=True)
                st.info("📦 Common pull. You got 1x Sausage (or 5 points back).")
        else:
            st.warning("Not enough points for a Mystery Box.")

    st.markdown("---")
    shop_items = st.session_state.user_data["shop_items"]
    shop_cols = st.columns(4)
    c_idx = 0
    for item_name, item_cost in shop_items.items():
        with shop_cols[c_idx % 4]:
            if st.button(f"{item_name}\n({item_cost} pts)"):
                if st.session_state.user_data["balance"] >= item_cost:
                    add_points(-item_cost, f"Bought: {item_name}", bypass_cap=True)
                    st.balloons() 
                    st.success(f"Purchased: {item_name}!")
                else:
                    st.warning("Not enough points.")
        c_idx += 1

st.markdown("---")
if st.button("🚪 Log Out"):
    save_config({"remembered_user": None})
    st.session_state.logged_in = False
    st.session_state.username = None
    st.rerun()