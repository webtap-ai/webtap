from typing import Dict, Generic, List, TypeVar

from .utils import ignore_docs

T = TypeVar('T')


class ListPage(Generic[T]):
    """A single page of items returned from a list() method."""

    #: list: List of returned objects on this page
    items: List[T]
    #: int: Count of the returned objects on this page
    count: int
    #: int: The limit on the number of returned objects offset specified in the API call
    offset: int
    #: int: The offset of the first object specified in the API call
    limit: int
    #: int: Total number of objects matching the API call criteria
    total: int
    #: bool: Whether the listing is descending or not
    desc: bool

    @ignore_docs
    def __init__(self, data: Dict) -> None:
        """Initialize a ListPage instance from the API response data."""
        self.items = data['items'] if 'items' in data else []
        self.offset = data['offset'] if 'offset' in data else 0
        self.limit = data['limit'] if 'limit' in data else 0
        self.count = data['count'] if 'count' in data else len(self.items)
        self.total = data['total'] if 'total' in data else self.offset + self.count
        self.desc = data['desc'] if 'desc' in data else False
