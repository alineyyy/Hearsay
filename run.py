#!/usr/bin/env python3
"""
Command-line entry point, used for development and for recording the demo.

Usage:
  python3 run.py ask "My student residence permit expires soon. How do I renew it?"
  python3 run.py verify            # check a piece of community advice (English sample)
  python3 run.py verify-zh         # same, with advice written in Chinese
  python3 run.py demo              # ask mode + verify mode, end to end
  python3 run.py --help            # modes and their cost

The mode is required and validated before anything loads: every mode spends
real Bedrock calls, so a typo must not be able to start one.
"""

import sys
import textwrap
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from agents.pipeline import Navigator  # noqa: E402

# ── Demo material ────────────────────────────────────────────────────────────
# A realistic piece of peer advice: partly right, partly stale, with amounts that
# need checking. Exactly the kind of post students actually rely on.

SAMPLE_EN = """
[Renewal tips from someone who just went through it]

1. Book your préfecture appointment 2 months ahead — it's all online now,
   don't waste time queuing in person.
2. Documents: passport, current titre de séjour, school enrollment certificate,
   proof of address, bank statements (you need to show at least €3000).
3. You get your récépissé the same day you submit, valid for 3 months.
4. Don't forget the timbre fiscal — I paid €160.
5. If your récépissé expires before the new card arrives, just walk into the
   préfecture and they'll extend it.

Good luck everyone!
"""

SAMPLE_ZH = """
【续居留经验帖】我去年刚办完学生居留续签,给学弟学妹们分享一下流程:

1. 一定要提前2个月在préfecture官网预约,现在都是网上约,别傻乎乎跑去现场排队
2. 材料清单:护照、现有居留证、学校在读证明、住房证明、银行流水
   (听说要证明账户里有3000欧以上才行)
3. 交完材料当场就会给你récépissé,有效期3个月,拿着它可以合法待着
4. 别忘了买税票 timbre fiscal,我当时交了 160 欧
5. 如果récépissé过期了新卡还没下来,可以直接去préfecture要求延期,他们会给你续

祝大家都顺利!
"""

SAMPLE_DATE = "2024-03-15"

STATUS_ICON = {
    "confirmed": "[OK]      CONFIRMED",
    "outdated": "[STALE]   OUTDATED",
    "partially_true": "[PARTIAL] PARTIALLY TRUE",
    "not_covered": "[GAP]     NOT COVERED",
    "contradicted": "[WRONG]   CONTRADICTED",
}


WIDTH = 92

# Punctuation that must not open a line. Letting it overflow the right margin
# by a column reads far better than stranding a 。 at the start of the next.
NO_LINE_START = "、。，．：；！？》」』）】〉·…—"


def display_width(text):
    """Width in terminal columns. East Asian characters occupy two."""
    return sum(
        0 if unicodedata.combining(ch)
        else 2 if unicodedata.east_asian_width(ch) in ("W", "F")
        else 1
        for ch in text
    )


def _break_units(text):
    """
    Split into the smallest pieces a line may break between: Latin words break
    on spaces, but Chinese has no spaces, so every wide character is its own
    unit and lines break between characters.
    """
    units, word = [], ""
    for ch in text:
        if ch.isspace() or display_width(ch) == 2:
            if word:
                units.append(word)
                word = ""
            units.append(" " if ch.isspace() else ch)
        else:
            word += ch
    if word:
        units.append(word)
    return units


def wrap(text, indent="      "):
    """
    Wrap to terminal width with a hanging indent: `indent` is a label ("  - ",
    "  reason : ") that belongs on the first line only; continuation lines get
    blanks of the same width so the text stays in one column.

    Measured in columns rather than characters — `textwrap` counts characters,
    which renders the Chinese output at roughly twice the intended width and
    leaves mixed CN/EN pages visibly ragged.
    """
    hanging = " " * display_width(indent)
    lines, line, prefix = [], "", indent

    for unit in _break_units(str(text)):
        candidate = line + unit
        overflows = display_width(prefix + candidate) > WIDTH
        if line and overflows and unit not in NO_LINE_START:
            lines.append((prefix + line).rstrip())
            prefix, line = hanging, ("" if unit == " " else unit)
        else:
            line = candidate

    lines.append((prefix + line).rstrip())
    return "\n".join(lines)


def rule(title):
    print("\n" + "=" * 94)
    print(title)
    print("=" * 94)


