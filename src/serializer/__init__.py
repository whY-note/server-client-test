from .base_serializer import BaseSerializer
from .json_serializer import JsonSerializer
from .msgpack_serializer import MsgPackSerializer
from .pickle_serializer import PickleSerializer


def create_serializer(name: str) -> BaseSerializer:
    serializers = {
        "json": JsonSerializer,
        "msgpack": MsgPackSerializer,
        "pickle": PickleSerializer
    }

    if name not in serializers:
        raise ValueError(f"Unknown serializer: {name}")

    return serializers[name]()

__all__ = [
    "BaseSerializer",
    "JsonSerializer",
    "MsgPackSerializer",
    "PickleSerializer",
    "create_serializer"
]