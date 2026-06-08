"""This module implements cross-sample overlay comparison of data blocks.

Unlike a normal block, which renders the data from a single item, the comparison
endpoint loads the underlying data for several blocks (potentially attached to
different items) and merges them into a single overlaid Bokeh plot.

It is fully generic: a block opts into overlay comparison by implementing
:meth:`pydatalab.blocks.base.DataBlock.get_comparison_data`, and this endpoint
discovers that capability by introspection of ``BLOCK_TYPES``. No per-block code
or central registry lives here — adding a new (core or plugin) block type to
overlay comparison requires no changes to this file.
"""

from typing import Any

import bokeh.embed
import pandas as pd
from flask import Blueprint, jsonify, request
from werkzeug.exceptions import BadRequest

from pydatalab.apps import BLOCK_TYPES
from pydatalab.bokeh_plots import DATALAB_BOKEH_THEME, selectable_axes_plot
from pydatalab.logger import LOGGER
from pydatalab.mongo import flask_mongo
from pydatalab.permissions import active_users_or_get_only, get_default_permissions

COMPARISON = Blueprint("comparison", __name__)


@COMPARISON.before_request
@active_users_or_get_only
def _(): ...


@COMPARISON.route("/blocks/compare/", methods=["POST"])
def compare_blocks():
    """Overlay the data from several blocks into a single Bokeh plot.

    Expects a JSON body of the form::

        {
            "blocks": [
                {"item_id": "sample-A", "block_id": "abc123", "label": "Sample A"},
                {"item_id": "sample-B", "block_id": "def456"}
            ]
        }

    ``label`` is optional and defaults to the item_id. All referenced blocks must be
    the same type, and that type must support overlay comparison (i.e. implement
    ``get_comparison_data``).

    Returns ``{"bokeh_plot_data": {...}}`` on success.
    """
    request_json = request.get_json() or {}
    block_refs = request_json.get("blocks")

    if not block_refs or not isinstance(block_refs, list):
        raise BadRequest("Must supply a non-empty list of blocks to compare.")
    if len(block_refs) < 2:
        raise BadRequest("Need at least two blocks to compare.")

    # Load each block's stored config from its parent item, respecting permissions.
    block_configs: list[dict[str, Any]] = []
    for ref in block_refs:
        item_id = ref.get("item_id")
        block_id = ref.get("block_id")
        if not item_id or not block_id:
            raise BadRequest("Each block reference must include `item_id` and `block_id`.")

        item = flask_mongo.db.items.find_one(
            {"item_id": item_id, **get_default_permissions(user_only=False)},
            {f"blocks_obj.{block_id}": 1},
        )
        if not item or block_id not in item.get("blocks_obj", {}):
            raise BadRequest(
                f"Could not find block {block_id!r} on item {item_id!r} (or no permission)."
            )
        block_configs.append(item["blocks_obj"][block_id])

    # All blocks must share a type that supports overlay comparison.
    blocktypes = {cfg.get("blocktype") for cfg in block_configs}
    if len(blocktypes) != 1:
        raise BadRequest(f"All blocks must be the same type to overlay; got {sorted(blocktypes)}.")

    blocktype = blocktypes.pop()
    block_cls = BLOCK_TYPES.get(blocktype)
    if block_cls is None or not block_cls.supports_comparison():
        raise BadRequest(f"Overlay comparison is not supported for {blocktype!r} blocks.")

    labelled_dfs: dict[str, pd.DataFrame] = {}
    comparison = None  # axis config; consistent across same-type blocks
    for ref, cfg in zip(block_refs, block_configs):
        block = block_cls.from_web(cfg)
        try:
            data = block.get_comparison_data()
        except BadRequest:
            raise
        except Exception as exc:
            LOGGER.warning("Could not load comparison data for block: %s", exc)
            raise BadRequest(f"Could not load data for block on item {ref.get('item_id')!r}: {exc}")

        if data is None or not data.series:
            raise BadRequest(f"No comparable data for block on item {ref.get('item_id')!r}.")
        comparison = data

        # Build a human-readable legend label, falling back to the item_id. A block
        # contributing several series is disambiguated by the per-series sublabel.
        base_label = ref.get("label") or ref.get("item_id")
        for sublabel, df in data.series:
            label = base_label if not sublabel else f"{base_label} – {sublabel}"
            unique_label = label
            suffix = 1
            while unique_label in labelled_dfs:
                suffix += 1
                unique_label = f"{label} ({suffix})"
            labelled_dfs[unique_label] = df

    plot = selectable_axes_plot(
        labelled_dfs,
        x_options=comparison.x_options,
        x_default=comparison.x_default,
        y_options=comparison.y_options or None,
        y_default=comparison.y_default,
        plot_line=True,
        plot_points=False,
        use_unique_labels=False,
    )

    return jsonify(
        {
            "status": "success",
            "bokeh_plot_data": bokeh.embed.json_item(plot, theme=DATALAB_BOKEH_THEME),
        }
    )
