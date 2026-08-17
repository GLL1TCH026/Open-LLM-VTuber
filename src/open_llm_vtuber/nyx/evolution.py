from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class PatchCandidate:
    title: str
    summary: str
    diff: str = ""
    approved: bool = False


class SelfReview:
    """Minimal evolution layer: propose changes before applying them."""

    def __init__(self) -> None:
        self.candidates: List[PatchCandidate] = []

    def propose(self, title: str, summary: str, diff: str) -> PatchCandidate:
        candidate = PatchCandidate(title=title, summary=summary, diff=diff)
        self.candidates.append(candidate)
        return candidate

    def approve(self, title: str) -> PatchCandidate | None:
        for candidate in self.candidates:
            if candidate.title == title:
                candidate.approved = True
                return candidate
        return None

    def pending(self) -> List[PatchCandidate]:
        return [item for item in self.candidates if not item.approved]
