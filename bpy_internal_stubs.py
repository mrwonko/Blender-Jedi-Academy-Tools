"""
Equivalents for the types from bpy.stub_internal, which we don't want to import directly.

The goal here is to satisfy the type checker.
"""

import typing

OperatorReturnItems = typing.Literal[
    "RUNNING_MODAL",  # Running Modal.Keep the operator running with blender.
    "CANCELLED",  # Cancelled.The operator exited without doing anything, so no undo entry should be pushed.
    "FINISHED",  # Finished.The operator exited after completing its action.
    "PASS_THROUGH",  # Pass Through.Do nothing and pass the event on.
    "INTERFACE",  # Interface.Handled but not executed (popup menus).
]
