# False if distributing
DEBUG : bool|None = False
# DEBUG : bool = True
# DEBUG : bool = False

# if DEBUG is None:
#     from pathlib import Path
#     if Path

if DEBUG:
    LOG_LEVEL = 'DEBUG'
else:
    LOG_LEVEL = 'INFO'