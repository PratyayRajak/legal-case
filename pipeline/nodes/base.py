"""Base class for LangGraph pipeline nodes.

Each node receives a PipelineState dict and returns an updated dict.
Nodes must be pure (no side effects on the state object) and typed.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

# Type alias for the LangGraph state dict
PipelineState = dict[str, Any]


class PipelineNode(ABC):
    """Abstract base for all pipeline nodes."""

    node_name: str = "unnamed"

    @abstractmethod
    async def run(self, state: PipelineState) -> PipelineState:
        """Execute the node and return updated state.

        Args:
            state: Current pipeline state dict.

        Returns:
            Updated pipeline state dict (may be the same object with new keys).
        """
        ...

    def __repr__(self) -> str:
        return f"<PipelineNode: {self.node_name}>"
