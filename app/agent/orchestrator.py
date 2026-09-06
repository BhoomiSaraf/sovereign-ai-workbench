from app.agent.executor import AgentExecutor
from app.agent.planner import AgentPlanner
from app.agent.state import AgentState
from app.models.manager import ModelManager
from app.router.model_router import ModelRouter
from app.tools.calculator import SafeCalculator
from app.tools.registry import ToolRegistry
from app.tools.vision import VisionTool


class AgentOrchestrator:
    """
    High-level entry point for the sovereign AI agent.

    Responsible for:
        - constructing the agent pipeline
        - registering approved local tools
        - creating agent state
        - creating the execution plan
        - executing the agent workflow
    """

    def __init__(
        self,
        router=None,
        model_manager=None,
        tool_registry=None,
    ):
        self.router = router or ModelRouter()

        self.model_manager = (
            model_manager or ModelManager()
        )

        self.tool_registry = (
            tool_registry
            or self._create_default_registry()
        )

        # AgentPlanner requires the router.
        self.planner = AgentPlanner(
            router=self.router
        )

        self.executor = AgentExecutor(
            router=self.router,
            model_manager=self.model_manager,
            tool_registry=self.tool_registry,
        )

    # ==========================================================
    # PUBLIC API
    # ==========================================================

    def run(
        self,
        user_input: str,
        has_image: bool = False,
        image_path: str = None,
    ) -> AgentState:

        if not user_input or not user_input.strip():
            raise ValueError(
                "User input cannot be empty."
            )

        state = AgentState(
            user_input=user_input,
            has_image=has_image,
            image_path=image_path,
        )

        plan = self.planner.create_plan(
            state
        )

        # Preserve the simple list representation used
        # by the agent state, UI, and existing tests.
        if hasattr(plan, "steps"):
           state.metadata["plan"] = plan.steps
        else:
           state.metadata["plan"] = plan

        return self.executor.execute(
           state
        )
    # ==========================================================
    # DEFAULT TOOL REGISTRY
    # ==========================================================

    def _create_default_registry(
        self,
    ) -> ToolRegistry:

        registry = ToolRegistry()

        # ------------------------------------------------------
        # Calculator
        # ------------------------------------------------------

        calculator = SafeCalculator()

        registry.register(
            name="calculator",
            description=(
                "Performs safe deterministic arithmetic "
                "calculations."
            ),
            function=calculator.calculate,
        )

        # ------------------------------------------------------
        # Vision
        # ------------------------------------------------------

        vision = VisionTool(
            model_manager=self.model_manager
        )

        registry.register(
            name="vision",
            description=(
                "Analyzes local images, engineering "
                "drawings, P&IDs, and inspection images "
                "using the local multimodal model."
            ),
            function=vision.execute,
        )

        return registry