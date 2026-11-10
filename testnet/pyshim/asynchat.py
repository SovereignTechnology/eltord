"""Import-only stand-in for asynchat, removed from Python 3.12 (see asyncore.py here)."""
import asyncore


class async_chat(asyncore.dispatcher):
    pass
