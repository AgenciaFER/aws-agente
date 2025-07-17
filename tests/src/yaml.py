
class SafeLoader:
    pass
class SafeDumper:
    pass

def safe_load(stream):
    return {}

def dump(data, stream=None, **kwargs):
    if stream is None:
        return ""
    else:
        stream.write("")
