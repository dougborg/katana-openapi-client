from enum import Enum


class ServiceRequestDataType(str, Enum):
    SERVICES = "services"

    def __str__(self) -> str:
        return str(self.value)
