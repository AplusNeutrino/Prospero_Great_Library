from pathlib import Path
from ..util import atomic_json

def write_json(path,data):
    atomic_json(Path(path),data)
