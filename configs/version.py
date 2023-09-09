# version description
# the base format is major.minor.patch.date
# major
# bumping major version means it forces everyone to update
# it bumps only in the event of breaking changes or lots of feature updates (in minors) to push to users
# minor
# bumping minor means that there is a feature update/improvement
# normally only a few feature updates require no immediate update by users
# minor version is preserved when bumping major, except for breaking changes that recount feature update
# patch
# patch is bugfix or implementation tweak that brings no feature update
# patch number always got reset when major/minor bumps
# date
# format is YYMMDD, which gives a fast insight on what should be done



DATE = '230908'

AC_VERSION = '0.12.0' + '.' + DATE
