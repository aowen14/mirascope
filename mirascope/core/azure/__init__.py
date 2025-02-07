"""The Mirascope Azure Module."""

from typing import TypeAlias

from azure.ai.inference.models import ChatRequestMessage

from ._call import azure_call
from ._call import azure_call as call
from .call_params import AzureCallParams
from .call_response import AzureCallResponse
from .call_response_chunk import AzureCallResponseChunk
from .dynamic_config import AzureDynamicConfig
from .stream import AzureStream
from .tool import AzureTool, AzureToolConfig

AzureMessageParam: TypeAlias = ChatRequestMessage

__all__ = [
    "call",
    "AzureDynamicConfig",
    "AzureCallParams",
    "AzureCallResponse",
    "AzureCallResponseChunk",
    "AzureMessageParam",
    "AzureStream",
    "AzureTool",
    "AzureToolConfig",
    "azure_call",
]
