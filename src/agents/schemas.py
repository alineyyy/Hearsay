"""
Structured data contracts exchanged between the agents in the pipeline.

Each stage hands off a validated Pydantic model rather than free-form text
(via Strands' `structured_output`), which keeps the pipeline inspectable,
testable and safe to render in a UI.
"""

import json
from typing import Any, List, Literal

from pydantic import BaseModel, Field, model_validator


class _Model(BaseModel):
    """
    Backstop against one model failure: emitting a nested structure as a JSON
    *string* instead of real JSON.

    The primary defence is `strict_tools` on the Bedrock model (see
    `pipeline._model`), which makes the shape a decoding constraint rather
    than an instruction. This layer only matters if a call ever reaches a
    model without it, and it reports rather than swallows a malformed string —
    the observed failure was an unescaped double quote inside Chinese prose,
    and a silent `except` there costs an entire run to diagnose.
    """

    @model_validator(mode="before")
    @classmethod
    def _parse_stringified_json(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        for name, value in data.items():
            field = cls.model_fields.get(name)
            # Only structured fields: a genuine string field may legitimately
            # start with a bracket, and must be left alone.
            if field is None or field.annotation is str or not isinstance(value, str):
                continue
            stripped = value.strip()
            if not stripped.startswith(("[", "{")):
                continue
            try:
                data[name] = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"{cls.__name__}.{name} arrived as a string that is not valid "
                    f"JSON ({exc}). Excerpt: {stripped[max(0, exc.pos - 80):exc.pos + 80]!r}"
                ) from exc
        return data


# Verdict vocabulary — kept as a closed set so the UI can render each
# consistently and so the model cannot invent an ambiguous middle ground.
VerdictStatus = Literal[
    "confirmed",        # official sources support the claim
    "outdated",         # was true once, superseded by a later official update
    "partially_true",   # broadly right, details differ
    "not_covered",      # official sources are silent — common for edge cases
    "contradicted",     # official sources state the opposite
]


class QueryPlan(_Model):
    """Stage 1 — turn a question in any language into a French retrieval plan."""

    procedure: str = Field(
        description="The administrative procedure the user is dealing with, in English"
    )
    user_situation: str = Field(
        description="The user's circumstances and anything unusual about their case, "
        "in English. Use 'not specified' if the question gives no detail."
    )
    user_language: str = Field(
        description="The language the user wrote in, as an English name "
        "(e.g. 'English', 'Chinese', 'Spanish', 'Arabic'). The final answer must use this language."
    )
    french_queries: List[str] = Field(
        description="3-5 French search phrases using the formal terminology that actually "
        "appears in French administrative documents, e.g. "
        "'renouvellement titre de séjour étudiant'. Never translate literally.",
        min_length=1,
    )
    themes: List[str] = Field(
        default_factory=list,
        description="Official topic filters. Choose from: 'Étranger - Europe', 'Logement', "
        "'Social - Santé', 'Argent - Impôts - Consommation', 'Travail - Formation', "
        "'Papiers - Citoyenneté - Élections'.",
    )
    missing_info: List[str] = Field(
        default_factory=list,
        description="Key facts still needed for an accurate answer (e.g. 'type of residence "
        "permit held'), written in the user's language. Empty if nothing is missing.",
    )


class Claim(_Model):
    """A single checkable assertion extracted from community advice."""

    text: str = Field(
        description="The claim, stated specifically enough to be checked against official "
        "sources, in the user's language"
    )
    topic: str = Field(description="What this claim is about, in English")
    french_queries: List[str] = Field(
        description="French search phrases for verifying this specific claim", min_length=1
    )


class ClaimSet(_Model):
    """Everything checkable found in one piece of community advice."""

    source_hint: str = Field(
        default="unknown",
        description="Any date or provenance clue found in the text; 'unknown' if none",
    )
    claims: List[Claim] = Field(description="The extracted claims", min_length=1)


class Evidence(_Model):
    """An official citation backing a verdict."""

    doc_id: str = Field(description="Official document ID, e.g. F2231")
    title: str = Field(description="Official document title (French)")
    official_url: str = Field(description="Canonical service-public.fr URL")
    last_official_update: str = Field(
        description="Date this official document was last substantively updated"
    )
    quote: str = Field(
        description="The passage that supports the verdict, translated into the user's language"
    )


class Verdict(_Model):
    """The judgement on one community claim — the core output of this product."""

    claim: str = Field(description="The claim being judged, in the user's language")
    status: VerdictStatus = Field(description="The verdict")
    confidence: Literal["high", "medium", "low"] = Field(
        description="How confident this verdict is, given the evidence found"
    )
    explanation: str = Field(
        description="Why this verdict, and exactly where the claim diverges from official "
        "sources. Written in the user's language."
    )
    evidence: List[Evidence] = Field(
        default_factory=list, description="Official sources supporting this verdict"
    )


class VerdictSet(_Model):
    verdicts: List[Verdict] = Field(description="One verdict per extracted claim")
    overall_note: str = Field(
        default="",
        description="An overall caution about this piece of advice, in the user's language. "
        "May be empty.",
    )


class Step(_Model):
    """One step in an actionable checklist."""

    order: int = Field(description="Step number, starting at 1")
    action: str = Field(
        description="What to do, concrete enough to act on, in the user's language"
    )
    where: str = Field(
        default="", description="Where it is done — platform or institution. Empty if unknown."
    )
    documents: List[str] = Field(
        default_factory=list, description="Documents needed for this step, in the user's language"
    )
    deadline: str = Field(default="", description="Timing requirement. Empty if none.")
    source: Literal["official", "community", "official_and_community"] = Field(
        description="Where this step's information comes from. Must be reported honestly — "
        "this is how the user decides how much to trust it."
    )


class Guide(_Model):
    """The final deliverable handed to the user."""

    summary: str = Field(
        description="Two or three sentences answering the user's core question, "
        "in the user's language"
    )
    steps: List[Step] = Field(default_factory=list, description="The actionable checklist")
    warnings: List[str] = Field(
        default_factory=list,
        description="Pitfalls and risks — common rejection reasons, easily missed documents, "
        "timing traps. In the user's language.",
    )
    open_questions: List[str] = Field(
        default_factory=list,
        description="Things the user must confirm elsewhere because official sources do not "
        "cover their specific case, plus who to ask. In the user's language.",
    )
