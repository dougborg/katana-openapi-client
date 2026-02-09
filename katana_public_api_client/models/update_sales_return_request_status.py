from enum import StrEnum


class UpdateSalesReturnRequestStatus(StrEnum):
    NOT_RETURNED = "NOT_RETURNED"
    RESTOCKED_ALL = "RESTOCKED_ALL"
    RETURNED_ALL = "RETURNED_ALL"

    def __str__(self) -> str:
        return str(self.value)
