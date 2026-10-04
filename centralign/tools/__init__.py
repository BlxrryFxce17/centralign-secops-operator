"""
Tool Registry for CentrAlign Operator.
Provides unified tool discovery, schema introspection, and execution.
"""

from typing import Dict, List, Optional
from .base import BaseTool, ToolResult
from .file_ops import FileSearchTool, DocumentParserTool, WriteArtifactTool
from .browser_mock import SimulatedBrowserTool
from .api_gateway import APIGatewayTool
from .secops_systems import (
    LookupEmployeeTool, TerminateSSOSessionsTool, RevokeCloudIAMTool,
    RevokeRepoAccessTool, LockDeviceMDMTool, VerifySecurityStateTool, QuerySecurityStateTool
)

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._register_default_tools()

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    @property
    def tools(self) -> Dict[str, BaseTool]:
        return self._tools

    def has(self, name: str) -> bool:
        return name in self._tools

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, str]]:
        return [{"name": t.name, "description": t.description} for t in self._tools.values()]

    def execute(self, name: str, **kwargs) -> ToolResult:
        tool = self.get_tool(name)
        if not tool:
            return ToolResult(False, error=f"Tool '{name}' not found in registry. Available tools: {list(self._tools.keys())}")
        return tool.run(**kwargs)

    def _register_default_tools(self):
        # SecOps Identity & Access Management Tools
        self.register(LookupEmployeeTool())
        self.register(TerminateSSOSessionsTool())
        self.register(RevokeCloudIAMTool())
        self.register(RevokeRepoAccessTool())
        self.register(LockDeviceMDMTool())
        self.register(VerifySecurityStateTool())
        self.register(QuerySecurityStateTool())

        # Enterprise Tools & Artifact Generation
        self.register(FileSearchTool())
        self.register(DocumentParserTool())
        self.register(WriteArtifactTool())
        self.register(SimulatedBrowserTool())
        self.register(APIGatewayTool())
