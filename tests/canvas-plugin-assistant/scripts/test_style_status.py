"""Tests for style_status.py, the sole producer of style-status.json."""

import json
import os
import re
import shutil
from pathlib import Path

import pytest

import style_status
from style_status import (
    REQUIRED_CHECKS,
    SCHEMA_VERSION,
    STATUS_PATH,
    build_payload,
    main,
    parse_record,
    write_status,
)


def _read_status(plugin_dir: Path) -> dict:
    """Load the status file written under `plugin_dir`."""
    return json.loads((plugin_dir / STATUS_PATH).read_text(encoding="utf-8"))


# The real ruleset the workflow ships, not a hand-copied subset. Tests that
# assert on what ruff includes or excludes have to read this file, because the
# behavior under test is the interaction between its `exclude` and the command
# line.
SHIPPED_RUFF_CONFIG = (
    Path(__file__).parents[3] / "canvas-plugin-assistant" / "config" / "pyproject.toml"
)

# The real mypy ruleset the scaffold copies and /cpa:style falls back to. Its
# `exclude` is what keeps a required check out of the plugin's virtualenv, so a
# test about that behavior has to read this file rather than a subset.
SHIPPED_MYPY_CONFIG = (
    Path(__file__).parents[3] / "canvas-plugin-assistant" / "config" / "mypy.ini"
)


@pytest.fixture
def shipped_ruff_config() -> str:
    """The shipped ruff ruleset, skipping when ruff itself is unavailable."""
    if shutil.which("ruff") is None:
        pytest.skip("ruff is not on PATH")
    if not SHIPPED_RUFF_CONFIG.is_file():
        pytest.skip(f"shipped ruff config is missing at {SHIPPED_RUFF_CONFIG}")
    return str(SHIPPED_RUFF_CONFIG)


@pytest.fixture
def shipped_mypy_config() -> str:
    """The shipped mypy ruleset, skipping when the mypy toolchain is unavailable."""
    if not SHIPPED_MYPY_CONFIG.is_file():
        pytest.skip(f"shipped mypy config is missing at {SHIPPED_MYPY_CONFIG}")
    if not style_status.tool_available(
        style_status.BOUNDED_MYPY, "mypy", SHIPPED_MYPY_CONFIG.parent
    ):
        pytest.skip("mypy toolchain is not resolvable through uv")
    return str(SHIPPED_MYPY_CONFIG)


class TestBuildPayload:
    """Tests for the payload shape and the style_clean rule."""

    def test_all_passing_is_clean(self) -> None:
        """Every check ran and passed, so style_clean is true."""
        payload = build_payload(
            {"ruff": "pass", "mypy": "pass", "manifest": "pass"}
        )

        assert payload == {
            "version": SCHEMA_VERSION,
            "style_clean": True,
            "checks": {"ruff": True, "mypy": True, "manifest": True},
            "tree_digest": None,
        }

    def test_a_failure_is_not_clean(self) -> None:
        """A check that ran and failed makes style_clean false and is named."""
        payload = build_payload(
            {"ruff": "pass", "mypy": "fail", "manifest": "pass"}
        )

        assert payload["style_clean"] is False
        assert payload["checks"]["mypy"] is False

    def test_skipped_check_is_omitted_not_passed(self) -> None:
        """A skipped check is absent from `checks` rather than recorded as true."""
        payload = build_payload(
            {"ruff": "pass", "mypy": "pass", "manifest": "skip"}
        )

        assert "manifest" not in payload["checks"]
        assert payload["style_clean"] is True

    def test_nothing_ran_is_unknown_not_clean(self) -> None:
        """No check ran at all, so style_clean is null rather than vacuously true.

        This is the fail-open case: the toolchain was absent, so the build is
        genuinely unassessed and must not read back as a clean one.
        """
        payload = build_payload(
            {"ruff": "skip", "mypy": "skip", "manifest": "skip"}
        )

        assert payload == {
            "version": SCHEMA_VERSION,
            "style_clean": None,
            "checks": {},
            "tree_digest": None,
        }

    def test_skipped_required_check_is_unknown(self) -> None:
        """A required check that did not run makes the overall state unknown, even
        when the checks that did run all passed."""
        for skipped in REQUIRED_CHECKS:
            outcomes = dict.fromkeys(("ruff", "mypy", "manifest"), "pass")
            outcomes[skipped] = "skip"

            payload = build_payload(outcomes)

            assert payload["style_clean"] is None, skipped

    def test_skipped_manifest_does_not_make_it_unknown(self) -> None:
        """The manifest check is not required — a plugin without a manifest still
        gets a real verdict."""
        payload = build_payload({"ruff": "pass", "mypy": "fail", "manifest": "skip"})

        assert payload["style_clean"] is False

    def test_carries_a_version(self) -> None:
        """The payload is versioned so a reader can reject an unknown shape."""
        assert build_payload({"ruff": "pass"})["version"] == SCHEMA_VERSION


class TestWriteStatus:
    """Tests for the atomic write."""

    def test_creates_the_artifacts_directory(self, tmp_path: Path) -> None:
        """The .cpa-workflow-artifacts directory is created when absent."""
        write_status(tmp_path, {"version": 1, "style_clean": True, "checks": {}})

        assert (tmp_path / STATUS_PATH).is_file()

    def test_overwrites_invalid_existing_json(self, tmp_path: Path) -> None:
        """A corrupt or truncated status file is replaced wholesale.

        The writer never parses what is already there, so a file left invalid by
        an interrupted run is regenerated by the next check rather than inspected.
        """
        dest = tmp_path / STATUS_PATH
        dest.parent.mkdir(parents=True)
        dest.write_text('{"style_clean": tr', encoding="utf-8")

        write_status(tmp_path, {"version": 1, "style_clean": False, "checks": {}})

        assert _read_status(tmp_path) == {
            "version": 1,
            "style_clean": False,
            "checks": {},
        }

    def test_overwrites_an_older_shape(self, tmp_path: Path) -> None:
        """A payload from a previous schema is replaced, not merged."""
        dest = tmp_path / STATUS_PATH
        dest.parent.mkdir(parents=True)
        dest.write_text('{"style_clean": true, "extra": "gone"}', encoding="utf-8")

        write_status(tmp_path, {"version": 1, "style_clean": True, "checks": {}})

        assert "extra" not in _read_status(tmp_path)

    def test_leaves_no_temporary_file_behind(self, tmp_path: Path) -> None:
        """The tmp file used for the atomic replace is not left in the directory,
        so CPA's `git add` of this directory never picks one up."""
        write_status(tmp_path, {"version": 1, "style_clean": True, "checks": {}})

        assert [path.name for path in (tmp_path / STATUS_PATH.parent).iterdir()] == [
            STATUS_PATH.name
        ]

    def test_ends_with_a_newline(self, tmp_path: Path) -> None:
        """The file is newline-terminated so it reads cleanly in a diff."""
        dest = write_status(tmp_path, {"version": 1, "style_clean": True, "checks": {}})

        assert dest.read_text(encoding="utf-8").endswith("}\n")


