import sys

try:

    import tqdm                                 # pip install tqdm

    import langdetect                           # pip install langdetect
    import yaml                                 # pip install pyyaml

    import ffmpeg                               # pip install ffmpeg-python
    import pymediainfo                          # pip install pymediainfo
    import webptools                            # pip install webptools

    import ssd_checker                          # pip install ssd_checker

    import ass                                  # pip install ass
    import ass_parser                           # pip install ass-parser
    import ass_tag_parser                       # pip install ass-tag-parser
    import fontTools                            # pip install fonttools

    import py7zr                                # pip install py7zr
    import rarfile                              # pip install rarfile

    import requests                             # pip install requests
    import bs4                                  # pip install beautifulsoup4

    import numpy                                # pip install numpy
    import scipy                                # pip install scipy

except ImportError:

    print('!!! Missing necessary external packages !!!')
    print('Run `python -m pip install -r requirements.txt` to enable the scripts.')
    print()
    input('Press Enter to exit')
    sys.exit(1)

del sys

