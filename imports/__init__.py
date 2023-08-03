'''NOTICE
This 'imports' package is used as the 'gateway' between low-level modules/utils and high-level scripts.
Low-level modules/utils are everything under checkers/configs/helpers/utils/loggers/langs.
High-level scripts are every python script under the root directory (VNx/Mx/Sx.py)

Low-level modules/utils must NEVER import the 'imports' package.
High-level scripts must ONLY import from this 'imports' package.
'''

from configs import *
from .startup import *


chkPython()
chkDep()
updatePATH(USER_PATHS)
chkFFMPEG(FFMPEG_PATH)
chkRAR(RAR_PATH)


from .builtin import *
from .thirdparty import *
from .submodule import *
from .aftercollation import *
