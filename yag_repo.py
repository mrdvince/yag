from utils import repo_file
import os
import configparser

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