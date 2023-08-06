import logging
import itertools
from pathlib import Path

from helpers.season import Season
from helpers.corefile import CoreFile
from helpers.naming import cmpCoreFileNaming
from configs.runtime import *
from .naming import *
from .tracks import *

import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm


__all__ = [
    'chkSeason',
    'chkSeasonFiles',
    'chkSeasonNaming',
    'chkSeasonPerNamingField',
    'chkSeasonNaming',
    'chkNamingDependency',
    'chkFinalNamingConflict',
    'chkCorrelatedNaming',
    ]




def chkSeasonFiles(inp: Season|list[CoreFile], logger: logging.Logger):
    cfs = inp.cfs if isinstance(inp, Season) else inp
    with logging_redirect_tqdm([logger]):
        for cf in tqdm.tqdm(cfs, desc='Checking', unit='file', ascii=True, dynamic_ncols=True):
            if cf.ext in VNx_ALL_EXTS:
                chkFile(cf, logger=logger)
            else:
                logger.error(f'Skipping "{cf.path}" as its extension is not listed as valid.')




def chkCorrelatedNaming(season: Season, logger: logging.Logger) -> bool:

    ok = True
    cfs = season.cfs

    for i, info in enumerate(cfs):
        logger.debug(f'Checking for "{info.src}"...')

        # counterpart check
        if info.e.endswith('mka'):
            found_counterpart = False
            for j, info2 in enumerate(cfs):
                # mka counterpart requires [:9] all
                if (info2.e == 'mkv') and all(cmpCoreFileNaming(info, info2)[:9]):
                    found_counterpart = True
                    break
            if not found_counterpart:
                logger.warning(f'Found dangling MKA having no counterpart MKV ("{info.crc}").')
                ok = False

        if info.e == 'ass':
            found_counterpart = False
            for j, info2 in enumerate(cfs):
                # ass counterpart requires [:8] at custom (ex. suffix)
                if (info2.e == 'mkv') and all(cmpCoreFileNaming(info, info2)[:8]):
                    found_counterpart = True
                    break
            if not found_counterpart:
                logger.warning('Found dangling ASS having no counterpart MKV.')
                ok = False

        if info.e == 'flac':
            found_counterpart = False
            for j, info2 in enumerate(cfs):
                # flac counterpart only requires [:4] at typename
                # because we can have one [Menu].flac but multi [Menu01~4].png
                if (info2.e == 'png') and all(cmpCoreFileNaming(info, info2)[:4]):
                    found_counterpart = True
                    break
            if not found_counterpart:
                logger.warning('Found dangling FLAC having no counterpart PNG.')
                ok = False

    # TODO: stopped the user if an invalid refernce is found
    # TODO: warn that naming reference refers to another reference
    return ok




def chkSeasonGlobalNaming(season: Season, logger: logging.Logger):

    num_vid = len([cf for cf in season.cfs if ((cf.l == '') and (cf.e in VNx_VID_EXTS))])
    num_ass = len([cf for cf in season.cfs if ((cf.l == '') and (cf.e in VNx_SUB_EXTS))])
    num_arc = len([cf for cf in season.cfs if ((cf.l == '') and (cf.e in VNx_ARC_EXTS))])
    num_mka = len([cf for cf in season.cfs if ((cf.l == '') and (cf.e in VNx_EXT_AUD_EXTS))])

    # if mka presents, the amount of mkv/mka at root should match
    if num_mka and (num_mka != num_vid):
        logger.warning(f'The amount of MKA seems incorrect at root (got {num_mka} but {num_vid} videos).')

    # if coop with subsgrp with ass
    if season.g.endswith('VCB-Studio') and season.g != 'VCB-Studio' and season.x == '':
        if num_ass % num_vid != 0:
            logger.warning(f'The amount of ASS subs seems incorrect (got {num_ass} but {num_vid} videos).')
        if num_arc != 1:
            logger.warning(f'The amount of font pack seems incorrect (expect 1 got {num_arc}).')

    # if we have a base language suffix, check if all video have the same language tag
    # if default.x in COMMON_SUBS_LANG_TAGS:
    #     for info in infos:
    #         if info.src.lower().endswith(VID_EXT) and info.x != default.x:
    #             logger.warning(f'Base language suffix is "{default.x}" but this is "{info.x}" ("{info.src}").')
    #         elif info.x != default.x: # also, other files should have no language tag
    #             logger.warning(f'The file should have no language suffix ("{info.src}").')

    # TODO check each ass/mka all have a counterpart mkv/mp4




