from collections.abc import Mapping

import polars as pl
from streamlit.delta_generator import DeltaGenerator

from enviroflow_app.elt.motherduck import md
from enviroflow_app.model import Raw_Project


def build_projects(
    conn: md.MotherDuck,
    labour_hours: pl.DataFrame,
    render_target: DeltaGenerator,
    quotes: pl.DataFrame,
) -> Mapping[str, Raw_Project]:
    pass
