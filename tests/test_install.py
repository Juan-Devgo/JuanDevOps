"""Unit tests for install.py. PATH changes are tested on sandboxed profiles and a fake registry."""
import os
import stat
import sys
import types
import unittest
from unittest import mock

from _support import REPO, Sandbox, jdharness

import install  # noqa: E402  (_support puts the repo on sys.path)


class InstallFilesTest(Sandbox):
    @unittest.skipIf(os.name == "nt", "POSIX launcher")
    def test_posix_copies_executable_script(self):
        bin_dir = self.tmp / "bin"
        install.install_files(bin_dir)
        target = bin_dir / "jdharness"
        self.assertEqual(target.read_bytes(), (REPO / "jdharness.py").read_bytes())
        self.assertTrue(target.stat().st_mode & stat.S_IXUSR)
        self.assertTrue(target.read_text().startswith("#!/usr/bin/env python3"))

    def test_windows_writes_script_and_launchers(self):
        bin_dir = self.tmp / "bin"
        with mock.patch.object(install, "WINDOWS", True), \
                mock.patch.object(sys, "executable", r"C:\Python\python.exe"):
            install.install_files(bin_dir)
            self.assertEqual([p.name for p in install.launchers(bin_dir)],
                             ["jdharness.py", "jdharness.cmd", "jdharness"])
        self.assertEqual((bin_dir / "jdharness.py").read_bytes(), (REPO / "jdharness.py").read_bytes())
        cmd = (bin_dir / "jdharness.cmd").read_bytes()
        self.assertEqual(cmd, b'@echo off\r\n"C:\\Python\\python.exe" "%~dp0jdharness.py" %*\r\n')
        sh = (bin_dir / "jdharness").read_text()
        self.assertIn('exec "C:/Python/python.exe" "$(dirname "$0")/jdharness.py" "$@"', sh)


class PosixPathTest(Sandbox):
    def setUp(self):
        super().setUp()
        self.bin_dir = self.tmp / "bin"
        env = mock.patch.dict(os.environ, {"PATH": os.pathsep.join(["/usr/bin", "/bin"])})
        env.start()
        self.addCleanup(env.stop)

    def add(self, shell, platform=None):
        os.environ["SHELL"] = shell
        with mock.patch.object(sys, "platform", platform or sys.platform):
            return install.posix_add_path(self.bin_dir)

    def test_profile_per_shell(self):
        self.assertEqual(self.add("/usr/bin/zsh"), self.home / ".zshrc")
        self.assertEqual(self.add("/bin/bash", "linux"), self.home / ".bashrc")
        self.assertEqual(self.add("/bin/bash", "darwin"), self.home / ".bash_profile")
        self.assertEqual(self.add("/bin/dash"), self.home / ".profile")
        fish = self.add("/usr/bin/fish")
        self.assertEqual(fish, self.home / ".config/fish/conf.d/jdharness.fish")
        self.assertIn(f'set -gx PATH "{self.bin_dir}" $PATH', fish.read_text())

    def test_block_is_added_once_and_keeps_existing_content(self):
        rc = self.home / ".bashrc"
        rc.write_text("alias ll='ls -l'")  # no trailing newline
        self.add("/bin/bash", "linux")
        self.add("/bin/bash", "linux")
        text = rc.read_text()
        self.assertTrue(text.startswith("alias ll='ls -l'\n# >>> jdharness >>>\n"))
        self.assertEqual(text.count(install.MARK_START), 1)
        self.assertIn(f'export PATH="{self.bin_dir}:$PATH"', text)

    def test_nothing_to_do_when_already_on_path(self):
        os.environ["PATH"] = os.pathsep.join([str(self.bin_dir), "/usr/bin"])
        self.assertIsNone(self.add("/bin/bash"))
        self.assertFalse((self.home / ".bashrc").exists())

    def test_remove_strips_only_the_block(self):
        rc = self.home / ".zshrc"
        rc.write_text("export A=1\n")
        self.add("/usr/bin/zsh")
        rc.write_text(rc.read_text() + "export B=2\n")
        fish = self.add("/usr/bin/fish")
        with mock.patch("sys.stdout"):
            install.posix_remove_path()
        self.assertEqual(rc.read_text(), "export A=1\nexport B=2\n")
        self.assertFalse(fish.exists())