class TestParseRecord:
    """Tests for --record argument parsing."""

    def test_parses_pairs_and_defaults_the_rest_to_skip(self) -> None:
        """An unmentioned check defaults to skip, never to pass."""
        assert parse_record(["ruff=pass", "mypy=fail"]) == {
            "ruff": "pass",
            "mypy": "fail",
            "manifest": "skip",
        }

    def test_none_means_nothing_ran(self) -> None:
        """The `none` token records every check as skipped."""
        assert parse_record(["none"]) == {
            "ruff": "skip",
            "mypy": "skip",
            "manifest": "skip",
        }

    def test_rejects_an_unknown_check(self) -> None:
        """A typo'd check name is an error, not a silently ignored pair."""
        try:
            parse_record(["ruffff=pass"])
        except ValueError as exc:
            assert "ruffff" in str(exc)
        else:
            raise AssertionError("expected ValueError")

    def test_rejects_an_unknown_outcome(self) -> None:
        """Only pass/fail/skip are accepted, so `true` cannot mean pass by accident."""
        try:
            parse_record(["ruff=true"])
        except ValueError as exc:
            assert "true" in str(exc)
        else:
            raise AssertionError("expected ValueError")


class TestToolFailureIsNotACheckFailure:
    """Exit 2 means the tool could not run, so the check is skipped not failed."""

    def _stub_runs(self, monkeypatch, ruff, mypy):
        """Make run_checks see the given (returncode, output) pairs.

        Resolution is stubbed as succeeding so these cases isolate what the tool
        itself reported; the probe has its own tests.
        """
        calls = iter([("format", 0, ""), ("ruff", *ruff), ("mypy", *mypy)])

        def fake_run(cmd, cwd, timeout):
            _name, code, out = next(calls)
            return code, out

        monkeypatch.setattr(style_status, "tool_available", lambda spec, tool, cwd: True)
        monkeypatch.setattr(style_status, "_run", fake_run)

    def test_ruff_exit_2_is_a_skip(self, tmp_path: Path, monkeypatch) -> None:
        """An unparseable ruleset must not be recorded as a plugin style failure.

        It is a platform problem, and `fail` would both misattribute it and,
        upstream in Studio, spend the agent's fix budget on an unfixable error.
        """
        self._stub_runs(monkeypatch, ruff=(2, "ruff failed"), mypy=(0, ""))
        (tmp_path / "mypy.ini").write_text("[mypy]\n")

        outcomes = style_status.run_checks(
            tmp_path, "ruff.toml", str(tmp_path / "mypy.ini")
        )

        assert outcomes["ruff"] == "skip"
        assert style_status.build_payload(outcomes)["style_clean"] is None

    def test_ruff_exit_1_is_a_real_failure(self, tmp_path: Path, monkeypatch) -> None:
        """Diagnostics are what exit 1 means, so they stay a failed check."""
        self._stub_runs(
            monkeypatch, ruff=(1, "handler.py:4:5: D103 ..."), mypy=(0, "")
        )
        (tmp_path / "mypy.ini").write_text("[mypy]\n")

        outcomes = style_status.run_checks(
            tmp_path, "ruff.toml", str(tmp_path / "mypy.ini")
        )

        assert outcomes["ruff"] == "fail"

    def test_mypy_exit_2_is_a_skip(self, tmp_path: Path, monkeypatch) -> None:
        """mypy that could not start has reported nothing about the plugin's types."""
        self._stub_runs(monkeypatch, ruff=(0, ""), mypy=(2, "usage: mypy ..."))
        (tmp_path / "mypy.ini").write_text("[mypy]\n")

        outcomes = style_status.run_checks(
            tmp_path, "ruff.toml", str(tmp_path / "mypy.ini")
        )

        assert outcomes["mypy"] == "skip"

    def test_a_signal_kill_is_a_skip(self, tmp_path: Path, monkeypatch) -> None:
        """A negative code means the tool was killed, not that the plugin is dirty.

        An OOM-kill returns -9, which the documented 0/1/2 contract does not
        cover. Testing the complement of "the tool reported on the code" keeps it
        out of the plugin's record.
        """
        self._stub_runs(monkeypatch, ruff=(-9, ""), mypy=(0, ""))
        (tmp_path / "mypy.ini").write_text("[mypy]\n")

        outcomes = style_status.run_checks(
            tmp_path, "ruff.toml", str(tmp_path / "mypy.ini")
        )

        assert outcomes["ruff"] == "skip"

    def test_an_unknown_exit_code_is_a_skip(self, tmp_path: Path, monkeypatch) -> None:
        """A code above 2 is not a documented diagnostic result, so it is a skip."""
        self._stub_runs(monkeypatch, ruff=(0, ""), mypy=(3, "internal error"))
        (tmp_path / "mypy.ini").write_text("[mypy]\n")

        outcomes = style_status.run_checks(
            tmp_path, "ruff.toml", str(tmp_path / "mypy.ini")
        )

        assert outcomes["mypy"] == "skip"

    def test_mypy_exit_1_is_a_real_failure(self, tmp_path: Path, monkeypatch) -> None:
        """Type errors stay a failed check."""
        self._stub_runs(
            monkeypatch, ruff=(0, ""), mypy=(1, "x.py:2: error: Incompatible ...")
        )
        (tmp_path / "mypy.ini").write_text("[mypy]\n")

        outcomes = style_status.run_checks(
            tmp_path, "ruff.toml", str(tmp_path / "mypy.ini")
        )

        assert outcomes["mypy"] == "fail"


class TestMain:
    """Tests for the command-line entry point."""

    def test_record_writes_the_status(self, tmp_path: Path) -> None:
        """--record emits the payload from the outcomes the caller supplied."""
        exit_code = main(
            ["--record", "ruff=pass", "mypy=fail", "--plugin-dir", str(tmp_path)]
        )

        assert exit_code == 0
        assert _read_status(tmp_path) == {
            "version": SCHEMA_VERSION,
            "style_clean": False,
            "checks": {"ruff": True, "mypy": False},
            "tree_digest": style_status.tree_digest(tmp_path),
        }

    def test_record_none_writes_the_unknown_status(self, tmp_path: Path) -> None:
        """--record none records that nothing ran, rather than leaving a stale file.

        This is what the Studio gate writes when its master switch is off, so an
        earlier run's verdict cannot survive as a description of new code.
        """
        (tmp_path / STATUS_PATH).parent.mkdir(parents=True)
        (tmp_path / STATUS_PATH).write_text(
            '{"version": 1, "style_clean": true, "checks": {"ruff": true}}',
            encoding="utf-8",
        )

        exit_code = main(["--record", "none", "--plugin-dir", str(tmp_path)])

        assert exit_code == 0
        assert _read_status(tmp_path) == {
            "version": SCHEMA_VERSION,
            "style_clean": None,
            "checks": {},
            "tree_digest": style_status.tree_digest(tmp_path),
        }

    def test_run_without_a_ruff_config_records_unknown(self, tmp_path: Path) -> None:
        """--run against a missing ruleset records the unknown state instead of
        reporting a clean build."""
        exit_code = main(
            [
                "--run",
                "--plugin-dir", str(tmp_path),
                "--ruff-config", str(tmp_path / "absent.toml"),
            ]
        )

        assert exit_code == 0
        assert _read_status(tmp_path)["style_clean"] is None

    def test_rejects_run_without_a_ruff_config_argument(self, tmp_path: Path) -> None:
        """--run needs to be told which ruleset to enforce."""
        assert main(["--run", "--plugin-dir", str(tmp_path)]) == 2

    def test_rejects_a_missing_plugin_dir(self, tmp_path: Path) -> None:
        """A plugin dir that does not exist is a usage error, not a silent no-op."""
        assert main(["--record", "none", "--plugin-dir", str(tmp_path / "nope")]) == 2

    def test_reports_a_write_failure(self, tmp_path: Path) -> None:
        """An unwritable destination exits 2 rather than claiming success."""
        os.chmod(tmp_path, 0o500)
        try:
            exit_code = main(["--record", "none", "--plugin-dir", str(tmp_path)])
        finally:
            os.chmod(tmp_path, 0o700)

        assert exit_code == 2


