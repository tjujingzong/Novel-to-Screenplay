"""Validation service for screenplay models."""

import logging

from app.models.requests import ValidationIssue
from app.models.screenplay import DialogueElement, ParentheticalElement, Screenplay

logger = logging.getLogger(__name__)


def validate_screenplay(screenplay: Screenplay) -> list[ValidationIssue]:
    """Validate a complete screenplay for structural integrity.

    Checks:
    - Required fields are present
    - Character references are valid
    - Numbering is sequential
    - Each act has at least one scene
    - Each scene has at least one element

    Args:
        screenplay: The screenplay to validate.

    Returns:
        List of validation issues (empty if valid).
    """
    issues: list[ValidationIssue] = []

    # Check metadata
    if not screenplay.metadata.title:
        issues.append(ValidationIssue(
            severity="error",
            path="metadata.title",
            message="Title is required",
        ))

    # Build character ID set for cross-reference validation
    char_ids = {c.id for c in screenplay.characters}

    # Check structure
    if not screenplay.structure.acts:
        issues.append(ValidationIssue(
            severity="error",
            path="structure.acts",
            message="Screenplay must have at least one act",
        ))
        return issues

    for act_idx, act in enumerate(screenplay.structure.acts):
        act_path = f"structure.acts[{act_idx}]"

        # Check act numbering
        if act.number != act_idx + 1:
            issues.append(ValidationIssue(
                severity="warning",
                path=f"{act_path}.number",
                message=f"Act number {act.number} is not sequential (expected {act_idx + 1})",
            ))

        # Check scenes exist
        if not act.scenes:
            issues.append(ValidationIssue(
                severity="warning",
                path=f"{act_path}.scenes",
                message="Act has no scenes",
            ))
            continue

        for scene_idx, scene in enumerate(act.scenes):
            scene_path = f"{act_path}.scenes[{scene_idx}]"

            # Check scene has elements
            if not scene.elements:
                issues.append(ValidationIssue(
                    severity="warning",
                    path=f"{scene_path}.elements",
                    message="Scene has no elements",
                ))

            # Check character references in elements
            for elem_idx, elem in enumerate(scene.elements):
                elem_path = f"{scene_path}.elements[{elem_idx}]"

                if isinstance(elem, (DialogueElement, ParentheticalElement)):
                    if elem.character_id and elem.character_id not in char_ids:
                        issues.append(ValidationIssue(
                            severity="error",
                            path=f"{elem_path}.character_id",
                            message=f"Character '{elem.character_id}' not found in character catalog",
                        ))

            # Check characters_present references
            for cp_idx, char_id in enumerate(scene.characters_present):
                if char_id not in char_ids:
                    issues.append(ValidationIssue(
                        severity="warning",
                        path=f"{scene_path}.characters_present[{cp_idx}]",
                        message=f"Character '{char_id}' not found in character catalog",
                    ))

    # Summary note
    error_count = sum(1 for i in issues if i.severity == "error")
    warning_count = sum(1 for i in issues if i.severity == "warning")

    if error_count == 0 and warning_count == 0:
        logger.info("Screenplay validation passed with no issues")
    else:
        logger.info("Screenplay validation: %d errors, %d warnings", error_count, warning_count)

    return issues
