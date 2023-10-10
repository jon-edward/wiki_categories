import abc
from typing import Optional

import tqdm

__all__ = (
    "ProgressManager",
    "NoopProgressManager",
    "TqdmProgressManager"
)


class ProgressManager(abc.ABC):
    """
    Abstract class that specifies desired functionality for a progress manager for streaming.
    """

    @abc.abstractmethod
    def start(self, total: int) -> None:
        """
        Is called before a resource starts streaming.

        :param total:  Total size of compressed resource in bytes
        """

    @abc.abstractmethod
    def update(self, n: int) -> None:
        """
        Is called throughout streaming.

        :param n:  Size of bytes received from stream.
        """

    @abc.abstractmethod
    def close(self) -> None:
        """
        Is called after streaming has finished.
        """


class NoopProgressManager(ProgressManager):
    """
    A progress manager with no functionality.
    """

    def start(self, _total: int):
        pass

    def update(self, _n: int):
        pass

    def close(self):
        pass


class TqdmProgressManager(ProgressManager):
    """
    A progress manager that uses tqdm to log progress.
    """

    _p_bar: Optional[tqdm.tqdm] = None

    def start(self, total: int):
        assert self._p_bar is None, "Tried to call 'start' twice before 'close'."
        self._p_bar = tqdm.tqdm(total=total, unit='B', unit_scale=True, unit_divisor=1024)

    def update(self, n: int):
        assert self._p_bar is not None, "Tried to call 'update' before 'start'."
        self._p_bar.update(n)

    def close(self):
        assert self._p_bar is not None, "Tried to call 'close' before 'start'."
        self._p_bar.close()
        self._p_bar = None
