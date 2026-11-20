"""Tests for platform_session module."""

import json
import sys
from types import ModuleType
from unittest.mock import MagicMock, call, patch
from urllib.parse import quote

import pytest


class PlatformError(Exception):
    """Stand-in for canvas_cli.apps.platform.client.PlatformError."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class PlatformAuthError(Exception):
    """Stand-in for canvas_cli.apps.platform.auth.PlatformAuthError."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def _build_stubs() -> dict[str, ModuleType]:
    """Build stand-ins for the canvas CLI modules, which are only installed at runtime via `uv run --with`."""
    canvas_cli = ModuleType("canvas_cli")
    apps = ModuleType("canvas_cli.apps")
    platform = ModuleType("canvas_cli.apps.platform")
    auth = ModuleType("canvas_cli.apps.platform.auth")
    client = ModuleType("canvas_cli.apps.platform.client")
    auth.PlatformAuthError = PlatformAuthError  # type: ignore[attr-defined]
    auth.resolve_platform_url = MagicMock()  # type: ignore[attr-defined]
    auth.stored_tokens = MagicMock()  # type: ignore[attr-defined]
    client.PlatformError = PlatformError  # type: ignore[attr-defined]
    client.PlatformClient = MagicMock()  # type: ignore[attr-defined]
    client.segment = lambda value: quote(value, safe="")  # type: ignore[attr-defined]
    platform.auth = auth  # type: ignore[attr-defined]
    platform.client = client  # type: ignore[attr-defined]
    apps.platform = platform  # type: ignore[attr-defined]
    canvas_cli.apps = apps  # type: ignore[attr-defined]
    return {
        "canvas_cli": canvas_cli,
        "canvas_cli.apps": apps,
        "canvas_cli.apps.platform": platform,
        "canvas_cli.apps.platform.auth": auth,
        "canvas_cli.apps.platform.client": client,
    }


# The stubs are only in sys.modules while the module under test is imported, so they do not leak into other test modules.
with patch.dict(sys.modules, _build_stubs()):
    import platform_session
    from platform_session import PlatformSession

PLATFORM = "https://platform.canvasmedical.com"
ME = {
    "email": "dana@acme.example",
    "organizations": [
        {
            "name": "Acme",
            "slug": "acme",
            "plugin_prefix": "acme",
            "capabilities": ["push_plugin_code"],
        },
        {"name": "Beta", "slug": "beta", "plugin_prefix": "beta", "capabilities": []},
    ],
}
INSTANCES = [
    {
        "slug": "acme-staging",
        "managed": True,
        "capabilities": ["deploy_plugin", "read_plugin_logs"],
        "test_instance": True,
        "production": False,
    },
    {
        "slug": "acme-prod",
        "managed": True,
        "capabilities": [],
        "test_instance": False,
        "production": True,
    },
    {
        "slug": "old",
        "managed": False,
        "capabilities": ["deploy_plugin"],
        "test_instance": False,
        "production": False,
    },
]


@pytest.fixture
def signed_in():
    """Patch the CLI modules in platform_session as signed in; yield the client instance mock."""
    with (
        patch.object(platform_session, "auth") as auth,
        patch.object(platform_session, "PlatformClient") as client_class,
    ):
        auth.resolve_platform_url.return_value = PLATFORM
        auth.stored_tokens.return_value = {"access_token": "t"}
        client = client_class.return_value
        client.me.return_value = ME
        client.instances.return_value = INSTANCES
        yield client


