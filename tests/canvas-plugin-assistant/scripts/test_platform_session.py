"""Tests for platform_session module."""

import sys
from types import ModuleType
from unittest.mock import MagicMock, call, patch

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
    {"slug": "acme-staging", "managed": True, "capabilities": ["deploy_plugin"]},
    {"slug": "acme-prod", "managed": True, "capabilities": []},
    {"slug": "old", "managed": False, "capabilities": ["deploy_plugin"]},
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
            "Run `uv run --with 'canvas>=0.263.0' canvas login` in your terminal "
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

    def test_run__instances_prints_slugs(self, signed_in, capsys):
        """Prints one deployable slug per line for commands to consume."""
        tested = PlatformSession
        signed_in.instances.return_value = INSTANCES + [
            {"slug": "acme-qa", "managed": True, "capabilities": ["deploy_plugin"]},
        ]

        tested.run("instances")

        assert capsys.readouterr().out == "acme-staging\nacme-qa\n"
        assert signed_in.mock_calls == [call.instances()]

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

        assert mock_run.mock_calls == [call(show=show)]

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
