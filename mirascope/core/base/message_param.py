"""This module contains the base class for message parameters."""

from typing import Literal

from pydantic import BaseModel


class TextPart(BaseModel):
    """A content part for text.

    Attributes:
        type: Always "text"
        text: The text content
    """

    type: Literal["text"]
    text: str


class CacheControlPart(BaseModel):
    """A `TextPart` with cache control.

    This part is currently only available with Anthropic. For more details, see:
    https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching

    Attributes:
        type: Always "cache_control"
        cache_type: Currently only "ephemeral" is available.
    """

    type: Literal["cache_control"]
    cache_type: str


class ImagePart(BaseModel):
    """A content part for images.

    Attributes:
        type: Always "image"
        media_type: The media type (e.g. image/jpeg)
        image: The raw image bytes
        detail: (Optional) The detail to use for the image (supported by OpenAI)
    """

    type: Literal["image"]
    media_type: str
    image: bytes
    detail: str | None


class AudioPart(BaseModel):
    """A content part for audio.

    Attributes:
        type: Always "audio"
        media_type: The media type (e.g. audio/wav)
        audio: The raw audio bytes
    """

    type: Literal["audio"]
    media_type: str
    audio: bytes


class BaseMessageParam(BaseModel):
    """A base class for message parameters.

    usage docs: learn/prompts.md#messages

    Attributes:
        role: The role of the message (e.g. "system", "user", "assistant")
        content: The content of the message
    """

    role: str
    content: str | list[TextPart | ImagePart | AudioPart | CacheControlPart]
