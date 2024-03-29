import dataclasses
import enum


class Proto(enum.Enum):
    GEMINI = 0
    HTTP = 1


class Status(enum.Enum):
    OK = 0
    NOT_FOUND = 1
    ERROR = 2
    TEMPORARY_REDIRECTION = 3
    PERMANENT_REDIRECTION = 4


@dataclasses.dataclass
class Request:
    path: str
    proto: Proto


@dataclasses.dataclass
class Response:
    content: bytes
    content_type: str
    status: Status
