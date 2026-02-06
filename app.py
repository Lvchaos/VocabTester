import random
import time
import streamlit as st

st.set_page_config(page_title="Vocab Tester", layout="wide")

IGNORE_CASE = True
N_QUESTIONS = 15

# -----------------------------
# 1) Define your quiz sets here
# -----------------------------
QUIZ_SETS = {
    "set1": {
        "title": "Quiz Set 1",
        "word_bank": [
            # <-- put your 30 words for set 1 here
            "authoritarian", "truism", "prudence", "astounded", "munificent",
            "moderate", "mitigate", "callow", "duplicitous", "conducive",
            "notorious", "astute", "versatile", "derivative", "assumptive",
            "meticulous", "eulogy", "deride", "derive", "dogmatic",
            "liberal", "integrity", "insipid", "compelling", "proponent",
            "contempt", "incongruous", "exonerate", "renown", "enigma"
        ],
        "question_bank": {
            # mapping: word -> sentence with exactly one _____
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
            # Add the remaining words’ questions if you want them eligible for random sampling
        },
    },
    "set2": {
        "title": "Quiz Set 2",
        "word_bank": [
            # <-- put your 30 words for set 2 here
            "commentator", "detract", "expressive", "resilient", "ambivalent",
            "exacerbate", "perceive", "prosaic", "preserve", "engaging",
            "tenacious", "digressing", "scrutiny", "portray", "commend",
            "solicitous", "convoluted", "capricious", "inhibit", "altruistic",
            "diffident", "prophetic", "conformity", "distribution", "authoritative",
            "conformist", "collaborating", "debilitate", "contentious", "reticent"
        ],
        "question_bank": {
            "preserve": "To _____ the specimen, we stored it at −80°C immediately.",
            "debilitate": "Severe dehydration can _____ older adults within hours.",
            "commend": "The committee decided to _____ her for sustained volunteer service.",
            "collaborating": "The two teams are _____ on a joint grant proposal.",
            "perceive": "Most people can _____ a slight change in pitch.",
            "solicitous": "He was unusually _____, repeatedly checking that everyone was comfortable.",
            "conformist": "As a strict _____, he followed every workplace rule without question.",
            "detract": "Excessive decorative details can _____ from the main argument.",
            "capricious": "Because the weather changes without warning, mountain hiking can feel _____.",
            "distribution": "The chart shows the age _____ of the participants in the study.",
            "portray": "The biography tries to _____ the scientist as meticulous rather than charismatic.",
            "ambivalent": "She felt _____ about the move—excited yet sad to leave friends behind.",
            "resilient": "Despite setbacks, the team stayed _____ and kept improving the design.",
            "digressing": "Please stop _____ and answer the question directly.",
            "altruistic": "Donating anonymously to help strangers is an _____ act.",
        },
    },
}


# --------------------------------
# 2) Helpers: generate a new quiz
# --------------------------------
def clear_answer_keys():
    for k in list(st.session_state.keys()):
        if k.startswith("ans_"):
            del st.session_state[k]


def new_quiz(set_id: str):
    set_data = QUIZ_SETS[set_id]
    wb = set_data["word_bank"]
    qb = set_data["question_bank"]

    available = [w for w in wb if w in qb]
    if len(available) < N_QUESTIONS:
        st.error(
            f"{set_data['title']} needs at least {N_QUESTIONS} words defined in question_bank. "
            f"Currently: {len(available)}"
        )
        st.stop()

    clear_answer_keys()

    selected_words = random.sample(available, N_QUESTIONS)

    # Create items then shuffle order (this is your “shuffle question order”)
    items = [{"word": w, "prompt": qb[w]} for w in selected_words]
    random.shuffle(items)

    st.session_state.quiz_items = items
    st.session_state.started_at = int(time.time())


# -----------------------------
# 3) UI: pick quiz set (single click)
# -----------------------------
st.title("Vocab Tester")

if "selected_set" not in st.session_state:
    st.session_state.selected_set = None

if st.session_state.selected_set is None:
    st.subheader("Choose a quiz set")

    c1, c2 = st.columns(2)
    with c1:
        if st.button(QUIZ_SETS["set1"]["title"], use_container_width=True, key="pick_set1"):
            st.session_state.selected_set = "set1"
            new_quiz("set1")
            st.rerun()

    with c2:
        if st.button(QUIZ_SETS["set2"]["title"], use_container_width=True, key="pick_set2"):
            st.session_state.selected_set = "set2"
            new_quiz("set2")
            st.rerun()

    st.stop()

# -----------------------------
# 4) Sidebar: always-visible word bank (all 30)
# -----------------------------
set_id = st.session_state.selected_set
set_data = QUIZ_SETS[set_id]

st.sidebar.header(set_data["title"])
st.sidebar.subheader("Word Bank (All 30)")

sb_cols = st.sidebar.columns(2)
for i, w in enumerate(set_data["word_bank"]):
    sb_cols[i % 2].markdown(f"- **{w}**")

st.sidebar.divider()
if st.sidebar.button("Start / New attempt (reshuffle)"):
    new_quiz(set_id)

if st.sidebar.button("Change quiz set"):
    st.session_state.selected_set = None
    # optional: clear current quiz items
    if "quiz_items" in st.session_state:
        del st.session_state.quiz_items
    st.rerun()


# -----------------------------
# 5) Main: questions + ONE Submit button at bottom
# -----------------------------
if "quiz_items" not in st.session_state:
    new_quiz(set_id)

quiz_items = st.session_state.quiz_items

st.subheader("Questions")

student_name = st.text_input("Student name / ID (required)", key="student_name")

with st.form("quiz_form", clear_on_submit=False):
    for i, item in enumerate(quiz_items, start=1):
        st.markdown(f"**{i}.** {item['prompt']}")
        st.text_input(" ", key=f"ans_{set_id}_{item['word']}", label_visibility="collapsed")
        st.write("")

    submitted = st.form_submit_button("Submit")  # single button at the bottom

if submitted:
    if not student_name.strip():
        st.error("Please enter your name / ID.")
        st.stop()

    correct = 0
    for item in quiz_items:
        w = item["word"]
        user = (st.session_state.get(f"ans_{set_id}_{w}") or "").strip()
        ok = (user.lower() == w.lower()) if IGNORE_CASE else (user == w)
        if ok:
            correct += 1

    st.success("Submitted.")
    st.success(f"Score: {correct}/{len(quiz_items)}")
    # (As requested) no “Incorrect items …” output
