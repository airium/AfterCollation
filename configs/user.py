'''
The file lists hard-coded configs for the user to customize the program behaviors.
'''

#* basic user config ---------------------------------------------------------------------------------------------------

# you can add necessary paths here so making AC able to locate executables at your preference
# adding paths to file wont matter as the program will trim the filename and append only the dir to PATH
#! expanding environment variable is supported, but you should use '$' instead of '%' even if on Windows
USER_PATHS : list[str] = [
    '%USERPROFILE%/scoop/shims',
    'C:/Program Files/WinRAR',
    'C:/Program Files (x86)/WinRAR',
    'C:/Program Files/7-Zip',
    # add you paths below

    #  'C:\Program Files',  #! dont add the path string like this
    #  'C:/Program Files',  #! use forward slash
    # r'C:\Program Files',  #! or prepend 'r' to avoid escaping
    ]

# if you want to be more conscious about the path to certain executables, you can specify it here
# they are the same effect as `USER_PATHS`
FFMPEG_PATH : str = ''
RAR_PATH : str = ''

# this is the temporary directory used to decompress 7z/zip/rar and so check its content
#! if using a relative path, take care that it means the relative path to the script location
# by default, items will be decompressed to the os-provided temp idr
# this is, %TEMP% (=%LOCALAPPDATA%/Temp on Windows), or /tmp on Linux/Mac
#! you should use '$' to indicate an environment variable even if on Windows
# all decompressed files will be immediately deleted after the program exits
TEMP_DIRPATH_DECOMPRESS : str = '$TEMP'

# the temporary directory for SR to create hardlinks
# a relative path is relative to the drive root where the working files are located
#! if using an absolute path, make sure the path is on the same partition as your working files
TEMP_DIRNAME_HARDLINK : str = '@AC-Temp'

# enable this option to attach an audio digest for each m2ts with audio tracks in VNA.csv
# this will make VND more accurate in matching the encoded MKV/MP4 to the original M2TS and then copy the naming
# note that this will cause full reading m2ts files, significantly slowing down VNA
ENABLE_AUDIO_SAMPLES_IN_VNA : bool = True

# this is the default output format from VNA
VNA_DEFAULT_CONFIG = {'csv': True, 'yaml': False, 'json': False }

# you can optionally turn off the file checking in VND
# this will make VND much faster to generate the naming proposal (VND.csv)
# which would be helpful when you are adding new files frequently
ENABLE_FILE_CHECKING_IN_VND : bool = True

# file checking should be done in VND and re-done in VNR
# but if you want to be noticed earlier after VNE, enable this option
# note this will much slow down VNE
ENABLE_FILE_CHECKING_IN_VNE : bool = False

# use at most this number of multi-proc workers for IO-intensive jobs e.g. CRC32
# the default value 8 should be able to max out PCIe 4.0 x4 SSDs
# it will be automatically lower to not exceed the number of physical CPU cores
MAX_NUM_IO_WORKERS : int = 8

# whether to still enable multi-processing when ssd checker failed
# it typically happens when you're using certain RAMDISK on Windows e.g. ImDisk
# ssd checker cannot lookup the device type of such SCSI devices
ENABLE_MULTI_PROC_IF_UNSURE : bool = False

# this is used to determine the number of multi-proc workers for CPU/RAM-intensive jobs
# the number is calculated based on your available RAM at script startup, not the total RAM
# it will be automatically lower to not exceed the number of physical CPU cores
MIN_RAM_PER_WORKER : int = 10 # this unit is GiB

# whether to use VGMDB/MB/FREEDB in MusicRechecker
ENABLE_VGMDB : bool = True
ENABLE_MUSICBREAINZ : bool = False
ENABLE_FREEDB : bool = False

# proxy and user agent to connect outside
#! refactoring vgmdb with requests has not been completed
#! for now, you can only use http proxy, i.e. no socks5
PROXY : str = ''
# PROXY : str = 'http://127.0.0.1:7890'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'

# output language of all scripts
#! it has no usage for now
LANGUAGE = 'en-GB'

#* advanced user config ------------------------------------------------------------------------------------------------

# copping black edges of videos results in an actual height of 1072px or similar
# such video is still considered to be labeled as 1080px
# if the resultant height >= this value (default=900), the program sill mark it as 1080px
MIN_VID_HEIGHT_TO_STILL_LABEL_AS_1080 : int = 900
assert 720 < MIN_VID_HEIGHT_TO_STILL_LABEL_AS_1080 <= 1080 # use 1080 to disable this option

# media tracks can differ a little bit in duration, which is normal from some Web/BDMV/DVD sources
# this is the upper threshold in millisecond in duration difference between tracks in a video file
# this value should be more loose than `SAME_DURATION_THRESHOLD`
MAX_DURATION_DIFF_BETWEEN_TRACKS : int = 200

