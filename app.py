import random
import time
import streamlit as st

# --- your WORD_BANK and QUESTION_BANK here ---
# WORD_BANK = [...]
# QUESTION_BANK = {...}

IGNORE_CASE = True
N_QUESTIONS = 15

st.set_page_config(page_title="Word Blank Quiz", layout="wide")
st.title("Word Blank Quiz")

# ---- pick the 15 words for the quiz (keep this as-is, but ensure you pick from those with questions) ----
if "quiz_words" not in st.session_state:
    available = [w for w in WORD_BANK if w in QUESTION_BANK]
    if len(available) < N_QUESTIONS:
        st.error(f"Need at least {N_QUESTIONS} words with questions in QUESTION_BANK. Currently: {len(available)}")
        st.stop()

    st.session_state.quiz_words = random.sample(available, N_QUESTIONS)
    st.session_state.started_at = int(time.time())

quiz_words = st.session_state.quiz_words

# =========================
# Sidebar: FULL word bank (all 30)
# =========================
st.sidebar.header("Word Bank (All 30)")
# Show as columns inside sidebar
sb_cols = st.sidebar.columns(2)  # 2 columns fits most sidebars; change to 3 if you want
for i, w in enumerate(WORD_BANK):
    sb_cols[i % 2].markdown(f"- **{w}**")

st.sidebar.divider()
st.sidebar.caption("Keep this open while answering.")

# =========================
# Main: Questions + one Submit button at bottom
# =========================
student_name = st.text_input("Student name / ID (required)", key="student_name")

with st.form("quiz_form", clear_on_submit=False):
    # Render questions (no submit per item; Enter does not submit the form)
    for i, w in enumerate(quiz_words, start=1):
        st.markdown(f"**{i}.** {QUESTION_BANK[w]}")
        st.text_input(" ", key=f"ans_{w}", label_visibility="collapsed")
        st.write("")

    submitted = st.form_submit_button("Submit")  # single button at bottom

if submitted:
    if not student_name.strip():
        st.error("Please enter your name / ID.")
        st.stop()

    correct = 0
    wrong_items = []

    for w in quiz_words:
        user = (st.session_state.get(f"ans_{w}") or "").strip()
        gold = w.strip()
        ok = user.lower() == gold.lower() if IGNORE_CASE else user == gold
        if ok:
            correct += 1
        else:
            wrong_items.append(w)

    st.success(f"Score: {correct}/{len(quiz_words)}")

    # Don’t reveal answers
    if wrong_items:
        st.warning("Incorrect items (answers not shown): " + ", ".join(wrong_items))
