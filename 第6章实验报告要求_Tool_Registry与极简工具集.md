# AI 智能体开发基础实验报告要求

> **课程名称：** AI 智能体开发基础  
> **实验名称：** Tool Registry 分发机制与极简工具集  
> **建议时长：** 3 课时

---

## 一、实验目的

1. 理解 Agent Harness 中 **Tool Registry** 的作用，掌握它的三大职责：动态挂载（Register）、描述暴露（Expose Schema）、路由分发与执行（Dispatch & Execute）。
2. 掌握 `BaseTool` 接口契约，能够按照统一接口实现具体工具，并为工具编写 `input_schema`。
3. 理解 **Context Bloat（上下文膨胀）** 的危害，掌握由 `read`、`write`、`edit`、`bash` 构成的"图灵完备四大原语"。
4. 掌握 `bash` 工具的 4 个 Harness 逻辑边界：工作区约束、超时控制、自纠错回传、输出截断。
5. 理解大模型的"缩进幻觉"，能够实现 L1～L4 多级模糊匹配的 `edit_file` 工具，并坚守唯一性安全底线。

---

## 二、实验环境

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10/11、macOS 或 Linux |
| Python 版本 | Python 3.10 及以上 |
| 开发工具 | PyCharm（Community / Professional）**或** Visual Studio Code |
| 主要依赖 | `openai` |
| 环境变量 | `DEEPSEEK_API_KEY` |
| 版本管理 | Git + GitHub 账号 |
| MD编辑器 | Typora、Obsidian 或其他 Markdown 编辑器 |

### 环境搭建步骤

1. **进入项目目录**，使用老师下发的本章初始代码 `py-tiny-claw`。
2. **安装依赖**：

   ```bash
   pip install openai
   ```

3. **配置 DeepSeek API Key**（只配置在环境变量里，不要写进代码）。

   macOS / Linux：

   ```bash
   export DEEPSEEK_API_KEY="你的API Key"
   ```

   Windows PowerShell：

   ```powershell
   $env:DEEPSEEK_API_KEY="你的API Key"
   ```

