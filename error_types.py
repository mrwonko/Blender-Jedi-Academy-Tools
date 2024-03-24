from typing import NewType

ErrorMessage = NewType("ErrorMessage", str)
NoError = ErrorMessage("")
