import sqlite3

import requests
import streamlit as st

from codespaces_blank.database import (
    add_feedback_batch,
    create_table,
    load_feedback,
)

st.set_page_config(page_title="Customer Feedback Analyzer", page_icon="💬", layout="wide")
create_table()


def analyze_review(api_url: str, review: str) -> dict[str, str | int]:
    try:
        response = requests.post(
            f"{api_url.rstrip('/')}/analyze",
            json={"text": review},
            timeout=60,
        )
        response.raise_for_status()
        analysis = response.json()
        if not isinstance(analysis, dict):
            raise ValueError("The API response must be a JSON object.")

        label = analysis.get("label")
        score = analysis.get("score")
        theme = analysis.get("theme")
        if not isinstance(label, str) or not isinstance(theme, str):
            raise ValueError("The API response is missing a valid label or theme.")
        if isinstance(score, bool) or not isinstance(score, int):
            raise ValueError("The API response is missing a valid integer score.")

        return {
            "Review": review,
            "Sentiment": label,
            "Score": score,
            "Theme": theme,
            "Status": "Complete",
        }
    except requests.RequestException as exc:
        error = str(exc)
    except (ValueError, TypeError) as exc:
        error = str(exc)

    return {
        "Review": review,
        "Sentiment": "",
        "Score": "",
        "Theme": "",
        "Status": f"Error: {error}",
    }


st.title("Customer Feedback Analyzer")
st.write("Analyze a batch of customer reviews and compare their sentiment, score, and theme.")

api_url = st.sidebar.text_input("FastAPI base URL", value="http://localhost:8000")
reviews_text = st.text_area(
    "Reviews",
    height=260,
    placeholder="Enter one review per line",
    help="Each non-empty line is sent to the FastAPI /analyze endpoint as a separate review.",
)

if st.button("Analyze reviews", type="primary"):
    reviews = [line.strip() for line in reviews_text.splitlines() if line.strip()]
    if not api_url.strip():
        st.error("Enter the FastAPI base URL.")
    elif not reviews:
        st.warning("Enter at least one review, with each review on its own line.")
    else:
        progress = st.progress(0, text="Analyzing reviews...")
        results: list[dict[str, str | int]] = []
        for index, review in enumerate(reviews, start=1):
            results.append(analyze_review(api_url.strip(), review))
            progress.progress(index / len(reviews), text=f"Analyzed {index} of {len(reviews)} reviews")

        st.session_state["analysis_results"] = results
        st.session_state["analysis_saved"] = False
        progress.empty()

if results := st.session_state.get("analysis_results"):
    completed = sum(result["Status"] == "Complete" for result in results)
    st.subheader("Analysis results")
    st.caption(f"{completed} of {len(results)} reviews analyzed successfully.")
    st.dataframe(results, width="stretch", hide_index=True)
    if completed:
        if st.button(
            "Save results to database",
            disabled=st.session_state.get("analysis_saved", False),
        ):
            try:
                add_feedback_batch(
                    [
                        {
                            "text": str(result["Review"]),
                            "label": str(result["Sentiment"]),
                            "score": int(result["Score"]),
                            "theme": str(result["Theme"]),
                        }
                        for result in results
                        if result["Status"] == "Complete"
                    ]
                )
            except sqlite3.Error as exc:
                st.error(f"Could not save review results: {exc}")
            else:
                st.session_state["analysis_saved"] = True
                st.success(f"Saved {completed} reviews to the database.")

st.subheader("Review history")
if st.button("Load history"):
    try:
        st.session_state["review_history"] = load_feedback()
    except sqlite3.Error as exc:
        st.error(f"Could not load review history: {exc}")

if history := st.session_state.get("review_history"):
    st.dataframe(
        [
            {
                "ID": record["id"],
                "Review": record["text"],
                "Sentiment": record["label"],
                "Score": record["score"],
                "Theme": record["theme"],
            }
            for record in history
        ],
        width="stretch",
        hide_index=True,
    )
elif "review_history" in st.session_state:
    st.info("No saved reviews yet.")
