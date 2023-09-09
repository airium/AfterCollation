import re
import logging
import itertools
from helpers.corefile import CF
from utils.mediainfo import *
from utils.language import chkLang
from configs import *


__all__ = ['chkMenuTracks', 'cmpMenuContent']




def cmpMenuContent(input1: CF|list[CF], input2: CF|list[CF], logger: logging.Logger):

    if isinstance(input1, CF): input1 = [input1]
    if isinstance(input2, CF): input2 = [input2]

    if not input1 and not input2:
        logger.error('Missing input(s).)')
        return

    has_menu = True
    for cf in input1 + input2:
        if not cf.has_menu:
            has_menu = False
    if not has_menu:
        logger.info('No menu track found in input(s).')
        return

    match len(input1), len(input2):
        case 1, 1:
            if not input1[0].has_menu:
                logger.error(f'"{input1[0].path}" has no menu track.')
            elif not input2[0].has_menu:
                logger.error(f'"{input2[0].path}" has no menu track.')
            else:
                # NOTE checking if it should only include 1 menu is not the job in cmpMenu
                ts1s = input1[0].menu_timestamps
                ts2s = input2[0].menu_timestamps
                for ts1, ts2 in zip(ts1s, ts2s):
                    if len(ts1) != len(ts2):
                        logger.error(f'Number of menu entries differs: {len(ts1)} vs {len(ts2)}')
                    n = min(len(ts1), len(ts2))
                    if not matchMenuTimeStamps(ts1[:n], ts2[:n]):
                        logger.error(f'Menu entries differs in time.')
        case 1, _:
            if not input1[0].has_menu:
                logger.error(f'"{input1[0].path}" has no menu track.')
                return
            # NOTE checking if it should only include 1 menu is not the job in cmpMenu
            ts1 = input1[0].menu_timestamps[0]
            durations = [cf.duration for cf in input2]
            expected_timestamps = list(itertools.accumulate(durations))
            # NOTE remember to remoev the last one
            if not matchMenuTimeStamps(ts1, expected_timestamps[:-1]):
                logger.error(f'Menu entries differs in time for sliced videos.')
        case _, 1:
            if not input2[0].has_menu:
                logger.error(f'"{input2[0].path}" has no menu track.')
                return
            # NOTE checking if it should only include 1 menu is not the job in cmpMenu
            ts2 = input2[0].menu_timestamps[0]
            durations = [cf.duration for cf in input1]
            expected_timestamps = list(itertools.accumulate(durations))
            # NOTE remember to remoev the last one
            if not matchMenuTimeStamps(ts2, expected_timestamps[:-1]):
                logger.error(f'Menu entries differs in time for sliced videos.')
        case _, _:
            logger.info('Multi vs multi-input is not supported for menu check for now.')




def chkMenuTracks(cf: CF, logger: logging.Logger):

    if cf.ext not in COMMON_VIDEO_EXTS:
        logger.error(f'The file is not a known file type with menu.')
        return
    if cf.ext not in VX_VID_EXTS:
        logger.warning(f'The menu checker is not designed to check the file type "{cf.ext}".')
        return
    if not cf.has_menu:
        return

    if len(cf.menu_tracks) > 1:
        logger.warning('The file has >1 menus.')

    for t in cf.menu_tracks:
        # first
        chap_times, chap_texts = list(zip(*[(k, v) for (k, v) in t.to_data().items() if re.match(LIBMEDIAINFO_CHAPTER_REGEX, k)]))
        # disable sorting may preserve the original order?
        # chap_times, chap_texts = zip(*sorted(zip(chap_times, chap_texts)))
        # start checking the chapter content
        i, last_chap_time, chap_langs, chap_desps, is_chapter_xx = 0, '', [], [], False
        for i, (chap_time, chap_text) in enumerate(zip(chap_times, chap_texts), start=1):
            if (i == 1) and (chap_time != '00_00_00000'):
                logger.warning('The first chapter not starts at 00:00:00')
            if last_chap_time and (chap_time <= last_chap_time):
                logger.warning(f'Chapter {i} at {chap_time} should > last chapter at {last_chap_time}.')
            if m := re.search(MENU_TEXT_STD_REGEX, chap_text):
                is_chapter_xx = True
                if (idx := int(m.group('idx'))) != i:
                    logger.warning(f'Chapter #{i} is mistakenly labelled as chapter #{idx}.')
                chap_lang = m.group('lang')
                chap_text = m.group('text')
            elif m := re.search(MENU_TEXT_CUSTOM_REGEX, chap_text):
                logger.warning(f'Using custom chapter text #{i:02d}:\"{m.group("text")}\"')
                chap_lang = m.group('lang')
                chap_text = m.group('text')
            else:
                chap_lang = ''
            chap_desps += [chap_text]
            chap_langs += [chap_lang]
            last_chap_time = chap_time
        # after-loop check
        if i == 0:
            logger.warning('Menu with only the starting chapter should be removed.')
        if m := re.match(LIBMEDIAINFO_CHAPTER_REGEX, last_chap_time):
            hour, minute, milisecond = m.groups()
            last_chap_time = int(hour) * 3600000 + int(minute) * 60000 + int(milisecond)
            duration = cf.duration
            if last_chap_time >= (duration - MIN_DISTANCE_FROM_LASTER_CHAP_TO_END):
                logger.warning('The last chapter locates too close to the video end.')
            elif last_chap_time >= duration:
                logger.warning('The last chapter locates outside of the video duration.')
            else:
                pass  # ok
        # check if the menu language label agrees with its text
        if cf.gtr.format == 'Matroska':  # MP4 chap has no language label
            if len(chap_langs := set(chap_langs)) != 1:
                logger.warning('Menu language label looks malformed.')
            if chap_langs and (chap_lang := chap_langs.pop()):
                if is_chapter_xx:
                    found_lang = 'en'
                else:
                    found_langs = []
                    chap_desp = ' '.join(chap_desps).lower()
                    n = 0
                    for en_text in KNOWN_MENU_EN_TEXTS:
                        if en_text.lower() in chap_desp:
                            n += 1
                    if n >= 2:  # consider it's English if >2 matches
                        found_lang = 'en'
                    else:
                        found_lang = chkLang(chap_desp)
                if chap_lang != found_lang:
                    logger.warning(
                        f'Menu language detected "{found_lang}" != tagged "{chap_lang}" '
                        '(note the detection is not accurate at the moment).'
                        )

    # val1 = CHAP_NAME_PATTERN.match(line1).groups()
    # val2 = CHAP_NAME_PATTERN.match(line2).groups()
    # # idx1, idx2 = val1[0], val2[0]
    # # if idx1 != idx2:
    # #     ret.append(f"Error: chapter index not much at line {i:2d}: {idx1} vs {idx2}")
    # if (mo := re.match(r"Chapter ([0-9][0-9])", val1[1])):
    #     if mo.groups()[0] != val1[0]:
    #         ret.append(f"Error: chapter index in name is not correct at line {i:2}: {line1}")
    # elif 'vcb' in str(fp1):
    #         ret.append(f"Warning: using custom chapter name at line {i:2}: {line1}")
    # if (mo := re.match(r"Chapter ([0-9][0-9])", val2[1])):
    #     if mo.groups()[0] != val2[0]:
    #         ret.append(f"Error: chapter index in name is not correct at line {i:2}: {line2}")
    # elif 'vcb' in str(fp2):
    #         ret.append(f"Warning: using custom chapter name at line {i:2}: {line2}")
