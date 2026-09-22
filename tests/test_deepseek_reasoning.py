from types import SimpleNamespace

from internal.provider.openai import OpenAIProvider
from internal.schema.message import Message, ToolCall, ToolDefinition, ROLE_ASSISTANT, ROLE_USER


class DummyChatCompletions:
    @staticmethod
    def create(**kwargs):
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="final answer",
                        reasoning_content="thinking step",
                        tool_calls=[],
                    )
                )
            ]
        )


class DummyClient:
    chat = SimpleNamespace(completions=DummyChatCompletions())


def test_generate_preserves_reasoning_content():
    provider = OpenAIProvider(client=DummyClient(), model="deepseek-v4-pro")
    msg = Message(role=ROLE_USER, content="hi")

    result = provider.generate([msg], None)

    assert result.content == "final answer"
    assert result.reasoning_content == "thinking step"


def test_assistant_message_serializes_reasoning_content():
    provider = OpenAIProvider(client=DummyClient(), model="deepseek-v4-pro")
    msg = Message(
        role=ROLE_ASSISTANT,
        content="response",
        reasoning_content="internal thought",
        tool_calls=[ToolCall(id="call_1", name="get_weather", arguments='{"city":"北京"}')],
    )

    tools = [
        ToolDefinition(
            name="get_weather",
            description="天气",
            input_schema={"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]},
        )
    ]

    provider.generate([msg], tools)
