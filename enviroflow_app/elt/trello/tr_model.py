from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import AnyUrl, BaseModel, Field, computed_field


class CustomFieldValue(BaseModel):
    text: Optional[str] = Field(default=None)
    number: Optional[float] = Field(default=None)
    checked: Optional[bool] = Field(default=None)
    date: Optional[datetime] = Field(default=None)


class CustomFieldItem(BaseModel):
    id: str
    idCustomField: str
    idModel: str
    modelType: str
    value: Optional[CustomFieldValue] = Field(default=None)
    idValue: Optional[str]  # For dropdown fields to match with the options


class CustomField(BaseModel):
    id: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None)
    type: Optional[str] = Field(default=None)
    options: Optional[List[Dict[str, Any]]] | None = Field(
        default=None,
    )  # For dropdown options


class Attachment(BaseModel):
    id: str
    url: AnyUrl
    fileName: str


class Label(BaseModel):
    id: str
    idBoard: str
    name: str
    color: str
    uses: int


class Card(BaseModel):
    id: str
    desc: Optional[str] = Field(default=None)
    address: Optional[str] = Field(default=None)
    board_name: Optional[str] = Field(default=None)
    due: Optional[datetime] = Field(default=None)
    dueComplete: Optional[bool] = Field(default=None)
    idBoard: str
    idList: str
    idLabels: Optional[list[str]] = Field(default=None)
    labels: Optional[list[Label]] = Field(default=None)
    name: str
    shortLink: str
    staticMapUrl: Optional[AnyUrl] = Field(default=None)
    url: AnyUrl
    attachments: list[Attachment] | None = Field(default=None)
    customFieldItems: list[CustomFieldItem] | None = Field(default=None)
    list_name: Optional[str] = Field(default=None)
    custom_fields: Optional[dict] = Field(default=None)
    coordinates: Optional[dict[str, float]] = Field(default=None)

    def build_custom_fields(self, field_lookup: dict, drop_down_options: dict):
        custom_fields = {}
        if self.customFieldItems is not None:
            for cfi in self.customFieldItems:
                field_name = field_lookup[cfi.idCustomField]["name"]
                field_type = field_lookup[cfi.idCustomField]["type"]
                if cfi.value is not None:
                    match field_type:
                        case "checkbox":
                            field_value = cfi.value.checked
                        case "date":
                            field_value = cfi.value.date
                        case "text":
                            field_value = cfi.value.text
                        case "number":
                            field_value = cfi.value.number
                        case _:
                            field_value = None
                elif field_type == "list":
                    field_value = drop_down_options[cfi.idValue]
                else:
                    field_value = None

                custom_fields[field_name] = {
                    "type": field_type,
                    "value_id": cfi.id,
                    "field_id": cfi.idCustomField,
                    "value": field_value,
                }

            self.custom_fields = custom_fields

            return self


class Board(BaseModel):
    """Representation of a trello board"""

    id: str
    name: str
    idOrganization: str
    url: AnyUrl
    shortUrl: AnyUrl
    cards: list[Card]
    customFields: list[CustomField]
    list_lookup: Optional[dict] = Field(default=None)  # dict

    @computed_field
    @property
    def custom_fields_lookup(self) -> dict:
        field_dict = {
            field.id: {
                "name": field.name,
                "type": field.type,
            }
            for field in self.customFields
        }
        return field_dict

    @computed_field
    @property
    def drop_down_options(self) -> dict:
        dropdown_options = {}
        for cf in self.customFields:
            if cf.type == "list":
                for opt in cf.options:
                    dropdown_options[opt["id"]] = opt["value"]["text"]
        return dropdown_options

    def set_list_names(self, list_lookup: dict):
        """Sets the list names for each car"""
        self.list_lookup = list_lookup
        for card in self.cards:
            card.list_name = list_lookup[card.idList]

    def model_post_init(self, ctx) -> None:
        for card in self.cards:
            card.board_name = self.name
            card.build_custom_fields(self.custom_fields_lookup, self.drop_down_options)
            if self.list_lookup is not None:
                self.set_list_names(self.list_lookup)
