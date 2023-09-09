from pathlib import Path
from logging import Logger
from typing import Iterable, Optional

from langs import *
from configs import *
from utils import findCommonParentDir


__all__ = ['proposePath', 'initScansDraftDstParentDir', 'initAlbumDraftDstParentDir']




def proposePath(paths: Iterable[Path], dst_filename: str, logger: Logger|None = None) -> Path:
    paths = list(paths)
    if not paths: raise ValueError(GOT_NO_INPUT_0)
    call = logger.info if logger else lambda msg: print(msg)
    if not (log_path := findCommonParentDir(*paths)):
        log_path = paths[0].parent / dst_filename
        call(CANT_PROPOSE_COMMON_PARENT_FOR_LOG_1.format(log_path))
    elif log_path.is_dir():
        log_path = log_path.joinpath(dst_filename)
    else:
        log_path = log_path.parent.joinpath(dst_filename)
    return log_path




def initScansDraftDstParentDir(
    *, dst_path: Path|None = None, input_paths: list[Path]|None = None, script_path: Path|None = None
    ) -> Path:

    if dst_path:
        if dst_path.is_dir():
            return dst_path
        elif dst_path.is_file():
            pass
        else:
            try:
                dst_path.mkdir(parents=True, exist_ok=True)
                return dst_path
            except:
                pass

    if SD_WORKING_DIR:
        sd_dir = Path(SD_WORKING_DIR)
        if sd_dir.is_dir():
            return sd_dir
        elif sd_dir.is_file():
            pass
        if not sd_dir.is_file():
            try:
                sd_dir.mkdir(parents=True, exist_ok=True)
                return sd_dir
            except:
                pass

    if input_paths:
        if common_path := findCommonParentDir(*input_paths):
            return common_path

    if script_path:
        return script_path.parent

    raise NotADirectoryError(CANT_INIT_OUTPUT_DIR_0)




def initAlbumDraftDstParentDir(
    *, dst_path: Optional[Path] = None, input_paths: Optional[list[Path]] = None, script_path: Optional[Path] = None
    ) -> Path:

    if dst_path:
        if dst_path.is_dir():
            return dst_path
        elif dst_path.is_file():
            pass
        else:
            try:
                dst_path.mkdir(parents=True, exist_ok=True)
                return dst_path
            except:
                pass

    if AD_WORKING_DIR:
        ad_dir = Path(AD_WORKING_DIR)
        if ad_dir.is_dir():
            return ad_dir
        elif ad_dir.is_file():
            pass
        if not ad_dir.is_file():
            try:
                ad_dir.mkdir(parents=True, exist_ok=True)
                return ad_dir
            except:
                pass

    if input_paths:
        if common_path := findCommonParentDir(*input_paths):
            return common_path

    if script_path:
        return script_path.parent

    raise NotADirectoryError(CANT_INIT_OUTPUT_DIR_0)
