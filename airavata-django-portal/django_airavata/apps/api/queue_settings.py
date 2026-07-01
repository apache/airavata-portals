"""In-process queue-settings calculator registry (no framework deps).

A gateway registers calculators with :func:`queue_settings_calculator`, then the
``QueueSettingsCalculatorViewSet`` invokes them by id via
:func:`calculate_queue_settings`; positional/keyword args are forwarded verbatim
to the registered callable.

This is a portal extension point (relocated from the retired
``airavata.helpers.queue_settings``): gateway apps import
``queue_settings_calculator`` from here to register their calculators.
"""

from __future__ import annotations

from collections.abc import Callable
from types import FunctionType
from typing import Any, NamedTuple

QUEUE_SETTINGS_CALCULATORS: list[QueueSettingsCalculator] = []


class QueueSettingsCalculator(NamedTuple):
    id: str
    name: str
    func: FunctionType


def queue_settings_calculator(
    _func: FunctionType | None = None,
    *,
    id: str | None = None,
    name: str | None = None,
    **kwargs: Any,
) -> Callable[..., Any]:
    def decorator(func: FunctionType) -> FunctionType:
        name_ = name
        if name_ is None:
            name_ = func.__name__
        id_ = id
        if id_ is None:
            id_ = func.__module__ + ":" + func.__name__
        if exists(id_):
            raise Exception(f"Duplicate queue settings calculator id: {id_}")
        QUEUE_SETTINGS_CALCULATORS.append(QueueSettingsCalculator(id_, name_, func))
        return func

    if _func is None:
        return decorator
    else:
        return decorator(_func)


def calculate_queue_settings(calculator_id: str, *args: Any, **kwargs: Any) -> Any:
    calcs = [calc for calc in QUEUE_SETTINGS_CALCULATORS if calc.id == calculator_id]
    if len(calcs) == 0:
        raise LookupError(
            f"Could not find queue settings calculator for {calculator_id}"
        )
    calc = calcs[0]
    try:
        return calc.func(*args, **kwargs)
    except Exception as e:
        raise Exception(
            f"Failed to calculate queue settings for {calculator_id}"
        ) from e


def get_all() -> list[QueueSettingsCalculator]:
    return QUEUE_SETTINGS_CALCULATORS.copy()


def exists(calculator_id: str) -> bool:
    calcs = [calc for calc in QUEUE_SETTINGS_CALCULATORS if calc.id == calculator_id]
    return len(calcs) == 1


def reset_registry() -> None:
    global QUEUE_SETTINGS_CALCULATORS
    QUEUE_SETTINGS_CALCULATORS = []