# different encoders can sometimes encode the final to difference duration from the same source
# this is the upper threshold in millisecond in duration difference so we still consider them as the same
# the default value (50ms) allowed a single frame difference under 23.976fps (~42ms per frame)
SAME_DURATION_THRESHOLD : int  = 50

# the chapter timestampped at the end of the video should be removed
# any chapter locates within this time (in ms) to the end of the video will be considered to be unnecessary
MIN_DISTANCE_FROM_LASTER_CHAP_TO_END : int = 3000

# rarely, we get no metadata/filename clue to determine if audios within a folder is of split or joint-tracks layout
# in such case, we can guess based on the number of audio tracks
# if the number audio exceeds this number, we consider the album is of track-split layout
# the default value is set 5, as it's very rare that a single ALBUM have more than 5 discs
# in practice, such case is only seen in the complete soundtrack album of some game series with decades of history
#! setting this value too low will decrease the reliability of Mx tools
MIN_NUM_AUDIO_TO_SEEN_AS_SPLIT_TRACK_DISC : int = 5

# warn the user of image files smaller than this size (unit: B)
SMALL_IMAGE_FILE_SIZE = 1024

# normally, we consider A3 (297x420mm) is the largest size that a regular home scanner can do
# so the max possible pixel count along the long side under 600dpi is 420/25.4*600=9921px
# if any side exceeds 10000px, tell the user to consider downsampling from the 'useless' 1200dpi
LARGE_SCANS_THRESHOLD = 10000

# warn that user if the cover art is unnecessarily large
# digital cover art rarely exceeds ~3000px
NORMAL_COVER_ART_LENGTH = 4000 # 4000px
NORMAL_COVER_ART_FILESIZE = 10 * 1024 * 1024 # 10MiB

#* algorithms ----------------------------------------------------------------------------------------------------------

# if the ASS subtitle contains at least this number of unique characters in CHS/CHT/JPN
# it is then considered to be CHS/CHT/JPN
MIN_UNIQUE_CHAR_IN_ASS : int = 5

# this is the start point and length (both in second) used to detect the offset between two audio tracks
# change them accordingly if you want to detect the offset from other interval
CHK_OFFSET_STA : int = 0
CHK_OFFSET_LEN : int = 30
assert CHK_OFFSET_LEN > 0

# we know (a²+b²) is at least 2 times of a*b (==2 if a==b), and the multiplier become larger if a/b are apart farther
# but if the multiplier is below `XCORR_RATIO`, we still think a≈b
# this is used to match lossless/lossy encoded audios
XCORR_RATIO : int = 4
assert XCORR_RATIO >= 2 # 2 means only exactly match is accepted

# if the average difference on samples is below this value, then we think 2 audio are the same
# note the difference is defined in integer value of signed 16-bit PCM, i.e. the max/min value of audio is 32767/-32768
# NOTE 1 in 16-bit integer PCM == 1.5e-6 for floating PCM (2**16*1.5e-5=0.98)
MAX_DIFF_MEAN : int = 1

#* others --------------------------------------------------------------------------------------------------------------

# this is the show name that will be applied when the program didn't correctly catch your mistake of forgetting filling any showname for VND. This should never appear on your hard disk - but if you see it, please fill a bug report.
FALLBACK_TITLE = '1145141919810'

#* don't touch below --------------------------------------------------------------------------------------------------

import psutil
cpu, ram = psutil.cpu_count(logical=False), psutil.virtual_memory().total // (1024**3)
NUM_IO_JOBS = min(cpu, MAX_NUM_IO_WORKERS)
NUM_CPU_JOBS = min(cpu, max(ram // (MIN_RAM_PER_WORKER), 1))
del psutil, cpu, ram


if TEMP_DIRNAME_HARDLINK:
    from pathlib import Path
    TEMP_DIR_PATH = Path(TEMP_DIRNAME_HARDLINK)
    del Path
else:
    TEMP_DIR_PATH = None


import os, pathlib
if TEMP_DIRNAME_HARDLINK:
    TEMP_DIR_HARDLINK = pathlib.Path(os.path.expandvars(TEMP_DIRNAME_HARDLINK))
else:
    TEMP_DIR_HARDLINK = pathlib.Path('@AC-TEMP')
del os, pathlib, TEMP_DIRNAME_HARDLINK


import os, pathlib
if TEMP_DIRPATH_DECOMPRESS:
    TEMP_DIR_DECOMPRESS = pathlib.Path(os.path.expandvars(TEMP_DIRPATH_DECOMPRESS))
else:
    TEMP_DIR_DECOMPRESS = pathlib.Path(os.path.expandvars('$TEMP'))
del os, pathlib, TEMP_DIRPATH_DECOMPRESS


if not LANGUAGE:
    import locale
    LANGUAGE = locale.getdefaultlocale()[LANGUAGE]
    del locale


if PROXY:
    import os
    os.environ['HTTP_PROXY'] = PROXY
    os.environ['HTTPS_PROXY'] = PROXY
    os.environ['SOCKS_PROXY'] = PROXY
    del os
