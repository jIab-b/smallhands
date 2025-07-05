"""Abstract executor for SmallHands."""
from abc import ABC, abstractmethod
from typing import Any, Callable

class BaseExecutor(ABC):
    """Executor interface."""
    @abstractmethod
    def submit(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        ...

    @abstractmethod
    def shutdown(self) -> None:
        ...
