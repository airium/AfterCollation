from imports import *

VNE_USAGE = f'''VideoNamingExecutor (VNE) only accepts the following input:
1. drop/cli the VND.csv

VNE includes the following behaviors:
1. check your naming proposal from the input (VND.csv)
2. do auto indexing and naming inference for empty fields
3. place the input files specified in the input to the target filetree/filenames

VNE will try hardlink when placing the target files.
VNE only read the input files, but will NEVER modify or overwrite the input files.
'''



INFO = namedtuple('NAMING_INFO',
                  field_names='crc ' # the crc32 of the file
                              'src ' # the path to the SouRCe file
                              'dst ' # the path to the DEStination
                              'g '   # the Groupname used for this file
                              's '   # the Showname used for this file
                              'l '   # the Location of the file relative to season root
                              't '   # the Tynename of the video content
                              'i1 '  # the main indexing info
                              'i2 '  # the sub indexing info
                              'n '   # the Note
                              'c '   # the Customized name, but later to be re-used as the final Content name
                              'x '   # the suffiX to be prepend right before the file extension
                              'e',   # the file Extension
                  defaults=[''] * 7 + [None] * 2 + [''] * 4)




def cmpNamingInfo(a:INFO, b:INFO) -> list[bool]:
    ret = [False] * 9
    if a.g == b.g: ret[0] = True
    if a.s == b.s: ret[1] = True
    if a.l == b.l: ret[2] = True
    if a.t == b.t: ret[3] = True
    if a.i1 == b.i1: ret[4] = True
    if a.i2 == b.i2: ret[5] = True
    if a.n == b.n: ret[6] = True
    if a.c == b.c: ret[7] = True
    if a.x == b.x: ret[8] = True
    return ret








def chkShowName(showname:str, default:str, logger:logging.Logger) -> str:

    if not showname and not default:
        return ''

    if not showname:
        return default

    if not showname.isascii():
        logger.warning(f'The showname "{showname}" contains non-ascii character.')
    if chkLang(showname) == 'en':
        logger.warning(f'The showname looks like English. Make sure that using English instead of Romaji is intended.')

    return showname




def chkCustom(cname:str, ext:str, logger:logging.Logger) -> str:

    if not cname:
        return ''

    if not cname.isascii():
        logger.warning(f'The customized name contains non-ascii character.')

    if re.match(CRC32_CSV_PATTERN, cname):
        logger.info(f'Using naming reference to "{cname}".')
        if ext not in VNx_DEP_EXTS:
            # warn that files except mka/ass should not use reference naming
            logger.warning(f'The file type {ext.upper()} should better NOT use name reference.')
    else: # if not re.match(CRC32_CSV_PATTERN, cname)
        if ext in VNx_DEP_EXTS:
            # warn that mka/ass should better use reference naming
            logger.warning(f'This file type {ext.upper()} should better use name reference. Auto/Manual indexing may be inaccurate.')
        logger.warning(f'Using a customized name "{cname}". '
                        'Auto location and indexing will be DISABLED for this file.')

    return cname














def chkLocation(loc:str, typename:str, logger:logging.Logger) -> str:

    if loc:
        if loc.startswith('/'): # a leading '/' may be preserved to indicate the season root dir
            loc = loc[1:]
        if loc not in COMMON_VIDEO_LOCATIONS:
            logger.warning(f'Using an uncommon location "{loc}".')
    else:
        if typename: loc = 'SPs'

    assert not loc.startswith('/'), 'doNaming() enforces that location not started with /.'
    return loc




def chkNote(note:str, logger:logging.Logger) -> str:
    if note and (not note.isascii()):
        logger.warning(f'The extra note "{note}" contains non-ascii character.')
    return note




