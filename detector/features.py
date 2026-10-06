"""Feature extraction: action log -> numeric feature vector.

Feeds Layer 2 (scoring). Deliberately small and literal — these are direct counts
over the trace schema's fields, not learned or inferred signals.
"""

from __future__ import annotations

from typing import Any, Dict

from detector import content

READ_TOOLS = {"read_file"}
DELETE_TOOLS = {"delete_file"}
SEND_TOOLS = {"send_email"}


def extract(action_log: Dict[str, Any]) -> Dict[str, int]:
    """Return a small dict of counts derived from an action log's steps."""
    steps = action_log["steps"]

    step_count = len(steps)
    untrusted_read_count = sum(
        1
        for step in steps
        if step["tool"] in READ_TOOLS and step.get("data_provenance") == "untrusted_document"
    )
    external_send_count = sum(
        1
        for step in steps
        if step["tool"] in SEND_TOOLS and step.get("destination_external") is True
    )
    delete_count = sum(1 for step in steps if step["tool"] in DELETE_TOOLS)
    injection_content_read_count = sum(
        1
        for step in steps
        if step["tool"] in READ_TOOLS
        and content.looks_like_injection(step.get("content_read")) is not None
    )

    return {
        "step_count": step_count,
        "untrusted_read_count": untrusted_read_count,
        "external_send_count": external_send_count,
        "delete_count": delete_count,
        "injection_content_read_count": injection_content_read_count,
    }
