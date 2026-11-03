"""Unit and in-process tests for jdharness.py."""
import json
import os
import shutil
import unittest
from unittest import mock

from _support import AGENT, SKILLS, VAULT_AGENT, VAULT_TEXT, Sandbox, add_vault_agent, jdharness, make_source

ITEMS = [f"skills/{s}" for s in SKILLS] + [f"agents/{AGENT}"]


class InstallTest(Sandbox):
    def test_copies_skills_and_agents_into_agents_dir(self):
        self.install("--no-claude")
        for skill in SKILLS:
            self.assertEqual((self.project / ".agents/skills" / skill / "SKILL.md").read_text(), f"# {skill}\n")
        self.assertTrue((self.project / ".agents/agents" / AGENT).is_file())
        self.assertFalse((self.project / ".claude").exists())

    def test_ignores_dirs_without_skill_md_and_non_markdown_agents(self):
        self.install("--no-claude")
        self.assertFalse((self.project / ".agents/skills/notes").exists())
        self.assertFalse((self.project / ".agents/agents/readme.txt").exists())
        self.assertEqual(self.manifest()["items"], ITEMS)

    def test_claude_links_point_to_agents_dir(self):
        self.install("--claude")
        manifest = self.manifest()
        self.assertTrue(manifest["claude"])
        self.assertEqual(sorted(manifest["links"]), sorted(ITEMS))
        for rel in ITEMS:
            link, target = self.project / ".claude" / rel, self.project / ".agents" / rel
            if manifest["links"][rel] == "symlink":
                self.assertTrue(link.is_symlink())
                self.assertEqual(link.resolve(), target.resolve())
                self.assertFalse(os.path.isabs(os.readlink(link)), "symlinks must be relative")
        # editing the source of truth is visible through .claude
        (self.project / ".agents/skills/jd-alpha/SKILL.md").write_text("edited\n")
        if manifest["links"]["skills/jd-alpha"] != "copy":
            self.assertEqual((self.project / ".claude/skills/jd-alpha/SKILL.md").read_text(), "edited\n")

    def test_manifest_records_source_and_version(self):
        self.install("--no-claude")
        manifest = self.manifest()
        self.assertEqual(manifest["source"], str(self.src))
        self.assertEqual(manifest["version"], jdharness.VERSION)
        self.assertIsNone(manifest["commit"])  # source is not a git repo

    def test_prompt_defaults_to_claude_when_not_interactive(self):
        self.install()
        self.assertTrue(self.manifest()["claude"])

    def test_prompt_answer_no_skips_claude(self):
        code, _, err = self.cli("install", "-p", str(self.project), "--source", str(self.src),
                                tty=True, answers=["maybe", "n"])
        self.assertEqual(code, 0, err)
        self.assertFalse(self.manifest()["claude"])
        self.assertFalse((self.project / ".claude").exists())

    def test_prompt_empty_answer_uses_default_yes(self):
        code, _, err = self.cli("install", "-p", str(self.project), "--source", str(self.src),
                                tty=True, answers=[""])
        self.assertEqual(code, 0, err)
        self.assertTrue(self.manifest()["claude"])

    def test_reinstall_is_idempotent(self):
        self.install("--claude")
        first = self.manifest()
        self.install("--claude")
        self.assertEqual(self.manifest(), first)

    def test_keeps_unrelated_files(self):
        (self.project / ".agents/skills/mine").mkdir(parents=True)
        (self.project / ".claude/skills/other").mkdir(parents=True)
        (self.project / ".claude/settings.json").write_text("{}")
        self.install("--claude")
        self.assertTrue((self.project / ".agents/skills/mine").is_dir())
        self.assertTrue((self.project / ".claude/skills/other").is_dir())
        self.assertEqual((self.project / ".claude/settings.json").read_text(), "{}")

    def test_conflict_in_agents_dir_stops_without_changes(self):
        mine = self.project / ".agents/skills/jd-alpha/SKILL.md"
        mine.parent.mkdir(parents=True)
        mine.write_text("mine\n")
        code, _, err = self.cli("install", "-p", str(self.project), "--source", str(self.src), "--no-claude")
        self.assertEqual(code, 1)
        self.assertIn("--force", err)
        self.assertEqual(mine.read_text(), "mine\n")
        self.assertIsNone(self.manifest())

    def test_conflict_in_claude_dir_stops(self):
        (self.project / ".claude/agents").mkdir(parents=True)
        (self.project / ".claude/agents" / AGENT).write_text("mine\n")
        code, _, err = self.cli("install", "-p", str(self.project), "--source", str(self.src), "--claude")
        self.assertEqual(code, 1)
        self.assertIn(AGENT, err)

    def test_force_replaces_conflicts(self):
        mine = self.project / ".agents/skills/jd-alpha/SKILL.md"
        mine.parent.mkdir(parents=True)
        mine.write_text("mine\n")
        self.install("--no-claude", "--force")
        self.assertEqual(mine.read_text(), "# jd-alpha\n")

    def test_missing_project_dir_fails(self):
        code, _, err = self.cli("install", "-p", str(self.tmp / "nope"), "--source", str(self.src))
        self.assertEqual(code, 1)
        self.assertIn("not a directory", err)


