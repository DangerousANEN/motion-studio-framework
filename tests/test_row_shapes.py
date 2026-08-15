"""Spec row-shape validation: catch what would render a red ERROR card.

WHY THIS TEST EXISTS
--------------------
`validate_spec` already proved a list-valued field is PRESENT. It did not check
the shape of the items inside it, and the two failures are not equivalent:

  * A missing list renders one placeholder scene.
  * A wrong item shape fails Zod inside Root.tsx and replaces the ENTIRE video
    with a red ERROR card — which renders to a real mp4 and can be uploaded.

Found in the wild with `tokens: [{name, symbol, value, change}]`. Plausible,
accepted by every Python check, and `value` is not `amount`, so all three rows
failed `invalid_type`. The render "succeeded" and produced a red card.

The hard/soft split is the point of these tests: the TS schema declares some item
keys as required and others as optional-with-passthrough. Treating a soft field as
hard rejects valid specs; treating a hard field as soft ships red cards. Each
field below was checked against src/VideoSpec.schema.ts, not assumed.
"""
from __future__ import annotations

import io
import re
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from msf.spec import _ROW_SHAPES_HARD, _ROW_SHAPES_SOFT, validate_spec

REPO = Path(__file__).resolve().parents[1]
SCHEMA_TS = REPO / "remotion" / "src" / "VideoSpec.schema.ts"


def _spec(**scene_fields) -> dict:
    return {
        "width": 1080,
        "height": 1920,
        "fps": 60,
        "durationInFrames": 180,
        "style": "pop",
        "scenes": [{"id": "s", "durationInFrames": 180, **scene_fields}],
    }


