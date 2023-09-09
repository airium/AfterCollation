import re
import logging
from pathlib import Path

from utils import listDir
from configs import *
from .season import *
from .naming import *
from helpers.series import *
from helpers.season import *


__all__ = [
    'chkSeries',
    'chkSeriesFiles',
    'chkSeriesNaming',
    ]




def chkSeries(series: Series, logger: logging.Logger):
    chkSeriesFiles(series, logger)
    chkSeriesNaming(series, logger)




def chkSeriesFiles(series: Series, logger: logging.Logger):
    pass




def chkSeriesNaming(series: Series, logger: logging.Logger, check_sub_seasons: bool = True):
    pass

    # if not input_dir.is_dir():
    #     logger.warning('The input path is not a dir, so absolutely not a SERIES dir to check.')
    #     return

    # series_mobj = re.match(VCBS_SERIES_ROOT_DIRNAME_PATTERN, input_dir.name)
    # if not series_mobj:
    #     logger.error('The input does not match the SERIES naming pattern.')

    # series_grptag = series_mobj.group('grptag') if series_mobj else ''
    # series_title = series_mobj.group('title') if series_mobj else ''
    # series_misclabel = series_mobj.group('misclabel') if series_mobj else ''

    # possible_season_dirs = listDir(input_dir, rglob=False)
    # if len(possible_season_dirs) == 0:
    #     logger.warning('No sub dirs for season videos found.')
    # elif len(possible_season_dirs) == 1:
    #     logger.warning('There is only one sub dir. It may be not necessary to use the SERIES dir.')

    # season_dirs = []
    # season_grptags = []
    # season_titles = []
    # season_qlabels = []
    # season_misclabels = []
    # for possible_season_dir in possible_season_dirs:
    #     season_mobj = re.match(VCBS_SEASON_ROOT_DIRNAME_PATTERN, possible_season_dir.name)
    #     if not season_mobj:
    #         logger.error('The sub dirname does NOT match the SEASON naming pattern.')
    #     else:
    #         season_dirs.append(possible_season_dir)
    #         season_grptags.append(season_mobj.group('grptag'))
    #         season_titles.append(season_mobj.group('title'))
    #         season_qlabels.append(season_mobj.group('qlabel'))
    #         season_misclabels.append(season_mobj.group('misclabel'))

    # #* -----------------------------------------------------------------------------------------------------------------

    # if series_grptag:
    #     logger.info(f'Found SERIES group tag "{series_grptag}"')
    #     chkSeriesGroupTag(series_grptag, logger)
    # for season_grptag in season_grptags:
    #     chkSeriesGroupTag(season_grptag, logger)

    # if series_title: logger.info(f'Found SERIES show name "{series_title}"')
    # if series_misclabel:
    #     if series_misclabel.lower() in AVAIL_SUB_LANG_TAGS:
    #         logger.info(f'Found SERIES language label "{series_misclabel}". Take care.')
    #     else:
    #         logger.info(f'Found SERIES non-language label "{series_misclabel}". Take more care.')

    # if check_sub_seasons:
    #     for season_dir in season_dirs:
    #         chkSeasonNaming(season_dir, logger)
