"""Tests the `vertex._utils.setup_call` module."""

from unittest.mock import MagicMock, patch

import pytest
from google.cloud.aiplatform_v1beta1.types import (
    GenerationConfig as GenerationConfigType,
)
from vertexai.generative_models import (
    Content,
    GenerationConfig,
    GenerativeModel,
    Part,
    ToolConfig,
)

from mirascope.core.vertex._utils._setup_call import setup_call
from mirascope.core.vertex.tool import VertexTool


@pytest.fixture()
def mock_base_setup_call() -> MagicMock:
    """Returns the mock setup_call function."""
    mock_setup_call = MagicMock()
    mock_setup_call.return_value = [MagicMock() for _ in range(3)] + [{}]
    return mock_setup_call


@patch(
    "mirascope.core.vertex._utils._setup_call.convert_message_params",
    new_callable=MagicMock,
)
@patch("mirascope.core.vertex._utils._setup_call._utils", new_callable=MagicMock)
@patch(
    "mirascope.core.vertex._utils._setup_call.GenerativeModel", new_callable=MagicMock
)
def test_setup_call(
    mock_generative_model: MagicMock,
    mock_utils: MagicMock,
    mock_convert_message_params: MagicMock,
    mock_base_setup_call: MagicMock,
) -> None:
    """Tests the `setup_call` function."""
    mock_client = MagicMock(spec=GenerativeModel)
    mock_generative_model.return_value = mock_client
    mock_utils.setup_call = mock_base_setup_call
    fn = MagicMock()
    create, prompt_template, messages, tool_types, call_kwargs = setup_call(
        model="gemini-1.5-flash",
        client=None,
        fn=fn,
        fn_args={},
        dynamic_config=None,
        tools=None,
        json_mode=False,
        call_params={},
        extract=False,
    )
    assert prompt_template == mock_base_setup_call.return_value[0]
    assert tool_types == mock_base_setup_call.return_value[2]
    assert "contents" in call_kwargs and call_kwargs["contents"] == messages
    mock_base_setup_call.assert_called_once_with(fn, {}, None, None, VertexTool, {})
    mock_convert_message_params.assert_called_once_with(
        mock_base_setup_call.return_value[1]
    )
    assert messages == mock_convert_message_params.return_value
    mock_generative_model.assert_called_once_with(model_name="gemini-1.5-flash")
    assert create(**call_kwargs)
    mock_client.generate_content.assert_called_once_with(**call_kwargs)
    mock_client.generate_content.reset_mock()
    assert create(stream=True, **call_kwargs)
    mock_client.generate_content.assert_called_once_with(**call_kwargs, stream=True)
    mock_client.generate_content.reset_mock()
    assert create(stream=False, **call_kwargs)
    mock_client.generate_content.assert_called_once_with(**call_kwargs)


@pytest.mark.parametrize("generation_config_type", [dict, GenerationConfig])
@patch(
    "mirascope.core.vertex._utils._setup_call.convert_message_params",
    new_callable=MagicMock,
)
@patch("mirascope.core.vertex._utils._setup_call._utils", new_callable=MagicMock)
@patch(
    "mirascope.core.vertex._utils._setup_call.GenerativeModel", new_callable=MagicMock
)
def test_setup_call_json_mode(
    mock_generative_model: MagicMock,
    mock_utils: MagicMock,
    mock_convert_message_params: MagicMock,
    mock_base_setup_call: MagicMock,
    generation_config_type: type,
) -> None:
    """Tests the `setup_call` function with JSON mode."""
    mock_utils.setup_call = mock_base_setup_call
    mock_utils.json_mode_content = MagicMock(return_value="mock content")
    mock_generative_model.return_value = MagicMock()
    mock_base_setup_call.return_value[1] = [
        Content(role="user", parts=[Part.from_text("test")])
    ]
    mock_base_setup_call.return_value[-1]["tools"] = MagicMock()
    mock_base_setup_call.return_value[-1]["generation_config"] = GenerationConfigType(
        candidate_count=1,
        max_output_tokens=100,
        response_mime_type="application/xml",
        response_schema=None,
        stop_sequences=["\n"],
        temperature=0.5,
        top_k=0,
        top_p=0,
    )
    mock_convert_message_params.side_effect = lambda x: x
    _, _, messages, _, call_kwargs = setup_call(
        model="gemini-1.5-flash",
        client=None,
        fn=MagicMock(),
        fn_args={},
        dynamic_config=None,
        tools=None,
        json_mode=True,
        call_params={},
        extract=False,
    )
    assert messages[-1].parts[-1].text == "mock content"
    assert "tools" not in call_kwargs
    assert "generation_config" in call_kwargs
    generation_config = call_kwargs["generation_config"]
    assert generation_config.temperature == 0.5
    assert generation_config.top_p == 0
    assert generation_config.top_k == 0
    assert generation_config.candidate_count == 1
    assert generation_config.max_output_tokens == 100
    assert generation_config.stop_sequences == ["\n"]
    assert generation_config.response_mime_type == "application/json"


@patch(
    "mirascope.core.vertex._utils._setup_call.convert_message_params",
    new_callable=MagicMock,
)
@patch("mirascope.core.vertex._utils._setup_call._utils", new_callable=MagicMock)
@patch(
    "mirascope.core.vertex._utils._setup_call.GenerativeModel", new_callable=MagicMock
)
def test_setup_call_extract(
    mock_generative_model: MagicMock,
    mock_utils: MagicMock,
    mock_convert_message_params: MagicMock,
    mock_base_setup_call: MagicMock,
) -> None:
    """Tests the `setup_call` function with extraction."""
    mock_tool = MagicMock()
    mock_tool._name.side_effect = lambda: "test"
    mock_base_setup_call.return_value[2] = [mock_tool]
    mock_utils.setup_call = mock_base_setup_call
    _, _, _, _, call_kwargs = setup_call(
        model="gemini-1.5-flash",
        client=None,
        fn=MagicMock(),
        fn_args={},
        dynamic_config=None,
        tools=None,
        json_mode=False,
        call_params={},
        extract=True,
    )
    assert "tool_config" in call_kwargs and isinstance(
        call_kwargs["tool_config"], ToolConfig
    )
    function_calling_config = call_kwargs[
        "tool_config"
    ]._gapic_tool_config.function_calling_config
    assert function_calling_config.allowed_function_names == ["test"]
    assert function_calling_config.mode == function_calling_config.Mode.ANY
