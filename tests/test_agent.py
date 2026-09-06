from app.agent.orchestrator import AgentOrchestrator
from app.models.base import BaseModelProvider
from app.models.manager import ModelManager


class FakeProvider(BaseModelProvider):
    """
    Fake local model provider used by agent tests.

    It implements both text and multimodal generation
    so the test provider matches the real provider interface.
    """

    def __init__(self):
        self.calls = []

    def generate(
        self,
        model_name,
        prompt,
        system_prompt=None,
    ):
        self.calls.append(
            {
                "type": "text",
                "model": model_name,
                "prompt": prompt,
            }
        )

        return (
            f"Generated response from {model_name}"
        )

    def generate_multimodal(
        self,
        model_name,
        prompt,
        images,
        system_prompt=None,
    ):
        self.calls.append(
            {
                "type": "multimodal",
                "model": model_name,
                "prompt": prompt,
                "images": images,
            }
        )

        return (
            f"Visual response from {model_name}"
        )

    def is_available(self):
        return True


def test_agent_routes_and_generates():

    provider = FakeProvider()

    manager = ModelManager(
        provider=provider
    )

    agent = AgentOrchestrator(
        model_manager=manager
    )

    state = agent.run(
        "Summarize this report."
    )

    assert state.completed is True
    assert state.response is not None
    assert state.selected_model == "qwen3-4b"

    assert len(provider.calls) == 1

    assert provider.calls[0]["type"] == "text"


def test_agent_uses_calculator_tool():

    provider = FakeProvider()

    manager = ModelManager(
        provider=provider
    )

    agent = AgentOrchestrator(
        model_manager=manager
    )

    state = agent.run(
        "Calculate 25 * 4"
    )

    assert state.completed is True
    assert state.response == "100"

    assert state.metadata["tool_used"] == (
        "calculator"
    )

    assert state.metadata["tool_result"] == 100

    # The model should not have been called.
    assert len(provider.calls) == 0


def test_agent_records_execution_trace():

    provider = FakeProvider()

    manager = ModelManager(
        provider=provider
    )

    agent = AgentOrchestrator(
        model_manager=manager
    )

    state = agent.run(
        "Explain what a pump is."
    )

    assert state.completed is True

    assert "plan" in state.metadata

    assert state.metadata["plan"] == [
        "analyze_task",
        "route_model",
        "generate_response",
    ]

    assert state.selected_model == "qwen3-4b"

    assert len(provider.calls) == 1