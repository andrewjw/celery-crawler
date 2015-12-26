import os

from whoosh import index
from whoosh.fields import *

schema = Schema(
    title=TEXT(stored=True),
    url=ID(stored=True, unique=True),
    desc=ID(stored=True),
    rank=NUMERIC(stored=True, numtype=float),
    raw=TEXT,
    content=TEXT)

_ix = None

def get_index():
    global _ix

    if _ix is not None:
        pass
    elif not os.path.exists("indexdir"):
        os.mkdir("indexdir")
        _ix = index.create_in("indexdir", schema)
    else:
        _ix = index.open_dir("indexdir")

    return _ix

def get_writer():
    return get_index().writer()

def get_searcher():
    return get_index().searcher()

def get_last_change():
    get_index() # create directory

    if os.path.exists("indexdir/since.txt"):
        try:
            return int(open("indexdir/since.txt").read())
        except ValueError:
            return 0
    else:
        return 0

def set_last_change(since):
    get_index() # create directory

    open("indexdir/since.txt", "w").write(str(since))
