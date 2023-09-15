import itertools
from logging import Logger

from langs import *
from utils import *
from configs import *
from helpers.corefile import CF

import numpy as np


__all__ = ['chkCfAudTracks', 'cmpCfAudContent']




def chkCfAudTracks(cf: CF, logger: Logger, decode: bool = True):

    if cf.ext not in COMMON_VIDEO_EXTS + COMMON_AUDIO_EXTS:
        logger.error(GOT_UNKNOWN_AUD_EXT_1.format(cf.ext))
        return
    if cf.ext not in VX_WITH_AUD_EXTS:
        logger.warning(UNSUPPORTED_EXT_TO_CHECK_1.format(cf.ext))
        return
    if not cf.has_audio:
        return

    #* ---------------------------------------------------------------------------------------------
    # specific check for each audio file type
    match cf.ext:

        case 'mkv':
            if cf.has_video and not cf.audio_tracks:
                logger.error('The MKV has no audio track.')
            if not cf.audio_tracks:
                logger.error('The MKV has no audio track.')
            if len([atr for atr in cf.audio_tracks if (atr and atr.compression_mode == 'Lossless')]) > 2:
                logger.warning('The MKV has more than 2 lossless audio tracks. Consider using MKA.')
            if len(cf.audio_tracks) > 1:
                mkv_stem = m.group('stem').lower() if (m := re.match(TRANSCODED_FILESTEM_REGEX, cf.path.stem)) else ''
                if mkv_stem:
                    mka_files = listFile(cf.path.parent, ext='mka', rglob=False)
                    mka_stems = [
                        m.group('stem').lower()
                        for m in [re.match(TRANSCODED_FILESTEM_REGEX, mka.stem) for mka in mka_files] if m
                        ]
                    if mkv_stem in mka_stems:
                        logger.warning(
                            'It seems that there is already a counterpart MKA, so the MKV should contain only 1 audio track.'
                            )
            for i, atr in enumerate(cf.audio_tracks):
                if i == 0 and atr.default != 'Yes':
                    logger.warning(f'The MKV audio track #{i} should be marked as DEFAULT.')
                if i == 0 and atr.compression_mode != 'Lossless':
                    logger.info(f'The MKV audio track #{i} is not lossless.')
                if i == 0 and atr.channel_s != 2:
                    logger.warning(f'The MKV audio track #{i} is not 2ch.')
                if i > 0 and atr.channel_s > 2:  # we do have i == 0 but 6ch in practice, so only give not 2ch warn as above
                    logger.warning(f'The MKV audio track #{i} is >2ch, which should placed in MKA.')
                if not atr.language:
                    logger.warning(f'The MKV audio track #{i} is missing language tag.')
                elif atr.language not in COMMON_AUDIO_LANGS:
                    logger.warning(f'The MKV audio track #{i} has uncommon language label "{atr.language}".')
            # TODO how can we detect and warn the user that IV should use AAC?
            # implementation here

        case 'mka':
            if not cf.path.with_suffix('.mkv').is_file():
                mka_stem = m.group('stem').lower() if (m := re.match(TRANSCODED_FILESTEM_REGEX, cf.path.stem)) else ''
                if mka_stem:
                    mkv_files = listFile(cf.path.parent, rglob=False)
                    mkv_stems = [
                        m.group('stem').lower()
                        for m in [re.match(TRANSCODED_FILESTEM_REGEX, mkv.stem) for mkv in mkv_files] if m
                        ]
                    if mka_stem in mkv_stems:
                        logger.warning('Cannot find the counterpart MKV of the same filename.')
                else:
                    logger.warning('Cannot find the counterpart MKV (filename too complicated).')

            for i, atr in enumerate(cf.audio_tracks):
                if i == 0 and atr.compression_mode != 'Lossless':
                    logger.warning('The MKA first audio track is not lossless.')
                # TODO mediainfo auto assign default to the first track, but the mka may not have such tag in fact
                # try using MKVInfo to accurately get this tag
                # if i == 0 and atr.default == 'Yes':
                #     logger.warning('The MKA first audio track is not lossless.')
                if not atr.language:
                    logger.warning(f'The MKA track #{i} is missing language tag.')
                if atr.language not in COMMON_AUDIO_LANGS:
                    logger.warning(f'The MKA track #{i} has uncommon language label "{atr.language}".')

        case 'mp4':
            if not cf.audio_tracks:
                logger.error('The MP4 has no audio track.')
            if len(cf.audio_tracks) > 1:
                logger.warning('The MP4 has more than 1 audio track.')
            for i, atr in enumerate(cf.audio_tracks):
                if atr.format != 'AAC':
                    logger.warning(f'The MP4 audio track #{i} is not AAC.')
                if atr.channel_s != 2:
                    logger.warning(f'The MP4 audio track #{i} is not 2ch.')
                if not atr.language:
                    logger.warning(f'The MP4 audio track #{i} is missing language tag.')
                if atr.language not in COMMON_AUDIO_LANGS:
                    logger.warning(f'The MP4 audio track #{i} has uncommon language label "{atr.language}".')

        case 'flac':
            # it seems that FLAC has no specific checking
            pass
        case _:
            logger.error(f'Updated {VX_WITH_AUD_EXTS=} but forgot to update the checker.')
            return

    #* ---------------------------------------------------------------------------------------------
    # general check applicable to all audio files
    for i, atr in enumerate(cf.audio_tracks):
        if i > 0 and atr.default == 'Yes':
            logger.warning(f'The audio track #{i} should not be marked as DEFAULT.')
        if atr.forced == 'Yes':
            logger.warning(f'The audio track #{i} should NOT be marked as FORCED.')
        if atr.format not in COMMON_AUDIO_FORMATS:
            logger.warning(f'The audio track #{i} is uncommon format "{atr.format}".')
        if atr.bit_depth and (atr.bit_depth not in COMMON_AUDIO_DEPTH):
            logger.warning(f'The audio track #{i} has uncommon bit depth "{atr.bit_depth}".')
        if atr.sampling_rate not in COMMON_AUDIO_FREQ:
            logger.warning(f'The audio track #{i} is of uncommon sampling rate "{atr.sampling_rate}".')
        if atr.channel_s not in COMMON_AUDIO_CHANNEL:
            logger.warning(f'The audio track #{i} if of uncommon channel number "{atr.channel_s}".')
        if atr.bit_rate_mode:
            pass  # TODO seems difficult to check something meaningful here (AAC has no such tag)
        if not atr.duration:
            logger.error(f'The audio track #{i} has no duration.')
        elif not matchTime(int(float(atr.duration)), cf.duration, MAX_DURATION_DIFF_BETWEEN_TRACKS):
            logger.warning(f'The audio track #{i} has a different duration.')
        if atr.delay:
            logger.warning(f'The audio track #{i} has delay ({atr.delay}).')

        # do a full decoding test for each audio track
        if decode:
            if not tstFFmpegAudioDecode(cf.path, id=i):
                logger.error(f'The audio track #{i} failed to decode.')




