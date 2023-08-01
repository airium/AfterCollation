import logging
from pathlib import Path
from utils.fileutils import listFile, listDir
from configs.specification import ALL_EXTS_IN_SCANS, STD_BKS_DIRNAME


__all__ = ['getScansDirs', 'getScansFiles']




def getScansDirs(root:Path, logger:logging.Logger) -> list[Path]:

    scans_dirs = [d for d in listDir(root) if d.name.lower() == STD_BKS_DIRNAME.lower()]
    if not scans_dirs:
        logger.warning(f'No "{STD_BKS_DIRNAME}" is found. '
                       f'SR will consider the input "{root}" as a "{STD_BKS_DIRNAME}" folder.')
        scans_dirs = [root]

    ret = []
    for scans_dir in scans_dirs:
        if scans_dir == root:
            ret.append(scans_dir)
            break
        # avoid duplicated processing of scans dir under scans dir
        parent_has_scans = False
        for p in scans_dir.parent.relative_to(root).as_posix().split('/'):
            if p.lower() == STD_BKS_DIRNAME.lower():
                parent_has_scans = True
                break
        if parent_has_scans: continue
        ret.append(scans_dir)
    return ret




def getScansFiles(scans_dir:Path, logger:logging.Logger) -> list[Path]:

    all_files = listFile(scans_dir)
    scans_files = listFile(scans_dir, ext=ALL_EXTS_IN_SCANS)
    if (diffs := set(all_files).difference(set(scans_files))):
        for diff in diffs:
            logger.error(f'Disallowed file "{diff}".')
    return scans_files