class TestReadStatus:
    """Tests for reading the record back.

    Every way of failing to get a trustworthy answer must be UNKNOWN, never
    CLEAN. A reader that resolves an unreadable record to a pass reintroduces
    the vacuous-true defect on the read side, which is the whole point of the
    null rule on the write side.
    """

    def _write(self, plugin_dir: Path, body: str) -> None:
        dest = plugin_dir / STATUS_PATH
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(body, encoding="utf-8")

    def _write_record(self, plugin_dir: Path, **payload: object) -> None:
        """Write a record that is correctly versioned and describes this tree.

        Fills in the version and a matching digest so a test about one rule is
        not answered by an earlier gate instead.
        """
        body = {
            "version": SCHEMA_VERSION,
            "tree_digest": style_status.tree_digest(plugin_dir),
            **payload,
        }
        self._write(plugin_dir, json.dumps(body))

    def test_clean_when_every_check_passed(self, tmp_path: Path) -> None:
        """The one case that reads as clean."""
        self._write_record(
            tmp_path,
            style_clean=True,
            checks={"ruff": True, "mypy": True, "manifest": True},
        )

        verdict, _ = style_status.read_status(tmp_path)

        assert verdict == style_status.CLEAN

    def test_clean_without_a_manifest_check(self, tmp_path: Path) -> None:
        """A plugin with no manifest still reads clean — it is not a required check."""
        self._write_record(
            tmp_path, style_clean=True, checks={"ruff": True, "mypy": True}
        )

        verdict, _ = style_status.read_status(tmp_path)

        assert verdict == style_status.CLEAN

    def test_failed_names_the_check(self, tmp_path: Path) -> None:
        """A recorded failure is FAILED and says which check, so a caller can act."""
        self._write_record(
            tmp_path, style_clean=False, checks={"ruff": True, "mypy": False}
        )

        verdict, detail = style_status.read_status(tmp_path)

        assert verdict == style_status.FAILED
        assert "mypy" in detail

    def test_missing_file_is_unknown(self, tmp_path: Path) -> None:
        """No record means nobody has assessed this code, not that it is fine."""
        verdict, _ = style_status.read_status(tmp_path)

        assert verdict == style_status.UNKNOWN

    def test_invalid_json_is_unknown(self, tmp_path: Path) -> None:
        """A truncated record from an interrupted run is unknown, not a pass."""
        self._write(tmp_path, '{"version": 1, "style_clean": tr')

        verdict, _ = style_status.read_status(tmp_path)

        assert verdict == style_status.UNKNOWN

    def test_a_json_non_object_is_unknown(self, tmp_path: Path) -> None:
        """Valid JSON that is not an object cannot carry a verdict."""
        self._write(tmp_path, '"clean"')

        verdict, _ = style_status.read_status(tmp_path)

        assert verdict == style_status.UNKNOWN

    def test_an_unrecognized_version_is_unknown(self, tmp_path: Path) -> None:
        """The load-bearing check: a future shape must not be read as this one.

        Everything else degrades safely. Skipping this one silently misreads a v3
        payload as a v2, which is why it is compared explicitly.
        """
        self._write(
            tmp_path,
            '{"version": 3, "style_clean": true, "checks": {"ruff": true, "mypy": true}}',
        )

        verdict, detail = style_status.read_status(tmp_path)

        assert verdict == style_status.UNKNOWN
        assert "version" in detail

    def test_a_missing_version_is_unknown(self, tmp_path: Path) -> None:
        """A payload predating the version field is an unrecognized shape."""
        self._write(tmp_path, '{"style_clean": true, "checks": {"ruff": true}}')

        verdict, _ = style_status.read_status(tmp_path)

        assert verdict == style_status.UNKNOWN

    def test_a_skipped_required_check_is_unknown(self, tmp_path: Path) -> None:
        """An absent key means that check did not run, so the build is unassessed.

        Read by presence, not by value — this is the fail-open case where the
        toolchain was missing.
        """
        self._write_record(tmp_path, style_clean=None, checks={})

        verdict, detail = style_status.read_status(tmp_path)

        assert verdict == style_status.UNKNOWN
        assert "ruff" in detail and "mypy" in detail

    def test_passing_checks_with_a_null_verdict_is_unknown(self, tmp_path: Path) -> None:
        """A self-inconsistent record is not resolved in the optimistic direction."""
        self._write_record(
            tmp_path, style_clean=None, checks={"ruff": True, "mypy": True}
        )

        verdict, _ = style_status.read_status(tmp_path)

        assert verdict == style_status.UNKNOWN

    def test_a_non_boolean_check_value_is_a_corrupt_record(self, tmp_path: Path) -> None:
        """A value that is neither true nor false means the record is corrupt.

        That is UNKNOWN rather than FAILED: reporting it as "your ruff is dirty"
        would be a claim about the code, when all we know is the record is junk.
        Either way it is never a pass.
        """
        for value in ("yes", None, 1, []):
            self._write_record(
                tmp_path,
                style_clean=True,
                checks={"ruff": value, "mypy": True},
            )

            verdict, detail = style_status.read_status(tmp_path)

            assert verdict == style_status.UNKNOWN, value
            assert "ruff" in detail, value

    def test_a_literal_false_is_a_real_failure(self, tmp_path: Path) -> None:
        """FAILED is reserved for a check that ran and reported a problem."""
        self._write_record(
            tmp_path, style_clean=False, checks={"ruff": False, "mypy": True}
        )

        verdict, detail = style_status.read_status(tmp_path)

        assert verdict == style_status.FAILED
        assert detail == "ruff"

    def test_an_incomplete_assessment_outranks_a_known_failure(self, tmp_path: Path) -> None:
        """A missing required check wins over a recorded failure.

        Re-running surfaces the failure anyway, whereas reporting FAILED here
        would present a partial verdict as the whole story.
        """
        self._write_record(tmp_path, style_clean=False, checks={"ruff": False})

        verdict, detail = style_status.read_status(tmp_path)

        assert verdict == style_status.UNKNOWN
        assert "mypy" in detail


class TestCheckMode:
    """Tests for the --check CLI, which /cpa:wrap-up calls."""

    def test_exit_0_when_clean(self, tmp_path: Path) -> None:
        """Clean exits 0."""
        main(["--record", "ruff=pass", "mypy=pass", "--plugin-dir", str(tmp_path)])

        assert main(["--check", "--plugin-dir", str(tmp_path)]) == 0

    def test_exit_1_when_a_check_failed(self, tmp_path: Path) -> None:
        """A real failure exits 1 — the caller should fix the code."""
        main(["--record", "ruff=pass", "mypy=fail", "--plugin-dir", str(tmp_path)])

        assert main(["--check", "--plugin-dir", str(tmp_path)]) == 1

    def test_exit_3_when_unknown(self, tmp_path: Path) -> None:
        """Unknown exits 3, distinct from 1, so the caller says "re-run" not "fix"."""
        main(["--record", "none", "--plugin-dir", str(tmp_path)])

        assert main(["--check", "--plugin-dir", str(tmp_path)]) == 3

    def test_exit_3_with_no_record_at_all(self, tmp_path: Path) -> None:
        """A never-checked plugin is unknown, and never silently 0."""
        assert main(["--check", "--plugin-dir", str(tmp_path)]) == 3


