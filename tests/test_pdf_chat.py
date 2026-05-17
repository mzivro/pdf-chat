from types import SimpleNamespace
from unittest.mock import MagicMock, patch


class TestPDFChatHandleUserInput:
    def test_appends_user_and_assistant_messages(self):
        mock_engine = MagicMock()
        mock_engine.ask.return_value = iter(["Answer"])

        session = SimpleNamespace(
            engine=mock_engine,
            ready=True,
            messages=[],
        )

        with (
            patch("pdf_chat.st") as mock_st,
            patch("pdf_chat.st.session_state", session, create=True),
        ):
            mock_st.chat_message.return_value.__enter__ = MagicMock(
                return_value=MagicMock()
            )
            mock_st.chat_message.return_value.__exit__ = MagicMock(return_value=False)
            mock_st.empty.return_value = MagicMock()

            from pdf_chat import PDFChat

            chat = object.__new__(PDFChat)
            chat._handle_user_input("What is in the PDF?")

        assert session.messages == [
            {"role": "user", "content": "What is in the PDF?"},
            {"role": "assistant", "content": "Answer"},
        ]
        mock_engine.ask.assert_called_once_with("What is in the PDF?")