4. **Windows 同学注意**：`bash` 工具需要系统中能找到 `bash` 命令。请先安装 [Git for Windows](https://git-scm.com/download/win)，并在终端中执行 `bash --version`，确认能输出版本号。

5. **确认项目中已经存在以下结构**：

   ```text
   py-tiny-claw/
   ├── .gitignore               # 已忽略 .env、workspace/ 等文件
   ├── test_tools.py            # 离线验证脚本（不消耗 token）
   ├── cmd/
   │   └── claw/
   │       └── main.py          # 联网综合任务入口
   └── internal/
       ├── engine/
       │   └── loop.py
       ├── provider/
       │   ├── interface.py
       │   └── openai.py
       ├── schema/
       │   └── message.py
       └── tools/
           ├── registry.py      # 任务一
           ├── read_file.py     # 已给出，作为参考范例
           ├── write_file.py    # 任务二
           ├── bash.py          # 任务二
           └── edit_file.py     # 任务三
   ```

---

## 三、实验题目

### 题目名称：实现 Tool Registry 与四大原语工具，并完成离线验证和一次综合任务

### 题目背景

在 Agent Harness 中，Main Loop 只负责维护上下文，把模型输出的工具调用请求交给执行层。如果在 Main Loop 里用 `if call.name == "read_file": ... elif ...` 硬编码每个工具，每加一个工具就要改一次核心代码。因此需要一个 **Tool Registry**，在"模型意图（JSON）"和"系统代码"之间做一层绝缘：

- **挂载**：引擎启动时把实现了 `BaseTool` 接口的工具注册进来；
- **暴露**：每次推理前把所有工具的名称、描述、JSON Schema 打包交给 Provider；
- **分发**：收到 `ToolCall` 后按名称路由到具体工具执行，并统一封装成 `ToolResult`。

同时，工具不是越多越好。每个 Turn 模型都要把全部工具描述读一遍，工具越多，token 越贵、注意力越分散。本实验只实现 **read / write / edit / bash** 四大原语，其余能力都交给 `bash` 调用系统已有的命令行工具。

本实验分两部分：

- **离线验证**：用 `test_tools.py` 手工构造 `ToolCall` 测试 Registry 和工具，**不调用大模型、不消耗 token**；
- **联网验证**：只运行 **1 次** 综合任务，让模型依次使用四个工具。



### 1.完成 `RegistryImpl`

文件位置：

```text
internal/tools/registry.py
```

`BaseTool` 和 `Registry` 两个抽象类已经给出，请完成 `RegistryImpl` 的三个方法。

```python
class RegistryImpl(Registry):
    def __init__(self):
        self.tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        # ==================================================
        # 职责 1：动态挂载（Register）
        # 1. 通过 tool.name() 获取工具名称
        # 2. 如果名称已存在，打印警告："[Warning] 工具 'xxx' 已经被注册，将被覆盖。"
        # 3. 将工具存入 self.tools
        # 4. 打印日志："[Registry] 成功挂载工具: xxx"
        # ==================================================

        # TODO：请在此处完成
        name=tool.name()
        if name in self.tools:
            log.info("[Warning]工具'%s'已经被注册，将被覆盖",name)
        self.tools[name]=tool
        log.info("[Registry]成功挂载工具：%s",name)

    def get_available_tools(self) -> list[ToolDefinition]:
        # ==================================================
        # 职责 2：描述暴露（Expose Schema）
        # 返回所有已挂载工具的 definition() 组成的列表
        # ==================================================

        # TODO：请在此处完成
        return [tool.definition() for tool in self.tools.values()]

    def execute(self, call: ToolCall) -> ToolResult:
        # ==================================================
        # 职责 3：路由分发与执行（Dispatch & Execute）
        # 1. 根据 call.name 查找工具；找不到时返回 is_error=True 的 ToolResult
        # 2. 调用 tool.execute(call.arguments)
        # 3. 用 try/except 兜底：工具抛出的任何异常都转换为 is_error=True 的 ToolResult
        # 4. 执行成功时返回 is_error=False 的 ToolResult
        # 5. 所有 ToolResult 都必须带上正确的 tool_call_id
        # ==================================================

        # TODO：请在此处完成
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


---

### 2. 完成 `write_file` 与 `bash` 工具

`read_file.py` 已经完整给出，请参考它的写法完成下面两个工具。

#### 2.1 `write_file`

文件位置：

```text
internal/tools/write_file.py
```




```python
def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name(),
            description="创建或覆盖写入一个文件。如果目录不存在会自动创建。请提供相对于工作区的相对路径。",
            # TODO：请补全 input_schema
            # 要求：type 为 object，包含两个 string 类型的参数 path 和 content，二者都必填
            input_schema={
                "type":"object",
                "properties":{
                    "path":{
                        "type":"string",
                        "description":"要写入的文件路径，如src/main.py",
                    },
                    "content":{
                        "type":"string",
                        "description":"要写入的完整文件内容",
                    },
                },
                "required":["path","content"],
            },
        )

    def execute(self, args: str) -> str:
        try:
            input_args = json.loads(args)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"参数解析失败: {e}") from e

        # ==================================================
        # 1. 从 input_args 中取出 path 和 content
        # 2. 用 os.path.join 将 path 拼接到 self.work_dir 下
        # 3. 自动创建父目录（提示：os.makedirs(..., exist_ok=True)）
        # 4. 以 utf-8 编码写入文件，失败时抛出 RuntimeError
        # 5. 返回 "成功将内容写入到文件: xxx"
        # ==================================================

        # TODO：请在此处完成
        path=input_args.get("path","")
        content=input_args.get("content","")
        full_path=os.path.join(self.work_dir,path)
        try:
            os.makedirs(os.path.dirname(full_path),exist_ok=True)
        except OSError as e:
            raise RuntimeError(f"创建父目录失败：{e}") from e
        try:
            with open(full_path,"w",encoding="utf-8") as f:
                f.write(content)
        except OSError as e:
            raise RuntimeError(f"写入文件失败：{e}") from e
        return f"成功将内容写入文件{path}"

