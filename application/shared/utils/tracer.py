import time
import os
import uuid
import contextvars
from functools import wraps
from typing import List, Dict, Any
from application.monitoring.logger import AppLogger

logger = AppLogger.get_logger("tracer")

# Create a ContextVar to store the current trace context per thread/task
trace_context = contextvars.ContextVar('trace_context', default=None)

class TraceNode:
    def __init__(self, name: str):
        self.name = name
        self.start_time = time.time()
        self.duration_ms = 0.0
        self.children = []
        self.inputs = ""
        self.outputs = ""
        self.raw_inputs = None
        self.raw_outputs = None

def _safe_str(val, max_len=150):
    try:
        s = str(val).replace('\n', '\\n').replace('\r', '')
        if len(s) > max_len:
            return s[:max_len] + "..."
        return s
    except:
        return "<unprintable>"

class RequestTracer:
    """
    Manages the lifecycle of a request trace.
    Stores the steps as a tree for the current execution context.
    """
    def __init__(self, request_id: str, user_id: str):
        self.request_id = request_id
        self.user_id = user_id
        self.start_time = time.time()
        self.root_nodes = []
        self._stack = []

    def push(self, name: str) -> TraceNode:
        node = TraceNode(name)
        if self._stack:
            self._stack[-1].children.append(node)
        else:
            self.root_nodes.append(node)
        self._stack.append(node)
        return node
        
    def pop(self, node: TraceNode):
        node.duration_ms = (time.time() - node.start_time) * 1000
        if self._stack and self._stack[-1] is node:
            self._stack.pop()
        else:
            try:
                self._stack.remove(node)
            except ValueError:
                pass

    def _format_nodes(self, nodes: List[TraceNode], depth: int = 1) -> List[str]:
        lines = []
        for node in nodes:
            indent = "    " * depth
            lines.append(f"{indent}└─ {node.name}: {node.duration_ms:.2f}ms")
            
            detail_indent = indent + "   │ "
            if node.inputs:
                lines.append(f"{detail_indent}In: {node.inputs}")
            if node.outputs:
                lines.append(f"{detail_indent}Out: {node.outputs}")
                
            lines.extend(self._format_nodes(node.children, depth + 1))
        return lines

    def _node_to_dict(self, node: TraceNode) -> dict:
        return {
            "name": node.name,
            "duration_ms": node.duration_ms,
            "raw_inputs": node.raw_inputs,
            "raw_outputs": node.raw_outputs,
            "children": [self._node_to_dict(c) for c in node.children]
        }

    def dump_trace(self):
        """Calculates total time and writes the trace tree to traces.log and traces.jsonl."""
        total_time_ms = (time.time() - self.start_time) * 1000
        
        logs_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        log_file = os.path.join(logs_dir, "traces.log")
        json_file = os.path.join(logs_dir, "traces.jsonl")
        
        # 1. Write to JSONL
        import json
        trace_data = {
            "trace_id": self.request_id,
            "user_id": self.user_id,
            "total_time_ms": total_time_ms,
            "roots": [self._node_to_dict(n) for n in self.root_nodes]
        }
        with open(json_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(trace_data, ensure_ascii=False) + "\n")
            
        # 2. Write to TEXT log
        lines = []
        lines.append(f"[TRACE ID: {self.request_id}] User: {self.user_id}")
        
        tree_lines = self._format_nodes(self.root_nodes)
        if not tree_lines:
            lines.append("  (No steps recorded)")
        else:
            lines.extend(tree_lines)
            
        lines.append("-" * 32)
        lines.append(f"Total Time: {total_time_ms:.2f}ms")
        lines.append("\n")
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write("\n".join(lines))
            
        logger.info(f"Trace completed for {self.request_id} in {total_time_ms:.2f}ms.")


def trace_step(func):
    """
    AOP Decorator to measure function execution time and append it to the current trace.
    Works for both synchronous and asynchronous functions.
    """
    import asyncio
    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = trace_context.get()
            if not tracer:
                return await func(*args, **kwargs)
                
            node = tracer.push(f"{func.__module__}.{func.__qualname__}")
            args_str = ", ".join([_safe_str(a) for a in args])
            kwargs_str = ", ".join([f"{k}={_safe_str(v)}" for k, v in kwargs.items()])
            node.inputs = f"({args_str}{', ' if args_str and kwargs_str else ''}{kwargs_str})"
            
            # Store raw for JSON
            safe_args = [repr(a) for a in args]
            safe_kwargs = {k: repr(v) for k,v in kwargs.items()}
            node.raw_inputs = {"args": safe_args, "kwargs": safe_kwargs}
            
            try:
                result = await func(*args, **kwargs)
                node.outputs = _safe_str(result)
                node.raw_outputs = repr(result)
                return result
            finally:
                tracer.pop(node)
        return async_wrapper
    else:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = trace_context.get()
            if not tracer:
                return func(*args, **kwargs)
                
            node = tracer.push(f"{func.__module__}.{func.__qualname__}")
            args_str = ", ".join([_safe_str(a) for a in args])
            kwargs_str = ", ".join([f"{k}={_safe_str(v)}" for k, v in kwargs.items()])
            node.inputs = f"({args_str}{', ' if args_str and kwargs_str else ''}{kwargs_str})"
            
            # Store raw for JSON
            safe_args = [repr(a) for a in args]
            safe_kwargs = {k: repr(v) for k,v in kwargs.items()}
            node.raw_inputs = {"args": safe_args, "kwargs": safe_kwargs}
            
            try:
                result = func(*args, **kwargs)
                node.outputs = _safe_str(result)
                node.raw_outputs = repr(result)
                return result
            finally:
                tracer.pop(node)
        return sync_wrapper

def trace_all_methods(cls):
    """
    Class decorator to apply @trace_step to all public methods of a class.
    """
    import inspect
    for name, method in inspect.getmembers(cls, inspect.isfunction):
        if not name.startswith("_"):
            setattr(cls, name, trace_step(method))
    return cls
