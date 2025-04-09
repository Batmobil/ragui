import streamlit as st
from typing import Dict, Any, List, Optional
import json
import pandas as pd # Import pandas for DataFrame creation

# Import other modules
import llm_interface # Now uses placeholders
import ontology_processor
import document_processor
import ui_generator

class OntologyAgent:
    def __init__(self, ontology_proc: ontology_processor.OntologyProcessor):
        self.ontology_proc = ontology_proc
        # Initialize state variables
        if 'agent_initialized' not in st.session_state:
            st.session_state.ontology_loaded = False
            st.session_state.ontology_path = None
            st.session_state.documents = {} # {filename: content}
            st.session_state.last_extraction_results = {} # {doc_name: results}
            # Store the *type* of result expected if using placeholders
            st.session_state.last_extraction_type = None
            st.session_state.last_analysis_results = None # Analysis not implemented via LLM placeholder yet
            st.session_state.last_query_results = None
            st.session_state.last_gaps_assessment = None # Stores the dict {gaps_found: [], summary: str}
            st.session_state.current_alignment_task = None # Not used for placeholder suggestions directly
            st.session_state.last_alignment_suggestions = None # Stores the dict {entity_text: str, suggestions: []}
            st.session_state.conversation_history = []
            st.session_state.pending_ui_specs = [] # Specs to be rendered in the next cycle
            st.session_state.agent_initialized = True
            self._add_message("assistant", "Hello! I am your Generative Ontology Assistant (LLM Placeholder Mode). How can I help?")

    def _clear_pending_ui(self):
        st.session_state.pending_ui_specs = []
        # Clear selections associated with previous UI
        keys_to_remove = [k for k in st.session_state if k.startswith('selected_value_')]
        for k in keys_to_remove:
            del st.session_state[k]
        # Reset task-specific state that UI relied on
        st.session_state.last_alignment_suggestions = None


    def _add_message(self, role: str, content: Any, is_explanation: bool = False):
        # Ensure content is displayable (convert dicts/lists to JSON strings for chat history)
        if isinstance(content, (dict, list)):
             display_content = f"```json\n{json.dumps(content, indent=2)}\n```"
        else:
             display_content = str(content)

        st.session_state.conversation_history.append({
            "role": role,
            "content": display_content, # Store the string representation
            "is_explanation": is_explanation
        })

    def _add_ui_spec(self, ui_spec: Dict[str, Any]):
        if "id" not in ui_spec:
            ui_spec["id"] = f"{ui_spec.get('type', 'ui')}_{hash(json.dumps(ui_spec, sort_keys=True))}"
        st.session_state.pending_ui_specs.append(ui_spec)

    def handle_user_input(self, user_input: str):
        self._add_message("user", user_input)
        self._clear_pending_ui()

        # 1. Interpret Request using LLM Placeholder
        context = {
            "ontology_loaded": st.session_state.ontology_loaded,
            "ontology_path": st.session_state.ontology_path,
            "documents": st.session_state.documents,
            "ontology_processor": self.ontology_proc if st.session_state.ontology_loaded else None,
            "last_extraction_results": bool(st.session_state.last_extraction_results),
            "last_gaps_assessment": bool(st.session_state.last_gaps_assessment),
        }
        # Pass history for context
        llm_response = llm_interface.interpret_request(user_input, context, st.session_state.conversation_history)

        action = llm_response.get("action", "clarify")
        params = llm_response.get("parameters", {})
        explanation = llm_response.get("explanation", "[LLM Placeholder: No explanation provided]")
        confidence = llm_response.get("confidence", 0.0) # Placeholder returns 0.0

        # 2. Agent Reasoning Step
        # Use explanation from LLM placeholder if action isn't simple/fallback
        if action not in ["greet", "clarify", "help", "reset", "load_ontology_prompt", "load_document_prompt", "placeholder_action"]:
             self._add_message("assistant", f"Okay, based on the LLM placeholder interpretation (Action: {action}), I'll proceed. {explanation}", is_explanation=True)
        elif action == "clarify" or action == "placeholder_action":
             # Show the raw explanation/placeholder content if clarification needed or intent failed
             self._add_message("assistant", explanation)

        # 3. Execute Action
        self._execute_action(action, params)

    def handle_ui_callback(self, element_id: str, event_data: Dict):
        action = event_data.get("action")
        spec = event_data.get("spec", {})
        print(f"UI Callback: element_id={element_id}, action={action}")

        self._clear_pending_ui()

        self._add_message("assistant", f"Processing your interaction with element '{spec.get('label', element_id)}'...", is_explanation=True)

        if action == "button_click":
            if spec.get("purpose") == "confirm_alignment":
                radio_key = spec.get("linked_radio_key")
                selected_uri = st.session_state.get(f'selected_value_{radio_key}')
                # Get context from when the suggestions were generated
                alignment_context = st.session_state.get("last_alignment_suggestions")

                if selected_uri and alignment_context:
                    entity_text = alignment_context.get("entity_text", "[Unknown Entity]")
                    if selected_uri == "no_match" or selected_uri == "placeholder_uri": # Handle placeholder case
                        response = f"Understood. For entity '**{entity_text}**', you selected '{selected_uri}'. (Alignment not performed due to placeholder mode)."
                        self._add_message("assistant", response)
                    else:
                        # Actual alignment logic would go here
                        response = f"Confirmed: '**{entity_text}**' alignment with <{selected_uri}> selected. (Note: Alignment triple not added in placeholder mode)."
                        self._add_message("assistant", response)
                else:
                    self._add_message("assistant", "Sorry, could not process alignment confirmation (missing selection or context).", ui_spec={"type": "error", "text": "Alignment confirmation failed."})
                    self._add_ui_spec({"type": "error", "text": "Alignment confirmation failed."})

            else:
                 self._add_message("assistant", f"Button '{spec.get('label')}' clicked. (Placeholder interaction - no specific action defined).")

        elif action == "form_submit":
             form_data = event_data.get("data", {})
             self._add_message("assistant", f"Received data from form '{spec.get('label')}':")
             # Display the received data as JSON
             self._add_ui_spec({"type": "markdown", "content": f"```json\n{json.dumps(form_data, indent=2)}\n```"})
             self._add_message("assistant", "(Placeholder - Form data not processed further)")


    def _execute_action(self, action: str, params: Dict):
        """Executes the action logic, now interacting with LLM placeholders."""

        # --- Basic Actions (No LLM needed) ---
        if action == "greet":
            self._add_message("assistant", "Hello! (Placeholder Mode)")
        elif action == "help":
            # Keep help text as before
            help_text = "..." # (Same help text as before)
            self._add_message("assistant", help_text)
            self._add_ui_spec({"type": "markdown", "content": help_text})
        elif action == "reset":
             # (Same reset logic as before)
             st.session_state.ontology_loaded = False # etc...
             st.session_state.conversation_history = []
             st.session_state.pending_ui_specs = []
             self._add_message("assistant", "State has been reset.")
        elif action == "load_ontology_prompt":
            self._add_message("assistant", "Use the sidebar to upload an ontology file.")
        elif action == "load_document_prompt":
             self._add_message("assistant", "Use the sidebar to upload document(s).")
        elif action == "clarify" or action == "placeholder_action":
             # The explanation/clarification message was already added by handle_user_input
             self._add_message("assistant", "Could you please rephrase or provide more details?") # Generic follow-up

        # --- Actions Requiring Document(s) -> LLM Placeholder ---
        elif action in ["extract_entities", "summarize_document"]:
            if not st.session_state.documents:
                 self._add_message("assistant", "Action requires loaded documents.", ui_spec={"type": "warning", "text":"No documents loaded."}); return

            target_doc_name = params.get("target_document", "all")
            docs_to_process = {}
            # (Logic to select docs_to_process remains the same) ...
            if target_doc_name == "all": docs_to_process = st.session_state.documents
            elif target_doc_name in st.session_state.documents: docs_to_process = {target_doc_name: st.session_state.documents[target_doc_name]}
            else: self._add_message("assistant", f"Document '{target_doc_name}' not found.", ui_spec={"type": "warning", "text":f"Doc not found: {target_doc_name}"}); return

            extraction_type = "entities" if action == "extract_entities" else "summary"
            st.session_state.last_extraction_type = extraction_type # Store type
            results_store = {} # Store actual placeholder results

            self._add_message("assistant", f"Calling LLM placeholder for '{extraction_type}' on '{target_doc_name}'...", is_explanation=True)
            for name, content in docs_to_process.items():
                if content:
                    # --- LLM Placeholder Call ---
                    llm_result = llm_interface.perform_extraction_llm(content, extraction_type)
                    results_store[name] = llm_result # Store placeholder result
                else:
                     self._add_message("assistant", f"Skipping '{name}' (no content).")

            st.session_state.last_extraction_results = results_store # Store results

            # --- Display Placeholder Result ---
            self._add_message("assistant", f"LLM Placeholder response received for {extraction_type}:")
            if extraction_type == "entities":
                all_entities = []
                for doc_name, entities in results_store.items():
                    if isinstance(entities, list): # Check if placeholder returned a list structure
                         for entity in entities:
                             # Add doc name if placeholder structure allows
                             if isinstance(entity, dict): entity['document'] = doc_name
                             all_entities.append(entity)
                # Use DataFrame even for placeholder text
                self._add_ui_spec({"type": "dataframe", "data": pd.DataFrame(all_entities), "id": "extraction_results_table"})
            else: # Summary or keywords
                 for doc_name, result in results_store.items():
                      self._add_ui_spec({"type": "markdown", "content": f"**{doc_name}:**\n\n{result}"})


        # --- Actions Requiring Ontology -> LLM Placeholder ---
        elif action == "generate_ontology_business_summary":
            if not st.session_state.ontology_loaded:
                self._add_message("assistant", "Action requires loaded ontology.", ui_spec={"type": "warning", "text":"Ontology not loaded."}); return

            self._add_message("assistant", "Gathering info and calling LLM placeholder for ontology summary...", is_explanation=True)
            ontology_stats = self.ontology_proc.get_summary()
            key_concepts = self.ontology_proc.get_key_concepts_sample(sample_size=5) # Smaller sample ok

            # --- LLM Placeholder Call ---
            summary_text = llm_interface.generate_ontology_business_summary_llm(
                ontology_stats=ontology_stats,
                key_concepts=key_concepts,
                ontology_name=st.session_state.get("ontology_path")
            )

            # --- Display Placeholder Result ---
            self._add_message("assistant", "LLM Placeholder response for ontology summary:")
            self._add_ui_spec({"type": "markdown", "content": summary_text, "id": "ontology_summary_text"})

        elif action == "query_ontology":
            if not st.session_state.ontology_loaded:
                self._add_message("assistant", "Action requires loaded ontology.", ui_spec={"type": "warning", "text":"Ontology not loaded."}); return

            query_desc = params.get("query_description", "unknown topic")
            self._add_message("assistant", f"Calling LLM placeholder to generate SPARQL for '{query_desc}'...", is_explanation=True)

            # --- LLM Placeholder Call ---
            # Prepare context (optional, could be empty)
            onto_context = self.ontology_proc.get_key_concepts_sample(sample_size=5)
            onto_context["namespaces"] = self.ontology_proc.namespaces

            sparql_query = llm_interface.generate_sparql_query_llm(query_desc, onto_context)

            # --- Display Placeholder Result & Attempt Execution ---
            if sparql_query:
                self._add_message("assistant", "LLM Placeholder generated SPARQL query:")
                self._add_ui_spec({"type":"markdown", "content": f"```sparql\n{sparql_query}\n```"})
                self._add_message("assistant", "Attempting to execute the generated query...")
                results = self.ontology_proc.run_sparql_query(sparql_query)
                st.session_state.last_query_results = results
                if results is not None:
                     self._add_message("assistant", "Query Execution Result:")
                     if results:
                         self._add_ui_spec({"type": "dataframe", "data": pd.DataFrame(results), "id": "query_results_table"})
                     else:
                         self._add_ui_spec({"type": "info", "text": "Query executed, no results returned."})
                else:
                     self._add_message("assistant", "Query execution failed (check query syntax or ontology).", ui_spec={"type":"error", "text":"Query execution failed"})
            else:
                 self._add_message("assistant", "LLM Placeholder failed to generate a SPARQL query.", ui_spec={"type":"warning", "text":"SPARQL generation failed"})

        elif action == "explain_ontology_concept":
            if not st.session_state.ontology_loaded:
                 self._add_message("assistant", "Action requires loaded ontology.", ui_spec={"type": "warning", "text":"Ontology not loaded."}); return

            concept_uri = params.get("concept_uri") # Assume intent detection provided URI
            concept_term = params.get("concept_term", concept_uri) # Fallback display name

            if not concept_uri:
                 # If LLM intent detection failed to get URI, try simple term lookup?
                 # For now, require URI from params.
                 self._add_message("assistant", f"Cannot explain concept: missing URI parameter for term '{concept_term}'.", ui_spec={"type":"error", "text":"Missing URI"}); return

            self._add_message("assistant", f"Getting details for <{concept_uri}> and calling LLM placeholder for explanation...", is_explanation=True)
            details = self.ontology_proc.get_entity_details(concept_uri)

            if not details:
                 self._add_message("assistant", f"Could not retrieve details for <{concept_uri}> from the ontology.", ui_spec={"type":"error", "text":f"Details not found for {concept_uri}"}); return

            # --- LLM Placeholder Call ---
            explanation_text = llm_interface.generate_concept_explanation_llm(details)

            # --- Display Placeholder Result ---
            self._add_message("assistant", f"LLM Placeholder explanation for {concept_term} (<{concept_uri}>):")
            self._add_ui_spec({"type": "markdown", "content": explanation_text})


        # --- Actions Requiring Both -> LLM Placeholder ---
        elif action == "assess_gaps":
            if not st.session_state.ontology_loaded or not st.session_state.documents:
                 self._add_message("assistant", "Action requires loaded ontology and documents.", ui_spec={"type": "warning", "text":"Ontology or doc missing."}); return

            target_doc_name = params.get("target_document", "all")
            docs_to_process = {}
            # (Logic to select docs_to_process remains the same) ...
            if target_doc_name == "all": docs_to_process = st.session_state.documents
            elif target_doc_name in st.session_state.documents: docs_to_process = {target_doc_name: st.session_state.documents[target_doc_name]}
            else: self._add_message("assistant", f"Document '{target_doc_name}' not found.", ui_spec={"type": "warning", "text":f"Doc not found: {target_doc_name}"}); return


            # 1. Extract Terms using LLM Placeholder
            self._add_message("assistant", f"Step 1: Calling LLM Placeholder to extract terms from '{target_doc_name}'...", is_explanation=True)
            all_extracted_terms = []
            for name, content in docs_to_process.items():
                 if content:
                     # --- LLM Placeholder Call ---
                     extracted = llm_interface.perform_extraction_llm(content, "entities")
                     # Ensure extracted is a list before extending
                     if isinstance(extracted, list):
                         # Add document source info if possible
                         for term in extracted:
                             if isinstance(term, dict): term['document'] = name
                         all_extracted_terms.extend(extracted)
                     else:
                          # Handle case where placeholder didn't return a list
                           all_extracted_terms.append({"text": str(extracted), "type": "PLACEHOLDER_ERROR", "document": name})

            if not all_extracted_terms or all_extracted_terms[0].get("type") == "PLACEHOLDER": # Check if extraction yielded placeholder
                 self._add_message("assistant", "Term extraction (placeholder) did not yield usable results for gap assessment.", ui_spec={"type":"info", "text":"Term extraction failed/placeholder."}); return

            # 2. Call LLM Placeholder for Gap Assessment
            self._add_message("assistant", "Step 2: Calling LLM Placeholder for gap assessment...", is_explanation=True)
            classes = self.ontology_proc.get_classes()
            individuals = self.ontology_proc.get_individuals()
            labels = self.ontology_proc.get_all_labels()

            # --- LLM Placeholder Call ---
            gaps_result = llm_interface.assess_knowledge_gaps_llm(
                extracted_terms=all_extracted_terms, # Pass the results from step 1
                ontology_classes=classes,
                ontology_individuals=individuals,
                ontology_labels=labels
            )
            st.session_state.last_gaps_assessment = gaps_result

            # 3. Display Placeholder Results
            self._add_message("assistant", "LLM Placeholder response for knowledge gaps:")
            summary = gaps_result.get('summary', "[Placeholder summary missing]")
            gaps_found = gaps_result.get('gaps_found', [])
            self._add_ui_spec({"type": "markdown", "content": f"**Summary:** {summary}"})
            if gaps_found:
                 # Use DataFrame even for placeholder data
                 self._add_ui_spec({"type": "dataframe", "data": pd.DataFrame(gaps_found), "id": "gaps_table"})
            else:
                 self._add_ui_spec({"type": "info", "text": "Placeholder indicated no gaps found or failed."})


        elif action == "align_entity":
            if not st.session_state.ontology_loaded:
                 self._add_message("assistant", "Action requires loaded ontology.", ui_spec={"type": "warning", "text":"Ontology not loaded."}); return

            entity_text = params.get("entity_to_align")
            if not entity_text:
                 self._add_message("assistant", "Missing 'entity_to_align' parameter.", ui_spec={"type":"error", "text":"Missing parameter"}); return

            self._add_message("assistant", f"Calling LLM placeholder to find alignments for '{entity_text}'...", is_explanation=True)
            classes = self.ontology_proc.get_classes()
            individuals = self.ontology_proc.get_individuals()
            labels = self.ontology_proc.get_all_labels()

            # --- LLM Placeholder Call ---
            alignment_suggestions = llm_interface.suggest_alignment_llm(entity_text, classes, individuals, labels)
            st.session_state.last_alignment_suggestions = alignment_suggestions # Store for callback context

            # --- Display Placeholder Suggestions UI ---
            self._add_message("assistant", "LLM Placeholder response for alignment suggestions:")
            suggestions = alignment_suggestions.get("suggestions", [])
            actual_entity = alignment_suggestions.get("entity_text", entity_text) # Use text from placeholder if possible

            if suggestions:
                 # Add "no match" if placeholder didn't (though prompt asks it to)
                 if not any(s.get("uri") == "no_match" for s in suggestions):
                     suggestions.append({"uri": "no_match", "label": "No suitable match / Create new", "type": "action", "score": 0.1})

                 radio_key = f"radio_align_{hash(actual_entity)}"
                 # The UI generator should handle the dict format from the placeholder
                 self._add_ui_spec({
                     "type": "radio",
                     "label": f"Select match for '{actual_entity}':",
                     "options": suggestions, # Pass suggestion list directly
                     "id": radio_key
                 })
                 self._add_ui_spec({
                     "type": "button",
                     "label": f"Confirm Alignment for '{actual_entity}'",
                     "id": f"button_confirm_align_{hash(actual_entity)}",
                     "purpose": "confirm_alignment",
                     "linked_radio_key": radio_key
                 })
            else:
                 self._add_message("assistant", f"LLM Placeholder found no alignment suggestions for '{actual_entity}'.", ui_spec={"type":"info", "text":"No suggestions"})

        # --- Experimental / Other ---
        elif action == "suggest_ontology_modification":
             self._add_message("assistant", f"LLM Interpretation: Suggest Ontology Modification based on: '{params.get('raw_request', 'request')}'", is_explanation=True)
             self._add_message("assistant", "(Placeholder Action: This would involve complex LLM analysis to propose specific ontology changes (e.g., new triples). Not implemented.)")
             # Could add a UI spec for a form here as a next step if needed

        else:
             # Fallback for unknown actions returned by placeholder (unlikely if prompt is good)
             self._add_message("assistant", f"Unknown action '{action}' received from LLM placeholder. Please try again.")
