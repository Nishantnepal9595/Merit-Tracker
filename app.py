import streamlit as st
import json
import os
import random
import pandas as pd
import pytz
from datetime import datetime, timedelta

st.set_page_config(page_title="Merit Tracker Pro", page_icon="📈", layout="wide")

DB_FILE = "database.json"
CONFIG_FILE = "config.json"

# --- NEPAL TIMEZONE HANDLING ---
NEPAL_TZ = pytz.timezone('Asia/Kathmandu')

def get_nepal_time():
    return datetime.now(NEPAL_TZ)

def get_nepal_date_str():
    return str(get_nepal_time().date())

# --- DEFAULT DATA SCHEMA ---
def get_default_data():
    today_str = get_nepal_date_str()
    return {
        "balance": 0, 
        "lifetime_exp": 0, 
        "streak": 0, 
        "last_login": str(get_nepal_time().date() - timedelta(days=1)),
        "daily_tasks_date": today_str,
        "completed_dailies": [],
        "history": [], 
        "daily_earnings": {}, 
        "screen_time_log": {}, 
        "screen_time_points_awarded": {}, 
        "baseline_screen_time": None, 
        "shop_items": { 
            "1x Sausage": 5, "Plate of Momo": 15, "Evening Out": 15, "Guilt-Free YouTube (1hr)": 20, 
            "Cafe Study": 25, "Junk Food": 30, "Chocolate": 30, "New Book or Clothing": 60
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
    today_str = get_nepal_date_str()
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
    today_str = get_nepal_date_str()
    if today_str not in st.session_state.user_data["daily_earnings"]:
        st.session_state.user_data["daily_earnings"][today_str] = 0

    actual_amount = amount

    # 50-POINT MAX CAP WITH REFUND FIX
    if amount > 0 and not bypass_cap:
        current_earned = st.session_state.user_data["daily_earnings"].get(today_str, 0)
        if current_earned >= 50:
            st.warning("🛑 Daily limit of 50 points reached!")
            return 0
        elif current_earned + amount > 50:
            actual_amount = 50 - current_earned
            st.warning(f"⚠️ Daily limit approaching! Only added {actual_amount} points.")
        st.session_state.user_data["daily_earnings"][today_str] += actual_amount
        st.session_state.user_data["lifetime_exp"] += actual_amount 
    elif amount < 0:
        current_earned = st.session_state.user_data["daily_earnings"].get(today_str, 0)
        st.session_state.user_data["daily_earnings"][today_str] = max(0, current_earned + amount)

    st.session_state.user_data["balance"] += actual_amount
    
    if actual_amount != 0:
        now = get_nepal_time().strftime("%Y-%m-%d %I:%M %p")
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
today_str = get_nepal_date_str()
last_login_str = st.session_state.user_data["last_login"]
last_login_date = datetime.strptime(last_login_str, "%Y-%m-%d").date()
current_date = get_nepal_time().date()

if today_str != last_login_str:
    if current_date - last_login_date == timedelta(days=1): st.session_state.user_data["streak"] += 1
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
col_title, col_logout, col_cal = st.columns([6, 1, 2])

with col_title:
    st.title(f"🛡️ {st.session_state.username}'s Tracker")
    current_rank = get_rank(st.session_state.user_data.get("lifetime_exp", 0))
    st.subheader(f"Rank: **{current_rank}** | Lifetime EXP: {st.session_state.user_data.get('lifetime_exp', 0)}")
    
    target_date = datetime(2026, 12, 1).date()
    days_left = (target_date - current_date).days
    
    quotes = [
        "Discipline is choosing between what you want now and what you want most.",
        "Suffer the pain of discipline, or suffer the pain of regret.",
        "Your future is created by what you do today, not tomorrow.",
        "Don't stop when you're tired. Stop when you're done."
    ]
    daily_quote = quotes[current_date.toordinal() % len(quotes)]
    
    st.markdown(f"**⏳ {days_left} Days until Dec 1, 2026**")
    st.caption(f"💡 *\"{daily_quote}\"*")

with col_logout:
    st.write("")
    if st.button("🚪 Log Out"):
        save_config({"remembered_user": None})
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()

with col_cal:
    month = get_nepal_time().strftime("%b").upper()
    day = get_nepal_time().strftime("%d")
    weekday = get_nepal_time().strftime("%A").upper()
    cal_html = f"""
    <div style="float: right; border: 2px solid #ff4b4b; border-radius: 10px; padding: 10px; width: 100px; text-align: center; background-color: rgba(255, 75, 75, 0.1);">
        <div style="font-size: 14px; color: #ff4b4b; font-weight: bold;">{month}</div>
        <div style="font-size: 32px; font-weight: bold; margin: 2px 0;">{day}</div>
        <div style="font-size: 11px; color: gray;">{weekday}</div>
    </div>
    """
    st.markdown(cal_html, unsafe_allow_html=True)

st.markdown("---")

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Wallet Balance", f"{st.session_state.user_data['balance']} pts")
col2.metric("🔥 Daily Streak", f"{st.session_state.user_data['streak']} Days")
if baseline is not None: col3.metric("📱 Wkly Avg Screen", f"{avg_screen_time:.1f} Hrs")
else: col3.metric("📱 Wkly Avg Screen", "Needs Setup")
today_earned = st.session_state.user_data['daily_earnings'].get(today_str, 0)
col4.metric("📈 Today's Earnings", f"{today_earned} / 50 Max")

with st.expander("📊 View 30-Day Activity Heatmap"):
    last_30_days = [(current_date - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(29, -1, -1)]
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
    st.write(f"Earn **+3 points** for every hour under your {avg_screen_time:.1f}hr average. Lose **-3 points** for going over.")
    st_col1, st_col2 = st.columns([2, 1])
    with st_col1:
        current_val = st.session_state.user_data["screen_time_log"].get(today_str, avg_screen_time)
        today_hours = st.number_input("Log Today's Screen Time (Hours)", min_value=0.0, max_value=24.0, value=float(current_val), step=0.5)

    with st_col2:
        st.write("")
        st.write("")
        if st.button("Submit / Update Screen Time"):
            diff = avg_screen_time - today_hours
            new_points = int(diff * 3) # 3 POINTS PER HOUR
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

# --- DYNAMIC TASK ENGINE & LIVE POMODORO ---
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
    st.subheader("🧹 Chores")
    for task, pts in tasks.get("Chores", {}).items():
        if st.button(f"{task} [+{pts}]"): claim_daily(task, pts)

st.markdown("---")
st.subheader("⏱️ Live Pomodoro & Study Engine")
pomo_col1, pomo_col2 = st.columns([1, 2])

with pomo_col1:
    st.components.v1.html("""
    <div style="text-align: center; font-family: sans-serif; padding: 15px; background: #1e1e1e; color: white; border-radius: 10px; border: 1px solid #4CAF50;">
        <h2 id="timer" style="font-size: 45px; margin: 0; padding-bottom: 10px;">50:00</h2>
        <button onclick="startTimer()" style="padding: 10px 20px; font-size: 16px; cursor: pointer; border: none; border-radius: 5px; background: #4CAF50; color: white; font-weight: bold;">Start Focus</button>
        <button onclick="resetTimer()" style="padding: 10px 20px; font-size: 16px; cursor: pointer; border: none; border-radius: 5px; background: #ff4b4b; color: white; margin-left: 5px; font-weight: bold;">Reset</button>
        <script>
        let time = 3000; let running = false; let interval;
        function updateDisplay() {
            let min = Math.floor(time / 60); let sec = time % 60;
            document.getElementById('timer').innerText = (min < 10 ? "0" : "") + min + ":" + (sec < 10 ? "0" : "") + sec;
        }
        function startTimer() {
            if(running) return; running = true;
            interval = setInterval(() => {
                if(time > 0) { time--; updateDisplay(); }
                else { clearInterval(interval); alert("Pomodoro Complete! Claim your points."); }
            }, 1000);
        }
        function resetTimer() { clearInterval(interval); running = false; time = 3000; updateDisplay(); }
        </script>
    </div>
    """, height=180)

with pomo_col2:
    st.write("Let the timer run. When it finishes, log your work below to claim your points.")
    pomo_sessions = st.number_input("50-Min Deep Work Sessions Finished [+3 pts each]", min_value=0, max_value=10, value=0)
    lectures = st.number_input("Lectures Watched [+2]", min_value=0, max_value=15, value=0)
    numericals = st.number_input("Independent Numericals Solved [+1]", min_value=0, max_value=50, value=0)
    if st.button("Log Study Session"):
        earned = (pomo_sessions * 3) + (lectures * 2) + (numericals * 1)
        if earned > 0:
            add_points(earned, f"Study: {pomo_sessions} Pomo, {lectures} Lec, {numericals} Num")
            st.success("Study logged! Massive respect for the focus.")

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
    
    if st.button("🎲 Buy Mystery Box (15 pts)", type="primary", use_container_width=True):
        if st.session_state.user_data["balance"] >= 15:
            add_points(-15, "Bought: Mystery Box", bypass_cap=True)
            roll = random.random()
            if roll < 0.05: 
                st.balloons()
                add_points(40, "Mystery Box: EPIC WIN", bypass_cap=True)
                st.success("🎉 EPIC WIN! You found 40 Points inside!")
            elif roll < 0.40: 
                st.success("✨ RARE WIN! You won a Cafe Study Session voucher!")
            else: 
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
with st.expander("📝 Point Audit Log (History)"):
    if len(st.session_state.user_data["history"]) > 0:
        st.dataframe(pd.DataFrame(st.session_state.user_data["history"]), use_container_width=True, hide_index=True)

# --- ACCOUNT SETTINGS & PERFECT ADMIN ---
st.markdown("---")
with st.expander("⚙️ Account Settings & Admin Panel"):
    tab_tasks, tab_shop, tab_sec, tab_override = st.tabs(["Manage Tasks", "Manage Shop", "Security & Passwords", "Manual Override"])
    
    with tab_tasks:
        st.subheader("Add New Task")
        add_cat = st.selectbox("Category", ["Morning", "Evening", "Chores", "Penalties"], key="add_task_cat")
        add_name = st.text_input("New Task Name", key="add_task_name")
        add_pts = st.number_input("Points", value=1, key="add_task_pts")
        if st.button("Create Task"):
            st.session_state.user_data["custom_tasks"][add_cat][add_name] = add_pts
            save_user_data()
            st.success(f"Added {add_name}!")
            st.rerun()
            
        st.markdown("---")
        st.subheader("Edit or Delete Existing Task")
        edit_cat = st.selectbox("Select Category", ["Morning", "Evening", "Chores", "Penalties"], key="edit_task_cat")
        task_list = list(st.session_state.user_data["custom_tasks"][edit_cat].keys())
        if len(task_list) > 0:
            selected_task = st.selectbox("Select Task to Edit", task_list)
            current_pts = st.session_state.user_data["custom_tasks"][edit_cat][selected_task]
            new_task_name = st.text_input("Rename Task", value=selected_task)
            new_task_pts = st.number_input("Change Points", value=current_pts, key="edit_pts")
            
            colA, colB = st.columns(2)
            with colA:
                if st.button("Save Changes"):
                    del st.session_state.user_data["custom_tasks"][edit_cat][selected_task]
                    st.session_state.user_data["custom_tasks"][edit_cat][new_task_name] = new_task_pts
                    save_user_data()
                    st.success("Task updated!")
                    st.rerun()
            with colB:
                if st.button("🗑️ Delete Task"):
                    del st.session_state.user_data["custom_tasks"][edit_cat][selected_task]
                    save_user_data()
                    st.error("Task deleted.")
                    st.rerun()
        else:
            st.write("No tasks in this category.")

    with tab_shop:
        st.subheader("Add New Shop Item")
        add_shop_name = st.text_input("Item Name", key="add_shop_name")
        add_shop_price = st.number_input("Price", min_value=1, value=10, key="add_shop_price")
        if st.button("Create Item"):
            st.session_state.user_data["shop_items"][add_shop_name] = add_shop_price
            save_user_data()
            st.success("Item Added!")
            st.rerun()
            
        st.markdown("---")
        st.subheader("Edit or Delete Existing Item")
        shop_list = list(st.session_state.user_data["shop_items"].keys())
        if len(shop_list) > 0:
            selected_item = st.selectbox("Select Item", shop_list)
            current_price = st.session_state.user_data["shop_items"][selected_item]
            new_item_name = st.text_input("Rename Item", value=selected_item)
            new_item_price = st.number_input("Change Price", value=current_price)
            
            colC, colD = st.columns(2)
            with colC:
                if st.button("Save Item Changes"):
                    del st.session_state.user_data["shop_items"][selected_item]
                    st.session_state.user_data["shop_items"][new_item_name] = new_item_price
                    save_user_data()
                    st.success("Item updated!")
                    st.rerun()
            with colD:
                if st.button("🗑️ Delete Item"):
                    del st.session_state.user_data["shop_items"][selected_item]
                    save_user_data()
                    st.error("Item deleted.")
                    st.rerun()
                    
    with tab_sec:
        st.subheader("Change Password")
        old_password = st.text_input("Enter Old Password", type="password")
        new_password = st.text_input("Enter New Password", type="password")
        if st.button("Update Password"):
            db = load_db()
            if db["users"][st.session_state.username]["password"] == old_password:
                db["users"][st.session_state.username]["password"] = new_password
                save_db(db)
                st.success("Password Updated Successfully!")
            else:
                st.error("Incorrect Old Password.")
                
        st.write("")
        st.error("🚨 DANGER ZONE")
        if st.button("Reset My Entire Profile"):
            st.session_state.user_data = get_default_data()
            save_user_data()
            st.warning("Profile reset to zero. Fresh start initialized.")
            st.rerun()
            
    with tab_override:
        st.subheader("Fix Mistakes (Manual Override)")
        correction = st.number_input("Add/Subtract points manually", value=0, step=1, key="manual_pts")
        if st.button("Apply Manual Override"):
            add_points(correction, "Manual Correction", bypass_cap=True)
            st.success(f"Wallet adjusted by {correction}.")
            st.rerun()