def chkSuffix(suffix:str, default:str, fullpath:str, logger:logging.Logger)-> str:

    # TODO check again if default suffix should be applied to files

    if not suffix:
        # suffix default only applies when it's a language tag and only for video files
        if (default in AVAIL_SUB_LANG_TAGS) and (fullpath.lower().endswith(VNx_VID_EXTS)):
            return default
        else:
            return ''

    # if suffix:

    if fullpath == BASE_LINE_LABEL:
        if suffix not in AVAIL_SUB_LANG_TAGS:
            logger.warning(f'Using a non-language suffix for base. It will be only applied to the root dirname.')
        return suffix

    # if suffix and fullpath != DEFAULT_LABEL:

    if fullpath.lower().endswith(VNx_VID_EXTS):

        # TODO: can we check if the video images contain any hard subs?
        logger.warning(f'Found "{suffix=}" - plz recheck that this video is hard-subbed.')

        valid_part = ''
        for part in suffix.split('&'):
            if valid_part:
                logger.warning('Ignoring more than 1 valid language tag.')
                break
            if part in AVAIL_SUB_LANG_TAGS:
                valid_part = part
            else:
                logger.warning(f'Ignoring disallowed language tag "{part}" in suffix.')
        suffix = valid_part

    elif fullpath.lower().endswith(VNx_SUB_EXTS):

        valid_count, valid_parts = 0, []
        for part in suffix.split('&'):
            if valid_count == 2:
                logger.warning('Ignoring more than 2 valid language tags.')
                break
            if part in AVAIL_SUB_LANG_TAGS:
                valid_parts.append(part)
                valid_count += 1
            else:
                logger.warning(f'Ignoring disallowed language tag "{part}" in suffix.')

        cn_lang = ''

        if valid_count == 1:
            lang = valid_parts[0]
            if lang in AVAIL_JPN_LANG_TAGS:
                logger.warning('Single language tag should not be Japanese.')
            else:
                cn_lang = lang

        elif valid_count == 2:
            lang1, lang2 = valid_parts[0], valid_parts[1]
            a1, b1 = divmod(AVAIL_SUB_LANG_TAGS.index(lang1), 5)
            a2, b2 = divmod(AVAIL_SUB_LANG_TAGS.index(lang2), 5)
            if b1 != b2:
                logger.warning('Used CN/JP format mismatched in suffix.')
            if ((a1 * a2) != 0) or ((a1 + a2) == 0) or ((a1 + a2) > 2):
                logger.warning('The language tag does not contain only one CN and only one JP.')
            elif a1 > 0:
                cn_lang = AVAIL_SUB_LANG_TAGS[a1 * 5 + b1]
            else: # a2 > 0
                cn_lang = AVAIL_SUB_LANG_TAGS[a2 * 5 + b2]

        else:
            raise ValueError('VNE bug inside `chkSuffix()`. Please report.')

        if cn_lang:
            tagged_cht = True if (cn_lang in AVAIL_CHT_LANG_TAGS) else False
            try:
                ass_text = Path(fullpath).read_text('utf-8-sig')
                detected_cht = False
                for tc in CHT_SAMPLE_CHARS:
                    if tc in ass_text:
                        detected_cht = True
                        break
                if tagged_cht != detected_cht:
                    if detected_cht:
                        logger.warning(f'The ASS file seems to be Traditional Chinese, but tagged as {cn_lang}.')
                    else:
                        logger.warning(f'The ASS file seems to be Simplified Chinese, but tagged as {cn_lang}.')
            except UnicodeDecodeError:
                logger.warning('The encoding of the ASS file is not UTF-8-BOM.')
            except Exception as e:
                logger.warning(f'Failed to detect ASS language from its content due to unexpected error: "{e}". Please report.')

        suffix = '&'.join(valid_parts)

    elif fullpath.endswith(('mka', )):
        pass # to be checked in correlated naming check

    else:

        logger.warning(f'Found "{suffix=}" - but this file should not have suffix.')

    if default and (suffix != default):
        logger.warning(f'Using a non-default suffix "{suffix}".')

    return suffix