class TestTreeDigest:
    """Tests for the fingerprint that tells a current record from a stale one."""

    def test_covers_sources_the_manifest_and_the_mypy_config(
        self, tmp_path: Path
    ) -> None:
        """The digest spans exactly the inputs that decide a verdict."""
        (tmp_path / "handler.py").write_text("x = 1\n", encoding="utf-8")
        (tmp_path / "CANVAS_MANIFEST.json").write_text("{}", encoding="utf-8")
        (tmp_path / "mypy.ini").write_text("[mypy]\n", encoding="utf-8")

        covered = {str(path) for path in style_status.digest_files(tmp_path)}

        assert covered == {"handler.py", "CANVAS_MANIFEST.json", "mypy.ini"}

    def test_covers_type_stubs(self, tmp_path: Path) -> None:
        """Both tools read `.pyi`, so a stub is an input like any source.

        ruff lints and formats stubs directly, and mypy prefers a `foo.pyi` over
        its `foo.py` sibling for what it reports, so a stub can decide a verdict
        with no `.py` file changing.
        """
        (tmp_path / "handler.py").write_text("x = 1\n", encoding="utf-8")
        (tmp_path / "vendor.pyi").write_text("def add(a: int) -> int: ...\n", encoding="utf-8")

        covered = {str(path) for path in style_status.digest_files(tmp_path)}

        assert covered == {"handler.py", "vendor.pyi"}

    def test_moves_when_a_stub_changes(self, tmp_path: Path) -> None:
        """Editing a stub stales the record, the same as editing a source."""
        (tmp_path / "handler.py").write_text("x = 1\n", encoding="utf-8")
        stub = tmp_path / "vendor.pyi"
        stub.write_text("def add(a: int) -> int: ...\n", encoding="utf-8")
        before = style_status.tree_digest(tmp_path)

        stub.write_text("def add(a: int) -> str: ...\n", encoding="utf-8")

        assert style_status.tree_digest(tmp_path) != before

    def test_a_nested_mypy_config_is_not_an_input(self, tmp_path: Path) -> None:
        """Only the top-level mypy.ini is read, so only that one counts.

        ``resolve_mypy_config`` reads ``plugin_dir/mypy.ini`` and nothing deeper,
        so a nested copy changes no verdict and digesting it would stale a record
        over a file nothing read. The manifest is different -- it is resolved
        rather than named, so it is digested wherever it resolves.
        """
        (tmp_path / "handler.py").write_text("x = 1\n", encoding="utf-8")
        (tmp_path / "mypy.ini").write_text("[mypy]\n", encoding="utf-8")
        before = style_status.tree_digest(tmp_path)
        nested = tmp_path / "vendored"
        nested.mkdir()
        (nested / "mypy.ini").write_text("[mypy]\nstrict = True\n", encoding="utf-8")

        assert style_status.tree_digest(tmp_path) == before

    def test_only_the_resolved_manifest_is_an_input(self, tmp_path: Path) -> None:
        """A second manifest that is not the plugin's changes no verdict.

        The check formats one manifest, the one ``find_manifest`` resolves, so
        that is the only one whose contents can decide anything.
        """
        (tmp_path / "handler.py").write_text("x = 1\n", encoding="utf-8")
        (tmp_path / "CANVAS_MANIFEST.json").write_text('{"name": "x"}', encoding="utf-8")
        before = style_status.tree_digest(tmp_path)
        decoy = tmp_path / "fixtures"
        decoy.mkdir()
        (decoy / "CANVAS_MANIFEST.json").write_text("{}", encoding="utf-8")

        assert style_status.tree_digest(tmp_path) == before

    def test_moves_when_the_plugin_mypy_config_changes(self, tmp_path: Path) -> None:
        """A plugin's own mypy.ini wins over the fallback, so it decides the verdict.

        Relaxing a rule in it can turn a recorded mypy failure into a pass
        without any source file changing, so a digest that ignored it would
        report a verdict reached under rules that no longer apply.
        """
        (tmp_path / "handler.py").write_text("x = 1\n", encoding="utf-8")
        config = tmp_path / "mypy.ini"
        config.write_text("[mypy]\nwarn_return_any = True\n", encoding="utf-8")
        before = style_status.tree_digest(tmp_path)

        config.write_text("[mypy]\nwarn_return_any = False\n", encoding="utf-8")

        assert style_status.tree_digest(tmp_path) != before

    def test_ignores_files_no_check_reads(self, tmp_path: Path) -> None:
        """A README or a lockfile cannot change a verdict, so it cannot stale one."""
        (tmp_path / "handler.py").write_text("x = 1\n", encoding="utf-8")
        before = style_status.tree_digest(tmp_path)

        (tmp_path / "README.md").write_text("docs\n", encoding="utf-8")

        assert style_status.tree_digest(tmp_path) == before

    def test_ignores_the_caches_and_the_record_itself(self, tmp_path: Path) -> None:
        """Writing the record must not invalidate the record it just wrote.

        The artifacts directory holds the status file, and a .py under a cache
        directory is not the plugin's source, so neither belongs in the digest.
        """
        (tmp_path / "handler.py").write_text("x = 1\n", encoding="utf-8")
        before = style_status.tree_digest(tmp_path)
        for directory in (".cpa-workflow-artifacts", "__pycache__", ".venv"):
            nested = tmp_path / directory
            nested.mkdir()
            (nested / "noise.py").write_text("y = 2\n", encoding="utf-8")

        assert style_status.tree_digest(tmp_path) == before

    def test_ignores_virtualenvs_by_any_name(self, tmp_path: Path) -> None:
        """A dependency's source under any virtualenv name must not stale the digest.

        ruff and the manifest search skip a bare `venv`, `.tox`, `.direnv` and the
        rest, not just `.venv`. The digest has to skip the identical set, or on a
        plugin whose virtualenv is a non-dot `venv/` it hashes installed-dependency
        files and churns on every dependency change, so `--check` reads UNKNOWN
        against unchanged plugin sources.
        """
        (tmp_path / "handler.py").write_text("x = 1\n", encoding="utf-8")
        before = style_status.tree_digest(tmp_path)
        for directory in ("venv", "env", ".tox", ".nox", ".direnv"):
            nested = tmp_path / directory / "site-packages" / "dep"
            nested.mkdir(parents=True)
            (nested / "installed.py").write_text("y = 2\n", encoding="utf-8")
            (nested / "installed.pyi").write_text("y: int\n", encoding="utf-8")

        assert style_status.tree_digest(tmp_path) == before

    def test_moves_when_a_source_changes(self, tmp_path: Path) -> None:
        """Editing a checked file changes the digest."""
        source = tmp_path / "handler.py"
        source.write_text("x = 1\n", encoding="utf-8")
        before = style_status.tree_digest(tmp_path)

        source.write_text("x = 2\n", encoding="utf-8")

        assert style_status.tree_digest(tmp_path) != before

    def test_moves_when_a_file_is_renamed(self, tmp_path: Path) -> None:
        """Names are hashed too, so a rename is not invisible to the digest."""
        source = tmp_path / "handler.py"
        source.write_text("x = 1\n", encoding="utf-8")
        before = style_status.tree_digest(tmp_path)

        source.rename(tmp_path / "renamed.py")

        assert style_status.tree_digest(tmp_path) != before


