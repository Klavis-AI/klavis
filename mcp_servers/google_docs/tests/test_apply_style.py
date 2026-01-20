"""Unit tests for google_docs_apply_style tool."""

import pytest
from unittest.mock import patch, MagicMock


class TestApplyStyleInput:
    """Tests for input parameter validation."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_document_id_is_required(self):
        """Test that document_id parameter is required."""
        from server import apply_style

        with pytest.raises(TypeError):
            await apply_style()

    @pytest.mark.asyncio(loop_scope="function")
    async def test_start_and_end_index_are_required(self):
        """Test that start_index and end_index are required."""
        from server import apply_style

        with pytest.raises(TypeError):
            await apply_style("doc123")

        with pytest.raises(TypeError):
            await apply_style("doc123", 1)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_returns_error_when_no_styles_specified(self):
        """Test that error is returned when no style parameters are provided."""
        from server import apply_style, auth_token_context

        token = auth_token_context.set("test_token")
        try:
            result = await apply_style("doc123", 1, 10)

            assert result["success"] is False
            assert "No styles specified" in result["error"]
        finally:
            auth_token_context.reset(token)


class TestApplyStyleTextStyles:
    """Tests for text style API calls."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_bold_style_request_structure(self):
        """Test that bold style generates correct API request."""
        from server import apply_style, auth_token_context

        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service):
                await apply_style("doc123", 1, 10, bold=True)

                call_args = mock_service.documents.return_value.batchUpdate.call_args
                requests = call_args.kwargs["body"]["requests"]

                assert len(requests) == 1
                update_style = requests[0]["updateTextStyle"]
                assert update_style["range"]["startIndex"] == 1
                assert update_style["range"]["endIndex"] == 10
                assert update_style["textStyle"]["bold"] is True
                assert "bold" in update_style["fields"]
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_italic_style_request_structure(self):
        """Test that italic style generates correct API request."""
        from server import apply_style, auth_token_context

        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service):
                await apply_style("doc123", 5, 15, italic=True)

                call_args = mock_service.documents.return_value.batchUpdate.call_args
                requests = call_args.kwargs["body"]["requests"]
                update_style = requests[0]["updateTextStyle"]

                assert update_style["textStyle"]["italic"] is True
                assert "italic" in update_style["fields"]
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_multiple_text_styles_combined(self):
        """Test that multiple text styles are combined in single request."""
        from server import apply_style, auth_token_context

        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service):
                await apply_style(
                    "doc123", 1, 10,
                    bold=True,
                    italic=True,
                    underline=True
                )

                call_args = mock_service.documents.return_value.batchUpdate.call_args
                requests = call_args.kwargs["body"]["requests"]

                # Should be single updateTextStyle request with all styles
                assert len(requests) == 1
                update_style = requests[0]["updateTextStyle"]
                assert update_style["textStyle"]["bold"] is True
                assert update_style["textStyle"]["italic"] is True
                assert update_style["textStyle"]["underline"] is True
                assert "bold" in update_style["fields"]
                assert "italic" in update_style["fields"]
                assert "underline" in update_style["fields"]
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_font_size_request_structure(self):
        """Test that font_size generates correct API request."""
        from server import apply_style, auth_token_context

        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service):
                await apply_style("doc123", 1, 10, font_size=14)

                call_args = mock_service.documents.return_value.batchUpdate.call_args
                requests = call_args.kwargs["body"]["requests"]
                update_style = requests[0]["updateTextStyle"]

                assert update_style["textStyle"]["fontSize"]["magnitude"] == 14
                assert update_style["textStyle"]["fontSize"]["unit"] == "PT"
                assert "fontSize" in update_style["fields"]
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_font_family_request_structure(self):
        """Test that font_family generates correct API request."""
        from server import apply_style, auth_token_context

        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service):
                await apply_style("doc123", 1, 10, font_family="Arial")

                call_args = mock_service.documents.return_value.batchUpdate.call_args
                requests = call_args.kwargs["body"]["requests"]
                update_style = requests[0]["updateTextStyle"]

                assert update_style["textStyle"]["weightedFontFamily"]["fontFamily"] == "Arial"
                assert "weightedFontFamily" in update_style["fields"]
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_foreground_color_request_structure(self):
        """Test that foreground_color generates correct API request with RGB conversion."""
        from server import apply_style, auth_token_context

        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service):
                await apply_style("doc123", 1, 10, foreground_color="#FF0000")

                call_args = mock_service.documents.return_value.batchUpdate.call_args
                requests = call_args.kwargs["body"]["requests"]
                update_style = requests[0]["updateTextStyle"]
                rgb = update_style["textStyle"]["foregroundColor"]["color"]["rgbColor"]

                # #FF0000 = red (1.0, 0.0, 0.0)
                assert rgb["red"] == 1.0
                assert rgb["green"] == 0.0
                assert rgb["blue"] == 0.0
                assert "foregroundColor" in update_style["fields"]
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_background_color_request_structure(self):
        """Test that background_color generates correct API request."""
        from server import apply_style, auth_token_context

        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service):
                await apply_style("doc123", 1, 10, background_color="#00FF00")

                call_args = mock_service.documents.return_value.batchUpdate.call_args
                requests = call_args.kwargs["body"]["requests"]
                update_style = requests[0]["updateTextStyle"]
                rgb = update_style["textStyle"]["backgroundColor"]["color"]["rgbColor"]

                # #00FF00 = green (0.0, 1.0, 0.0)
                assert rgb["red"] == 0.0
                assert rgb["green"] == 1.0
                assert rgb["blue"] == 0.0
                assert "backgroundColor" in update_style["fields"]
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_link_url_request_structure(self):
        """Test that link_url generates correct API request."""
        from server import apply_style, auth_token_context

        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service):
                await apply_style("doc123", 1, 10, link_url="https://example.com")

                call_args = mock_service.documents.return_value.batchUpdate.call_args
                requests = call_args.kwargs["body"]["requests"]
                update_style = requests[0]["updateTextStyle"]

                assert update_style["textStyle"]["link"]["url"] == "https://example.com"
                assert "link" in update_style["fields"]
        finally:
            auth_token_context.reset(token)


