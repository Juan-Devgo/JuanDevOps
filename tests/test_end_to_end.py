"""End to end: clone, install.py, jdharness install/update/remove, uninstall.

Runs real subprocesses, a real git remote and the real skills of this repo,
inside a temporary HOME.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _support import REPO, sandbox_env

WINDOWS = os.name == "nt"
GIT = ["git", "-c", "user.name=test", "-c", "user.email=test@example.com", "-c", "init.defaultBranch=main"]


@unittest.skipUnless(shutil.which("git"), "git is required")
class EndToEndTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="jdharness-e2e-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.env = {k: v for k, v in os.environ.items() if k != "JDHARNESS_SOURCE"}
        self.env.update(sandbox_env(self.home))
        self.env["PATH"] = os.pathsep.join(p for p in os.environ.get("PATH", "").split(os.pathsep)
                                           if ".local" not in p)
        self.env["PYTHONDONTWRITEBYTECODE"] = "1"
        self.bin_dir = self.tmp / "bin"
        self.project = self.tmp / "project"
        self.project.mkdir()

        # upstream repo with this repo's files, and the user's clone of it
        self.upstream = self.tmp / "upstream"
        self.upstream.mkdir()
        for name in ("skills", "agents"):
            shutil.copytree(REPO / name, self.upstream / name)
        for name in ("install.py", "jdharness.py"):
            shutil.copy2(REPO / name, self.upstream / name)
        self.git(self.upstream, "init", "-q")
        self.commit("initial")
        self.clone = self.tmp / "clone"
        self.run_ok([*GIT, "clone", "-q", str(self.upstream), str(self.clone)])

    def run_ok(self, argv, cwd=None):
        result = subprocess.run(argv, cwd=cwd, env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, f"{argv}\n{result.stdout}\n{result.stderr}")
        return result.stdout

    def git(self, repo, *args):
        return self.run_ok([*GIT, "-C", str(repo), *args]).strip()

    def commit(self, message):
        self.git(self.upstream, "add", "-A")
        self.git(self.upstream, "commit", "-q", "-m", message)

    def jd(self, *args):
        launcher = [sys.executable, str(self.bin_dir / "jdharness.py")] if WINDOWS else [str(self.bin_dir / "jdharness")]
        return self.run_ok([*launcher, *args])

    def install_py(self, *args):
        extra = ["--no-modify-path"] if WINDOWS else []  # never edit the real registry
        return self.run_ok([sys.executable, str(self.clone / "install.py"), "--bin-dir", str(self.bin_dir), *extra, *args])

    def test_full_lifecycle(self):
        skills = sorted(p.parent.name for p in (REPO / "skills").glob("*/SKILL.md"))
        agents = sorted(p.name for p in (REPO / "agents").glob("*.md"))

        # 1. install.py installs the command and points it at the clone
        out = self.install_py()
        self.assertIn("Installed jdharness", out)
        if not WINDOWS:
            self.assertIn(str(self.bin_dir), (self.home / ".bashrc").read_text())

        # 2. jdharness install: real skills in .agents, links in .claude
        out = self.jd("install", "-p", str(self.project), "--claude")
        self.assertIn(f"{len(skills)} skills, {len(agents)} agent(s)", out)
        for skill in skills:
            installed = self.project / ".claude/skills" / skill / "SKILL.md"
            self.assertEqual(installed.read_bytes(), (REPO / "skills" / skill / "SKILL.md").read_bytes())
        for agent in agents:
            self.assertTrue((self.project / ".claude/agents" / agent).is_file())
        manifest = json.loads((self.project / ".agents/.jdharness.json").read_text())
        self.assertEqual(manifest["source"], str(self.clone))
        self.assertEqual(manifest["commit"], self.git(self.clone, "rev-parse", "--short", "HEAD"))

        # 3. upstream ships a new skill and a new jdharness version
        new_skill = self.upstream / "skills/jd-zeta"
        new_skill.mkdir()
        (new_skill / "SKILL.md").write_text("---\nname: jd-zeta\ndescription: test\n---\n")
        script = self.upstream / "jdharness.py"
        script.write_text(re.sub(r'VERSION = "[^"]+"', 'VERSION = "9.9.9"', script.read_text()))
        self.commit("add jd-zeta, bump version")

        # 4. update pulls, replaces jdharness itself, restarts and refreshes the project
        out = self.jd("update", "-p", str(self.project))
        self.assertIn("restarting with the new version", out)
        self.assertIn("jdharness 9.9.9", self.jd("--version"))
        self.assertTrue((self.project / ".claude/skills/jd-zeta/SKILL.md").is_file())
        manifest = json.loads((self.project / ".agents/.jdharness.json").read_text())
        self.assertEqual(manifest["commit"], self.git(self.upstream, "rev-parse", "--short", "HEAD"))
        self.assertEqual(manifest["version"], "9.9.9")

        # 5. a second update is a no-op
        out = self.jd("update", "-p", str(self.project))
        self.assertNotIn("restarting", out)

        # 6. remove deletes the harness from the project
        self.jd("remove", "-p", str(self.project), "-y")
        self.assertEqual(list(self.project.iterdir()), [])

        # 7. install.py --uninstall removes the command, config and PATH block
        self.install_py("--uninstall")
        self.assertEqual(list(self.bin_dir.iterdir()), [])
        if not WINDOWS:
            self.assertNotIn("jdharness", (self.home / ".bashrc").read_text())
            self.assertFalse((self.home / ".config/jdharness").exists())

    def test_install_in_current_directory_and_global(self):
        self.install_py()
        self.run_ok([*([sys.executable, str(self.bin_dir / "jdharness.py")] if WINDOWS
                       else [str(self.bin_dir / "jdharness")]), "install", "--no-claude"], cwd=self.project)
        self.assertTrue((self.project / ".agents/skills").is_dir())
        self.assertFalse((self.project / ".claude").exists())
        self.jd("install", "-p", str(self.home), "--claude")  # -p ~ : all projects
        self.assertTrue((self.home / ".claude/skills/jd-agents/SKILL.md").is_file())


class RepoContentTest(unittest.TestCase):
    """The shipped skills and agent follow the methodology's format."""

    def frontmatter(self, path):
        text = path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"), f"{path} has no frontmatter")
        block = text.split("---\n", 2)[1]
        return dict(line.split(": ", 1) for line in block.splitlines() if ": " in line)

    def test_skills(self):
        skills = sorted((REPO / "skills").glob("*/SKILL.md"))
        self.assertGreater(len(skills), 0)
        for path in skills:
            with self.subTest(skill=path.parent.name):
                meta = self.frontmatter(path)
                self.assertEqual(meta.get("name"), path.parent.name)
                self.assertTrue(meta.get("description"))
                lines = len(path.read_text(encoding="utf-8").splitlines())
                self.assertLessEqual(lines, 80, f"{path.parent.name} has {lines} lines (max 80)")

    def test_agents(self):
        for path in sorted((REPO / "agents").glob("*.md")):
            with self.subTest(agent=path.name):
                meta = self.frontmatter(path)
                self.assertEqual(meta.get("name"), path.stem)
                for key in ("description", "tools", "model"):
                    self.assertTrue(meta.get(key), f"{path.name} has no {key}")


if __name__ == "__main__":
    unittest.main()
