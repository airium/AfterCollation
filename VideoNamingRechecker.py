from imports import *

VNR_USAGE = '''
VideoNamingRechecker (VNR) accepts the following input:
1. one dir -> do basic checking without reference group
2. two dirs -> match videos inside two dirs and generate a VNR.csv for your review
3. one VNR.csv -> do video comparison as instructed in CSV
4. even numbers of files (mkv/mp4/png/flac) -> do video comparison
'''




def main2doStandardCheck(input_dir:Path):

    logger = initLogger(log_path := input_dir.parent.joinpath(f'VNR-{TIMESTAMP}.log'))
    logger.info(f'Using VideoNamingRechecker (VNR) of AfterCollation {AC_VERSION}')
    logger.info(f'Mode: do standard checking of naming and files for "{input_dir}".')

    subdirs = listDir(input_dir, rglob=False)
    subfiles = listDir(input_dir, rglob=False)

    if not subdirs and not subfiles:
        logger.error(f'Cannot check empty dir "{input_dir}".')
    # NOTE we just assume so, this is not robust however
    elif subdirs and not subdirs:
        chkSeriesNaming(input_dir, logger)
    else:
        chkSeasonNaming(input_dir, logger)

    logger.info('')
    logger.info('NEXT:')
    logger.info(f'View the log "{log_path}".')
    logger.info(f'For any ERROR, you should now start fixing them.')
    logger.info(f'For any WARNING, you should make sure they do not matter.')
    logger.info(f'Some INFO may still contain a notice, do not skip them too fast.')
    logger.info('')




def main2doComparisonFromCSV(input_csv_path:Path):

    logger = initLogger(log_path := input_csv_path.parent.joinpath(f'VNR-{TIMESTAMP}.log'))
    logger.info(f'Using VideoNamingRechecker (VNR) of AfterCollation {AC_VERSION}')
    logger.info(f'Mode: do video comparison as instructed in "{input_csv_path}".')

    succ, groups = readCSV4VNR(input_csv_path)
    if not succ:
        logger.error(f'Failed to read "{input_csv_path}".')
        logging.shutdown()
        return

    for grouping_id, group_items in groups.items():

        if not grouping_id:
            continue

        logger.info(f'------------------------------------------------------------------------------------------------')
        logger.info(f'Checking grouping "{grouping_id}" with the following items:')
        subgrps, enableds, fullpaths = zip(*group_items)
        enableds = toEnabledList(enableds)
        for sub_grp, enabled, fullpath in zip(subgrps, enableds, fullpaths):
            logger.info(f'{sub_grp:s} ({"E" if enabled else "D"}): "{fullpath}"')
        if sum(enableds) < 2:
            logger.warning('Cannot check this group due to <2 items enabled. Skipping.')
            continue
        subgrps = [sub_grp for sub_grp, enabled in zip(subgrps, enableds) if enabled]
        fullpaths = [full_path for full_path, enabled in zip(fullpaths, enableds) if enabled]
        subgrp_tags = list(set(subgrps))
        assert subgrp_tags # this should never happen

        fullpaths = [Path(fullpath) for fullpath in fullpaths]
        all_files_exist = True
        for fullpath in fullpaths:
            if not fullpath.is_file():
                logger.error(f'File "{fullpath}" is missing.')
                all_files_exist = False
        if not all_files_exist:
            logger.error('Some files are missing. Please check again.')
            continue

        # NOTE this is no longer considered as unsupported
        # if len(valid_subgrps) > 2:
        #     logger.error(f'>2 subgroups defined in group "{grouping_id}". It will be converted to 2 subgroups.')
        #     valid_subgrps = valid_subgrps[:2]
        #     subgrps = [(valid_subgrps[-1] if (sub_grp not in valid_subgrps) else sub_grp) for sub_grp in subgrps]
        #     logger.info(f'Converted subgrouping:')
        #     for sub_grp, fullpath in zip(subgrps, fullpaths):
        #         logger.info(f'{sub_grp:s}: "{fullpath}"')

        if len(subgrp_tags) == 1:
            subgrps = ['1', '2']
            if len(fullpaths) > 2:
                logger.warning('>2 items defined in a single subgroup. Plz note auto subgrouping is not accurate.')
                base_parent = fullpaths[0].parent
                for i, fullpath in zip(itertools.count(), fullpaths):
                    subgrps[i] = '1' if fullpath.is_relative_to(base_parent) else '2'
                logger.info(f'Auto subgrouping:')
                for sub_grp, fullpath in zip(subgrps, fullpaths):
                    logger.info(f'{sub_grp:s}: "{fullpath}"')

        src = [fullpath for (sub_grp, fullpath) in zip(subgrps, fullpaths) if sub_grp == subgrp_tags[0]]
        refs = []
        for subgrp_tag in subgrp_tags[1:]:
            refs.append([fullpath for (sub_grp, fullpath) in zip(subgrps, fullpaths) if sub_grp == subgrp_tag])

        doComparison(src, *refs, grpname=grouping_id, subgrps_names=subgrp_tags, logger=logger)




