"""
Reports the Canvas Platform sign-in, the organizations that can publish plugins, and the deployable instances.

Usage:
    uv run --with 'canvas>=0.263.0' python platform_session.py whoami
    uv run --with 'canvas>=0.263.0' python platform_session.py instances
    uv run --with 'canvas>=0.263.0' python platform_session.py publishers
"""

import argparse
import sys
from typing import Any

from canvas_cli.apps.platform import auth
from canvas_cli.apps.platform.auth import PlatformAuthError
from canvas_cli.apps.platform.client import PlatformClient, PlatformError


class PlatformSession:
    """Reads the person's Canvas Platform session through the Canvas CLI's own sign-in and API client."""

    @classmethod
    def run(cls, show: str) -> None:
        """
        Print the requested view of the Platform session, or exit 1 when it cannot be shown.

        Args:
            show (str): "whoami" for the sign-in summary, "instances" for deployable instance slugs, "publishers" for publishing organization slugs and prefixes.
        """
        try:
            platform: str = auth.resolve_platform_url()
            if auth.stored_tokens(platform) is None:
                cls.exit_with_error(
                    f"Not signed in to Canvas Platform at {platform}. "
                    "Run `uv run --with 'canvas>=0.263.0' canvas login` in your terminal "
                    "(it opens a browser), then try again."
                )

            client = PlatformClient(platform)
            if show == "whoami":
                cls.print_whoami(
                    platform, client.me(), cls.deployable_instances(client.instances())
                )
            elif show == "publishers":
                cls.print_publishers(cls.publishing_orgs(client.me()))
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
    def deployable_instances(cls, instances: list[dict[str, Any]]) -> list[str]:
        """
        Slugs of the instances the person can deploy plugins to, as the Canvas CLI decides it.

        Args:
            instances (list[dict]): The `/api/v1/instances` payload.

        Returns:
            list[str]: Slugs of managed instances with the deploy_plugin capability.
        """
        return [
            instance["slug"]
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
    def print_instances(cls, slugs: list[str]) -> None:
        """
        Print one deployable instance slug per line, or exit 1 when there are none.

        Args:
            slugs (list[str]): Deployable instance slugs.
        """
        if not slugs:
            cls.exit_with_error(
                "There is no instance Canvas Platform manages that you can deploy plugins to."
            )
        print("\n".join(slugs))

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
        parser.add_argument("show", choices=["whoami", "instances", "publishers"])
        args = parser.parse_args()

        cls.run(show=args.show)


if __name__ == "__main__":
    PlatformSession.main()
