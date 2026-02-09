from enum import StrEnum


class CreateProductOperationRowItemType(StrEnum):
    FIXED = "fixed"
    PERUNIT = "perUnit"
    PROCESS = "process"
    SETUP = "setup"

    def __str__(self) -> str:
        return str(self.value)
