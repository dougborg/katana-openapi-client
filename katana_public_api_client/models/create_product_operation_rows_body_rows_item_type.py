from enum import Enum


class CreateProductOperationRowsBodyRowsItemType(str, Enum):
    FIXED = "fixed"
    PERUNIT = "perUnit"
    PROCESS = "process"
    SETUP = "setup"

    def __str__(self) -> str:
        return str(self.value)
