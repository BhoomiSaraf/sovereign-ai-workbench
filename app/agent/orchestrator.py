from app.agent.executor import AgentExecutor
from app.agent.planner import AgentPlanner
from app.agent.state import AgentState
from app.models.manager import ModelManager
from app.router.model_router import ModelRouter
from app.tools.calculator import SafeCalculator
from app.tools.documents import DocumentTool
from app.tools.pdf import PDFTool
from app.tools.python import PythonTool
from app.tools.registry import ToolRegistry, ToolCapability
from app.tools.vision import VisionTool
from app.tools.knowledge import KnowledgeTool
from app.tools.artifact import ArtifactTool
from app.security.workspace import TaskWorkspace
from uuid import uuid4
from app.tools.workspace import WorkspaceTool

class AgentOrchestrator:
    def __init__(
        self,
        router=None,
        model_manager=None,
        tool_registry=None,
    ):
        self.router = router or ModelRouter()
        self.model_manager = model_manager or ModelManager()

        self.tool_registry = (
            tool_registry or self._create_default_registry()
        )

        self.planner = AgentPlanner(router=self.router)

        self.executor = AgentExecutor(
            router=self.router,
            model_manager=self.model_manager,
            tool_registry=self.tool_registry,
        )

    
    def run(
    self,
    user_input: str,
    has_image: bool = False,
    image_path: str | None = None,
    file_path: str | None = None,
    ):
        """
        Run the sovereign local AI workflow.

        file_path:
            Optional local document path for PDF, DOCX, or TXT
            processing.
        """

        if not user_input or not user_input.strip():
            raise ValueError(
                "user_input cannot be empty."
            )

        if has_image and not image_path:
            raise ValueError(
                "image_path is required when has_image=True."
            )

        task_id = uuid4().hex

        workspace = TaskWorkspace(
            task_id=task_id
        )

        state = AgentState(
            user_input=user_input,
            has_image=has_image,
            image_path=image_path,
        )

        state.metadata["task_id"] = task_id
        state.metadata["workspace_root"] = str(
            workspace.root
        )

        # Store local document path for the document tool.
        if file_path:
            state.metadata["file_path"] = file_path

        plan = self.planner.create_plan(state)
        state.task_requirements = plan.requirements
        state.metadata["plan"] = plan.steps
        state.metadata["task_requirements"] = plan.requirements

        if hasattr(plan, "steps"):
            state.metadata["plan"] = plan.steps
        else:
            state.metadata["plan"] = plan

        return self.executor.execute(state)
    
    def _create_default_registry(self):
        registry = ToolRegistry(
            allowed_capabilities={
                ToolCapability.READ,
                ToolCapability.WRITE,
                ToolCapability.EXECUTE,
            }
        )

        # ---------------------------------------------------------
        # Calculator
        # ---------------------------------------------------------

        calculator = SafeCalculator()

        registry.register(
            name="calculator",
            description="Performs safe deterministic arithmetic calculations.",
            function=calculator.calculate,
        )

        # ---------------------------------------------------------
        # Vision
        # ---------------------------------------------------------

        vision = VisionTool(
            model_manager=self.model_manager
        )

        registry.register(
            name="vision",
            description=(
                "Analyzes local images, engineering drawings, "
                "P&IDs, and inspection images using the local "
                "multimodal model."
            ),
            function=vision.execute,
        )

        # ---------------------------------------------------------
        # Documents
        # ---------------------------------------------------------

        documents = DocumentTool()

        registry.register(
            name="documents",
            description=(
                "Extracts text and structured information "
                "from local PDF, DOCX, and text documents."
            ),
            function=documents.execute,
        )

        # ---------------------------------------------------------
        # PDF
        # ---------------------------------------------------------

        pdf = PDFTool()

        registry.register(
            name="pdf",
            description=(
                "Performs local PDF text extraction and "
                "PDF inspection."
            ),
            function=pdf.extract_text,
        )

        # ---------------------------------------------------------
        # Python sandbox
        # ---------------------------------------------------------

        python_tool = PythonTool()

        registry.register(
            name="python",
            description=(
                "Executes Python code inside an isolated "
                "local Docker sandbox with networking disabled."
            ),
            function=python_tool.execute,
        )

        
        knowledge = KnowledgeTool()

        registry.register(
            name="knowledge_search",
            description=(
                    "Searches the private organizational knowledge base "
                    "using the local vector database and local embeddings."
            ),
            function=knowledge.execute,
        )

        artifact = ArtifactTool()

        registry.register(
            name="artifact",
            description=(
                "Generates and validates local DOCX approval notes "
                "and other workflow artifacts."
            ),
            function=artifact.execute,
        )

        workspace = WorkspaceTool()

        registry.register(
            name="read_file",
            description="Reads a file strictly inside the current task workspace.",
            function=workspace.read_file,
            capabilities={ToolCapability.READ},
        )

        registry.register(
            name="write_file",
            description="Writes a file strictly inside the current task workspace.",
            function=workspace.write_file,
            capabilities={ToolCapability.WRITE},
        )

        registry.register(
            name="list_files",
            description="Lists files strictly inside the current task workspace.",
            function=workspace.list_files,
            capabilities={ToolCapability.READ},
        )

        registry.register(
            name="create_directory",
            description="Creates a directory strictly inside the current task workspace.",
            function=workspace.create_directory,
            capabilities={ToolCapability.WRITE},
        )
        return registry

