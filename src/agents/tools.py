"""
Deterministic tools available to the agents.

Nothing here calls an LLM: these are retrieval and date arithmetic. Facts come from
tools, judgement comes from agents — which is what makes every conclusion traceable
to a specific official document.
"""

import sys
from datetime import date, datetime
from pathlib import Path

from strands import tool

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from retrieval.corpus import get_corpus  # noqa: E402


@tool
def search_official_docs(query: str, theme: str = "") -> str:
    """
    Search the official French service-public.fr corpus for administrative information.

    Args:
        query: A French search phrase using formal French administrative terminology,
               e.g. "renouvellement titre de séjour étudiant". Must be French, not
               English or any other language — the corpus is in French.
        theme: Optional topic filter. One of: "Étranger - Europe", "Logement",
               "Social - Santé", "Argent - Impôts - Consommation", "Travail - Formation",
               "Papiers - Citoyenneté - Élections".

    Returns:
        Matching official passages, each with its canonical URL and the date that
        official document was last substantively updated.
    """
    corpus = get_corpus()
    results = corpus.search(query, top_k=5, theme=theme or None)
    if not results:
        return (
            f"No official content found for '{query}'. Try different French "
            f"administrative terminology."
        )

    lines = []
    for i, r in enumerate(results, 1):
        lines.append(
            f"[{i}] DOC {r['doc_id']} — {r['title']}\n"
            f"    Section: {r['section'] or '(body)'}\n"
            f"    Last official update: {r['last_official_update']}\n"
            f"    Official URL: {r['official_url']}\n"
            f"    Content: {r['text'][:900]}"
        )
        for svc in r.get("online_services", [])[:2]:
            if svc.get("url"):
                cerfa = f" (CERFA {svc['cerfa']})" if svc.get("cerfa") else ""
                lines.append(f"    Online service: {svc['title']}{cerfa} -> {svc['url']}")
    return "\n\n".join(lines)


@tool
def check_information_recency(official_update_date: str, community_post_date: str = "") -> str:
    """
    Compare when an official document was last updated against when a piece of community
    advice was posted, to judge whether that advice may have gone stale.

    This is a core check for this product: community posts never expire on their own,
    but the rules they describe do change.

    Args:
        official_update_date: Official document's last update date, YYYY-MM-DD.
        community_post_date: When the community advice was posted, YYYY-MM-DD.
                             Leave empty if unknown.

    Returns:
        An assessment of whether the advice predates a relevant official change.
    """

    def parse(s):
        s = (s or "").strip()
        for fmt, length in (("%Y-%m-%d", 10), ("%Y-%m", 7), ("%Y", 4)):
            try:
                return datetime.strptime(s[:length], fmt).date()
            except Exception:
                continue
        return None

    official = parse(official_update_date)
    community = parse(community_post_date)
    today = date.today()

    if not official:
        return (
            "This official document carries no update date, so recency cannot be compared. "
            "Tell the user to confirm against the official page."
        )

    months_old = (today - official).days // 30
    parts = [
        f"Official document last updated {official.isoformat()} (about {months_old} months ago)."
    ]

    if community:
        gap_months = (official - community).days // 30
        if gap_months > 0:
            parts.append(
                f"WARNING: the community advice was posted {community.isoformat()}, and the "
                f"official document was updated about {gap_months} months AFTER that "
                f"({official.isoformat()}). This advice may be out of date — official wins."
            )
        else:
            parts.append(
                f"The community advice was posted {community.isoformat()}, after the last "
                f"official update, so there is no timing conflict."
            )
    else:
        parts.append(
            "The community advice has no post date, so its recency cannot be established — "
            "say so explicitly in the answer."
        )

    return " ".join(parts)
