"""Unit tests for the to_me parameter in user_search_messages function."""

import pytest
from unittest.mock import patch, AsyncMock


class TestSearchToMeParameter:
    """Tests for the to_me parameter in user_search_messages."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_to_me_off_does_not_modify_query(self):
        """Test that to_me='off' does not add any filter to the query."""
        from user_tools.search import user_search_messages

        mock_response = {
            "ok": True,
            "messages": {
                "total": 0,
                "matches": [],
            },
            "response_metadata": {},
        }

        with patch(
            "user_tools.search.make_slack_user_request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_request:
            await user_search_messages(query="test query", to_me="off")

            # Verify the query was not modified
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            params = call_args.kwargs.get("params") or call_args[1].get("params")
            assert params["query"] == "test query"

    @pytest.mark.asyncio(loop_scope="function")
    async def test_to_me_dm_adds_to_filter(self):
        """Test that to_me='dm' adds 'to:<@user_id>' to the query."""
        from user_tools.search import user_search_messages

        mock_response = {
            "ok": True,
            "messages": {
                "total": 0,
                "matches": [],
            },
            "response_metadata": {},
        }

        with patch(
            "user_tools.search.make_slack_user_request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_request, patch(
            "user_tools.search.get_current_user_id",
            new_callable=AsyncMock,
            return_value="U12345678",
        ):
            await user_search_messages(query="test query", to_me="dm")

            # Verify 'to:<@user_id>' was added to the query
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            params = call_args.kwargs.get("params") or call_args[1].get("params")
            assert params["query"] == "test query to:<@U12345678>"

    @pytest.mark.asyncio(loop_scope="function")
    async def test_to_me_mention_adds_mention_filter(self):
        """Test that to_me='mention' adds '<@user_id>' to the query."""
        from user_tools.search import user_search_messages

        mock_response = {
            "ok": True,
            "messages": {
                "total": 0,
                "matches": [],
            },
            "response_metadata": {},
        }

        with patch(
            "user_tools.search.make_slack_user_request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_request, patch(
            "user_tools.search.get_current_user_id",
            new_callable=AsyncMock,
            return_value="U12345678",
        ):
            await user_search_messages(query="test query", to_me="mention")

            # Verify '<@user_id>' was added to the query
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            params = call_args.kwargs.get("params") or call_args[1].get("params")
            assert params["query"] == "test query <@U12345678>"

    @pytest.mark.asyncio(loop_scope="function")
    async def test_to_me_dm_calls_get_current_user_id(self):
        """Test that to_me='dm' calls get_current_user_id to retrieve the user ID."""
        from user_tools.search import user_search_messages

        mock_response = {
            "ok": True,
            "messages": {
                "total": 0,
                "matches": [],
            },
            "response_metadata": {},
        }

        with patch(
            "user_tools.search.make_slack_user_request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ), patch(
            "user_tools.search.get_current_user_id",
            new_callable=AsyncMock,
            return_value="U12345678",
        ) as mock_get_user_id:
            await user_search_messages(query="test", to_me="dm")

            mock_get_user_id.assert_called_once()

    @pytest.mark.asyncio(loop_scope="function")
    async def test_to_me_mention_calls_get_current_user_id(self):
        """Test that to_me='mention' calls get_current_user_id to retrieve the user ID."""
        from user_tools.search import user_search_messages

        mock_response = {
            "ok": True,
            "messages": {
                "total": 0,
                "matches": [],
            },
            "response_metadata": {},
        }

        with patch(
            "user_tools.search.make_slack_user_request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ), patch(
            "user_tools.search.get_current_user_id",
            new_callable=AsyncMock,
            return_value="U12345678",
        ) as mock_get_user_id:
            await user_search_messages(query="test", to_me="mention")

            mock_get_user_id.assert_called_once()

    @pytest.mark.asyncio(loop_scope="function")
    async def test_to_me_off_does_not_call_get_current_user_id(self):
        """Test that to_me='off' does NOT call get_current_user_id."""
        from user_tools.search import user_search_messages

        mock_response = {
            "ok": True,
            "messages": {
                "total": 0,
                "matches": [],
            },
            "response_metadata": {},
        }

        with patch(
            "user_tools.search.make_slack_user_request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ), patch(
            "user_tools.search.get_current_user_id",
            new_callable=AsyncMock,
            return_value="U12345678",
        ) as mock_get_user_id:
            await user_search_messages(query="test", to_me="off")

            mock_get_user_id.assert_not_called()