class TestRun:
    """Tests for PlatformSession.run method."""

    def test_run__signed_out_exits_with_login_instruction(self, capsys):
        """Refuses when signed out because deploying needs a Platform session the agent cannot create itself."""
        tested = PlatformSession

        with (
            patch.object(platform_session, "auth") as auth,
            patch.object(platform_session, "PlatformClient") as client_class,
        ):
            auth.resolve_platform_url.return_value = PLATFORM
            auth.stored_tokens.return_value = None
            with pytest.raises(SystemExit) as exc_info:
                tested.run("whoami")

        assert exc_info.value.code == 1
        expected = (
            f"ERROR: Not signed in to Canvas Platform at {PLATFORM}. "
            "Run `uv run --with 'canvas>=1.2.0' canvas login` in your terminal "
            "(it opens a browser), then try again.\n"
        )
        assert capsys.readouterr().out == expected
        assert auth.mock_calls == [
            call.resolve_platform_url(),
            call.stored_tokens(PLATFORM),
        ]
        assert client_class.mock_calls == []

    def test_run__whoami_lists_publishing_orgs_and_instances(self, signed_in, capsys):
        """Lists only orgs that can push plugin code and instances that accept deploys."""
        tested = PlatformSession

        tested.run("whoami")

        expected = (
            f"Signed in to {PLATFORM} as dana@acme.example\n"
            "  Acme (acme): plugin prefix acme__\n"
            "Instances you can deploy to: acme-staging\n"
        )
        assert capsys.readouterr().out == expected

    def test_run__whoami_no_publishing_org(self, signed_in, capsys):
        """Signed in with no publishing org still exits 0, with guidance and no deployable instances."""
        tested = PlatformSession
        signed_in.me.return_value = {
            "email": "dana@acme.example",
            "organizations": [{"name": "Beta", "slug": "beta"}],
        }
        signed_in.instances.return_value = []

        tested.run("whoami")

        expected = (
            f"Signed in to {PLATFORM} as dana@acme.example\n"
            "  No organization lets you push plugin code. Ask an organization admin for the Plugin developer role.\n"
            "Instances you can deploy to: none\n"
        )
        assert capsys.readouterr().out == expected

    def test_run__instances_prints_slug_test_instance_and_production(self, signed_in, capsys):
        """Prints one line per deployable instance so commands offer branch deploys only to test instances."""
        tested = PlatformSession
        signed_in.instances.return_value = INSTANCES + [
            {
                "slug": "acme-live",
                "managed": True,
                "capabilities": ["deploy_plugin"],
                "test_instance": False,
                "production": True,
            },
        ]

        tested.run("instances")

        expected = (
            "acme-staging test_instance=true production=false logs=true\n"
            "acme-live test_instance=false production=true logs=false\n"
        )
        assert capsys.readouterr().out == expected
        assert signed_in.mock_calls == [call.instances()]

    def test_run__instances_without_capabilities_key_is_not_listed(self, signed_in, capsys):
        """A row that omits `capabilities` cannot carry deploy_plugin, so it is never listed as logs=false."""
        tested = PlatformSession
        signed_in.instances.return_value = [
            {
                "slug": "acme-staging",
                "managed": True,
                "capabilities": ["deploy_plugin"],
                "test_instance": True,
                "production": False,
            },
            {
                "slug": "acme-other",
                "managed": True,
                "capabilities": ["deploy_plugin"],
                "test_instance": True,
                "production": False,
            },
        ]
        del signed_in.instances.return_value[1]["capabilities"]

        tested.run("instances")

        assert capsys.readouterr().out == "acme-staging test_instance=true production=false logs=false\n"

    def test_run__instances_without_test_instance_key_exits(self, signed_in, capsys):
        """Refuses when Platform omits `test_instance`: guessing false or true would hide or offer every instance for branch deploys."""
        tested = PlatformSession
        signed_in.instances.return_value = [
            {"slug": "acme-staging", "managed": True, "capabilities": ["deploy_plugin"]},
        ]

        with pytest.raises(SystemExit) as exc_info:
            tested.run("instances")

        assert exc_info.value.code == 1
        expected = "ERROR: Canvas Platform does not report test instances; update Canvas Platform.\n"
        assert capsys.readouterr().out == expected

    def test_run__instances_without_production_key_exits(self, signed_in, capsys):
        """Refuses when Platform omits `production`: a production gate must not fail open, since a guessed false skips the production confirmation."""
        tested = PlatformSession
        signed_in.instances.return_value = [
            {
                "slug": "acme-live",
                "managed": True,
                "capabilities": ["deploy_plugin"],
                "test_instance": False,
            },
        ]

        with pytest.raises(SystemExit) as exc_info:
            tested.run("instances")

        assert exc_info.value.code == 1
        expected = "ERROR: Canvas Platform does not report which instances are production; update Canvas Platform.\n"
        assert capsys.readouterr().out == expected

    def test_run__instances_staged_production_is_production(self, signed_in, capsys):
        """An instance Canvas Platform stages Production is production even before Console flags it.

        Platform's own rule (`InstanceAssignment.unsafe`) counts the stage beside Console's flag, so the
        release step's production confirmation has to as well.
        """
        tested = PlatformSession
        signed_in.instances.return_value = [
            {
                "slug": "acme-live",
                "stage": "production",
                "managed": True,
                "capabilities": ["deploy_plugin"],
                "test_instance": False,
                "production": False,
            },
        ]

        tested.run("instances")

        assert capsys.readouterr().out == "acme-live test_instance=false production=true logs=false\n"

    def test_run__instances_none_exits(self, signed_in, capsys):
        """Refuses with no deployable instance because a deploy would have nowhere to go."""
        tested = PlatformSession
        signed_in.instances.return_value = [INSTANCES[1], INSTANCES[2]]

        with pytest.raises(SystemExit) as exc_info:
            tested.run("instances")

        assert exc_info.value.code == 1
        expected = "ERROR: There is no instance Canvas Platform manages that you can deploy plugins to.\n"
        assert capsys.readouterr().out == expected

    def test_run__publishers_prints_slug_and_prefix(self, signed_in, capsys):
        """Prints one line per organization that can push plugin code, as `<slug> <prefix>__`, for commands to consume."""
        tested = PlatformSession

        tested.run("publishers")

        assert capsys.readouterr().out == "acme acme__\n"
        assert signed_in.mock_calls == [call.me()]

    def test_run__publishers_none_exits(self, signed_in, capsys):
        """Refuses with no publishing organization because creating a plugin needs a prefix to name its package."""
        tested = PlatformSession
        signed_in.me.return_value = {
            "email": "dana@acme.example",
            "organizations": [ME["organizations"][1]],
        }

        with pytest.raises(SystemExit) as exc_info:
            tested.run("publishers")

        assert exc_info.value.code == 1
        expected = "ERROR: No organization lets you push plugin code. Ask an organization admin for the Plugin developer role.\n"
        assert capsys.readouterr().out == expected

    def test_run__records_prints_the_platform_body(self, signed_in, capsys):
        """Prints Platform's records body unchanged so the skill reads each row's fields and collected_at."""
        tested = PlatformSession
        body = {
            "instance": "acme-staging",
            "model": "Team",
            "collected_at": "2026-11-18T09:30:00Z",
            "records": [
                {
                    "key": "7",
                    "label": "Nursing",
                    "fields": {"members": ["Dana Lee"], "responsibilities": ["Triage"]},
                    "collected_at": "2026-11-18T09:30:00Z",
                },
            ],
        }
        signed_in.get.return_value = body

        tested.run("records", slug="acme-staging", model="Team")

        assert json.loads(capsys.readouterr().out) == body
        assert signed_in.mock_calls == [
            call.get("/api/v1/instances/acme-staging/records?model=Team")
        ]

    def test_run__records_keeps_a_null_collected_at(self, signed_in, capsys):
        """A model Canvas Platform has not read yet stays null, which the report words as not read yet."""
        tested = PlatformSession
        body = {
            "instance": "acme-staging",
            "model": "Questionnaire",
            "collected_at": None,
            "records": [],
        }
        signed_in.get.return_value = body

        tested.run("records", slug="acme-staging", model="Questionnaire")

        assert json.loads(capsys.readouterr().out)["collected_at"] is None

    def test_run__records_quotes_the_slug(self, signed_in, capsys):
        """A slug is one path segment, as the Canvas CLI's own client sends it."""
        tested = PlatformSession
        signed_in.get.return_value = {}

        tested.run("records", slug="a/b", model="NoteType")

        assert signed_in.mock_calls == [
            call.get("/api/v1/instances/a%2Fb/records?model=NoteType")
        ]

    def test_run__records_not_found_exits_with_platform_message(self, signed_in, capsys):
        """A 404 for an instance the person cannot reach surfaces Platform's sentence."""
        tested = PlatformSession
        signed_in.get.side_effect = PlatformError("Instance not found.")

        with pytest.raises(SystemExit) as exc_info:
            tested.run("records", slug="nope", model="Team")

        assert exc_info.value.code == 1
        assert capsys.readouterr().out == "ERROR: Instance not found.\n"

    def test_run__plugins_prints_the_installed_plugins_body(self, signed_in, capsys):
        """Prints the instance's plugin inventory as Platform returns it."""
        tested = PlatformSession
        body = {
            "instance": "acme-staging",
            "collected_at": None,
            "plugins": [{"name": "acme__intake", "version": "1.2.0", "enabled": True}],
        }
        signed_in.installed_plugins.return_value = body

        tested.run("plugins", slug="acme-staging")

        assert json.loads(capsys.readouterr().out) == body
        assert signed_in.mock_calls == [call.installed_plugins("acme-staging")]

    def test_run__plugins_not_found_exits_with_platform_message(self, signed_in, capsys):
        """A 404 for an instance the person cannot reach surfaces Platform's sentence."""
        tested = PlatformSession
        signed_in.installed_plugins.side_effect = PlatformError("Instance not found.")

        with pytest.raises(SystemExit) as exc_info:
            tested.run("plugins", slug="nope")

        assert exc_info.value.code == 1
        assert capsys.readouterr().out == "ERROR: Instance not found.\n"

    def test_run__platform_error_exits_with_message(self, signed_in, capsys):
        """Network failures surface the CLI's own message."""
        tested = PlatformSession
        signed_in.me.side_effect = PlatformError(
            f"Could not reach Canvas Platform at {PLATFORM}"
        )

        with pytest.raises(SystemExit) as exc_info:
            tested.run("whoami")

        assert exc_info.value.code == 1
        assert (
            capsys.readouterr().out
            == f"ERROR: Could not reach Canvas Platform at {PLATFORM}\n"
        )

    def test_run__auth_error_exits_with_message(self, signed_in, capsys):
        """An expired session surfaces the CLI's own message."""
        tested = PlatformSession
        signed_in.instances.side_effect = PlatformAuthError(
            "Session expired. Run `canvas login`."
        )

        with pytest.raises(SystemExit) as exc_info:
            tested.run("instances")

        assert exc_info.value.code == 1
        assert (
            capsys.readouterr().out == "ERROR: Session expired. Run `canvas login`.\n"
        )