class SourceTest(Sandbox):
    def test_invalid_explicit_source_fails(self):
        code, _, err = self.cli("install", "-p", str(self.project), "--source", str(self.tmp))
        self.assertEqual(code, 1)
        self.assertIn("not a JuanDevops repo", err)

    def test_source_from_env(self):
        os.environ["JDHARNESS_SOURCE"] = str(self.src)
        code, _, err = self.cli("install", "-p", str(self.project), "--no-claude")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.manifest()["source"], str(self.src))

    def test_source_from_config_written_by_install_py(self):
        jdharness.write_config({"source": str(self.src)})
        self.assertIn(str(self.home), str(jdharness.config_file()))
        code, _, err = self.cli("install", "-p", str(self.project), "--no-claude")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.manifest()["source"], str(self.src))

    def test_empty_source_fails(self):
        empty = self.tmp / "empty"
        (empty / "skills").mkdir(parents=True)
        (empty / "agents").mkdir()
        code, _, err = self.cli("install", "-p", str(self.project), "--source", str(empty))
        self.assertEqual(code, 1)
        self.assertIn("no skills or agents", err)


class UpdateTest(Sandbox):
    def update(self, *extra):
        return self.cli("update", "-p", str(self.project), "--no-pull", *extra)

    def test_without_harness_fails(self):
        code, _, err = self.update()
        self.assertEqual(code, 1)
        self.assertIn("jdharness install", err)

    def test_adds_new_and_drops_removed_items(self):
        self.install("--claude")
        shutil.rmtree(self.src / "skills/jd-beta")
        make_source(self.tmp / "extra", skills=("jd-gamma",), agents=())
        shutil.copytree(self.tmp / "extra/skills/jd-gamma", self.src / "skills/jd-gamma")
        code, _, err = self.update()
        self.assertEqual(code, 0, err)
        self.assertFalse((self.project / ".agents/skills/jd-beta").exists())
        self.assertFalse(os.path.lexists(self.project / ".claude/skills/jd-beta"))
        self.assertTrue((self.project / ".claude/skills/jd-gamma/SKILL.md").is_file())
        self.assertIn("skills/jd-gamma", self.manifest()["items"])

    def test_repo_overwrites_local_edits_in_agents(self):
        self.install("--no-claude")
        local = self.project / ".agents/agents" / AGENT
        local.write_text("local edit\n")
        (self.src / "agents" / AGENT).write_text("new upstream\n")
        self.assertEqual(self.update()[0], 0)
        self.assertEqual(local.read_text(), "new upstream\n")

    def test_keeps_claude_choice_from_manifest(self):
        self.install("--claude")
        self.assertEqual(self.update()[0], 0)
        self.assertTrue(self.manifest()["claude"])
        self.assertTrue((self.project / ".claude/skills/jd-alpha").exists())

    def test_no_claude_removes_links_and_prunes_claude_dir(self):
        self.install("--claude")
        self.assertEqual(self.update("--no-claude")[0], 0)
        self.assertFalse((self.project / ".claude").exists())
        self.assertEqual(self.manifest()["links"], {})

    def test_claude_flag_adds_links_later(self):
        self.install("--no-claude")
        self.assertEqual(self.update("--claude")[0], 0)
        self.assertTrue((self.project / ".claude/agents" / AGENT).exists())

    def test_falls_back_to_manifest_source(self):
        self.install("--no-claude")
        code, _, err = self.update()  # no --source, no config, no env
        self.assertEqual(code, 0, err)

    def test_pull_skipped_for_non_git_source(self):
        self.install("--no-claude")
        code, out, err = self.cli("update", "-p", str(self.project))
        self.assertEqual(code, 0, err)
        self.assertIn("skipping pull", out)