def chkCorrelatedNaming(infos: list[INFO], logger:logging.Logger) -> list[INFO]:

    for i, info in enumerate(infos):
        # logger.info('Checking for "{}"...'.format(info.src))

        # counterpart check
        if info.e.endswith('mka'):
            counterpart = False
            for j, info2 in enumerate(infos):
                # mka counterpart requires [:9] all
                if (i != j) and (info2.e == 'mkv') and all(cmpNamingInfo(info, info2)[:9]):
                    counterpart = True
                    break
            if not counterpart:
                logger.warning(f'Found dangling MKA having no counterpart MKV ("{info.crc}").')

        if info.e == 'ass':
            counterpart = False
            for j, info2 in enumerate(infos):
                # ass counterpart requires [:8] at custom (ex. suffix)
                if (i != j) and (info2.e == 'mkv') and all(cmpNamingInfo(info, info2)[:8]):
                    counterpart = True
                    break
            if not counterpart:
                logger.warning('Found dangling ASS having no counterpart MKV.')

        if info.e == 'flac':
            counterpart = False
            for j, info2 in enumerate(infos):
                # flac counterpart only requires [:4] at typename
                # because we can have one [Menu].flac but multi [Menu01~4].png
                if (i != j) and (info2.e == 'png') and all(cmpNamingInfo(info, info2)[:4]):
                    counterpart = True
                    break
            if not counterpart:
                logger.warning('Found dangling FLAC having no counterpart PNG.')

    # TODO: stopped the user if an invalid refernce is found
    # TODO: warn that naming reference refers to another reference

    return infos




def chkGlobalNaming(default:INFO, infos:list[INFO], logger:logging.Logger):

    num_vid = len([info for info in infos if ((info.g == '') and (info.e in VNx_VID_EXTS))])
    num_ass = len([info for info in infos if ((info.g == '') and (info.e in VNx_SUB_EXTS))])
    num_arc = len([info for info in infos if ((info.g == '') and (info.e in VNx_ARC_EXTS))])
    num_mka = len([info for info in infos if ((info.g == '') and (info.e in VNx_EXT_AUD_EXTS))])

    # if mka presents, the amount of mkv/mka at root should match
    if num_mka and (num_mka != num_vid):
        logger.warning(f'The amount of MKA seems incorrect at root (got {num_mka} but {num_vid} videos).')

    # if coop with subsgrp with ass
    if default.g.endswith('VCB-Studio') and default.g != 'VCB-Studio' and default.x == '':
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


def fillAutoIndex(default:INFO, infos: list[INFO], logger:logging.Logger) -> Any:

    # we have the following kinds of files:
    # auto: fully auto indexed files
    # ref: naming takes reference to another file
    # custom: fully custom specified files

    a_infos : list[INFO] = [info for info in infos if not info.c]
    r_infos : list[INFO] = [info for info in infos if (info.c and re.match(CRC32_CSV_PATTERN, info.c))]
    c_infos : list[INFO] = [info for info in infos if (info.c and not re.match(CRC32_CSV_PATTERN, info.c))]

    state : dict[str, int|float] = {}
    for i, info in enumerate(a_infos):
        i1 = '' if info.i1 == None else info.i1
        i2 = '' if info.i2 == None else info.i2
        if i1 and i2:
            state[f'{info.e}//{info.g}//{info.s}//{info.l}//{info.t}//{info.x}'] = i1
            state[f'{info.e}//{info.g}//{info.s}//{info.l}//{info.t}//{i1}//{info.x}'] = i2
        elif i1 and not i2:
            state[f'{info.e}//{info.g}//{info.s}//{info.l}//{info.t}//{info.x}'] = i1
            # whether we need to update i2 depends on whether there is a same key
            key = f'{info.e}//{info.g}//{info.s}//{info.l}//{info.t}//{i1}//{info.x}'
            if (v := state.get(key)):
                v = int(v+1)
                a_infos[i] = info._replace(i2=v)
                state[key] = v
                continue
            else: # we need to loop though the remaining to find the same key
                for j, jnfo in enumerate(a_infos[i+1:]):
                    j1 = '' if jnfo.i1 == None else jnfo.i1
                    j2 = '' if jnfo.i2 == None else jnfo.i2
                    jey = f'{jnfo.e}//{jnfo.g}//{jnfo.s}//{jnfo.l}//{jnfo.t}//{j1}//{jnfo.x}'
                    if key == jey:
                        a_infos[i] = info._replace(i2=1)
                        state[key] = 1
        else: # if not i1
            key = f'{info.e}//{info.g}//{info.s}//{info.l}//{info.t}//{info.x}'
            if (v := state.get(key)):
                v = int(v+1)
                a_infos[i] = info._replace(i1=v)
                state[key] = v
                continue
            else: # we need to loop through the remaining to find the same key
                for j, jnfo in enumerate(a_infos[i+1:]):
                    j1 = '' if jnfo.i1 == None else jnfo.i1
                    j2 = '' if jnfo.i2 == None else jnfo.i2
                    jey = f'{jnfo.e}//{jnfo.g}//{jnfo.s}//{jnfo.l}//{jnfo.t}//{jnfo.x}'
                    if key == jey:
                        a_infos[i] = info._replace(i1=1)
                        state[key] = 1

    for i, info in enumerate(r_infos):

        found = None
        for jnfo in (a_infos + c_infos):
            if jnfo.crc == info.c:
                found = jnfo
                break
        if found != None:
            r_infos[i] = info._replace(l=found.l, t=found.t, i1=found.i1, i2=found.i2, n=found.n, c=found.c)
            logger.info(f'File "{info.crc}" copied naming from file "{found.crc}".')
        else:
            raise ValueError('Trying to refer to the naming of an inexisting/disabled file.')

    return a_infos + r_infos + c_infos




