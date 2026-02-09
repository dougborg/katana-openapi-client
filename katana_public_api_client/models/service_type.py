from enum import StrEnum


class ServiceType(StrEnum):
    SERVICE = "service"

    def __str__(self) -> str:
        return str(self.value)
