"""The `middleware_factory` method for handling the call response."""

import inspect
from collections.abc import AsyncGenerator, Awaitable, Callable, Generator
from contextlib import AbstractContextManager, contextmanager
from functools import wraps
from typing import (
    Any,
    ParamSpec,
    TypeVar,
    cast,
    overload,
)

from pydantic import BaseModel

from mirascope.core.base._utils._base_type import BaseType

from ..core.base.call_response import BaseCallResponse
from ..core.base.stream import BaseStream
from ..core.base.structured_stream import BaseStructuredStream

_BaseCallResponseT = TypeVar("_BaseCallResponseT", bound=BaseCallResponse)
_BaseStructuredStreamT = TypeVar("_BaseStructuredStreamT", bound=BaseStructuredStream)
_BaseStreamT = TypeVar("_BaseStreamT", bound=BaseStream)
_ResponseModelT = TypeVar("_ResponseModelT", bound=BaseModel | BaseType)
ResponseModel = BaseModel | BaseType
_P = ParamSpec("_P")
SyncFunc = Callable[
    _P, _BaseCallResponseT | _BaseStreamT | _ResponseModelT | _BaseStructuredStreamT
]
AsyncFunc = Callable[
    _P,
    Awaitable[
        _BaseCallResponseT | _BaseStreamT | _ResponseModelT | _BaseStructuredStreamT
    ],
]
_T = TypeVar("_T")
_R = TypeVar("_R")


@contextmanager
def default_context_manager(
    fn: SyncFunc | AsyncFunc,
) -> Generator[None, None, None]:
    yield None


