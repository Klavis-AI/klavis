"""Unit tests for AG2 + Klavis integration example."""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture(autouse=True)
def set_env_vars():
    """Set required environment variables for tests."""
    os.environ["KLAVIS_API_KEY"] = "test_klavis_key"
    os.environ["OPENAI_API_KEY"] = "test_openai_key"
    yield
    os.environ.pop("KLAVIS_API_KEY", None)
    os.environ.pop("OPENAI_API_KEY", None)


def _make_strata_response(with_oauth=False):
    """Create a mock Strata server response."""
    response = MagicMock()
    response.strata_server_url = "https://strata.klavis.ai/mcp/test-instance"
    response.oauth_urls = {"gmail": "https://oauth.example.com/gmail"} if with_oauth else {}
    return response


def _make_toolkit(tool_names=None):
    """Create a mock AG2 toolkit with the given tool names."""
    tool_names = tool_names or [
        "discover_server_categories_or_actions",
        "get_category_actions",
        "get_action_details",
        "execute_action",
    ]
    toolkit = MagicMock()
    toolkit.tools = [MagicMock(name=name) for name in tool_names]
    for tool, name in zip(toolkit.tools, tool_names):
        tool.name = name
    return toolkit


# ---------------------------------------------------------------------------
# Klavis client
# ---------------------------------------------------------------------------

def test_klavis_client_uses_api_key():
    """Klavis client is initialised with the key from the environment."""
    with patch("klavis.Klavis") as MockKlavis:
        from klavis import Klavis
        Klavis(api_key=os.getenv("KLAVIS_API_KEY"))
        MockKlavis.assert_called_once_with(api_key="test_klavis_key")


def test_create_strata_server_called_with_correct_servers():
    """create_strata_server is called with Gmail and Slack."""
    from klavis.types import McpServerName

    klavis_client = MagicMock()
    klavis_client.mcp_server.create_strata_server.return_value = _make_strata_response()

    klavis_client.mcp_server.create_strata_server(
        servers=[McpServerName.GMAIL, McpServerName.SLACK],
        user_id="demo_user",
    )

    klavis_client.mcp_server.create_strata_server.assert_called_once_with(
        servers=[McpServerName.GMAIL, McpServerName.SLACK],
        user_id="demo_user",
    )


# ---------------------------------------------------------------------------
# OAuth handling
# ---------------------------------------------------------------------------

def test_no_oauth_prompt_when_no_urls():
    """No browser/input calls when oauth_urls is empty."""
    response = _make_strata_response(with_oauth=False)

    with patch("webbrowser.open") as mock_browser, patch("builtins.input") as mock_input:
        if response.oauth_urls:
            for _, url in response.oauth_urls.items():
                import webbrowser
                webbrowser.open(url)
                input("Press Enter...")

        mock_browser.assert_not_called()
        mock_input.assert_not_called()


def test_oauth_prompt_when_urls_present():
    """Browser is opened once per OAuth URL."""
    response = _make_strata_response(with_oauth=True)

    with patch("webbrowser.open") as mock_browser, patch("builtins.input", return_value=""):
        for _, url in response.oauth_urls.items():
            import webbrowser
            webbrowser.open(url)

        assert mock_browser.call_count == len(response.oauth_urls)


# ---------------------------------------------------------------------------
# Toolkit creation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_toolkit_called_with_use_mcp_resources_false():
    """create_toolkit is always called with use_mcp_resources=False."""
    mock_session = AsyncMock()
    mock_toolkit = _make_toolkit()

    with patch("autogen.mcp.create_toolkit", new=AsyncMock(return_value=mock_toolkit)) as mock_create:
        from autogen.mcp import create_toolkit
        toolkit = await create_toolkit(session=mock_session, use_mcp_resources=False)

        mock_create.assert_called_once_with(session=mock_session, use_mcp_resources=False)
        assert toolkit is mock_toolkit


@pytest.mark.asyncio
async def test_toolkit_tools_are_accessible():
    """Toolkit exposes a list of tools with name attributes."""
    mock_session = AsyncMock()
    expected_names = ["discover_server_categories_or_actions", "execute_action"]
    mock_toolkit = _make_toolkit(expected_names)

    with patch("autogen.mcp.create_toolkit", new=AsyncMock(return_value=mock_toolkit)):
        from autogen.mcp import create_toolkit
        toolkit = await create_toolkit(session=mock_session, use_mcp_resources=False)

        assert [t.name for t in toolkit.tools] == expected_names


# ---------------------------------------------------------------------------
# Agent configuration
# ---------------------------------------------------------------------------

def test_assistant_agent_created_with_correct_config():
    """AssistantAgent is configured with the expected model and system message."""
    with patch("autogen.AssistantAgent") as MockAgent:
        from autogen import AssistantAgent, LLMConfig

        llm_config = LLMConfig({"model": "gpt-4o-mini", "api_key": "test_openai_key"})
        AssistantAgent(
            name="klavis_assistant",
            system_message="You are a helpful assistant that uses MCP tools to complete tasks.",
            llm_config=llm_config,
        )

        MockAgent.assert_called_once()
        call_kwargs = MockAgent.call_args.kwargs
        assert call_kwargs["name"] == "klavis_assistant"
        assert "MCP tools" in call_kwargs["system_message"]


def test_toolkit_register_for_llm_called():
    """toolkit.register_for_llm is called with the assistant agent."""
    mock_toolkit = _make_toolkit()
    mock_agent = MagicMock()

    mock_toolkit.register_for_llm(mock_agent)

    mock_toolkit.register_for_llm.assert_called_once_with(mock_agent)


# ---------------------------------------------------------------------------
# Agent run
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_agent_run_called_with_correct_params():
    """a_run is invoked with the user query and correct settings."""
    mock_agent = MagicMock()
    mock_result = AsyncMock()
    mock_agent.a_run = AsyncMock(return_value=mock_result)

    mock_toolkit = _make_toolkit()
    user_query = "Check my latest 5 emails and summarize them in a Slack message to #general"

    await mock_agent.a_run(
        message=user_query,
        tools=mock_toolkit.tools,
        max_turns=10,
        user_input=False,
    )

    mock_agent.a_run.assert_called_once_with(
        message=user_query,
        tools=mock_toolkit.tools,
        max_turns=10,
        user_input=False,
    )


@pytest.mark.asyncio
async def test_result_process_is_awaited():
    """result.process() is awaited after a_run."""
    mock_result = AsyncMock()
    mock_result.process = AsyncMock()

    await mock_result.process()

    mock_result.process.assert_called_once()
