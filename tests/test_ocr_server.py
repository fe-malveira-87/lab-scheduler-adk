import os
from unittest.mock import MagicMock, mock_open, patch

import pytest

from mcp_servers.ocr.ocr_engine import OCREngine, _MOCK_EXAMS


def test_returns_mock_when_no_api_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    engine = OCREngine()
    result = engine.extract("any/path.jpg")
    assert result == _MOCK_EXAMS


def test_mock_result_is_list_of_strings(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    engine = OCREngine()
    result = engine.extract("any/path.png")
    assert isinstance(result, list)
    assert all(isinstance(name, str) for name in result)


def test_mock_result_is_not_empty(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    engine = OCREngine()
    result = engine.extract("any/path.jpg")
    assert len(result) > 0


def test_returns_list_from_gemini_response(monkeypatch, tmp_path):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    fake_image = tmp_path / "pedido.jpg"
    fake_image.write_bytes(b"\xff\xd8\xff")  # minimal JPEG magic bytes

    mock_response = MagicMock()
    mock_response.text = "Hemograma Completo\nUrina I\nCreatinina"

    mock_types = MagicMock()
    mock_genai = MagicMock()
    mock_genai.Client.return_value.models.generate_content.return_value = mock_response

    with patch.dict("sys.modules", {"google.genai": mock_genai, "google.genai.types": mock_types}):
        engine = OCREngine()
        result = engine.extract(str(fake_image))

    assert result == ["Hemograma Completo", "Urina I", "Creatinina"]


def test_gemini_result_is_list_of_strings(monkeypatch, tmp_path):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    fake_image = tmp_path / "pedido.png"
    fake_image.write_bytes(b"\x89PNG")

    mock_response = MagicMock()
    mock_response.text = "TSH\nT4 Livre"

    mock_types = MagicMock()
    mock_genai = MagicMock()
    mock_genai.Client.return_value.models.generate_content.return_value = mock_response

    with patch.dict("sys.modules", {"google.genai": mock_genai, "google.genai.types": mock_types}):
        engine = OCREngine()
        result = engine.extract(str(fake_image))

    assert isinstance(result, list)
    assert all(isinstance(name, str) for name in result)
    assert len(result) > 0
