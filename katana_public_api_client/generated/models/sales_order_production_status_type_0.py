from enum import Enum


class SalesOrderProductionStatusType0(str, Enum):
    BLOCKED = "BLOCKED"
    DONE = "DONE"
    IN_PROGRESS = "IN_PROGRESS"
    NONE = "NONE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_STARTED = "NOT_STARTED"

    def __str__(self) -> str:
        return str(self.value)
