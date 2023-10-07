"""
Contains logic for streaming a gzip-compressed external resource,
and exposes custom functionality for logging progress.

Example usage:

>>> from requests import Session
>>>
>>> url = "https://dumps.wikimedia.org/enwiki/20230920/enwiki-20230920-categorylinks.sql.gz"
>>> session = Session()
>>> progress_manager = TqdmProgressManager()
>>>
>>> for line in GzipResource(url, session, progress_manager).stream_lines():
>>>     ...  # Do something with line.
"""


import abc
import zlib
from typing import Optional, Generator

import tqdm as tqdm
from requests import Session


class ProgressManager(abc.ABC):
    """
    Abstract class that specifies desired functionality for a progress manager for streaming.
    """

    @abc.abstractmethod
    def start(self, total: int) -> None:
        """
        Is called before a resource starts streaming.

        :param total:  Total size of compressed resource in bytes
        :return:
        """

    @abc.abstractmethod
    def update(self, n: int) -> None:
        """
        Is called throughout streaming.

        :param n:  Size of bytes received from stream.
        :return:
        """

    @abc.abstractmethod
    def close(self) -> None:
        """
        Is called after streaming has finished.

        :return:
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


class Resource(abc.ABC):
    """
    An abstract class that defines expected functionality for streaming a resource.
    """

    @abc.abstractmethod
    def stream_lines(self) -> Generator[bytes, None, None]:
        """
        Is intended to be used to generate buffered lines of a resource.
        See GzipResource for implementation.
        """
        ...


class GzipResource(Resource):
    """
    Used to stream a gzip-compressed resource.
    """

    url: str
    session: Session
    progress_manager: ProgressManager

    def __init__(self, url: str, session: Session, progress_manager: ProgressManager):
        self.url = url
        self.session = session
        self.progress_manager = progress_manager

    def stream_lines(self) -> Generator[bytes, None, None]:
        """
        Streams bytes of a resource, split on "\\n".

        :return:  The generator that yields lines of the resource.
        """

        response = self.session.get(self.url, stream=True)

        size: int = int(response.headers["Content-Length"])
        self.progress_manager.start(size)

        decompress_obj = zlib.decompressobj(16 + zlib.MAX_WBITS)
        content = response.iter_content(chunk_size=1024)

        buffer = b""

        for c in content:
            self.progress_manager.update(len(c))

            buffer += decompress_obj.decompress(c)

            try:
                split_at = buffer.index(b"\n")
                yield buffer[:split_at]
                buffer = buffer[split_at+1:]

            except ValueError:
                continue

        for tail_line in buffer.split(b"\n"):
            yield tail_line

        self.progress_manager.close()
