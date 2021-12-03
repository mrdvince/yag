import argparse
import collections
import configparser
import hashlib
import os
import re
import sys
import zlib

argparser = argparse.ArgumentParser(description="Yet another yag")
argsubparsers = argparser.add_subparsers(title="subcommands", dest="subcommand")
argsubparsers.required = True


class YagRepository:
    worktree = None
    gitdir = None
    conf = None

    def __init__(self, path, force: bool = False):
        self.worktree = path
        self.gitdir = os.path.join(path, ".yag")

        if not (os.path.isdir(self.gitdir) or force):
            raise Exception(f"Not a yag repository {path}")

        self.conf = configparser.ConfigParser()
        cf = repo_file(self, "config")

        if cf and os.path.exists(cf):
            self.conf.read([cf])
        elif not force:
            raise Exception(f"Configuration file missing")

        if not force:
            vers = int(self.conf.get("core", "repositoryformatversion"))
            if vers != 0:
                raise Exception(f"Unsupported repositoryformatversion {vers}")


def repo_path(repo, *path):
    return os.path.join(repo.gitdir, *path)


def repo_file(repo, *path, mkdir=False):
    if repo_dir(repo, *path[:-1], mkdir=mkdir):
        return repo_path(repo, *path)


def repo_dir(repo, *path, mkdir=False):
    path = repo_path(repo, *path)
    if os.path.exists(path):
        if os.path.isdir(path):
            return path
        else:
            raise Exception(f"Not a directory {path}")
    if mkdir:
        os.makedirs(path)
        return path
    else:
        return None


def repo_create(path):
    repo = YagRepository(path, True)
    if os.path.exists(repo.gitdir):
        if not os.path.isdir(repo.gitdir):
            raise Exception(f"{path} is not a directory")
        if os.listdir(repo.gitdir):
            raise Exception(f"{repo.gitdir} not empty")
    else:
        os.makedirs(repo.gitdir)

    assert repo_dir(repo, "branches", mkdir=True)
    assert repo_dir(repo, "objects", mkdir=True)
    assert repo_dir(repo, "refs", "tags", mkdir=True)
    assert repo_dir(repo, "refs", "heads", mkdir=True)

    with open(repo_file(repo, "description"), "w") as f:
        f.write(
            "Unnamed repository; edit this file 'description' to name the repository.\n"
        )
    with open(repo_file(repo, "HEAD"), "w") as f:
        f.write("ref: refs/heads/master\n")

    with open(repo_file(repo, "config"), "w") as f:
        config = repo_default_config()
        config.write(f)

    return repo


def repo_default_config():
    ret = configparser.ConfigParser()

    ret.add_section("core")
    ret.set("core", "repositoryformatversion", "0")
    ret.set("core", "filemode", "false")
    ret.set("core", "bare", "false")

    return ret


argsp = argsubparsers.add_parser("init", help="Initialize a new, empty repository.")
argsp.add_argument(
    "path",
    metavar="directory",
    nargs="?",
    default=".",
    help="Where to create the repository.",
)


def cmd_init(args):
    repo_create(args.path)


def main(argv=sys.argv[1:]):
    args = argparser.parse_args(argv)

    if args.subcommand == "init":
        cmd_init(args)
