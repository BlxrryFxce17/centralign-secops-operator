"""
Base tool abstraction for CentrAlign AI Operator runtime.
All connectors inherit from BaseTool to ensure schema validation,
telemetry, and uniform observation returns.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import time

class ToolResult:
    def __init__(self, success: bool, data: Any = None, error: Optional[str] = None, observation: str = ""):
        self.success = success
        self.data = data
        self.error = error
        self.observation = observation or (str(data) if success else str(error))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "observation": self.observation
        }

class BaseTool(ABC):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Executes tool action and returns ToolResult."""
        pass

    def run(self, **kwargs) -> ToolResult:
        start_time = time.time()
        try:
            res = self.execute(**kwargs)
            duration = (time.time() - start_time) * 1000
            return res
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                observation=f"Tool '{self.name}' encountered execution exception: {str(e)}"
            )

    def get_spec(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description
        }
