"""Tests pour helpers.common.chart_format."""

from helpers.common.chart_format import ascii_bars, bar_chart, with_ascii


def test_ascii_bars_empty() -> None:
    assert ascii_bars([], []) == ""
    assert ascii_bars(["a"], []) == ""


def test_ascii_bars_scales_to_max() -> None:
    text = ascii_bars(["A", "B"], [100, 50], width=10, label_width=4)
    lines = text.splitlines()
    assert len(lines) == 2
    assert lines[0].startswith("A")
    assert lines[0].count("█") == 10
    assert lines[1].count("█") == 5
    assert lines[0].endswith("100")
    assert lines[1].endswith("50")


def test_ascii_bars_all_zeros() -> None:
    text = ascii_bars(["x"], [0], width=8, label_width=4)
    assert "█" not in text
    assert text.endswith("0")


def test_ascii_bars_truncates_label_and_items() -> None:
    text = ascii_bars(
        ["very-long-organization-name", "b", "c"],
        [3, 2, 1],
        width=4,
        max_items=2,
        label_width=8,
    )
    lines = text.splitlines()
    assert len(lines) == 2
    assert "…" in lines[0]


def test_bar_chart_includes_ascii() -> None:
    chart = bar_chart(["Montréal", "Laval"], [389, 130], metric="datasets")
    assert chart["type"] == "bar"
    assert chart["metric"] == "datasets"
    assert chart["categories"] == ["Montréal", "Laval"]
    assert chart["values"] == [389, 130]
    assert "Montréal" in chart["ascii"]
    assert "389" in chart["ascii"]


def test_with_ascii_skips_non_bar() -> None:
    line = {"type": "line", "points": []}
    assert with_ascii(line) is line or with_ascii(line) == line
    assert "ascii" not in with_ascii({"type": "line", "points": []})
