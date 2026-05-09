from pydantic import ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.

    This class defines all runtime parameters used across the application,
    including model configuration, chunking strategy, and performance limits.
    Validation is performed using Pydantic validators.

    Parameters
    ----------
    openai_api_key : str
        API key used to authenticate with OpenAI services.
    openai_model : str, optional
        Name of the OpenAI model to use (default is "gpt-4.1-mini").
    chunk_size : int, optional
        Maximum size of text chunks used during document splitting.
    chunk_overlap : int, optional
        Number of overlapping tokens between consecutive chunks.
    memory_token_limit : int, optional
        Maximum number of tokens stored in conversational memory.
    max_ocr_pages : int, optional
        Maximum number of PDF pages processed using OCR.
    embed_batch_size : int, optional
        Batch size used during embedding generation.
    debug : bool, optional
        Enables debug logging when set to True.

    Raises
    ------
    ValueError
        If any configuration parameter is invalid.
    """

    openai_api_key: str
    openai_model: str = "gpt-4.1-mini"
    chunk_size: int = 512
    chunk_overlap: int = 50
    memory_token_limit: int = 3000
    max_ocr_pages: int = 10
    embed_batch_size: int = 64
    debug: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    @field_validator("openai_api_key")
    def validate_openai_api_key(cls, v):
        """
        Validate OpenAI API key.

        Parameters
        ----------
        v : str
            API key string.

        Returns
        -------
        str
            Stripped API key.

        Raises
        ------
        ValueError
            If API key is empty.
        """
        v = v.strip()
        if not v:
            raise ValueError("No OpenAI API key provided")
        return v

    @field_validator("chunk_size")
    def validate_chunk_size(cls, v):
        """
        Validate chunk size.

        Parameters
        ----------
        v : int
            Chunk size.

        Returns
        -------
        int
            Validated chunk size.

        Raises
        ------
        ValueError
            If chunk size is non-positive.
        """
        if v <= 0:
            raise ValueError("CHUNK_SIZE must be positive and non-zero")
        return v

    @field_validator("chunk_overlap")
    def validate_chunk_overlap(cls, v):
        """
        Validate chunk overlap.

        Parameters
        ----------
        v : int
            Chunk overlap.

        Returns
        -------
        int
            Validated chunk overlap.

        Raises
        ------
        ValueError
            If chunk overlap is lower than zero.
        """
        if v < 0:
            raise ValueError("CHUNK_OVERLAP must be positive")
        return v

    @field_validator("memory_token_limit")
    def validate_memory_token_limit(cls, v):
        """
        Validate memory token limit.

        Parameters
        ----------
        v : int
            Memory token limit.

        Returns
        -------
        int
            Validated memory token limit.

        Raises
        ------
        ValueError
            If memory token limit is non-positive.
        """
        if v <= 0:
            raise ValueError("MEMORY_TOKEN_LIMIT must be positive")
        return v

    @field_validator("max_ocr_pages")
    def validate_max_ocr_pages(cls, v):
        """
        Validate max ocr pages.

        Parameters
        ----------
        v : int
            Max ocr pages.

        Returns
        -------
        int
            Validated max ocr pages.

        Raises
        ------
        ValueError
            If max ocr pages is non-positive.
        """
        if v <= 0:
            raise ValueError("MAX_OCR_PAGES must be positive")
        return v

    @field_validator("embed_batch_size")
    def validate_embed_batch_size(cls, v):
        """
        Validate embed batch size.

        Parameters
        ----------
        v : int
            Embed batch size.

        Returns
        -------
        int
            Validated embed batch size.

        Raises
        ------
        ValueError
            If embed batch size is not in <1; 512> range.
        """
        if not (1 <= v <= 512):
            raise ValueError("EMBED_BATCH_SIZE must be between 1 and 512")
        return v

    @model_validator(mode="after")
    def validate_chunk_config(self):
        """
        Validate consistency between chunk size and overlap.

        Returns
        -------
        Settings

        Raises
        ------
        ValueError
            If overlap is greater than or equal to chunk size.
        """
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
        return self


try:
    settings = Settings()
except ValidationError as e:
    raise RuntimeError(f"Invalid configuration:\n{e}") from e
