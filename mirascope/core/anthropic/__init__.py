"""The Mirascope Anthropic Module."""

from typing import TypeAlias

from anthropic.types import MessageParam

from ._call import anthropic_call
from ._call import anthropic_call as call
from .call_params import AnthropicCallParams
from .call_response import AnthropicCallResponse
from .call_response_chunk import AnthropicCallResponseChunk
from .dynamic_config import AnthropicDynamicConfig
from .stream import AnthropicStream
from .tool import AnthropicTool, AnthropicToolConfig

AnthropicMessageParam: TypeAlias = MessageParam

__all__ = [
    "call",
    "AnthropicDynamicConfig",
    "AnthropicCallParams",
    "AnthropicCallResponse",
    "AnthropicCallResponseChunk",
    "AnthropicMessageParam",
    "AnthropicStream",
    "AnthropicTool",
    "AnthropicToolConfig",
    "anthropic_call",
]
