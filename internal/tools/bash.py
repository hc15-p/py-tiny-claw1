import json
import os
import shutil
import subprocess
from internal.schema.message import ToolDefinition
from internal.tools.registry import BaseTool
class BashTool(BaseTool):
    def __init__(self,work_dir:str):
        self.work_dir=work_dir
        self.bash_path=shutil.which("bash")
        if self.bash_path is None:
            git_path=shutil.which("git")
            if git_path is not None:
                git_root=os.path.dirname(os.path.dirname(git_path))
                for candidate in (
                    os.path.join(git_root,"bin","bash.exe"),
                    os.path.join(git_root,"usr","bin","bash.exe"),
                ):
                    if os.path.isfile(candidate):
                        self.bash_path=candidate
                        break
        if self.bash_path is None:
            raise RuntimeError("找不到bash，请安装Git for Windows或将bash.exe所在目录加入PATH")
    def name(self)->str:
        return "bash"
    def definition(self)->ToolDefinition:
        return ToolDefinition(
            name=self.name(),
            description="在当前工作区执行任意的bash命令。支持链式命令（如&&）。返回标准输出（stdout）和标准错误（stderr）。",
            input_schema={
                "type":"object",
                "properties":{
                    "command":{
                        "type":"string",
                        "description":"要执行的bash命令",
                    },
                },
                "required":["command"],
            },
        )
    def execute(self,args:str)->str:
        try:
            input_args=json.loads(args)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"参数解析失败：{e}") from e
        try:
            proc=subprocess.run(
                [self.bash_path,"-c",input_args.get("command","")],
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )
        except subprocess.TimeoutExpired as e:
            partial=(e.stdout or"")+(e.stderr or"")
            if isinstance(partial,bytes):
                partial=partial.decode("utf-8",errors="replace")
            return partial+"\n[警告：，命令执行超时（30s），已被系统强制终止。]"
        output_str=(proc.stdout or"")+(proc.stderr or"")
        if proc.returncode!=0:
            return f"执行报错:exit status {proc.returncode}\n输出：\n{output_str}"
        if output_str=="":
            return "命令执行成功，无终端输出。"
        MAX_LEN=8000
        if len(output_str)>MAX_LEN:
            return f"{output_str[:MAX_LEN]}\n\n...[终端输出过长，已截断至前{MAX_LEN}字节]..."
        return output_str