class TestMain:
    """Tests for PlatformSession.main method."""

    @pytest.mark.parametrize("show", ["whoami", "instances", "publishers"])
    def test_main__parses_show(self, show, monkeypatch):
        """Passes the positional argument to run."""
        tested = PlatformSession
        monkeypatch.setattr("sys.argv", ["platform_session.py", show])

        with patch.object(tested, "run") as mock_run:
            tested.main()

        assert mock_run.mock_calls == [call(show=show, slug=None, model=None)]

    def test_main__parses_records_slug_and_model(self, monkeypatch):
        """Passes the instance slug and model to run."""
        tested = PlatformSession
        monkeypatch.setattr(
            "sys.argv", ["platform_session.py", "records", "acme-staging", "CareTeamRole"]
        )

        with patch.object(tested, "run") as mock_run:
            tested.main()

        assert mock_run.mock_calls == [
            call(show="records", slug="acme-staging", model="CareTeamRole")
        ]

    def test_main__parses_plugins_slug(self, monkeypatch):
        """Passes the instance slug to run."""
        tested = PlatformSession
        monkeypatch.setattr("sys.argv", ["platform_session.py", "plugins", "acme-staging"])

        with patch.object(tested, "run") as mock_run:
            tested.main()

        assert mock_run.mock_calls == [call(show="plugins", slug="acme-staging", model=None)]

    def test_main__rejects_unknown_model(self, monkeypatch):
        """Rejects a model outside the four Platform serves."""
        tested = PlatformSession
        monkeypatch.setattr(
            "sys.argv", ["platform_session.py", "records", "acme-staging", "Patient"]
        )

        with pytest.raises(SystemExit) as exc_info:
            tested.main()

        assert exc_info.value.code == 2

    @pytest.mark.parametrize(
        "argv",
        [["records"], ["records", "acme-staging"], ["plugins"]],
    )
    def test_main__rejects_missing_slug_or_model(self, argv, monkeypatch):
        """records needs a slug and a model, and plugins needs a slug."""
        tested = PlatformSession
        monkeypatch.setattr("sys.argv", ["platform_session.py", *argv])

        with pytest.raises(SystemExit) as exc_info:
            tested.main()

        assert exc_info.value.code == 2

    def test_main__rejects_unknown_show(self, monkeypatch):
        """Rejects values outside the choices."""
        tested = PlatformSession
        monkeypatch.setattr("sys.argv", ["platform_session.py", "logout"])

        with pytest.raises(SystemExit) as exc_info:
            tested.main()

        assert exc_info.value.code == 2