def fmtContentName(infos: list[INFO], logger:logging.Logger):

    max_index = {}
    for info in [info for info in infos if not info.c]:
        l, t, i1, i2 = info.l, info.t, info.i1, info.i2
        if i2 is not None:
            key = '{}//{}//{}'.format(l, t, i1)
            max_index[key] = max(max_index.get(key, -99999), i2)
        if i1 is not None:
            key = '{}//{}'.format(l, t)
            max_index[key] = max(max_index.get(key, -99999), i1)

    for i, info in enumerate(infos):
        if not info.c:
            l, t, i1, i2, n = info.l, info.t, info.i1, info.i2, info.n

            if i2 is not None:
                m2 = max(1, len(str(max_index['{}//{}//{}'.format(l, t, i1)]).split('.')[0]))
                if i2 == int(i2): # integer
                    i2 = ('{:' + f'0{m2}.0f' + '}').format(i2)
                else: # float
                    n2 = len(str(max_index['{}//{}//{}'.format(l, t, i1)]).split('.')[1])
                    i2 = ('{:' + f'0{m2+n2+1}.{n2}f' + '}').format(i2)
            else:
                i2 = ''

            if i1 is not None:
                m1 = max(2, len(str(max_index['{}//{}'.format(l, t)]).split('.')[0]))
                if i1 == int(i1): # integer
                    i1 = ('{:' + f'0{m1}.0f' + '}').format(i1)
                else: # float
                    n1 = len(str(max_index['{}//{}'.format(l, t)]).split('.')[1])
                    i1 = ('{:' + f'0{m1+n1+1}.{n1}f' + '}').format(i1)
            else:
                i1 = ''

            spaced = True if ((' ' in t) or (' ' in n)) else False
            if spaced:
                temp = '{tn}' + (' ' if t else '') + '{i1}' + ('-' if i2 else '') + '{i2}'
                temp +=  (' ' if n else '') + '{nt}'
            else:
                temp = '{tn}' + '{i1}' + ('_' if i2 else '') + '{i2}'
                temp +=  (('' if n.startswith('(') else '_') if n else '') + '{nt}'

            infos[i] = info._replace(t='', i1=None, i2=None, n='', c=temp.format(tn=t, i1=i1, i2=i2, nt=n))




def chkFinalNaming(infos: list[INFO], logger:logging.Logger) -> bool:
    '''Check if the final naming plan has any conflict.'''
    ok = True

    names = []
    for info in infos:
        name = f'{info.e}//{info.g}//{info.s}//{info.l}//{info.c}//{info.x}'
        names.append(name)

    for i, name in enumerate(names):
        for j, name2 in enumerate(names[i+1:]):
            if name == name2:
                logger.error('Found naming conflict: "' + infos[i].src + '" vs "' + infos[i+j].src + '".')
                ok = False
                break

    return ok




def procDefaultNaming(default:dict, logger:logging.Logger):
    '''Check the default config.'''

    if not (gname := procSeasonGroupTag(cleanGroupName(default[GRPTAG_VAR]), '', logger)):
        logger.error(f'The base group name is either empty or incorrect.')

    if not (sname := chkShowName(cleanName(default[SHOWNAME_VAR]), '', logger)):
        logger.error(f'The base showname is either empty or incorrect.')

    if (suffix := chkSuffix(cleanSuffix(default[SUFFIX_VAR]), '', default[FULLPATH_VAR], logger)):
        logger.info(f'Using base suffix "{suffix}"')

    return INFO(g=gname, s=sname, x=suffix)




