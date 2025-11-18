from dataclasses import dataclass, field
from datetime import date
from functools import cached_property

import pandas as pd
import polars as pl
from loguru import logger

QUOTE_LOOKUP = [
    (
        "ss",
        "sewer",
        "[R,r]emove and replace(?!.*stormwater).*.sewer(?!.*stormwater)",
        "Remove and replace sewer per metre",
        True,
    ),
    (
        "sw",
        "storm water",
        "[R,r]emove and replace(?!.*sewer).*.stormwater(?!.*sewer)",
        "Remove and replace stormwater per metre",
        True,
    ),
    (
        "sssw",
        "storm water and sewer in shared trench",
        "sewer and stormwater|[S,s]hared [T,t]rench",
        "Remove and reinstate sewer and stormwater in shared trench per metre",
        True,
    ),
    (
        "gully",
        "gully trap",
        "[G,g]ully",
        "Remove and dispose existing gully. Supply and install new gully trap and dish",
        True,
    ),
    (
        "bub",
        "bubble up sump",
        "[B,b]ubble",
        "Supply and install bubble up sump",
        True,
    ),
    (
        "cap_sewer",
        "cap sewer less than 300mm deep",
        "[C,c]ap [S,s]ewer",
        "Concrete cap sewer as current sewer is less than 300mm deep",
        True,
    ),
    (
        "drive_sump",
        "driveway sump",
        "[D,d]riveway [S,s]ump",
        "Heavy duty Driveway Sump - Supply and install",
        True,
    ),
    (
        "channel_drain",
        "channel drains per metre",
        "[C,c]hannel [D,d]rains",
        "Supply and install channel drains per metre as indicated",
        True,
    ),
    (
        "hardfill",
        "AP20/40 hardfill per m3",
        "[A,a][P,p]20/40",
        "AP20/40 per m3 (includes delivery and compaction)",
        True,
    ),
    (
        "concrete",
        "all concrete",
        "[R,r]emove and replace(?!.*[P,p]aver).*[C,c]oncrete",
        "Remove concrete per m2",
        True,
    ),
    (
        "concut",
        "double cut concrete",
        "[D,d]ouble [C,c]ut",
        "Double cut concrete",
        True,
    ),
    (
        "asphalt",
        "asphalt",
        "[R,r]emove and replace.*asphalt*",
        "Remove asphalt per m2",
        True,
    ),
    (
        "deck",
        "deck",
        "^((?!.*[P,p]ipelining|[C,c]oncrete|[U,u]nder|[P,p]aint|CCTV|[s,S]tormwater|[s,S]ide|[L,l]abour|[R,r]e-route|[C,c]onnect|[A,a]dditional|[U,u]plift|[P,p]atch|[R,r]e-.*).)*.[d,D]eck",
        "Remove decking as required",
        True,
    ),
    (
        "gravel",
        "gravel driveway",
        "[D,d]riveway [G,g]ravel",
        "Driveway gravel to replace above trenchlines per m3",
        True,
    ),
    (
        "pavers_not_in_concrete",
        "pavers not set in concrete",
        "^((?!.*Pipelining.*).)*.pavers not|relay [P,p]avers",
        "Uplift and store pavers onsite, per m2",
        True,
    ),
    (
        "pavers_in_concrete",
        "pavers set in concrete",
        "^((?!.*Pipelining.*).)*.pavers set",
        "Remove pavers set in concrete. per m2",
        True,
    ),
    (
        "bush",
        "remove bush/tree",
        "[B,b]ush",
        "Remove and dispose of bush/tree",
        True,
    ),
    (
        "bark_mulch",
        "bark mulch",
        "[B,b]ark [M,m]ulch",
        "Place bark munch per m3",
        True,
    ),
    (
        "bark_nugget",
        "bark nugget",
        "[B,b]ark [N,n]ugget",
        "Place bark munch per m3",
        True,
    ),
    (
        "clothes_line",
        "remove and reinstate clothes line",
        "[C,c]lothes [L,l]ine",
        "Clothes Line remove, store on site and reinstate after repairs",
        True,
    ),
    (
        "fence",
        "remove and reinstate fence",
        "[F,f]ence",
        "Fence - remove and reinstate fence per metre (if fence too damaged to reinstate please contact PM)",
        True,
    ),
    (
        "weed_mat",
        "weed mat 1x20m",
        "[W,w]eed [M,m]at",
        "Weed mat per 1x20m roll",
        True,
    ),
    (
        "hydroseed",
        "compact soil, level and hydroseed",
        "[H,h]ydroseed",
        "Supply and compact soil, level, ready for hydroseed above trench lines",
        True,
    ),
    (
        "stones_on_mat",
        "store stones on mat and reinstate",
        "stones on mat",
        "Uplift, store decorative stones on mat, reinstate after repairs",
        True,
    ),
    (
        "add_lab",
        "additional labour to bucket chip and barrel spoil",
        "[A,a]dditional [L,l]abour",
        "Additional labour to bucket chip and barrel spoil",
        True,
    ),
    (
        "gas",
        "temporary gas bottle",
        "[G,g]as [B,b]ottle",
        "Remove large bottles at trench line, store on site, provide small gas bottle, reinstate after repairs",
        True,
    ),
    (
        "watermain",
        "blueline watermain",
        "[B,b]lueline|[W,w]atermain",
        "Install new 25mm Blueline in existing trench per m",
        True,
    ),
    (
        "pipelining",
        "pipelining",
        "[P,p]ipelining|[P,p]ipe [L,l]ining",
        "",
        False,
    ),
    (
        "trench_shield",
        "manhole trench shield",
        "[S,s]hield|[T,t]rench [S,s]hield|[M,m]anhole [T,t]rench",
        "",
        True,
    ),
    ("contaminated", "contaminated soil", "[C,c]ontaminated", "", True),
]


