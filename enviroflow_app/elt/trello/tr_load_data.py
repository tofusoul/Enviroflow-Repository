import polars as pl

from enviroflow_app.helpers.str_helpers import clean_field_name

from . import tr_model


def build_cards_df_from_boards_dict(
    boards_dict: dict[str, tr_model.Board],
) -> pl.DataFrame:
    """Builds the dataframe from the pydantic model that parses the board data request json.
    also includs a function that drops custom fields on the boards that aren't relevant
    to current needs. Alter the two constants in that subfunction to alter what is dropped and renamed
    """
    # get_custom_field_names:
    boards = [b for b in boards_dict.values()]
    custom_field_names = []
    cards = []

    for b in boards:
        for v in b.custom_fields_lookup.values():
            custom_field_names.append(v["name"])
        cards.extend(b.cards)

    card_records = []
    custom_field_names = list(set(custom_field_names))

    for c in cards:
        card = {}
        card["card_title"] = c.name
        card["card_id"] = c.id
        card["short_url"] = c.shortLink
        card["url"] = c.url
        card["board_name"] = c.board_name
        card["status"] = c.list_name
        card["labels"] = [label.name for label in c.labels]
        card["desc"] = c.desc
        card["address"] = c.address
        card["due"] = c.due
        card["due_complete"] = c.dueComplete
        card["attatchments"] = [str(a.url) for a in c.attachments]
        card["static_map_url"] = c.staticMapUrl
        card["coordinates"] = c.coordinates

        for cf in custom_field_names:
            if cf in c.custom_fields:
                card[clean_field_name(cf)] = c.custom_fields[cf]["value"]
            else:
                card[clean_field_name(cf)] = None
        # get rid of unused fields
        card.pop("spouting_done", None)

        card_records.append(card)

    df = pl.from_dicts(card_records, infer_schema_length=10000)
    return df