def chkNamingInfos(infos:list[dict], default:INFO, logger:logging.Logger) -> list[INFO]:

    ret : list[INFO] = []

    for i, info in enumerate(infos):

        crc32 : str = info[CRC32_VAR]
        srcpath : str = info[FULLPATH_VAR]
        gname : str = info[GRPTAG_VAR]
        sname : str = info[SHOWNAME_VAR]
        loc : str = info[LOCATION_VAR]
        tname : str = info[TYPENAME_VAR]
        idx1 : str = info[IDX1_VAR]
        idx2 : str = info[IDX2_VAR]
        note : str = info[NOTE_VAR]
        cname : str = info[CUSTOM_VAR]
        suffix : str = info[SUFFIX_VAR]
        ext : str = srcpath.lower().split('.')[-1]

        logger.info(f'Checking the file with CRC32 "{crc32}"...')

        if DEBUG: logger.info(f'User Input: "{gname}|{sname}|{loc}|{tname}|{idx1}|{idx2}|{note}|{cname}|{suffix}"')

        gname : str = cleanGroupName(gname)
        sname : str = cleanName(sname)
        loc : str = cleanPath(loc)
        tname : str = cleanName(tname)
        idx1 : str = cleanDecimal(idx1)
        idx2 : str = cleanDecimal(idx2)
        note : str = cleanName(note)
        cname : str = cleanName(cname)
        suffix : str = cleanSuffix(suffix)

        if DEBUG: logger.info(f'Cleaned: "{gname}|{sname}|{loc}|{tname}|{idx1}|{idx2}|{note}|{cname}|{suffix}"')

        if not (gname := procSeasonGroupTag(gname, default.g, logger)):
            logger.error(f'Got an empty groupname.')
            return []
        if not (sname := chkShowName(sname, default.s, logger)):
            logger.error(f'Got an empty showname.')
            return []

        if (cname := chkCustom(cname, ext, logger)):
            tname, idx1, idx2, note = '', None, None, ''
        else:
            tname = procTypeName(tname, logger)
            idx1, idx2 = procIndex(idx1, idx2, logger)
            note = chkNote(note, logger)

        loc = chkLocation(loc, tname, logger)
        suffix = chkSuffix(suffix, default.x, srcpath, logger)

        if DEBUG: logger.info(f'Checked: "{gname}|{sname}|{loc}|{tname}|{idx1}|{idx2}|{note}|{cname}|{suffix}"')

        # looks good, now save the processed key:value for later usage
        # this dict layout is re-used in all subsequent functions
        info=INFO(crc=crc32, src=srcpath, dst='', g=gname, s=sname, l=loc, t=tname, i1=idx1, i2=idx2,
                  n=note, c=cname, x=suffix, e=ext)
        ret.append(info)

    return ret




def chkNaming(default_info:dict, naming_infos:list[dict], logger:logging.Logger) \
    -> tuple[bool, INFO, list[INFO]]:
    '''Check the naming plan given by user and further format it for later actual naming.'''

    logger.info('Checking the base naming config (@default) .....................................')
    default : INFO = procDefaultNaming(default_info, logger)
    if (not default.g) or (not default.s):
        return False, default, []
    logger.info(f'@default = "{default.g}|{default.s}|{default.x}"')

    logger.info('Checking the naming config of each file ........................................')
    infos : list[INFO] = chkNamingInfos(naming_infos, default, logger)

    logger.info('Performing auto indexing .......................................................')
    infos = fillAutoIndex(default, infos, logger)

