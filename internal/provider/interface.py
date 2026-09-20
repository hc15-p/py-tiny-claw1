from abc import ABC,abstractclassmethod
from internal.schema.message import Message,ToolDefinition
class LLMProvider(ABC):
    """LLMProcider定义了与大模型通信的统一接口"""
    @abstractclassmethod
    def generate(self,message:list[Message],available_tools:list[ToolDefinition] | None)->Message:
        """generate 接收当前上下文历史和可用工具列表，返回模型响应"""
        pass