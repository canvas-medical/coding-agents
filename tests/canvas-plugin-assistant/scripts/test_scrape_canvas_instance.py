"""Tests for scrape_canvas_instance module."""

import sys
from html.parser import HTMLParser
from types import SimpleNamespace
from unittest.mock import MagicMock, call, mock_open, patch

import pytest

from scrape_canvas_instance import (
    AdminTableParser,
    CanvasInstanceScraper,
    CSRFTokenParser,
)


# =============================================================================
# CSRFTokenParser Tests
# =============================================================================


class TestCSRFTokenParser:
    """Tests for CSRFTokenParser class."""

    def test_inheritance(self):
        """Test CSRFTokenParser inherits from HTMLParser."""
        tested = CSRFTokenParser

        result = issubclass(tested, HTMLParser)

        expected = True
        assert result is expected

    def test___init__(self):
        """Test __init__ initializes csrf_token to None."""
        tested = CSRFTokenParser()

        result = tested.csrf_token

        expected = None
        assert result is expected

    def test_handle_starttag__finds_csrf_token(self):
        """Test handle_starttag extracts CSRF token from input field."""
        tested = CSRFTokenParser()
        attrs = [("name", "csrfmiddlewaretoken"), ("value", "abc123token")]

        tested.handle_starttag("input", attrs)

        result = tested.csrf_token
        expected = "abc123token"
        assert result == expected

    def test_handle_starttag__ignores_non_input_tags(self):
        """Test handle_starttag ignores non-input tags."""
        tested = CSRFTokenParser()
        attrs = [("name", "csrfmiddlewaretoken"), ("value", "abc123token")]

        tested.handle_starttag("div", attrs)

        result = tested.csrf_token
        expected = None
        assert result is expected

    def test_handle_starttag__ignores_inputs_without_csrf_name(self):
        """Test handle_starttag ignores inputs without csrfmiddlewaretoken name."""
        tested = CSRFTokenParser()
        attrs = [("name", "username"), ("value", "testuser")]

        tested.handle_starttag("input", attrs)

        result = tested.csrf_token
        expected = None
        assert result is expected


# =============================================================================
# AdminTableParser Tests
# =============================================================================


