import pytest
from pydantic import ValidationError

from settings import Settings


class TestSettings:
    def test_defaults_with_valid_api_key(self):
        s = Settings(openai_api_key="sk-test")
        assert s.openai_model == "gpt-4.1-mini"
        assert s.chunk_size == 512
        assert s.chunk_overlap == 50
        assert s.debug is False

    def test_strips_api_key(self):
        s = Settings(openai_api_key="  sk-test  ")
        assert s.openai_api_key == "sk-test"

    @pytest.mark.parametrize(
        "field,value,match",
        [
            ("openai_api_key", "", "No OpenAI API key"),
            ("chunk_size", 0, "CHUNK_SIZE"),
            ("chunk_overlap", -1, "CHUNK_OVERLAP"),
            ("memory_token_limit", 0, "MEMORY_TOKEN_LIMIT"),
            ("max_ocr_pages", 0, "MAX_OCR_PAGES"),
            ("embed_batch_size", 0, "EMBED_BATCH_SIZE"),
            ("embed_batch_size", 513, "EMBED_BATCH_SIZE"),
        ],
    )
    def test_field_validation_errors(self, field, value, match):
        data = {"openai_api_key": "sk-test", field: value}
        with pytest.raises(ValidationError, match=match):
            Settings(**data)

    def test_chunk_overlap_must_be_smaller_than_chunk_size(self):
        with pytest.raises(ValidationError, match="CHUNK_OVERLAP must be smaller"):
            Settings(openai_api_key="sk-test", chunk_size=100, chunk_overlap=100)
