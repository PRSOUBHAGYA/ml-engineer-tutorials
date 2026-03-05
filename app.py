import streamlit as st
import json
import os
import time

# --- 1. PAGE CONFIG (Ensure layout="wide" is here) ---
st.set_page_config(page_title="ML Academy", page_icon="⚙️", layout="wide")

# --- 2. JSON LOADER (Prevents UI Shrinkage) ---
def get_curriculum():
    if not os.path.exists("phases.json"):
        st.error("📂 'phases.json' not found in directory!")
        return {}
    with open("phases.json", "r") as f:
        return json.load(f)

PHASES = get_curriculum()

# --- 3. DATA PERSISTENCE ---
DB_FILE = "ml_mastery_gate.json"
def load_progress():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            data = json.load(f)
            return {
                "completed": set(data.get("completed", [])),
                "quizzes": set(data.get("quizzes", [])),
                "notes": data.get("notes", {})
            }
    return {"completed": set(), "quizzes": set(), "notes": {}}

# --- 4. INITIALIZE SESSION ---
if 'mastered' not in st.session_state:
    prog = load_progress()
    st.session_state.mastered = prog["completed"]
    st.session_state.quizzes_done = prog["quizzes"]
    st.session_state.user_notes = prog["notes"]
    # Fallback if PHASES is empty
    if PHASES:
        st.session_state.active_phase = list(PHASES.keys())[0]
        st.session_state.current_id = PHASES[st.session_state.active_phase][0]["id"]

