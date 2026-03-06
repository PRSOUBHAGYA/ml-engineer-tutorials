import streamlit as st
import json
import os
import time

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="ML Academy", page_icon="🎓", layout="wide")

# --- 2. JSON CURRICULUM LOADER ---
def get_curriculum():
    if not os.path.exists("phases.json"):
        st.error("📂 Critical Error: 'phases.json' not found! Please create it in the same folder.")
        return {}
    with open("phases.json", "r") as f:
        try:
            return json.load(f)
        except Exception as e:
            st.error(f"❌ Error parsing JSON: {e}")
            return {}

PHASES = get_curriculum()

# --- 3. DATA PERSISTENCE (Progress & Notes) ---
DB_FILE = "ml_mastery_gate.json"

def load_progress():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                data = json.load(f)
                return {
                    "completed": set(data.get("completed", [])),
                    "quizzes": set(data.get("quizzes", [])),
                    "notes": data.get("notes", {})
                }
            except:
                return {"completed": set(), "quizzes": set(), "notes": {}}
    return {"completed": set(), "quizzes": set(), "notes": {}}

def save_data():
    with open(DB_FILE, "w") as f:
        json.dump({
            "completed": list(st.session_state.mastered),
            "quizzes": list(st.session_state.quizzes_done),
            "notes": st.session_state.user_notes
        }, f)

# --- 4. INITIALIZE SESSION STATE ---
if 'mastered' not in st.session_state:
    prog = load_progress()
    st.session_state.mastered = prog["completed"]
    st.session_state.quizzes_done = prog["quizzes"]
    st.session_state.user_notes = prog["notes"]
    if PHASES:
        # Set default starting point
        first_phase = list(PHASES.keys())[0]
        st.session_state.active_phase = first_phase
        st.session_state.current_id = PHASES[first_phase][0]["id"]

# --- 5. LOCKING LOGIC ---
def is_unlocked(lesson_id):
    all_flat = []
    for p in PHASES.values(): 
        all_flat.extend(p)
    
    for i, v in enumerate(all_flat):
        if v['id'] == lesson_id:
            if i == 0: return True
            prev = all_flat[i-1]
            return prev['id'] in st.session_state.mastered and prev['id'] in st.session_state.quizzes_done
    return False