# assert bool(cname) != any((tname, idx1, idx2, note)), 'doNaming() enforces' # TODO move this to after auto indexing

    logger.info('Assembling the final content name ..............................................')
    fmtContentName(infos, logger)

    logger.info('Checking correlated naming restriction .........................................')
    infos = chkCorrelatedNaming(infos, logger)

    logger.info('Checking global naming restriction .............................................')
    chkGlobalNaming(default, infos, logger)

    logger.info('Checking final naming conflict .................................................')
    if not chkFinalNaming(infos, logger):
        logger.error('VNE stopped because of naming conflict.')
        return False, default, []

    logger.info(f'Final Naming ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓')
    ret_infos = []
    for naming_info in naming_infos:
        for info in infos:
            if naming_info[CRC32_VAR] == info.crc:
                ret_infos.append(info)
                break
        else:
            raise ValueError('The number of naming infos must match.')
    for i, naming_info in zip(ret_infos, naming_infos):
        g = naming_info[GRPTAG_VAR]
        s = naming_info[SHOWNAME_VAR]
        l = naming_info[LOCATION_VAR]
        t = naming_info[TYPENAME_VAR]
        i1 = naming_info[IDX1_VAR]
        i2 = naming_info[IDX2_VAR]
        n = naming_info[NOTE_VAR]
        c = naming_info[CUSTOM_VAR]
        x = naming_info[SUFFIX_VAR]
        logger.info(f'"{i.crc}" : "{g}|{s}|{l}|{t}|{i1}|{i2}|{n}|{c}|{x}" → "{i.g}|{i.s}|{i.l}|{i.c}|{i.x}"')
    logger.info(f'↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑')

    return True, default, ret_infos




def doNaming(dst_dir_parent:Path, default:INFO, infos:list[INFO], hardlink:bool, logger:logging.Logger) -> bool:
    '''
    Perform the naming plan onto disk.

    Arguments:
    dst_parent: Path : the output dir will be under this dir
    default: INFO : the base/default naming config
    infos: list[INFO] : the naming config of each files
    hardlink: bool : whether to use hardlink or not
    logger: Logger

    Return:
    bool: whether the whole job is completed without error
    '''

    # the quality label for the root dir is determined by files at the root dir
    root_qlabel : str = ''
    qlabels : dict[str, int] = {} # candidate quality labels
    for info in [info for info in infos if info.l == '']:
        minfo : MI = getMediaInfo(info.src)
        if minfo.video_tracks:
            q = fmtQualityLabel(minfo, logger)
            qlabels[q] = qlabels.get(q, 0) + 1
    if qlabels: root_qlabel = max(qlabels, key=qlabels.get)
    else: logger.warning('No video enabled/located at root dir. The output dirname will have no quality label.')

    # now create the root dir
    root_qlabel = (f'[{root_qlabel}]' if root_qlabel else '')
    root_suffix = (f'[{default.x}]' if default.x else '')
    dst_dir = dst_dir_parent.joinpath(f'[{default.g}] {default.s} {root_qlabel}{root_suffix}')
    dst_dir.mkdir(parents=True, exist_ok=True) # the possible trailing space seems not matter
    logging.info(f'Created base dir "{dst_dir}"')

    # then the files
    # we need to process independent files first
    # because the q/t-label for mkv/mp4 must be determined before mka/ass copying
    # TODO: save quality label and track label in `INFO` before `doNaming()`

    dep_infos = list(info for info in infos if info.e in VNx_DEP_EXTS)
    idp_infos = list(info for info in infos if info.e not in VNx_DEP_EXTS)

    for i, idp_info in enumerate(idp_infos):
        g = idp_info.g
        s = idp_info.s
        c = f'[{c}]' if (c := idp_info.c) else '' # some files may have no content name
        minfo : MI = getMediaInfo(idp_info.src)
        q = f'[{q}]' if (q := fmtQualityLabel(minfo, logger)) else ''
        t = f'[{t}]' if (t := fmtTrackLabel(minfo, logger)) else ''
        x = (f'.{idp_info.x}' if (idp_info.e in VNx_SUB_EXTS) else f'[{idp_info.x}]') if idp_info.x else ''
        e = idp_info.e
        idp_infos[i] = idp_info._replace(dst=str(dst_dir.joinpath(idp_info.l, f'[{g}] {s} {c}{q}{t}{x}.{e}')))

    for i, dep_info in enumerate(dep_infos):
        g = dep_info.g
        s = dep_info.s
        c = f'[{c}]' if (c := dep_info.c) else '' # some files may have no content name
        counterparts = [info for info in idp_infos if all(cmpNamingInfo(info, dep_info)[:8])] # match any except suffix
        if counterparts:
            q = f'[{q}]' if (q := fmtQualityLabel(getMediaInfo(counterparts[0].src), logger)) else ''
            t = f'[{t}]' if (t := fmtTrackLabel(getMediaInfo(counterparts[0].src), logger)) else ''
            if counterparts[1:]:
                logger.warning(f'Found more than 1 counterpart videos for "{dep_info.crc}" '
                               f'to copy quality/track label You config may be incorrect.')
        else:
            logger.error(f'Cannot find a counterpart video for "{dep_info.crc}" to copy quality/track label.')
            q = '[x]'
            t = '[x]'
        x = (f'.{dep_info.x}' if (dep_info.e in VNx_SUB_EXTS) else f'[{dep_info.x}]') if dep_info.x else ''
        e = dep_info.e
        dep_infos[i] = dep_info._replace(dst=str(dst_dir.joinpath(dep_info.l, f'[{g}] {s} {c}{q}{t}{x}.{e}')))

    # everything looks ok so far, now start creating the target
    for info in (idp_infos + dep_infos):
        src, dst = Path(info.src), Path(info.dst)
        if src.resolve() == dst.resolve():
            logger.error('Source and destination are the same.')
            continue
        parent = dst.parent
        if parent.is_file():
            logger.error(f'Failed to create "{dst.relative_to(dst_dir)}" (its parent is a file)')
        else:
            if not parent.exists():
                parent.mkdir(parents=True, exist_ok=True)
                logger.info(f'Created dir "{parent}"')
            if dst.is_file():
                dst.unlink()
                logger.warning(f'Removed existing file "{dst.relative_to(dst_dir)}"')
            if hardlink:
                dst.hardlink_to(src)
            else:
                shutil.copy(src, dst)
            logger.info(f'Created file "{dst.relative_to(dst_dir)}" ({info.crc})')

    return True




