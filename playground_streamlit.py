from pathlib import Path

from stqdm import stqdm

import streamlit as st
import diskcache
from oai_client import OAIClient
from settings import Settings

DEFAULT_PROMPT = """
Human: Here's a passage I've been thinking about:

Many people use meditation to treat stress and stressrelated conditions and to promote general health. 1,2 o counsel patients appropriately, clinicians need to know more about meditation programs and how they can affect health outcomes. Meditation training programs vary in several ways, including the type of mental activity promoted, the amount of training recommended, the use and qualifications of an instructor, and the degree of emphasis on religion or spirituality. Some meditative techniques are integrated into a broader alternative approach that includes dietary and/or movement therapies (eg, ayurveda or yoga).

Assistant: OK, understood.

Human: Please summarize the passage for me.

Assistant:
""".rstrip()

script_path = Path(__file__).parent


@st.cache(ttl=60 * 60 * 24)
def init_oai_client():
    ctx = Settings.from_env_file(".env.secret")
    cache = diskcache.Cache(directory=ctx.disk_cache_dir)
    oai_client = OAIClient(
        api_key=ctx.openai_api_key,
        organization_id=ctx.openai_org_id,
        cache=cache,
    )
    return oai_client


def main():
    oai_client = init_oai_client()
    prompt = st.text_area("Prompt", value=DEFAULT_PROMPT, height=500)
    model_name = st.selectbox(
        "Model",
        [
            "text-davinci-002",
        ],
        index=0,
    )
    max_tokens = st.number_input(
        "Max tokens", value=32, min_value=0, max_value=2048, step=2
    )
    temperature = st.number_input("Temperature", value=0.7)
    stop = st.multiselect(
        "Stop",
        [
            "Human:",
            "Assistant:",
            "\n\n",
            "\n",
            "Q:",
            "A:",
        ],
    )

    # TODO(bfortuner): Add CMD+ENTER Run Key binding: https://github.com/streamlit/streamlit/issues/1291
    if st.button("Run"):
        print("Running")
        text_placeholder = st.empty()

        resp = oai_client.complete(
            prompt,
            model=model_name,  # type: ignore
            max_tokens=max_tokens,  # type: ignore
            temperature=temperature,
            stop=stop,
        )

        text_placeholder.write(resp.get("completion"))


if __name__ == "__main__":
    main()
