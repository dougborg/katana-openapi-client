from enum import Enum


class WebhookLogsExportRequestStatusFilterItem(str, Enum):
    FAILURE = "failure"
    RETRY = "retry"
    SUCCESS = "success"

    def __str__(self) -> str:
        return str(self.value)
