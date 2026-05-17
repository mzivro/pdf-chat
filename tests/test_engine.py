from unittest.mock import MagicMock, patch

import pytest
from llama_index.core import Document


@pytest.fixture
def engine():
    with (
        patch("engine.OpenAI"),
        patch("engine.LlamaSettings"),
        patch("engine.ChatMemoryBuffer") as mock_memory_cls,
    ):
        mock_memory_cls.from_defaults.return_value = MagicMock()
        from engine import Engine

        eng = Engine()
        eng.splitter = MagicMock()
        yield eng


class TestEngineValid:
    def test_returns_false_for_short_text(self, engine):
        docs = [Document(text="short")]
        assert engine._valid(docs) is False

    def test_returns_false_for_whitespace_only(self, engine):
        docs = [Document(text="   " * 50)]
        assert engine._valid(docs) is False

    def test_returns_true_when_total_text_exceeds_threshold(self, engine):
        docs = [Document(text="a" * 60), Document(text="b" * 50)]
        assert engine._valid(docs) is True


class TestEngineOcr:
    def test_ocr_concatenates_page_text(self, engine):
        mock_image = MagicMock()
        with (
            patch("engine.convert_from_path", return_value=[mock_image, mock_image]),
            patch("engine.pytesseract.image_to_string", side_effect=["page1", "page2"]),
            patch("engine.settings") as mock_settings,
        ):
            mock_settings.max_ocr_pages = 2
            doc = engine._ocr("/fake/path.pdf")

        assert doc.text == "page1page2"

    def test_ocr_continues_after_page_error(self, engine):
        mock_image = MagicMock()
        with (
            patch("engine.convert_from_path", return_value=[mock_image]),
            patch(
                "engine.pytesseract.image_to_string",
                side_effect=RuntimeError("tesseract failed"),
            ),
            patch("engine.settings") as mock_settings,
        ):
            mock_settings.max_ocr_pages = 1
            doc = engine._ocr("/fake/path.pdf")

        assert doc.text == ""


class TestEngineLoadPdfs:
    def test_loads_and_chunks_valid_pdf(self, engine):
        doc = Document(text="x" * 150, metadata={})
        node = MagicMock()
        engine.loader.load_data = MagicMock(return_value=[doc])
        engine.splitter.get_nodes_from_documents = MagicMock(return_value=[node])

        nodes = engine._load_pdfs([(b"%PDF-fake", "sample.pdf")])

        assert nodes == [node]
        engine.splitter.get_nodes_from_documents.assert_called_once()
        loaded_docs = engine.splitter.get_nodes_from_documents.call_args[0][0]
        assert loaded_docs[0].metadata["filename"] == "sample.pdf"

    def test_falls_back_to_ocr_when_extraction_invalid(self, engine):
        ocr_doc = Document(text="ocr text " * 20)
        node = MagicMock()
        engine.loader.load_data = MagicMock(return_value=[Document(text="tiny")])
        engine._ocr = MagicMock(return_value=ocr_doc)
        engine.splitter.get_nodes_from_documents = MagicMock(return_value=[node])

        nodes = engine._load_pdfs([(b"%PDF-fake", "scan.pdf")])

        engine._ocr.assert_called_once()
        assert nodes == [node]

    def test_removes_temp_file_after_processing(self, engine, tmp_path):
        doc = Document(text="x" * 150)
        engine.loader.load_data = MagicMock(return_value=[doc])
        engine.splitter.get_nodes_from_documents = MagicMock(return_value=[])

        created_paths = []

        original_named_temp = __import__("tempfile").NamedTemporaryFile

        def tracking_named_temp(*args, **kwargs):
            tmp = original_named_temp(*args, **kwargs)
            created_paths.append(tmp.name)
            return tmp

        with patch("engine.tempfile.NamedTemporaryFile", tracking_named_temp):
            engine._load_pdfs([(b"%PDF-fake", "file.pdf")])

        assert created_paths
        assert not __import__("os").path.exists(created_paths[0])


class TestEngineIngestAndAsk:
    def test_ingest_resets_memory_and_builds_chat_engine(self, engine):
        mock_index = MagicMock()
        mock_chat = MagicMock()
        mock_index.as_chat_engine.return_value = mock_chat
        mock_node = MagicMock()

        with patch("engine.VectorStoreIndex", return_value=mock_index):
            engine._load_pdfs = MagicMock(return_value=[mock_node])
            uploaded = [MagicMock(read=MagicMock(return_value=b"pdf"), name="a.pdf")]

            engine.ingest(uploaded)

        engine.memory.reset.assert_called_once()
        mock_index.as_chat_engine.assert_called_once()
        assert engine.chat_engine is mock_chat

    def test_ask_yields_tokens_from_stream(self, engine):
        mock_response = MagicMock()
        mock_response.response_gen = iter(["Hello", " ", "world"])
        engine.chat_engine = MagicMock()
        engine.chat_engine.stream_chat.return_value = mock_response

        tokens = list(engine.ask("What is this?"))

        assert tokens == ["Hello", " ", "world"]
        engine.chat_engine.stream_chat.assert_called_once_with("What is this?")
