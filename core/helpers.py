from typing import *

import errorHandler

def ToInt(s:Union[str, bytes]) -> int:
    try:
        i = int(s)
        return i
    except Exception:
        errorHandler.error("[ToInt.py]: Data: [" + s + "] is not suitable for convertion!")
