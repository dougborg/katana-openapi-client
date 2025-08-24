from enum import Enum


class ServiceVariantType(str, Enum):
    SERVICE = "service"

    def __str__(self) -> str:
        return str(self.value)
