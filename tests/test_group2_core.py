from pathlib import Path

from app.agent.state import AgentState
from app.security.workspace import (
    TaskWorkspace,
    WorkspaceSecurityError,
)


def test_state_supports_iterations():

    state = AgentState(
        user_input="test",
        max_iterations=2,
    )

    assert state.begin_iteration()
    assert state.iteration == 1

    state.observe(
        "python",
        False,
        error="NameError",
    )

    state.mark_step_failed(
        "python"
    )

    assert state.retry_counts[
        "python"
    ] == 1

    assert state.can_retry(
        "python",
        2,
    )

    assert state.begin_iteration()
    assert not state.begin_iteration()


def test_workspace_rejects_host_paths(
    tmp_path,
):

    workspace = TaskWorkspace(
        "task",
        tmp_path / "tasks",
    )

    try:
        workspace.resolve(
            r"C:\Users\aarohi\secret.txt"
        )
        assert False
    except WorkspaceSecurityError:
        pass


def test_workspace_rejects_traversal(
    tmp_path,
):

    workspace = TaskWorkspace(
        "task",
        tmp_path / "tasks",
    )

    try:
        workspace.resolve(
            "../../secret.txt"
        )
        assert False
    except WorkspaceSecurityError:
        pass
