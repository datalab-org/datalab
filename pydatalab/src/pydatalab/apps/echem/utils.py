import navani.echem as ec
import numpy as np
import pandas as pd

from pydatalab.logger import LOGGER
from pydatalab.utils import reduce_df_size


def reduce_echem_cycle_sampling(df: pd.DataFrame, num_samples: int = 100) -> pd.DataFrame:
    """Reduce number of cycles to at most `num_samples` points per half cycle. Will
    keep the endpoint values of each half cycle.

    Parameters:
        df: The echem dataframe to reduce, which must have cycling data stored
            under a `"half cycle"` column.
        num_samples: The maximum number of sample points to include per cycle.

    Returns:
        The output dataframe.

    """

    return_df = pd.DataFrame([])

    for _, half_cycle in df.groupby("half cycle"):
        return_df = pd.concat([return_df, reduce_df_size(half_cycle, num_samples, endpoint=True)])

    return return_df


def compute_gpcl_differential(
    df: pd.DataFrame,
    mode: str = "dQ/dV",
    smoothing: bool = True,
    polynomial_spline: int = 3,
    s_spline: float = 1e-5,
    window_size_1: int = 101,
    window_size_2: int = 1001,
    polyorder_1: int = 5,
    polyorder_2: int = 5,
    use_normalized_capacity: bool = False,
) -> pd.DataFrame:
    """Compute differential dQ/dV or dV/dQ for the input dataframe.

    Args:
        df: The input dataframe containing the raw cycling data.
        mode: Either 'dQ/dV' or 'dV/dQ'. Invalid inputs will default to 'dQ/dV'.
        smoothing: Whether or not to apply additional smoothing to the output differential curve.
        polynomial_spline: The degree of the B-spline fit used by navani.
        s_spline: The smoothing parameter used by navani.
        window_size_1: The window size for the `savgol` filter when smoothing the capacity.
        window_size_2: The window size for the `savgol` filter when smoothing the final differential.
        polyorder_1: The polynomial order for the `savgol` filter when smoothing the capacity.
        polyorder_2: The polynomial order for the `savgol` filter when smoothing the final differential.

    Returns:
        A data frame containing the voltages, capacities and requested differential
        on the reduced cycle list.

    """
    if len(df) < 2:
        LOGGER.debug(
            "compute_gpcl_differential called on dataframe with length %s, too small to calculate derivatives",
            len(df),
        )
        return df

    if mode.lower().replace("/", "") == "dvdq":
        y_label = "voltage (V)"
        x_label = "capacity (mAh/g)" if use_normalized_capacity else "capacity (mAh)"
        yp_label = "dV/dQ (V/mA)"
    else:
        y_label = "capacity (mAh/g)" if use_normalized_capacity else "capacity (mAh)"
        x_label = "voltage (V)"
        yp_label = "dQ/dV (mA/V)"

    smoothing_parameters = {
        "polynomial_spline": polynomial_spline,
        "s_spline": s_spline,
        "window_size_1": window_size_1 if window_size_1 % 2 else window_size_1 + 1,
        "window_size_2": window_size_2 if window_size_2 % 2 else window_size_2 + 1,
        "polyorder_1": polyorder_1,
        "polyorder_2": polyorder_2,
        "final_smooth": smoothing,
    }

    differential_df = pd.DataFrame()

    # Loop over distinct half cycles
    for cycle in df["half cycle"].unique():
        # Extract all segments corresponding to this half cycle index
        df_cycle = df[df["half cycle"] == cycle]

        # Compute the desired derivative
        try:
            x, yp, y = ec.dqdv_single_cycle(
                df_cycle[y_label], df_cycle[x_label], **smoothing_parameters
            )
        except TypeError as e:
            LOGGER.debug(
                "Calculating derivative %s of half_cycle %s failed with the following error (likely it is a rest or voltage hold):\n                 %s\n                Skipping derivative calculation for this half cycle.",
                mode,
                cycle,
                e,
            )
            continue

        # Set up an array per cycle segment that stores the cycle and half-cycle index
        cycle_index = df_cycle["full cycle"].max()
        cycle_index_array = np.full(len(x), int(cycle_index), dtype=int)
        half_cycle_index_array = np.full(len(x), int(cycle), dtype=int)

        differential_df = pd.concat(
            [
                differential_df,
                pd.DataFrame(
                    {
                        x_label: x,
                        y_label: y,
                        yp_label: yp,
                        "full cycle": cycle_index_array,
                        "half cycle": half_cycle_index_array,
                    }
                ),
            ]
        )

    return differential_df


def filter_df_by_cycle_index(df: pd.DataFrame, cycle_list: list[int] | None = None) -> pd.DataFrame:
    """Filters the input dataframe by the chosen rows in the `cycle_list`.
    If `half_cycle` is a column in the df, it will be used for filtering,
    otherwise `cycle index` will be used.

    Args:
        df: The input dataframe to filter. Must have the column "half cycle".
        cycle_list: The provided list of cycle indices to keep.

    Returns:
        A dataframe with all the data for the selected cycles.

    """
    if cycle_list is None:
        return df

    cycle_list = sorted(i for i in cycle_list if i > 0)

    if "half cycle" not in df.columns:
        if "cycle index" not in df.columns:
            raise ValueError(
                "Input dataframe must have either 'half cycle' or 'cycle index' column"
            )

        if len(cycle_list) == 1 and max(cycle_list) > df["cycle index"].max():
            cycle_list[0] = df["cycle index"].max()
        return df[df["cycle index"].isin(i for i in cycle_list)].copy()

    try:
        if len(cycle_list) == 1 and 2 * max(cycle_list) > df["half cycle"].max():
            cycle_list[0] = df["half cycle"].max() // 2
        half_cycles = [
            i
            for item in cycle_list
            for i in [max((2 * int(item)) - 1, df["half cycle"].min()), 2 * int(item)]
        ]
    except ValueError as exc:
        raise ValueError(
            f"Unable to parse `cycle_list` as integers: {cycle_list}. Error: {exc}"
        ) from exc
    return df[df["half cycle"].isin(half_cycles)].copy()
