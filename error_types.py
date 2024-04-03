from .mod_reload import reload_modules
reload_modules(locals(), __package__, [], [".casts"])  # nopep8

from typing import List, NewType, Optional, Tuple, TypeVar
from .casts import optional_list_cast

ErrorMessage = NewType("ErrorMessage", str)
NoError = ErrorMessage("")

T = TypeVar("T")


def ensureListIsGapless(l: List[Optional[T]]) -> Tuple[Optional[List[T]], ErrorMessage]:
    emptyIndices = [i for i, x in enumerate(l) if x is None]
    if len(emptyIndices) > 0:  # a surface that was referenced did not get created
        return None, ErrorMessage(f"unexpected None at indices {emptyIndices}")
    return optional_list_cast(List[T], l), NoError
