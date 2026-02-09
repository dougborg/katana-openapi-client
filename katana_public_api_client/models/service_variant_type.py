from enum import StrEnum


class ServiceVariantType(StrEnum):
    SERVICE = "service"

    def __str__(self) -> str:
        return str(self.value)
