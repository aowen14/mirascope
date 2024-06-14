"""Tests for Mirascope's Anthropic types module."""

from typing import Type

import pytest
from anthropic.lib.streaming import ContentBlockStopEvent
from anthropic.types import (
    ContentBlockDeltaEvent,
    ContentBlockStartEvent,
    Message,
    MessageStartEvent,
    TextBlock,
    Usage,
)

from mirascope.anthropic.tools import AnthropicTool
from mirascope.anthropic.types import (
    AnthropicAsyncStream,
    AnthropicCallResponse,
    AnthropicCallResponseChunk,
    AnthropicStream,
    AnthropicToolStream,
)


def test_anthropic_call_response(fixture_anthropic_message: Message):
    """Tests the `AnthropicCallResponse` class."""
    response = AnthropicCallResponse(
        response=fixture_anthropic_message, start_time=0, end_time=1
    )
    assert response.content == "test"
    assert response.message_param == {
        "content": [{"text": "test", "type": "text"}],
        "role": "assistant",
    }
    assert response.tools is None
    assert response.tool is None
    assert response.usage is not None
    assert response.output_tokens is not None
    assert response.input_tokens is not None
    assert response.model == fixture_anthropic_message.model
    assert response.id == fixture_anthropic_message.id
    assert response.finish_reasons == [fixture_anthropic_message.stop_reason]
    assert response.dump() == {
        "start_time": 0,
        "end_time": 1,
        "output": fixture_anthropic_message.model_dump(),
    }


def test_anthropic_call_response_json_mode_tool(
    fixture_anthropic_message_with_json_tool: Message,
    fixture_anthropic_book_tool: type[AnthropicTool],
):
    """Tests the `AnthropicCallResponse` class with a json mode tool."""
    response = AnthropicCallResponse(
        response=fixture_anthropic_message_with_json_tool,
        response_format="json",
        start_time=0,
        end_time=0,
        tool_types=[fixture_anthropic_book_tool],
    )
    assert response.tools is not None
    assert response.tools[0].args == {
        "title": "The Name of the Wind",
        "author": "Patrick Rothfuss",
    }


def test_anthropic_call_response_with_tools_bad_stop_reason(
    fixture_anthropic_message_with_tools_bad_stop_reason: Message,
    fixture_anthropic_book_tool: Type[AnthropicTool],
):
    """Tests the `AnthropicCallResponse` class with a tool and bad stop reason."""
    response = AnthropicCallResponse(
        response=fixture_anthropic_message_with_tools_bad_stop_reason,
        tool_types=[fixture_anthropic_book_tool],
        start_time=0,
        end_time=1,
    )
    with pytest.raises(RuntimeError):
        response.tool


def test_anthropic_call_response_chunk(
    fixture_anthropic_message_chunk: ContentBlockDeltaEvent,
):
    """Tests the `AnthropicCallResponseChunk` class."""
    chunk = AnthropicCallResponseChunk(chunk=fixture_anthropic_message_chunk)
    assert chunk.content == "test"

    chunk = AnthropicCallResponseChunk(
        chunk=ContentBlockStartEvent(
            content_block=TextBlock(text="test_start", type="text"),
            index=0,
            type="content_block_start",
        )
    )
    assert chunk.content == "test_start"
    assert chunk.type == "content_block_start"

    chunk = AnthropicCallResponseChunk(
        chunk=ContentBlockStopEvent(
            index=2,
            type="content_block_stop",
            content_block=TextBlock(text="", type="text"),
        )
    )
    assert chunk.content == ""
    assert chunk.type == "content_block_stop"

    chunk = AnthropicCallResponseChunk(
        chunk=MessageStartEvent(
            message=Message(
                id="test_id",
                model="test_model",
                role="assistant",
                type="message",
                content=[TextBlock(text="test", type="text")],
                stop_reason="end_turn",
                usage=Usage(input_tokens=1, output_tokens=1),
            ),
            type="message_start",
        )
    )
    assert chunk.usage is not None
    assert chunk.output_tokens == 1
    assert chunk.input_tokens == 1
    assert chunk.model == "test_model"
    assert chunk.id == "test_id"
    assert chunk.finish_reasons == ["end_turn"]
