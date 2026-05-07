from enum import StrEnum


class DependenciesValidationErrorCode(StrEnum):
    DEPENDENCIES = "dependencies"

    def __str__(self) -> str:
        return str(self.value)
