from dataclasses import dataclass, field


@dataclass
class StackItem:
    """
    Represents one object on the stack.
    """

    source: object

    controller: str

    targets: list = field(default_factory=list)

    effects: list = field(default_factory=list)

    ability: object | None = None