def chkNamingDependency(season: Season, logger: logging.Logger, hook: bool = True) -> bool:

    ok = True
    dep_cfs = list(cf for cf in season.cfs if cf.e in VNx_DEP_EXTS)
    idp_cfs = list(cf for cf in season.cfs if cf.e not in VNx_DEP_EXTS)

    for i, dep_cf in enumerate(dep_cfs):
        if dep_cf.depends: continue
        counterparts = [cf for cf in idp_cfs if all(cmpCoreFileNaming(cf, dep_cf)[:8])]  # match any except suffix
        if counterparts:
            if hook:
                dep_cf.depends = counterparts[0]
                logger.info(f'The file with CRC32 0x{dep_cf.crc} now depends CRC32 0x{counterparts[0].crc} for naming.')
            if counterparts[1:]:
                logger.warning(
                    f'Found more than 1 counterpart videos for file with CRC32 0x{dep_cf.crc} '
                    f'to copy the naming from. You config may be incorrect.'
                    )
        else:
            logger.error(f'Found NO counterpart video for "{dep_cf.crc}" to copy the quality/track label.')
            ok = False

    return ok




def chkFinalNamingConflict(season: Season, logger: logging.Logger) -> bool:

    ok = True
    names = []
    crc32s = []
    for cf in season.cfs:
        i_name = f'{cf.e}//{cf.g}//{cf.t}//{cf.l}//{cf.f}//{cf.x}'
        names.append(i_name)
        crc32s.append(cf.crc32)
    # we need to show every conflict to the user, so cant use a faster method like set()
    for i, i_name, i_crc32 in zip(itertools.count(), names, crc32s):
        for j, j_name, j_crc32 in zip(itertools.count(), names[i + 1:], crc32s[i + 1:]):
            if i_name == j_name:
                ok = False
                logger.error(
                    f'Found naming conflict between files with CRC32 0x{i_crc32} vs 0x{j_crc32} '
                    f'(possibly at CSV line {i+2} and {i+j+2}).'
                    )

    return ok




def chkSeasonPerNamingField(season: Season, logger: logging.Logger) -> bool:

    ok = True

    ok = ok if chkGrpTag(season.g, logger) else False
    ok = ok if chkTitle(season.t, logger) else False
    ok = ok if chkSuffix(season.x, logger) else False

    for cf in season.cfs:
        ok = ok if chkGrpTag(cf.g, logger) else False
        ok = ok if chkTitle(cf.t, logger) else False
        ok = ok if chkLocation(cf.l, logger) else False
        ok = ok if chkTypeName(cf.c, logger) else False
        ok = ok if chkIndex(cf.i1, cf.i2, logger) else False
        ok = ok if chkNote(cf.n, logger) else False
        ok = ok if chkCustom(cf.f, logger) else False
        ok = ok if chkSuffix(cf.x, logger) else False

    return ok




def chkSeasonNaming(season: Season, logger: logging.Logger) -> bool:
    if not chkSeasonPerNamingField(season, logger): return False
    if not chkCorrelatedNaming(season, logger): return False
    if not chkSeasonGlobalNaming(season, logger): return False

    return True



    return True, default, ret_infos




def chkSeason(season: Season, logger: logging.Logger) -> bool:
    if not chkSeasonNaming(season, logger): return False
    if not chkSeasonFiles(season, logger): return False
    return True