def middleware_factory(
    custom_context_manager: Callable[
        [SyncFunc | AsyncFunc], AbstractContextManager[_T]
    ] = default_context_manager,
    custom_decorator: Callable | None = None,
    handle_call_response: Callable[
        [BaseCallResponse, SyncFunc | AsyncFunc, _T | None], None
    ]
    | None = None,
    handle_call_response_async: Callable[
        [BaseCallResponse, SyncFunc | AsyncFunc, _T | None], Awaitable[None]
    ]
    | None = None,
    handle_stream: Callable[[BaseStream, SyncFunc | AsyncFunc, _T | None], None]
    | None = None,
    handle_stream_async: Callable[
        [BaseStream, SyncFunc | AsyncFunc, _T | None], Awaitable[None]
    ]
    | None = None,
    handle_response_model: Callable[
        [ResponseModel, SyncFunc | AsyncFunc, _T | None], None
    ]
    | None = None,
    handle_response_model_async: Callable[
        [ResponseModel, SyncFunc | AsyncFunc, _T | None], Awaitable[None]
    ]
    | None = None,
    handle_structured_stream: Callable[
        [BaseStructuredStream, SyncFunc | AsyncFunc, _T | None], None
    ]
    | None = None,
    handle_structured_stream_async: Callable[
        [BaseStructuredStream, SyncFunc | AsyncFunc, _T | None], Awaitable[None]
    ]
    | None = None,
) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
    '''A factory method for creating middleware decorators.

    Example:

    ```python
    from mirascope.core import openai, prompt_template
    from mirascope.integrations import middleware_factory

    def with_saving():
        """Saves some data after a Mirascope call."""

        return middleware_factory(
            custom_context_manager=custom_context_manager,
            custom_decorator=custom_decorator,
            handle_call_response=handle_call_response,
            handle_call_response_async=handle_call_response_async,
            handle_stream=handle_stream,
            handle_stream_async=handle_stream_async,
            handle_response_model=handle_response_model,
            handle_response_model_async=handle_response_model_async,
            handle_structured_stream=handle_structured_stream,
            handle_structured_stream_async=handle_structured_stream_async,
        )


    @with_saving()
    @openai.call("gpt-4o-mini")
    @prompt_template("Recommend a {genre} book")
    def recommend_book(genre: str):
        ...


    response = recommend_book("fantasy")  # `with_saving` automatically run
    print(response.content)
    ```
    '''

    @overload
    def decorator(fn: Callable[_P, _R]) -> Callable[_P, _R]: ...

    @overload
    def decorator(fn: Callable[_P, Awaitable[_R]]) -> Callable[_P, Awaitable[_R]]: ...

    def decorator(
        fn: Callable[_P, _R | Awaitable[_R]],
    ) -> Callable[_P, _R | Awaitable[_R]]:
        if inspect.iscoroutinefunction(fn):

            @wraps(fn)
            async def wrapper_async(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                result = await fn(*args, **kwargs)
                if (
                    isinstance(result, BaseCallResponse)
                    and handle_call_response_async is not None
                ):
                    with custom_context_manager(fn) as context:
                        await handle_call_response_async(result, fn, context)
                elif isinstance(result, BaseStream):
                    original_class = type(result)
                    original_aiter = result.__aiter__

                    def new_stream_aiter(
                        self: Any,  # noqa: ANN401
                    ) -> AsyncGenerator[tuple[Any, Any | None], Any]:  # noqa: ANN401
                        async def generator() -> (
                            AsyncGenerator[tuple[Any, Any | None], Any]
                        ):
                            with custom_context_manager(fn) as context:
                                async for chunk, tool in original_aiter():
                                    yield chunk, tool
                                if handle_stream_async is not None:
                                    await handle_stream_async(result, fn, context)

                        return generator()

                    class MiddlewareAsyncStream(original_class):
                        __aiter__ = (
                            custom_decorator(fn)(new_stream_aiter)
                            if custom_decorator
                            else new_stream_aiter
                        )

                    result.__class__ = MiddlewareAsyncStream
                elif (
                    isinstance(result, ResponseModel)
                    and handle_response_model_async is not None
                ):
                    with custom_context_manager(fn) as context:
                        await handle_response_model_async(result, fn, context)
                elif isinstance(result, BaseStructuredStream):
                    original_class = type(result)
                    original_aiter = result.__aiter__

                    def new_aiter(
                        self: Any,  # noqa: ANN401
                    ) -> AsyncGenerator[tuple[Any, Any | None], Any]:  # noqa: ANN401
                        async def generator() -> (
                            AsyncGenerator[tuple[Any, Any | None], Any]
                        ):
                            with custom_context_manager(fn) as context:
                                async for chunk in original_aiter():
                                    yield chunk
                                if handle_structured_stream_async is not None:
                                    await handle_structured_stream_async(
                                        result, fn, context
                                    )

                        return generator()

                    class MiddlewareAsyncStructuredStream(original_class):
                        __aiter__ = (
                            custom_decorator(fn)(new_aiter)
                            if custom_decorator
                            else new_aiter
                        )

                    result.__class__ = MiddlewareAsyncStructuredStream
                return cast(_R, result)

            return (
                custom_decorator(fn)(wrapper_async)
                if custom_decorator
                else wrapper_async
            )
        else:

            @wraps(fn)
            def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                result = fn(*args, **kwargs)
                if (
                    isinstance(result, BaseCallResponse)
                    and handle_call_response is not None
                ):
                    with custom_context_manager(fn) as context:
                        handle_call_response(result, fn, context)
                elif isinstance(result, BaseStream):
                    original_class = type(result)
                    original_iter = result.__iter__

                    def new_stream_iter(
                        self: Any,  # noqa: ANN401
                    ) -> Generator[tuple[Any, Any | None], None, None]:  # noqa: ANN401
                        # Create the context manager when user iterates over the stream
                        with custom_context_manager(fn) as context:
                            yield from original_iter()
                            if handle_stream is not None:
                                handle_stream(result, fn, context)

                    class MiddlewareStream(original_class):
                        __iter__ = (
                            custom_decorator(fn)(new_stream_iter)
                            if custom_decorator
                            else new_stream_iter
                        )

                    result.__class__ = MiddlewareStream
                elif (
                    isinstance(result, ResponseModel)
                    and handle_response_model is not None
                ):
                    with custom_context_manager(fn) as context:
                        handle_response_model(result, fn, context)
                elif isinstance(result, BaseStructuredStream):
                    original_class = type(result)
                    original_iter = result.__iter__

                    def new_iter(
                        self: Any,  # noqa: ANN401
                    ) -> Generator[
                        Generator[tuple[Any, Any | None], None, None]
                        | Generator[Any, None, None],
                        Any,
                        None,
                    ]:  # noqa: ANN401
                        # Create the context manager when user iterates over the stream
                        with custom_context_manager(fn) as context:
                            yield from original_iter()
                            if handle_structured_stream is not None:
                                handle_structured_stream(result, fn, context)

                    class MiddlewareStructuredStream(original_class):
                        __iter__ = (
                            custom_decorator(fn)(new_iter)
                            if custom_decorator
                            else new_iter
                        )

                    result.__class__ = MiddlewareStructuredStream
                return cast(_R, result)

            return custom_decorator(fn)(wrapper) if custom_decorator else wrapper

    return decorator
