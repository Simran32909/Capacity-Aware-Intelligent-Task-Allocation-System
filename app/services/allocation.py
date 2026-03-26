"""Capacity-aware task allocation (skill match, spare hours, lowest utilization)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


def utilization_rate(user: User) -> float:
    """Fraction of weekly capacity already used (0.0–1.0+)."""
    if user.weekly_capacity_hours <= 0:
        return 1.0
    return user.current_assigned_hours / user.weekly_capacity_hours


def _required_skill_parts(required: str) -> list[str]:
    """
    One skill: \"SQL\"
    Several (comma or semicolon): \"Python, HTML, CSS\" → user must have ALL of them.
    """
    if not required or not required.strip():
        return []
    raw = required.replace(";", ",")
    return [p.strip().lower() for p in raw.split(",") if p.strip()]


def _skill_matches(user_skills: list[str], required: str) -> bool:
    """Every required part must appear in the user's skills (case-insensitive)."""
    parts = _required_skill_parts(required)
    if not parts:
        return False
    user_set = {s.strip().lower() for s in user_skills if isinstance(s, str) and s.strip()}
    return all(p in user_set for p in parts)


def find_best_user(
    db: Session,
    *,
    required_skill: str,
    estimated_hours: int,
) -> tuple[User | None, str | None]:
    """
    Returns (assignee, None) on success, or (None, human-readable reason) if unassigned.

    Candidates must:
    - have every skill in `required_skill` (one name, or several separated by commas),
    - have spare capacity >= estimated_hours.

    Tie-break: lowest utilization_rate, then lowest user id for stability.
    """
    users = list(db.scalars(select(User)).all())
    skill = required_skill.strip()

    if not users:
        return None, "No team members yet. Add people on the Team tab first."

    candidates: list[User] = []
    has_skill: list[User] = []
    for u in users:
        if not _skill_matches(u.skills, skill):
            continue
        has_skill.append(u)
        spare = u.weekly_capacity_hours - u.current_assigned_hours
        if spare < estimated_hours:
            continue
        candidates.append(u)

    if candidates:
        chosen = min(candidates, key=lambda u: (utilization_rate(u), u.id))
        return chosen, None

    if not has_skill:
        parts = _required_skill_parts(skill)
        if len(parts) > 1:
            shown = ", ".join(parts)
            return (
                None,
                f"No team member has all of these skills: {shown}. "
                "Add each skill to someone’s profile on the Team tab (comma-separated).",
            )
        return (
            None,
            "No team member has this skill. Match spelling to the Team tab "
            f'(you asked for "{skill.strip()}").',
        )

    return (
        None,
        "Someone has this skill, but no one has enough spare hours left this week "
        f"(task needs {estimated_hours} h; check capacity vs. current load).",
    )
