"""
Reports the Canvas Platform sign-in, the organizations that can publish plugins, and the deployable instances.

Usage:
    uv run --with 'canvas>=1.2.0' python platform_session.py whoami
    uv run --with 'canvas>=1.2.0' python platform_session.py instances
    uv run --with 'canvas>=1.2.0' python platform_session.py publishers
    uv run --with 'canvas>=1.2.0' python platform_session.py records <slug> <CareTeamRole|NoteType|Questionnaire|Team>
    uv run --with 'canvas>=1.2.0' python platform_session.py plugins <slug>
"""

import argparse
import json
import sys
from typing import Any

from canvas_cli.apps.platform import auth
from canvas_cli.apps.platform.auth import PlatformAuthError
from canvas_cli.apps.platform.client import PlatformClient, PlatformError, segment

RECORD_MODELS: list[str] = ["CareTeamRole", "NoteType", "Questionnaire", "Team"]


class PlatformSession:
    """Reads the person's Canvas Platform session through the Canvas CLI's own sign-in and API client."""

    @classmethod
    def run(cls, show: str, slug: str | None = None, model: str | None = None) -> None:
        """
        Print the requested view of the Platform session, or exit 1 when it cannot be shown.

        Args:
            show (str): "whoami" for the sign-in summary, "instances" for deployable instance slugs with their test_instance, production, and logs flags, "publishers" for publishing organization slugs and prefixes, "records" for one model's setup records on an instance as JSON, "plugins" for an instance's installed plugins as JSON.
            slug (str | None): The instance slug, for "records" and "plugins".
            model (str | None): One of RECORD_MODELS, for "records".
        """
        try:
            platform: str = auth.resolve_platform_url()
            if auth.stored_tokens(platform) is None:
                cls.exit_with_error(
                    f"Not signed in to Canvas Platform at {platform}. "
                    "Run `uv run --with 'canvas>=1.2.0' canvas login` in your terminal "
                    "(it opens a browser), then try again."
                )

            client = PlatformClient(platform)
            if show == "whoami":
                cls.print_whoami(
                    platform,
                    client.me(),
                    [
                        instance["slug"]
                        for instance in cls.deployable_instances(client.instances())
                    ],
                )
            elif show == "publishers":
                cls.print_publishers(cls.publishing_orgs(client.me()))
            elif show == "records":
                print(
                    json.dumps(
                        client.get(
                            f"/api/v1/instances/{segment(str(slug))}/records?model={model}"
                        ),
                        indent=2,
                    )
                )
            elif show == "plugins":
                print(json.dumps(client.installed_plugins(str(slug)), indent=2))
            else:
                cls.print_instances(cls.deployable_instances(client.instances()))
        except (PlatformAuthError, PlatformError) as error:
            cls.exit_with_error(error.message)

    @classmethod
    def publishing_orgs(cls, me: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Organizations the person can push plugin code for, as the Canvas CLI decides it.

        Args:
            me (dict): The `/api/v1/me` payload.

        Returns:
            list[dict]: Organizations with the push_plugin_code capability and a plugin prefix.
        """
        return [
            org
            for org in me.get("organizations", [])
            if "push_plugin_code" in org.get("capabilities", [])
            and org.get("plugin_prefix")
        ]

    @classmethod
    def deployable_instances(cls, instances: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        The instances the person can deploy plugins to, as the Canvas CLI decides it.

        Args:
            instances (list[dict]): The `/api/v1/instances` payload.

        Returns:
            list[dict]: Rows of managed instances with the deploy_plugin capability.
        """
        return [
            instance
            for instance in instances
            if instance.get("managed")
            and "deploy_plugin" in instance.get("capabilities", [])
        ]

    @classmethod
    def print_whoami(cls, platform: str, me: dict[str, Any], slugs: list[str]) -> None:
        """
        Print the sign-in summary: email, publishing organizations, and deployable instances.

        Args:
            platform (str): The Platform URL.
            me (dict): The `/api/v1/me` payload.
            slugs (list[str]): Deployable instance slugs.
        """
        print(f"Signed in to {platform} as {me['email']}")
        orgs = cls.publishing_orgs(me)
        for org in orgs:
            print(
                f"  {org['name']} ({org['slug']}): plugin prefix {org['plugin_prefix']}__"
            )
        if not orgs:
            print(
                "  No organization lets you push plugin code. Ask an organization admin for the Plugin developer role."
            )
        print(f"Instances you can deploy to: {', '.join(slugs) or 'none'}")

    @classmethod
    def print_publishers(cls, orgs: list[dict[str, Any]]) -> None:
        """
        Print one `<slug> <plugin_prefix>__` line per publishing organization, or exit 1 when there are none.

        Args:
            orgs (list[dict]): Organizations the person can push plugin code for.
        """
        if not orgs:
            cls.exit_with_error(
                "No organization lets you push plugin code. Ask an organization admin for the Plugin developer role."
            )
        print("\n".join(f"{org['slug']} {org['plugin_prefix']}__" for org in orgs))

    @classmethod
    def print_instances(cls, instances: list[dict[str, Any]]) -> None:
        """
        Print one `<slug> test_instance=<true|false> production=<true|false> logs=<true|false>` line per deployable instance.

        `production` is true when the row's `production` flag is set or its `stage` is "production",
        because Canvas Platform's own unsafe-instance rule counts both.

        `logs` is true when the row's capabilities include `read_plugin_logs`. Deployable rows always
        carry `capabilities`, since `deployable_instances` selects on `deploy_plugin` in it.

        Exits 1 when there are none, or when a row lacks `test_instance` or `production` (a Canvas
        Platform that does not report it), since guessing would offer or hide every instance for
        branch deploys, or skip the production confirmation.

        Args:
            instances (list[dict]): Deployable instance rows.
        """
        if not instances:
            cls.exit_with_error(
                "There is no instance Canvas Platform manages that you can deploy plugins to."
            )
        if any("test_instance" not in instance for instance in instances):
            cls.exit_with_error(
                "Canvas Platform does not report test instances; update Canvas Platform."
            )
        if any("production" not in instance for instance in instances):
            cls.exit_with_error(
                "Canvas Platform does not report which instances are production; update Canvas Platform."
            )
        print(
            "\n".join(
                f"{instance['slug']} test_instance={str(bool(instance['test_instance'])).lower()} "
                f"production={str(bool(instance['production']) or instance.get('stage') == 'production').lower()} "
                f"logs={str('read_plugin_logs' in instance['capabilities']).lower()}"
                for instance in instances
            )
        )

    @classmethod
    def exit_with_error(cls, message: str) -> None:
        """
        Print error message and exit with code 1.

        Args:
            message (str): The error text.
        """
        print(f"ERROR: {message}")
        sys.exit(1)

    @classmethod
    def main(cls) -> None:
        """Parse arguments and run."""
        parser = argparse.ArgumentParser(description="Show the Canvas Platform session")
        parser.add_argument(
            "show",
            choices=["whoami", "instances", "publishers", "records", "plugins"],
        )
        parser.add_argument("slug", nargs="?", help="Instance slug, for records and plugins")
        parser.add_argument("model", nargs="?", choices=RECORD_MODELS, help="Model, for records")
        args = parser.parse_args()
        if args.show in ("records", "plugins") and args.slug is None:
            parser.error(f"{args.show} needs an instance slug")
        if args.show == "records" and args.model is None:
            parser.error("records needs a model")

        cls.run(show=args.show, slug=args.slug, model=args.model)


if __name__ == "__main__":
    PlatformSession.main()