# --- 6. UNIFIED CSS (Responsive Buttons & Tight Gaps) ---
st.markdown("""
    <style>
    /* 1. Main Container & Gap Minimization */
    .block-container { padding-top: 1.5rem; max-width: 98% !important; padding-left: 1rem; padding-right: 1rem; }
    [data-testid="column"] { padding: 0 5px !important; }
    
    /* 2. Background & Sidebar */
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    [data-testid="stSidebar"] { 
        background-color: #161b22 !important; 
        border-right: 1px solid #30363d; 
        min-width: 260px !important; 
        max-width: 260px !important; 
    }
    
    /* 3. Sidebar UI */
    .sidebar-title { font-size: 24px !important; font-weight: 800; color: #f0f6fc; text-align: center; margin-bottom: 10px; text-shadow: 0 0 10px rgba(56, 189, 248, 0.4); }
    .progress-container { background: rgba(255,255,255,0.03); padding: 12px; border-radius: 8px; border: 1px solid #30363d; margin-bottom: 15px; }
    
    /* 4. Responsive Playlist Buttons */
    div.stButton > button { 
        height: auto !important; 
        padding: 8px 15px !important; 
        width: auto !important; 
        min-width: 100%; 
        white-space: normal !important; 
        text-align: left !important; 
        line-height: 1.3;
        border-radius: 4px; 
        border: 1px solid #30363d; 
        background: #21262d; 
        color: #c9d1d9;
    }
    div.stButton > button:hover { border-color: #38bdf8; color: #38bdf8; }
    div.stButton > button[kind="primary"] { background: #238636 !important; color: white !important; border: none; }
    
    /* 5. Content Cards */
    .quiz-card { background: #1c2128; padding: 20px; border: 2px solid #30363d; border-radius: 8px; margin: 15px 0; }
    .goal-box { background-color: rgba(56, 189, 248, 0.05); border-left: 4px solid #38bdf8; padding: 12px; margin-bottom: 20px; border-radius: 4px; border: 1px solid rgba(56,189,248,0.1); }
    .stTextArea textarea { background-color: #010409 !important; color: #7ee787 !important; font-family: 'Courier New', monospace !important; border: 1px solid #30363d !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 7. SIDEBAR RENDER ---
with st.sidebar:
    st.markdown("<div class='sidebar-title'>🎓 ML Engineer Guide</div>", unsafe_allow_html=True)
    
    # Progress Card
    with st.container():
        st.markdown('<div class="progress-container">', unsafe_allow_html=True)
        all_flat = [v for p in PHASES.values() for v in p]
        truly_mastered = [v['id'] for v in all_flat if v['id'] in st.session_state.mastered and v['id'] in st.session_state.quizzes_done]
        done, total = len(truly_mastered), len(all_flat)
        perc = int(done/total*100) if total > 0 else 0
        st.write(f"**Mastery: {perc}%**")
        st.progress(done/total if total > 0 else 0)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### PHASES")
    for phase_name, videos in PHASES.items():
        unlocked = is_unlocked(videos[0]['id'])
        label = phase_name if unlocked else f"🔒 {phase_name}"
        if st.button(label, key=f"p_{phase_name}", use_container_width=True, 
                     type="primary" if st.session_state.active_phase == phase_name else "secondary"):
            st.session_state.active_phase = phase_name
            st.rerun()

    st.divider()
    with st.expander("⚙️ System Reset"):
        st.warning("🚨 Irreversible Action!")
        if st.button("CONFIRM RESET", use_container_width=True):
            st.session_state.mastered = set(); st.session_state.quizzes_done = set(); st.session_state.user_notes = {}
            st.session_state.active_phase = list(PHASES.keys())[0]
            st.session_state.current_id = PHASES[st.session_state.active_phase][0]["id"]
            if os.path.exists(DB_FILE): os.remove(DB_FILE)
            st.rerun()

    st.divider()
    
    st.markdown("""
        <a href="https://www.linkedin.com/in/prsoubhagya/" target="_blank">
            <div style="
                font-size: 0.8rem; 
                color: #c9d1d9; 
                opacity: 0.7; 
                border-top: 1px solid #30363d; 
                padding-top: 10px;">
                <b>Connect With Soubhagya Pradhan</b><br>
            </div>
        </a>
        <a href='https://www.linkedin.com/in/athletickoder/' target="_blank">
            <div style="
                font-size: 0.8rem; 
                color: #c9d1d9; 
                opacity: 0.7; 
                border-top: 1px solid #30363d; 
                padding-top: 10px;">
                🙏 <b>Special Thanks:</b><br>
                Anshuman Mishra's Newsletter for the curriculum inspiration and guidance." 
            </div>
        </a>
    """, unsafe_allow_html=True)

# --- 8. MAIN INTERFACE RENDER ---
curr = next(v for p in PHASES.values() for v in p if v["id"] == st.session_state.current_id)
col_left, col_right = st.columns([2, 1], gap="small")

with col_left:
    st.markdown(f"## {curr['title']}")
    
    if curr["url"]:
        st.video(curr["url"])
    else:
        st.info("📺 **Note:** Video stream processing...")

    is_m = curr["id"] in st.session_state.mastered
    is_q = curr["id"] in st.session_state.quizzes_done
    
    if not is_m:
        st.info("💡 Watch the tutorial, then check the box to unlock the Quiz.")
        if st.checkbox("I have watched the video", key=f"ready_{curr['id']}"):
            st.session_state.mastered.add(curr["id"]); save_data(); st.rerun()
    
    elif is_m and not is_q:
        st.warning("🧪 **Mastery Mode**: Answer all correctly to proceed.")
        with st.form(key=f"gate_form_{curr['id']}"):
            user_answers = []
            for i, q_data in enumerate(curr['quiz']):
                ans = st.radio(f"{i+1}. {q_data['q']}", q_data['options'], index=None, key=f"q_{curr['id']}_{i}")
                user_answers.append(ans)
            
            if st.form_submit_button("Verify Mastery"):
                correct_count = sum(1 for i, q_data in enumerate(curr['quiz']) if user_answers[i] == q_data['a'])
                if correct_count == len(curr['quiz']):
                    st.session_state.quizzes_done.add(curr['id']); save_data(); st.balloons(); st.rerun()
                else:
                    st.session_state.mastered.remove(curr['id']); save_data()
                    st.error(f"❌ Result: {correct_count}/{len(curr['quiz'])}. Unit reset."); time.sleep(1.5); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.success(f"🎊 Mastery Achieved!")
        if st.button("Proceed to Next Lesson ➜", use_container_width=True):
            all_f = [v for p in PHASES.values() for v in p]
            idx = [v['id'] for v in all_f].index(curr['id'])
            if idx < len(all_f)-1:
                st.session_state.current_id = all_f[idx+1].get('id'); st.rerun()

    st.text_area("Lesson Notes", value=st.session_state.user_notes.get(curr["id"], ""), height=150, key=f"note_{curr['id']}")

with col_right:
    st.markdown("### 📽️ Curriculum")
    st.markdown(f"<div class='goal-box'><b>🎯 Current Goal:</b><br>{curr.get('goal', 'Master concepts.')}</div>", unsafe_allow_html=True)
    # st.divider()

    for v in PHASES[st.session_state.active_phase]:
        unl = is_unlocked(v['id'])
        done_all = v['id'] in st.session_state.mastered and v['id'] in st.session_state.quizzes_done
        
        c1, c2 = st.columns([0.05, 0.95])
        with c1:
            st.write("✅" if done_all else "🔓" if unl else "🔒")
        with c2:
            if st.button(v['title'], key=f"nav_{v['id']}", disabled=not unl, 
                         type="primary" if st.session_state.current_id == v['id'] else "secondary"):
                st.session_state.current_id = v['id']; st.rerun()