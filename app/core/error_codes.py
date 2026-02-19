from enum import Enum


class ErrorCode(str, Enum):
    # Validation
    VAL_REQUEST_INVALID = "VAL_REQUEST_001"

    # Resources
    RES_USER_NOT_FOUND = "RES_USER_001"

    # System
    SYS_INTERNAL_ERROR = "SYS_001"