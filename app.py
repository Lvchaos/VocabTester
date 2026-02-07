import json
import random
import time
from pathlib import Path

import streamlit as st

# =========================
# Config
# =========================
SETS_DIR = Path(__file__).parent / "sets"
def sets_signature():
    if not SETS_DIR.exists():
        return tuple()
    paths = sorted(SETS_DIR.glob("*.json"), key=set_sort_key)
    return tuple((p.name, p.stat().st_mtime_ns) for p in paths)

def file_mtime_ns(path: Path) -> int:
    return path.stat().st_mtime_ns

IGNORE_CASE = True

st.set_page_config(page_title="Vocab Tester", layout="wide")
st.markdown(
    """
    <style>
    /* Hide "Press Enter to submit/apply" under inputs */
    div[data-testid="InputInstructions"] { display: none; }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# Helpers: loading sets
# =========================
import re

def set_sort_key(p: Path):
    stem = p.stem.lower()

    # Examples:
    # set001               -> prefix=None, setnum=1
    # 2000vocab_set001     -> prefix=2000, setnum=1
    # 1500vocab_set010     -> prefix=1500, setnum=10

    m_set = re.search(r"set(\d+)$", stem)          # grab trailing set###
    setnum = int(m_set.group(1)) if m_set else 10**12

    m_prefix = re.match(r"(\d+)", stem)            # grab leading number if present
    prefix = int(m_prefix.group(1)) if m_prefix else 10**12

    # Primary sort: prefix (1500 before 2000; plain 'set###' goes last by default)
    # Secondary: set number
    # Tertiary: full stem for stability
    return (prefix, setnum, stem)


@st.cache_data
def list_set_files(_sig):
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
def load_set_by_id(set_id: str, _mtime_ns: int):
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
    st.session_state.pop("last_result", None)

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
        columns[i % cols].markdown(
            f"<div style='margin:0; padding:0; line-height:2.5; "
            f"white-space:normal; overflow-wrap:anywhere;'>"
            f"• <b>{w}</b></div>",
            unsafe_allow_html=True
        )


# =========================
# App UI
# =========================
st.title("Vocab Tester")

available_sets = list_set_files(sets_signature())
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
    h1, h2 = st.columns([4, 1])
    with h1:
        st.subheader("Choose a quiz set")
    with h2:
        st.write("")  # small vertical align tweak
        if st.button("Reload"):
            st.cache_data.clear()
            st.rerun()


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

    left, _ = st.columns([2, 5])  # adjust left width: [1.8, 6] if you want narrower

    with left:
        q = st.text_input("Search titles")
        filtered_titles = [t for t in titles_in_file_order if q.lower() in t.lower()]

        chosen_title = st.selectbox(
            "Select a set",
            options=["(Choose one)"] + filtered_titles,
            index=0,
            key="set_choice_first"
        )

        if st.button("Reload test list"):
            st.cache_data.clear()
            st.rerun()

        if chosen_title != "(Choose one)":
            if st.button("Start", type="primary"):
                set_id = title_to_id[chosen_title]
                st.session_state.selected_set_id = set_id

                set_path = SETS_DIR / f"{set_id}.json"
                set_data = load_set_by_id(set_id, file_mtime_ns(set_path))  # reload single JSON
                st.session_state.selected_set_data = set_data

                make_new_quiz(set_id, set_data)
                st.rerun()

    st.stop()
# -------------------------
# Loaded set
# -------------------------
set_id = st.session_state.selected_set_id
set_path = SETS_DIR / f"{set_id}.json"
set_data = load_set_by_id(set_id, file_mtime_ns(set_path))
st.session_state.selected_set_data = set_data  # keep if you want

# =========================
# Sidebar: Word bank (vertical list)
# =========================
st.sidebar.header(set_data["title"])
st.sidebar.subheader("Word Bank")

# change cols=1 if you want a single vertical column
show_word_bank_vertical(sorted(set_data["word_bank"]), cols=2)

st.sidebar.divider()

if st.sidebar.button("Start / New attempt (reshuffle)"):
    set_path = SETS_DIR / f"{set_id}.json"
    set_data = load_set_by_id(set_id, file_mtime_ns(set_path))  # reload single JSON
    st.session_state.selected_set_data = set_data

    make_new_quiz(set_id, set_data)
    st.rerun()
    

if st.sidebar.button("Change quiz set"):
    st.session_state.pop("last_result", None)
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

wrong_words_set = set()
r = st.session_state.get("last_result")

# Only highlight if the stored result matches the current set + current quiz attempt
if r and r.get("set_id") == set_id and r.get("quiz_id") == st.session_state.get("started_at"):
    wrong_words_set = set(r.get("wrong_words", []))

with st.form("quiz_form", clear_on_submit=False):
    for i, item in enumerate(quiz_items, start=1):
        if item["word"] in wrong_words_set:
            st.markdown(
                f"""
                <div style="
                    background: rgba(255, 75, 75, 0.12);
                    border-left: 6px solid #ff4b4b;
                    padding: 0.6rem 0.8rem;
                    border-radius: 0.5rem;
                    margin-bottom: 0.25rem;
                ">
                    <b>{i}.</b> {item['prompt']}
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(f"**{i}.** {item['prompt']}")

        st.text_input(" ", key=f"ans_{set_id}_{item['word']}", label_visibility="collapsed")
        st.write("")

    submitted = st.form_submit_button("Submit")

if submitted:
    wrong_nums = []
    wrong_words = []
    correct = 0

    for i, item in enumerate(quiz_items, start=1):
        word = item["word"]
        user = (st.session_state.get(f"ans_{set_id}_{word}") or "").strip()
        ok = (user.lower() == word.lower()) if IGNORE_CASE else (user == word)

        if ok:
            correct += 1
        else:
            wrong_nums.append(i)
            wrong_words.append(word)  # only for highlighting; not displayed

    st.session_state.last_result = {
        "set_id": set_id,
        "quiz_id": st.session_state.get("started_at"),
        "title": set_data["title"],
        "correct": correct,
        "total": len(quiz_items),
        "wrong_nums": wrong_nums,
        "wrong_words": wrong_words
    }

    st.rerun()  # rerun so the questions render with red highlights
    
r = st.session_state.get("last_result")
if r and r.get("set_id") == set_id and r.get("quiz_id") == st.session_state.get("started_at"):
    wrong_str = ", ".join(map(str, r["wrong_nums"])) if r["wrong_nums"] else "None"
    st.success(f"{r['title']} — Score: {r['correct']}/{r['total']} — Incorrect #: {wrong_str}")