class TestStaleRecord:
    """A well-formed record about code that has since changed reads as unknown."""

    def test_editing_a_source_stales_the_record(self, tmp_path: Path) -> None:
        """The failure a shape check cannot catch: valid JSON, wrong code.

        Every other rejection is about a record that is malformed on its face.
        This one is entirely well-formed and simply describes a different tree,
        which is why the digest exists.
        """
        source = tmp_path / "handler.py"
        source.write_text("x = 1\n", encoding="utf-8")
        main(["--record", "ruff=pass", "mypy=pass", "--plugin-dir", str(tmp_path)])
        assert style_status.read_status(tmp_path)[0] == style_status.CLEAN

        source.write_text("x = 2\n", encoding="utf-8")

        verdict, detail = style_status.read_status(tmp_path)
        assert verdict == style_status.UNKNOWN
        assert "different code" in detail

    def test_unknown_not_failed_so_the_advice_is_rerun(self, tmp_path: Path) -> None:
        """Stale is UNKNOWN (exit 3), never FAILED: nobody has assessed this code."""
        source = tmp_path / "handler.py"
        source.write_text("x = 1\n", encoding="utf-8")
        main(["--record", "ruff=pass", "mypy=pass", "--plugin-dir", str(tmp_path)])
        source.write_text("x = 2\n", encoding="utf-8")

        assert main(["--check", "--plugin-dir", str(tmp_path)]) == 3

    def test_restoring_the_checked_tree_restores_the_verdict(
        self, tmp_path: Path
    ) -> None:
        """The digest is content-addressed, so reverting an edit is not a change."""
        source = tmp_path / "handler.py"
        source.write_text("x = 1\n", encoding="utf-8")
        main(["--record", "ruff=pass", "mypy=pass", "--plugin-dir", str(tmp_path)])
        source.write_text("x = 2\n", encoding="utf-8")

        source.write_text("x = 1\n", encoding="utf-8")

        assert style_status.read_status(tmp_path)[0] == style_status.CLEAN

    def test_a_record_without_a_digest_is_unknown(self, tmp_path: Path) -> None:
        """A current-version record that cannot prove freshness is not a pass."""
        dest = tmp_path / STATUS_PATH
        dest.parent.mkdir(parents=True)
        dest.write_text(
            json.dumps(
                {
                    "version": SCHEMA_VERSION,
                    "style_clean": True,
                    "checks": {"ruff": True, "mypy": True},
                }
            ),
            encoding="utf-8",
        )

        verdict, detail = style_status.read_status(tmp_path)

        assert verdict == style_status.UNKNOWN
        assert "digest" in detail


class TestStatusReport:
    """Tests for the structured read, which exists so consumers stop re-parsing."""

    def test_clean_carries_the_per_check_booleans(self, tmp_path: Path) -> None:
        """A consumer gets the detail without going near the JSON."""
        (tmp_path / "handler.py").write_text("x = 1\n", encoding="utf-8")
        main(
            [
                "--record", "ruff=pass", "mypy=pass", "manifest=pass",
                "--plugin-dir", str(tmp_path),
            ]
        )

        report = style_status.inspect_status(tmp_path)

        assert report.verdict == style_status.CLEAN
        assert report.exit_code == 0
        assert report.present is True
        assert report.checks == {"ruff": True, "mypy": True, "manifest": True}
        assert report.failed == []
        assert report.style_clean is True

    def test_failed_names_every_failing_check(self, tmp_path: Path) -> None:
        """`failed` is the list a caller would otherwise parse out by hand."""
        (tmp_path / "handler.py").write_text("x = 1\n", encoding="utf-8")
        main(
            [
                "--record", "ruff=fail", "mypy=fail", "manifest=pass",
                "--plugin-dir", str(tmp_path),
            ]
        )

        report = style_status.inspect_status(tmp_path)

        assert report.verdict == style_status.FAILED
        assert report.exit_code == 1
        assert report.failed == ["mypy", "ruff"]

    def test_an_untrustworthy_record_carries_no_check_data(
        self, tmp_path: Path
    ) -> None:
        """The rule that keeps the structured read as safe as the verdict.

        Echoing `checks` out of a payload the verdict just rejected would hand a
        consumer exactly the numbers the guards refused to stand behind, which
        is the naive-parse defect moved up one layer.
        """
        dest = tmp_path / STATUS_PATH
        dest.parent.mkdir(parents=True)
        dest.write_text(
            '{"version": 3, "style_clean": true, "checks": {"ruff": true}}',
            encoding="utf-8",
        )

        report = style_status.inspect_status(tmp_path)

        assert report.verdict == style_status.UNKNOWN
        assert report.exit_code == 3
        assert report.checks == {}
        assert report.failed == []
        assert report.style_clean is None

    def test_a_missing_record_is_reported_absent(self, tmp_path: Path) -> None:
        """`present` separates "never checked" from "checked and unreadable"."""
        report = style_status.inspect_status(tmp_path)

        assert report.verdict == style_status.UNKNOWN
        assert report.present is False

    def test_read_status_is_the_narrow_view(self, tmp_path: Path) -> None:
        """The tuple API stays the first two fields of the report."""
        (tmp_path / "handler.py").write_text("x = 1\n", encoding="utf-8")
        main(["--record", "ruff=pass", "mypy=fail", "--plugin-dir", str(tmp_path)])

        report = style_status.inspect_status(tmp_path)

        assert style_status.read_status(tmp_path) == (report.verdict, report.detail)


class TestJsonOutput:
    """Tests for --check --json, the cross-repo structured read."""

    def test_emits_the_report_and_keeps_the_exit_code(
        self, tmp_path: Path, capsys
    ) -> None:
        """Structure on stdout, same 0/1/3 contract the command tables document."""
        (tmp_path / "handler.py").write_text("x = 1\n", encoding="utf-8")
        main(["--record", "ruff=pass", "mypy=fail", "--plugin-dir", str(tmp_path)])
        capsys.readouterr()

        exit_code = main(["--check", "--json", "--plugin-dir", str(tmp_path)])

        emitted = json.loads(capsys.readouterr().out)
        assert exit_code == 1
        assert emitted["verdict"] == style_status.FAILED
        assert emitted["exit_code"] == 1
        assert emitted["checks"] == {"ruff": True, "mypy": False}
        assert emitted["failed"] == ["mypy"]

    def test_unknown_emits_json_too(self, tmp_path: Path, capsys) -> None:
        """A caller parsing stdout gets an object for every verdict, not just good ones."""
        exit_code = main(["--check", "--json", "--plugin-dir", str(tmp_path)])

        emitted = json.loads(capsys.readouterr().out)
        assert exit_code == 3
        assert emitted["verdict"] == style_status.UNKNOWN
        assert emitted["present"] is False

    def test_json_without_check_is_rejected(self, tmp_path: Path) -> None:
        """--json describes a read, so pairing it with a write is a usage error."""
        assert (
            main(["--record", "ruff=pass", "--json", "--plugin-dir", str(tmp_path)])
            == 2
        )