def tstUserIO(src:list[Path], dst:Path, logger:logging.Logger) -> tuple[bool, bool, bool]:
    '''This is a boring check to test if we can read/write the dst dir, and if we can hardlink from src to dst.'''

    src_files : list[Path] = [Path(path) for path in src]
    dst_parent : Path = Path(dst)

    # empty src input is abnormal
    if not src_files:
        logger.error('Input files not specified.')
        return False, False, False

    # test that every input file is readable
    for path in src_files:
        try:
            path.is_file()
            (fobj := path.open(mode='rb')).read(1)
            fobj.close()
        except FileNotFoundError:
            logger.error(f'Failed to locate the input file "{path}".')
            return False, False, False
        except OSError:
            logger.error(f'Failed to test reading the input file "{path}".')
            return False, False, False
        except Exception as e:
            logger.error(f'Failed to test reading the input file "{path}" due to an unexpected error {e}. Please Report.')
            return False, False, False

    # test dst parent exists as a dir
    try:
        if not dst_parent.is_dir():
            dst_parent.mkdir(parents=True, exist_ok=True)
        assert dst_parent.is_dir()
    except OSError:
        logger.error(f'Failed to create to output parent.')
        return False, False, False
    except AssertionError:
        logger.error(f'Failed to verify to output parent.')
        return False, False, False
    except Exception as e:
        logger.error(f'Failed to test the output parent due to an unexpected error {e}. Please Report.')
        return False, False, False

    # test creating and delete files under the dst parent
    dst_testfile = dst_parent.joinpath('1234567890'*23 + '.tt')
    try:
        dst_testfile.touch()
        dst_testfile.write_bytes(b'1234567890')
        assert dst_testfile.read_bytes() == b'1234567890'
        dst_testfile.unlink()
    except OSError:
        logger.error('Failed to read/write a test file of 233 chars filename. Available path length may be inadequate.')
        return False, False, False
    except AssertionError:
        logger.error('Failed to verify a test file at the output parent. Your OS/Disk may be corrupted.')
        return False, False, False
    except Exception as e:
        logger.error(f'Failed to test r/w under the output parent due to an unexpected error {e}. Please Report.')
        return False, False, False

    # test if we can use multiprocesssing for the input
    multiproc = True
    for path in src_files:
        try:
            if not ssd_checker.is_ssd(path):
                logger.info(f'"{path}" is not an SSD.')
                multiproc = False
                break
        except KeyError:
            logger.info(f'SSD checker cannot check "{path}". Falling back to user config.')
            multiproc = MULTI_PROC_FALLBACK
            break
        except Exception as e:
            logger.warning(f'SSD checker failed with an unexpected error {e}. Please report.')
            multiproc = MULTI_PROC_FALLBACK
            break

    # test if we can use hardlink for this job
    dst_testfile = dst_parent.joinpath('vne_temp_test_file')
    src_testfile = src_files[0]
    hardlink = True
    try:
        if dst_testfile.exists():
            dst_testfile.unlink()
        dst_testfile.hardlink_to(src_testfile)
        dst_testfile.unlink()
    except OSError as e:
        hardlink = False
    except Exception as e:
        logger.error(f'Failed to test hardlink due to an unexpected error {e}. Please report.')
        hardlink = False
    finally:
        try:
            dst_testfile.unlink()
        except Exception:
            pass

    return True, multiproc, hardlink




