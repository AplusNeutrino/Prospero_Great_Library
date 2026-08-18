from . import statuses  # keep normalize package import-safe
from ..models import Rating

def normalize_rating(value, scale, source=None):
    return Rating.from_value(value, scale, source)
