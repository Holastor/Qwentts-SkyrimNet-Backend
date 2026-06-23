from typing import List, Tuple
from src import config
from src.config import _log, STRESS_MARK, STRESS_VOWELS


def _shorten_text_if_needed(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text

    snippet = text[:max_chars]
    split_at = max(snippet.rfind("."), snippet.rfind(","), snippet.rfind(" "))
    if split_at > 0:
        shortened = snippet[: split_at + 1].strip()
    else:
        shortened = snippet.strip()
    if not shortened:
        shortened = snippet

    _log(
        f"WARNING: text was shortened from {len(text)} to {len(shortened)} chars "
        f"because --max-text-chars={max_chars}"
    )
    return shortened


def _prepare_qwentts_gen_text(text: str) -> tuple[str, bool]:
    gen_text = _shorten_text_if_needed(text, config.MAX_TEXT_CHARS)
    ending_pause_appended = False

    if config.APPEND_ENDING_PAUSE and config.ENDING_PAUSE_TEXT and not gen_text.rstrip().endswith("..."):
        gen_text = f"{gen_text.rstrip()} {config.ENDING_PAUSE_TEXT}"
        ending_pause_appended = True

    _log(f"original text: {text}")
    gen_text, pronunciation_warnings = _convert_plus_stress_format(gen_text)
    changed = gen_text != text

    for warning in pronunciation_warnings:
        _log(f"WARNING: plus stress conversion: {warning}")
    _log(f"qwentts gen_text: {gen_text}")
    _log(f"qwentts gen_text changed: {str(changed).lower()}")
    _log(f"was ending pause appended: {str(ending_pause_appended).lower()}")
    return gen_text, ending_pause_appended


def _convert_plus_stress_format(text: str) -> tuple[str, list[str]]:
    if "+" not in text:
        return text, []

    converted: list[str] = []
    warnings: list[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char != "+":
            converted.append(char)
            index += 1
            continue

        next_index = index + 1
        if next_index >= len(text):
            warnings.append("removed '+' at end of text")
            index += 1
            continue

        next_char = text[next_index]
        if next_char in STRESS_VOWELS:
            converted.append(next_char)
            if next_index + 1 >= len(text) or text[next_index + 1] != STRESS_MARK:
                converted.append(STRESS_MARK)
            index += 2
            continue

        warnings.append(f"removed '+' before non-vowel '{next_char}'")
        index += 1

    return "".join(converted), warnings
