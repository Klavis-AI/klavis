import pytest
from unittest.mock import AsyncMock, patch

from tools.base import ms_graph_token_context
from tools.teams import (
    list_all_teams,
    get_team,
    list_channels,
    create_channel,
    send_channel_message,
    list_joined_teams,
)
from tools.chats import list_chats, send_chat_message
from tools.users import list_users, get_user
from tools.meetings import create_online_meeting, list_online_meetings


@pytest.fixture(autouse=True)
def set_token_context():
    """Set a mock token in the context for all tests."""
    token = ms_graph_token_context.set("mock_access_token")
    yield
    ms_graph_token_context.reset(token)


class TestTeamsTools:
    @pytest.mark.asyncio
    async def test_list_all_teams(self):
        mock_response = {
            "value": [
                {"id": "team-1", "displayName": "Team One"},
                {"id": "team-2", "displayName": "Team Two"},
            ]
        }
        with patch("tools.teams.make_graph_api_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await list_all_teams()

            mock_request.assert_called_once_with(
                "GET", "/groups?$filter=resourceProvisioningOptions/Any(x:x eq 'Team')"
            )
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_get_team(self):
        mock_response = {"id": "team-123", "displayName": "Test Team", "description": "A test team"}
        with patch("tools.teams.make_graph_api_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await get_team("team-123")

            mock_request.assert_called_once_with("GET", "/teams/team-123")
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_list_channels(self):
        mock_response = {
            "value": [
                {"id": "channel-1", "displayName": "General"},
                {"id": "channel-2", "displayName": "Random"},
            ]
        }
        with patch("tools.teams.make_graph_api_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await list_channels("team-123")

            mock_request.assert_called_once_with("GET", "/teams/team-123/channels")
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_create_channel(self):
        mock_response = {"id": "new-channel", "displayName": "New Channel", "membershipType": "standard"}
        with patch("tools.teams.make_graph_api_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await create_channel("team-123", "New Channel", "A new channel")

            mock_request.assert_called_once_with(
                "POST",
                "/teams/team-123/channels",
                json_data={
                    "displayName": "New Channel",
                    "description": "A new channel",
                    "membershipType": "standard",
                },
            )
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_create_channel_without_description(self):
        mock_response = {"id": "new-channel", "displayName": "New Channel", "membershipType": "standard"}
        with patch("tools.teams.make_graph_api_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await create_channel("team-123", "New Channel")

            mock_request.assert_called_once_with(
                "POST",
                "/teams/team-123/channels",
                json_data={
                    "displayName": "New Channel",
                    "description": None,
                    "membershipType": "standard",
                },
            )
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_send_channel_message(self):
        mock_response = {"id": "msg-123", "body": {"content": "Hello, Team!"}}
        with patch("tools.teams.make_graph_api_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await send_channel_message("team-123", "channel-456", "Hello, Team!")

            mock_request.assert_called_once_with(
                "POST",
                "/teams/team-123/channels/channel-456/messages",
                json_data={"body": {"content": "Hello, Team!"}},
            )
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_list_joined_teams(self):
        mock_response = {
            "value": [
                {"id": "team-1", "displayName": "My Team One"},
                {"id": "team-2", "displayName": "My Team Two"},
            ]
        }
        with patch("tools.teams.make_graph_api_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await list_joined_teams()

            mock_request.assert_called_once_with("GET", "/me/joinedTeams")
            assert result == mock_response


class TestChatsTools:
    @pytest.mark.asyncio
    async def test_list_chats(self):
        mock_response = {
            "value": [
                {"id": "chat-1", "chatType": "oneOnOne"},
                {"id": "chat-2", "chatType": "group"},
            ]
        }
        with patch("tools.chats.make_graph_api_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await list_chats()

            mock_request.assert_called_once_with("GET", "/chats")
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_send_chat_message(self):
        mock_response = {"id": "msg-123", "body": {"content": "Hello!"}}
        with patch("tools.chats.make_graph_api_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await send_chat_message("chat-123", "Hello!")

            mock_request.assert_called_once_with(
                "POST",
                "/chats/chat-123/messages",
                json_data={"body": {"content": "Hello!"}},
            )
            assert result == mock_response


class TestUsersTools:
    @pytest.mark.asyncio
    async def test_list_users(self):
        mock_response = {
            "value": [
                {"id": "user-1", "displayName": "User One", "mail": "user1@example.com"},
                {"id": "user-2", "displayName": "User Two", "mail": "user2@example.com"},
            ]
        }
        with patch("tools.users.make_graph_api_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await list_users()

            mock_request.assert_called_once_with("GET", "/users")
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_get_user(self):
        mock_response = {"id": "user-123", "displayName": "Test User", "mail": "test@example.com"}
        with patch("tools.users.make_graph_api_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await get_user("user-123")

            mock_request.assert_called_once_with("GET", "/users/user-123")
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_get_user_by_principal_name(self):
        mock_response = {"id": "user-123", "displayName": "Test User", "mail": "test@example.com"}
        with patch("tools.users.make_graph_api_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await get_user("test@example.com")

            mock_request.assert_called_once_with("GET", "/users/test@example.com")
            assert result == mock_response


class TestMeetingsTools:
    @pytest.mark.asyncio
    async def test_create_online_meeting(self):
        mock_response = {
            "id": "meeting-123",
            "subject": "Team Sync",
            "startDateTime": "2024-01-15T10:00:00Z",
            "endDateTime": "2024-01-15T11:00:00Z",
            "joinWebUrl": "https://teams.microsoft.com/l/meetup-join/...",
        }
        with patch("tools.meetings.make_graph_api_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await create_online_meeting(
                "user-123",
                "Team Sync",
                "2024-01-15T10:00:00Z",
                "2024-01-15T11:00:00Z",
            )

            mock_request.assert_called_once_with(
                "POST",
                "/users/user-123/onlineMeetings",
                json_data={
                    "subject": "Team Sync",
                    "startDateTime": "2024-01-15T10:00:00Z",
                    "endDateTime": "2024-01-15T11:00:00Z",
                },
            )
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_list_online_meetings(self):
        mock_response = {
            "value": [
                {"id": "meeting-1", "subject": "Meeting One"},
                {"id": "meeting-2", "subject": "Meeting Two"},
            ]
        }
        with patch("tools.meetings.make_graph_api_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await list_online_meetings("user-123")

            mock_request.assert_called_once_with("GET", "/users/user-123/onlineMeetings")
            assert result == mock_response
