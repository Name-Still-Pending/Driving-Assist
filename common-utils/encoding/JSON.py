import json


def encode_bin(obj: {}):
    return json.dumps(obj).encode("utf-8")


def decode_bin(obj: bin):
    return json.loads(obj.decode("utf-8"))



