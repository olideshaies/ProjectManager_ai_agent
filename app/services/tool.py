from typing import Callable

class Tool:
    def __init__(self, name: str, description: str, func: Callable[[str], str]):
        self.name = name
        self.description = description
        self.func = func

    def run(self, query: str) -> str:
        return self.func(query)
