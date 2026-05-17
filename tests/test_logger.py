from unittest.mock import patch

from logger import Logger


class TestLogger:
    def test_writes_when_enabled(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with patch("logger.settings") as mock_settings:
            mock_settings.debug = True
            log = Logger()
            log("hello")

        logfile = tmp_path / "logfile.txt"
        assert logfile.exists()
        content = logfile.read_text()
        assert "hello" in content
        assert content.endswith("\n")

    def test_skips_when_disabled(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with patch("logger.settings") as mock_settings:
            mock_settings.debug = False
            log = Logger()
            log("hello")

        assert not (tmp_path / "logfile.txt").exists()
