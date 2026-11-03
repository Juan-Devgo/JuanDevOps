#!/usr/bin/env python3
"""Install the jdharness command from this repo.

Linux/macOS: copies it to ~/.local/bin/jdharness and adds that directory to PATH
in your shell profile.
Windows: copies it to %LOCALAPPDATA%\\Programs\\jdharness with jdharness.cmd
(cmd/PowerShell) and jdharness (Git Bash) launchers, and adds that directory to
the user PATH.
"""
import argparse
import os
import shutil
import stat
import sys
from pathlib import Path

if sys.version_info < (3, 8):
    sys.exit("jdharness needs Python 3.8 or newer")

REPO = Path(__file__).resolve().parent
WINDOWS = os.name == "nt"
MARK_START, MARK_END = "# >>> jdharness >>>", "# <<< jdharness <<<"

sys.dont_write_bytecode = True  # keep the repo free of __pycache__
sys.path.insert(0, str(REPO))
import jdharness  # noqa: E402


def default_bin_dir():
    if WINDOWS:
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "Programs" / "jdharness"
    return Path.home() / ".local" / "bin"


def launchers(bin_dir):
    if WINDOWS:
        return [bin_dir / "jdharness.py", bin_dir / "jdharness.cmd", bin_dir / "jdharness"]
    return [bin_dir / "jdharness"]


def install_files(bin_dir):
    bin_dir.mkdir(parents=True, exist_ok=True)
    source = REPO / "jdharness.py"
    if WINDOWS:
        shutil.copyfile(source, bin_dir / "jdharness.py")
        python = sys.executable
        (bin_dir / "jdharness.cmd").write_bytes(
            f'@echo off\r\n"{python}" "%~dp0jdharness.py" %*\r\n'.encode())
        (bin_dir / "jdharness").write_bytes(
            f'#!/bin/sh\nexec "{python.replace(chr(92), "/")}" "$(dirname "$0")/jdharness.py" "$@"\n'.encode())
    else:
        target = bin_dir / "jdharness"
        shutil.copyfile(source, target)
        target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


# --- PATH: Linux/macOS ------------------------------------------------------

def profiles():
    home = Path.home()
    return [home / ".zshrc", home / ".bashrc", home / ".bash_profile", home / ".profile",
            home / ".config" / "fish" / "conf.d" / "jdharness.fish"]


def profile_for_shell():
    shell = Path(os.environ.get("SHELL", "")).name
    home = Path.home()
    if shell == "zsh":
        return home / ".zshrc"
    if shell == "bash":
        return home / (".bash_profile" if sys.platform == "darwin" else ".bashrc")
    if shell == "fish":
        return home / ".config" / "fish" / "conf.d" / "jdharness.fish"
    return home / ".profile"


def on_path(directory):
    def norm(p):
        return os.path.normcase(os.path.normpath(os.path.expanduser(p)))
    return norm(str(directory)) in {norm(p) for p in os.environ.get("PATH", "").split(os.pathsep) if p}


def posix_add_path(bin_dir):
    if on_path(bin_dir):
        return None
    profile = profile_for_shell()
    text = profile.read_text(encoding="utf-8") if profile.exists() else ""
    if MARK_START in text:
        return profile
    if profile.suffix == ".fish":
        line = f'contains "{bin_dir}" $PATH; or set -gx PATH "{bin_dir}" $PATH'
    else:
        line = f'case ":$PATH:" in *":{bin_dir}:"*) ;; *) export PATH="{bin_dir}:$PATH" ;; esac'
    profile.parent.mkdir(parents=True, exist_ok=True)
    separator = "\n" if text and not text.endswith("\n") else ""
    profile.write_text(f"{text}{separator}{MARK_START}\n{line}\n{MARK_END}\n", encoding="utf-8")
    return profile


