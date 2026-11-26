"""The third verdict state added to the copies of the detectors (PREREG_V2_ADDENDUM_13.md)."""


class Undecidable:
    """A verdict the detector could not reach. Using it as true or false raises, so no caller can read it as clean by accident."""

    def __init__(self, reason):
        self.reason = reason

    def __bool__(self):
        raise TypeError(f"verdict is undecidable ({self.reason}); handle it explicitly")

    def __repr__(self):
        return f"UNDECIDABLE({self.reason})"
