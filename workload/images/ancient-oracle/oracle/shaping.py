"""
Response shaping: orders list items so the useful ones come first.

HTF L4: dit bestand bevatte de tijdsbom. pressure() schatte een "load" op basis
van het uur (0 voor 12:00, 1 vanaf 16:00), en settle() gooide bij die load
willekeurig items weg, verhaspelde podnamen, verzon statussen, en gaf vanaf
~15:30 een lege lijst terug. Dat is allemaal verwijderd: de Oracle geeft nu op
elk uur exact wat de cluster zegt, enkel gesorteerd.
"""


def _relevance(item):
    """Pods in trouble first, then by namespace and name."""
    status = item.get("status") or {}
    meta = item.get("metadata") or {}

    trouble = status.get("phase") not in (
        None, "Running", "Active", "Succeeded"
    )

    return (
        0 if trouble else 1,
        meta.get("namespace", ""),
        meta.get("name", ""),
    )


def order(items):
    """The items, ordered by relevance. Nothing added, removed or changed."""
    return sorted(items, key=_relevance)
