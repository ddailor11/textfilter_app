import streamlit as st
import pandas as pd
import re
import unicodedata
from io import BytesIO

st.set_page_config(
    page_title="Text Filter Tool",
    layout="wide"
)

st.title("🚫 Text Filter Tool")
st.write(
    """
    Upload a CSV and detect rows containing flagged words or phrases.
    You can manage both flagged and excluded word lists below.
    """
)

# ============================================================
# DEFAULT FLAGGED WORDS
# ============================================================

default_flagged_words = [
    "retarded", "nigger", "hitler", "retard", "tard", "fucktard",
    "fuck off", "fuck you", "fag", "faggot", "asshole", "ass hole",
    "bullshit", "cock", "cunt", "crap", "cocksucker", "dick",
    "dickhead", "fucker", "go to hell", "go straight to hell",
    "slut", "shit", "tranny", "transgender", "twat", "splooge",
    "pussy", "pigfucker", "motherfucker", "mother fucker", "maga",
    "charlie", "kirk", "fuck no", "hell no", "he’ll no",
    "go fuck yourself", "fuck u", "eat shit", "you lost",
    "trump is king", "trump 2028", "go trump", "trump 2024",
    "red", "nigga", "idiots", "suck my", "make america great again",
    "trump2028", "gay", "f you", "fuck blue", "libtard", "fuh",
    "spick", "i voted for trump", "trump for king", "communist",
    "socialist", "marxist", "commie", "commies", "liberals", "commy",
    "daddy", "marx", "fucku", "get fucked", "suck a dick",
    "i love trump", "f that", "lib", "midget", "spic", "illegals",
    "illegal immigrants", "open borders", "women’s sports",
    "womens sports", "2028", "cum", "socialism", "demorats",
    "demons", "demonrats", "i’m a republican", "i vote republican",
    "i’m republican", "i voted for republicans", "scumbag", "die",
    "cunty", "kill yourself", "soros", "leftist", "leftists"
]

# ============================================================
# DEFAULT EXCLUDED WORDS / EMOJIS
# These are ALWAYS excluded.
# ============================================================

default_excluded_words = [
    "emphasized",
    "disliked",
    "liked",
    "👍",
    "loved",
    "questioned"
]

# ============================================================
# SESSION STATE
# ============================================================

if "flagged_words" not in st.session_state:
    st.session_state.flagged_words = default_flagged_words.copy()

if "excluded_words" not in st.session_state:
    st.session_state.excluded_words = default_excluded_words.copy()

# Always ensure permanent exclusions remain present.
st.session_state.excluded_words = sorted(
    set(st.session_state.excluded_words + default_excluded_words)
)

# ============================================================
# NORMALIZATION
# ============================================================

def normalize_text(value):
    """
    Lowercase text and remove punctuation while preserving
    letters, numbers, spaces, and emojis.

    This allows:
        FUCK YOU
        fuck-you
        fuck.you
        fuck, you

    to be treated as the same phrase.
    """

    if pd.isna(value):
        return ""

    text = str(value).lower()

    normalized = []

    for char in text:
        category = unicodedata.category(char)

        # Remove punctuation.
        if category.startswith("P"):
            normalized.append(" ")

        # Keep everything else, including emojis.
        else:
            normalized.append(char)

    text = "".join(normalized)

    # Collapse repeated whitespace.
    text = re.sub(r"\s+", " ", text).strip()

    return text


# ============================================================
# CREATE MATCHING PATTERN
# ============================================================

def normalize_term(term):
    """
    Normalize a search term using the same rules as the text.
    """
    return normalize_text(term)


def build_pattern(word_list):
    """
    Build a regex pattern from a list of terms.

    Longer phrases are checked first so that:
        "go straight to hell"

    is matched before:
        "go to hell"
    """

    if not word_list:
        return None

    normalized_terms = []

    for word in word_list:
        normalized = normalize_term(word)

        if normalized:
            normalized_terms.append(normalized)

    # Remove duplicates.
    normalized_terms = sorted(
        set(normalized_terms),
        key=len,
        reverse=True
    )

    if not normalized_terms:
        return None

    escaped_terms = [
        re.escape(term)
        for term in normalized_terms
    ]

    # Word boundaries work well for normal words.
    # We use lookarounds so emoji terms work too.
    pattern = r"(?<!\w)(" + "|".join(escaped_terms) + r")(?!\w)"

    return re.compile(pattern, re.IGNORECASE)


# ============================================================
# FIND MATCHES
# ============================================================

def find_matches(text, pattern):
    if not pattern:
        return []

    matches = pattern.findall(text)

    return sorted(
        set(match.lower() for match in matches)
    )


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("⚙️ Manage Word Lists")

# ------------------------------------------------------------
# FLAGGED WORDS
# ------------------------------------------------------------

with st.sidebar.expander("🚨 Manage Flagged Words", expanded=False):

    flagged_text = st.text_area(
        "Flagged words/phrases — one per line:",
        value="\n".join(st.session_state.flagged_words),
        height=300,
        key="flagged_editor"
    )

    if st.button(
        "Update Flagged List",
        key="update_flagged"
    ):
        new_list = [
            line.strip().lower()
            for line in flagged_text.splitlines()
            if line.strip()
        ]

        st.session_state.flagged_words = sorted(
            set(new_list)
        )

        st.success("Flagged word list updated.")