class TestApplyStyleParagraphStyles:
    """Tests for paragraph style API calls."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_heading_type_request_structure(self):
        """Test that heading_type generates correct API request."""
        from server import apply_style, auth_token_context

        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service):
                await apply_style("doc123", 1, 20, heading_type="HEADING_1")

                call_args = mock_service.documents.return_value.batchUpdate.call_args
                requests = call_args.kwargs["body"]["requests"]

                # Should have updateParagraphStyle request
                para_style_request = None
                for req in requests:
                    if "updateParagraphStyle" in req:
                        para_style_request = req["updateParagraphStyle"]
                        break

                assert para_style_request is not None
                assert para_style_request["paragraphStyle"]["namedStyleType"] == "HEADING_1"
                assert "namedStyleType" in para_style_request["fields"]
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_alignment_request_structure(self):
        """Test that alignment generates correct API request."""
        from server import apply_style, auth_token_context

        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service):
                await apply_style("doc123", 1, 20, alignment="CENTER")

                call_args = mock_service.documents.return_value.batchUpdate.call_args
                requests = call_args.kwargs["body"]["requests"]

                para_style_request = None
                for req in requests:
                    if "updateParagraphStyle" in req:
                        para_style_request = req["updateParagraphStyle"]
                        break

                assert para_style_request is not None
                assert para_style_request["paragraphStyle"]["alignment"] == "CENTER"
                assert "alignment" in para_style_request["fields"]
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_line_spacing_request_structure(self):
        """Test that line_spacing generates correct API request."""
        from server import apply_style, auth_token_context

        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service):
                await apply_style("doc123", 1, 20, line_spacing=150)

                call_args = mock_service.documents.return_value.batchUpdate.call_args
                requests = call_args.kwargs["body"]["requests"]

                para_style_request = None
                for req in requests:
                    if "updateParagraphStyle" in req:
                        para_style_request = req["updateParagraphStyle"]
                        break

                assert para_style_request is not None
                assert para_style_request["paragraphStyle"]["lineSpacing"] == 150
                assert "lineSpacing" in para_style_request["fields"]
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_space_above_and_below_request_structure(self):
        """Test that space_above and space_below generate correct API requests."""
        from server import apply_style, auth_token_context

        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service):
                await apply_style("doc123", 1, 20, space_above=12, space_below=6)

                call_args = mock_service.documents.return_value.batchUpdate.call_args
                requests = call_args.kwargs["body"]["requests"]

                para_style_request = None
                for req in requests:
                    if "updateParagraphStyle" in req:
                        para_style_request = req["updateParagraphStyle"]
                        break

                assert para_style_request is not None
                assert para_style_request["paragraphStyle"]["spaceAbove"]["magnitude"] == 12
                assert para_style_request["paragraphStyle"]["spaceAbove"]["unit"] == "PT"
                assert para_style_request["paragraphStyle"]["spaceBelow"]["magnitude"] == 6
                assert para_style_request["paragraphStyle"]["spaceBelow"]["unit"] == "PT"
        finally:
            auth_token_context.reset(token)


class TestApplyStyleMixedStyles:
    """Tests for mixed text and paragraph styles."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_text_and_paragraph_styles_generate_separate_requests(self):
        """Test that text and paragraph styles generate separate API requests."""
        from server import apply_style, auth_token_context

        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service):
                await apply_style(
                    "doc123", 1, 20,
                    bold=True,
                    heading_type="HEADING_1"
                )

                call_args = mock_service.documents.return_value.batchUpdate.call_args
                requests = call_args.kwargs["body"]["requests"]

                # Should have both updateTextStyle and updateParagraphStyle
                has_text_style = any("updateTextStyle" in req for req in requests)
                has_para_style = any("updateParagraphStyle" in req for req in requests)

                assert has_text_style
                assert has_para_style
        finally:
            auth_token_context.reset(token)


