from typing import List, Optional, Union, cast
import mathutils
from typing import Any, TypeVar, Type

T = TypeVar('T')
U = TypeVar('U')

# Aliases for type casts with stricter semantics.
# These are unchecked, but should help identify dangerous code pieces.
# Try to avoid naked cast(), it is too ambiguous.


def optional_cast(t: Type[T], v: Optional[T]) -> T:
    """
    A cast used to turn Optional[T] into T.
    This is a code smell. Where possible, just improve the typing.
    One acceptable use case are Panels. Their draw() function is only called when poll() returns true.
    So any None-checks performed in poll() can be assumed to have succeeded in draw().
    TODO: remove all non-Panel optional_casts
    """
    return cast(T, v)


def optional_list_cast(t: Type[List[T]], v: List[Optional[T]]) -> List[T]:
    """
    Avoid using this directly, use error_types.ensureListIsGapless instead.
    """
    return cast(List[T], v)


def union_cast(t: Type[T], v: Union[T, U]) -> T:
    """A cast from a union to one of its elements"""
    return cast(T, v)


# A cast used to turn a type into one of its sub-types.
# Should happen close to a check that ensures this is valid.
downcast = cast

# A cast for the result of struct.unpack().
# Python's type system is not powerful enough to express the correct return type.
# Make sure these casts correspond to the unpack format string.
unpack_cast = cast
