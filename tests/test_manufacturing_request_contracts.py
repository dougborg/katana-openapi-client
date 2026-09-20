"""Wire serialization of the live-verified #830 contracts."""

from http import HTTPStatus

import httpx
import pytest
from pydantic import ValidationError

from katana_public_api_client.api.serial_number.create_serial_numbers import (
    _parse_response,
)
from katana_public_api_client.client import Client
from katana_public_api_client.models import (
    CreateSerialNumbersRequest,
    UpdateManufacturingOrderOperationRowRequest,
)
from katana_public_api_client.models_pydantic._generated import (
    UpdateManufacturingOrderOperationRowRequest as PydanticOperationPatch,
)


def test_operation_patch_needs_only_changed_field() -> None:
    request = UpdateManufacturingOrderOperationRowRequest(operation_name="Polish")
    assert request.to_dict() == {"operation_name": "Polish"}
    assert (
        PydanticOperationPatch(operation_name="Polish").to_attrs().to_dict()
        == request.to_dict()
    )


def test_operation_patch_rejects_parent_id() -> None:
    with pytest.raises(ValidationError):
        PydanticOperationPatch.model_validate({"manufacturing_order_id": 1})


def test_serial_creation_omissions_and_empty_success() -> None:
    assert CreateSerialNumbersRequest(resource_id=1).to_dict() == {"resource_id": 1}
    response = httpx.Response(HTTPStatus.NO_CONTENT)
    assert (
        _parse_response(
            client=Client(
                base_url="https://example.test", raise_on_unexpected_status=True
            ),
            response=response,
        )
        is None
    )
