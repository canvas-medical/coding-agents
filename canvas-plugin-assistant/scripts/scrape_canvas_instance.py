import re
import sys
from datetime import datetime
from html.parser import HTMLParser

import requests


class CSRFTokenParser(HTMLParser):
    """Parser to extract CSRF token from login page."""

    def __init__(self):
        super().__init__()
        self.csrf_token: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple]) -> None:
        if tag == 'input':
            attrs_dict = dict(attrs)
            if attrs_dict.get('name') == 'csrfmiddlewaretoken':
                self.csrf_token = attrs_dict.get('value')


class AdminTableParser(HTMLParser):
    """Parser to extract table data from Django admin pages."""

    def __init__(self):
        super().__init__()
        self.in_table = False
        self.in_thead = False
        self.in_tbody = False
        self.in_row = False
        self.in_cell = False
        self.in_link = False
        self.current_cell_classes: list[str] = []
        self.current_cell_text = ""
        self.current_row: dict[str, str] = {}
        self.rows: list[dict[str, str]] = []
        self.table_found = False

    def handle_starttag(self, tag: str, attrs: list[tuple]) -> None:
        attrs_dict = dict(attrs)
        classes = attrs_dict.get('class', '').split()

        if tag == 'table':
            if attrs_dict.get('id') == 'result_list':
                self.in_table = True
                self.table_found = True
        elif self.in_table:
            if tag == 'thead':
                self.in_thead = True
            elif tag == 'tbody':
                self.in_tbody = True
            elif tag == 'tr' and self.in_tbody:
                self.in_row = True
                self.current_row = {}
            elif tag in ('th', 'td') and self.in_row:
                if 'action-checkbox' not in classes and 'action-checkbox-column' not in classes:
                    self.in_cell = True
                    self.current_cell_classes = classes
                    self.current_cell_text = ""
            elif tag == 'a' and self.in_cell:
                self.in_link = True

    def handle_endtag(self, tag: str) -> None:
        if tag == 'table' and self.in_table:
            self.in_table = False
        elif tag == 'thead':
            self.in_thead = False
        elif tag == 'tbody':
            self.in_tbody = False
        elif tag == 'tr' and self.in_row:
            self.in_row = False
            if self.current_row:
                self.rows.append(self.current_row)
            self.current_row = {}
        elif tag in ('th', 'td') and self.in_cell:
            self.in_cell = False
            field_name = self._get_field_name()
            text = self.current_cell_text.strip()
            # Remove sorting arrows
            text = re.sub(r'[▲▼]', '', text).strip()
            if text:
                self.current_row[field_name] = text
            self.current_cell_classes = []
            self.current_cell_text = ""
        elif tag == 'a' and self.in_link:
            self.in_link = False

    def handle_data(self, data: str) -> None:
        if self.in_cell:
            self.current_cell_text += data

    def _get_field_name(self) -> str:
        """Extract field name from cell classes."""
        for cls in self.current_cell_classes:
            if cls.startswith('field-'):
                return cls.replace('field-', '').replace('_', ' ').title()
        return "Name"