class TestApplyStyleResponse:
    """Tests for response handling."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_success_response_structure(self):
        """Test that success response has correct structure."""
        from server import apply_style, auth_token_context

        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service):
                result = await apply_style("doc123", 1, 10, bold=True)

                assert result["success"] is True
                assert result["document_id"] == "doc123"
                assert result["styled_range"]["start_index"] == 1
                assert result["styled_range"]["end_index"] == 10
                assert "bold" in result["applied_styles"]
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_applied_styles_list_is_accurate(self):
        """Test that applied_styles list accurately reflects applied styles."""
        from server import apply_style, auth_token_context

        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service):
                result = await apply_style(
                    "doc123", 1, 10,
                    bold=True,
                    italic=False,  # Explicitly set to False
                    font_size=14
                )

                # Should include all specified styles
                assert any("bold" in s for s in result["applied_styles"])
                assert any("no-italic" in s for s in result["applied_styles"])
                assert any("fontSize:14" in s for s in result["applied_styles"])
        finally:
            auth_token_context.reset(token)


class TestApplyStyleErrors:
    """Tests for error handling."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_raises_on_api_error(self):
        """Test that API errors are properly raised."""
        from server import apply_style, auth_token_context
        from googleapiclient.errors import HttpError

        mock_service = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status = 400
        mock_service.documents.return_value.batchUpdate.return_value.execute.side_effect = HttpError(
            mock_resp,
            b'{"error": {"message": "Invalid range"}}'
        )

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service):
                with pytest.raises(RuntimeError, match="Google Docs API Error"):
                    await apply_style("doc123", 1, 10, bold=True)
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_raises_on_invalid_hex_color(self):
        """Test that invalid hex color raises ValueError."""
        from server import apply_style, auth_token_context

        token = auth_token_context.set("test_token")
        try:
            with pytest.raises(ValueError, match="Invalid hex color"):
                await apply_style("doc123", 1, 10, foreground_color="invalid")
        finally:
            auth_token_context.reset(token)
