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
import re

def set_sort_key(p: Path):
    # Handles set001, set1, set0007, etc.
    m = re.fullmatch(r"set(\d+)", p.stem.lower())
    n = int(m.group(1)) if m else 10**12
    return (n, p.stem.lower())  # ascending

@st.cache_data
def list_set_files():
    if not SETS_DIR.exists():
        return []

    sets = []
    for path in sorted(SETS_DIR.glob("*.json"), key=set_sort_key):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            title = data.get("title", path.stem)
            sets.append({"id": path.stem, "title": title})
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


def clear_answer_keys(prefix: str = "ans_"):
    for k in list(st.session_state.keys()):
        if k.startswith(prefix):
            del st.session_state[k]


def make_new_quiz(set_id: str, set_data: dict):
    """
    Use ALL questions in question_bank, shuffle order, store in session_state.
    """
    qb = set_data["question_bank"]

    # Show every question in question_bank (e.g., 25)
    words = list(qb.keys())

    clear_answer_keys()

    items = [{"word": w, "prompt": qb[w]} for w in words]
    random.shuffle(items)

    st.session_state.quiz_items = items
    st.session_state.started_at = int(time.time())


def show_word_bank_vertical(words: list[str], cols: int = 2):
    """
    Display word bank vertically (one word per line), optionally split into columns.
    """
    cols = max(1, cols)
    columns = st.sidebar.columns(cols)
    for i, w in enumerate(words):
        columns[i % cols].markdown(f"- **{w}**")


# =========================
# App UI
# =========================
st.title("Vocab Tester")

available_sets = list_set_files()
if not available_sets:
    st.error("No quiz sets found. Put your JSON files in a folder named 'sets' next to app.py.")
    st.stop()

labels = [f"{s['id']} — {s['title']}" for s in available_sets]
label_to_id = {f"{s['id']} — {s['title']}": s["id"] for s in available_sets}

# -------------------------
# Set selection screen (no default) — order by filename, display titles only
# -------------------------
if "selected_set_id" not in st.session_state:
    st.session_state.selected_set_id = None

if st.session_state.selected_set_id is None:
    st.subheader("Choose a quiz set")

    # IMPORTANT: titles are in filename order because available_sets is already sorted
    titles_in_file_order = [s["title"] for s in available_sets]

    # Titles must be unique if you're displaying ONLY titles
    title_to_id = {}
    duplicates = []
    for s in available_sets:
        if s["title"] in title_to_id:
            duplicates.append(s["title"])
        else:
            title_to_id[s["title"]] = s["id"]
    if duplicates:
        st.error("Duplicate titles found. Titles must be unique if the dropdown shows only titles.")
        st.write("Duplicates:", sorted(set(duplicates)))
        st.stop()

    q = st.text_input("Search titles")
    filtered_titles = [t for t in titles_in_file_order if q.lower() in t.lower()]

    chosen_title = st.selectbox(
        "Select a set",
        options=["(Choose one)"] + filtered_titles,
        index=0,
        key="set_choice_first"
    )

    if chosen_title != "(Choose one)":
        if st.button("Start", type="primary"):
            set_id = title_to_id[chosen_title]
            st.session_state.selected_set_id = set_id
            st.session_state.selected_set_data = load_set_by_id(set_id)
            make_new_quiz(set_id, st.session_state.selected_set_data)
            st.rerun()

    st.stop()

# -------------------------
# Loaded set
# -------------------------
set_id = st.session_state.selected_set_id
set_data = st.session_state.selected_set_data

# =========================
# Sidebar: Word bank (vertical list)
# =========================
st.sidebar.header(set_data["title"])
st.sidebar.subheader("Word Bank")

# change cols=1 if you want a single vertical column
show_word_bank_vertical(sorted(set_data["word_bank"]), cols=2)

st.sidebar.divider()

if st.sidebar.button("Start / New attempt (reshuffle)"):
    make_new_quiz(set_id, set_data)
    st.rerun()

if st.sidebar.button("Change quiz set"):
    st.session_state.selected_set_id = None
    st.session_state.selected_set_data = None
    if "quiz_items" in st.session_state:
        del st.session_state.quiz_items
    clear_answer_keys()
    st.rerun()

# Ensure quiz exists
if "quiz_items" not in st.session_state:
    make_new_quiz(set_id, set_data)

quiz_items = st.session_state.quiz_items

# =========================
# Main: Questions + one Submit button
# =========================
st.subheader("Questions")

with st.form("quiz_form", clear_on_submit=False):
    for i, item in enumerate(quiz_items, start=1):
        st.markdown(f"**{i}.** {item['prompt']}")
        st.text_input(" ", key=f"ans_{set_id}_{item['word']}", label_visibility="collapsed")
        st.write("")

    submitted = st.form_submit_button("Submit")

if submitted:
    correct = 0
    for item in quiz_items:
        word = item["word"]
        user = (st.session_state.get(f"ans_{set_id}_{word}") or "").strip()
        ok = (user.lower() == word.lower()) if IGNORE_CASE else (user == word)
        if ok:
            correct += 1

    st.success("Submitted.")
    st.success(f"{set_data['title']} — Score: {correct}/{len(quiz_items)}")
