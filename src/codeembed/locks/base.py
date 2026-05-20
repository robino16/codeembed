from abc import ABC, abstractmethod


class LockBase(ABC):
    @abstractmethod
    def try_acquire(self) -> bool: ...

    @abstractmethod
    def release(self) -> None: ...

    def __enter__(self) -> "LockBase":
        return self

    def __exit__(self, *args: object) -> None:
        self.release()