class RemoveTest(Sandbox):
    def test_removes_everything_it_installed(self):
        self.install("--claude")
        code, out, err = self.cli("remove", "-p", str(self.project), "-y")
        self.assertEqual(code, 0, err)
        self.assertFalse((self.project / ".agents").exists())
        self.assertFalse((self.project / ".claude").exists())
        self.assertTrue((self.src / "skills/jd-alpha/SKILL.md").is_file(), "source must stay intact")

    def test_keeps_unrelated_files(self):
        self.install("--claude")
        (self.project / ".claude/settings.json").write_text("{}")
        (self.project / ".agents/skills/mine").mkdir()
        self.assertEqual(self.cli("remove", "-p", str(self.project), "-y")[0], 0)
        self.assertTrue((self.project / ".claude/settings.json").is_file())
        self.assertTrue((self.project / ".agents/skills/mine").is_dir())
        self.assertFalse((self.project / ".agents/skills/jd-alpha").exists())

    def test_aliases(self):
        for alias in ("delete", "uninstall"):
            self.install("--claude")
            self.assertEqual(self.cli(alias, "-p", str(self.project), "-y")[0], 0)
            self.assertIsNone(self.manifest())

    def test_cancels_without_confirmation(self):
        self.install("--no-claude")
        code, out, _ = self.cli("remove", "-p", str(self.project))  # not a tty: default is no
        self.assertEqual(code, 0)
        self.assertIn("Cancelled", out)
        self.assertIsNotNone(self.manifest())

    def test_confirmation_yes(self):
        self.install("--no-claude")
        code, _, _ = self.cli("remove", "-p", str(self.project), tty=True, answers=["y"])
        self.assertEqual(code, 0)
        self.assertIsNone(self.manifest())

    def test_without_harness_fails(self):
        self.assertEqual(self.cli("remove", "-p", str(self.project), "-y")[0], 1)

    @unittest.skipIf(os.name == "nt", "symlink replacement scenario is POSIX-only")
    def test_never_deletes_real_dir_that_replaced_a_link(self):
        self.install("--claude")
        link = self.project / ".claude/skills/jd-alpha"
        link.unlink()
        link.mkdir()
        (link / "SKILL.md").write_text("mine\n")
        self.assertEqual(self.cli("remove", "-p", str(self.project), "-y")[0], 0)
        self.assertEqual((link / "SKILL.md").read_text(), "mine\n")


class StatusAndCliTest(Sandbox):
    def test_status(self):
        self.assertEqual(self.cli("status", "-p", str(self.project))[0], 1)
        self.install("--claude")
        code, out, _ = self.cli("status", "-p", str(self.project))
        self.assertEqual(code, 0)
        self.assertIn("2 skills, 1 agent(s)", out)
        self.assertIn(f"{len(ITEMS)} links", out)

    def test_no_command_prints_help(self):
        code, out, _ = self.cli()
        self.assertEqual(code, 1)
        self.assertIn("install", out)

    def test_version(self):
        code, out, _ = self.cli("--version")
        self.assertEqual(code, 0)
        self.assertIn(jdharness.VERSION, out)

    def test_corrupt_manifest(self):
        (self.project / ".agents").mkdir()
        (self.project / ".agents" / jdharness.MANIFEST).write_text("{nope")
        code, _, err = self.cli("status", "-p", str(self.project))
        self.assertEqual(code, 1)
        self.assertIn("corrupt", err)


