#!/usr/bin/env python3
"""jdharness: install, update or remove the JuanDevops harness in a project.

The harness lives in <path>/.agents (source of truth). Optionally, <path>/.claude
gets links to it so Claude Code loads the skills and the subagent.
"""
import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

VERSION = "1.0.0"
MANIFEST = ".jdharness.json"
WINDOWS = os.name == "nt"
PRUNE = (".agents/skills", ".agents/agents", ".agents", ".claude/skills", ".claude/agents", ".claude")
VAULT_TOKEN = b"{{OBSIDIAN_VAULT}}"  # replaced with the vault path; files with it need a vault


def die(message):
    print(f"jdharness: error: {message}", file=sys.stderr)
    sys.exit(1)


def ask(question, default):
    if not sys.stdin.isatty():
        return default
    hint = "[Y/n]" if default else "[y/N]"
    while True:
        answer = input(f"{question} {hint} ").strip().lower()
        if not answer:
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False


# --- config (written by install.py) -----------------------------------------

def config_file():
    if WINDOWS:
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "jdharness" / "config.json"


def read_config():
    try:
        return json.loads(config_file().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def write_config(data):
    path = config_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def read_vault():
    """Obsidian Vault path chosen in install.py, or None for no Obsidian."""
    return read_config().get("vault") or None


# --- source repo ------------------------------------------------------------

def is_source(path):
    return (path / "skills").is_dir() and (path / "agents").is_dir()


def find_source(explicit, manifest=None):
    candidates = []
    if explicit:
        candidates.append(("--source", explicit, True))
    if os.environ.get("JDHARNESS_SOURCE"):
        candidates.append(("JDHARNESS_SOURCE", os.environ["JDHARNESS_SOURCE"], True))
    if read_config().get("source"):
        candidates.append((str(config_file()), read_config()["source"], False))
    if manifest and manifest.get("source"):
        candidates.append(("manifest", manifest["source"], False))
    candidates.append(("script dir", str(Path(__file__).resolve().parent), False))
    for origin, raw, strict in candidates:
        path = Path(raw).expanduser().resolve()
        if is_source(path):
            return path
        if strict:
            die(f"{origin}: {path} is not a JuanDevops repo (needs skills/ and agents/)")
    die("JuanDevops repo not found. Run install.py from the cloned repo or pass --source.")


def needs_vault(path):
    return path.is_file() and VAULT_TOKEN in path.read_bytes()


def source_items(src, vault):
    items = ["skills/" + d.name for d in sorted((src / "skills").iterdir()) if (d / "SKILL.md").is_file()]
    items += ["agents/" + f.name for f in sorted((src / "agents").glob("*.md")) if vault or not needs_vault(f)]
    if not items:
        die(f"no skills or agents found in {src}")
    return items


def git(src, *args):
    if not (src / ".git").exists() or shutil.which("git") is None:
        return None
    result = subprocess.run(["git", "-C", str(src), *args], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


# --- filesystem -------------------------------------------------------------

def is_link(path):
    if path.is_symlink():
        return True
    if WINDOWS:  # junctions are reparse points but not symlinks
        try:
            return bool(getattr(os.lstat(path), "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)
        except OSError:
            return False
    return False


def lexists(path):
    return path.exists() or is_link(path)


def remove(path):
    if is_link(path):
        if WINDOWS:
            try:
                os.rmdir(path)  # directory symlink or junction: removes only the link
            except OSError:
                os.unlink(path)
        else:
            path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def remove_link(path, kind):
    # never delete a real directory that replaced one of our links
    if kind in ("symlink", "junction") and not is_link(path):
        return
    remove(path)


def copy(src, dst):
    if src.is_dir():
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)


def copy_item(src, dst, vault):
    if vault and needs_vault(src):
        dst.write_bytes(src.read_bytes().replace(VAULT_TOKEN, vault.encode("utf-8")))
    else:
        copy(src, dst)


def make_link(target, link):
    """Create link -> target and return the kind used."""
    is_dir = target.is_dir()
    try:
        os.symlink(os.path.relpath(target, link.parent), link, target_is_directory=is_dir)
        return "symlink"
    except (OSError, NotImplementedError):
        if not WINDOWS:
            raise
    # Windows without symlink privilege (no Developer Mode, not admin)
    if is_dir:
        try:
            result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True)
            if result.returncode == 0:
                return "junction"
        except OSError:
            pass
    else:
        try:
            os.link(target, link)
            return "hardlink"
        except OSError:
            pass
    copy(target, link)
    return "copy"


def prune(project):
    for rel in PRUNE:
        path = project / rel
        if path.is_dir() and not is_link(path) and not any(path.iterdir()):
            path.rmdir()


# --- harness ----------------------------------------------------------------

def read_manifest(project):
    path = project / ".agents" / MANIFEST
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        die(f"{path} is corrupt; delete it and run install --force")


def sync(project, src, claude, force):
    agents, claude_dir = project / ".agents", project / ".claude"
    old = read_manifest(project) or {}
    owned, old_links = set(old.get("items", [])), old.get("links", {})
    vault = read_vault()
    items = source_items(src, vault)

    if not force:
        conflicts = [agents / i for i in items if i not in owned and lexists(agents / i)]
        if claude:
            conflicts += [claude_dir / i for i in items if i not in old_links and lexists(claude_dir / i)]
        if conflicts:
            die("these paths exist and were not installed by jdharness (use --force to replace them):\n  "
                + "\n  ".join(map(str, conflicts)))

    # links are always recreated; items removed upstream are dropped
    for rel, kind in old_links.items():
        remove_link(claude_dir / rel, kind)
    for rel in owned - set(items):
        remove(agents / rel)

    for rel in items:
        dst = agents / rel
        remove(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        copy_item(src / rel, dst, vault)

    links = {}
    if claude:
        for rel in items:
            link = claude_dir / rel
            remove(link)
            link.parent.mkdir(parents=True, exist_ok=True)
            links[rel] = make_link(agents / rel, link)

    manifest = {"version": VERSION, "source": str(src), "commit": git(src, "rev-parse", "--short", "HEAD"),
                "claude": claude, "vault": vault, "items": items, "links": links}
    (agents / MANIFEST).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    prune(project)
    return manifest


def report(project, manifest):
    items = manifest["items"]
    skills = sum(i.startswith("skills/") for i in items)
    print(f"Harness: {skills} skills, {len(items) - skills} agent(s) in {project / '.agents'}")
    if manifest["claude"]:
        kinds = ", ".join(sorted(set(manifest["links"].values())))
        print(f"Claude Code: {len(manifest['links'])} links in {project / '.claude'} ({kinds})")
        if "copy" in kinds:
            print("  Links were not possible, so .claude has copies: run 'jdharness update' after editing .agents.")
    else:
        print("Claude Code: not linked (run with --claude to add .claude)")
    if manifest.get("vault"):
        print(f"Obsidian Vault: {manifest['vault']}")
    else:
        print("Obsidian Vault: none, so jd-obsidian-sync is not installed (run install.py to add a vault)")
    source = manifest["source"] + (f" @ {manifest['commit']}" if manifest.get("commit") else "")
    print(f"Source: {source}")


def project_dir(args):
    path = Path(args.path).expanduser().resolve()
    if not path.is_dir():
        die(f"{path} is not a directory")
    return path


def cmd_install(args):
    project = project_dir(args)
    src = find_source(args.source)
    claude = args.claude
    if claude is None:
        claude = ask("Add a .claude directory for Claude Code (links to .agents)?", default=True)
    report(project, sync(project, src, claude, args.force))


def cmd_update(args):
    project = project_dir(args)
    manifest = read_manifest(project)
    if manifest is None:
        die(f"no harness in {project}. Run: jdharness install -p \"{project}\"")
    src = find_source(args.source, manifest)
    if not args.no_pull:
        if git(src, "rev-parse", "--git-dir") is None:
            print(f"{src} is not a git repo (or git is missing); skipping pull")
        else:
            print(f"Pulling {src}", flush=True)
            if subprocess.run(["git", "-C", str(src), "pull", "--ff-only"]).returncode:
                die("git pull failed; fix the repo or run with --no-pull")
        self_update(src)
    claude = manifest.get("claude", False) if args.claude is None else args.claude
    report(project, sync(project, src, claude, args.force))


def self_update(src):
    new, me = src / "jdharness.py", Path(__file__).resolve()
    if not new.is_file() or new.resolve() == me or new.read_bytes() == me.read_bytes():
        return
    shutil.copyfile(new, me)
    print(f"Updated {me}; restarting with the new version", flush=True)
    sys.exit(subprocess.run([sys.executable, str(me), *sys.argv[1:], "--no-pull"]).returncode)


def cmd_remove(args):
    project = project_dir(args)
    manifest = read_manifest(project)
    if manifest is None:
        die(f"no harness in {project}")
    if not args.yes and not ask(f"Remove the JuanDevops harness from {project}?", default=False):
        print("Cancelled (use -y to skip the question).")
        return
    for rel, kind in manifest.get("links", {}).items():
        remove_link(project / ".claude" / rel, kind)
    for rel in manifest.get("items", []):
        remove(project / ".agents" / rel)
    (project / ".agents" / MANIFEST).unlink()
    prune(project)
    print(f"Removed the harness from {project}")


def cmd_status(args):
    project = project_dir(args)
    manifest = read_manifest(project)
    if manifest is None:
        print(f"No harness in {project}")
        sys.exit(1)
    report(project, manifest)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="jdharness",
        description="Install, update or remove the JuanDevops harness. It lives in <path>/.agents; "
                    "<path>/.claude can link to it for Claude Code.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    sub = parser.add_subparsers(dest="command", metavar="command")

    def add(name, func, help, aliases=(), source=True, claude=True):
        sp = sub.add_parser(name, help=help, aliases=list(aliases))
        sp.set_defaults(func=func)
        sp.add_argument("-p", "--path", default=".", help="project directory (default: current directory)")
        if source:
            sp.add_argument("--source", help="JuanDevops repo to install from (default: the one install.py ran from)")
        if claude:
            group = sp.add_mutually_exclusive_group()
            group.add_argument("--claude", dest="claude", action="store_const", const=True,
                               help="link .claude to .agents without asking")
            group.add_argument("--no-claude", dest="claude", action="store_const", const=False,
                               help="do not create (or remove) the .claude links")
            sp.add_argument("-f", "--force", action="store_true",
                            help="replace existing paths that jdharness did not install")
        return sp

    add("install", cmd_install, "install the harness in a project")
    update = add("update", cmd_update, "pull the repo and refresh the harness")
    update.add_argument("--no-pull", action="store_true", help="refresh from the local repo without git pull")
    remove_cmd = add("remove", cmd_remove, "delete the harness from a project", ("delete", "uninstall"),
                     source=False, claude=False)
    remove_cmd.add_argument("-y", "--yes", action="store_true", help="do not ask for confirmation")
    add("status", cmd_status, "show what is installed", source=False, claude=False)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 1
    try:
        args.func(args)
    except KeyboardInterrupt:
        print()
        return 130
    except OSError as error:
        die(str(error))
    return 0


if __name__ == "__main__":
    sys.exit(main())