@dataclass(kw_only=True)
class Quote:
    quote_no: str
    quote_ref: str = field(repr=False)
    quote_status: str | None = field(default=None)
    created: date | None = field(repr=False)
    quote_source: str
    quote_lines: pl.DataFrame = field(repr=False)
    quote_value: float | None = field(default=None)

    def __str__(self):
        desc = (
            f"{self.quote_no}-{self.quote_ref}-${self.quote_value}-{self.quote_status}"
        )
        return desc

    def __repr__(self):
        return self.__str__()

    # TODO: Build Budget Into Code
    # budget: float
    # labour_budget: float
    # supplier_budget: float
    # total_budget: float
    #
    @cached_property
    def df(self):
        return self.quote_lines.to_pandas()

    @staticmethod
    def filter_quote_dfs(df_pandas: pd.DataFrame, filter_str: str) -> pd.DataFrame:
        """Accepts any quote dataframe and filter the lines according to the conditions"""
        try:
            filtered = df_pandas[
                df_pandas["item_desc"].str.contains(filter_str, regex=True)
            ]
            filtered = filtered.copy()  # Avoid SettingWithCopyWarning
            filtered.loc[:, "line_qty"] = filtered["line_pct"] * filtered["quantity"]
            return filtered
        except KeyError:
            logger.error("couldn't find data frame column to filter")
            return pd.DataFrame()

    def filter_quote(self, filter_str: str) -> pd.DataFrame:
        """Accepts a regex filter string and returns a sub quote with only lines that contains the string"""
        return self.filter_quote_dfs(self.df, filter_str)

    @cached_property
    def quote_analysis(self) -> dict:
        """Creates a dictionary that gives the attributes of the quotes that can be used in downstream applications"""
        df = pd.DataFrame()
        analysis = {}
        for i in QUOTE_LOOKUP:
            try:
                df = self.filter_quote(i[2])  # type: ignore
            except Exception as e:
                logger.error(f"{self.quote_ref} could not be filtered /n {e}")
            try:
                qty = float(df["line_qty"].sum())
            except Exception as e:
                logger.error(f"{self.quote_ref} couldn't sum up quantities/n {e}")
                qty = 0
            try:
                has = bool(self.df["item_desc"].str.contains(i[2]).any())
            except Exception as e:
                logger.error(
                    f"{self.quote_ref} couldn't process filter on item name /n {e}",
                )
                has = False
            analysis[i[0]] = {
                "df": df,
                "desc": i[1],
                "qty": qty,
                "has": has,
                "sub": i[3],
                "subs_work": i[4],
            }

        return analysis

    @cached_property
    def qty_from_quote(self) -> dict:
        qtys = {}
        try:
            for (
                k,
                v,
            ) in self.quote_analysis.items():
                if v["has"]:
                    qtys[k] = v
        except Exception as e:
            logger.error(f"{self.quote_ref} quote can't be parsed \n{e}")
            qtys = {}

        return qtys

    # @cached_property
    # def quote_value(self) -> float:
    #     return self.df["line_total"].sum()

    @cached_property
    def quote_lines_dict(self) -> list[dict]:
        df = self.df.drop(columns=["quote_no", "quote_ref", "customer", "quote_source"])
        quote_lines = df.to_dict(orient="records")
        return quote_lines

    @cached_property
    def qty_dict(self) -> dict:
        qty = {}
        qty_src = self.qty_from_quote.copy()
        for key, data in qty_src.items():
            df: pd.DataFrame = data["df"].drop(columns=["quote_ref", "customer"])
            qty[key] = {k: v for k, v in data.items() if k != "df"}
            qty[key]["relevant_quote_lines"] = df.to_dict("records")
        return qty


def merge_quotes(quotes: list[Quote], name: str) -> Quote:
    """If the quote list has multiple quotes, merge the quotes and into one dataframe,
    else return the quote
    """
    dfs = [quote.quote_lines for quote in quotes]
    try:
        df = pl.concat(dfs)
    except ValueError:
        logger.error("couldn't concatenate quote")
        df = pl.DataFrame()
    merged_quotes = Quote(
        created=date.today(),
        quote_lines=df,
        quote_no="various",
        quote_ref=name,
        quote_source="merged",
    )
    return merged_quotes
