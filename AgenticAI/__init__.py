"""JARVIS Agentic AI layer for Sensex_Option_Intraday.

This package is advisory/diagnostic only. It must never place broker orders
or override the deterministic trade decision.
"""
from .agent_orchestrator import dispatch_agent_review

__all__ = ["dispatch_agent_review"]