def posix_remove_path():
    for profile in profiles():
        if not profile.is_file():
            continue
        lines = profile.read_text(encoding="utf-8").splitlines(keepends=True)
        if not any(l.strip() == MARK_START for l in lines):
            continue
        kept, inside = [], False
        for line in lines:
            if line.strip() == MARK_START:
                inside = True
            elif line.strip() == MARK_END:
                inside = False
            elif not inside:
                kept.append(line)
        if profile.suffix == ".fish" and not "".join(kept).strip():
            profile.unlink()
        else:
            profile.write_text("".join(kept), encoding="utf-8")
        print(f"Removed the PATH entry from {profile}")


# --- PATH: Windows ----------------------------------------------------------

def windows_path(bin_dir, add):
    """Add or remove bin_dir in the user PATH. Returns True if it changed."""
    import ctypes
    import winreg

    def norm(p):
        return os.path.normcase(os.path.normpath(os.path.expandvars(p)))

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0,
                        winreg.KEY_READ | winreg.KEY_WRITE) as key:
        try:
            value, kind = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            value, kind = "", winreg.REG_EXPAND_SZ
        parts = [p for p in value.split(";") if p]
        present = any(norm(p) == norm(str(bin_dir)) for p in parts)
        if add == present:
            return False
        parts = parts + [str(bin_dir)] if add else [p for p in parts if norm(p) != norm(str(bin_dir))]
        winreg.SetValueEx(key, "Path", 0, kind, ";".join(parts))
    # tell Explorer and new terminals that the environment changed
    result = ctypes.c_ulong()
    ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment", 0x0002, 5000,
                                             ctypes.byref(result))
    return True


# --- commands ---------------------------------------------------------------

def install(bin_dir, modify_path):
    missing = [n for n in ("skills", "agents", "jdharness.py") if not (REPO / n).exists()]
    if missing:
        sys.exit(f"install.py must run from the cloned JuanDevops repo (missing: {', '.join(missing)})")
    install_files(bin_dir)
    jdharness.write_config({"source": str(REPO), "bin_dir": str(bin_dir)})
    print(f"Installed jdharness in {bin_dir}")
    print(f"Source repo: {REPO} (keep it here; 'jdharness update' pulls it)")

    if not modify_path:
        if not on_path(bin_dir):
            print(f"Add {bin_dir} to your PATH to use the jdharness command.")
    elif WINDOWS:
        if windows_path(bin_dir, add=True):
            print(f"Added {bin_dir} to your user PATH. Open a new terminal.")
    else:
        profile = posix_add_path(bin_dir)
        if profile:
            print(f"Added {bin_dir} to PATH in {profile}. Open a new terminal or run: source \"{profile}\"")
    print("Next: cd into a project and run 'jdharness install' (or 'jdharness --help').")


def uninstall(bin_dir, modify_path):
    for path in launchers(bin_dir):
        if path.exists():
            path.unlink()
            print(f"Removed {path}")
    config = jdharness.config_file()
    if config.exists():
        config.unlink()
        if not any(config.parent.iterdir()):
            config.parent.rmdir()
    if modify_path:
        if WINDOWS:
            if windows_path(bin_dir, add=False):
                print(f"Removed {bin_dir} from your user PATH")
            if bin_dir.is_dir() and not any(bin_dir.iterdir()):
                bin_dir.rmdir()
        else:
            posix_remove_path()
    print("jdharness uninstalled. Harnesses already in projects stay; remove them first with 'jdharness remove'.")


def main():
    parser = argparse.ArgumentParser(description="Install the jdharness command from this repo.")
    parser.add_argument("--bin-dir", type=Path,
                        help=f"where to put jdharness (default: {default_bin_dir()})")
    parser.add_argument("--no-modify-path", action="store_true",
                        help="do not touch PATH or shell profiles")
    parser.add_argument("--uninstall", action="store_true",
                        help="remove the jdharness command, its config and its PATH entry")
    args = parser.parse_args()
    saved = jdharness.read_config().get("bin_dir")
    bin_dir = (args.bin_dir or (Path(saved) if args.uninstall and saved else default_bin_dir()))
    bin_dir = bin_dir.expanduser().resolve()
    try:
        (uninstall if args.uninstall else install)(bin_dir, not args.no_modify_path)
    except OSError as error:
        sys.exit(f"install.py: error: {error}")


if __name__ == "__main__":
    main()
