"""Tests for the morse code translation module."""

import pytest

from morse import morse_translator, MORSE_ALPHABET


class TestMorseTranslator:
    """Tests for morse_translator function."""

    def test_single_letter(self) -> None:
        """Test translating a single letter."""
        result = morse_translator("A")
        assert "x xxx" in result

    def test_single_letter_lowercase(self) -> None:
        """Test that lowercase is converted to uppercase."""
        result = morse_translator("a")
        assert "x xxx" in result

    def test_word(self) -> None:
        """Test translating a word."""
        result = morse_translator("SOS")
        # S = "x x x", O = "xxx xxx xxx", S = "x x x"
        assert "x x x" in result
        assert "xxx xxx xxx" in result

    def test_empty_string(self) -> None:
        """Test empty string returns empty result."""
        result = morse_translator("")
        assert result == ""

    def test_unknown_character(self) -> None:
        """Test unknown characters are skipped."""
        result = morse_translator("A$B")
        # $ is not in alphabet, should be skipped
        assert "x xxx" in result  # A
        assert "xxx x x x" in result  # B

    def test_space_character(self) -> None:
        """Test space is translated correctly."""
        result = morse_translator("A B")
        assert "  " in result  # Space should be in result

    def test_numbers(self) -> None:
        """Test number translation."""
        result = morse_translator("1")
        assert "x xxx xxx xxx xxx" in result

    def test_special_characters(self) -> None:
        """Test special character translation."""
        result = morse_translator(".")
        assert "x xxx x xxx x xxx" in result

    def test_german_umlauts(self) -> None:
        """Test German umlaut translation."""
        result = morse_translator("Ä")
        assert "x xxx x xxx" in result


class TestMorseAlphabet:
    """Tests for the morse alphabet dictionary."""

    def test_all_letters_present(self) -> None:
        """Test that all basic letters are in the alphabet."""
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            assert letter in MORSE_ALPHABET

    def test_all_numbers_present(self) -> None:
        """Test that all numbers are in the alphabet."""
        for num in "0123456789":
            assert num in MORSE_ALPHABET

    def test_space_present(self) -> None:
        """Test that space is in the alphabet."""
        assert " " in MORSE_ALPHABET

    def test_morse_format(self) -> None:
        """Test that morse codes only contain x and space."""
        for code in MORSE_ALPHABET.values():
            for char in code:
                assert char in "x ", f"Invalid character in morse code: {char}"
