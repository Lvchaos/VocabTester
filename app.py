import json
import random
import time
from pathlib import Path

import streamlit as st

# =========================
# Config
# =========================
SETS_DIR = Path(__file__).parent / "sets"
IGNORE_CASE = True

st.set_page_config(page_title="Vocab Tester", layout="wide")


# =========================
# Helpers: loading sets
# =========================
@st.cache_data
def list_set_files():
    """Return list of available set files with (id, title, path)."""
    if not SETS_DIR.exists():
        return []

    sets = []
    for path in sorted(SETS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            title = data.get("title", path.stem)
            sets.append({"id": path.stem, "title": title, "path": str(path)})
        except Exception:
            continue
    return sets


@st.cache_data
def load_set_by_id(set_id: str):
    path = SETS_DIR / f"{set_id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    for key in ("title", "word_bank", "question_bank"):
        if key not in data:
            raise ValueError(f"{path.name} is missing required key: '{key}'")

    if not isinstance(data["word_bank"], list):
        raise ValueError(f"{path.name}: 'word_bank' must be a list")

    if not isinstance(data["question_bank"], dict):
        raise ValueError(f"{path.name}: 'question_bank' must be an object/dict")

    return data


def format_word_bank_5_per_line(words: list[str]) -> str:
    lines = []
    for i in range(0, len(words), 5):
        lines.append(", ".join(words[i:i + 5]))
    return "\n".join(lines)


def clear_answer_keys(prefix: str = "ans_"):
    for k in list(st.session_state.keys()):
        if k.startswith(prefix):
            del st.session_state[k]


def make_new_quiz(set_id: str, set_data: dict):
    """
    Use ALL questions in question_bank, shuffle order, store in session_state.
    """
    word_bank = set_data["word_bank"]
    question_bank = set_data["question_bank"]

    # Eligible = words that exist in both places (keeps you safe if word_bank has extras)
    eligible = [w for w in word_bank if w in question_bank]

    if len(eligible) == 0:
        raise ValueError(f"Set '{set_id}' has no usable questions (question_bank is empty?).")

    # IMPORTANT: show all questions (25), not a random subset
    clear_answer_keys()

    items = [{"word": w, "prompt": question_bank[w]} for w in eligible]
    random.shuffle(items)

    st.session_state.quiz_items = items
    st.session_state.started_at = int(time.time())


# =========================
# App UI
# =========================
st.title("Vocab Tester")

available_sets = list_set_files()
if not available_sets:
    st.error("No quiz sets found. Put your JSON files in a folder named 'sets' next to app.py.")
    st.stop()

options = [f"{s['id']} — {s['title']}" for s in available_sets]
label_to_id = {f"{s['id']} — {s['title']}": s["id"] for s in available_sets}

if "selected_set_id" not in st.session_state:
    st.session_state.selected_set_id = None


def on_set_change():
    chosen_label = st.session_state.set_choice
    set_id = label_to_id[chosen_label]
    st.session_state.selected_set_id = set_id

    set_data = load_set_by_id(set_id)
    st.session_state.selected_set_data = set_data

    make_new_quiz(set_id, set_data)


st.selectbox(
    "Choose a quiz set",
    options=options,
    index=0,
    key="set_choice",
    on_change=on_set_change
)

# First load init
if st.session_state.selected_set_id is None:
    on_set_change()

set_id = st.session_state.selected_set_id
set_data = st.session_state.selected_set_data

# =========================
# Sidebar: Full word bank (all words), 5 per line
# =========================
st.sidebar.header(set_data["title"])
st.sidebar.subheader("Word Bank")
st.sidebar.code(format_word_bank_5_per_line(set_data["word_bank"]))

if st.sidebar.button("Start / New attempt (reshuffle)"):
    make_new_quiz(set_id, set_data)
    st.rerun()

# Ensure quiz exists
if "quiz_items" not in st.session_state:
    make_new_quiz(set_id, set_data)

quiz_items = st.session_state.quiz_items

# =========================
# Main: Questions + one Submit button
# =========================
st.subheader("Questions")

student_name = st.text_input("Student name / ID (required)", key="student_name")

with st.form("quiz_form", clear_on_submit=False):
    for i, item in enumerate(quiz_items, start=1):
        st.markdown(f"**{i}.** {item['prompt']}")
        st.text_input(" ", key=f"ans_{set_id}_{item['word']}", label_visibility="collapsed")
        st.write("")

    submitted = st.form_submit_button("Submit")

if submitted:
    if not student_name.strip():
        st.error("Please enter your name / ID.")
        st.stop()

    correct = 0
    for item in quiz_items:
        word = item["word"]
        user = (st.session_state.get(f"ans_{set_id}_{word}") or "").strip()
        ok = (user.lower() == word.lower()) if IGNORE_CASE else (user == word)
        if ok:
            correct += 1

    st.success("Submitted.")
    st.success(f"Score: {correct}/{len(quiz_items)}")
