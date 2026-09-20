from abc import ABC,abstractclassmethod
from internal.schema.message import ToolDefinition,ToolCall,ToolResult
class Registry(ABC):
    """工具注册中心接口"""
    @abstractclassmethod
    def get_available_tools(self)->list[ToolDefinition]:
        return
    @abstractclassmethod
    def execute(self,call:ToolCall)->ToolResult:
        return