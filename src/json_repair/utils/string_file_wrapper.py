import os
from typing import TextIO


class StringFileWrapper:
    # This is a trick to simplify the code, transform the filedescriptor handling into a string handling
    def __init__(self, fd: TextIO, chunk_length: int) -> None:
        """
        Initialize the StringFileWrapper with a file descriptor and chunk length.

        Args:
            fd (TextIO): The file descriptor to wrap.
            CHUNK_LENGTH (int): The length of each chunk to read from the file.

        Attributes:
            fd (TextIO): The wrapped file descriptor.
            length (int): The total length of the file content.
            buffers (dict[int, str]): Dictionary to store chunks of file content.
            buffer_length (int): The length of each buffer chunk.
        """
        self.fd = fd
        # Buffers are chunks of text read from the file and cached to reduce disk access.
        self.buffers: dict[int, str] = {}
        if not chunk_length or chunk_length < 2:
            chunk_length = 1_000_000
        # chunk_length now refers to the number of characters per chunk.
        self.buffer_length = chunk_length
        # Keep track of the starting file position ("cookie") for each chunk so we can
        # seek safely without landing in the middle of a multibyte code point.
        self._chunk_positions: list[int] = [0]
        self.length: int | None = None

    def get_buffer(self, index: int) -> str:
        """
        Retrieve or load a buffer chunk from the file.

        Args:
            index (int): The index of the buffer chunk to retrieve.

        Returns:
            str: The buffer chunk at the specified index.
        """
        pass

    def __getitem__(self, index: int | slice) -> str:
        """
        Retrieve a character or a slice of characters from the file.

        Args:
            index (Union[int, slice]): The index or slice of characters to retrieve.

        Returns:
            str: The character(s) at the specified index or slice.
        """
        # The buffer is an array that is seek like a RAM:
        # self.buffers[index]: the row in the array of length 1MB, index is `i` modulo CHUNK_LENGTH
        # self.buffures[index][j]: the column of the row that is `i` remainder CHUNK_LENGTH
        if isinstance(index, slice):
            start, stop, step = self._normalize_slice(index)

            if step == 0:
                raise ValueError("slice step cannot be zero")
            if step != 1:
                return "".join(self[i] for i in range(start, stop, step))

            if start >= stop:
                return ""
            return self._slice_from_buffers(start, stop)
        if index < 0:
            index += len(self)
        if index < 0:
            raise IndexError("string index out of range")
        buffer_index = index // self.buffer_length
        buffer = self.get_buffer(buffer_index)
        return buffer[index % self.buffer_length]

    def __len__(self) -> int:
        """
        Get the total length of the file.

        Returns:
            int: The total number of characters in the file.
        """
        if self.length is None:
            while self.length is None:
                chunk_index = len(self._chunk_positions)
                self._ensure_chunk_position(chunk_index)
        assert self.length is not None
        return self.length

    def _normalize_slice(self, index: slice) -> tuple[int, int, int]:
        pass

    def _slice_from_buffers(self, start: int, stop: int) -> str:
        pass

    def __setitem__(self, index: int | slice, value: str) -> None:  # pragma: no cover
        """
        Set a character or a slice of characters in the file.

        Args:
            index (slice): The slice of characters to set.
            value (str): The value to set at the specified index or slice.
        """
        start = index.start or 0 if isinstance(index, slice) else index or 0

        if start < 0:
            start += len(self)

        current_position = self.fd.tell()
        self.fd.seek(start)
        self.fd.write(value)
        self.fd.seek(current_position)

    def _ensure_chunk_position(self, chunk_index: int) -> None:
        """
        Ensure that we know the starting file position for the given chunk index.
        """
        pass