def show(result):
    plan = result["plan"]
    rule("1. INTENT & SEARCH PLAN")
    print(f"   Procedure      : {plan.procedure}")
    print(f"   Situation      : {plan.user_situation}")
    print(f"   User language  : {plan.user_language}")
    print(f"   French queries : {' / '.join(plan.french_queries)}")
    if plan.missing_info:
        print(f"   Missing info   : {'; '.join(plan.missing_info)}")

    rule(f"2. OFFICIAL EVIDENCE ({len(result['official_sources'])} passages retrieved)")
    for r in result["official_sources"][:5]:
        print(f"   [{r['last_official_update']}]  {r['doc_id']}  {r['title'][:58]}")
        print(f"                {r['official_url']}")

    if result["verdicts"]:
        rule("3-4. CROSS-VERIFICATION OF COMMUNITY ADVICE")
        for v in result["verdicts"].verdicts:
            print(f"\n   {STATUS_ICON.get(v.status, v.status)}   (confidence: {v.confidence})")
            print(wrap(v.claim, "      claim  : "))
            print(wrap(v.explanation, "      reason : "))
            for e in v.evidence[:2]:
                print(f"      source : {e.doc_id} — {e.title[:44]} (updated {e.last_official_update})")
                print(f"               {e.official_url}")
        if result["verdicts"].overall_note:
            print("\n" + wrap(result["verdicts"].overall_note, "   NOTE: "))

    guide = result["guide"]
    rule("5. ACTIONABLE GUIDE")
    print(wrap(guide.summary, "   "))
    for s in guide.steps:
        print(f"\n   [{s.order}] {s.action}")
        print(f"       source    : {s.source}")
        if s.where:
            print(f"       where     : {s.where}")
        if s.documents:
            print(f"       documents : {'; '.join(s.documents)}")
        if s.deadline:
            print(f"       deadline  : {s.deadline}")
    if guide.warnings:
        print("\n   WARNINGS:")
        for w in guide.warnings:
            print(wrap(w, "      - "))
    if guide.open_questions:
        print("\n   NEEDS CONFIRMATION:")
        for q in guide.open_questions:
            print(wrap(q, "      - "))
    print()


MODES = {
    "ask": "answer a question, given after the mode (one run)",
    "verify": "check the built-in English sample of community advice (one run)",
    "verify-zh": "the same advice in Chinese — shows the multilingual path (one run)",
    "demo": "ask mode + verify mode, end to end (TWO runs)",
}


def usage(error=""):
    """Print usage and return an exit code."""
    if error:
        print(f"run.py: {error}\n")
    print("Usage: python3 run.py <mode> [question]\n")
    for name, description in MODES.items():
        print(f"  {name:<10}  {description}")
    print("\nEvery mode makes several Bedrock calls and takes a minute or two,")
    print("so a mode must be named explicitly — there is no default.")
    return 2 if error else 0


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""

    # Validate before constructing Navigator: a typo should cost nothing. This
    # used to fall through to `demo`, so a mistyped mode silently spent two
    # full pipeline runs — the most expensive thing this CLI can do.
    if mode in ("-h", "--help", "help"):
        return usage()
    if mode not in MODES:
        return usage(f"unknown mode {mode!r}" if mode else "no mode given")

    nav = Navigator()
    print(f"Official corpus ready: {nav.corpus.stats()}")

    if mode == "ask":
        q = " ".join(sys.argv[2:]) or \
            "My student residence permit expires soon. How do I renew it?"
        print(f"\nASK MODE — {q}")
        show(nav.run(text=q))

    elif mode in ("verify", "verify-zh"):
        sample = SAMPLE_ZH if mode == "verify-zh" else SAMPLE_EN
        question = ("这篇续居留经验帖里的说法,现在还准确吗?" if mode == "verify-zh"
                    else "Is this renewal advice still accurate?")
        print("\nVERIFY MODE — community advice under review:")
        print(textwrap.indent(sample.strip(), "   | "))
        show(nav.run(text=f"{sample}\n\n{question}", posted_date=SAMPLE_DATE))

    else:  # demo
        print("\nASK MODE")
        show(nav.run(text="My student residence permit expires soon. How do I renew it?"))
        print("\n\nVERIFY MODE")
        show(nav.run(text=SAMPLE_EN, posted_date=SAMPLE_DATE))

    return 0


if __name__ == "__main__":
    sys.exit(main())
