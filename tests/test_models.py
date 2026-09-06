from unittest.mock import Mock

from app.models.manager import ModelManager
from app.router.model_registry import get_model_by_name


def test_model_manager_passes_ollama_model_name():
    provider = Mock()

    provider.generate.return_value = "test response"

    manager = ModelManager(provider=provider)

    model = get_model_by_name("qwen3-4b")

    result = manager.generate(
        model=model,
        prompt="Hello",
    )

    assert result == "test response"

    provider.generate.assert_called_once_with(
        model_name="qwen3:4b",
        prompt="Hello",
        system_prompt=None,
    )


def test_model_manager_provider_availability():
    provider = Mock()

    provider.is_available.return_value = True

    manager = ModelManager(provider=provider)

    assert manager.is_available() is True