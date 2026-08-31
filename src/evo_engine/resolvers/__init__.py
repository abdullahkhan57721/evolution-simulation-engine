"""Domain-neutral simulation event resolver foundations."""

from evo_engine.resolvers._preference_order import (
    resolve_capacity_preference_order,
    resolve_exclusive_preference_order,
)
from evo_engine.resolvers.accept_all import AcceptAll

__all__ = [
    "AcceptAll",
    "resolve_capacity_preference_order",
    "resolve_exclusive_preference_order",
]
