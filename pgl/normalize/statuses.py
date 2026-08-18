BANGUMI_COLLECTION_TYPES = {
    1: "wishlist",
    2: "completed",
    3: "in_progress",
    4: "on_hold",
    5: "dropped",
    "want": "wishlist",
    "collect": "completed",
    "doing": "in_progress",
    "on_hold": "on_hold",
    "dropped": "dropped",
}

NEODB_STATUSES = {
    "wishlist": "wishlist",
    "wish": "wishlist",
    "want": "wishlist",
    "in_progress": "in_progress",
    "progress": "in_progress",
    "doing": "in_progress",
    "complete": "completed",
    "completed": "completed",
    "done": "completed",
    "on_hold": "on_hold",
    "hold": "on_hold",
    "dropped": "dropped",
}

def map_bangumi(value):
    return BANGUMI_COLLECTION_TYPES.get(value)

def map_neodb(value):
    if value is None:
        return None
    return NEODB_STATUSES.get(str(value).strip().casefold().replace(" ", "_"))