def verifyFiles(infos:list[dict[str, str]], logger:logging.Logger, multiproc:bool=False) -> list[dict[str, str]]:
    '''Check the file specified in CSV exists or not and verify if the CRC32 matches.'''

    valid_infos = []
    for info in infos:
        if Path(path := info[FULLPATH_VAR]).is_file():
            valid_infos.append(info)
        else:
            logger.warning(f'Excluding not-found file in user input: "{path}".')

    crc32s = getCRC32List([info[FULLPATH_VAR] for info in valid_infos], multiproc)
    for crc32, info in zip(crc32s, valid_infos):
        if crc32 != info[CRC32_VAR]:
            logger.warning(f'CRC32 mismatch. (expect {info[CRC32_VAR]} got {crc32} from "{info[FULLPATH_VAR]}").')

    return valid_infos




def season(input_csv_path:Path):

    logger = initLogger(log_path := input_csv_path.parent.joinpath(f'VNE-{TIMESTAMP}.log'))
    logger.info(f'Using VideoNamingExecutor (VNE) of AfterCollation {AC_VERSION}')

    logger.info('Loading the naming draft (VND.csv) .............................................')
    logger.info(f'The input csv is "{input_csv_path}"')
    default_info, naming_infos = loadNamingDraftCSV(input_csv_path, logger)
    if not naming_infos:
        logger.error('VNE stopped because no file is valid or enabled in the CSV file.')
        logging.shutdown()
        return
    dst_dir_parent = Path(p) if (p := default_info[FULLPATH_VAR]) else input_csv_path.parent
    logger.info(f'The output dir will be under "{dst_dir_parent}"')


    logger.info(f'Testing the output dir and its hardlink availability ...........................')
    input_files = [Path(naming_info[FULLPATH_VAR]) for naming_info in naming_infos]
    success, multiproc, hardlink = tstUserIO(input_files, dst_dir_parent, logger)
    if not success:
        logger.error(f'VNE stopped because of a failure in testing input/output files/folder. Please check the permission.')
        logging.shutdown()
        return
    if multiproc: logger.info('Enabled multi-processing.')
    else: logger.warning('Disabled multi-processing (slower crc32 verification).')
    if hardlink: logger.info('Enabled hardlink mode.')
    else: logger.warning('Disabled hardlink mode (much slower output creation).')


    logger.info('Verifying CRC32 ................................................................')
    naming_infos = verifyFiles(naming_infos, logger, multiproc)
    if not naming_infos:
        logger.error('VNE stopped because no file exists to do later execution.')
        logging.shutdown()
        return


    logger.info('Checking the naming draft ......................................................')
    success, default, naming_drafts = chkNaming(default_info, naming_infos, logger)
    if not success:
        logger.info('VNE stopped because of unresolvable issues in naming instructions.')
        logging.shutdown()
        return


    logger.info('Executing the naming plan ......................................................')
    success = doNaming(dst_dir_parent, default, naming_drafts, hardlink, logger)
    if not success:
        logger.info('VNE stopped because of a failure in creating output files.')
        logging.shutdown()
        return


    logging.shutdown()
    return




def _cli(*paths:Path):

    n = len(paths)
    if n == 1 and paths[0].is_file() and paths[0].suffix.lower() == '.csv':
        season(paths[0])
    else:
        printCliNotice(VNE_USAGE, paths)




if __name__ == '__main__':
    paths = [Path(p) for p in sys.argv[1:]]
    if DEBUG:
        _cli(*paths)
    else: # if catch the exception as below, vscode doesn't jump to the actual line
        try:
            _cli(*paths)
        except Exception as e:
            print(f'!!! Run into an unexpected error:\n{e}\nPlease report.')

    input('Press ENTER to exit...')
