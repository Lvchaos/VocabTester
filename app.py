import random
import hashlib
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

st.set_page_config(page_title="Word Blank Quiz", layout="centered")
st.title("Word Blank Quiz")

# ---- initialize a stable random selection per session ----
if "quiz_words" not in st.session_state:
    # Only choose from words that have question prompts defined
    available = [w for w in WORD_BANK if w in QUESTION_BANK]
    if len(available) < N_QUESTIONS:
        st.error(f"Need at least {N_QUESTIONS} words with questions in QUESTION_BANK. Currently: {len(available)}")
        st.stop()
    st.session_state.quiz_words = random.sample(available, N_QUESTIONS)
    st.session_state.started_at = int(time.time())

quiz_words = st.session_state.quiz_words

# ---- word bank display (spread out in columns) ----
st.subheader("Word Bank")
cols = st.columns(3)
for i, w in enumerate(quiz_words):
    cols[i % 3].markdown(f"- **{w}**")

st.divider()
st.subheader("Questions")

student_name = st.text_input("Student name / ID (required)", key="student_name")

with st.form("quiz_form"):
    answers = {}
    for i, w in enumerate(quiz_words, start=1):
        prompt = QUESTION_BANK[w]
        st.write(f"**{i}.** {prompt}")
        answers[w] = st.text_input("Your answer", key=f"ans_{w}")
        st.write("")

    submitted = st.form_submit_button("Submit")

if submitted:
    if not student_name.strip():
        st.error("Please enter your name / ID.")
        st.stop()

    correct = 0
    wrong_words = []

    for w in quiz_words:
        user = (st.session_state.get(f"ans_{w}") or "").strip()
        gold = w.strip()
        ok = user.lower() == gold.lower() if IGNORE_CASE else user == gold
        if ok:
            correct += 1
        else:
            wrong_words.append(w)

    st.success(f"Score: {correct}/{len(quiz_words)}")

    if wrong_words:
        # Don’t reveal answers; just show which items were incorrect
        st.warning("Incorrect items (answers not shown): " + ", ".join(wrong_words))

    # Optional: “submission code” students can paste into LMS
    payload = student_name.strip() + "|" + "|".join((st.session_state.get(f"ans_{w}") or "").strip() for w in quiz_words)
    code = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:10].upper()
    st.info(f"Submission code: **{code}**")
