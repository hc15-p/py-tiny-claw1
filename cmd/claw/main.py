import logging
import os
import sys
from internal.engine.loop import AgentEngine
from internal.provider.openai import new_deepseek_openai_provider
from internal.tools.bash import BashTool
from internal.tools.edit_file import EditFileTool
from internal.tools.read_file import ReadFileTool
from internal.tools.registry import new_registry
from internal.tools.write_file import WriteFileTool
logging.basicConfig(level=logging.INFO,format="%(asctime)s %(message)s",datefmt="%Y/%m/%d %H:%M:%S")
def main():
    if not os.getenv("DeepSeek_API_KEY"):
        sys.exit("请先导出DeepSeek_API_KEY环境变量")
    work_dir=os.getcwd()
    llm_provider=new_deepseek_openai_provider("deepseek-v4-pro")
    registry=new_registry()
    registry.register(ReadFileTool(work_dir))
    registry.register(WriteFileTool(work_dir))
    registry.register(BashTool(work_dir))
    registry.register(EditFileTool(work_dir))
    eng=AgentEngine(llm_provider,registry,work_dir,False)
    prompt="""请按顺序完成以下操作，每一步都使用对应的工具：
    1.用write_file创建calc.py，内容是一个函数add(a,b)返回a+b,并在文件末尾print(add(2,3))
    2.用bash执行python calc.py
    3.用edit_file把return a+b改成return a*b
    4.用read_file读取calc.py确认修改成功
    5.再用bash执行一次python calc.py，告诉我两次输出分别是多少
    """
    try:
        eng.run(prompt)
    except Exception as e:
        sys.exit(f"引擎崩溃:{e}")
if __name__=="__main__":
    main()