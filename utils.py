"""Utility functions for the Streamlit apps."""
import json
import os
import uuid

import streamlit as st
from stqdm import stqdm


def make_prompt_id(prompt_name: str):
    """Make a prompt ID from a chat name."""
    return f"{prompt_name}_{str(uuid.uuid1())[:8]}"


def save_prompt(
    prompt_id: str,
    prompt: str,
    params: dict,
    inputs: dict,
    prompt_dir: str = "./prompts/",
):
    """Save a prompt transcript to disk."""
    params_fpath = os.path.join(prompt_dir, prompt_id, "params.json")
    prompt_fpath = os.path.join(prompt_dir, prompt_id, "prompt.txt")
    inputs_fpath = os.path.join(prompt_dir, prompt_id, "inputs.json")

    os.makedirs(os.path.dirname(params_fpath), exist_ok=True)
    json.dump(params, open(params_fpath, "w"))
    open(prompt, "w").write(prompt_fpath)
    json.dump(inputs, open(inputs_fpath, "w"), indent=2)


def load_prompt(prompt_id: str, prompt_dir: str = "./prompts/") -> dict:
    """Load a prompt from disk by prompt_id."""
    params_fpath = os.path.join(prompt_dir, prompt_id, "params.json")
    prompt_fpath = os.path.join(prompt_dir, prompt_id, "prompt.txt")
    inputs_fpath = os.path.join(prompt_dir, prompt_id, "inputs.json")
    return {
        "params": json.load(open(params_fpath)),
        "prompt": open(prompt_fpath).read(),
        "inputs": json.load(open(inputs_fpath)),
    }


def check_password(debug=False):
    """Returns `True` if the user had the correct password."""
    if debug:
        return True

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True


def sleep_and_return(st_container, time_per_step, num_steps):
    with st_container:
        for _ in stqdm(range(num_steps)):
            time.sleep(time_per_step)


def init_session_state(widget_keys: List[str], query_params: dict):
    for key in widget_keys:
        if query_params.get(key) is not None:
            query_value = query_params[key][0]
            if key not in st.session_state:
                if "bool" in key:
                    query_value = True if query_value.lower() == "true" else False
                st.session_state[key] = query_value


def write_query_params(widget_values: Dict[str, str]):
    query_params = {}
    for widget_name, widget_value in widget_values.items():
        session_value = st.session_state.get(widget_name)
        if "bool" in widget_name and widget_value is False:
            query_value = session_value if session_value is not None else widget_value
        else:
            query_value = widget_value if widget_value is not None else session_value
        if query_value is not None:
            query_params[widget_name] = query_value

    st.experimental_set_query_params(**query_params)
