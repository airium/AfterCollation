from pathlib import Path
from lark import Lark


__all__ = ['ALBUM_DIRNAME_LARK']

#! must use earley parser
ALBUM_DIRNAME_LARK = Lark((Path(__file__).parent/'lark/album.lark').read_text('utf-8'), parser='earley')