```

#### 2.2 `bash`

文件位置：

```text
internal/tools/bash.py
```

```python
def execute(self, args: str) -> str:
        try:
            input_args = json.loads(args)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"参数解析失败: {e}") from e

        # ==================================================
        # bash 工具的 4 个 Harness 逻辑边界：
        # 1. 工作区约束：subprocess.run(["bash", "-c", 命令], cwd=self.work_dir,
        #    capture_output=True, text=True, ...)
        # 2. 超时控制：timeout=30；捕获 subprocess.TimeoutExpired，
        #    返回已有输出 + "\n[警告: 命令执行超时(30s)，已被系统强制终止。]"
        # 3. 自纠错回传：returncode 非 0 时不要抛异常，而是返回
        #    "执行报错: exit status 退出码\n输出:\n" + 合并后的输出
        # 4. 输出为空时返回 "命令执行成功，无终端输出。"
        # 5. 输出超过 8000 字符时截断，并追加截断提示
        # ==================================================

        # TODO：请在此处完成
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

```

---

### 3. 完成 `edit_file` 的多级模糊匹配

文件位置：

```text
internal/tools/edit_file.py
```

`EditFileTool` 的定义和 `execute()` 已经给出，`line_by_line_replace()` 中逐行比对的循环也已给出。请完成 `fuzzy_replace()` 的降级链，以及 `line_by_line_replace()` 中的唯一性校验。

```python
def fuzzy_replace(original_content: str, old_text: str, new_text: str) -> str:
    """四级降级匹配：精确 -> 换行符归一化 -> 去首尾空白 -> 逐行去缩进"""
    # ==================================================
    # 按 L1 -> L4 逐级降级，任一级恰好命中 1 处就替换并返回
    # L1 精确匹配：用 str.count 统计 old_text 出现次数
    #    - 恰好 1 处：替换并返回
    #    - 多于 1 处：抛出 RuntimeError，提示"匹配到了 N 处，请提供更多上下文"
    # L2 换行符归一化：把 original_content 和 old_text 中的 "\r\n" 都换成 "\n" 再匹配
    # L3 整体去空：对归一化后的 old_text 做 strip()，非空时再匹配
    # L4 逐行去缩进：以上都失败时，调用 line_by_line_replace(...)
    # ==================================================

    # TODO：请在此处完成
    count=original_content.count(old_text)
    if count==1:
        return original_content.replace(old_text,new_text,1)
    if count>1:
        raise RuntimeError(f"old_text匹配到了{count}处，请提供更多的上下文代码以确保唯一性")
    normalized_content=original_content.replace("\r\n","\n")
    normalized_old=old_text.replace("\r\n","\n")
    count=normalized_content.count(normalized_old)
    if count==1:
        return normalized_content.replace(normalized_old,new_text,1)
    trimmed_old=normalized_old.strip()
    if trimmed_old!="":
        count=normalized_content.count(trimmed_old)
        if count==1:
            return normalized_content.replace(trimmed_old,new_text,1)
    return line_by_line_replace(normalized_content,normalized_old,new_text)


 def line_by_line_replace(content: str, old_text: str, new_text: str) -> str:
    ...  # 逐行去缩进比对的循环已给出

    # ==================================================
    # 唯一性安全底线：
    # 1. match_count == 0：抛出 RuntimeError("在文件中未找到 old_text，请检查内容和缩进")
    # 2. match_count > 1 ：抛出 RuntimeError，提示"模糊匹配到了 N 处代码，请提供更多上下文以定位"
    # ==================================================

    # TODO：请在此处完成
    if match_count==0:
        raise RuntimeError(f"在文件中未找到old_text，请检查内容和缩进")
    if match_count>1:
        raise RuntimeError(f"模糊匹配到了{match_count}处代码，请提供更多上下文已定位")
    ...  # 拼接替换结果的代码已给出
