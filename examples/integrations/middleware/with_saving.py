from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import Any, cast

from pydantic import BaseModel
from sqlalchemy import JSON, Column
from sqlmodel import Field, Session, SQLModel, create_engine

from mirascope.core import anthropic, prompt_template
from mirascope.core.base import BaseCallResponse, BaseType
from mirascope.core.base.stream import BaseStream
from mirascope.core.base.structured_stream import BaseStructuredStream
from mirascope.integrations import middleware_factory

engine = create_engine("sqlite:///database.db")


class CallResponseTable(SQLModel, table=True):
    """CallResponse model"""

    __tablename__: str = "call_response"  #  type: ignore

    id: int | None = Field(default=None, primary_key=True)
    function_name: str = Field(default="")
    prompt_template: str | None = Field(default=None)
    content: str | None = Field(default=None)
    response_model: dict | None = Field(sa_column=Column(JSON), default=None)
    cost: float | None = Field(default=None)


# ONE TIME SETUP
SQLModel.metadata.create_all(engine)


@contextmanager
def custom_context_manager(
    fn: Callable,
) -> Generator[Session, Any, None]:
    print(f"Saving call: {fn.__name__}")
    with Session(engine) as session:
        yield session


def handle_call_response(
    result: BaseCallResponse, fn: Callable, session: Session | None
):
    if not session:
        raise ValueError("Session is not set.")

    call_response_row = CallResponseTable(
        function_name=fn.__name__,
        content=result.content,
        prompt_template=result.prompt_template,
        cost=result.cost,
    )
    session.add(call_response_row)
    session.commit()


async def handle_call_response_async(
    result: BaseCallResponse, fn: Callable, session: Session | None
):
    handle_call_response(result, fn, session)


def handle_stream(stream: BaseStream, fn: Callable, session: Session | None):
    if not session:
        raise ValueError("Session is not set.")

    result = stream.construct_call_response()
    call_response_row = CallResponseTable(
        function_name=fn.__name__,
        content=result.content,
        prompt_template=result.prompt_template,
        cost=result.cost,
    )
    session.add(call_response_row)
    session.commit()


async def handle_stream_async(
    stream: BaseStream, fn: Callable, session: Session | None
):
    handle_stream(stream, fn, session)


def handle_response_model(
    response_model: BaseModel | BaseType, fn: Callable, session: Session | None
):
    if not session:
        raise ValueError("Session is not set.")

    if isinstance(response_model, BaseModel):
        result = cast(BaseCallResponse, response_model._response)  # pyright: ignore[reportAttributeAccessIssue]
        call_response_row = CallResponseTable(
            function_name=fn.__name__,
            response_model=response_model.model_dump(),
            prompt_template=result.prompt_template,
            cost=result.cost,
        )
    else:
        call_response_row = CallResponseTable(
            function_name=fn.__name__,
            content=str(response_model),
            prompt_template=fn._prompt_template,  # pyright: ignore[reportFunctionMemberAccess]
        )
    session.add(call_response_row)
    session.commit()


async def handle_response_model_async(
    response_model: BaseModel | BaseType, fn: Callable, session: Session | None
):
    handle_response_model(response_model, fn, session)


def handle_structured_stream(
    structured_stream: BaseStructuredStream, fn: Callable, session: Session | None
):
    if not session:
        raise ValueError("Session is not set.")

    result: BaseCallResponse = structured_stream.stream.construct_call_response()
    call_response_row = CallResponseTable(
        function_name=fn.__name__,
        content=result.content,
        prompt_template=result.prompt_template,
        cost=result.cost,
    )
    session.add(call_response_row)
    session.commit()


async def handle_structured_stream_async(
    structured_stream: BaseStructuredStream, fn: Callable, session: Session | None
):
    handle_structured_stream(structured_stream, fn, session)


def with_saving():
    """Saves some data after a Mirascope call."""

    return middleware_factory(
        custom_context_manager=custom_context_manager,
        custom_decorator=None,
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
@anthropic.call(model="claude-3-5-sonnet-20240620")
@prompt_template("What is your purpose?")
def run(): ...


print(run())
