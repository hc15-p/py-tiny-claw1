import logging
from abc import ABC,abstractclassmethod
from internal.schema.message import ToolDefinition,ToolCall,ToolResult
log=logging.getLogger(__name__)
class BaseTool(ABC):
    @abstractclassmethod
    def name(self)->str:
        pass
    @abstractclassmethod
    def definition(self)->ToolDefinition:
        pass
    @abstractclassmethod
    def execute(self,args:str)->str:
        """args为原始JSON字符串，由工具自行解析；执行失败时抛出异常"""
class Registry(ABC):
    """工具注册中心接口"""
    @abstractclassmethod
    def register(self,tool:BaseTool):
        return
    @abstractclassmethod
    def get_available_tools(self)->list[ToolDefinition]:
        return
    @abstractclassmethod
    def execute(self,call:ToolCall)->ToolResult:
        return
class RegistryImpl(Registry):
    def __init__(self):
        self.tools:dict[str,BaseTool]={}
    def register(self,tool:BaseTool):
        name=tool.name()
        if name in self.tools:
            log.info("[Warning]工具'%s'已经被注册，将被覆盖",name)
        self.tools[name]=tool
        log.info("[Registry]成功挂载工具：%s",name)
    def get_available_tools(self)->list[ToolDefinition]:
        return [tool.definition() for tool in self.tools.values()]
    def execute(self,call:ToolCall)->ToolResult:
        tool=self.tools.get(call.name)
        if tool is None:
            err_msg=f"Error:系统中不存在名为'{call.name}'的工具。"
            return ToolResult(
                tool_call_id=call.id,
                output=err_msg,
                is_error=True,
            )
        try:
            output=tool.execute(call.arguments)
        except Exception as e:
            return ToolResult(
                tool_call_id=call.id,
                output=f"Error executing{call.name}:{e}",
                is_error=True
            )
        return ToolResult(
            tool_call_id=call.id,
            output=output,
            is_error=False
        )
def new_registry()->Registry:
    return RegistryImpl()