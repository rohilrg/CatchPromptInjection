# test_prompt_injection_detector.py

from unittest.mock import Mock
import pytest
from src.detector import PromptInjectionDetector

@pytest.fixture
def detector():
    config_path = "src/config/config.json"  # Replace with actual path
    return PromptInjectionDetector(config_path)

def test_first_sanity_check_invoker(detector):
    # Mocking request
    detector.request = {"query": "test query"}

    # Mocking response from _model_default_factory
    detector.first_sanity_check_pipeline = Mock()
    detector.first_sanity_check_pipeline.return_value = [
        {"label": "INJECTION", "score": 0.8}
    ]

    result = detector.first_sanity_check_invoker()

    assert result["return"] is True
    assert result["Input query is"] == "PROMPT INJECTION"
    assert result["Confidence level:"] == 0.8


if __name__ == "__main__":
    pytest.main()