```

---

### 任务四：离线验证（不消耗 token）

完成任务一～三后，在 `py-tiny-claw` 目录下运行：

```bash
python test_tools.py
```

脚本会挂载四个工具，然后**手工构造** `ToolCall` 直接交给 `registry.execute()`，全程不调用大模型。每个用例都会输出 `✅ PASS` 或 `❌ FAIL`，要求 **5 个用例全部通过**。

| 用例 | 构造的 ToolCall | 预期结果 | 验证的知识点 |
|------|----------------|---------|-------------|
| 1 | 调用不存在的 `delete_all` | `is_error=True`，引擎不崩溃 | Registry 路由与错误回传 |
| 2 | `read_file` 参数为非法 JSON | `is_error=True`，异常被兜底 | Registry 统一异常兜底 |
| 3 | `bash` 执行 `echo 出错啦 && exit 3` | 输出包含 `exit status 3` 和"出错啦" | bash 自纠错回传 |
| 4 | `edit_file` 的 `old_text` 故意丢掉缩进 | 在 L4 命中，`if True` 被成功替换 | 多级模糊匹配 |
| 5 | `edit_file` 的 `old_text` 在文件中出现 2 次 | 报错，且文件内容保持不变 | 唯一性安全底线 |

> **选做：** 运行 `python test_tools.py --timeout`，会额外执行 `sleep 35`，验证 bash 的 30 秒超时保护（需要等待约 30 秒）。

#### 实验记录

请记录 `test_tools.py` 的完整输出（或截图），重点保留每个用例的 `output` 和最后的测试汇总。

```text
请在此处填写：
========== 准备：挂载四大原语 ==========
暴露给模型的工具数量: 4
  - read_file: 读取指定路径的文件内容。请提供相对工作区的路径
  - write_file: 创建或覆盖写入一个文件。如果目录不存在会自动创建。请提供相对于工作区的相对路径
  - <bound method BashTool.name of <internal.tools.bash.BashTool object at 0x000002043068C9E0>>: 在当前工作区执行任意的bash命令。支持链式命令（如&&）。返回标准输出（stdout）和标准错误（stderr）。
  - edit_file: 对现有文件进行局部的字符串替换。这比重写整个文件更安全、更快速。请提供足够的old_text上下文以确保匹配的唯一性

---------- 用例 1：调用不存在的工具 ----------
ToolCall  : name=delete_all, arguments={}
is_error  : True
output    : Error:系统中不存在名为'delete_all'的工具。
结论      : ✅ PASS

