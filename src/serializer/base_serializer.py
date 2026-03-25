from abc import ABC, abstractmethod
from typing import Any

class BaseSerializer(ABC):
    '''序列化基类'''
    @abstractmethod
    def serialize(self, data: Any) -> bytes:
        ''' 将数据序列化为 bytes '''
        pass

    @abstractmethod
    def deserialize(self, raw_bytes: bytes) -> Any:
        ''' 从 bytes 反序列化 '''
        pass