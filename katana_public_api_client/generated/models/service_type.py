from enum import Enum


class ServiceType(str, Enum):
    SERVICES = "services"

    def __str__(self) -> str:
        return str(self.value)