class TestRuffStaysOutOfTheVirtualenv:
    """The checks must not walk into the plugin's own .venv.

    The Canvas ruleset sets `exclude`, which replaces ruff's built-in
    exclusions, so `.venv` is not excluded by the config. `ruff check --fix`
    would then rewrite installed dependency source. These run the real shipped
    ruleset rather than a hand-copied subset, because the defect lives in the
    interaction between that file's `exclude` and the command line.
    """

    def _tree(self, tmp_path: Path, monkeypatch) -> dict[str, Path]:
        """A non-git plugin dir holding a vendored file, generated code and a source.

        mypy is switched off for this class so the captured output is ruff's
        alone; otherwise mypy's own findings on the same files would satisfy
        assertions meant to be about ruff's file selection.
        """
        monkeypatch.setattr(
            style_status, "resolve_mypy_config", lambda plugin_dir, mypy_config: None
        )
        unformatted = "import os,sys\ndef f( a,b ):\n  return a+b\n"
        paths = {
            "vendored": tmp_path / ".venv" / "site-packages" / "vend" / "v.py",
            "vendored_venv": tmp_path / "venv" / "site-packages" / "vend" / "v.py",
            "vendored_tox": tmp_path / ".tox" / "py" / "site-packages" / "vend" / "v.py",
            "generated": tmp_path / "canvas_generated" / "g.py",
            "source": tmp_path / "src" / "s.py",
        }
        for path in paths.values():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(unformatted, encoding="utf-8")
        return paths

    def test_a_vendored_file_is_left_untouched(
        self, tmp_path: Path, capsys, monkeypatch, shipped_ruff_config: str
    ) -> None:
        """ruff touches nothing under a virtualenv the ruleset would walk into.

        Covers `.venv` and the other virtualenv/tooling names the Canvas ruleset
        drops from ruff's defaults -- a bare `venv` and a `.tox` env -- not just
        `.venv`, since a plugin whose virtualenv has any of those names hits the
        same defect.
        """
        paths = self._tree(tmp_path, monkeypatch)
        vendored = ("vendored", "vendored_venv", "vendored_tox")
        before = {name: paths[name].read_bytes() for name in vendored}

        outcomes = style_status.run_checks(
            tmp_path, ruff_config=shipped_ruff_config, mypy_config=None
        )

        for name in vendored:
            assert paths[name].read_bytes() == before[name], f"{name} was rewritten"
        # Proves the run had a non-zero denominator: ruff did look at this tree
        # and did report on it, so "nothing under a virtualenv" is a real
        # exclusion rather than a run that checked nothing at all.
        assert outcomes["ruff"] == "fail"
        assert "src/s.py" in capsys.readouterr().err

    def test_both_subcommands_accept_the_exclusion(
        self, tmp_path: Path, capsys, monkeypatch, shipped_ruff_config: str
    ) -> None:
        """The control for the test above: the exclusion must be a valid argument.

        `ruff format` and `ruff check` do not accept the same flags --
        `--extend-exclude` is valid for check and rejected by format with exit 2.
        A rejected argument means formatting silently stops happening, and since
        a format that never ran also leaves `.venv` untouched, the exclusion test
        passes for the wrong reason. Asserting on the rewritten file cannot tell
        them apart either, because `ruff check --fix` rewrites the same file.

        So this asserts the thing that actually differs: nothing reported that it
        could not run.
        """
        self._tree(tmp_path, monkeypatch)

        style_status.run_checks(
            tmp_path, ruff_config=shipped_ruff_config, mypy_config=None
        )

        assert "could not run" not in capsys.readouterr().err

    def test_generated_code_stays_excluded(
        self, tmp_path: Path, capsys, monkeypatch, shipped_ruff_config: str
    ) -> None:
        """The narrower flag must not un-exclude what the ruleset excludes.

        `--exclude .venv` would replace the ruleset's own list and pull
        `canvas_generated/` back into scope. Only `--extend-exclude` adds to it,
        so this fails if the flag is ever swapped.
        """
        paths = self._tree(tmp_path, monkeypatch)
        before = paths["generated"].read_bytes()

        style_status.run_checks(
            tmp_path, ruff_config=shipped_ruff_config, mypy_config=None
        )

        reported = capsys.readouterr().err
        assert "canvas_generated" not in reported
        assert "src/s.py" in reported
        assert paths["generated"].read_bytes() == before


