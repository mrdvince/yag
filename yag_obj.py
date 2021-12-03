import hashlib
import logging
import zlib
from typing import Any

from utils import repo_file

class YagObject:
    repo = None

    def __init__(self, repo, data=None):
        self.repo = repo
        if data is not None:
            self.deserialize(data)

    def deserialize(self, data):
        raise NotImplementedError("deserialize not implemented")

    def serialize(self):
        """This function MUST be implemented by subclasses.

        It must read the object's contents from self.data, a byte string, and do
        whatever it takes to convert it into a meaningful representation.
        What exactly that means depend on each subclass.
        """

        raise NotImplementedError("serialize not implemented")


class YagBlob(YagObject):
    fmt = b"blob"

    def deserialize(self, data):
        self.blobdata = data

    def serialize(self):
        return self.blobdata


def object_read(repo, sha):
    """Read object from yag repo.

    Returns a yag object whose exact type depends on the object.
    """
    path = repo_file(repo, "objects", sha[:2], sha[2:])

    with open(path, "rb") as f:
        raw = zlib.decompress(f.read())

        # Object type
        x = raw.find(b" ")
        logging.info(x)
        fmt = raw[0:x]
        logging.info(fmt)

        # Read and validate object type
        y = raw.find(b"\x00", x)
        size = int(raw[x:y].decode("ascii"))
        if size != len(raw) - y - 1:
            raise Exception(f"Malformed object {sha}")
        # Pick constructor
        if fmt == b"commit":
            c = GitCommit
        elif fmt == b"tree":
            c = GitTree
        elif fmt == b"tag":
            c = GitTag
        elif fmt == b"blob":
            c = GitBlob
        else:
            raise Exception(
                "Unknown type {0} for object {1}".format(fmt.decode("ascii"), sha)
            )
    return c(repo, raw[y + 1:])


def object_find(repo, name, fmt=None, follow=True):
    return name


def object_write(obj: YagBlob, write=True):
    # Serialize obj
    data = obj.serialize()
    # Add header
    result: Any = obj.fmt + b' ' + str(len(data)).encode() + b'\x00' + data
    # Hash
    sha = hashlib.sha1(result).hexdigest()
    if write:
        # Path
        path = repo_file(obj.repo, "objects", sha[0:2], sha[2:], mkdir=write)
        with open(path, 'wb') as f:
            # Compress and write
            f.write(zlib.compress(result))
    return sha