def main2doMatching2CSV(input1_dir:Path, input2_dir:Path):

    log_path = findCommonParentDir(input1_dir, input2_dir)
    if not log_path:
        print('!!! Cannot find a common parent dir of your input. '
              'Output log will be located at the same dir as this script.')
        log_path = Path(__file__).parent.joinpath(f'VNR-{TIMESTAMP}.log')
    elif log_path.is_dir():
        log_path = log_path.joinpath(f'VNR-{TIMESTAMP}.log')
    else:
        log_path = log_path.parent.joinpath(f'VNR-{TIMESTAMP}.log')

    logger = initLogger(log_path)
    logger.info(f'Using VideoNamingRechecker (VNR) of AfterCollation {AC_VERSION}')
    logger.info(f'Mode: try video matching between "{input1_dir}" and "{input2_dir}".')

    assert input1_dir.is_dir() and input2_dir.is_dir()

    input1_fs_all : list[Path] = listFile(input1_dir, ext=VNx_MAIN_EXTS)
    input2_fs_all : list[Path] = listFile(input2_dir, ext=VNx_MAIN_EXTS)
    input1_fs = filterOutCDsScans(input1_fs_all)
    input2_fs = filterOutCDsScans(input2_fs_all)
    if len(input1_fs) != len(input1_fs_all):
        logger.info(f'Removed some FLAC in {STD_CDS_DIRNAME} from the input dir "{input1_dir}".')
    if len(input2_fs) != len(input2_fs_all):
        logger.info(f'Removed some FLAC in {STD_CDS_DIRNAME} from the input dir "{input2_dir}".')

    input1_cfs = [CF(f) for f in input1_fs]
    input2_cfs = [CF(f) for f in input2_fs]

    groups : dict[str, list[tuple[str, str, str]]] = dict()
    if not input1_cfs or not input2_cfs:
        logger.warning('No video files found in either of the input dirs.')
        logger.info('VNR will still try to generate a non-ref CSV in case you want to fill it by yourself.')
        if input1_cfs and not input2_cfs:
            for i, input1_cf in enumerate(input1_cfs):
                groups[str(i)] = [('', '', input1_cf.path.resolve().as_posix())]
        elif input2_cfs and not input1_cfs:
            for i, input2_cf in enumerate(input2_cfs):
                groups[str(i)] = [('', '', input2_cf.path.resolve().as_posix())]
        else:
            raise ValueError # NOTE this should be never reached

        csv_parent = findCommonParentDir(input1_dir, input2_dir)
        if not csv_parent: csv_path = input1_dir.parent.joinpath(f'VNR-{TIMESTAMP}.csv')
        else: csv_path = csv_parent.joinpath(f'VNR-{TIMESTAMP}.csv')
        if writeCSV4VNR(csv_path, groups):
            logger.info(f'Successfully written to "{csv_path}"..')
        else:
            logger.error(f'Failed to write to "{csv_path}".')
        logging.shutdown()
        return

    groups : dict[str, list[tuple[str, str, str]]] = dict()
    idx = itertools.count(1)

    # now let's start matching, we do it in this order:
    # 1. match by chapter timestamps, high robust (may fail if main videos rarely use identical chapters)
    # 2. match by audio samples, high robust (may fail in CMs with identical audio)
    # 3. match by duration, mid robust (may fail in any videos having identical duration)

    #***********************************************************************************************
    # step 1: match by chapter timestamps

    for input1_cf in input1_cfs[:]: # make a copy of the list, so we can call .remove() in the loop
        # NOTE we only match the first menu track, is this not robust enough?
        matches = [input2_fi for input2_fi in input2_cfs if (
                   input1_cf.menu_tracks and input2_fi.menu_tracks
                   and matchMenuTimeStamps(input1_cf.menu_timestamps[0], input2_fi.menu_timestamps[0]))]
        if len(matches) == 1:
            groups[str(next(idx))] = [
                ('1', '', input1_cf.path.resolve().as_posix()),
                ('2', '', matches[0].path.resolve().as_posix())
            ]
            input1_cfs.remove(input1_cf)
            input2_cfs.remove(matches[0])
            logger.info(f'Matched by chapter timestamp: "{input1_cf.path}" <-> "{matches[0].path}"')
        elif len(matches) > 1:
            logger.warning(f'Cannot match "{input1_cf.path}" as multiple counterparts have the same chapter timestamp.')
        else:
            if input1_cf.menu_tracks:
                logger.warning(f'Cannot match "{input1_cf.path}" as NO counterpart has the same chapter timestamp.')

    #***********************************************************************************************
    # step 2: match by audio digest
    if ENABLE_VNA_AUDIO_SAMPLES:
        for input1_cf in input1_cfs[:]: # make a copy of the list, so we can call .remove() in the loop
            matches = [input2_fi for input2_fi in input2_cfs \
                       if cmpAudioSamples(input1_cf.audio_samples, input2_fi.audio_samples)]
            if len(matches) == 1:
                groups[str(next(idx))] = [
                    ('1', '', input1_cf.path.resolve().as_posix()),
                    ('2', '', matches[0].path.resolve().as_posix())
                ]
                input1_cfs.remove(input1_cf)
                input2_cfs.remove(matches[0])
                logger.info(f'Matched by audio digest: "{input1_cf.path}" <-> "{matches[0].path}"')
            elif len(matches) > 1:
                logger.warning(f'Cannot match "{input1_cf.path}" as multiple counterparts have the same audio digest.')
            else:
                if input1_cf.audio_samples:
                    logger.warning(f'Cannot match "{input1_cf.path}" as NO counterpart has the same audio digest.')

    #***********************************************************************************************
    # step 3: match by duration
    for input1_cf in input1_cfs[:]: # make a copy of the list, so we can call .remove() in the loop
        matches = [input2_fi for input2_fi in input2_cfs if (
                    input1_cf.has_duration and input2_fi.has_duration
                    and matchTime(input1_cf.duration, input2_fi.duration))]
        if len(matches) == 1:
            groups[str(next(idx))] = [
                ('1', '', input1_cf.path.resolve().as_posix()),
                ('2', '', matches[0].path.resolve().as_posix())
            ]
            input1_cfs.remove(input1_cf)
            input2_cfs.remove(matches[0])
            logger.info(f'Matched by duration: "{input1_cf.path}" <-> "{matches[0].path}"')
        elif len(matches) > 1:
            # TODO this implementation is dirty, fix it
            if all('menu' in fi.path.name.lower() for fi in (input1_cf, *matches)):
                subidx = itertools.count(1)
                group : list[tuple[str, str, str]] = []
                group.append((str(next(subidx)), '', input1_cf.path.resolve().as_posix()))
                for match in matches:
                    group.append((str(next(subidx)), '', match.path.resolve().as_posix()))
                    input2_cfs.remove(match)
                input1_cfs.remove(input1_cf)
                groups[str(next(idx))] = group
                logger.info(f'Matched by duration for menus: "{input1_cf.path}". (NOTE this is not robust)')
            else:
                logger.warning(f'Cannot match "{input1_cf.path}" as multiple counterparts have the same duration.')
        else:
            logger.warning(f'Cannot match "{input1_cf.path}" as NO counterpart has the same duration.')

    # we need to do this again for input2_fis
    for input2_cf in input2_cfs[:]: # make a copy of the list, so we can call .remove() in the loop
        matches = [input1_fi for input1_fi in input1_cfs if (
                    input2_cf.has_duration and input1_fi.has_duration
                    and matchTime(input2_cf.duration, input1_fi.duration))]
        if len(matches) == 1:
            groups[str(next(idx))] = [
                ('1', '', input2_cf.path.resolve().as_posix()),
                ('2', '', matches[0].path.resolve().as_posix())
            ]
            input2_cfs.remove(input2_cf)
            input1_cfs.remove(matches[0])
            logger.info(f'Matched by duration: "{matches[0].path}" <-> "{input2_cf.path}"')
        elif len(matches) > 1:
            # TODO this implementation is dirty, fix it
            if all('menu' in fi.path.name.lower() for fi in (input2_cf, *matches)):
                subidx = itertools.count(1)
                group : list[tuple[str, str, str]] = []
                group.append((str(next(subidx)), '', input2_cf.path.resolve().as_posix()))
                for match in matches:
                    group.append((str(next(subidx)), '', match.path.resolve().as_posix()))
                    input1_cfs.remove(match)
                input2_cfs.remove(input2_cf)
                groups[str(next(idx))] = group
                logger.info(f'Matched by duration for menus: "{input2_cf.path}". (NOTE this is not robust)')
            else:
                logger.warning(f'Cannot match "{input2_cf.path}" as multiple counterparts have the same duration.')
        else:
            logger.warning(f'Cannot match "{input2_cf.path}" as NO counterpart has the same duration.')

    #***********************************************************************************************
    # slicing is common in videos, so we need to match the rest by filename

    for input1_cf in [input1_fi for input1_fi in input1_cfs if input1_fi.menu_tracks]:
        timestamps = input1_cf.menu_timestamps[0]
        if len(timestamps) < 2: continue # this seems an incorrect menu
        distances = [(timestamps[i+1] - timestamps[i]) for i in range(len(timestamps)-1)]
        founds : list[CF] = []
        for i, distance in enumerate(distances):
            for input2_cf in input2_cfs:
                if input2_cf in founds: continue
                if matchTime(distance, input2_cf.duration):
                    founds.append(input2_cf)
                    break
        if len(founds) == len(distances):
            matched_group : list[tuple[str, str, str]] = []
            matched_group.append(('1', '', input1_cf.path.resolve().as_posix()))
            for found in founds:
                matched_group.append(('2', '', found.path.resolve().as_posix()))
                input2_cfs.remove(found)
            input1_cfs.remove(input1_cf)
            groups[str(next(idx))] = matched_group
            logger.info(f'Matched sliced videos: {input1_cf}')

    # we need to do this again for input2_fis
    for input2_cf in [input2_fi for input2_fi in input2_cfs if input2_fi.menu_tracks]:
        timestamps = input2_cf.menu_timestamps[0]
        if len(timestamps) < 2: continue # this seems an incorrect menu
        distances = [(timestamps[i+1] - timestamps[i]) for i in range(len(timestamps)-1)]
        founds : list[CF] = []
        for i, distance in enumerate(distances):
            for input1_cf in input1_cfs:
                if input1_cf in founds: continue
                if matchTime(distance, input1_cf.duration):
                    founds.append(input1_cf)
                    break
        if len(founds) == len(distances):
            matched_group : list[tuple[str, str, str]] = []
            # NOTE always place input1_fis first
            for found in founds:
                matched_group.append(('1', '', found.path.resolve().as_posix()))
                input1_cfs.remove(found)
            input2_cfs.remove(input2_cf)
            matched_group.append(('2', '', input2_cf.path.resolve().as_posix()))
            groups[str(next(idx))] = matched_group
            logger.info(f'Matched sliced videos: {input2_cf}')

    #***********************************************************************************************
    # place all the rest into an unnamed group
    unmatched_group : list[tuple[str, str, str]] = []
    for input1_cf in input1_cfs:
        unmatched_group.append(('', '', input1_cf.path.resolve().as_posix()))
    for input2_cf in input2_cfs:
        unmatched_group.append(('', '', input2_cf.path.resolve().as_posix()))
    if unmatched_group:
        groups[''] = unmatched_group

    #***********************************************************************************************
    # write the result to a CSV

    csv_parent = findCommonParentDir(input1_dir, input2_dir)
    if not csv_parent: csv_path = input1_dir.parent.joinpath(f'VNR-{TIMESTAMP}.csv')
    else: csv_path = csv_parent.joinpath(f'VNR-{TIMESTAMP}.csv')
    if writeCSV4VNR(csv_path, groups):
        logger.info(f'Successfully written to "{csv_path}".')
        logger.info('')
        logger.info('NEXT:')
        logger.info('Please check again the matching result.')
        logger.info('And then drop the CSV to VNR again to start the comparison.')
        logger.info('')
    else:
        logger.error(f'Failed to write to "{csv_path}".')




