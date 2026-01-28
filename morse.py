"""Morse code translation module."""

import logging

logger = logging.getLogger(__name__)

MORSE_ALPHABET: dict[str, str] = {
    "A": "x xxx",
    "B": "xxx x x x",
    "C": "xxx x xxx x",
    "D": "xxx x x",
    "E": "x",
    "F": "x x xxx x",
    "G": "xxx xxx x",
    "H": "x x x x",
    "I": "x x",
    "J": "x xxx xxx xxx",
    "K": "xxx x xxx",
    "L": "x xxx x x",
    "M": "xxx xxx",
    "N": "xxx x",
    "O": "xxx xxx xxx",
    "P": "x xxx xxx x",
    "Q": "xxx xxx x xxx",
    "R": "x xxx x",
    "S": "x x x",
    "T": "xxx",
    "U": "x x xxx",
    "V": "x x x xxx",
    "W": "x xxx xxx",
    "X": "xxx x x xxx",
    "Y": "xxx x xxx xxx",
    "Z": "xxx xxx x x",
    " ": "  ",
    "Ä": "x xxx x xxx",
    "Ö": "xxx xxx xxx x",
    "Ü": "x x xxx xxx",
    "1": "x xxx xxx xxx xxx",
    "2": "x x xxx xxx xxx",
    "3": "x x x xxx xxx",
    "4": "x x x x xxx",
    "5": "x x x x x",
    "6": "xxx x x x x",
    "7": "xxx xxx x x x",
    "8": "xxx xxx xxx x x",
    "9": "xxx xxx xxx xxx x",
    "0": "xxx xxx xxx xxx xxx",
    ".": "x xxx x xxx x xxx",
    "?": "x x xxx xxx x x",
    "!": "xxx x xxx x xxx xxx",
    ",": "xxx xxx x x xxx xxx",
    '"': "x xxx x x xxx x",
    "&": "x xxx x x x",
    "/": "xxx x x xxx x",
    "@": "x xxx xxx x xxx x",
    "=": "xxx x x x xxx",
    "(": "xxx x xxx xxx x",
    ")": "xxx x xxx xxx x xxx",
    ":": "xxx xxx xxx x x x",
    "+": "x xxx x xxx x",
    "-": "xxx x x x x xxx",
}


def morse_translator(text: str) -> str:
    """Translate text to morse code pattern.

    Args:
        text: The text to translate to morse code.

    Returns:
        A string of 'x' (signal) and spaces representing morse code.
    """
    logger.debug(f"Translating to morse: {text}")
    result = "".join(MORSE_ALPHABET.get(c, "") + "  " for c in text.upper())
    logger.debug(f"Morse result: {result}")
    return result


# Backwards compatibility alias
morseTranslator = morse_translator