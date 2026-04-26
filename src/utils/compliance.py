"""
Compliance check: runs on every generated caption before posting.
Blocks banned language, requires disclaimers, gates publishing.
"""

from __future__ import annotations
from dataclasses import dataclass

BANNED_PHRASES = [
    "lock of the day",
    "lock ",
    " lock",
    "guaranteed",
    "guarantee",
    "sure thing",
    "sure bet",
    "can't lose",
    "cant lose",
    "100% winner",
    "100% win",
    "fixed match",
    "fixed game",
    "inside info",
    "insider info",
    "rigged",
    "secret tip",
    "exclusive pick",
    "vip lock",
    "max play",
    "max unit",
]

REQUIRED_PHRASES_ANY = [
    ["18+", "18 +"],
    ["ConnexOntario", "1-866-531-2600", "connexontario.ca", "1-800-GAMBLER"],
    ["not betting advice", "not advice", "analytical content", "entertainment"],
]


@dataclass
class ComplianceResult:
    passed: bool
    violations: list[str]
    missing_required: list[str]

    def summary(self) -> str:
        if self.passed:
            return "✅ Compliance passed"
        parts = []
        if self.violations:
            parts.append(f"❌ Banned phrases: {', '.join(self.violations)}")
        if self.missing_required:
            parts.append(f"❌ Missing required: {', '.join(self.missing_required)}")
        return " | ".join(parts)


def check(text: str) -> ComplianceResult:
    """Check a caption/post body for compliance.

    Returns ComplianceResult. `passed=False` → do not post, route to review queue.
    """
    lower = text.lower()

    violations = [phrase for phrase in BANNED_PHRASES if phrase in lower]

    missing = []
    labels = ["age gate (18+)", "helpline (ConnexOntario or equivalent)", "not-advice disclaimer"]
    for label, group in zip(labels, REQUIRED_PHRASES_ANY):
        if not any(p.lower() in lower for p in group):
            missing.append(label)

    return ComplianceResult(
        passed=not violations and not missing,
        violations=violations,
        missing_required=missing,
    )


if __name__ == "__main__":
    good = """
    Model pick: Lakers -4.5 vs Warriors — edge +4.6%, 1u size.
    18+ only. Analytical content, not betting advice.
    ConnexOntario 1-866-531-2600 if you need help.
    """
    bad = "🔒 LOCK OF THE DAY — guaranteed winner, can't lose, VIP exclusive!"

    print("GOOD:", check(good).summary())
    print("BAD: ", check(bad).summary())
