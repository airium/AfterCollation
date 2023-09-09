import time

# the timestamp at script startup
TIMESTAMP: str = time.strftime('%y%m%d-%H%M%S')
# the year at script startup
THIS_YEAR: int = int(time.strftime('%Y'))
# the month at script startup
THIS_MONTH: int = int(time.strftime('%m'))
# this day at script startup
THIS_DAY: int = int(time.strftime('%d'))

YYMMDD: str = time.strftime('%y%m%d')
HHMMSS: str = time.strftime('%H%M%S')