def main2doDroppedComparison(*paths:Path):

    assert len(paths) % 2 == 0
    group1 = paths[:len(paths)//2]
    group2 = paths[len(paths)//2:]

    log_path = findCommonParentDir(*paths)
    if not log_path:
        print('!!! Cannot find a common parent dir of your input. '
              'Output log will be located at the same dir as this script.')
        log_path = Path(__file__).parent.joinpath(f'VNR-{TIMESTAMP}.log')
    elif log_path.is_dir():
        log_path = log_path.joinpath(f'VNR-{TIMESTAMP}.log')
    else:
        log_path = log_path.parent.joinpath(f'VNR-{TIMESTAMP}.log')

    logger = initLogger(log_path)
    logger.info(f'Using VideoNamingRechecker (VNR) of AfterCollation {AC_VERSION}')
    logger.info(f'Mode: do video comparison from directly dropped files.')

    total = len(group1)
    for i, (path1, path2) in enumerate(zip(group1, group2)):
        logger.info(f'------------------------------------------------------------------------------------------------')
        logger.info(f'Checking grouping "{i+1:03d}/{total:03d}" with the following items:')
        logger.info(f'a: "{path1}"')
        logger.info(f'b: "{path2}"')
        doComparison([path1], [path2], logger=logger)




def _cli(*paths:Path):

    n = len(paths)
    if (n == 1) and (path := paths[0]).is_dir():
        main2doStandardCheck(paths[0])
    elif (n == 1) and (path := paths[0]).is_file() \
    and re.match(VNR_TABLE_FILENAME_PATTERN, path.name):
        main2doComparisonFromCSV(paths[0])
    elif n == 2 and paths[0].is_dir() and paths[1].is_dir():
        main2doMatching2CSV(paths[0], paths[1])
    elif paths and (not n % 2) and all(p.is_file() and p.suffix.endswith(VNx_MAIN_EXTS) for p in paths):
        main2doDroppedComparison(*paths)
    else:
        printCliNotice(VNR_USAGE, paths)




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
