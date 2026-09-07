from typing import Any


class AgentValidator:
    """
    Deterministic final validation gate.

    No network calls and no second router/model are used here.
    """

    def validate_response(
        self,
        state,
    ) -> tuple[bool, str]:

        if state.response is None:
            return (
                False,
                "No response was generated.",
            )

        if not str(state.response).strip():
            return (
                False,
                "Generated response is empty.",
            )

        return (
            True,
            "Response is non-empty.",
        )

    def validate_evidence(
        self,
        state,
    ) -> tuple[bool, str]:

        requirements = (
            state.task_requirements
        )

        if requirements is None:
            return (
                True,
                "No explicit evidence requirement.",
            )

        required = []

        if getattr(
            requirements,
            "needs_document",
            False,
        ):
            required.append("document")

        if getattr(
            requirements,
            "needs_vision",
            False,
        ):
            required.append("vision")

        if getattr(
            requirements,
            "needs_knowledge",
            False,
        ):
            required.append("knowledge")

        missing = [
            source
            for source in required
            if not state.evidence.get(source)
        ]

        if missing:
            return (
                False,
                "Missing evidence: "
                + ", ".join(missing),
            )

        return (
            True,
            "Evidence requirements satisfied.",
        )

    def validate_artifact(
        self,
        state,
    ) -> tuple[bool, str]:

        result = state.tool_results.get(
            "artifact"
        )

        if result is None:
            return (
                True,
                "No artifact requested.",
            )

        if hasattr(result, "get"):

            if result.get("success") is False:
                return (
                    False,
                    result.get(
                        "error",
                        "Artifact generation failed.",
                    ),
                )

            validation = result.get(
                "validation"
            )

            if isinstance(
                validation,
                dict,
            ):

                if validation.get(
                    "valid"
                ) is False:
                    return (
                        False,
                        "Artifact validation failed.",
                    )

        return (
            True,
            "Artifact validation passed.",
        )

    def validate_code(
        self,
        state,
    ) -> tuple[bool, str]:

        result = state.tool_results.get(
            "python"
        )

        if result is None:
            return (
                True,
                "No Python execution requested.",
            )

        if hasattr(result, "get"):

            if result.get("success") is False:

                error = (
                    result.get("error")
                    or result.get("stderr")
                    or "Python execution failed."
                )

                return (
                    False,
                    str(error),
                )

        return (
            True,
            "Code execution passed.",
        )

    def validate(
        self,
        state,
    ) -> dict[str, Any]:

        response_ok, response_message = (
            self.validate_response(state)
        )

        evidence_ok, evidence_message = (
            self.validate_evidence(state)
        )

        artifact_ok, artifact_message = (
            self.validate_artifact(state)
        )

        code_ok, code_message = (
            self.validate_code(state)
        )

        valid = all(
            [
                response_ok,
                evidence_ok,
                artifact_ok,
                code_ok,
            ]
        )

        return {
            "valid": valid,
            "response": {
                "success": response_ok,
                "message": response_message,
            },
            "evidence": {
                "success": evidence_ok,
                "message": evidence_message,
            },
            "artifact": {
                "success": artifact_ok,
                "message": artifact_message,
            },
            "code": {
                "success": code_ok,
                "message": code_message,
            },
        }
