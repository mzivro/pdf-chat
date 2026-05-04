from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Document, VectorStoreIndex
from llama_index.core import Settings as LlamaSettings
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.readers.file import PDFReader
from llama_index.llms.openai import OpenAI
from pdf2image import convert_from_path
from settings import settings
from logger import logger

import streamlit as st
import pytesseract
import tempfile
import os


class Engine:
    """
    Core document processing and chat engine.

    Responsible for:
    - PDF ingestion
    - Text extraction (including OCR fallback)
    - Document chunking and embedding
    - Chat-based querying with memory

    Attributes
    ----------
    llm : OpenAI
        Language model instance.
    loader : PDFReader
        PDF document loader.
    splitter : SentenceSplitter
        Text chunking utility.
    memory : ChatMemoryBuffer
        Conversational memory buffer.
    chat_engine : object or None
        Chat engine instance created after ingestion.
    """
    def __init__(self):
        """
        Initialize engine components.

        Sets up LLM, embedding model, document loader,
        text splitter, and memory buffer.
        """
        logger("Engine initiated")
        self.llm = OpenAI(model=settings.openai_model, api_key=settings.openai_api_key)

        LlamaSettings.embed_model = OpenAIEmbedding(
            api_key=settings.openai_api_key,
            embed_batch_size=settings.embed_batch_size
        )

        self.loader = PDFReader()
        self.splitter = SentenceSplitter(
            chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap
        )

        self.memory = ChatMemoryBuffer.from_defaults(
            token_limit=settings.memory_token_limit
        )
        self.chat_engine = None

    def ingest(self, uploaded_files):
        """
        Ingest uploaded PDF files.

        Parameters
        ----------
        uploaded_files : list
            List of uploaded file-like objects.

        Notes
        -----
        This method resets memory and rebuilds the vector index.
        """
        self.memory.reset()
        self.chat_engine = None

        file_data = [(file.read(), file.name) for file in uploaded_files]
        nodes = self._load_pdfs(file_data)

        index = VectorStoreIndex(nodes)

        self.chat_engine = index.as_chat_engine(
            chat_mode="context", memory=self.memory, llm=self.llm
        )

    def ask(self, prompt):
        """
        Query the chat engine.

        Parameters
        ----------
        prompt : str
            User query.

        Yields
        ------
        str
            Response tokens streamed incrementally.
        """
        response = self.chat_engine.stream_chat(prompt)

        for token in response.response_gen:
            yield token

    def _ocr(self, path):
        """
        Perform OCR on a PDF file.

        Parameters
        ----------
        path : str
            Path to PDF file.

        Returns
        -------
        Document
            Extracted text wrapped in a Document object.

        Notes
        -----
        Processes up to MAX_OCR_PAGES pages.
        """
        logger("OCR engaged")

        images = convert_from_path(path, last_page=settings.max_ocr_pages)
        text = ""

        for img in images:
            try:
                text += pytesseract.image_to_string(img, lang="pol+eng")
            except Exception as e:
                logger(f"OCR error: {e}")

        return Document(text=text)

    def _valid(self, docs):
        """
        Check if extracted documents contain sufficient text.

        Parameters
        ----------
        docs : list of Document

        Returns
        -------
        bool
            True if total text length exceeds threshold.
        """
        return sum(len(d.text.strip()) for d in docs) > 100

    def _load_pdfs(self, file_bytes_list):
        """
        Load and process PDF files.

        Parameters
        ----------
        file_bytes_list : list of tuple
            List of (file_bytes, filename).

        Returns
        -------
        list
            List of processed nodes ready for indexing.

        Notes
        -----
        Falls back to OCR if standard extraction fails.
        Temporary files are cleaned up after processing.
        """
        all_nodes = []

        for file_bytes, name in file_bytes_list:
            path = None
            try:
                # temp file save
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(file_bytes)
                    path = tmp.name

                # load docs
                docs = self.loader.load_data(file=path)

                # if PDFReader fails to get text, engage OCR
                if not docs or not self._valid(docs):
                    docs = [self._ocr(path)]

                # metadata
                for doc in docs:
                    doc.metadata = doc.metadata or {}
                    doc.metadata["filename"] = name

                # chunking
                nodes = self.splitter.get_nodes_from_documents(docs)
                all_nodes.extend(nodes)
            finally:
                if path and os.path.exists(path):
                    os.remove(path)

        logger(f"In total {len(all_nodes)} nodes were created")

        return all_nodes
