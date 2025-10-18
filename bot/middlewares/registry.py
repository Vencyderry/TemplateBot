import dataclasses
from typing import List, Optional

from telegrinder import ABCMiddleware


@dataclasses.dataclass
class Middlewares:
    message: List[Optional[ABCMiddleware]] = dataclasses.field(default_factory=list)
    callback_query: List[Optional[ABCMiddleware]] = dataclasses.field(default_factory=list)
