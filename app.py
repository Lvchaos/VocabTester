import random
import time
import streamlit as st


WORD_BANK = [
    "authoritarian", "truism", "prudence", "astounded", "munificent",
    "moderate", "mitigate", "callow", "duplicitous", "conducive",
    "notorious", "astute", "versatile", "derivative", "assumptive",
    "meticulous", "eulogy", "deride", "derive", "dogmatic",
    "liberal", "integrity", "insipid", "compelling", "proponent",
    "contempt", "incongruous", "exonerate", "renown", "enigma"
]

# You should provide (at least) one sentence per word.
# Make sure each sentence has exactly one blank "_____" and is unambiguous.
QUESTION_BANK = {
    "eulogy": "She delivered a moving _____ at her grandfather’s funeral.",
    "authoritarian": "The country fell under an _____ regime that censored the press and jailed critics.",
    "proponent": "He is a strong _____ of renewable energy and publicly campaigns for it.",
    "derive": "From these results, we can _____ a clear relationship between dosage and response.",
    "munificent": "A _____ patron funded the scholarship program without seeking recognition.",
    "truism": "Saying “practice makes perfect” is a _____ that offers little new insight.",
    "deride": "Some commentators began to _____ the proposal without addressing its evidence.",
    "incongruous": "The cheerful music felt _____ in a scene meant to be solemn.",
    "moderate": "The chair had to _____ the debate to keep speakers from interrupting.",
    "dogmatic": "His _____ certainty left no room for questions or alternatives.",
    "astounded": "The researchers were _____ to discover the error had reversed the conclusion.",
    "prudence": "Basic financial _____ suggests saving before making expensive purchases.",
    "liberal": "A _____ democracy typically protects civil liberties and freedom of expression.",
    "enigma": "The sudden disappearance remains an _____ even decades later.",
    "renown": "After the discovery, she achieved international _____ in her field.",
    # Add the rest of your words here...
}

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