st.sidebar.write(
    f"Flagged terms: **{len(st.session_state.flagged_words)}**"
)

# ------------------------------------------------------------
# EXCLUDED WORDS
# ------------------------------------------------------------

with st.sidebar.expander("❎ Manage Excluded Words", expanded=False):

    excluded_text = st.text_area(
        "Excluded words/phrases — one per line:",
        value="\n".join(st.session_state.excluded_words),
        height=300,
        key="excluded_editor"
    )

    if st.button(
        "Update Excluded List",
        key="update_excluded"
    ):
        new_list = [
            line.strip().lower()
            for line in excluded_text.splitlines()
            if line.strip()
        ]

        # Permanent exclusions are always retained.
        st.session_state.excluded_words = sorted(
            set(new_list + default_excluded_words)
        )

        st.success(
            "Excluded word list updated. "
            "The six permanent exclusions remain active."
        )

st.sidebar.write(
    f"Excluded terms: **{len(st.session_state.excluded_words)}**"
)

# ============================================================
# SHOW PERMANENT EXCLUSIONS
# ============================================================

with st.sidebar.expander("🔒 Permanent Exclusions"):

    st.write(
        "These exclusions are automatically applied to every upload:"
    )

    for word in default_excluded_words:
        st.write(f"• {word}")

# ============================================================
# FILE UPLOAD
# ============================================================

uploaded_file = st.file_uploader(
    "📤 Upload a CSV file",
    type=["csv"]
)

if uploaded_file:

    try:
        df = pd.read_csv(uploaded_file)

    except Exception as e:
        st.error(f"Could not read the CSV file: {e}")
        st.stop()

    # --------------------------------------------------------
    # CHECK FOR TEXT COLUMN
    # --------------------------------------------------------

    if "text" not in df.columns:

        st.error(
            '❌ CSV must contain a column named "text".'
        )

        st.write("Columns found in your CSV:")
        st.write(list(df.columns))

        st.stop()

    st.success(
        f"✅ File uploaded successfully — {len(df):,} rows."
    )

    # --------------------------------------------------------
    # NORMALIZE TEXT
    # --------------------------------------------------------

    df["_normalized_text"] = df["text"].apply(
        normalize_text
    )

    # --------------------------------------------------------
    # BUILD PATTERNS
    # --------------------------------------------------------

    flagged_pattern = build_pattern(
        st.session_state.flagged_words
    )

    excluded_pattern = build_pattern(
        st.session_state.excluded_words
    )

    # --------------------------------------------------------
    # FIND FLAGGED TERMS
    # --------------------------------------------------------

    df["matched_flagged"] = df["_normalized_text"].apply(
        lambda text: find_matches(
            text,
            flagged_pattern
        )
    )

    # --------------------------------------------------------
    # FIND EXCLUDED TERMS
    # --------------------------------------------------------

    df["matched_excluded"] = df["_normalized_text"].apply(
        lambda text: find_matches(
            text,
            excluded_pattern
        )
    )

    # --------------------------------------------------------
    # DETERMINE WHICH ROWS ARE FLAGGED
    # --------------------------------------------------------

    df["contains_flagged"] = df["matched_flagged"].apply(bool)

    df["contains_excluded"] = df["matched_excluded"].apply(bool)

    # A row is included only when:
    #
    # 1. It contains a flagged term
    # AND
    # 2. It does NOT contain an excluded term

    flagged_df = df[
        df["contains_flagged"]
        & ~df["contains_excluded"]
    ].copy()

    # --------------------------------------------------------
    # FORMAT MATCHED TERMS FOR CSV
    # --------------------------------------------------------

    flagged_df["matched_flagged"] = flagged_df[
        "matched_flagged"
    ].apply(
        lambda x: ", ".join(x)
    )

    flagged_df["matched_excluded"] = flagged_df[
        "matched_excluded"
    ].apply(
        lambda x: ", ".join(x)
    )

    # --------------------------------------------------------
    # REMOVE INTERNAL COLUMN
    # --------------------------------------------------------

    flagged_df = flagged_df.drop(
        columns=["_normalized_text"]
    )

    # --------------------------------------------------------
    # RESULTS
    # --------------------------------------------------------

    st.subheader("Results")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total rows",
            f"{len(df):,}"
        )

    with col2:
        st.metric(
            "Flagged rows",
            f"{len(flagged_df):,}"
        )

    with col3:
        excluded_count = (
            df["contains_flagged"]
            & df["contains_excluded"]
        ).sum()

        st.metric(
            "Removed by exclusions",
            f"{excluded_count:,}"
        )

    # --------------------------------------------------------
    # DISPLAY RESULTS
    # --------------------------------------------------------

    if not flagged_df.empty:

        st.subheader("🚨 Flagged Rows")

        st.dataframe(
            flagged_df,
            use_container_width=True,
            hide_index=True
        )

        # ----------------------------------------------------
        # DOWNLOAD CSV
        # ----------------------------------------------------

        output = BytesIO()

        flagged_df.to_csv(
            output,
            index=False,
            encoding="utf-8-sig"
        )

        st.download_button(
            label="📥 Download Flagged Rows as CSV",
            data=output.getvalue(),
            file_name="flagged_texts_filtered.csv",
            mime="text/csv"
        )

    else:

        st.info(
            "✅ No flagged content remained after applying exclusions."
        )

else:

    st.info(
        "⬆️ Upload a CSV file to begin."
    )
