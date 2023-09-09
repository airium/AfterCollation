import os
import sys
import shutil
from pathlib import Path

from langs import *


__all__ = ['chkPython', 'chkDep', 'updatePATH', 'chkFFMPEG', 'chkRAR']




def chkPython():

    if sys.version_info < (3, 10):
        print(f'!!! Python 3.10 is required, but {sys.version_info} is used. !!!')
        input(ENTER_TO_EXIT_0)
        sys.exit(1)




def chkDep():
    try:
        import tqdm  # pip install tqdm
        import langdetect  # pip install langdetect
        import yaml  # pip install pyyaml
        import ffmpeg  # pip install ffmpeg-python
        import pymediainfo  # pip install pymediainfo
        import webptools  # pip install webptools
        import ssd_checker  # pip install ssd_checker
        import ass  # pip install ass
        import ass_parser  # pip install ass-parser
        import ass_tag_parser  # pip install ass-tag-parser
        import fontTools  # pip install fonttools
        import pyzipper
        import py7zr  # pip install py7zr
        import rarfile  # pip install rarfile
        import cryptography
        import requests  # pip install requests
        import bs4  # pip install beautifulsoup4
        import numpy  # pip install numpy
        import scipy  # pip install scipy
        import bencoder
        import lark

    except ImportError:
        print('!!! Missing necessary external packages !!!')
        print('Run `python -m pip install -r requirements.txt` to enable the scripts.')
        input('Press Enter to exit')
        sys.exit(1)




def updatePATH(path: str|Path|list|tuple):
    if isinstance(path, (str, Path)):
        paths = [Path(path)]
    else:
        paths = [Path(p) for p in path]
    paths = [(p.parent if p.is_file() else p) for p in paths]
    chars = ';'.join(os.path.expandvars(p) for p in paths)
    os.environ['PATH'] = f'{chars};{os.environ["PATH"]}'




def chkFFMPEG(path: str|Path = ''):
    if path: updatePATH(path)
    if not shutil.which('ffmpeg'):
        print('!!! FFMPEG is not installed or not added to PATH !!!')
        print('Please install FFMPEG and add it to "configs/user.py/USER_PATHS|FFMPEG_PATH".')
        input(ENTER_TO_EXIT_0)
        sys.exit(1)




def chkRAR(path: str|Path = ''):
    if path: updatePATH(path)
    if not shutil.which('rar'):
        print('!!! WinRAR is not installed or not added to PATH !!!')
        print('Please install WinRAR and add it to "configs/user.py/USER_PATHS|RAR_PATH".')
        input(ENTER_TO_EXIT_0)
        sys.exit(1)