# --- 5. REINFORCED CSS (Full Width) ---
st.markdown("""
    <style>
    /* Force main content to use full width */
    .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 95% !important; }
    
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    [data-testid="stSidebar"] { background-color: #161b22 !important; min-width: 320px !important; }
    
    .sidebar-title { font-size: 26px !important; font-weight: 800; color: #f0f6fc; text-align: center; margin-bottom: 15px; }
    .progress-container { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 20px; }
    
    div.stButton > button { height: 42px; width: 100%; border-radius: 4px; border: 1px solid #30363d; background: #21262d; color: #c9d1d9; }
    div.stButton > button[kind="primary"] { background: #238636 !important; border: none; }
    
    .quiz-card { background: #1c2128; padding: 25px; border: 2px solid #30363d; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# ... (Include is_unlocked, Sidebar, and Main Interface logic here) ...

# --- 5. LOGIC & STYLE ---
def is_unlocked(lesson_id):
    all_flat = []
    for p in PHASES.values(): all_flat.extend(p)
    for i, v in enumerate(all_flat):
        if v['id'] == lesson_id:
            if i == 0: return True
            prev = all_flat[i-1]
            return prev['id'] in st.session_state.mastered and prev['id'] in st.session_state.quizzes_done
    return False

def save_data():
    with open(DB_FILE, "w") as f:
        json.dump({
            "completed": list(st.session_state.mastered),
            "quizzes": list(st.session_state.quizzes_done),
            "notes": st.session_state.user_notes
        }, f)

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown("<div class='sidebar-title'>🎓 ML ACADEMY</div>", unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="progress-container">', unsafe_allow_html=True)
        all_flat = [v for p in PHASES.values() for v in p]
        truly_mastered = [v['id'] for v in all_flat if v['id'] in st.session_state.mastered and v['id'] in st.session_state.quizzes_done]
        done, total = len(truly_mastered), len(all_flat)
        st.write(f"**Mastery: {int(done/total*100) if total > 0 else 0}%**")
        st.progress(done/total if total > 0 else 0)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### PHASES")
    for phase_name, videos in PHASES.items():
        unlocked = is_unlocked(videos[0]['id'])
        if st.button(phase_name if unlocked else f"🔒 {phase_name}", key=f"p_{phase_name}", use_container_width=True, disabled=not unlocked,
                     type="primary" if st.session_state.active_phase == phase_name else "secondary"):
            st.session_state.active_phase = phase_name
            st.session_state.current_id = videos[0]['id']
            st.rerun()

    st.divider()
    st.markdown("### ⚠️ Danger Zone")
    with st.expander("System Reset"):
        st.warning("🚨 **WARNING**: Deleting progress is permanent.")
        if st.button("CONFIRM NUCLEAR RESET", use_container_width=True):
            st.session_state.mastered = set(); st.session_state.quizzes_done = set(); st.session_state.user_notes = {}
            st.session_state.active_phase = "Phase 1: Intuition"; st.session_state.current_id = "p1_c1"
            if os.path.exists(DB_FILE): os.remove(DB_FILE)
            st.rerun()

# --- 7. MAIN INTERFACE ---
curr = next(v for p in PHASES.values() for v in p if v["id"] == st.session_state.current_id)
col_left, col_right = st.columns([2, 1], gap="medium")

with col_left:
    st.markdown(f"## {curr['title']}")
    if curr["url"]: st.video(curr["url"])
    else: st.info("📺 **Note:** Video stream processing...")

    is_m = curr["id"] in st.session_state.mastered
    is_q = curr["id"] in st.session_state.quizzes_done
    
    if not is_m:
        st.info("💡 Watch the tutorial above. Once finished, check the box below to start your Mastery Quiz.")
        if st.checkbox("I have watched the video and am ready for the Quiz", key=f"ready_{curr['id']}"):
            st.session_state.mastered.add(curr["id"]); save_data(); st.rerun()
    
    elif is_m and not is_q:
        st.warning("🧪 **Mastery Validation**: Answer all 5 correctly to proceed.")
        st.markdown('<div class="quiz-card">', unsafe_allow_html=True)
        with st.form(key=f"gate_form_{curr['id']}"):
            user_answers = []
            for i, q_data in enumerate(curr['quiz']):
                ans = st.radio(f"{i+1}. {q_data['q']}", q_data['options'], index=None, key=f"q_{curr['id']}_{i}")
                user_answers.append(ans)
            
            if st.form_submit_button("Verify Mastery"):
                correct_count = 0
                for i, q_data in enumerate(curr['quiz']):
                    if user_answers[i] == q_data['a']:
                        correct_count += 1
                
                if correct_count == len(curr['quiz']):
                    st.session_state.quizzes_done.add(curr['id']); save_data(); st.balloons(); st.rerun()
                else:
                    st.session_state.mastered.remove(curr['id']); save_data()
                    st.error(f"❌ Result: {correct_count}/{len(curr['quiz'])}. Resetting unit..."); time.sleep(1.5); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.success(f"🎊 Mastery Achieved! Next unit available.")
        if st.button("Proceed to Next Lesson ➜", use_container_width=True):
            all_f = [v for p in PHASES.values() for v in p]
            idx = [v['id'] for v in all_f].index(curr['id'])
            if idx < len(all_f)-1:
                st.session_state.current_id = all_f[idx+1].get('id'); st.rerun()

    st.text_area("Learning Logs", value=st.session_state.user_notes.get(curr["id"], ""), height=150, key=f"note_{curr['id']}")

with col_right:
    st.markdown("### 📽️ Course Curriculum")
    st.markdown(f"<div class='goal-box'><b>🎯 Current Goal:</b><br>{curr.get('goal', 'Master concepts.')}</div>", unsafe_allow_html=True)
    st.divider()
    for v in PHASES[st.session_state.active_phase]:
        unl = is_unlocked(v['id'])
        done_all = v['id'] in st.session_state.mastered and v['id'] in st.session_state.quizzes_done
        row = st.columns([0.15, 0.85])
        with row[0]: st.write("✅" if done_all else "🔓" if unl else "🔒")
        with row[1]:
            if st.button(v['title'], key=f"nav_{v['id']}", disabled=not unl, use_container_width=True, type="primary" if st.session_state.current_id == v['id'] else "secondary"):
                st.session_state.current_id = v['id']; st.rerun()