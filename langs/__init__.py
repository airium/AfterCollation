from configs.user import LANGUAGE as __LANGUAGE
import importlib as __importlib

# # https://stackoverflow.com/a/43059528/14040883
# __translations = __importlib.import_module(f'.{__LANGUAGE}', __package__)
# if "__all__" in __translations.__dict__:
#     __names = __translations.__dict__["__all__"]
# else:
#     __names = [x for x in __translations.__dict__ if not x.startswith("_")]
# globals().update({k: getattr(__translations, k) for k in __names})


match __LANGUAGE:
    case 'en_GB':
        from .en_GB import *
    case 'en_US':
        from .en_US import *
    case 'zh_CN':
        from .zh_CN import *
    case _:
        raise ValueError(f'Unsupported language "{__LANGUAGE}".')
