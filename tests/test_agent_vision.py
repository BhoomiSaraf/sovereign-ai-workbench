from pathlib import Path

from app.agent.orchestrator import AgentOrchestrator
from app.models.manager import ModelManager


class FakeProvider:

    def generate(
        self,
        model_name,
        prompt,
        system_prompt=None,
    ):
        return "Final response based on visual analysis."

    def generate_multimodal(
        self,
        model_name,
        prompt,
        images,
        system_prompt=None,
    ):
        return (
            "Detected P-101, T-101, V-101, "
            "V-102 and PSV-101."
        )

    def is_available(self):
        return True


def test_agent_executes_vision_workflow(
    tmp_path: Path,
):

    image_path = tmp_path / "pid.png"

    image_path.write_bytes(
        b"fake-image-data"
    )

    manager = ModelManager(
        provider=FakeProvider()
    )

    agent = AgentOrchestrator(
        model_manager=manager
    )

    state = agent.run(
        user_input="Analyze this P&ID.",
        has_image=True,
        image_path=str(image_path),
    )

    assert state.completed is True

    assert state.vision_context is not None

    assert "P-101" in state.vision_context

    assert (
        state.metadata["vision_model"]
        == "qwen2.5-vl-3b"
    )

    assert "vision" in state.tool_results

    event_types = [
        event["type"]
        for event in state.events
    ]

    assert "vision_analysis" in event_types