class TestAdminTableParser:
    """Tests for AdminTableParser class."""

    def test_inheritance(self):
        """Test AdminTableParser inherits from HTMLParser."""
        tested = AdminTableParser

        result = issubclass(tested, HTMLParser)

        expected = True
        assert result is expected

    def test___init__(self):
        """Test __init__ initializes all attributes correctly."""
        tested = AdminTableParser()

        assert tested.in_table is False
        assert tested.in_thead is False
        assert tested.in_tbody is False
        assert tested.in_row is False
        assert tested.in_cell is False
        assert tested.in_link is False
        assert tested.current_cell_classes == []
        assert tested.current_cell_text == ""
        assert tested.current_row == {}
        assert tested.rows == []
        assert tested.table_found is False

    def test_handle_starttag__sets_in_table_for_result_list(self):
        """Test handle_starttag sets in_table when id is result_list."""
        tested = AdminTableParser()
        attrs = [("id", "result_list")]

        tested.handle_starttag("table", attrs)

        assert tested.in_table is True
        assert tested.table_found is True

    def test_handle_starttag__ignores_table_without_result_list_id(self):
        """Test handle_starttag ignores tables without result_list id."""
        tested = AdminTableParser()
        attrs = [("id", "other_table")]

        tested.handle_starttag("table", attrs)

        result = tested.in_table
        expected = False
        assert result is expected

    def test_handle_starttag__sets_in_thead(self):
        """Test handle_starttag sets in_thead when inside table."""
        tested = AdminTableParser()
        tested.in_table = True

        tested.handle_starttag("thead", [])

        result = tested.in_thead
        expected = True
        assert result is expected

    def test_handle_starttag__sets_in_tbody(self):
        """Test handle_starttag sets in_tbody when inside table."""
        tested = AdminTableParser()
        tested.in_table = True

        tested.handle_starttag("tbody", [])

        result = tested.in_tbody
        expected = True
        assert result is expected

    def test_handle_starttag__sets_in_row_in_tbody(self):
        """Test handle_starttag sets in_row and resets current_row in tbody."""
        tested = AdminTableParser()
        tested.in_table = True
        tested.in_tbody = True
        tested.current_row = {"old": "data"}

        tested.handle_starttag("tr", [])

        assert tested.in_row is True
        assert tested.current_row == {}

    def test_handle_starttag__ignores_tr_outside_tbody(self):
        """Test handle_starttag ignores tr when not in tbody."""
        tested = AdminTableParser()
        tested.in_table = True
        tested.in_tbody = False

        tested.handle_starttag("tr", [])

        result = tested.in_row
        expected = False
        assert result is expected

    def test_handle_starttag__handles_th_cell(self):
        """Test handle_starttag handles th cell inside row."""
        tested = AdminTableParser()
        tested.in_table = True
        tested.in_row = True
        attrs = [("class", "field-name sortable")]

        tested.handle_starttag("th", attrs)

        assert tested.in_cell is True
        assert tested.current_cell_text == ""
        assert tested.current_cell_classes == ["field-name", "sortable"]

    def test_handle_starttag__handles_td_cell(self):
        """Test handle_starttag handles td cell inside row."""
        tested = AdminTableParser()
        tested.in_table = True
        tested.in_row = True
        attrs = [("class", "field-title")]

        tested.handle_starttag("td", attrs)

        assert tested.in_cell is True
        assert tested.current_cell_classes == ["field-title"]

    def test_handle_starttag__skips_action_checkbox_cell(self):
        """Test handle_starttag skips action-checkbox cells."""
        tested = AdminTableParser()
        tested.in_table = True
        tested.in_row = True
        attrs = [("class", "action-checkbox")]

        tested.handle_starttag("td", attrs)

        result = tested.in_cell
        expected = False
        assert result is expected

    def test_handle_starttag__skips_action_checkbox_column_cell(self):
        """Test handle_starttag skips action-checkbox-column cells."""
        tested = AdminTableParser()
        tested.in_table = True
        tested.in_row = True
        attrs = [("class", "action-checkbox-column")]

        tested.handle_starttag("td", attrs)

        result = tested.in_cell
        expected = False
        assert result is expected

    def test_handle_starttag__handles_anchor_in_cell(self):
        """Test handle_starttag sets in_link when anchor inside cell."""
        tested = AdminTableParser()
        tested.in_table = True
        tested.in_cell = True

        tested.handle_starttag("a", [("href", "/admin/item/1/")])

        result = tested.in_link
        expected = True
        assert result is expected

    def test_handle_starttag__ignores_anchor_outside_cell(self):
        """Test handle_starttag ignores anchor when not in cell."""
        tested = AdminTableParser()
        tested.in_table = True
        tested.in_cell = False

        tested.handle_starttag("a", [("href", "/admin/item/1/")])

        result = tested.in_link
        expected = False
        assert result is expected

    def test_handle_endtag__table(self):
        """Test handle_endtag resets in_table for table end tag."""
        tested = AdminTableParser()
        tested.in_table = True

        tested.handle_endtag("table")

        result = tested.in_table
        expected = False
        assert result is expected

    def test_handle_endtag__thead(self):
        """Test handle_endtag resets in_thead for thead end tag."""
        tested = AdminTableParser()
        tested.in_thead = True

        tested.handle_endtag("thead")

        result = tested.in_thead
        expected = False
        assert result is expected

    def test_handle_endtag__tbody(self):
        """Test handle_endtag resets in_tbody for tbody end tag."""
        tested = AdminTableParser()
        tested.in_tbody = True

        tested.handle_endtag("tbody")

        result = tested.in_tbody
        expected = False
        assert result is expected

    def test_handle_endtag__tr_appends_row(self):
        """Test handle_endtag appends current_row to rows when in row."""
        tested = AdminTableParser()
        tested.in_row = True
        tested.current_row = {"Name": "Test Role"}

        tested.handle_endtag("tr")

        assert tested.in_row is False
        assert tested.current_row == {}
        assert tested.rows == [{"Name": "Test Role"}]

    def test_handle_endtag__tr_skips_empty_row(self):
        """Test handle_endtag skips empty rows."""
        tested = AdminTableParser()
        tested.in_row = True
        tested.current_row = {}

        tested.handle_endtag("tr")

        assert tested.in_row is False
        assert tested.rows == []

    def test_handle_endtag__td_adds_field_to_row(self):
        """Test handle_endtag adds field to current_row."""
        tested = AdminTableParser()
        tested.in_cell = True
        tested.current_cell_classes = ["field-name"]
        tested.current_cell_text = "  Test Name  "

        tested.handle_endtag("td")

        assert tested.in_cell is False
        assert tested.current_row == {"Name": "Test Name"}
        assert tested.current_cell_classes == []
        assert tested.current_cell_text == ""

    def test_handle_endtag__td_removes_sorting_arrows(self):
        """Test handle_endtag removes sorting arrows from text."""
        tested = AdminTableParser()
        tested.in_cell = True
        tested.current_cell_classes = ["field-name"]
        tested.current_cell_text = "Test ▲ Name ▼"

        tested.handle_endtag("td")

        assert tested.current_row == {"Name": "Test  Name"}

    def test_handle_endtag__td_skips_empty_text(self):
        """Test handle_endtag skips adding to row when text is empty."""
        tested = AdminTableParser()
        tested.in_cell = True
        tested.current_cell_classes = ["field-name"]
        tested.current_cell_text = "   "

        tested.handle_endtag("td")

        assert tested.current_row == {}

    def test_handle_endtag__th_processes_like_td(self):
        """Test handle_endtag processes th like td."""
        tested = AdminTableParser()
        tested.in_cell = True
        tested.current_cell_classes = ["field-title"]
        tested.current_cell_text = "Header Text"

        tested.handle_endtag("th")

        assert tested.in_cell is False
        assert tested.current_row == {"Title": "Header Text"}

    def test_handle_endtag__anchor(self):
        """Test handle_endtag resets in_link for anchor end tag."""
        tested = AdminTableParser()
        tested.in_link = True

        tested.handle_endtag("a")

        result = tested.in_link
        expected = False
        assert result is expected

    def test_handle_data__captures_text_in_cell(self):
        """Test handle_data captures text when in cell."""
        tested = AdminTableParser()
        tested.in_cell = True
        tested.current_cell_text = "Hello "

        tested.handle_data("World")

        result = tested.current_cell_text
        expected = "Hello World"
        assert result == expected

    def test_handle_data__ignores_text_outside_cell(self):
        """Test handle_data ignores text when not in cell."""
        tested = AdminTableParser()
        tested.in_cell = False
        tested.current_cell_text = ""

        tested.handle_data("Ignored text")

        result = tested.current_cell_text
        expected = ""
        assert result == expected

    def test__get_field_name__extracts_from_field_class(self):
        """Test _get_field_name extracts field name from field-* class."""
        tested = AdminTableParser()
        tested.current_cell_classes = ["sortable", "field-role_name", "column"]

        result = tested._get_field_name()

        expected = "Role Name"
        assert result == expected

    def test__get_field_name__returns_name_when_no_field_class(self):
        """Test _get_field_name returns 'Name' when no field-* class found."""
        tested = AdminTableParser()
        tested.current_cell_classes = ["sortable", "column"]

        result = tested._get_field_name()

        expected = "Name"
        assert result == expected

    def test__get_field_name__returns_name_for_empty_classes(self):
        """Test _get_field_name returns 'Name' for empty cell_classes."""
        tested = AdminTableParser()
        tested.current_cell_classes = []

        result = tested._get_field_name()

        expected = "Name"
        assert result == expected