class CanvasInstanceScraper:
    def __init__(self, instance_name: str, root_password: str):
        self.instance_name = instance_name
        self.base_url = f"https://{instance_name}.canvasmedical.com"
        self.admin_url = f"{self.base_url}/admin/"
        self.username = "root"
        self.password = root_password
        self.session = requests.Session()

    def login(self) -> bool:
        """Login to the Canvas admin portal."""
        print(f"Logging in to {self.admin_url}login/...")

        # Get the login page to retrieve CSRF token
        login_url = f"{self.admin_url}login/"
        response = self.session.get(login_url)
        if response.status_code != 200:
            print(f"Failed to access login page: {response.status_code}")
            return False

        # Parse CSRF token
        parser = CSRFTokenParser()
        parser.feed(response.text)
        csrf_token = parser.csrf_token

        if not csrf_token:
            print("Could not find CSRF token")
            return False

        # Prepare login data
        login_data = {
            'username': self.username,
            'password': self.password,
            'csrfmiddlewaretoken': csrf_token,
            'next': '/admin/'
        }

        # Submit login form
        response = self.session.post(
            login_url,
            data=login_data,
            headers={'Referer': login_url}
        )

        # Check if login was successful by trying to access admin page
        admin_response = self.session.get(self.admin_url)
        if 'Log out' in admin_response.text or admin_response.url == self.admin_url:
            print("Login successful!")
            return True
        else:
            print("Login failed!")
            return False

    def extract_table_data(self, url: str) -> list[dict[str, str]]:
        """Extract data from an admin page table."""
        print(f"Fetching {url}...")
        response = self.session.get(url)

        if response.status_code != 200:
            print(f"Failed to fetch {url}: {response.status_code}")
            return []

        parser = AdminTableParser()
        parser.feed(response.text)

        if not parser.table_found:
            print(f"No results table found at {url}")
            return []

        return parser.rows

    def get_roles(self) -> list[dict[str, str]]:
        """Extract care team roles."""
        return self.extract_table_data(f"{self.admin_url}api/careteamrole/?active__exact=1")

    def get_teams(self) -> list[dict[str, str]]:
        """Extract teams."""
        return self.extract_table_data(f"{self.admin_url}api/team/")

    def get_questionnaires(self) -> list[dict[str, str]]:
        """Extract active questionnaires from all use case categories."""
        urls = [
            f"{self.admin_url}api/questionnaire/?active__exact=AC&q=&use_case_in_charting__exact=QUES",
            f"{self.admin_url}api/questionnaire/?active__exact=AC&q=&use_case_in_charting__exact=ROS",
            f"{self.admin_url}api/questionnaire/?active__exact=AC&q=&use_case_in_charting__exact=EXAM",
            f"{self.admin_url}api/questionnaire/?active__exact=AC&q=&use_case_in_charting__exact=SA",
        ]
        all_questionnaires = []
        for url in urls:
            all_questionnaires.extend(self.extract_table_data(url))
        return all_questionnaires

    def get_note_types(self) -> list[dict[str, str]]:
        """Extract note types where is_active is true."""
        return self.extract_table_data(f"{self.admin_url}api/notetype/")

    def get_appointment_types(self) -> list[dict[str, str]]:
        """Extract appointment types (note types where is_active and is_schedulable are true)."""
        return self.extract_table_data(f"{self.admin_url}api/notetype/?is_active__exact=1&is_scheduleable__exact=1&q=")

    def get_installed_plugins(self) -> list[dict[str, str]]:
        """Extract installed plugins."""
        return self.extract_table_data(f"{self.admin_url}plugin_io/plugin/?is_enabled__exact=1")

    def generate_report(self) -> str:
        """Generate a comprehensive configuration report."""

        # Collect all data
        roles = self.get_roles()
        teams = self.get_teams()
        questionnaires = self.get_questionnaires()
        note_types = self.get_note_types()
        appointment_types = self.get_appointment_types()
        installed_plugins = self.get_installed_plugins()

        # Generate report
        report_lines = [
            "# Canvas Instance Configuration Report",
            "",
            f"**Instance**: {self.instance_name}.canvasmedical.com",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            "",
            "| Category | Count |",
            "|----------|-------|",
            f"| Roles | {len(roles)} |",
            f"| Teams | {len(teams)} |",
            f"| Questionnaires | {len(questionnaires)} |",
            f"| Note Types | {len(note_types)} |",
            f"| Appointment Types | {len(appointment_types)} |",
            f"| Installed Plugins | {len(installed_plugins)} |",
            "",
        ]

        # Roles section
        report_lines.extend([
            "## Roles",
            "",
        ])
        if roles:
            if roles[0]:
                headers = list(roles[0].keys())
                report_lines.append("| " + " | ".join(headers) + " |")
                report_lines.append("|" + "|".join([" --- " for _ in headers]) + "|")
                for role in roles:
                    report_lines.append("| " + " | ".join([role.get(header, "") for header in headers]) + " |")
        else:
            report_lines.append("No roles found.")
        report_lines.append("")

        # Teams section
        report_lines.extend([
            "## Teams",
            "",
        ])
        if teams:
            if teams[0]:
                headers = list(teams[0].keys())
                report_lines.append("| " + " | ".join(headers) + " |")
                report_lines.append("|" + "|".join([" --- " for _ in headers]) + "|")
                for team in teams:
                    report_lines.append("| " + " | ".join([team.get(header, "") for header in headers]) + " |")
        else:
            report_lines.append("No teams found.")
        report_lines.append("")

        # Questionnaires section
        report_lines.extend([
            "## Questionnaires",
            "",
        ])
        if questionnaires:
            if questionnaires[0]:
                headers = list(questionnaires[0].keys())
                report_lines.append("| " + " | ".join(headers) + " |")
                report_lines.append("|" + "|".join([" --- " for _ in headers]) + "|")
                for questionnaire in questionnaires:
                    report_lines.append("| " + " | ".join([questionnaire.get(header, "") for header in headers]) + " |")
        else:
            report_lines.append("No questionnaires found.")
        report_lines.append("")

        # Note Types section
        report_lines.extend([
            "## Note Types",
            "",
        ])
        if note_types:
            if note_types[0]:
                headers = list(note_types[0].keys())
                report_lines.append("| " + " | ".join(headers) + " |")
                report_lines.append("|" + "|".join([" --- " for _ in headers]) + "|")
                for note_type in note_types:
                    report_lines.append("| " + " | ".join([note_type.get(header, "") for header in headers]) + " |")
        else:
            report_lines.append("No note types found.")
        report_lines.append("")

        # Appointment Types section
        report_lines.extend([
            "## Appointment Types",
            "",
        ])
        if appointment_types:
            if appointment_types[0]:
                headers = list(appointment_types[0].keys())
                report_lines.append("| " + " | ".join(headers) + " |")
                report_lines.append("|" + "|".join([" --- " for _ in headers]) + "|")
                for appointment_type in appointment_types:
                    report_lines.append("| " + " | ".join([appointment_type.get(header, "") for header in headers]) + " |")
        else:
            report_lines.append("No appointment types found.")
        report_lines.append("")

        # Installed Plugins section
        report_lines.extend([
            "## Installed Plugins",
            "",
        ])
        if installed_plugins:
            if installed_plugins[0]:
                headers = list(installed_plugins[0].keys())
                report_lines.append("| " + " | ".join(headers) + " |")
                report_lines.append("|" + "|".join([" --- " for _ in headers]) + "|")
                for plugin in installed_plugins:
                    report_lines.append("| " + " | ".join([plugin.get(header, "") for header in headers]) + " |")
        else:
            report_lines.append("No installed plugins found.")
        report_lines.append("")

        # Recommendations section
        report_lines.extend([
            "## Plugin Development Recommendations",
            "",
            "Based on this configuration:",
            "",
        ])

        if teams:
            team_names = [team.get('Name', team.get('Team name', '')) for team in teams if team]
            report_lines.append(f"- **Available Teams for Task Assignment**: {', '.join(team_names) if team_names else 'None'}")

        if questionnaires:
            report_lines.append(f"- **Active Questionnaires**: {len(questionnaires)} questionnaires available")

        if installed_plugins:
            plugin_names = [plugin.get('Name', plugin.get('Package name', '')) for plugin in installed_plugins if plugin]
            report_lines.append(f"- **Existing Plugins**: {', '.join(plugin_names) if plugin_names else 'None'}")
        else:
            report_lines.append("- **Existing Plugins**: No plugins currently installed")

        report_lines.append("")

        return "\n".join(report_lines)

    @classmethod
    def main(cls, argv: list[str]) -> None:
        """Entry point for CLI execution."""
        if len(argv) < 3:
            print("Usage: python scrape_canvas_instance.py <instance_name> <root_password>")
            sys.exit(1)

        instance_name = argv[1]
        root_password = argv[2]

        scraper = cls(instance_name, root_password)

        if not scraper.login():
            print("Failed to login. Exiting.")
            sys.exit(1)

        report = scraper.generate_report()

        # Save report
        output_file = f"instance-config-{instance_name}.md"
        with open(output_file, 'w') as file:
            file.write(report)

        print(f"\nReport generated: {output_file}")
        print("\n" + "=" * 80)
        print(report)


if __name__ == "__main__":
    CanvasInstanceScraper.main(sys.argv)
