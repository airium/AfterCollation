from configs.user import USER_PATHS
from pathlib import Path
import sys
import os

__all__ = [ 'addPath' ]

def addPath(path:str|Path|list|tuple=USER_PATHS) -> None:
    if isinstance(path, (str, Path)):
        paths = [Path(path)]
    else:
        paths = [Path(p) for p in path]
    for path in paths:
        sys.path.append(os.path.expandvars(path))
