"""
Sync the local udmabuf-import working tree to the target
========================================================

Tars the local repository working tree (excluding VCS and build artifacts),
uploads it over the cijoe transport, and extracts it to the configured
``udmabuf.repository.path`` on the target.

This is used instead of a git clone (``core.repository_prep``) so that the
uncommitted ``module/`` and ``debian/`` packaging under development is what
gets built and validated, rather than whatever is on the upstream branch.

Run cijoe from the repository root; ``--src`` defaults to the current working
directory.

Retargetable: True
------------------
"""

from argparse import ArgumentParser
from pathlib import Path

REMOTE_TAR = "/tmp/udmabuf_import_worktree.tar.gz"
LOCAL_TAR = "/tmp/udmabuf_import_worktree.local.tar.gz"

EXCLUDES = [
    ".git",
    "cijoe-output",
    "cijoe-archive",
    "*.o",
    "*.ko",
    "*.deb",
    "*.mod",
    "*.mod.c",
    "udmabuf_import_cpu",
    "udmabuf_import_gpu",
]


def add_args(parser: ArgumentParser):
    parser.add_argument(
        "--src",
        type=str,
        default=None,
        help="local repo root to sync (default: current working directory)",
    )


def main(args, cijoe):
    dst = cijoe.getconf("udmabuf.repository.path")
    if not dst:
        print("error: missing config key 'udmabuf.repository.path'")
        return 1

    src = Path(args.src).resolve() if args.src else Path.cwd()
    if not (src / "module" / "udmabuf_import.c").is_file():
        print(f"error: {src} does not look like the udmabuf-import repo root")
        return 1

    excludes = " ".join(f"--exclude='{pat}'" for pat in EXCLUDES)
    err, _ = cijoe.run_local(f"tar czf {LOCAL_TAR} {excludes} -C '{src}' .")
    if err:
        return 1

    cijoe.put(LOCAL_TAR, REMOTE_TAR)

    err, _ = cijoe.run(
        f"rm -rf '{dst}' && mkdir -p '{dst}' && "
        f"tar xzf {REMOTE_TAR} -C '{dst}' && rm -f {REMOTE_TAR} && "
        f"ls '{dst}/module' '{dst}/debian'"
    )
    return 1 if err else 0
