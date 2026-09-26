"""MT5 execution boundary. Phase 1 deliberately has no order implementation."""
from abc import ABC, abstractmethod


class ExecutionDisabledError(RuntimeError):
    """Raised when an order is requested while execution is disabled."""


class MT5ExecutionPort(ABC):
    @abstractmethod
    def submit_demo_order(self, *args, **kwargs):
        raise NotImplementedError


class DisabledMT5Execution(MT5ExecutionPort):
    def submit_demo_order(self, *args, **kwargs):
        raise ExecutionDisabledError("MT5 order execution is disabled in Phase 1")
