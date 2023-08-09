import sys
from pathlib import Path
sys.path.append(str(Path(f"{__file__}").parent.parent.parent))
PARENT = Path(f"{__file__}").parent
del sys, Path