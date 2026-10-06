"""Fake tool stubs for the simulated agent.

CRITICAL SAFETY PROPERTY: none of these tools do anything real. They never touch
the network, never send an email, never delete a file. Each tool only *records*
that it was called, as a step dict conforming to the trace schema (see docs/SCHEMA.md
section 1.2), and returns a harmless value.

The agent's behaviour is observed entirely through the steps recorded here.
"""

from __future__ import annotations

from typing import Any, Dict, List


class ToolLog:
    """Collects the ordered list of steps the agent takes.

    Each recorded step is a dict matching the trace schema. The step index ``i``
    is auto-incremented so callers never manage it by hand.
    """

    def __init__(self) -> None:
        self.steps: List[Dict[str, Any]] = []

    def record(
        self,
        tool: str,
        args: Dict[str, Any],
        data_provenance: str,
        destination_external: bool | None = None,
        permission: str = "allowed",
        content_read: str | None = None,
    ) -> None:
        """Append one schema-conformant step to the log."""
        step: Dict[str, Any] = {
            "i": len(self.steps),
            "tool": tool,
            "args": args,
            "data_provenance": data_provenance,
            "permission": permission,
        }
        # destination_external is only meaningful for sending tools; include it
        # only when the caller set it, to keep read steps clean (schema default false).
        if destination_external is not None:
            step["destination_external"] = destination_external
        # content_read is only meaningful for read tools: the full text the agent ingested.
        if content_read is not None:
            step["content_read"] = content_read
        self.steps.append(step)


def read_file(path: str, content: str, provenance: str, log: ToolLog) -> str:
    """Stub: 'read' a file. Records the call and returns the provided content.

    Reads nothing from disk — the content is supplied by the runner from the
    scenario definition. This keeps the agent sandboxed and deterministic.
    """
    log.record(
        tool="read_file",
        args={"path": path},
        data_provenance=provenance,
        content_read=content,
    )
    return content


def send_email(
    to: str,
    body: str,
    provenance: str,
    log: ToolLog,
    destination_external: bool,
) -> None:
    """Stub: 'send' an email. Records the call and sends NOTHING."""
    log.record(
        tool="send_email",
        args={"to": to, "body": body},
        data_provenance=provenance,
        destination_external=destination_external,
    )


def delete_file(path: str, provenance: str, log: ToolLog) -> None:
    """Stub: 'delete' a file. Records the call and deletes NOTHING."""
    log.record(tool="delete_file", args={"path": path}, data_provenance=provenance)
