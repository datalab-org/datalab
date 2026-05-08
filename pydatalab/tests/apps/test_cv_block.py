from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from bokeh.models import ColorBar, Legend, LinearColorMapper, Plot

from pydatalab.apps.cv import CONTINUOUS_COLORMAP_THRESHOLD, CVBlock
from pydatalab.apps.cv.utils import _infer_half_cycles, _split_by_cycle, parse_chi_cv_txt
from pydatalab.bokeh_plots import selectable_axes_plot


def _get_figure(layout):
    """Extract the Bokeh Figure from a selectable_axes_plot layout by type, not position."""
    for child in layout.children:
        if isinstance(child, Plot):
            return child
    raise AssertionError("No Bokeh Figure found in layout children")


def _make_chi_txt(tmp_path, n_cycles: int = 3) -> Path:
    """Write a minimal CHI-format CV .txt file with the given number of full cycles."""
    # Each full cycle is one down-sweep and one up-sweep
    potential = []
    for _ in range(n_cycles):
        potential.extend(np.linspace(1.0, -1.0, 50).tolist())  # sweep down
        potential.extend(np.linspace(-1.0, 1.0, 50).tolist())  # sweep up
    current = [v * 1e-3 for v in potential]  # dummy current in A

    lines = ["Potential/V, Current/A\n", "\n"]
    lines += [f"{v:.6f}, {i:.6e}\n" for v, i in zip(potential, current)]

    path = tmp_path / "test_cv.txt"
    path.write_text("".join(lines))
    return path


# --- Parser tests ---


def test_parse_chi_txt_columns(tmp_path):
    path = _make_chi_txt(tmp_path, n_cycles=2)
    df = parse_chi_cv_txt(path)
    assert set(df.columns) == {"Potential (V)", "Current (mA)", "Cycle"}


def test_parse_chi_txt_cycle_count(tmp_path):
    path = _make_chi_txt(tmp_path, n_cycles=3)
    df = parse_chi_cv_txt(path)
    assert df["Cycle"].nunique() == 3


def test_parse_chi_txt_current_units(tmp_path):
    """Current should be in mA (input is A, so multiplied by 1000)."""
    path = _make_chi_txt(tmp_path, n_cycles=1)
    df = parse_chi_cv_txt(path)
    # Input current is potential * 1e-3 A; output should be potential * 1e-3 * 1000 = potential mA
    assert df["Current (mA)"].abs().max() == pytest.approx(1.0, abs=0.01)


def test_parse_chi_txt_missing_header(tmp_path):
    path = tmp_path / "bad.txt"
    path.write_text("some random text\nwithout the right header\n")
    with pytest.raises(RuntimeError, match="Could not find data header"):
        parse_chi_cv_txt(path)


def test_split_by_cycle():
    df = pd.DataFrame(
        {
            "Potential (V)": [0.0, 1.0, 0.0, 1.0],
            "Current (mA)": [0.1, 0.2, 0.3, 0.4],
            "Cycle": [0, 0, 1, 1],
        }
    )
    result = _split_by_cycle(df)
    assert list(result.keys()) == ["Cycle 0", "Cycle 1"]
    assert len(result["Cycle 0"]) == 2
    assert len(result["Cycle 1"]) == 2


def test_infer_half_cycles_leading_flat():
    """A hold at the start (zero diffs) must not create a spurious half-cycle boundary."""
    # Three flat points then a down-sweep then an up-sweep → 2 half-cycles (0 and 1)
    potential = np.array([1.0, 1.0, 1.0, 0.5, 0.0, -0.5, -1.0, -0.5, 0.0, 0.5, 1.0])
    hc = _infer_half_cycles(potential)
    # All flat points should be assigned to the same half-cycle as the first sweep
    assert hc[0] == hc[2] == hc[3], "leading hold should share half-cycle with first sweep"
    # There should be exactly one direction reversal → two distinct half-cycle values
    assert len(np.unique(hc)) == 2


# --- Mode A: discrete colors, at or below threshold ---


def test_mode_a_legend_shown_for_multiple_series(tmp_path):
    path = _make_chi_txt(tmp_path, n_cycles=CONTINUOUS_COLORMAP_THRESHOLD)
    cv_dict = _split_by_cycle(parse_chi_cv_txt(path))
    fig = _get_figure(CVBlock._format_cv_plot(cv_dict))
    external_legends = [r for r in fig.right if isinstance(r, Legend)]
    assert len(external_legends) == 1
    assert len(external_legends[0].items) == CONTINUOUS_COLORMAP_THRESHOLD
    assert external_legends[0].click_policy == "hide"


def test_mode_a_legend_hidden_for_single_series(tmp_path):
    path = _make_chi_txt(tmp_path, n_cycles=1)
    cv_dict = _split_by_cycle(parse_chi_cv_txt(path))
    fig = _get_figure(CVBlock._format_cv_plot(cv_dict))
    assert not any(isinstance(r, Legend) for r in fig.right)


def test_mode_a_no_colorbar(tmp_path):
    path = _make_chi_txt(tmp_path, n_cycles=CONTINUOUS_COLORMAP_THRESHOLD)
    cv_dict = _split_by_cycle(parse_chi_cv_txt(path))
    fig = _get_figure(CVBlock._format_cv_plot(cv_dict))
    assert not any(isinstance(r, ColorBar) for r in fig.right)


# --- Mode C: continuous colors, above threshold ---


def test_mode_c_colorbar_shown(tmp_path):
    path = _make_chi_txt(tmp_path, n_cycles=CONTINUOUS_COLORMAP_THRESHOLD + 1)
    cv_dict = _split_by_cycle(parse_chi_cv_txt(path))
    fig = _get_figure(CVBlock._format_cv_plot(cv_dict))
    colorbars = [r for r in fig.right if isinstance(r, ColorBar)]
    assert len(colorbars) == 1
    assert isinstance(colorbars[0].color_mapper, LinearColorMapper)


def test_mode_c_no_legend(tmp_path):
    path = _make_chi_txt(tmp_path, n_cycles=CONTINUOUS_COLORMAP_THRESHOLD + 1)
    cv_dict = _split_by_cycle(parse_chi_cv_txt(path))
    fig = _get_figure(CVBlock._format_cv_plot(cv_dict))
    assert not any(isinstance(r, Legend) for r in fig.right)


def test_mode_c_colorbar_range(tmp_path):
    path = _make_chi_txt(tmp_path, n_cycles=CONTINUOUS_COLORMAP_THRESHOLD + 1)
    cv_dict = _split_by_cycle(parse_chi_cv_txt(path))
    cycle_numbers = [df["Cycle"].iloc[0] for df in cv_dict.values()]
    fig = _get_figure(CVBlock._format_cv_plot(cv_dict))
    colorbar = next(r for r in fig.right if isinstance(r, ColorBar))
    assert colorbar.color_mapper.low == min(cycle_numbers)
    assert colorbar.color_mapper.high == max(cycle_numbers)


# --- Validation ---


def test_series_color_values_length_mismatch_raises(tmp_path):
    path = _make_chi_txt(tmp_path, n_cycles=3)
    cv_dict = _split_by_cycle(parse_chi_cv_txt(path))
    with pytest.raises(ValueError, match="series_color_values has 2 entries but df has 3"):
        selectable_axes_plot(
            cv_dict,
            x_options=["Potential (V)"],
            y_options=["Current (mA)"],
            series_color_values=[0, 1],  # wrong length
            plot_points=False,
            plot_line=True,
        )
