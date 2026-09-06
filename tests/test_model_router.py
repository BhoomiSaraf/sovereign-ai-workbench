import pytest

from app.router.model_router import ModelRouter


@pytest.fixture
def router():
    return ModelRouter()


# ======================================================================
# CODING
# ======================================================================

def test_coding_task_routes_to_coder(router):
    decision = router.route(
        "Debug this Python function"
    )

    assert decision.model.name == "qwen2.5-coder-7b"

    assert "coding" in decision.matched_capabilities
    assert "debugging" in decision.matched_capabilities


# ======================================================================
# GENERAL REASONING
# ======================================================================

def test_general_reasoning_routes_to_qwen3(router):
    decision = router.route(
        "Explain how a pressure vessel works"
    )

    assert decision.model.name == "qwen3-4b"

    assert (
        decision.task_requirements.primary_capability
        == "reasoning"
    )


# ======================================================================
# SUMMARIZATION
# ======================================================================

def test_summarization_routes_to_qwen3(router):
    decision = router.route(
        "Summarize this inspection report"
    )

    assert decision.model.name == "qwen3-4b"

    assert (
        "summarization"
        in decision.matched_capabilities
    )


# ======================================================================
# VISION
# ======================================================================

def test_vision_task_routes_to_vl(router):
    decision = router.route(
        "Analyze this P&ID and identify the major components",
        has_image=True,
    )

    assert decision.model.name == "qwen2.5-vl-3b"

    assert "vision" in decision.matched_capabilities
    assert "image_analysis" in decision.matched_capabilities

    assert (
        "image"
        in decision.task_requirements.modalities
    )


def test_image_keyword_triggers_vision(router):
    decision = router.route(
        "Analyze this diagram"
    )

    assert decision.model.name == "qwen2.5-vl-3b"


# ======================================================================
# RAG
# ======================================================================

def test_rag_is_flagged_but_does_not_select_a_rag_model(router):
    decision = router.route(
        "According to our pressure vessel SOP, "
        "what is the required inspection procedure?"
    )

    # RAG is a workflow requirement.
    assert (
        decision.task_requirements.rag_required
        is True
    )

    # Qwen3 is still the reasoning model.
    # RAG will later be called as a tool.
    assert decision.model.name == "qwen3-4b"


# ======================================================================
# SIMPLE TASK
# ======================================================================

def test_plain_question_uses_general_model(router):
    decision = router.route(
        "What is 15 times 17?"
    )

    assert decision.model.name == "qwen3-4b"

    assert (
        decision.task_requirements.primary_capability
        == "general"
    )

    assert (
        decision.task_requirements.rag_required
        is False
    )


# ======================================================================
# ROUTING EXPLANATION
# ======================================================================

def test_routing_decision_contains_explanation(router):
    decision = router.route(
        "Review this Python code for bugs"
    )

    assert decision.model is not None

    assert decision.score > 0

    assert decision.reason

    assert any(
        "Matched capabilities" in reason
        for reason in decision.reason
    )


# ======================================================================
# TEXT-ONLY MODEL FILTERING
# ======================================================================

def test_text_only_task_does_not_select_vision_model(router):
    decision = router.route(
        "Explain the maintenance procedure"
    )

    assert (
        decision.model.name
        != "qwen2.5-vl-3b"
    )
    