from abc import ABC, abstractmethod

import black
import isort


class CodeFormatter(ABC):
    @abstractmethod
    def format(self, text: str, *args, **kwargs) -> str:
        pass


class BlackFormatter(CodeFormatter):
    def __init__(self, mode: black.FileMode = black.FileMode()):
        self._mode = mode

    def format(self, text: str, *args, **kwargs) -> str:
        return black.format_str(text, mode=self._mode)


class ISortFormatter(CodeFormatter):
    def __init__(self, config: isort.Config = isort.Config()):
        self._config = config

    def format(self, text: str, *args, **kwargs) -> str:
        return isort.code(text, config=self._config)
