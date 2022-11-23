from pathlib import Path
from typing import List, Dict, Union

from stqdm import stqdm

import streamlit as st
import diskcache
from oai_client import OAIClient
from settings import Settings
import utils

PROMPT_DIR = "./data/prompts"
DEFAULT_PROMPT_ID = "default_prompt"
# TODO(bfortuner): Update with token limits
MODELS = [
    "text-davinci-002",
    "text-curie-001",
    "text-babbage-001",
    "text-ada-001",
    "code-davinci-002",
    "code-cushman-001",
]
STOP_SEQUENCES = [
    "newline",
    "double-newline",
    "Human:",
    "Assistant:",
    "Q:",
    "A:",
    "INPUT",
    "OUTPUT",
]
DEFAULT_PROMPT = utils.load_prompt(DEFAULT_PROMPT_ID, PROMPT_DIR)


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


@st.cache(ttl=5)
def list_prompts(prompt_dir: str) -> List[str]:
    return utils.list_prompts(prompt_dir)


def create_prompt(
    prompt_name: str, prompt_text: str, params: dict, inputs: dict, prompt_dir: str
):
    prompt_id = utils.make_prompt_id(prompt_name)
    utils.save_prompt(
        prompt_id,
        prompt_text=prompt_text,
        params=params,
        inputs=inputs,
        prompt_dir=prompt_dir,
    )
    return prompt_id


def main():
    utils.init_page_layout()
    session = st.session_state
    oai_client = init_oai_client()
    prompt_ids = list_prompts(PROMPT_DIR)
    print("PromptIds: ", prompt_ids)

    ## RUN + SAVE PROMPT
    col1, col2, col3, col4 = st.columns([4, 2, 2, 2])
    with col2:
        run_button = st.button("Run Prompt", help="Run the prompt")
    with col3:
        save_button = st.button("Save Prompt", help="Save the prompt")
    with col4:
        delete_prompt = st.button("Delete Prompt", help="Delete the prompt")

    ## SIDEBAR
    with st.sidebar:
        prompt_id_index = len(prompt_ids) - 1
        if "prompt_id" in session:
            prompt_id_index = prompt_ids.index(session.prompt_id)
        prompt_id = st.selectbox(
            "Select Prompt",
            options=prompt_ids,
            index=prompt_id_index,
            key="prompt_id",
        )

        if not prompt_id:
            return
        else:
            session.prompt = utils.load_prompt(prompt_id, PROMPT_DIR)

        ## MODEL PARAMS
        model = st.selectbox(
            "Model",
            MODELS,
            index=MODELS.index(session.prompt["params"]["model"]),
        )
        max_tokens = st.number_input(
            "Max tokens",
            value=session.prompt["params"]["max_tokens"],
            min_value=0,
            max_value=2048,
            step=2,
        )
        temperature = st.number_input(
            "Temperature", value=session.prompt["params"]["temperature"], step=0.05
        )
        stop = st.multiselect(
            "Stop",
            STOP_SEQUENCES,
            default=session.prompt["params"]["stop"]
            if session.prompt["params"]["stop"]
            else None,
        )

        def create_prompt_fn(session_state, prompt_name, params):
            if not prompt_name:
                st.error("Prompt name is required")
                return
            new_prompt_id = create_prompt(
                prompt_name=prompt_name,
                prompt_text="",
                params=params,
                inputs={},
                prompt_dir=PROMPT_DIR,
            )
            session_state.prompt_id = new_prompt_id
            session_state.prompt = utils.load_prompt(prompt_id, PROMPT_DIR)

        ## CREATE PROMPT
        st.markdown("---")
        st.markdown("New Prompt")
        prompt_name = st.text_input("Prompt Name")
        params = dict(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop,
        )
        st.button(
            "New Prompt",
            help="Create a new prompt",
            on_click=create_prompt_fn,
            kwargs={
                "session_state": session,
                "prompt_name": prompt_name,
                "params": params,
            },
        )

    prompt_tab, inputs_tab = st.tabs(["Prompt", "Inputs"])

    ## PROMPT TAB
    with prompt_tab:
        prompt_area = st.empty()
        prompt_text = prompt_area.text_area(
            "Prompt",
            value=session.prompt["prompt_text"],
            height=400,
            label_visibility="hidden",
            placeholder="Prompt text..",
        )
        # TODO(bfortuner): Allow running with CMD + ENTER
        if run_button:
            print("Running completion!")
            if stop:
                if "double-newline" in stop:
                    stop.remove("double-newline")
                    stop.append("\n\n")
                if "newline" in stop:
                    stop.remove("newline")
                    stop.append("\n")

            ## COMPLETION
            resp = oai_client.complete(
                prompt_text,
                model=model,  # type: ignore
                max_tokens=max_tokens,  # type: ignore
                temperature=temperature,
                stop=stop or None,
            )

            completion_text = st.text_area(
                "Completion",
                height=300,
                value=resp.get("completion"),
                disabled=True,
                # label_visibility="hidden",
            )

            if completion_text:
                print("Completion Result: \n\n", completion_text)

    if save_button:
        utils.save_prompt(
            prompt_id=prompt_id,
            prompt_text=prompt_text,
            params=dict(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop,
            ),
            inputs={},
            prompt_dir=PROMPT_DIR,
        )
        prompt_name = ""

    if delete_prompt:
        if len(prompt_ids) <= 1:
            st.error("Cannot delete last prompt")
        else:
            utils.delete_prompt(session.prompt_id, PROMPT_DIR)
            del session.prompt_id
            st.experimental_rerun()


if __name__ == "__main__":
    main()
