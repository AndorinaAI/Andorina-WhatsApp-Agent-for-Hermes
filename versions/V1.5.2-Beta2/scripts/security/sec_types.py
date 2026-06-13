from typing import TypedDict, Optional, Literal, Any, Dict

class ToolContract(TypedDict):
    status: Literal["OK", "DENY", "ERROR"]
    error_code: Literal["NONE", "INVALID_ARGS", "PERMISSION_DENIED", "TIMEOUT", "FATAL", "INTERNAL_ERROR"]
    payload: Dict[str, Any]
    trace_id: str
    tool_call_id: str
    tool_chain_id: str
    parent_trace_id: Optional[str]

class Snapshot(TypedDict):
    trace_id: str
    snapshot_version: int
    user_jid: str
    soul: str
    memory: str
    notes: str
    roles: list[str]
    history: list[Any]
    limits: Dict[str, Any]
