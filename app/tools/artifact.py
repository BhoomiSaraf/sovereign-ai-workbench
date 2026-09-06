from typing import Any, Dict, List

from app.artifacts.docx import DOCXArtifactGenerator
from app.artifacts.validator import ArtifactValidator


class ArtifactTool:
    """
    Agent-facing artifact generation tool.

    Generates local artifacts and validates them before
    returning the result to the agent.
    """

    name = "artifact"

    def __init__(
        self,
        docx_generator: DOCXArtifactGenerator | None = None,
        validator: ArtifactValidator | None = None,
    ):
        self.docx_generator = (
            docx_generator
            or DOCXArtifactGenerator()
        )

        self.validator = (
            validator
            or ArtifactValidator()
        )

    def execute(
        self,
        artifact_type: str,
        title: str,
        summary: str,
        findings: List[str] | None = None,
        recommendations: List[str] | None = None,
        knowledge_context: List[Dict[str, Any]] | None = None,
        uncertainties: List[str] | None = None,
        source_document: str | None = None,
        filename: str = "inspection_approval_note.docx",
    ) -> Dict[str, Any]:

        artifact_type = artifact_type.lower().strip()

        if artifact_type != "docx":
            raise ValueError(
                "MVP artifact tool currently supports DOCX only."
            )

        result = self.docx_generator.generate_approval_note(
            title=title,
            summary=summary,
            findings=findings,
            recommendations=recommendations,
            knowledge_context=knowledge_context,
            uncertainties=uncertainties,
            source_document=source_document,
            filename=filename,
        )

        validation = self.validator.validate(
            result["path"]
        )

        result["validation"] = validation

        if not validation.get("valid", False):
            raise RuntimeError(
                "Generated artifact failed validation."
            )

        return result