class WindowsFallbackTest(Sandbox):
    """Simulate Windows without symlink privilege on any OS."""

    def setUp(self):
        super().setUp()
        for patch in (mock.patch.object(jdharness, "WINDOWS", True),
                      mock.patch("os.symlink", side_effect=OSError("privilege not held"))):
            patch.start()
            self.addCleanup(patch.stop)

    def test_junction_for_dirs(self):
        target = self.src / "skills/jd-alpha"
        with mock.patch("subprocess.run", return_value=mock.Mock(returncode=0)) as run:
            self.assertEqual(jdharness.make_link(target, self.tmp / "link"), "junction")
        self.assertEqual(run.call_args[0][0][:4], ["cmd", "/c", "mklink", "/J"])

    def test_hardlink_for_files_and_copy_when_junction_fails(self):
        with mock.patch("subprocess.run", side_effect=FileNotFoundError("cmd")):
            self.install("--claude")
        links = self.manifest()["links"]
        self.assertEqual(links[f"agents/{AGENT}"], "hardlink")
        self.assertEqual(links["skills/jd-alpha"], "copy")
        self.assertTrue((self.project / ".claude/skills/jd-alpha/SKILL.md").is_file())

    def test_report_warns_about_copies_and_update_refreshes_them(self):
        with mock.patch("subprocess.run", return_value=mock.Mock(returncode=1)):
            out = self.install("--claude")
            self.assertIn("copies", out)
            (self.src / "skills/jd-alpha/SKILL.md").write_text("v2\n")
            self.assertEqual(self.cli("update", "-p", str(self.project), "--no-pull")[0], 0)
        self.assertEqual((self.project / ".claude/skills/jd-alpha/SKILL.md").read_text(), "v2\n")


class VaultTest(Sandbox):
    """Agents with {{OBSIDIAN_VAULT}} get the vault from install.py, or are skipped without one."""

    def setUp(self):
        super().setUp()
        add_vault_agent(self.src)
        self.vault = self.tmp / "My Vault"
        self.vault.mkdir()

    def set_vault(self, vault):
        jdharness.write_config({"source": str(self.src), "vault": vault and str(vault)})

    def test_without_vault_skips_agents_that_need_it(self):
        out = self.install("--claude")
        self.assertNotIn(f"agents/{VAULT_AGENT}", self.manifest()["items"])
        self.assertFalse((self.project / ".agents/agents" / VAULT_AGENT).exists())
        self.assertFalse(os.path.lexists(self.project / ".claude/agents" / VAULT_AGENT))
        self.assertTrue((self.project / ".agents/agents" / AGENT).is_file())
        self.assertIsNone(self.manifest()["vault"])
        self.assertIn("Obsidian Vault: none", out)

    def test_vault_path_is_written_into_the_agent(self):
        self.set_vault(self.vault)
        out = self.install("--claude")
        installed = self.project / ".claude/agents" / VAULT_AGENT
        self.assertEqual(installed.read_text(), f"Vault: `{self.vault}`\n")
        self.assertEqual(self.manifest()["vault"], str(self.vault))
        self.assertIn(f"Obsidian Vault: {self.vault}", out)
        self.assertEqual((self.src / "agents" / VAULT_AGENT).read_text(), VAULT_TEXT, "source must keep the token")

    def test_update_follows_vault_changes(self):
        self.set_vault(self.vault)
        self.install("--claude")
        other = self.tmp / "other"
        other.mkdir()
        self.set_vault(other)
        self.assertEqual(self.cli("update", "-p", str(self.project), "--no-pull")[0], 0)
        self.assertIn(str(other), (self.project / ".agents/agents" / VAULT_AGENT).read_text())
        self.set_vault(None)
        self.assertEqual(self.cli("update", "-p", str(self.project), "--no-pull")[0], 0)
        self.assertFalse((self.project / ".agents/agents" / VAULT_AGENT).exists())
        self.assertFalse(os.path.lexists(self.project / ".claude/agents" / VAULT_AGENT))
        self.assertIsNone(self.manifest()["vault"])


class ConfigTest(Sandbox):
    def test_roundtrip_and_missing(self):
        self.assertEqual(jdharness.read_config(), {})
        jdharness.write_config({"source": "x"})
        self.assertEqual(jdharness.read_config(), {"source": "x"})
        self.assertEqual(json.loads(jdharness.config_file().read_text()), {"source": "x"})

    def test_corrupt_config_is_ignored(self):
        jdharness.config_file().parent.mkdir(parents=True)
        jdharness.config_file().write_text("{nope")
        self.assertEqual(jdharness.read_config(), {})


if __name__ == "__main__":
    unittest.main()
