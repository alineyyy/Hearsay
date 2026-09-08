"""
社区信息源 —— 可插拔接口。

设计意图:社区经验对"官方文档覆盖不到的特殊情况"很有价值,但不同来源的
获取方式、可靠性、法律风险差异很大。所以这里把"社区源"抽象成统一接口,
具体实现可以随时增减,不影响上层 agent 逻辑。

当前实现:
  - PastedSource:用户自己粘贴的内容(零风险,且就是真实使用场景)
  - WebSearchSource:公开网页检索(论坛、问答、经验博客)

未来可扩展:任何平台连接器只需实现 fetch(),即可插入流水线。
"""

from dataclasses import dataclass, field
from typing import List, Protocol


@dataclass
class CommunityItem:
    """一条社区经验。"""

    text: str
    source_name: str
    url: str = ""
    posted_date: str = ""          # YYYY-MM-DD,未知则留空 —— 时效性判断要用
    extra: dict = field(default_factory=dict)


class CommunitySource(Protocol):
    """所有社区信息源都实现这个接口。"""

    name: str

    def fetch(self, query: str, limit: int = 5) -> List[CommunityItem]:
        ...


class PastedSource:
    """用户直接粘贴的社区内容。"""

    name = "用户粘贴"

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
    公开网页检索源(留学论坛、问答、经验博客等)。

    注意:实际的检索实现取决于运行环境可用的检索工具。
    这里保留接口,便于接入 Strands 的检索工具或任意搜索 API。
    """

    name = "公开网页"

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
    """从多个社区源汇总经验条目。"""
    items = []
    for src in sources:
        try:
            items.extend(src.fetch(query, limit_per_source))
        except Exception:
            continue
    return items
