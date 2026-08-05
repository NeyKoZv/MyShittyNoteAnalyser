from MyShittyNoteAnalyser.constants import DEFAULT_NOTATION, DEFAULT_NOTATION_BY_INSTRUMENT


def get_default_notation_for_instrument(instrument_name: str) -> str:
    """Return the recommended notation ("Sharps" or "Flats") for *instrument_name*.

    Falls back to ``DEFAULT_NOTATION`` from the global constants.
    """
    return DEFAULT_NOTATION_BY_INSTRUMENT.get(instrument_name, DEFAULT_NOTATION)


def resolve_notation_on_instrument_change(instrument_name: str) -> str:
    """Convenience: return the notation that should be auto-selected
    when the user picks *instrument_name*.

    Currently delegates to ``get_default_notation_for_instrument``,
    but exists as a single entry-point so future logic (e.g. user
    preference persistence) can be added here without touching UI code.
    """
    return get_default_notation_for_instrument(instrument_name)
