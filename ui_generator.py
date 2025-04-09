import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Callable

# This module takes instructions (usually from the agent/LLM)
# and generates corresponding Streamlit UI elements.

def render_ui_element(spec: Dict[str, Any], state: Dict[str, Any], callback_handler: Callable):
    """
    Renders a Streamlit UI element based on a specification dictionary.

    Args:
        spec (Dict): Specification for the UI element (e.g., {'type': 'button', 'label': 'Click Me', 'id': 'my_button'})
        state (Dict): Current application state (st.session_state) for context.
        callback_handler (Callable): Function to call when an interactive element is triggered.
    """
    ui_type = spec.get("type")
    element_id = spec.get("id", f"{ui_type}_{hash(json.dumps(spec))}") # Generate a somewhat stable ID

    if ui_type == "markdown":
        st.markdown(spec.get("content", ""), unsafe_allow_html=spec.get("unsafe_allow_html", False))

    elif ui_type == "dataframe":
        data = spec.get("data", [])
        if isinstance(data, list) and data and isinstance(data[0], dict):
            df = pd.DataFrame(data)
            st.dataframe(df)
        elif isinstance(data, pd.DataFrame):
             st.dataframe(data)
        else:
            st.warning(f"Invalid data format for dataframe: {type(data)}")

    elif ui_type == "table": # Simpler table
        data = spec.get("data", [])
        if isinstance(data, list) and data and isinstance(data[0], dict):
            df = pd.DataFrame(data)
            st.table(df)
        elif isinstance(data, pd.DataFrame):
             st.table(data)
        else:
            st.warning(f"Invalid data format for table: {type(data)}")

    elif ui_type == "button":
        label = spec.get("label", "Button")
        key = f"button_{element_id}"
        if st.button(label, key=key):
            # Trigger callback with button info
            callback_handler(element_id, {"action": "button_click", "spec": spec})

    elif ui_type == "radio":
        label = spec.get("label", "Select an option")
        options = spec.get("options", [])
        key = f"radio_{element_id}"
        # Format options if they are dicts (e.g., from alignment suggestions)
        option_map = {}
        display_options = []
        for opt in options:
            if isinstance(opt, dict):
                display_label = opt.get('label', str(opt))
                option_map[display_label] = opt.get('uri', opt) # Store the actual value (URI)
                display_options.append(display_label)
            else:
                display_options.append(str(opt))
                option_map[str(opt)] = opt

        # Use on_change for immediate feedback if needed, or just check value later
        selected_label = st.radio(
            label,
            options=display_options,
            key=key,
            index=spec.get("index", 0),
            horizontal=spec.get("horizontal", False)
        )
        # Store the *actual* selected value (URI) in session state if needed,
        # or pass it back via a confirmation button. For simplicity here,
        # we might need a 'Confirm Selection' button linked to this radio group.
        # We store the current selection to be picked up by a later action.
        state[f'selected_value_{key}'] = option_map.get(selected_label)


    elif ui_type == "form":
        label = spec.get("label", "Form")
        form_key = f"form_{element_id}"
        with st.form(key=form_key):
            st.markdown(f"**{label}**")
            form_elements = spec.get("elements", [])
            form_data = {}
            for elem_spec in form_elements:
                elem_type = elem_spec.get("type")
                elem_id = elem_spec.get("id")
                elem_label = elem_spec.get("label", "")
                elem_key = f"form_elem_{form_key}_{elem_id}"

                if elem_type == "text_input":
                    form_data[elem_id] = st.text_input(elem_label, key=elem_key, value=elem_spec.get("default", ""))
                elif elem_type == "text_area":
                     form_data[elem_id] = st.text_area(elem_label, key=elem_key, value=elem_spec.get("default", ""))
                # Add other form element types (selectbox, etc.) here
                else:
                     st.warning(f"Unsupported form element type: {elem_type}")

            submitted = st.form_submit_button(spec.get("submit_label", "Submit"))
            if submitted:
                 # Trigger callback with form data
                callback_handler(element_id, {"action": "form_submit", "data": form_data, "spec": spec})

    elif ui_type == "info":
         st.info(spec.get("text", "Info"))
    elif ui_type == "warning":
         st.warning(spec.get("text", "Warning"))
    elif ui_type == "error":
         st.error(spec.get("text", "Error"))

    else:
        st.warning(f"Unsupported UI element type: {ui_type}")
