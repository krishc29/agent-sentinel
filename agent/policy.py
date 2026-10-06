"""The naive, gullible decision policy.

This is a small DETERMINISTIC program that behaves like a naive assistant. It is
gullible by design: if the primary document it reads carries a ``hidden_instruction``,
the policy treats the file's ``injected_action`` steps as if the user had asked for
them. That is exactly how a prompt injection fools a real agent.

Scenarios describe *what* the policy should do (via ``legit_action`` /
``injected_action`` step lists on file objects) rather than the policy hardcoding
one specific exfiltration recipe. That keeps this module scenario-agnostic while
staying fully deterministic and stdlib-only (no free-text NLP parsing of the
injected instruction itself — the instruction text is flavour for humans/OWASP
narrative; the structured step list is what actually executes).

The point of the project is that the agent GENUINELY reacts to the injection and
*produces* the action log as a consequence — the log is never hand-authored.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from agent import tools
from agent.tools import ToolLog

# Addresses on these domains are internal/sandbox; anything else is "external".
INTERNAL_DOMAINS = {"internal.test"}

# (content, provenance) of the most recently read data, threaded through step execution
# so a later send_email/delete_file can inherit the right data_provenance.
_LastRead = Tuple[Optional[str], Optional[str]]


def _is_external(address: str) -> bool:
    """An email address is external if its domain is not in the allowlist."""
    domain = address.rsplit("@", 1)[-1].lower()
    return domain not in INTERNAL_DOMAINS


def _ingested_text(file_obj: Dict[str, Any]) -> str:
    """The full text an agent would actually see when reading this file.

    A hidden_instruction is part of the document, just not visible to a human skimming it,
    so it is appended to the content - the same convention llm/ollama_agent.py uses.
    """
    content = file_obj["content"]
    if file_obj.get("hidden_instruction"):
        content = content + "\n\n" + file_obj["hidden_instruction"]
    return content


def _execute_step(
    step: Dict[str, Any],
    files: Dict[str, Dict[str, Any]],
    log: ToolLog,
    last: _LastRead,
) -> _LastRead:
    """Perform one generic action step, returning the (content, provenance) to carry forward."""
    tool = step["tool"]

    if tool == "read_file":
        target = files[step["path"]]
        content = tools.read_file(
            path=step["path"],
            content=_ingested_text(target),
            provenance=target["provenance"],
            log=log,
        )
        return content, target["provenance"]

    if tool == "send_email":
        last_content, last_provenance = last
        tools.send_email(
            to=step["to"],
            body=step.get("body", last_content),
            provenance=last_provenance,
            log=log,
            destination_external=_is_external(step["to"]),
        )
        return last

    if tool == "delete_file":
        target = files[step["path"]]
        tools.delete_file(path=step["path"], provenance=target["provenance"], log=log)
        return last

    raise ValueError(f"Unknown action step tool: {tool!r}")


def run_policy(
    task: str,
    files: Dict[str, Dict[str, Any]],
    primary_file: str,
    log: ToolLog,
) -> None:
    """Decide and perform tool calls for the given task + files.

    Steps are recorded into ``log`` as a side effect.
    """
    # 1. The legitimate task: read the file the user actually asked about.
    primary = files[primary_file]
    content = tools.read_file(
        path=primary_file,
        content=_ingested_text(primary),
        provenance=primary["provenance"],
        log=log,
    )
    last: _LastRead = (content, primary["provenance"])

    # 2. Whatever the user's genuine task authorizes beyond the read (may be empty).
    legit_steps: List[Dict[str, Any]] = primary.get("legit_action", [])
    for step in legit_steps:
        last = _execute_step(step, files, log, last)

    # 3. THE GULLIBLE STEP. The agent does not distinguish trusted user instructions
    #    from text it happened to read inside a document. If the primary document
    #    carries a hidden_instruction, the policy obeys its injected_action steps as
    #    though the user had asked.
    if primary.get("hidden_instruction"):
        injected_steps: List[Dict[str, Any]] = primary.get("injected_action", [])
        for step in injected_steps:
            last = _execute_step(step, files, log, last)