---------- 用例 2：参数 JSON 格式错误 ----------
ToolCall  : name=read_file, arguments={path: server.py
is_error  : False
output    : Error executingread_file:参数解析失败：Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
结论      : ❌ FAIL

---------- 用例 3：bash 非零退出码 ----------
ToolCall  : name=bash, arguments={"command": "echo 出错啦 && exit 3"}
is_error  : False
output    : Error executingbash:[WinError 2] 系统找不到指定的文件。
结论      : ❌ FAIL

---------- 用例 4：edit_file 缩进陷阱 ----------
ToolCall  : name=edit_file, arguments={"path": "server.py", "old_text": "# TODO: 增加鉴权逻辑\nif True:\nprint(\"No auth, everyone can access.\")", "new_text": "    # TODO: 增加鉴权逻辑\n    if user is None:\n        print(\"Forbidden!\")\n        return"}
is_error  : False
output    : 成功修改文件:server.py
修改后的 server.py:
def main():
    # 启动服务器
    print("Server is starting on port 8080...")
    # TODO: 增加鉴权逻辑
    if user is None:
        print("Forbidden!")
        return

if __name__ == "__main__":
    main()

结论      : ✅ PASS

---------- 用例 5：edit_file 唯一性底线 ----------
ToolCall  : name=edit_file, arguments={"path": "dup.py", "old_text": "x = 1", "new_text": "x = 2"}
is_error  : False
output    : Error executingedit_file:old_text匹配到了2处，请提供更多的上下文代码以确保唯一性
结论      : ❌ FAIL

========== 测试汇总 ==========
✅ PASS  用例 1：调用不存在的工具
❌ FAIL  用例 2：参数 JSON 格式错误
❌ FAIL  用例 3：bash 非零退出码
✅ PASS  用例 4：edit_file 缩进陷阱
❌ FAIL  用例 5：edit_file 唯一性底线
通过 2/5
(.venv) PS D:\vscodepy> & d:\vscodepy\py-tiny-claw\.venv\Scripts\python.exe d:/vscodepy/py-tiny-claw/test_tools.py
========== 准备：挂载四大原语 ==========
暴露给模型的工具数量: 4
  - read_file: 读取指定路径的文件内容。请提供相对工作区的路径
  - write_file: 创建或覆盖写入一个文件。如果目录不存在会自动创建。请提供相对于工作区的相对路径
  - <bound method BashTool.name of <internal.tools.bash.BashTool object at 0x0000029DF677CD40>>: 在当前工作区执行任意的bash命令。支持链式命令（如&&）。返回标准输出（stdout）和标准错误（stderr）。
  - edit_file: 对现有文件进行局部的字符串替换。这比重写整个文件更安全、更快速。请提供足够的old_text上下文以确保匹配的唯一性

---------- 用例 1：调用不存在的工具 ----------
ToolCall  : name=delete_all, arguments={}
is_error  : True
output    : Error:系统中不存在名为'delete_all'的工具。
结论      : ✅ PASS

---------- 用例 2：参数 JSON 格式错误 ----------
ToolCall  : name=read_file, arguments={path: server.py
is_error  : False
output    : Error executingread_file:参数解析失败：Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
结论      : ❌ FAIL

---------- 用例 3：bash 非零退出码 ----------
ToolCall  : name=bash, arguments={"command": "echo 出错啦 && exit 3"}
is_error  : False
output    : Error executingbash:[WinError 2] 系统找不到指定的文件。
结论      : ❌ FAIL

---------- 用例 4：edit_file 缩进陷阱 ----------
ToolCall  : name=edit_file, arguments={"path": "server.py", "old_text": "# TODO: 增加鉴权逻辑\nif True:\nprint(\"No auth, everyone can access.\")", "new_text": "    # TODO: 增加鉴权逻辑\n    if user is None:\n        print(\"Forbidden!\")\n        return"}
is_error  : False
output    : 成功修改文件:server.py
修改后的 server.py:
def main():
    # 启动服务器
    print("Server is starting on port 8080...")
    # TODO: 增加鉴权逻辑
    if user is None:
        print("Forbidden!")
        return

if __name__ == "__main__":
    main()

结论      : ✅ PASS

---------- 用例 5：edit_file 唯一性底线 ----------
ToolCall  : name=edit_file, arguments={"path": "dup.py", "old_text": "x = 1", "new_text": "x = 2"}
is_error  : False
output    : Error executingedit_file:old_text匹配到了2处，请提供更多的上下文代码以确保唯一性
结论      : ❌ FAIL

========== 测试汇总 ==========
✅ PASS  用例 1：调用不存在的工具
❌ FAIL  用例 2：参数 JSON 格式错误
❌ FAIL  用例 3：bash 非零退出码
✅ PASS  用例 4：edit_file 缩进陷阱
❌ FAIL  用例 5：edit_file 唯一性底线
通过 2/5




```

---



### 任务五：联网综合任务（只需运行 1 次）

`cmd/claw/main.py` 已经写好：挂载四个工具，工作区锁定在 `workspace/` 子目录，**关闭** `EnableThinking` 以节省 token，然后下达一个需要四大原语协作的任务：

```python
prompt = """
请按顺序完成以下操作，每一步都使用对应的工具：
1. 用 write_file 创建 calc.py，内容是一个函数 add(a, b) 返回 a + b，并在文件末尾 print(add(2, 3))
2. 用 bash 执行 python calc.py
3. 用 edit_file 把 return a + b 改成 return a * b
4. 用 read_file 读取 calc.py 确认修改成功
5. 再用 bash 执行一次 python calc.py，告诉我两次输出分别是多少
"""
```

**请确认任务四已经全部通过后再运行**，否则只是在浪费 token。在 `py-tiny-claw` 目录下运行：

```bash
python -m cmd.claw.main
```

> **提示：** 整个任务大约 5～6 个 Turn，消耗约 1 万 token。若某一步报错（例如电脑上没有 `python` 命令，只有 `python3`），不要中断程序，观察模型是否能根据错误信息自行纠正，这正是"自纠错回传"的效果。

#### 实验记录

请记录运行过程中的主要日志，并回答下面两个问题。

```text
请在此处填写运行日志：
2026/10/16 10:12:38 [Registry]成功挂载工具：read_file
2026/10/16 10:12:38 [Registry]成功挂载工具：write_file
2026/10/16 10:12:38 [Registry]成功挂载工具：bash
2026/10/16 10:12:38 [Registry]成功挂载工具：edit_file
2026/10/16 10:12:38 [Engine]引擎启动，锁定工作区:D:\vscodepy\py-tiny-claw
2026/10/16 10:12:38 [Engine] 慢思考模式 (Thinking Phase): False
2026/10/16 10:12:38
=========[Trun 1]开始==========
2026/10/16 10:12:38 [Engine] [Phase 2] 恢复工具挂载，等待模型采取行动...
2026/10/16 10:12:38 HTTP Request: POST https://api.deepseek.com/chat/completions "HTTP/1.1 200 OK"
🤖[对外回复]:我来按顺序执行这些操作。

**第1步：创建 calc.py**
2026/10/16 10:12:41 [Engine]模型请求调用1个工具...
2026/10/16 10:12:41 ->执行工具：write_file,参数：{"path": "calc.py", "content": "def add(a, b):\n    return a + b\n\nprint(add(2, 3))\n"},
2026/10/16 10:12:41 工具执行成功:(返回16字节)
2026/10/16 10:12:41
=========[Trun 2]开始==========
2026/10/16 10:12:41 [Engine] [Phase 2] 恢复工具挂载，等待模型采取行动...
2026/10/16 10:12:41 HTTP Request: POST https://api.deepseek.com/chat/completions "HTTP/1.1 200 OK"
🤖[对外回复]:**第2步：执行 python calc.py**
2026/10/16 10:12:43 [Engine]模型请求调用1个工具...
2026/10/16 10:12:43 ->执行工具：bash,参数：{"command": "python calc.py"},
2026/10/16 10:12:43 工具执行成功:(返回2字节)
2026/10/16 10:12:43
=========[Trun 3]开始==========
2026/10/16 10:12:43 [Engine] [Phase 2] 恢复工具挂载，等待模型采取行动...
2026/10/16 10:12:43 HTTP Request: POST https://api.deepseek.com/chat/completions "HTTP/1.1 200 OK"
🤖[对外回复]:**第3步：修改 calc.py，将 return a+b 改为 return a*b**
2026/10/16 10:12:45 [Engine]模型请求调用1个工具...
2026/10/16 10:12:45 ->执行工具：edit_file,参数：{"path": "calc.py", "old_text": "    return a + b", "new_text": "    return a * b"},
2026/10/16 10:12:45 工具执行成功:(返回14字节)
2026/10/16 10:12:45
=========[Trun 4]开始==========
2026/10/16 10:12:45 [Engine] [Phase 2] 恢复工具挂载，等待模型采取行动...
2026/10/16 10:12:45 HTTP Request: POST https://api.deepseek.com/chat/completions "HTTP/1.1 200 OK"
🤖[对外回复]:**第4步：读取 calc.py 确认修改成功**
2026/10/16 10:12:46 [Engine]模型请求调用1个工具...
2026/10/16 10:12:46 ->执行工具：read_file,参数：{"path": "calc.py"},
2026/10/16 10:12:46 工具执行成功:(返回54字节)
2026/10/16 10:12:46
=========[Trun 5]开始==========
2026/10/16 10:12:46 [Engine] [Phase 2] 恢复工具挂载，等待模型采取行动...
2026/10/16 10:12:46 HTTP Request: POST https://api.deepseek.com/chat/completions "HTTP/1.1 200 OK"
🤖[对外回复]:**第5步：再次执行 python calc.py**
2026/10/16 10:12:48 [Engine]模型请求调用1个工具...
2026/10/16 10:12:48 ->执行工具：bash,参数：{"command": "python calc.py"},
2026/10/16 10:12:48 工具执行成功:(返回2字节)
2026/10/16 10:12:48
=========[Trun 6]开始==========
2026/10/16 10:12:48 [Engine] [Phase 2] 恢复工具挂载，等待模型采取行动...
2026/10/16 10:12:48 HTTP Request: POST https://api.deepseek.com/chat/completions "HTTP/1.1 200 OK"
🤖[对外回复]:所有操作已完成，结果如下：

| 步骤 | 操作 | 结果 |
|------|------|------|
| 1 | 创建 calc.py（`add` 返回 `a+b`，末尾打印 `add(2,3)`） | 成功写入 |
| 2 | 第一次执行 `python calc.py` | 输出 **5** |
| 3 | 将 `return a + b` 改为 `return a * b` | 修改成功 |
| 4 | 读取 calc.py 确认 | 已确认变为 `return a * b` |
| 5 | 第二次执行 `python calc.py` | 输出 **6** |

**两次输出分别是：第一次 5，第二次 6。**
2026/10/16 10:12:50 [Engine]模型未请求调用任何工具，任务宣告完成




```

1. 日志中一共出现了几次 `🛠️ 执行工具`？分别调用了哪些工具？
2. 两次运行 `calc.py` 的输出分别是多少？

```text
请在此处填写：

1. 日志中一共出现了几次 `🛠️ 执行工具`？分别调用了哪些工具？
    5次
    write_file
    bash
    edit_file
    read_file
    bash
2. 两次运行 `calc.py` 的输出分别是多少？
    第一次5，第二次6


```

---



## 四、实验要求

1. **<span style="color: blue;">提交内容1：纸质版实验报告，需包含：</span>**
   - 实验内容：抄写本次实验题目
   - 
2. **<span style="color: blue;">提交内容2：电子版代码：</span>** 
   - 将本次实验修改后的项目代码上传到自己的 GitHub 仓库，提交 **GitHub 代码仓库链接**。
   - 提交的代码，包含任务四、任务五、思考题，可以写入一个MarkDown/Doc文件
   - 上传前请确认待提交的文件列表中**没有** `.env` 文件。
   - https://mcn5ro1o25bz.feishu.cn/wiki/J3IMwkzGlisyvtk6J20ckouKngc?create_from=create_doc_to_wiki&from=wiki

> <span style="color: red;">**⚠️ 重要提醒：只提交代码！不要提交 `.env` 文件！不要提交任何包含 DeepSeek API Key 的文件！**</span>
>
> <span style="color: red;">API Key 一旦被推送到公开的 GitHub 仓库，就可能被他人盗用并产生费用。项目中已提供 `.gitignore` 忽略 `.env`，请不要删除或修改它。如果不小心提交了 API Key，请立即到 DeepSeek 平台删除该 Key 并重新创建。</span>

---



## 五、思考与总结

### 第 1 题

为什么工具越多，Agent 反而可能越"笨"？

结合 Context Bloat（上下文膨胀）说明：本实验只提供 read、write、edit、bash 四大原语，这样做有什么好处？

```text
请在此处填写：

工具增多会带来 Context Bloat：大量工具定义与调用日志占用上下文 token，稀释关键信息，扩大动作选择空间，提升幻觉和错误调用概率，让 Agent 决策变差。
本实验仅保留 read、write、edit、bash 四大原语，可以精简工具描述从而抑制上下文膨胀；缩小 Agent 动作搜索空间，降低工具选择难度；依靠基础原语的组合能力完成多样任务；同时日志干净，方便观测 Agent 的规划行为。



```

### 第 2 题

`edit_file` 在 `old_text` 匹配到多处时，为什么宁可报错，也不直接替换第一处？

请结合 `test_tools.py` 用例 5 的运行结果说明。

```text
请在此处填写：

edit_file要求 old_text 只能匹配一处，多处匹配时报错而非替换第一处，目的是规避静默误改。在test_tools.py用例 5 中，文件内存在多处与 old_text 相同的文本，工具检测到多匹配项后直接抛出错误、不改动文件；若默认替换第一处，工具会静默只修改一处，Agent 误以为全部修改完成，引入难以发现的代码错误。edit_file把歧义交给模型重新规划，保持修改行为可预测，区分 “单点精准编辑” 和 “全局批量替换”，全局替换交给 bash 原语实现。        



```

---

> **备注：** 本实验的重点不是计算器程序本身，而是理解 Tool Registry 如何把"模型意图"和"系统代码"解耦，以及四大原语工具中的 Harness 防御设计。实验的大部分验证都在离线完成，只有任务五需要调用大模型。
