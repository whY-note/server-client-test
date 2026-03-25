import struct

MAX_UDP_PAYLOAD = 1400 # 避免超过MTU
HEADER_FORMAT = "!IHH" # 'I' means unsigned int (4 bytes), 'H' means unsigned short (2 bytes)
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

MAX_CHUNK_SIZE = MAX_UDP_PAYLOAD - HEADER_SIZE
