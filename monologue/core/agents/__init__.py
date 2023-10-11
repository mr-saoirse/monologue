from ..spaces.Dialogue import Dialogue
from .monitoring import TheLangchainCallbackHandler
from .basic import *
import typing


def program(
    obj, functions: typing.List[dict], messages: typing.List[dict], **kwargs
) -> typing.List[dict]:
    """
    A decorator that decorates an arbitrary function ior tool
    applies the kwargs for the function and manipulates the functions and or messages



    """
