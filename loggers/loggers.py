import logging
from pathlib import Path
from configs.debug import LOG_LEVEL

__all__ = ['initLogger']


def initLogger(log_path:str|Path):
    log_path = Path(log_path)
    logging.basicConfig(filename=log_path,
                        datefmt='%Y%m%d-%H%M%S',
                        format='%(levelname)s: %(message)s',
                        encoding='utf-8-sig')
    logger = logging.getLogger()
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(logging.StreamHandler()) # print log to stdout
    logger.info(f'Initialised log at "{log_path}".')
    return logger
