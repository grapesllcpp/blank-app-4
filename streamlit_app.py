import json
from io import StringIO
from pathlib import Path

import pandas as pd
import streamlit as st

# -------------------------------------------------
# Streamlit App: Dictionary‑Based Text Classifier
# -------------------------------------------------
# This app lets users:
#  1. Upload a CSV containing a "Statement" column.
#  2. Inspect & edit keyword dictionaries (JSON format).
#  3. Classify each row, one‑hot encode category columns, and
#     download the annotated CSV.
# -------------------------------------------------

st.set_page_config(page_title="Dictionary Text Classifier", page_icon="📑", layout="wide")
st.title("📑 Dictionary‑Based Text Classifier")

st.markdown(
    """
Upload any CSV that contains a **`Statement`** column (text to classify).  
Edit the keyword dictionaries on the sidebar, then click **Run Classification**.
    """
)

# -----------------------------
# 1. Sidebar – Dictionary Editor
# -----------------------------
DEFAULT_DICTIONARIES = {
    "urgency_marketing": {
        "limited", "limited time", "limited run", "limited edition", "order now",
        "last chance", "hurry", "while supplies last", "before they're gone",
        "selling out", "selling fast", "act now", "don't wait", "today only",
        "expires soon", "final hours", "almost gone",
    },
    "exclusive_marketing": {
        "exclusive", "exclusively", "exclusive offer", "exclusive deal",
        "members only", "vip", "special access", "invitation only",
        "premium", "privileged", "limited access", "select customers",
        "insider", "private sale", "early access",
    },
}

# Initialize session‑state storage for dictionaries
if "dictionaries" not in st.session_state:
    st.session_state["dictionaries"] = DEFAULT_DICTIONARIES.copy()

def reset_to_default():
    st.session_state["dict_text"] = json.dumps(DEFAULT_DICTIONARIES, indent=4)
    st.session_state["dictionaries"] = DEFAULT_DICTIONARIES.copy()

with st.sidebar:
    st.header("🔧 Keyword Dictionaries")

    # Show editable JSON in a text area
    dict_text = st.text_area(
        "Edit dictionaries below (JSON format)",
        value=json.dumps(st.session_state.get("dictionaries"), indent=4),
        key="dict_text",
        height=300,
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save Changes"):
            try:
                parsed_dict = json.loads(dict_text)
                # Ensure all values are sets for fast lookup
                cleaned = {k: set(v) for k, v in parsed_dict.items()}
                st.session_state["dictionaries"] = cleaned
                st.success("Dictionaries updated!")
            except Exception as e:
                st.error(f"Failed to parse JSON: {e}")
    with col2:
        st.button("🔄 Reset", on_click=reset_to_default)

    st.markdown("""Apply your edits, then run the classification from the main panel.""")

# -----------------------------
# 2. Main – File Upload & Run
# -----------------------------

uploaded_file = st.file_uploader("📂 Upload your CSV", type=["csv"])

run_btn = st.button("▶️ Run Classification", disabled=uploaded_file is None)

if run_btn and uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Error reading CSV: {e}")
        st.stop()

    if "Statement" not in df.columns:
        st.error("The uploaded file must contain a 'Statement' column.")
        st.stop()

    # Helper: list categories matched in text
    def get_tags(text: str) -> list[str]:
        lower = str(text).lower()
        matches = []
        for category, words in st.session_state["dictionaries"].items():
            if any(word in lower for word in words):
                matches.append(category)
        return matches

    # Apply classification
    df["Tags"] = df["Statement"].apply(lambda x: ", ".join(get_tags(x)))
    for category in st.session_state["dictionaries"]:
        df[category] = df["Statement"].apply(lambda x: category in get_tags(x))

    st.success("Classification complete!")

    st.subheader("🔍 Preview (first 10 rows)")
    st.dataframe(df.head(10), use_container_width=True)

    # Prepare download
    buffer = StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)

    st.download_button(
        label="💾 Download annotated CSV",
        data=buffer,
        file_name="classified_data.csv",
        mime="text/csv",
    )

    # Optional: show full dictionaries used
    with st.expander("View dictionaries used in this run"):
        st.json({k: list(v) for k, v in st.session_state["dictionaries"].items()}, expanded=False)

elif uploaded_file is None:
    st.info("Upload a CSV file to begin.")
