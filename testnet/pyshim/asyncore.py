"""Import-only stand-in for asyncore, removed from Python 3.12.

el-tor's chutney fork imports chutney.Traffic (asyncore/asynchat) when TorNet loads, so every chutney command
fails on Python >= 3.12. labctl puts this directory on chutney's PYTHONPATH only on those versions, so
`configure`, `start`, `status` and `stop` work. Chutney's own traffic verifier needs the real modules and is
not used by labctl (it has its own origin and curl checks).
"""


class dispatcher:
    def __init__(self, *args, **kwargs):
        raise RuntimeError("asyncore stub: chutney's traffic verifier is unavailable on Python >= 3.12")


def loop(*args, **kwargs):
    raise RuntimeError("asyncore stub: chutney's traffic verifier is unavailable on Python >= 3.12")
