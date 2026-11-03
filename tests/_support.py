"""Shared sandbox for the jdharness and install.py tests.

Every test gets a temporary HOME and config directory, so nothing touches the
real profile, PATH, registry or ~/.config.
"""
import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO))

import jdharness  # noqa: E402

SKILLS = ("jd-alpha", "jd-beta")
AGENT = "jd-helper.md"
VAULT_AGENT = "jd-sync.md"
VAULT_TEXT = "Vault: `{{OBSIDIAN_VAULT}}`\n"


def add_vault_agent(root):
    """Add an agent that needs the Obsidian Vault, like jd-obsidian-sync."""
    (root / "agents" / VAULT_AGENT).write_text(VAULT_TEXT, encoding="utf-8")


def make_source(root, skills=SKILLS, agents=(AGENT,)):
    """Create a minimal JuanDevops repo: skills/<name>/SKILL.md and agents/*.md."""
    for name in skills:
        (root / "skills" / name).mkdir(parents=True)
        (root / "skills" / name / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")
    (root / "skills" / "notes").mkdir(parents=True)  # no SKILL.md: must be ignored
    (root / "agents").mkdir(parents=True, exist_ok=True)
    for name in agents:
        (root / "agents" / name).write_text(f"# {name}\n", encoding="utf-8")
    (root / "agents" / "readme.txt").write_text("not an agent\n", encoding="utf-8")
    return root


def sandbox_env(home):
    return {
        "HOME": str(home),
        "USERPROFILE": str(home),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "APPDATA": str(home / "AppData" / "Roaming"),
        "LOCALAPPDATA": str(home / "AppData" / "Local"),
        "SHELL": "/bin/bash",
    }


class FakeStdin(io.StringIO):
    def __init__(self, tty):
        super().__init__("")
        self.tty = tty

    def isatty(self):
        return self.tty


class Sandbox(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="jdharness-test-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = self.tmp / "home"
        self.home.mkdir()
        env = mock.patch.dict(os.environ, sandbox_env(self.home))
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("JDHARNESS_SOURCE", None)
        self.src = make_source(self.tmp / "src")
        self.project = self.tmp / "project"
        self.project.mkdir()

    def cli(self, *args, tty=False, answers=()):
        """Run jdharness in-process. Returns (exit code, stdout, stderr)."""
        out, err = io.StringIO(), io.StringIO()
        replies = iter(answers)
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
                mock.patch("sys.stdin", FakeStdin(tty)), \
                mock.patch("builtins.input", lambda prompt="": next(replies)):
            try:
                code = jdharness.main(list(args))
            except SystemExit as exit_:
                code = exit_.code
        return code, out.getvalue(), err.getvalue()

    def install(self, *extra):
        code, out, err = self.cli("install", "-p", str(self.project), "--source", str(self.src), *extra)
        self.assertEqual(code, 0, err)
        return out

    def manifest(self):
        return jdharness.read_manifest(self.project)
