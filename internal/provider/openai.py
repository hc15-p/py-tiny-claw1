import os
import openai
from internal.schema.message import (Message,ROLE_SYSTEM,ROLE_USER,ToolDefinition,ROLE_ASSISTANT,ToolCall)
class OpenAIProvider:
    def __init__(self,client:openai.OpenAI,model:str):
        self.client=client
        self.model=model
    def generate(self,msgs:list[Message],available_tools:list[ToolDefinition]|None)->Message:
        openai_msgs=[]
        for msg in msgs :
            if msg.role==ROLE_SYSTEM:
                openai_msgs.append({"role":"system","content":msg.content})
            elif msg.role==ROLE_USER:
                if msg.tool_call_id !="":
                    openai_msgs.append({"role":"tool","content":msg.content,"tool_call_id":msg.tool_call_id})
                else:
                    openai_msgs.append({"role":"user","content":msg.content})
            elif msg.role==ROLE_ASSISTANT:
                ast_param:dict={"role":"assistant"}
                if msg.content!="":
                    ast_param["content"]=msg.content
                if msg.reasoning_content!="":
                    ast_param["reasoning_content"]=msg.reasoning_content
                if len(msg.tool_calls)>0:
                    tool_calls=[]
                    for tc in msg.tool_calls:
                        tool_calls.append({"id":tc.id,"type":"function","function":{"name":tc.name,"arguments":tc.arguments,},})
                    ast_param["tool_calls"]=tool_calls
                openai_msgs.append(ast_param)
        openai_tools=[]
        for tool_def in available_tools or []:
            params_schema=tool_def.input_schema if isinstance(tool_def.input_schema,dict) else {}
            openai_tools.append({"type":"function","function":{"name":tool_def.name,"description":tool_def.description,"parameters":params_schema,},})
        params={"model":self.model,"messages":openai_msgs}
        if openai_tools:
            params["tools"]=openai_tools
        try:
            resp=self.client.chat.completions.create(**params)
        except Exception as e:
            raise RuntimeError(f"Openai/Deepseek API 请求失败:{e}")from e
        if len(resp.choices)==0:
            raise RuntimeError("API 返回了空的Choices")
        choice=resp.choices[0].message
        result_msg=Message(role=ROLE_ASSISTANT,content=choice.content or"",reasoning_content=getattr(choice,"reasoning_content",""))
        for tc in choice.tool_calls or []:
            if tc.type=="function":
                result_msg.tool_calls.append(ToolCall(id=tc.id,name=tc.function.name,arguments=tc.function.arguments,))
        return result_msg
def new_deepseek_openai_provider(model:str)->OpenAIProvider:
    api_key=os.getenv("DeepSeek_API_KEY")
    if not api_key:
        raise RuntimeError("请设置DeepSeek_API_KEY环境变量")
    base_url="https://api.deepseek.com"
    return OpenAIProvider(client=openai.OpenAI(api_key=api_key,base_url=base_url),model=model,)