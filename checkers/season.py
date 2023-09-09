import logging
import itertools

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
    'chkSeasonNamingLocally',
    'chkSeasonNamingCorrelation',
    'chkSeasonNamingGlobally',
    'chkNamingDependency',
    'chkFinalNamingConflict',
    ]




def chkSeason(season: Season, logger: logging.Logger) -> bool:
    if not chkSeasonFiles(season, logger): return False
    if not chkSeasonNaming(season, logger): return False
    return True




def chkSeasonFiles(inp: Season|list[CoreFile], logger: logging.Logger):
    cfs = inp.files if isinstance(inp, Season) else inp
    with logging_redirect_tqdm([logger]):
        for cf in tqdm.tqdm(cfs, desc='Checking', unit='file', ascii=True, dynamic_ncols=True):
            if cf.ext in VX_ALL_EXTS:
                chkFile(cf, logger=logger)
            else:
                logger.error(f'Skipping "{cf.path}" as its extension is not listed as valid.')




def chkSeasonNaming(season: Season, logger: logging.Logger) -> bool:
    '''
    Do leveled naming checks.
    If used in VP, the naming fields should be already auto-filled through `doAutoIndexing()`.

    #! as a general function, dont assume the naming fields has been cleaned through `cleanNamingDicts()`.
    #! since it will be not only used in VP but also in VR.
    '''
    # local-only naming check
    if not chkSeasonNamingLocally(season, logger): return False
    # mid-level naming check
    if not chkSeasonNamingCorrelation(season, logger): return False
    # global-level naming and sanity check
    if not chkSeasonNamingGlobally(season, logger): return False
    return True




def chkSeasonNamingLocally(season: Season, logger: logging.Logger) -> bool:
    '''Local only naming check.'''

    ok = True

    logger.info('Checking the naming of season root dir ...')
    ok = ok if chkGrpTag(season, logger) else False
    ok = ok if chkTitle(season, logger) else False
    ok = ok if chkSuffix(season, logger) else False

    for cf in season.files:

        logger.info(f'Checking the naming of file with CRC32 0x{cf.crc32} ...')
        ok = ok if chkGrpTag(cf, logger) else False
        ok = ok if chkTitle(cf, logger) else False
        ok = ok if chkLocation(cf, logger) else False
        ok = ok if chkClassification(cf, logger) else False
        ok = ok if chkIndex(cf, logger) else False
        ok = ok if chkSupplementDesp(cf, logger) else False
        ok = ok if chkCustomisedDesp(cf, logger) else False
        ok = ok if chkSuffix(cf, logger) else False

    return ok




def chkSeasonNamingCorrelation(season: Season, logger: logging.Logger) -> bool:

    ok = True
    cfs = season.files
    for i, cf in enumerate(cfs):
        logger.debug(f'Checking for {cf.e}/0x{cf.src} ...')

        match cf.e:

            case 'mka':  #* ---------------------------------------------------------------------------------------------
                mkv_partners: list[CoreFile] = []
                for ccf in (cfs[:i] + cfs[i + 1:]):
                    if all(cmpCoreFileNaming(cf, ccf)[:9]):  # MKA partner matches at [:9] (before ext)
                        if ccf.ext == 'mkv':
                            mkv_partners.append(ccf)
                        #? any other?

                #! each MKA should have 1 and only 1 MKV partner
                if len(mkv_partners) == 0:
                    logger.error(f'Found dangling MKA 0x{cf.crc32} having no partner video.')
                    ok = False
                if len(mkv_partners) >= 2:
                    logger.error(f'Found >1 partner MKV for the ASS 0x{cf.crc32}.')
                    ok = False

            case 'ass':  #* ---------------------------------------------------------------------------------------------

                vid_partners: list[CoreFile] = []
                ass_peers: list[CoreFile] = []
                for ccf in (cfs[:i] + cfs[i + 1:]):
                    if all(cmpCoreFileNaming(cf, ccf)[:8]):  # ASS partner matches at [:8] (before suffix)
                        if ccf.ext in VX_VID_EXTS:
                            vid_partners.append(ccf)
                        elif ccf.ext in VX_SUB_EXTS:
                            ass_peers.append(ccf)
                        #? any other?

                #! each ASS should have 1 and only 1 video partner
                if len(vid_partners) == 0:
                    logger.error(f'Found dangling ASS 0x{cf.crc32} having no counterpart video.')
                    ok = False
                if len(vid_partners) >= 2:
                    logger.error(f'Found >1 partner videos for the ASS 0x{cf.crc32}.')
                    ok = False

                #! if there are >1 ASS partners for the same video, they should have different suffixes
                for ass_peer in ass_peers:
                    if ass_peer.x == cf.x:
                        logger.error(f'Found peer ASS 0x{ass_peer.crc32} with the same suffix {cf.x}.')
                        ok = False

            case 'flac':  #* --------------------------------------------------------------------------------------------

                png_partners: list[CoreFile] = []
                for ccf in (cfs[:i] + cfs[i + 1:]):
                    # flac partner matches at [:4] (at classification)
                    # because we can reuse "[Menu].flac" for multi "[Menu01~4].png"
                    if all(cmpCoreFileNaming(cf, ccf)[:4]):
                        if ccf.ext == 'png':
                            png_partners.append(ccf)
                        #? any other?

                #! each FLAC should have at least
                if len(png_partners) == 0:
                    logger.error(f'Found dangling FLAC 0x{cf.crc32} having no partner PNG.')
                    ok = False
                if len(png_partners) >= 2:
                    logger.info(f'Possibly {len(png_partners)} PNGs are reusing the FLAC 0x{cf.crc32}. Take care.')

    # TODO: warn that naming reference refers to another reference
    return ok




def chkSeasonNamingGlobally(season: Season, logger: logging.Logger):

    # TODO: check suffix

    num_vid = len([cf for cf in season.files if ((cf.l == '') and (cf.e in VX_VID_EXTS))])
    num_ass = len([cf for cf in season.files if ((cf.l == '') and (cf.e in VX_SUB_EXTS))])
    num_arc = len([cf for cf in season.files if ((cf.l == '') and (cf.e in VX_ARC_EXTS))])
    num_mka = len([cf for cf in season.files if ((cf.l == '') and (cf.e in VX_EXT_AUD_EXTS))])

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
    dep_cfs = list(cf for cf in season.files if cf.e in VX_DEP_EXTS)
    idp_cfs = list(cf for cf in season.files if cf.e not in VX_DEP_EXTS)

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
    for cf in season.files:
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