# =============================================================================
# CanvasInstanceScraper Tests
# =============================================================================


class TestCanvasInstanceScraper:
    """Tests for CanvasInstanceScraper class."""

    @patch("scrape_canvas_instance.requests.Session")
    def test___init__(self, mock_session_class):
        """Test __init__ initializes all attributes correctly."""
        mock_session = MagicMock()
        mock_session_class.side_effect = [mock_session]

        tested = CanvasInstanceScraper("demo", "secret123")

        assert tested.instance_name == "demo"
        assert tested.base_url == "https://demo.canvasmedical.com"
        assert tested.admin_url == "https://demo.canvasmedical.com/admin/"
        assert tested.username == "root"
        assert tested.password == "secret123"
        assert tested.session == mock_session

        exp_calls = [call()]
        assert mock_session_class.mock_calls == exp_calls

    @patch("scrape_canvas_instance.requests.Session")
    def test_login__success(self, mock_session_class, capsys):
        """Test login returns True on successful login."""
        mock_session = MagicMock()
        mock_session_class.side_effect = [mock_session]

        get_response_login = SimpleNamespace(
            status_code=200,
            text='<input name="csrfmiddlewaretoken" value="token123">',
        )
        post_response = SimpleNamespace(status_code=200)
        get_response_admin = SimpleNamespace(
            status_code=200,
            text="Welcome! Log out",
            url="https://demo.canvasmedical.com/admin/",
        )
        mock_session.get.side_effect = [get_response_login, get_response_admin]
        mock_session.post.side_effect = [post_response]

        tested = CanvasInstanceScraper("demo", "secret123")

        result = tested.login()

        expected = True
        assert result is expected

        captured = capsys.readouterr()
        assert "Logging in to https://demo.canvasmedical.com/admin/login/..." in captured.out
        assert "Login successful!" in captured.out

        exp_session_calls = [
            call.get("https://demo.canvasmedical.com/admin/login/"),
            call.post(
                "https://demo.canvasmedical.com/admin/login/",
                data={
                    "username": "root",
                    "password": "secret123",
                    "csrfmiddlewaretoken": "token123",
                    "next": "/admin/",
                },
                headers={"Referer": "https://demo.canvasmedical.com/admin/login/"},
            ),
            call.get("https://demo.canvasmedical.com/admin/"),
        ]
        assert mock_session.mock_calls == exp_session_calls

    @patch("scrape_canvas_instance.requests.Session")
    def test_login__success_via_url_match(self, mock_session_class, capsys):
        """Test login returns True when admin URL matches."""
        mock_session = MagicMock()
        mock_session_class.side_effect = [mock_session]

        get_response_login = SimpleNamespace(
            status_code=200,
            text='<input name="csrfmiddlewaretoken" value="token123">',
        )
        post_response = SimpleNamespace(status_code=200)
        get_response_admin = SimpleNamespace(
            status_code=200,
            text="No logout text here",
            url="https://demo.canvasmedical.com/admin/",
        )
        mock_session.get.side_effect = [get_response_login, get_response_admin]
        mock_session.post.side_effect = [post_response]

        tested = CanvasInstanceScraper("demo", "secret123")

        result = tested.login()

        expected = True
        assert result is expected

        captured = capsys.readouterr()
        assert "Logging in to https://demo.canvasmedical.com/admin/login/..." in captured.out
        assert "Login successful!" in captured.out

        exp_session_calls = [
            call.get("https://demo.canvasmedical.com/admin/login/"),
            call.post(
                "https://demo.canvasmedical.com/admin/login/",
                data={
                    "username": "root",
                    "password": "secret123",
                    "csrfmiddlewaretoken": "token123",
                    "next": "/admin/",
                },
                headers={"Referer": "https://demo.canvasmedical.com/admin/login/"},
            ),
            call.get("https://demo.canvasmedical.com/admin/"),
        ]
        assert mock_session.mock_calls == exp_session_calls

    @patch("scrape_canvas_instance.requests.Session")
    def test_login__fails_on_get_status_not_200(self, mock_session_class, capsys):
        """Test login returns False when GET login page fails."""
        mock_session = MagicMock()
        mock_session_class.side_effect = [mock_session]

        get_response = SimpleNamespace(status_code=500, text="")
        mock_session.get.side_effect = [get_response]

        tested = CanvasInstanceScraper("demo", "secret123")

        result = tested.login()

        expected = False
        assert result is expected

        captured = capsys.readouterr()
        assert "Failed to access login page: 500" in captured.out

        exp_session_calls = [
            call.get("https://demo.canvasmedical.com/admin/login/"),
        ]
        assert mock_session.mock_calls == exp_session_calls

    @patch("scrape_canvas_instance.requests.Session")
    def test_login__fails_when_no_csrf_token(self, mock_session_class, capsys):
        """Test login returns False when no CSRF token found."""
        mock_session = MagicMock()
        mock_session_class.side_effect = [mock_session]

        get_response = SimpleNamespace(
            status_code=200,
            text="<html><body>No token here</body></html>",
        )
        mock_session.get.side_effect = [get_response]

        tested = CanvasInstanceScraper("demo", "secret123")

        result = tested.login()

        expected = False
        assert result is expected

        captured = capsys.readouterr()
        assert "Could not find CSRF token" in captured.out

        exp_session_calls = [
            call.get("https://demo.canvasmedical.com/admin/login/"),
        ]
        assert mock_session.mock_calls == exp_session_calls

    @patch("scrape_canvas_instance.requests.Session")
    def test_login__fails_when_login_unsuccessful(self, mock_session_class, capsys):
        """Test login returns False when login POST fails."""
        mock_session = MagicMock()
        mock_session_class.side_effect = [mock_session]

        get_response_login = SimpleNamespace(
            status_code=200,
            text='<input name="csrfmiddlewaretoken" value="token123">',
        )
        post_response = SimpleNamespace(status_code=200)
        get_response_admin = SimpleNamespace(
            status_code=200,
            text="Invalid credentials",
            url="https://demo.canvasmedical.com/admin/login/?next=/admin/",
        )
        mock_session.get.side_effect = [get_response_login, get_response_admin]
        mock_session.post.side_effect = [post_response]

        tested = CanvasInstanceScraper("demo", "wrongpass")

        result = tested.login()

        expected = False
        assert result is expected

        captured = capsys.readouterr()
        assert "Login failed!" in captured.out

        exp_session_calls = [
            call.get("https://demo.canvasmedical.com/admin/login/"),
            call.post(
                "https://demo.canvasmedical.com/admin/login/",
                data={
                    "username": "root",
                    "password": "wrongpass",
                    "csrfmiddlewaretoken": "token123",
                    "next": "/admin/",
                },
                headers={"Referer": "https://demo.canvasmedical.com/admin/login/"},
            ),
            call.get("https://demo.canvasmedical.com/admin/"),
        ]
        assert mock_session.mock_calls == exp_session_calls

    @patch("scrape_canvas_instance.requests.Session")
    def test_extract_table_data__success(self, mock_session_class, capsys):
        """Test extract_table_data returns parsed data on success."""
        mock_session = MagicMock()
        mock_session_class.side_effect = [mock_session]

        html_content = """
        <table id="result_list">
            <thead><tr><th class="field-name">Name</th></tr></thead>
            <tbody>
                <tr><td class="field-name">Role One</td></tr>
                <tr><td class="field-name">Role Two</td></tr>
            </tbody>
        </table>
        """
        get_response = SimpleNamespace(status_code=200, text=html_content)
        mock_session.get.side_effect = [get_response]

        tested = CanvasInstanceScraper("demo", "secret123")
        url = "https://demo.canvasmedical.com/admin/test/?all="

        result = tested.extract_table_data(url)

        expected = [{"Name": "Role One"}, {"Name": "Role Two"}]
        assert result == expected

        captured = capsys.readouterr()
        assert "Fetching https://demo.canvasmedical.com/admin/test/?all=..." in captured.out

        exp_session_calls = [call.get(url)]
        assert mock_session.mock_calls == exp_session_calls

    @patch("scrape_canvas_instance.requests.Session")
    def test_extract_table_data__status_not_200(self, mock_session_class, capsys):
        """Test extract_table_data returns empty list on non-200 status."""
        mock_session = MagicMock()
        mock_session_class.side_effect = [mock_session]

        get_response = SimpleNamespace(status_code=404, text="")
        mock_session.get.side_effect = [get_response]

        tested = CanvasInstanceScraper("demo", "secret123")
        url = "https://demo.canvasmedical.com/admin/test/?all="

        result = tested.extract_table_data(url)

        expected = []
        assert result == expected

        captured = capsys.readouterr()
        assert "Failed to fetch https://demo.canvasmedical.com/admin/test/?all=: 404" in captured.out

        exp_session_calls = [call.get(url)]
        assert mock_session.mock_calls == exp_session_calls

    @patch("scrape_canvas_instance.requests.Session")
    def test_extract_table_data__no_table_found(self, mock_session_class, capsys):
        """Test extract_table_data returns empty list when no table found."""
        mock_session = MagicMock()
        mock_session_class.side_effect = [mock_session]

        html_content = "<html><body><p>No table here</p></body></html>"
        get_response = SimpleNamespace(status_code=200, text=html_content)
        mock_session.get.side_effect = [get_response]

        tested = CanvasInstanceScraper("demo", "secret123")
        url = "https://demo.canvasmedical.com/admin/test/?all="

        result = tested.extract_table_data(url)

        expected = []
        assert result == expected

        captured = capsys.readouterr()
        assert "No results table found at https://demo.canvasmedical.com/admin/test/?all=" in captured.out

        exp_session_calls = [call.get(url)]
        assert mock_session.mock_calls == exp_session_calls

    @patch("scrape_canvas_instance.requests.Session")
    @patch.object(CanvasInstanceScraper, "extract_table_data")
    def test_get_roles(self, mock_extract, mock_session_class):
        """Test get_roles calls extract_table_data with correct URL."""
        mock_extract.side_effect = [[{"Name": "Admin"}]]

        tested = CanvasInstanceScraper("demo", "secret123")

        result = tested.get_roles()

        expected = [{"Name": "Admin"}]
        assert result == expected

        exp_session_class_calls = [call()]
        assert mock_session_class.mock_calls == exp_session_class_calls

        exp_extract_calls = [
            call("https://demo.canvasmedical.com/admin/api/careteamrole/?active__exact=1")
        ]
        assert mock_extract.mock_calls == exp_extract_calls

    @patch("scrape_canvas_instance.requests.Session")
    @patch.object(CanvasInstanceScraper, "extract_table_data")
    def test_get_teams(self, mock_extract, mock_session_class):
        """Test get_teams calls extract_table_data with correct URL."""
        mock_extract.side_effect = [[{"Name": "Team Alpha"}]]

        tested = CanvasInstanceScraper("demo", "secret123")

        result = tested.get_teams()

        expected = [{"Name": "Team Alpha"}]
        assert result == expected

        exp_session_class_calls = [call()]
        assert mock_session_class.mock_calls == exp_session_class_calls

        exp_extract_calls = [
            call("https://demo.canvasmedical.com/admin/api/team/")
        ]
        assert mock_extract.mock_calls == exp_extract_calls

    @patch("scrape_canvas_instance.requests.Session")
    @patch.object(CanvasInstanceScraper, "extract_table_data")
    def test_get_questionnaires(self, mock_extract, mock_session_class):
        """Test get_questionnaires loops through 4 URLs and combines results."""
        mock_extract.side_effect = [
            [{"Name": "Q1"}],
            [{"Name": "Q2"}],
            [],
            [{"Name": "Q3"}],
        ]

        tested = CanvasInstanceScraper("demo", "secret123")

        result = tested.get_questionnaires()

        expected = [{"Name": "Q1"}, {"Name": "Q2"}, {"Name": "Q3"}]
        assert result == expected

        exp_session_class_calls = [call()]
        assert mock_session_class.mock_calls == exp_session_class_calls

        exp_extract_calls = [
            call("https://demo.canvasmedical.com/admin/api/questionnaire/?active__exact=AC&q=&use_case_in_charting__exact=QUES"),
            call("https://demo.canvasmedical.com/admin/api/questionnaire/?active__exact=AC&q=&use_case_in_charting__exact=ROS"),
            call("https://demo.canvasmedical.com/admin/api/questionnaire/?active__exact=AC&q=&use_case_in_charting__exact=EXAM"),
            call("https://demo.canvasmedical.com/admin/api/questionnaire/?active__exact=AC&q=&use_case_in_charting__exact=SA"),
        ]
        assert mock_extract.mock_calls == exp_extract_calls

    @patch("scrape_canvas_instance.requests.Session")
    @patch.object(CanvasInstanceScraper, "extract_table_data")
    def test_get_note_types(self, mock_extract, mock_session_class):
        """Test get_note_types calls extract_table_data with correct URL."""
        mock_extract.side_effect = [[{"Name": "Progress Note"}]]

        tested = CanvasInstanceScraper("demo", "secret123")

        result = tested.get_note_types()

        expected = [{"Name": "Progress Note"}]
        assert result == expected

        exp_session_class_calls = [call()]
        assert mock_session_class.mock_calls == exp_session_class_calls

        exp_extract_calls = [
            call("https://demo.canvasmedical.com/admin/api/notetype/")
        ]
        assert mock_extract.mock_calls == exp_extract_calls

    @patch("scrape_canvas_instance.requests.Session")
    @patch.object(CanvasInstanceScraper, "extract_table_data")
    def test_get_appointment_types(self, mock_extract, mock_session_class):
        """Test get_appointment_types calls extract_table_data with correct URL."""
        mock_extract.side_effect = [[{"Name": "Office Visit"}]]

        tested = CanvasInstanceScraper("demo", "secret123")

        result = tested.get_appointment_types()

        expected = [{"Name": "Office Visit"}]
        assert result == expected

        exp_session_class_calls = [call()]
        assert mock_session_class.mock_calls == exp_session_class_calls

        exp_extract_calls = [
            call("https://demo.canvasmedical.com/admin/api/notetype/?is_active__exact=1&is_scheduleable__exact=1&q=")
        ]
        assert mock_extract.mock_calls == exp_extract_calls

    @patch("scrape_canvas_instance.requests.Session")
    @patch.object(CanvasInstanceScraper, "extract_table_data")
    def test_get_installed_plugins(self, mock_extract, mock_session_class):
        """Test get_installed_plugins calls extract_table_data with correct URL."""
        mock_extract.side_effect = [[{"Name": "My Plugin"}]]

        tested = CanvasInstanceScraper("demo", "secret123")

        result = tested.get_installed_plugins()

        expected = [{"Name": "My Plugin"}]
        assert result == expected

        exp_session_class_calls = [call()]
        assert mock_session_class.mock_calls == exp_session_class_calls

        exp_extract_calls = [
            call("https://demo.canvasmedical.com/admin/plugin_io/plugin/?is_enabled__exact=1")
        ]
        assert mock_extract.mock_calls == exp_extract_calls

    @patch("scrape_canvas_instance.requests.Session")
    @patch("scrape_canvas_instance.datetime")
    @patch.object(CanvasInstanceScraper, "get_roles")
    @patch.object(CanvasInstanceScraper, "get_teams")
    @patch.object(CanvasInstanceScraper, "get_questionnaires")
    @patch.object(CanvasInstanceScraper, "get_note_types")
    @patch.object(CanvasInstanceScraper, "get_appointment_types")
    @patch.object(CanvasInstanceScraper, "get_installed_plugins")
    def test_generate_report__with_data(
        self,
        mock_plugins,
        mock_apt_types,
        mock_note_types,
        mock_questionnaires,
        mock_teams,
        mock_roles,
        mock_datetime,
        mock_session_class,
    ):
        """Test generate_report with data in all sections."""
        mock_datetime.now.side_effect = [
            SimpleNamespace(strftime=lambda fmt: "2024-01-15 10:30:00")
        ]

        mock_roles.side_effect = [[{"Name": "Admin"}, {"Name": "Nurse"}]]
        mock_teams.side_effect = [[{"Name": "Team A"}]]
        mock_questionnaires.side_effect = [[{"Name": "PHQ-9"}]]
        mock_note_types.side_effect = [[{"Name": "Progress Note"}]]
        mock_apt_types.side_effect = [[{"Name": "Office Visit"}]]
        mock_plugins.side_effect = [[{"Name": "Plugin1"}]]

        tested = CanvasInstanceScraper("demo", "secret123")

        result = tested.generate_report()

        assert "# Canvas Instance Configuration Report" in result
        assert "**Instance**: demo.canvasmedical.com" in result
        assert "**Generated**: 2024-01-15 10:30:00" in result
        assert "## Roles" in result
        assert "| Name |" in result
        assert "| Admin |" in result
        assert "| Nurse |" in result
        assert "## Teams" in result
        assert "| Team A |" in result
        assert "## Questionnaires" in result
        assert "| PHQ-9 |" in result
        assert "## Note Types" in result
        assert "| Progress Note |" in result
        assert "## Appointment Types" in result
        assert "| Office Visit |" in result
        assert "## Installed Plugins" in result
        assert "| Plugin1 |" in result
        assert "## Plugin Development Recommendations" in result
        assert "- **Available Teams for Task Assignment**: Team A" in result
        assert "- **Active Questionnaires**: 1 questionnaires available" in result
        assert "- **Existing Plugins**: Plugin1" in result

        exp_calls = [call()]
        assert mock_roles.mock_calls == exp_calls
        assert mock_teams.mock_calls == exp_calls
        assert mock_questionnaires.mock_calls == exp_calls
        assert mock_note_types.mock_calls == exp_calls
        assert mock_apt_types.mock_calls == exp_calls
        assert mock_plugins.mock_calls == exp_calls
        assert mock_session_class.mock_calls == exp_calls

        exp_datetime_calls = [call.now()]
        assert mock_datetime.mock_calls == exp_datetime_calls

    @patch("scrape_canvas_instance.requests.Session")
    @patch("scrape_canvas_instance.datetime")
    @patch.object(CanvasInstanceScraper, "get_roles")
    @patch.object(CanvasInstanceScraper, "get_teams")
    @patch.object(CanvasInstanceScraper, "get_questionnaires")
    @patch.object(CanvasInstanceScraper, "get_note_types")
    @patch.object(CanvasInstanceScraper, "get_appointment_types")
    @patch.object(CanvasInstanceScraper, "get_installed_plugins")
    def test_generate_report__empty_data(
        self,
        mock_plugins,
        mock_apt_types,
        mock_note_types,
        mock_questionnaires,
        mock_teams,
        mock_roles,
        mock_datetime,
        mock_session_class,
    ):
        """Test generate_report with empty data in all sections."""
        mock_datetime.now.side_effect = [
            SimpleNamespace(strftime=lambda fmt: "2024-01-15 10:30:00")
        ]

        mock_roles.side_effect = [[]]
        mock_teams.side_effect = [[]]
        mock_questionnaires.side_effect = [[]]
        mock_note_types.side_effect = [[]]
        mock_apt_types.side_effect = [[]]
        mock_plugins.side_effect = [[]]

        tested = CanvasInstanceScraper("demo", "secret123")

        result = tested.generate_report()

        assert "# Canvas Instance Configuration Report" in result
        assert "No roles found." in result
        assert "No teams found." in result
        assert "No questionnaires found." in result
        assert "No note types found." in result
        assert "No appointment types found." in result
        assert "No installed plugins found." in result
        assert "- **Existing Plugins**: No plugins currently installed" in result

        exp_calls = [call()]
        assert mock_roles.mock_calls == exp_calls
        assert mock_teams.mock_calls == exp_calls
        assert mock_questionnaires.mock_calls == exp_calls
        assert mock_note_types.mock_calls == exp_calls
        assert mock_apt_types.mock_calls == exp_calls
        assert mock_plugins.mock_calls == exp_calls
        assert mock_session_class.mock_calls == exp_calls

        exp_datetime_calls = [call.now()]
        assert mock_datetime.mock_calls == exp_datetime_calls

    @patch("scrape_canvas_instance.requests.Session")
    @patch("scrape_canvas_instance.datetime")
    @patch.object(CanvasInstanceScraper, "get_roles")
    @patch.object(CanvasInstanceScraper, "get_teams")
    @patch.object(CanvasInstanceScraper, "get_questionnaires")
    @patch.object(CanvasInstanceScraper, "get_note_types")
    @patch.object(CanvasInstanceScraper, "get_appointment_types")
    @patch.object(CanvasInstanceScraper, "get_installed_plugins")
    def test_generate_report__empty_dict_in_list(
        self,
        mock_plugins,
        mock_apt_types,
        mock_note_types,
        mock_questionnaires,
        mock_teams,
        mock_roles,
        mock_datetime,
        mock_session_class,
    ):
        """Test generate_report with empty dict in list (roles[0] is empty)."""
        mock_datetime.now.side_effect = [
            SimpleNamespace(strftime=lambda fmt: "2024-01-15 10:30:00")
        ]

        mock_roles.side_effect = [[{}]]
        mock_teams.side_effect = [[{}]]
        mock_questionnaires.side_effect = [[{}]]
        mock_note_types.side_effect = [[{}]]
        mock_apt_types.side_effect = [[{}]]
        mock_plugins.side_effect = [[{}]]

        tested = CanvasInstanceScraper("demo", "secret123")

        result = tested.generate_report()

        # When roles[0] is empty dict, it's falsy so no table is generated
        assert "## Roles" in result
        assert "## Teams" in result
        # Empty dicts in teams filter out to empty string join
        assert "- **Available Teams for Task Assignment**:" in result

        exp_calls = [call()]
        assert mock_roles.mock_calls == exp_calls
        assert mock_teams.mock_calls == exp_calls
        assert mock_questionnaires.mock_calls == exp_calls
        assert mock_note_types.mock_calls == exp_calls
        assert mock_apt_types.mock_calls == exp_calls
        assert mock_plugins.mock_calls == exp_calls
        assert mock_session_class.mock_calls == exp_calls

        exp_datetime_calls = [call.now()]
        assert mock_datetime.mock_calls == exp_datetime_calls

    @patch("scrape_canvas_instance.requests.Session")
    @patch("scrape_canvas_instance.datetime")
    @patch.object(CanvasInstanceScraper, "get_roles")
    @patch.object(CanvasInstanceScraper, "get_teams")
    @patch.object(CanvasInstanceScraper, "get_questionnaires")
    @patch.object(CanvasInstanceScraper, "get_note_types")
    @patch.object(CanvasInstanceScraper, "get_appointment_types")
    @patch.object(CanvasInstanceScraper, "get_installed_plugins")
    def test_generate_report__team_name_fallback(
        self,
        mock_plugins,
        mock_apt_types,
        mock_note_types,
        mock_questionnaires,
        mock_teams,
        mock_roles,
        mock_datetime,
        mock_session_class,
    ):
        """Test generate_report uses Team name fallback key for teams."""
        mock_datetime.now.side_effect = [
            SimpleNamespace(strftime=lambda fmt: "2024-01-15 10:30:00")
        ]

        mock_roles.side_effect = [[]]
        mock_teams.side_effect = [[{"Team name": "Alpha Team"}]]
        mock_questionnaires.side_effect = [[]]
        mock_note_types.side_effect = [[]]
        mock_apt_types.side_effect = [[]]
        mock_plugins.side_effect = [[]]

        tested = CanvasInstanceScraper("demo", "secret123")

        result = tested.generate_report()

        assert "- **Available Teams for Task Assignment**: Alpha Team" in result

        exp_calls = [call()]
        assert mock_roles.mock_calls == exp_calls
        assert mock_teams.mock_calls == exp_calls
        assert mock_questionnaires.mock_calls == exp_calls
        assert mock_note_types.mock_calls == exp_calls
        assert mock_apt_types.mock_calls == exp_calls
        assert mock_plugins.mock_calls == exp_calls
        assert mock_session_class.mock_calls == exp_calls

        exp_datetime_calls = [call.now()]
        assert mock_datetime.mock_calls == exp_datetime_calls

    @patch("scrape_canvas_instance.requests.Session")
    @patch("scrape_canvas_instance.datetime")
    @patch.object(CanvasInstanceScraper, "get_roles")
    @patch.object(CanvasInstanceScraper, "get_teams")
    @patch.object(CanvasInstanceScraper, "get_questionnaires")
    @patch.object(CanvasInstanceScraper, "get_note_types")
    @patch.object(CanvasInstanceScraper, "get_appointment_types")
    @patch.object(CanvasInstanceScraper, "get_installed_plugins")
    def test_generate_report__plugin_package_name_fallback(
        self,
        mock_plugins,
        mock_apt_types,
        mock_note_types,
        mock_questionnaires,
        mock_teams,
        mock_roles,
        mock_datetime,
        mock_session_class,
    ):
        """Test generate_report uses Package name fallback key for plugins."""
        mock_datetime.now.side_effect = [
            SimpleNamespace(strftime=lambda fmt: "2024-01-15 10:30:00")
        ]

        mock_roles.side_effect = [[]]
        mock_teams.side_effect = [[]]
        mock_questionnaires.side_effect = [[]]
        mock_note_types.side_effect = [[]]
        mock_apt_types.side_effect = [[]]
        mock_plugins.side_effect = [[{"Package name": "my-plugin-pkg"}]]

        tested = CanvasInstanceScraper("demo", "secret123")

        result = tested.generate_report()

        assert "- **Existing Plugins**: my-plugin-pkg" in result

        exp_calls = [call()]
        assert mock_roles.mock_calls == exp_calls
        assert mock_teams.mock_calls == exp_calls
        assert mock_questionnaires.mock_calls == exp_calls
        assert mock_note_types.mock_calls == exp_calls
        assert mock_apt_types.mock_calls == exp_calls
        assert mock_plugins.mock_calls == exp_calls
        assert mock_session_class.mock_calls == exp_calls

        exp_datetime_calls = [call.now()]
        assert mock_datetime.mock_calls == exp_datetime_calls

    def test_main__insufficient_arguments(self, capsys):
        """Test main exits with code 1 when insufficient arguments provided."""
        tested = CanvasInstanceScraper

        with pytest.raises(SystemExit) as exc_info:
            tested.main(["script_name"])

        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        expected = "Usage: python scrape_canvas_instance.py <instance_name> <root_password>\n"
        assert captured.out == expected

    def test_main__insufficient_arguments_one_arg(self, capsys):
        """Test main exits with code 1 when only one argument provided."""
        tested = CanvasInstanceScraper

        with pytest.raises(SystemExit) as exc_info:
            tested.main(["script_name", "instance_only"])

        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        expected = "Usage: python scrape_canvas_instance.py <instance_name> <root_password>\n"
        assert captured.out == expected

    @patch("scrape_canvas_instance.requests.Session")
    @patch.object(CanvasInstanceScraper, "login")
    def test_main__login_fails(self, mock_login, mock_session_class, capsys):
        """Test main exits with code 1 when login fails."""
        mock_login.side_effect = [False]

        tested = CanvasInstanceScraper

        with pytest.raises(SystemExit) as exc_info:
            tested.main(["script_name", "demo", "secret123"])

        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Failed to login. Exiting.\n" in captured.out

        exp_calls = [call()]
        assert mock_login.mock_calls == exp_calls
        assert mock_session_class.mock_calls == exp_calls

    @patch("scrape_canvas_instance.requests.Session")
    @patch.object(CanvasInstanceScraper, "login")
    @patch.object(CanvasInstanceScraper, "generate_report")
    @patch("builtins.open", new_callable=mock_open)
    def test_main__success(
        self, mock_file_open, mock_generate_report, mock_login, mock_session_class, capsys
    ):
        """Test main generates report, writes file, and prints output on success."""
        mock_login.side_effect = [True]
        mock_generate_report.side_effect = ["# Report Content"]

        tested = CanvasInstanceScraper

        tested.main(["script_name", "demo", "secret123"])

        captured = capsys.readouterr()
        assert "\nReport generated: instance-config-demo.md" in captured.out
        assert "=" * 80 in captured.out
        assert "# Report Content" in captured.out

        exp_calls = [call()]
        assert mock_login.mock_calls == exp_calls
        assert mock_generate_report.mock_calls == exp_calls
        assert mock_session_class.mock_calls == exp_calls

        exp_file_open_calls = [
            call("instance-config-demo.md", "w"),
            call().__enter__(),
            call().write("# Report Content"),
            call().__exit__(None, None, None),
        ]
        assert mock_file_open.mock_calls == exp_file_open_calls
