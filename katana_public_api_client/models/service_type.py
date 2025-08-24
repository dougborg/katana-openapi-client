from enum import Enum


class ServiceType(str, Enum):
    SERVICE = "service"

    def __str__(self) -> str:
        return str(self.value)
