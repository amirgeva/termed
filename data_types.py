from dataclasses import dataclass


@dataclass
class CompletionItem:
    name: str
    signature: str
    score: float
