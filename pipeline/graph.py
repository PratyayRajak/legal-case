"""LangGraph pipeline graph definition.

The graph is defined here and nodes are wired in order.
In Phase 1, all nodes are stubs. The graph structure is correct.
"""
from __future__ import annotations

from langgraph.graph import END, StateGraph

from pipeline.nodes.base import PipelineState
from pipeline.nodes.stubs import (
    AssembleBriefNode,
    ChunkIndexNode,
    ClassifyNode,
    ConfidenceScoreNode,
    ConflictCheckNode,
    ExtractFieldsNode,
    IngestNode,
    NormalizeNode,
    OCRNode,
    PIIMaskNode,
    RulesCheckNode,
)


def build_pipeline_graph() -> StateGraph:
    """Build and return the LangGraph pipeline graph."""
    nodes = [
        IngestNode(),
        OCRNode(),
        PIIMaskNode(),
        ClassifyNode(),
        ChunkIndexNode(),
        ExtractFieldsNode(),
        NormalizeNode(),
        ConflictCheckNode(),
        RulesCheckNode(),
        ConfidenceScoreNode(),
        AssembleBriefNode(),
    ]

    graph = StateGraph(PipelineState)

    for node in nodes:
        graph.add_node(node.node_name, node.run)

    # Wire nodes in sequence
    node_names = [n.node_name for n in nodes]
    for i in range(len(node_names) - 1):
        graph.add_edge(node_names[i], node_names[i + 1])

    graph.add_edge(node_names[-1], END)
    graph.set_entry_point(node_names[0])

    return graph
