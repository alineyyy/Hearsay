"""
Community sources — a pluggable interface.

Community advice is most valuable exactly where official documents go quiet: the edge
cases. But sources differ wildly in how you reach them, how reliable they are, and what
they cost legally. So "where advice comes from" is an interface, and implementations can
come and go without the agents above noticing.

Shipped:
  - PastedSource      the user pastes it in. No platform risk, and it mirrors what
                      students actually do.
  - WebSearchSource   open web results — forums, Q&A, experience blogs.

Adding another source means implementing one fetch(). Nothing upstream changes.
"""

from dataclasses import dataclass, field
from typing import List, Protocol


@dataclass
class CommunityItem:
    """One piece of community advice."""

    text: str
    source_name: str
    url: str = ""
    posted_date: str = ""          # YYYY-MM-DD; empty if unknown. Recency checks need it.
    extra: dict = field(default_factory=dict)


class CommunitySource(Protocol):
    """Every community source implements this."""

    name: str

    def fetch(self, query: str, limit: int = 5) -> List[CommunityItem]:
        ...


class PastedSource:
    """Advice the user pasted in themselves."""

    name = "pasted by the user"

    def __init__(self, text: str, posted_date: str = "", url: str = ""):
        self.text = text
        self.posted_date = posted_date
        self.url = url

    def fetch(self, query: str = "", limit: int = 5) -> List[CommunityItem]:
        if not self.text.strip():
            return []
        return [CommunityItem(
            text=self.text.strip(),
            source_name=self.name,
            url=self.url,
            posted_date=self.posted_date,
        )]


class WebSearchSource:
    """
    Open web results — student forums, Q&A sites, experience blogs.

    The actual search is injected, so this works with a Strands retrieval tool, a search
    API, or anything else the deployment has available.
    """

    name = "open web"

    def __init__(self, search_fn=None):
        self.search_fn = search_fn

    def fetch(self, query: str, limit: int = 5) -> List[CommunityItem]:
        if self.search_fn is None:
            return []
        items = []
        for r in self.search_fn(query, limit) or []:
            items.append(CommunityItem(
                text=r.get("snippet", ""),
                source_name=r.get("site", self.name),
                url=r.get("url", ""),
                posted_date=r.get("date", ""),
            ))
        return items


def gather(sources: List[CommunitySource], query: str, limit_per_source: int = 3) -> List[CommunityItem]:
    """Collect advice across several sources."""
    items = []
    for src in sources:
        try:
            items.extend(src.fetch(query, limit_per_source))
        except Exception:
            continue
    return items