def cmpCfAudContent(input1: CF|list[CF], input2: CF|list[CF], logger: Logger) -> list[tuple[int, np.ndarray, int]]:
    '''
    Compare two groups of audios, supporting multi-track and multi-file.
    In each group, video files is concatenated in series; audio files is placed parallel (i.e. as a new track).

    Return: list[tuple[idx, np.ndarray, freq]]
    idx is the audio track index from 0
    np.ndarray is the difference audio of this track (input1[idx] - input2[idx])
    '''

    if isinstance(input1, CF): input1 = [input1]
    if isinstance(input2, CF): input2 = [input2]

    if not input1 and not input2:
        logger.error('Missing input(s).)')
        return []

    all_has_audio = True
    for cf in input1 + input2:
        if not cf.has_audio:
            logger.error(f'"{cf.path.name}" has no audio track.')
            all_has_audio = False
    if not all_has_audio:
        return []

    freqs = [at.sampling_rate for at in itertools.chain.from_iterable(cf.audio_tracks for cf in input1 + input2)]
    if not all(freqs):
        logger.error(f'Failed to read sampling rate from some input.')
        return []

    # tracks1: dict[idx, list[tuple[CoreFile, audio_idx_in_the_file]]]
    tracks1: dict[int, list[tuple[CF, int]]] = {}
    vcf1s = [cf for cf in input1 if cf.has_video]
    acf1s = [cf for cf in input1 if not cf.has_video]
    for cf1 in vcf1s:
        for i, at in enumerate(cf1.audio_tracks, start=0):
            tracks1[i] = tracks1.get(i, []) + [(cf1, i)]
    num_aud_in_vids = len(tracks1.keys())
    for cf1 in acf1s:
        for i, at in enumerate(cf1.audio_tracks, start=0):
            tracks1[i + num_aud_in_vids] = tracks1.get(i, []) + [(cf1, i)]

    tracks2: dict[int, list[tuple[CF, int]]] = {}
    vcf2s = [cf for cf in input2 if cf.has_video]
    acf2s = [cf for cf in input2 if not cf.has_video]
    for cf2 in vcf2s:
        for i, at in enumerate(cf2.audio_tracks, start=0):
            tracks2[i] = tracks2.get(i, []) + [(cf2, i)]
    num_aud_in_vids = len(tracks2.keys())
    for cf2 in acf2s:
        for i, at in enumerate(cf2.audio_tracks, start=0):
            tracks2[i + num_aud_in_vids] = tracks2.get(i, []) + [(cf2, i)]

    if len(tracks1.keys()) != len(tracks2.keys()):
        audio_nums_to_cmp = min(len(tracks1.keys()), len(tracks2.keys()))
        logger.warning(
            f'The number of audio tracks mismatches: {len(tracks1.keys())} vs {len(tracks2.keys())}. '
            f'VR will only compare the first {audio_nums_to_cmp} audio track(s).'
            )

    ret = []
    for (k, track1), (k2, track2) in zip(tracks1.items(), tracks2.items()):
        assert k == k2  # this should be never triggered

        fi1s, id1s = [cf for cf, _ in track1], [id for _, id in track1]
        # fi1s, id1s = zip(*track1) # NOTE not using this because language server has a bug
        fi2s, id2s = [cf for cf, _ in track2], [id for _, id in track2]
        # fi2s, id2s = zip(*track2) # NOTE not using this because language server has a bug

        bits = [cf.audio_tracks[i].bit_depth for cf, i in zip(fi1s + fi2s, id1s + id2s)]
        bits = [b for b in bits if b]  # remove None because aac/mp3 has not depth
        if len(set(bits)) > 1:
            logger.warning(f'#{k} audio tracks have different bit depths.')

        chans = [cf.audio_tracks[i].channel_s for cf, i in zip(fi1s + fi2s, id1s + id2s)]
        if len(set(chans)) > 1:
            logger.warning(f'#{k} audio tracks have different channel number.')

        freqs = [cf.audio_tracks[i].sampling_rate for cf, i in zip(fi1s + fi2s, id1s + id2s)]
        if len(set(freqs)) > 1:
            logger.error(f'#{k} audio tracks have different sampling rate.')
            continue

        freq = freqs[0]
        start = freq * CHK_OFFSET_STA
        length = freq * CHK_OFFSET_LEN
        audio1 = np.concatenate([readAudio(cf.path, id=i, start=start, length=length) for cf, i in track1])
        audio2 = np.concatenate([readAudio(cf.path, id=i, start=start, length=length) for cf, i in track2])

        start1, start2 = calcAudioOffset(audio1, audio2, start=freq * CHK_OFFSET_STA, length=freq * CHK_OFFSET_LEN)
        if offset := (start1 - start2):
            logger.warning(f'#{k} audio has detected offset: A1[{start1}:]≈A2[{start2}:] ({offset/freq:.3f}s)')

        if (len1 := len(audio1) - start1) != (len2 := len(audio2) - start2):
            logger.warning(f'#{k} audio has detected different length: {len1}≠{len2} ({(len1-len2)/freq:.3f}s)')

        diff_audio = subtractAudio(audio1, audio2)
        if (diff_mean := (np.abs(diff_audio / len(diff_audio)).sum())) > MAX_DIFF_MEAN:
            logger.warning(f'#{k} audio has too large difference (diff={diff_mean:.1e})>{MAX_DIFF_MEAN})')
            ret.append((k, diff_audio, freq))
        else:
            logger.info(f'Audio #{k} looks the same (diff={diff_mean:.1e}).')
        #     ret.append((k, None, freq))

    return ret