class TestMypyStaysOutOfTheVirtualenv:
    """mypy, a required check, must not walk into the plugin's own virtualenv.

    mypy walks a directory argument the way ruff does, but auto-skips only
    dot-prefixed names, so a bare `venv/` or `env/` is walked and any top-level
    module inside it type-checked. An error there would set `style_clean` false
    against code that is not the plugin's. These run the real shipped ruleset,
    because the behavior under test is that file's `exclude` plus the command
    line, exactly as the ruff class above does.
    """

    def _tree(self, tmp_path: Path) -> dict[str, Path]:
        """A plugin dir with a top-level module inside each virtualenv name.

        The modules sit directly under the virtualenv dir, not under
        `lib/pythonX.Y`, because the dotted component already stops mypy
        discovery there -- the bare-dir walk is the gap this closes.
        """
        untyped = "def leaked(value):\n    return value\n"
        paths = {
            "venv": tmp_path / "venv" / "vendored.py",
            "env": tmp_path / "env" / "vendored.py",
            "source": tmp_path / "src" / "s.py",
        }
        for path in paths.values():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(untyped, encoding="utf-8")
        return paths

    def test_the_shipped_config_excludes_virtualenv_dirs(
        self, tmp_path: Path, shipped_mypy_config: str
    ) -> None:
        """`config/mypy.ini`'s own `exclude` keeps mypy out of `venv/` and `env/`.

        Invokes mypy with the config alone -- no command-line `--exclude` -- so
        the assertion is about the shipped ruleset, which is what the scaffold
        copies, `/cpa:style` falls back to, and out-of-band mypy runs use.
        Without the rule mypy names `venv/vendored.py` and `env/vendored.py`;
        with it, only the real source remains.
        """
        self._tree(tmp_path)

        result = style_status._run(
            style_status.tool_cmd(
                style_status.BOUNDED_MYPY,
                "mypy",
                "--config-file", shipped_mypy_config,
                ".",
            ),
            tmp_path,
            style_status._MYPY_TIMEOUT,
        )

        assert result is not None, "mypy could not run"
        returncode, reported = result
        # Non-zero denominator: mypy did look at this tree and reported on the
        # real source, so "not under a virtualenv" is a real exclusion rather
        # than a run that checked nothing.
        assert returncode == 1
        assert "src/s.py" in reported
        assert "venv/vendored.py" not in reported
        assert "env/vendored.py" not in reported

    def test_run_checks_passes_the_exclusion_to_mypy(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """The control: the invocation carries `--exclude` with the venv regex.

        The behavioral test above rides on the shipped `config/mypy.ini`, whose
        `exclude` also covers these dirs. This asserts the command-line flag
        independently, so the coverage for a plugin shipping its own `mypy.ini`
        without the rule cannot silently regress.
        """
        captured: list[list[str]] = []

        def fake_run(cmd, cwd, timeout):
            captured.append(cmd)
            return (0, "")

        monkeypatch.setattr(
            style_status, "tool_available", lambda spec, tool, cwd: True
        )
        monkeypatch.setattr(style_status, "_run", fake_run)

        style_status.run_checks(tmp_path, ruff_config="unused.toml", mypy_config=None)

        mypy_cmds = [cmd for cmd in captured if "mypy" in cmd and "--version" not in cmd]
        assert mypy_cmds, "mypy was never invoked"
        mypy_cmd = mypy_cmds[0]
        assert "--exclude" in mypy_cmd
        regex = mypy_cmd[mypy_cmd.index("--exclude") + 1]
        for name in style_status._VENV_DIRS:
            assert re.search(regex, f"prefix/{name}/module.py"), (
                f"{name} is not excluded by {regex!r}"
            )


class TestPinnedToolchain:
    """The pinned versions must agree everywhere they are written down.

    The specs appear in this script, in three command docs, and in the sync
    workflow. A drifted pin means the workflow validates the ruleset against a
    ruff that is not the one the checks run, which is exactly the determinism
    this ticket exists to buy -- so it is a test rather than a comment asking
    the next person to remember.
    """

    _CPA = Path(__file__).parents[3] / "canvas-plugin-assistant"
    _WORKFLOW = (
        Path(__file__).parents[3]
        / ".github"
        / "workflows"
        / "update-canvas-ruff-config.yml"
    )

    def test_the_ruff_pin_is_the_same_in_every_document(self) -> None:
        """style.md, check-setup.md and new-plugin.md all name this script's pin."""
        for relative in (
            "commands/style.md",
            "commands/check-setup.md",
            "commands/new-plugin.md",
        ):
            text = (self._CPA / relative).read_text(encoding="utf-8")
            assert style_status.PINNED_RUFF in text, (
                f"{relative} does not name {style_status.PINNED_RUFF}"
            )

    def test_the_mypy_bound_is_the_same_in_every_document(self) -> None:
        """The same for the mypy bound, which is a range rather than a pin."""
        for relative in (
            "commands/style.md",
            "commands/check-setup.md",
            "commands/new-plugin.md",
            "commands/wrap-up.md",
        ):
            text = (self._CPA / relative).read_text(encoding="utf-8")
            assert style_status.BOUNDED_MYPY in text, (
                f"{relative} does not name {style_status.BOUNDED_MYPY}"
            )

    def test_the_sync_workflow_validates_against_the_same_ruff(self) -> None:
        """The workflow writes the version bare, so compare the version alone.

        It installs `ruff==${{ env.PINNED_RUFF }}` to parse the ruleset before
        pushing it. If that drifts from the ruff the checks run, the sync can
        green-light a config the real ruff rejects.
        """
        workflow = self._WORKFLOW.read_text(encoding="utf-8")
        version = style_status.PINNED_RUFF.split("==")[1]

        assert f"PINNED_RUFF: {version}" in workflow

    def test_the_checks_invoke_the_pinned_specs(self) -> None:
        """The argv the script builds carries the pin, not a bare tool name."""
        assert style_status.tool_cmd(style_status.PINNED_RUFF, "ruff", "--version") == [
            "uv", "run", "--no-project", "--with", style_status.PINNED_RUFF,
            "ruff", "--version",
        ]


class TestAnUnresolvableToolchainIsASkip:
    """uv's own failure must not read as the tool reporting violations.

    `uv run` passes the child's exit code through, and uv exits 1 when it cannot
    resolve `--with` -- an unsatisfiable pin, or a cache miss with no network.
    That is indistinguishable from ruff exiting 1 with diagnostics. Recording it
    as a failure would assert `style_clean: false` about code nothing examined,
    and a false failure blocks a deploy where a skip does not.
    """

    def test_ruff_that_cannot_resolve_is_skipped_not_failed(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """An exit-1 resolution failure records a skip, leaving the verdict unknown."""
        monkeypatch.setattr(
            style_status, "tool_available", lambda spec, tool, cwd: False
        )

        outcomes = style_status.run_checks(
            tmp_path, ruff_config="whatever.toml", mypy_config=None
        )

        assert outcomes["ruff"] == "skip"
        assert build_payload(outcomes)["style_clean"] is None

    def test_the_probe_rejects_a_nonzero_exit(self, tmp_path: Path, monkeypatch) -> None:
        """Only exit 0 counts as resolved; uv's exit 1 does not."""
        monkeypatch.setattr(
            style_status, "_run", lambda cmd, cwd, timeout: (1, "unsatisfiable")
        )

        assert (
            style_status.tool_available(style_status.PINNED_RUFF, "ruff", tmp_path)
            is False
        )

    def test_the_probe_accepts_a_clean_exit(self, tmp_path: Path, monkeypatch) -> None:
        """The negative case above is only meaningful if the positive one passes."""
        monkeypatch.setattr(
            style_status, "_run", lambda cmd, cwd, timeout: (0, "ruff 0.15.14")
        )

        assert (
            style_status.tool_available(style_status.PINNED_RUFF, "ruff", tmp_path)
            is True
        )


class TestMypyConfigFallback:
    """A plugin with no mypy.ini still gets a real verdict.

    Without a fallback, mypy is skipped without ever being invoked, and because
    mypy is required that leaves `style_clean` null and `--check` answering
    UNKNOWN however many rounds run. Of five recently sampled Studio-generated
    plugins, none shipped a mypy.ini, so this is the normal case.
    """

    def test_the_canonical_config_ships(self) -> None:
        """The fallback is only a fallback if the file is actually there."""
        assert style_status.FALLBACK_MYPY_CONFIG.is_file()
        assert "[mypy]" in style_status.FALLBACK_MYPY_CONFIG.read_text(encoding="utf-8")

    def test_falls_back_when_the_plugin_has_none(self, tmp_path: Path) -> None:
        """The canonical ruleset is used when the named config does not exist."""
        assert (
            style_status.resolve_mypy_config(tmp_path, "mypy.ini")
            == style_status.FALLBACK_MYPY_CONFIG
        )

    def test_falls_back_when_no_config_is_named(self, tmp_path: Path) -> None:
        """Naming nothing is the same case as naming something absent."""
        assert (
            style_status.resolve_mypy_config(tmp_path, None)
            == style_status.FALLBACK_MYPY_CONFIG
        )

    def test_the_plugins_own_config_wins(self, tmp_path: Path) -> None:
        """A plugin that ships a mypy.ini keeps deciding its own verdict."""
        own = tmp_path / "mypy.ini"
        own.write_text("[mypy]\n", encoding="utf-8")

        assert style_status.resolve_mypy_config(tmp_path, "mypy.ini") == own

    def test_a_relative_config_resolves_against_the_plugin_dir(
        self, tmp_path: Path
    ) -> None:
        """--run takes --plugin-dir, so a relative config is not cwd-relative.

        The recording step is invoked with a bare `mypy.ini`; resolving that
        against the process's cwd rather than the plugin would find the wrong
        file, or nothing, depending on where the agent happened to be standing.
        """
        plugin = tmp_path / "plugin"
        plugin.mkdir()
        own = plugin / "mypy.ini"
        own.write_text("[mypy]\n", encoding="utf-8")

        assert style_status.resolve_mypy_config(plugin, "mypy.ini") == own

    def test_mypy_runs_and_the_verdict_is_real(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """With no mypy.ini present, mypy is invoked and style_clean is a boolean.

        This is the defect in one assertion: the old guard skipped mypy without
        invoking it, so `style_clean` could never be anything but null.
        """
        (tmp_path / "handler.py").write_text("def f(a, b):\n    return a + b\n")
        invoked: list[list[str]] = []

        def fake_run(cmd, cwd, timeout):
            invoked.append(cmd)
            return 0, ""

        monkeypatch.setattr(style_status, "tool_available", lambda spec, tool, cwd: True)
        monkeypatch.setattr(style_status, "_run", fake_run)

        outcomes = style_status.run_checks(
            tmp_path, ruff_config="whatever.toml", mypy_config="mypy.ini"
        )

        assert outcomes["mypy"] == "pass"
        assert build_payload(outcomes)["style_clean"] is True
        assert any(
            "mypy" in cmd and str(style_status.FALLBACK_MYPY_CONFIG) in cmd
            for cmd in invoked
        ), invoked


class TestFindManifest:
    """The manifest is not always at the plugin dir.

    The canonical layout puts CANVAS_MANIFEST.json in the inner snake_case
    package while CPA_PLUGIN_DIR is the kebab-case container, so looking only at
    `plugin_dir/CANVAS_MANIFEST.json` misses it on exactly the layout
    /cpa:new-plugin creates. The consequence was a recorded `style_clean: true`
    with the manifest never checked.
    """

    def _nested(self, tmp_path: Path, body: str = '{"name": "ai_note_titles"}') -> Path:
        """The canonical layout: container dir, inner package, manifest inside it."""
        package = tmp_path / "ai_note_titles"
        package.mkdir()
        manifest = package / "CANVAS_MANIFEST.json"
        manifest.write_text(body, encoding="utf-8")
        return manifest

    def test_finds_a_nested_manifest(self, tmp_path: Path) -> None:
        """The defect in one assertion."""
        manifest = self._nested(tmp_path)

        assert style_status.find_manifest(tmp_path) == manifest

    def test_finds_a_flat_manifest(self, tmp_path: Path) -> None:
        """The flat layout keeps working — it was the only one that ever did."""
        manifest = tmp_path / "CANVAS_MANIFEST.json"
        manifest.write_text('{"name": "custom_data_uat"}', encoding="utf-8")

        assert style_status.find_manifest(tmp_path) == manifest

    def test_none_when_there_is_no_manifest(self, tmp_path: Path) -> None:
        """A plugin without a manifest still has to produce a verdict."""
        assert style_status.find_manifest(tmp_path) is None

    def test_prefers_the_manifest_matching_its_directory(self, tmp_path: Path) -> None:
        """The install directory's basename must equal the manifest name.

        `canvas install <dir>` names the plugin after the basename, and the
        runner rejects handlers from a foreign package, so the manifest whose
        directory matches its own `name` is the plugin's. This is the same rule
        Studio resolves with, so the two agree.
        """
        shallow = tmp_path / "CANVAS_MANIFEST.json"
        shallow.write_text('{"name": "something_else"}', encoding="utf-8")
        matching = self._nested(tmp_path)

        assert style_status.find_manifest(tmp_path) == matching

    def test_shallowest_wins_when_none_match(self, tmp_path: Path) -> None:
        """With no better signal, the shallowest candidate is the plugin's."""
        shallow = tmp_path / "CANVAS_MANIFEST.json"
        shallow.write_text('{"name": "mismatched"}', encoding="utf-8")
        deep = tmp_path / "pkg" / "inner"
        deep.mkdir(parents=True)
        (deep / "CANVAS_MANIFEST.json").write_text('{"name": "also_wrong"}', encoding="utf-8")

        assert style_status.find_manifest(tmp_path) == shallow

    def test_skips_manifests_inside_a_virtualenv(self, tmp_path: Path) -> None:
        """canvas-cli ships template manifests inside its own package."""
        vendored = tmp_path / ".venv" / "site-packages" / "canvas_cli" / "templates"
        vendored.mkdir(parents=True)
        (vendored / "CANVAS_MANIFEST.json").write_text('{"name": "templates"}', encoding="utf-8")

        assert style_status.find_manifest(tmp_path) is None

    def test_an_unreadable_manifest_is_still_a_candidate(self, tmp_path: Path) -> None:
        """A malformed manifest is precisely what the check exists to catch.

        Its `name` cannot be read, so it cannot match its directory, but
        discarding it would make the check silently skip the one case that most
        needs reporting.
        """
        manifest = self._nested(tmp_path, body="{not json")

        assert style_status.find_manifest(tmp_path) == manifest


class TestTheManifestCheckRunsOnTheCanonicalLayout:
    """End to end: the manifest check and the digest both reach a nested manifest."""

    def _plugin(self, tmp_path: Path) -> Path:
        """A nested plugin whose manifest is malformed: 4-space indent, wrong order."""
        package = tmp_path / "my_plugin"
        package.mkdir()
        (package / "handler.py").write_text("x = 1\n", encoding="utf-8")
        manifest = package / "CANVAS_MANIFEST.json"
        manifest.write_text(
            '{\n    "readme": "./README.md",\n    "name": "my_plugin"\n}\n',
            encoding="utf-8",
        )
        return manifest

    def test_the_manifest_check_is_recorded(self, tmp_path: Path, monkeypatch) -> None:
        """`manifest` appears in checks instead of being silently absent.

        Previously this key was missing on every nested plugin, so a record could
        read `style_clean: true` with the manifest unformatted.
        """
        self._plugin(tmp_path)
        monkeypatch.setattr(style_status, "tool_available", lambda spec, tool, cwd: True)
        monkeypatch.setattr(style_status, "_run", lambda cmd, cwd, timeout: (0, ""))

        outcomes = style_status.run_checks(
            tmp_path, ruff_config="whatever.toml", mypy_config=None
        )

        assert outcomes["manifest"] == "pass"
        assert "manifest" in build_payload(outcomes)["checks"]

    def test_the_real_formatter_canonicalizes_the_nested_manifest(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """Run against the real format_manifest.py, not a stub."""
        manifest = self._plugin(tmp_path)
        monkeypatch.setattr(style_status, "tool_available", lambda spec, tool, cwd: False)

        outcomes = style_status.run_checks(
            tmp_path, ruff_config="whatever.toml", mypy_config=None
        )

        assert outcomes["manifest"] == "pass"
        rewritten = manifest.read_text(encoding="utf-8")
        assert '"name"' in rewritten
        assert "    " not in rewritten, "still 4-space indented"

    def test_editing_the_nested_manifest_stales_the_record(self, tmp_path: Path) -> None:
        """The digest covers the manifest wherever it resolved.

        Injecting a key into a nested manifest used to leave the verdict at a
        clean exit 0, because the digest only matched config names at depth 1.
        """
        manifest = self._plugin(tmp_path)
        before = style_status.tree_digest(tmp_path)

        manifest.write_text('{"name": "my_plugin", "injected": true}\n', encoding="utf-8")

        assert style_status.tree_digest(tmp_path) != before

    def test_a_clean_record_reads_back_as_clean(self, tmp_path: Path) -> None:
        """The control: a fresh record on this layout is readable as clean.

        Without this, the staleness test above could pass for the wrong reason.
        """
        self._plugin(tmp_path)
        write_status(
            tmp_path,
            build_payload(
                {"ruff": "pass", "mypy": "pass", "manifest": "pass"},
                style_status.tree_digest(tmp_path),
            ),
        )

        assert style_status.inspect_status(tmp_path).verdict == style_status.CLEAN
