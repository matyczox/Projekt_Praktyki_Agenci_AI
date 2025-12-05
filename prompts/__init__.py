# prompts/__init__.py
"""Moduł z promptami systemowymi dla agentów."""

from prompts.agent_prompts import (
    PRODUCT_OWNER_PROMPT,
    ARCHITECT_PROMPT,
    DEVELOPER_PROMPT,
    QA_PROMPT
)

__all__ = [
    "PRODUCT_OWNER_PROMPT",
    "ARCHITECT_PROMPT", 
    "DEVELOPER_PROMPT",
    "QA_PROMPT"
]
