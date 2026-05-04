import streamlit as st
import tempfile
import os

from engine import Engine


class PDFChat:
    """
    Streamlit-based user interface for PDF question-answering.

    This class manages file upload, document ingestion, and chat interaction
    using a backend engine.

    Attributes
    ----------
    None
        State is managed via Streamlit session_state.
    """
    def __init__(self):
        """
        Initialize Streamlit UI and session state.

        Sets up page configuration and initializes engine,
        readiness flag, and message history.
        """
        st.set_page_config(page_title="PDF Chat", layout="centered")
        st.title("PDF Chat")

        if "engine" not in st.session_state:
            st.session_state.engine = Engine()

        if "ready" not in st.session_state:
            st.session_state.ready = False

        if "messages" not in st.session_state:
            st.session_state.messages = []

    def run(self):
        """
        Run the application.

        This method orchestrates rendering of file upload
        and chat sections.
        """
        self._files_sector()
        self._chat_section()

    def _files_sector(self):
        """
        Render file upload and ingestion controls.

        Handles PDF uploads and triggers ingestion into the engine.
        """
        uploaded_files = st.file_uploader(
            "Load sample data",
            type="pdf",
            accept_multiple_files=True,
            max_upload_size=20,
        )

        if st.button(
            "Ingest data",
            width="stretch",
            help="This button loads data into chat engine and resets the session",
        ):
            if uploaded_files:
                try:
                    with st.spinner("Processing..."):
                        st.session_state.engine.ingest(uploaded_files)
                        st.session_state.ready = True
                        st.session_state.messages = []
                except Exception as e:
                    st.error(f"Ingest failed: {e}")
            else:
                st.warning("No files uploaded")

    def _chat_section(self):
        """
        Render chat interface.

        Displays conversation history and handles user input.
        """
        if st.session_state.ready:
            self._render_history()

            if prompt := st.chat_input("What is your question?"):
                self._handle_user_input(prompt)

    def _render_history(self):
        """
        Render chat message history.

        Iterates over stored messages and displays them
        using Streamlit chat components.
        """
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    def _handle_user_input(self, prompt):
        """
        Process user query and generate response.

        Parameters
        ----------
        prompt : str
            User input question.

        Notes
        -----
        Response is streamed token-by-token from the engine.
        """
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            response = ""

            try:
                for token in st.session_state.engine.ask(prompt):
                    response += token
                    placeholder.markdown(response + "█")

                placeholder.markdown(response)

            except Exception as e:
                st.error(f"Application error: {e}")

        st.session_state.messages.append({"role": "assistant", "content": response})