class FakeKey:
    def __init__(self, store):
        self.store = store

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def fake_winreg(store):
    def query(key, name):
        if name not in key.store:
            raise FileNotFoundError(name)
        return key.store[name]

    def set_value(key, name, _reserved, kind, value):
        key.store[name] = (value, kind)

    return types.SimpleNamespace(
        HKEY_CURRENT_USER="HKCU", KEY_READ=1, KEY_WRITE=2, REG_SZ=1, REG_EXPAND_SZ=2,
        OpenKey=lambda *a: FakeKey(store), QueryValueEx=query, SetValueEx=set_value)


class WindowsPathTest(Sandbox):
    def setUp(self):
        super().setUp()
        self.store = {"Path": (r"C:\Tools;%USERPROFILE%\bin", 2)}
        self.broadcast = mock.Mock()
        for patch in (mock.patch.dict(sys.modules, {"winreg": fake_winreg(self.store)}),
                      mock.patch("ctypes.windll", types.SimpleNamespace(
                          user32=types.SimpleNamespace(SendMessageTimeoutW=self.broadcast)), create=True)):
            patch.start()
            self.addCleanup(patch.stop)
        self.bin_dir = self.tmp / "bin"

    def test_add_is_idempotent_and_keeps_type(self):
        self.assertTrue(install.windows_path(self.bin_dir, add=True))
        self.assertFalse(install.windows_path(self.bin_dir, add=True))
        value, kind = self.store["Path"]
        self.assertEqual(value, rf"C:\Tools;%USERPROFILE%\bin;{self.bin_dir}")
        self.assertEqual(kind, 2)
        self.assertEqual(self.broadcast.call_count, 1)
        self.assertEqual(self.broadcast.call_args[0][:4], (0xFFFF, 0x001A, 0, "Environment"))

    def test_remove(self):
        install.windows_path(self.bin_dir, add=True)
        self.assertTrue(install.windows_path(self.bin_dir, add=False))
        self.assertEqual(self.store["Path"][0], r"C:\Tools;%USERPROFILE%\bin")
        self.assertFalse(install.windows_path(self.bin_dir, add=False))

    def test_missing_path_value(self):
        self.store.clear()
        self.assertTrue(install.windows_path(self.bin_dir, add=True))
        self.assertEqual(self.store["Path"], (str(self.bin_dir), 2))


class MainTest(Sandbox):
    def main(self, *args):
        with mock.patch.object(sys, "argv", ["install.py", *args]), \
                mock.patch.dict(os.environ, {"PATH": "/usr/bin"}), \
                mock.patch("sys.stdout"):
            install.main()

    def test_default_bin_dir(self):
        expected = (self.home / "AppData/Local/Programs/jdharness" if os.name == "nt"
                    else self.home / ".local/bin")
        self.assertEqual(install.default_bin_dir(), expected)

    @unittest.skipIf(os.name == "nt", "would edit the real user PATH in the registry")
    def test_install_then_uninstall_leaves_nothing(self):
        self.main()
        bin_dir = self.home / ".local/bin"
        self.assertTrue((bin_dir / "jdharness").is_file())
        self.assertEqual(jdharness.read_config(), {"source": str(REPO), "bin_dir": str(bin_dir)})
        self.assertIn(install.MARK_START, (self.home / ".bashrc").read_text())
        self.main("--uninstall")
        self.assertFalse((bin_dir / "jdharness").exists())
        self.assertFalse(jdharness.config_file().exists())
        self.assertNotIn(install.MARK_START, (self.home / ".bashrc").read_text())

    def test_custom_bin_dir_without_path_changes(self):
        bin_dir = self.tmp / "custom"
        self.main("--bin-dir", str(bin_dir), "--no-modify-path")
        self.assertTrue(install.launchers(bin_dir)[0].is_file())
        self.assertFalse((self.home / ".bashrc").exists())
        self.main("--uninstall", "--no-modify-path")  # finds the custom dir in the config
        self.assertFalse(install.launchers(bin_dir)[0].exists())


if __name__ == "__main__":
    unittest.main()
