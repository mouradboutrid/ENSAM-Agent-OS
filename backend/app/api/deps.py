from __future__ import annotations
from typing import Optional

_app_state = {}


def set_app_state(key: str, value):
    _app_state[key] = value


def get_app_state(key: str, default=None):
    return _app_state.get(key, default)


def get_kernel():
    return _app_state["kernel"]


def get_router():
    return _app_state["router"]


def get_agents():
    return _app_state["agents"]


def get_memory():
    return _app_state["memory"]


def get_rag_pipeline():
    return _app_state["rag"]


def get_mcp_registry():
    return _app_state["mcp_registry"]


def get_mcp_client():
    return _app_state["mcp_client"]


def get_event_bus():
    return _app_state["event_bus"]


def get_cost_tracker():
    return _app_state["cost_tracker"]


def get_audit_logger():
    return _app_state["audit_logger"]


def get_metrics():
    return _app_state["metrics"]


def get_debate_engine():
    return _app_state["debate_engine"]
