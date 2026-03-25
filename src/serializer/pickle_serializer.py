import pickle 
from src.serializer.base_serializer import BaseSerializer

class PickleSerializer(BaseSerializer):
    def serialize(self, data) -> bytes:
        return pickle.dumps(data)
    
    def deserialize(self, raw_bytes: bytes):
        return pickle.loads(raw_bytes)