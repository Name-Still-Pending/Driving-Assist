import json


def json_encode(obj: {}):
    return json.dumps(obj).encode("utf-8")


def json_decode(obj: bin):
    return json.loads(obj.decode("utf-8"))