CORRUPT_CREDENTIALS = (
    "/Users/dana/.canvas/platform-credentials.json is not valid JSON "
    "(Expecting value: line 1 column 1 (char 0)). Move it aside and run `canvas login`."
)


class TestRunScenarios:
    """Cross-step scenarios for PlatformSession.run against the CLI's real failure and permission shapes."""

    @pytest.mark.parametrize("raising", ["resolve_platform_url", "stored_tokens"])
    def test_run__corrupt_credentials_file_exits_with_message(self, raising, capsys):
        """The CLI raises PlatformAuthError while reading a corrupt credentials file; show its fix, not a traceback."""
        tested = PlatformSession

        with (
            patch.object(platform_session, "auth") as auth,
            patch.object(platform_session, "PlatformClient") as client_class,
        ):
            auth.resolve_platform_url.return_value = PLATFORM
            getattr(auth, raising).side_effect = PlatformAuthError(CORRUPT_CREDENTIALS)
            with pytest.raises(SystemExit) as exc_info:
                tested.run("whoami")

        assert exc_info.value.code == 1
        assert capsys.readouterr().out == f"ERROR: {CORRUPT_CREDENTIALS}\n"
        assert client_class.mock_calls == []

    def test_run__publisher_without_deploy_rights(self, signed_in, capsys):
        """A Plugin developer can publish but not deploy: whoami still passes the sign-in check, instances refuses."""
        tested = PlatformSession
        signed_in.me.return_value = {
            "email": "github-actions@acme.example",
            "organizations": [
                {
                    "name": "Acme",
                    "slug": "acme",
                    "plugin_prefix": "acme",
                    "capabilities": ["push_plugin_code", "view_org_assets"],
                },
            ],
        }
        signed_in.instances.return_value = [
            {
                "slug": "acme-staging",
                "managed": True,
                "capabilities": ["configure_plugin"],
            },
        ]

        tested.run("whoami")

        expected = (
            f"Signed in to {PLATFORM} as github-actions@acme.example\n"
            "  Acme (acme): plugin prefix acme__\n"
            "Instances you can deploy to: none\n"
        )
        assert capsys.readouterr().out == expected

        with pytest.raises(SystemExit) as exc_info:
            tested.run("instances")

        assert exc_info.value.code == 1
        expected = "ERROR: There is no instance Canvas Platform manages that you can deploy plugins to.\n"
        assert capsys.readouterr().out == expected
