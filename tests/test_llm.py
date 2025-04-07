"""
Tests for the LLM module.
"""
import pytest
from unittest.mock import MagicMock, patch
from typing import List, Dict, Any

from kindroid.modules.llm import LLMModule


@pytest.fixture
def llm():
    """Create an LLM instance with mocked LMStudio."""
    with patch('lmstudio.LMStudio') as mock_lmstudio:
        mock_lmstudio.return_value.chat.return_value = "Test response"
        mock_lmstudio.return_value.list_models.return_value = ["test-model"]
        llm = LLMModule()
        llm.initialize()
        yield llm
        llm.shutdown()


def test_llm_initialization(llm):
    """Test LLM initialization."""
    assert llm.is_initialized
    assert llm.client is not None
    assert llm.model is not None


def test_llm_status(llm):
    """Test LLM status reporting."""
    status = llm.get_status()
    assert isinstance(status, dict)
    assert status['initialized'] is True
    assert isinstance(status['model'], str)
    assert isinstance(status['temperature'], float)
    assert isinstance(status['max_tokens'], int)


def test_chat(llm):
    """Test chat functionality."""
    response = llm.chat("Test message")
    assert isinstance(response, str)
    assert response == "Test response"


def test_list_models(llm):
    """Test model listing."""
    models = llm.list_models()
    assert isinstance(models, list)
    assert "test-model" in models


def test_set_model(llm):
    """Test model setting."""
    result = llm.set_model("test-model")
    assert result is True
    assert llm.model == "test-model"


def test_set_temperature(llm):
    """Test temperature setting."""
    result = llm.set_temperature(0.7)
    assert result is True
    assert llm.temperature == 0.7


def test_set_max_tokens(llm):
    """Test max tokens setting."""
    result = llm.set_max_tokens(100)
    assert result is True
    assert llm.max_tokens == 100


def test_uninitialized_llm():
    """Test operations on uninitialized LLM."""
    llm = LLMModule()
    assert llm.is_initialized is False
    
    with pytest.raises(RuntimeError):
        llm.chat("Test")
    
    with pytest.raises(RuntimeError):
        llm.list_models()
    
    with pytest.raises(RuntimeError):
        llm.set_model("test-model")
    
    with pytest.raises(RuntimeError):
        llm.set_temperature(0.7)
    
    with pytest.raises(RuntimeError):
        llm.set_max_tokens(100) 