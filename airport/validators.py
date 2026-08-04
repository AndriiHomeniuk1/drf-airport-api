from typing import Type

from django.core.exceptions import ValidationError
from django.db import models


def validate_is_active(
    field_name: str,
    instance: models.Model,
    error_to_raise: Type[Exception] = ValidationError
) -> None:
    if not instance.is_active:
        raise error_to_raise(
            {
                field_name: (
                    f"{instance.__class__.__name__} "
                    f"\"{instance}\" is no longer active."
                )
            }
        )
