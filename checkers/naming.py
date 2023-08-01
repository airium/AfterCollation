import re
import logging
from pathlib import Path

from configs import *
from utils import *
from helpers import *




def _chkGroupTagImpl(full_grptag:str, logger:logging.Logger):

    if not full_grptag or not full_grptag.strip():
        logger.warning(f'The full group tag is empty.')
        return

    if (striped_grptag := full_grptag.strip()) != full_grptag:
        logger.error(f'["{full_grptag}"] has leading/trailing spaces.')

    group_tags = splitGroupTags(striped_grptag)

    for group_tag in group_tags:
        if (striped_group_tag := group_tag.strip()) != group_tag:
            logger.error(f'"{full_grptag}" has leading/trailing spaces.')
            group_tag = striped_group_tag
        if group_tag and group_tag not in COMMON_GRP_NAMES:
            logger.error(f'Unknown group tag "{group_tag}" (or wrong case).')

    if '' in group_tags:
        logger.error(f'"{full_grptag}" contains empty sections.')
        ok = False

    if len(group_tags) != len(set(_.lower() for _ in group_tags)):
        logger.error(f'"{full_grptag}" contains duplicated tag(s).')
        ok = False

    if full_grptag.endswith('VCB-S'):
        logger.warning(f'"{full_grptag}" ends with "VCB-S", which is an old-fashioned tag.')
    elif not full_grptag.endswith('VCB-Studio'):
        logger.warning(f'"{full_grptag}" should end with "VCB-Studio".')




def chkSeriesGroupTag(grptag:str, logger:logging.Logger):
    _chkGroupTagImpl(grptag, logger)




def procSeasonGroupTag(grptag:str, default:str, logger:logging.Logger) -> str:

    if not grptag:
        return default

    _chkGroupTagImpl(grptag, logger)

    if default and (grptag != default):
        logger.warning(f'Using a non-default group name "{grptag}".')

    return grptag
















def procTypeName(typename:str, logger:logging.Logger) -> str:

    if typename not in COMMON_TYPENAME:
        logger.warning(f'The typename "{typename}" is uncommon (or wrong case).')
    if any((p in typename) for p in string.digits):
        logger.warning(f'The typename "{typename}" contains numbers, which is disallowed.')
    if typename and (not typename.isascii()):
        logger.error(f'The typename "{typename}" contains non-ascii character.')
        return ''

    return typename



def procIndex(idx1:str, idx2:str, logger:logging.Logger) -> tuple[int|float|None, int|float|None]:

    ret_idx1 : int|float|None = None
    ret_idx2 : int|float|None = None

    if idx1:
        if not isDecimal(idx1):
            logger.warning(f'The main index "{idx1}" will be ignored as not a decimal number.')
        elif not idx1.isdigit():
            logger.warning(f'The main index "{idx1}" is not an integer.')
            ret_idx1 = float(idx1)
        else:
            ret_idx1 = int(idx1)

    if ret_idx1 == None:
        ret_idx2 = None
        if idx2: logger.warning(f'The sub index "{idx2}" will be ignored as the main index is empty or invalid.')
    elif idx2:
        if not isDecimal(idx2):
            logger.warning(f'The sub index "{idx2}" will be ignored as not a decimal number.')
        elif not idx2.isdigit():
            logger.warning(f'The main index "{idx2}" is not an integer.')
            ret_idx2 = float(idx2)
        else:
            ret_idx2 = int(idx2)

    return ret_idx1, ret_idx2




# cmpNaming(g1, g2, logger)