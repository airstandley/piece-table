from typing import Protocol
from dataclasses import dataclass
from enum import StrEnum


class FileEditor(Protocol):

    def read_file(self, file_name: str):
        ...

    def write_file(self, file_name: str):
        ...

    def edit_line(self, line_number: int, new_line: str):
        ...

    def add_line(self, line_number: int, new_line: str):
        ...

    def remove_line(self, line_number: int):
        ...


class ArrayOfStrings:
    # Basic representation -> Array of Strings
    # Example:
    # data = [
    #     "This is the first line",
    #     "This is the second line"
    # ]
    data: list[str]

    def __init__(self, data: list[str] = None):
        if data is None:
            data = list()
        self.data = data

    def read_file(self, file_name: str):
        """
        Read a file in to an array of strings
        :param file_name: Filepath
        :return: Array of strings
        """
        with open(file_name) as f:
            self.data = f.readlines()

    def write_file(self, file_name: str):
        with open(file_name, "w") as f:
            f.writelines(self.data)

    def edit_line(self, line_number: int, new_line: str):
        # Editing data isn't that bad. O(1) for basic array.
        # Depending on implementation details you're either creating a new strings and
        # changing the pointer to the string or modifying the string's memory.
        if not new_line.endswith("\n"):
            new_line += "\n"
        self.data[line_number] = new_line

    def add_line(self, line_number: int, new_line: str):
        # As the article points out inserting a line can be expensive for large files. O(n) for basic array
        # If you're using a basic array you have to shift all the data after the insert in memory.
        # Technically depending on the version of Python 'list' might not be a simple array
        # (Current CPython is https://github.com/python/cpython/blob/main/Objects/listobject.c)
        # Great readup: https://rcoh.me/posts/notes-on-cpython-list-internals/
        # Worth noting because a dynamic linked list for example would save on insert time,
        # but make the line edit above much more expensive
        if not new_line.endswith("\n"):
            new_line += "\n"
        self.data.insert(line_number, new_line)

    def remove_line(self, line_number: int):
        # Same issues as with add_line
        self.data.pop(line_number)

    def __str__(self):
        return "".join(self.data)

class Source(StrEnum):
    original = "original"
    add = "add"


@dataclass
class Piece:
    source: Source
    start: int
    length: int


class PieceTable:
    # Piece Table -> Original Buffer, Add Buffer
    # Example:
    # data = {
    #     "original": "This is the first line\nThis is the second line\n",
    #     "add": "",
    #     "pieces": ("original", 0, 47)
    # }
    original: str
    line_indexes: dict[int, int]
    lines: int
    add: str
    pieces: list[Piece]

    def __init__(self, original: str = ""):
        self._initialize(original=original)

    def _initialize(self, original: str = ""):
        self.original = original
        self.line_indexes, self.lines = self.make_line_indexes(original)
        self.add = ""
        self.pieces = list()
        if original:
            self.pieces.append(Piece(source=Source.original, start=0, length=len(original)))

    @staticmethod
    def make_line_indexes(data: str) -> tuple[dict[int, int], int]:
        # Map line numbers to string indexes so we can use the same interfaces as the array of strings
        line_indexes = {
            0: 0
        }
        line_number = 0
        for index, char in enumerate(data):
            if char == "\n":
                line_number += 1
                line_indexes[line_number] = index
        return line_indexes, line_number

    def read_file(self, file_name: str):
        with open(file_name) as f:
            original = f.read()
        self._initialize(original)

    def write_file(self, file_name: str):
        with open(file_name, "w") as f:
            for piece in self.pieces:
                if piece.source == Source.original:
                    buffer = self.original
                elif piece.source == Source.add:
                    buffer = self.add
                else:
                    raise ValueError(f"Invalid Piece source: {piece.source}")

                f.write(buffer[piece.start:piece.start+piece.length])

    def edit_line(self, line_number: int, new_line: str):
        raise NotImplementedError("No Worky")
        # This is really an add and remove in one
        if not new_line.endswith("\n"):
            new_line += "\n"
        if line_number > self.lines:
            raise ValueError("Line number too large")

        new_piece = Piece(source=Source.add, start=len(self.add), length=len(new_line))
        # Add to the buffer
        self.add += new_line

        # Update pieces
        insert_index = self.line_indexes[line_number] + 1
        end_index = self.line_indexes[line_number + 1] if self.lines - line_number > 0 else None

        new_pieces = []
        current_index = 0
        for piece in self.pieces:
            if current_index + piece.length < insert_index:
                new_pieces.append(piece)
                current_index += piece.length
                continue

            if current_index > insert_index:
                new_pieces.append(piece)
                current_index += piece.length
                continue

            if current_index == insert_index:
                new_pieces.append(new_piece)

                new_pieces.append(Piece(source=piece.source, start=piece.start+))
            else:
                splice_distance = insert_index-current_index
                new_pieces.append(Piece(source=piece.source, start=piece.start, length=splice_distance))
                new_pieces.append(new_piece)
                new_pieces.append(Piece(
                    source=piece.source, start=piece.start+splice_distance, length=piece.length-splice_distance
                ))
        self.pieces = new_pieces

    def add_line(self, line_number: int, new_line: str):
        if not new_line.endswith("\n"):
            new_line += "\n"
        if line_number > self.lines:
            raise ValueError("Line number too large")

        new_piece = Piece(source=Source.add, start=len(self.add), length=len(new_line))
        # Add to the buffer
        self.add += new_line

        # Update pieces
        insert_index = self.line_indexes[line_number] + 1

        new_pieces = []
        current_index = 0
        for piece in self.pieces:
            if current_index + piece.length < insert_index:
                new_pieces.append(piece)
                current_index += piece.length
                continue

            if current_index > insert_index:
                new_pieces.append(piece)
                current_index += piece.length
                continue

            if current_index == insert_index:
                new_pieces.append(new_piece)
                new_pieces.append(piece)
            else:
                splice_distance = insert_index-current_index
                new_pieces.append(Piece(source=piece.source, start=piece.start, length=splice_distance))
                new_pieces.append(new_piece)
                new_pieces.append(Piece(
                    source=piece.source, start=piece.start+splice_distance, length=piece.length-splice_distance
                ))
        self.pieces = new_pieces

        # Update line_indexes
        self.lines += 1
        new_line_indexes = {}
        for i in range(0, self.lines):
            if i < line_number:
                new_line_indexes[i] = self.line_indexes[i]
            elif i == line_number:
                new_line_indexes[i] = insert_index
            else:
                new_line_indexes[i] = self.line_indexes[i-1] + new_piece.length

    def __str__(self):
        output = ""
        for piece in self.pieces:
            if piece.source == Source.original:
                buffer = self.original
            elif piece.source == Source.add:
                buffer = self.add
            else:
                raise ValueError(f"Invalid Piece source: {piece.source}")

            output += buffer[piece.start:piece.start+piece.length]
        return output




