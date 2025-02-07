"""The Mirascope Vertex Module."""

from typing import TypeAlias

from vertexai.generative_models import Content

from ._call import vertex_call
from ._call import vertex_call as call
from .call_params import VertexCallParams
from .call_response import VertexCallResponse
from .call_response_chunk import VertexCallResponseChunk
from .dynamic_config import VertexDynamicConfig
from .stream import VertexStream
from .tool import VertexTool

VertexMessageParam: TypeAlias = Content

__all__ = [
    "call",
    "VertexCallParams",
    "VertexCallResponse",
    "VertexCallResponseChunk",
    "VertexDynamicConfig",
    "VertexMessageParam",
    "VertexStream",
    "VertexTool",
    "vertex_call",
]
