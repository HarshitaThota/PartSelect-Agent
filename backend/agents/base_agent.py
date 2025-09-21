from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import json

class BaseAgent(ABC):
    """Base class for all agents in the system"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.tools = {}

    @abstractmethod
    async def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a query and return results"""
        pass

    def register_tool(self, name: str, func, description: str):
        """Register a tool that this agent can use"""
        self.tools[name] = {
            "function": func,
            "description": description
        }

    async def call_tool(self, tool_name: str, **kwargs) -> Any:
        """Call a registered tool"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not available for agent {self.name}")

        try:
            tool = self.tools[tool_name]
            return await tool["function"](**kwargs)
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}

    def get_available_tools(self) -> List[str]:
        """Get list of available tools"""
        return list(self.tools.keys())

    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get descriptions of all available tools"""
        return {name: tool["description"] for name, tool in self.tools.items()}

class AgentResult:
    """Standardized result format for agent operations"""

    def __init__(self, success: bool, data: Any = None, message: str = "",
                 next_agent: str = None, tools_used: List[str] = None):
        self.success = success
        self.data = data
        self.message = message
        self.next_agent = next_agent
        self.tools_used = tools_used or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "message": self.message,
            "next_agent": self.next_agent,
            "tools_used": self.tools_used
        }