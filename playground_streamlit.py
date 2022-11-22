from pathlib import Path

from stqdm import stqdm

import streamlit as st
from anthropic import *


def main():
    # Load placeholder text
    script_path = Path(__file__).parent
    paper_text = open(script_path / "data/paper.txt").read()

    # UI inputs
    input_type = st.radio("Input type", ["Text Q&A", "Prompt"])

    if input_type == "Prompt":
        paper_paragraph = paper_text.split("\n\n")[0]
        default_prompt = f"""\n{HUMAN_PROMPT} Here's a passage I've been thinking about:

{paper_paragraph}
{AI_PROMPT} OK, understood.
{HUMAN_PROMPT} Please summarize the passage for me.
{AI_PROMPT}"""
        prompt = st.text_area("Prompt", value=default_prompt, height=500)

    elif input_type == "Text Q&A":
        long_text = st.text_area(
            "Long text (e.g. academic paper)", value=paper_text, height=500
        )
        truncated_text = truncate(long_text)
        if long_text != truncated_text:
            st.warning(
                f"Truncated paper text from {len(paper_text)} to {len(truncated_text)} chars to fit into prompt"
            )
        question = st.text_input(
            "Question", value="Please summarize the passage for me."
        )
        prompt = make_qa_prompt(long_text, question)

    else:
        raise ValueError(f"Unknown input type: {input_type}")

    max_tokens = st.number_input("Max tokens", value=30)
    model_name = st.selectbox(
        "Model",
        [
            "junior-all-v6b-s750",
        ],
    )

    # Run model + print outputs as they're streamed back to us
    if st.button("Run"):
        text_placeholder = st.empty()

        for resp in stqdm(
            sync_sample(
                prompt=prompt,
                model=model_name,
                max_tokens=max_tokens,
            ),
            total=max_tokens + 1,
        ):
            text_placeholder.write(resp.get("completion"))

        st.write("Done!")


if __name__ == "__main__":
    main()
