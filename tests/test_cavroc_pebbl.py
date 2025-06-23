import pytest
from src.CavrocPebbl import style_accuracy


@pytest.mark.parametrize(
    "val,color",
    [("High", "#007BFF"), ("Intermediate", "#28a745"), ("Low", "#fd7e14")],
)
def test_style_accuracy_colors(val, color):
    out = style_accuracy(val)
    assert f'style="color: {color}' in out
    assert val in out


def test_style_accuracy_default():
    assert style_accuracy("Unknown") == "Unknown"