def _validate_quietly(spec: dict) -> str:
    """Run validate_spec, returning captured warnings (raises propagate)."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        validate_spec(spec)
    return buf.getvalue()


# --------------------------------------------------------------- hard failures

def test_the_actual_bug_is_rejected() -> None:
    """`value` instead of `amount` on a token row — the case that shipped."""
    with pytest.raises(ValueError, match="amount"):
        validate_spec(
            _spec(
                preset="CryptoWallet",
                balance=1.0,
                tokens=[{"name": "Ethereum", "symbol": "ETH", "value": 64200, "change": 4.2}],
            )
        )


def test_error_message_names_the_field_the_index_and_the_consequence() -> None:
    """A validation error the author cannot act on wastes the check.

    It must say WHICH row, WHICH key, what keys were actually supplied, and that
    the consequence is a whole-video red card rather than one bad scene.
    """
    with pytest.raises(ValueError) as exc:
        validate_spec(
            _spec(preset="CryptoWallet", balance=1.0, tokens=[{"symbol": "ETH"}, {"amount": 1}])
        )
    msg = str(exc.value)
    assert "tokens[0]" in msg, "must name the offending index"
    assert "'amount'" in msg, "must name the missing key"
    assert "symbol" in msg, "must show the keys that WERE supplied"
    assert "red ERROR card" in msg.lower() or "red error card" in msg.lower()


@pytest.mark.parametrize(
    ("preset", "field", "good", "bad"),
    [
        ("CryptoWallet", "tokens", {"symbol": "ETH", "amount": 1.0}, {"symbol": "ETH"}),
        ("BankCard", "transactions", {"label": "Кофе", "amount": -320}, {"label": "Кофе"}),
        ("DonutFill", "segments", {"label": "Да", "value": 60}, {"label": "Да"}),
        ("TgChat", "messages", {"text": "привет"}, {"from": "Аня"}),
    ],
)
def test_hard_fields_reject_missing_keys_and_accept_complete_ones(
    preset: str, field: str, good: dict, bad: dict
) -> None:
    validate_spec(_spec(preset=preset, title="T", **{field: [good]}))  # must not raise
    with pytest.raises(ValueError):
        validate_spec(_spec(preset=preset, title="T", **{field: [bad]}))


# --------------------------------------------------------------- soft failures

def test_soft_fields_warn_instead_of_raising() -> None:
    """These pass Zod and render a blank row, so raising would be a lie."""
    out = _validate_quietly(_spec(preset="Leaderboard", rows=[{"value": 94}]))
    assert "WARNING" in out and "rows[0]" in out


def test_leaderboard_accepts_label_as_an_alias_for_name() -> None:
    """`label` is explicitly supported by the TS schema; requiring `name` alone
    would reject a valid spec."""
    for key in ("name", "label"):
        out = _validate_quietly(_spec(preset="Leaderboard", rows=[{key: "Kimi-K3", "value": 94}]))
        assert "WARNING" not in out, f"{key} should be accepted silently, got: {out}"


# ------------------------------------------------------- shorthand must survive

@pytest.mark.parametrize(
    ("preset", "fields"),
    [
        ("QuizCard", {"question": "Что?", "options": ["а", "б", "в"]}),
        ("ProgressPath", {"steps": ["Первый", "Второй"]}),
        ("LyricLines", {"lines": ["строка одна", "строка два"]}),
    ],
)
def test_bare_string_shorthand_is_not_rejected(preset: str, fields: dict) -> None:
    """Several fields accept `['a','b']` via a Zod transform. The row-shape loop
    must skip non-dict items rather than demanding keys of a string."""
    validate_spec(_spec(preset=preset, **fields))


def test_absent_fields_are_not_checked() -> None:
    """A preset that never supplies `tokens` must not be asked about token keys."""
    validate_spec(_spec(preset="HeroKinetic", title="Заголовок", text="Текст"))


def test_empty_list_does_not_crash_the_loop() -> None:
    """An empty list fails the earlier _DATA_REQUIREMENTS check, not this one —
    assert on the message so a future refactor cannot silently swap which check
    fires."""
    with pytest.raises(ValueError, match="needs one of|renderable content"):
        validate_spec(_spec(preset="CryptoWallet", balance=1.0, tokens=[]))


# ----------------------------------------------- the tables match the TS schema

def _item_object_source(field: str) -> str | None:
    """The `z.object({...})` body governing items of `field`, from the schema."""
    ts = SCHEMA_TS.read_text(encoding="utf-8")
    # Named item schemas (TokenRowSchema etc.) referenced by the field.
    named = {
        "tokens": "TokenRowSchema",
        "transactions": "TransactionSchema",
        "segments": "SegmentSchema",
        "messages": "ChatMessageSchema",
    }
    if field in named:
        m = re.search(
            rf"export const {named[field]} = z\s*\n?\s*\.?object\(\{{(.*?)\n\}}\)", ts, re.S
        )
        return m.group(1) if m else None
    # Inline arrays may be multi-line or compact (`field: z.array(z.object({...}))`).
    # The compact expansion schemas deliberately trade vertical space for a
    # focused field list, so use the z.object close rather than fixed indentation.
    m = re.search(rf"\n    {field}: z[\s\S]{{0,240}}?\.object\(\{{([\s\S]*?)\}}\)", ts)
    return m.group(1) if m else None


def _field_declaration(body: str, key: str) -> str | None:
    """Return one object-field declaration without truncating a z.union at commas."""
    start = re.search(rf"\b{key}:\s*", body)
    if not start:
        return None
    tail = body[start.end():]
    next_field = re.search(
        r",\s*(?:(?:/\*.*?\*/|//[^\n]*\n)\s*)*[A-Za-z][A-Za-z0-9_]*:\s*z\.",
        tail,
        re.S,
    )
    return tail[:next_field.start()] if next_field else tail


def test_hard_table_keys_are_required_in_the_ts_schema(subtests=None) -> None:
    """Every HARD key must genuinely lack `.optional()` on the TS side.

    If one is actually optional, this validator rejects specs Remotion would have
    rendered — a false positive that blocks legitimate work.
    """
    for field, keys in _ROW_SHAPES_HARD.items():
        body = _item_object_source(field)
        assert body, f"cannot locate the item schema for {field!r} in VideoSpec.schema.ts"
        for key in keys:
            declaration = _field_declaration(body, key)
            assert declaration is not None, f"{field}[].{key} not found in the TS schema"
            assert ".optional()" not in declaration, (
                f"{field}[].{key} IS optional in the TS schema, so treating it as HARD "
                f"rejects valid specs. Move it to _ROW_SHAPES_SOFT."
            )


def test_soft_table_keys_are_optional_in_the_ts_schema() -> None:
    """And every SOFT key must genuinely BE optional — otherwise a missing one
    red-cards the render and we only printed a warning."""
    for field, keys in _ROW_SHAPES_SOFT.items():
        body = _item_object_source(field)
        assert body, f"cannot locate the item schema for {field!r} in VideoSpec.schema.ts"
        for key in keys:
            declaration = _field_declaration(body, key)
            assert declaration is not None, f"{field}[].{key} not found in the TS schema"
            assert ".optional()" in declaration, (
                f"{field}[].{key} is REQUIRED in the TS schema, so a missing value "
                f"red-cards the whole video. Move it to _ROW_SHAPES_HARD."
            )
