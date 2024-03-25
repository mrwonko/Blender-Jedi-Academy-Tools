from typing import List, Optional, cast
import mathutils
from typing import Any, TypeVar, Type

T = TypeVar('T')

# Aliases for type casts with stricter semantics.
# These are unchecked, but should help identify dangerous code pieces.
# Try to avoid naked cast(), it is too ambiguous.


def optional_cast(t: Type[T], v: Optional[T]) -> T:
    """
    A cast used to turn Optional[T] into T.
    This is a code smell. Where this is needed, the code should be restructured,
    so that it is no longer needed. It's a result from mutability overuse.
    TODO: remove all optional_casts
    """
    return cast(t, v)


def optional_list_cast(t: Type[List[T]], v: List[Optional[T]]) -> List[T]:  # TODO replace with error-returning helper
    return cast(t, v)


# A cast used to turn A | B into A or B, for properties that accept unions in the setter but return a fixed type in the setter.
# Blender uses this extensively to allow assigning sequences in place of vectors and matrices,
# and mypy doesn't currently support differing types in setters (https://github.com/python/mypy/issues/3004)
# and the bpy bindings don't currently define separate setter/getter (https://github.com/nutti/fake-bpy-module/issues/158)
getter_cast = cast


def matrix_getter_cast(x: Any) -> mathutils.Matrix:
    """Shorthand for getter_cast(mathutils.Matrix, x)"""
    return getter_cast(mathutils.Matrix, x)


def vector_getter_cast(x: Any) -> mathutils.Vector:
    """Shorthand for getter_cast(mathutils.Vector, x)"""
    return getter_cast(mathutils.Vector, x)


# A cast used to turn a type into one of its sub-types.
# Should happen close to a check that ensures this is valid.
downcast = cast

# A cast to resolve polymorphic functions being annotated with union return types instead of proper overloads.
overload_cast = cast


def vector_overload_cast(x: Any) -> mathutils.Vector:
    """
    Shorthand for overload_cast(mathutils.Vector, x).
    Matrix and Quaternion multiplication currently lacks overloads to distinguish vector returns.
    """
    return overload_cast(mathutils.Vector, x)


def matrix_overload_cast(x: Any) -> mathutils.Matrix:
    """
    Shorthand for overload_cast(mathutils.Matrix, x).
    Matrix and Quaternion multiplication currently lacks overloads to distinguish matrix returns.
    """
    return overload_cast(mathutils.Matrix, x)


# A cast for elements of bpy collections.
# For some reason, the generics of bpy.types.bpy_prop_collection aren't working for me.
# Once that's resolved, these casts can be replaced with proper generic annotations.
bpy_generic_cast = cast

# A cast for the result of struct.unpack().
# Python's type system is not powerful enough to express the correct return type.
# Make sure these casts correspond to the unpack format string.
unpack_cast = cast
