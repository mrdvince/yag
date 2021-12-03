import argparse
import collections
import logging
import os
import sys

from utils import repo_file, repo_dir, repo_default_config
from yag_obj import object_read, object_find, object_write
from yag_repo import YagRepository

argparser = argparse.ArgumentParser(description="Yet another yag")
argsubparsers = argparser.add_subparsers(title="subcommands", dest="subcommand")
argsubparsers.required = True


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


def repo_find(path=".", required=True):
    """Find the point where .yag folder is

    Start at current folder and go up
    the directory till the top most directory in the filesystem
    """
    path = os.path.realpath(path)
    if os.path.isdir(os.path.join(path, ".yag")):
        return YagRepository(path)

    parent = os.path.realpath(os.path.join(path, ".."))
    # if the parent and the current path are at the root not yag folder found
    if parent == path:
        if required:
            raise Exception(f"Not a yag repo")
        else:
            return None
    # recurse
    repo_find(parent, required=required)


argsp = argsubparsers.add_parser("init", help="Initialize a new, empty repository.")
argsp.add_argument(
    "path",
    metavar="directory",
    nargs="?",
    default=".",
    help="Where to create the repository.",
)
# git cat-file TYPE OBJECT
argsp = argsubparsers.add_parser("cat-file",
                                 help="Provide content of repository objects")

argsp.add_argument("type",
                   metavar="type",
                   choices=["blob", "commit", "tag", "tree"],
                   help="Specify the type")

argsp.add_argument("object",
                   metavar="object",
                   help="The object to display")


def cmd_cat_file(args):
    repo = repo_find()
    cat_file(repo, args.object, fmt=args.type.encode())


def cat_file(repo, obj, fmt=None):
    obj = object_read(repo, object_find(repo, obj, fmt=fmt))
    sys.stdout.buffer.write(obj.serialize())


# git hash-object [-w] [-t TYPE] FILE
argsp = argsubparsers.add_parser(
    "hash-object",
    help="Compute object ID and optionally creates a blob from a file")

argsp.add_argument("-t",
                   metavar="type",
                   dest="type",
                   choices=["blob", "commit", "tag", "tree"],
                   default="blob",
                   help="Specify the type")

argsp.add_argument("-w",
                   dest="write",
                   action="store_true",
                   help="Actually write the object into the database")

argsp.add_argument("path",
                   help="Read object from <file>")


def cmd_hash_object(args):
    if args.write:
        repo = YagRepository(".")
    else:
        repo = None

    with open(args.path, 'rb') as f:
        sha = object_hash(f, args.type.encode(), repo)
        logging.info(sha)


def object_hash(f, fmt, repo=None):
    data = f.read()
    # Choose constructor depending on
    # object type found in header.
    if fmt == b'commit':
        obj = GitCommit(repo, data)
    elif fmt == b'tree':
        obj = GitTree(repo, data)
    elif fmt == b'tag':
        obj = GitTag(repo, data)
    elif fmt == b'blob':
        obj = GitBlob(repo, data)
    else:
        raise Exception("Unknown type %s!" % fmt)
    return object_write(obj, repo)


def kvlm_parse(raw, start=0, dct=None):
    """Key value list message

    """
    if not dct:
        dct = collections.OrderedDict()
    # Next space and line
    spc = raw.find(b' ', start)
    n_line = raw.find(b'\n', start)

    # If space appears before new line, that's a keyword
    # Base case
    # =========
    # If newline appears first (or there's no space at all, in which
    # case find returns -1), we assume a blank line.  A blank line
    # means the remainder of the data is the message.
    if (spc < 0) or (n_line < spc):
        assert n_line == start

def cmd_init(args):
    repo_create(args.path)


def main(argv=sys.argv[1:]):
    args = argparser.parse_args(argv)

    if args.subcommand == "init":
        cmd_init(args)
