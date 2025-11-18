from __future__ import annotations

import json

# import csv
import os

# import re
import time
from datetime import datetime

# from phonenumbers import phonenumbermatcher
# import phonenumbers
from pathlib import Path

# import numpy as np
import pandas as pd
import requests
import tabulate
from streamlit import secrets

try:
    trello_key = os.environ["TRELLO_KEY"]
except KeyError:
    trello_key = (secrets["trello"]["api_key"],)
try:
    trello_token = os.environ["TRELLO_TOKEN"]
except KeyError:
    trello_token = (secrets["trello"]["api_token"],)


def select_board():
    """Runs the prompt to get the board ind to query. Returns the board id to hand to the function that gets the reference data."""
    board_name_from_input = input(
        "Please type the name of the board that you would like to run the query on?",
    ).casefold()

    # api_key = api_key
    # api_token = api_token
    # desc_table_rexp = desc_table_rexp

    org_url = "https://api.trello.com/1/organizations/envirofloplan/boards?lists=all&filter=open"

    headers = {"accept": "application:json"}

    query = {
        # "key": config.api_key,
        "key": trello_key,
        "token": trello_token,
        # "token": config.api_token,
    }
    org_response = requests.request("GET", org_url, headers=headers, params=query)

    org_json = json.dumps(json.loads(org_response.text))
    org_df = pd.read_json(org_json)
    org_fields_dict = org_df[["name", "id"]].set_index("name").to_dict()["id"]

    board_id_name = None

    board_id_list = []
    for key in org_fields_dict.keys():
        if str(key).casefold().__contains__(str(board_name_from_input)):
            board_id_list.append(key)

    if len(board_id_list) < 2:
        board_id_name = board_id_list.pop()
    else:
        record = display(board_id_list)
        board_id_name = get_list(record)

    board_id = org_fields_dict.get(board_id_name)
    return board_id


def board_options():
    org_url = "https://api.trello.com/1/organizations/envirofloplan/boards?lists=all"

    headers = {"accept": "application:json"}

    query = {
        "key": trello_key,
        "token": trello_token,
    }

    org_response = requests.request("GET", org_url, headers=headers, params=query)

    org_json = json.dumps(json.loads(org_response.text))
    org_df = pd.read_json(org_json)
    org_fields_dict = org_df[["name", "id"]].set_index("name").to_dict()["id"]

    org_fields_dict["----------Select A Board----------"] = ""

    return org_fields_dict


def analyse_board(board_id: str) -> Board:
    """Function to analyse the board using the name given and return the dataframes for the board, lists and custom fields."""
    board_json = get_main_json(board_id)
    board_object = Board(board_json)
    return board_object


def Call_API(self):
    """Base API call."""
    base_url = f"https://api.trello.com/1/{self}"

    headers = {"Accept": "application:json"}

    query = {
        "key": trello_key,
        "token": trello_token,
    }

    base_response = requests.request("GET", base_url, headers=headers, params=query)

    return base_response.text


def display(list1: list) -> list:
    counter = 0
    record = []
    for tables in list1:
        counter += 1
        record.append(tables)
        print("%s. %s" % (counter, tables))
    return record


def get_list(record: list) -> str:
    print("\nPlease input the number of the board from the list:")
    choose = input()
    choice = int(choose) - 1
    chosen = record[choice]
    return chosen


def get_main_json(board_id: str) -> pd.DataFrame:
    """Function to get the main json body for the board. This will contain all the cards, labels and customfields for all items."""
    all_board_data_url = f"boards/{board_id}/?cards=visible&checklists=all&card_fields=name,shortLink,due,dueComplete,labels,idList,desc,dateLastActivity,checklists&customFields=true&card_customFieldItems=true&card_checklists=all&card_labels=true&card_idList=true&attachments=true&card_attachments=true&attachment_fields=all"

    final_json = pd.json_normalize(
        json.loads(Call_API(all_board_data_url)),
        max_level=1,
    )

    return final_json


def get_field_values_json(self):
    field_values_url_tail = f"customFields/{self}/options"

    field_value_response = Call_API(field_values_url_tail)

    return field_value_response


def get_cards_json(board_json: json) -> json:
    """Function to get the card json for the board from the large JSON response."""
    cards_json = board_json["cards"]

    return cards_json.explode()


def get_list_resources(board_id: str):
    """Function to get the lists that are assigned to a board by sending a call to the API. This function returns both a Dataframe
    and a dictionary from the JSON response.
    """
    lists_url_tail = f"boards/{board_id}/?lists=all"

    lists_respsonse = Call_API(lists_url_tail)

    lists_json = pd.json_normalize(json.loads(lists_respsonse), max_level=1)

    for item in lists_json["lists"]:
        lists_df = pd.DataFrame(item)[["id", "name"]].set_index("id")

    lists_dict = lists_df.to_dict()["name"]

    list_counts_dict = {}

    for item in lists_dict.values():
        list_counts_dict[item] = 0

    return lists_df, lists_dict, list_counts_dict


def create_description_resources(field_type_table: pd.DataFrame) -> tuple:
    """Function to create the description resources for the cards."""
    description_info_id_dict = {}
    desc_info_template_list = [
        "Customer Name",
        "Phone",
        "Customer Email",
        "2nd Contact",
        "EQC Claim Number",
        "EQC Claim Manager",
    ]
    for field in desc_info_template_list:
        field_id = field_type_table.loc[field_type_table["name"] == field].index.values[
            0
        ]
        description_info_id_dict[field_id] = field

    description_field_ids = [key for key in description_info_id_dict]

    return description_field_ids, description_info_id_dict


def get_card_custom_fields(
    json_data: str,
    field_type_table: pd.DataFrame,
    dropdown_options: pd.DataFrame,
) -> dict:
    card_custom_field_values_dict = {}

    if len(json_data["customFieldItems"]) >= 1:
        custom_fields_list = []
        custom_fields_list_dropdowns = []
        for field in field_type_table.index:
            card_custom_field_values_dict[field] = None
        for custom_field in json_data["customFieldItems"]:
            if custom_field.get("value"):
                custom_fields_list.append(
                    {
                        key: custom_field[key]
                        for key in custom_field.keys() & {"idCustomField", "value"}
                    },
                )
                for custom_field in custom_fields_list:
                    field_type = field_type_table.loc[
                        field_type_table.index == custom_field["idCustomField"],
                        "type",
                    ]
                    custom_field_type = field_type[0]
                    if custom_field_type == "checkbox":
                        custom_field_id = custom_field["idCustomField"]
                        card_custom_field_values_dict[custom_field_id] = custom_field[
                            "value"
                        ]["checked"]

                    else:
                        custom_field_id = custom_field["idCustomField"]
                        card_custom_field_values_dict[custom_field_id] = custom_field[
                            "value"
                        ][custom_field_type]

            else:
                custom_fields_list_dropdowns.append(
                    {
                        key: custom_field[key]
                        for key in custom_field.keys() & {"idCustomField", "idValue"}
                    },
                )
                for custom_field in custom_fields_list_dropdowns:
                    custom_field_id = custom_field["idCustomField"]
                    dropdown_field_value = dropdown_options.loc[
                        dropdown_options["_id"] == custom_field["idValue"],
                        "value",
                    ].values[0]
                    card_custom_field_values_dict[custom_field_id] = (
                        dropdown_field_value
                    )

    return card_custom_field_values_dict


def get_board_checklists(board_json: json) -> list:
    """Function to get the checklists for the board from the large JSON response."""
    board_checklists_list = []
    for checklist in board_json["checklists"][0]:
        if checklist["checkItems"] == []:
            pass
        else:
            board_checklists_list.append(
                {
                    checklist["name"]: {
                        checklist["checkItems"][0]["name"]: {
                            "state": checklist["checkItems"][0]["state"],
                            "due": checklist["checkItems"][0]["due"],
                        },
                    },
                },
            )
    return board_checklists_list


def get_card_checklists(board_json: json) -> list:
    """Function to get the checklists for the board from the large JSON response."""
    card_checklists = []
    for checklist in board_json["checklists"].__iter__():
        temp_dict = {}
        checklist_name = checklist["name"]
        if checklist["checkItems"] == []:
            pass
        else:
            for check_item in checklist["checkItems"]:
                if temp_dict == {}:
                    temp_dict[checklist_name] = {
                        check_item["name"]: {
                            "state": check_item["state"],
                            "due": check_item["due"],
                        },
                    }
                else:
                    temp_dict[checklist_name][check_item["name"]] = {
                        "state": check_item["state"],
                        "due": check_item["due"],
                    }
            card_checklists.append(temp_dict)
    return card_checklists


class Board:
    """An object that represents the a Trello board."""

    card_data = []

    def __init__(self, data):
        self.id = data["id"][0]
        self.name = data["name"][0]

        if len(data["checklists"]) >= 1:
            self.checklists = get_board_checklists(data)
        else:
            self.checklists = None

        self.labels = get_board_labels(self.id)
        self.lists = []
        self.lists_df, self.lists_dict, self.list_counts_dict = get_list_resources(
            self.id,
        )
        for name in self.lists_dict.values():
            self.lists.append(name)

        self.custom_fields = []
        (
            self.boards_df,
            self.field_type_table,
            self.custom_fields_outline,
        ) = get_custom_field_items(self.id)
        self.dropdown_options = get_dropdown_options(self.field_type_table)
        for row in self.field_type_table.iterrows():
            str_field = (row[1].values[0], row[1].values[1])
            self.custom_fields.append(str_field)

        self.cards_list = []
        for item in data["cards"].explode():
            card = Card(
                item,
                self.field_type_table,
                self.lists_dict,
                self.dropdown_options,
            )
            self.cards_list.append(card)

        cards_dict_list = []

        for card in self.cards_list:
            card_dict = {}
            for attr, val in card.__dict__.items():
                card_dict[attr] = val
            self.list_counts_dict[card.card_list] += 1
            cards_dict_list.append(card_dict)

        self.cards_dict_list = cards_dict_list

    def __repr__(self):
        return f"Trello Board({os.linesep}{os.linesep}Id: {self.id},{os.linesep}Name: {self.name} {os.linesep}{os.linesep}Custom Fields: {os.linesep}{os.linesep}{tabulate.tabulate(self.field_type_table.values)}{os.linesep}{os.linesep}Board Lists: {os.linesep}{tabulate.tabulate(self.list_counts_dict.items())})"

    def get_list_info(self):
        """Return a table that shows the number of cards in each list."""
        headers = ["List name: ", "Card count: "]
        print(tabulate.tabulate(self.list_counts_dict.items(), headers))

    def view_cards_df(self):
        """Function to output the cards frame to the screen."""
        card_info_frame = pd.DataFrame(self.cards_dict_list)
        print(card_info_frame)

    def get_card(self, card_name: str) -> any:
        """Function to fetch a card from the board using the in str method."""
        card_name_casefold = card_name.casefold()
        try:
            for card in self.cards_list:
                if card_name_casefold in card.name.casefold():
                    return card

        except IndexError:
            print("Card not found.")

    def to_dataframe(self):
        """Returns Dataframes"""
        removed_columns = [
            # "field_type_table",
            # "lists_dict",
            # "dropdown_options",
            # "description",
            "old_description",
            # "checklists",
            # "due",
            # "due_complete",
        ]

        base_names = {"id": "card_id", "name": "address"}
        card_info_frame = pd.DataFrame(self.cards_dict_list)
        card_info_frame.rename(columns=base_names, inplace=True)
        card_info_frame.drop(removed_columns, axis=1, inplace=True)

        dropdown_options_frame = pd.DataFrame(self.dropdown_options)
        dropdown_options_frame = dropdown_options_frame[
            ["name", "value", "color", "_id"]
        ]

        list_info_frame = pd.DataFrame(self.list_counts_dict.items())
        labels_frame = self.labels
        lists_df = self.lists_df
        field_type_table = self.field_type_table

        return (
            card_info_frame,
            dropdown_options_frame,
            list_info_frame,
            field_type_table,
            labels_frame,
            lists_df,
        )

    def to_parquet(self):
        """Function to write the boards card data to a CSV file."""
        data_folder = Path(".", "Data", "trello_data")
        # snapshot_folder = Path(".", "Data", "trello_data", "snapshots")

        """Create the file name for the timestamped CSV files."""
        stamp = time.localtime()
        (
            str(stamp.tm_year)
            + "_"
            + str(stamp.tm_mon)
            + "_"
            + str(stamp.tm_mday)
            + "_"
            + str(stamp.tm_hour)
            + "_"
            + str(stamp.tm_min)
        )
        temp = []
        for word in self.name.split():
            temp.append(word.casefold()[:3])
            name = "_".join(temp)
        file_name = name

        """Saving the csv files. One has a timestamp and the other is the most recent."""
        removed_columns = [
            "field_type_table",
            "lists_dict",
            "dropdown_options",
            "description",
            "old_description",
            "checklists",
            # "due",
            # "due_complete",
        ]
        base_names = {"id": "card_id", "name": "address"}
        card_info_frame = pd.DataFrame(self.cards_dict_list)
        card_info_frame.rename(columns=base_names, inplace=True)
        card_info_frame.drop(removed_columns, axis=1, inplace=True)
        card_info_file_name = f"cards_{file_name}.csv"
        card_info_frame.to_parquet(Path(data_folder, card_info_file_name), index=False)
        # card_info_frame.to_parquet(
        # Path(snapshot_folder, card_info_snap_name), index=False
        # )
        dropdown_options_frame = pd.DataFrame(self.dropdown_options)
        dropdown_options_frame = dropdown_options_frame[
            ["name", "value", "color", "_id"]
        ]
        dropdown_options_file_name = f"dropdowns_{file_name}.csv"
        dropdown_options_frame.to_parquet(
            Path(data_folder, dropdown_options_file_name),
            index=False,
        )
        # dropdown_options_frame.to_parquet(
        # Path(snapshot_folder, dropdown_options_snap_name), index=True
        # )
        list_info_frame = pd.DataFrame(self.list_counts_dict.items())
        list_info_file_name = f"{file_name}_list_info.csv"
        list_info_frame.to_parquet(Path(data_folder, list_info_file_name), index=False)
        # list_info_frame.to_parquet(
        # Path(snapshot_folder, list_info_snap_name), index=False
        # )
        labels_file_name = f"labels_{file_name}.csv"
        self.labels.to_parquet(Path(data_folder, labels_file_name), index=True)
        # self.labels.to_parquet(Path(snapshot_folder, labels_snap_name), index=True)
        lists_df_file_name = f"lists_{file_name}.csv"
        self.lists_df.to_parquet(Path(data_folder, lists_df_file_name), index=True)
        # self.lists_df.to_parquet(Path(snapshot_folder, lists_df_snap_name), index=True)
        field_type_table_file_name = f"{file_name}_fields.csv"
        self.field_type_table.to_parquet(
            Path(data_folder, field_type_table_file_name),
            index=True,
        )
        # self.field_type_table.to_parquet(
        # Path(snapshot_folder, field_type_table_snap_name), index=True
        # )

    def to_csv(self):
        """Function to write the boards card data to a CSV file."""
        data_folder = Path(".", "Data", "trello_data")
        # snapshot_folder = Path(".", "Data", "trello_data", "snapshots")

        """Create the file name for the timestamped CSV files."""
        stamp = time.localtime()
        (
            str(stamp.tm_year)
            + "_"
            + str(stamp.tm_mon)
            + "_"
            + str(stamp.tm_mday)
            + "_"
            + str(stamp.tm_hour)
            + "_"
            + str(stamp.tm_min)
        )
        temp = []
        for word in self.name.split():
            temp.append(word.casefold()[:3])
            name = "_".join(temp)
        file_name = name

        """Saving the csv files. One has a timestamp and the other is the most recent."""
        removed_columns = [
            "field_type_table",
            "lists_dict",
            "dropdown_options",
            "description",
            "old_description",
            "checklists",
            # "due",
            # "due_complete",
        ]
        base_names = {"id": "card_id", "name": "address"}
        card_info_frame = pd.DataFrame(self.cards_dict_list)
        card_info_frame.rename(columns=base_names, inplace=True)
        card_info_frame.drop(removed_columns, axis=1, inplace=True)
        card_info_file_name = f"cards_{file_name}.csv"
        # old_df = pd.read_csv(Path(data_folder, card_info_file_name))
        # old_df["src"] = "old"
        # new_df = card_info_frame.copy()
        # new_df["src"] = "new"
        # diff_df = pd.concat([old_df, new_df], ignore_index=True)
        # subset=["address","shortLink","due","due_complete","labels","attachments","card_list","project_manager","job_assigned_to","concreter","customer_name","phone","customer_email","surveyed_by:","2nd_contact","quote_value","eqc_claim_number","eqc_claim_manager","survey_completed_on","sent_to_customer_date","report_sent_to_eqc","eqc_approved_date","scheduled_date_(week_beginning)","surveyed_by","pipelining_qty","concrete_qty","exposed_ag_concrete","asphalt_qty","pipeline_patch_required","digger_type","variation_value"]
        # diff_df = diff_df.loc[diff_df.astype(str).drop_duplicates(subset=subset).index]
        # diff_df_file_name = f"diff_{file_name}.csv"
        # diff_df_snap_name = f"diff_{file_name_stamp}.csv"
        # diff_df.to_csv(Path(data_folder, diff_df_file_name), index=False)
        # diff_df.to_csv(Path(snapshot_folder, diff_df_snap_name), index=False)
        # card_info_snap_name = f"cards_{file_name_stamp}.csv"
        card_info_frame.to_csv(Path(data_folder, card_info_file_name), index=False)
        # card_info_frame.to_csv(Path(snapshot_folder, card_info_snap_name), index=False)
        dropdown_options_frame = pd.DataFrame(self.dropdown_options)
        dropdown_options_frame = dropdown_options_frame[
            ["name", "value", "color", "_id"]
        ]
        dropdown_options_file_name = f"dropdowns_{file_name}.csv"
        # dropdown_options_snap_name = f"dropdowns_{file_name_stamp}.csv"
        dropdown_options_frame.to_csv(
            Path(data_folder, dropdown_options_file_name),
            index=False,
        )
        # dropdown_options_frame.to_csv(
        #     Path(snapshot_folder, dropdown_options_snap_name), index=True
        # )
        list_info_frame = pd.DataFrame(self.list_counts_dict.items())
        list_info_file_name = f"{file_name}_list_info.csv"
        # list_info_snap_name = f"{file_name_stamp}_list_info.csv"
        list_info_frame.to_csv(Path(data_folder, list_info_file_name), index=False)
        # list_info_frame.to_csv(Path(snapshot_folder, list_info_snap_name), index=False)
        labels_file_name = f"labels_{file_name}.csv"
        # labels_snap_name = f"labels_{file_name_stamp}.csv"
        self.labels.to_csv(Path(data_folder, labels_file_name), index=True)
        # self.labels.to_csv(Path(snapshot_folder, labels_snap_name), index=True)
        lists_df_file_name = f"lists_{file_name}.csv"
        # lists_df_snap_name = f"lists_{file_name_stamp}.csv"
        self.lists_df.to_csv(Path(data_folder, lists_df_file_name), index=True)
        # self.lists_df.to_csv(Path(snapshot_folder, lists_df_snap_name), index=True)
        field_type_table_file_name = f"{file_name}_fields.csv"
        # field_type_table_snap_name = f"{file_name_stamp}_fields.csv"
        self.field_type_table.to_csv(
            Path(data_folder, field_type_table_file_name),
            index=True,
        )
        # self.field_type_table.to_csv(
        #     Path(snapshot_folder, field_type_table_snap_name), index=True
        # )


def get_custom_field_items(board_id: str):
    """Calls the custom fields API and produces a dataframe with custom field information for reference."""
    board_url_tail = f"boards/{board_id}/customFields"

    board_json = json.dumps(json.loads(Call_API(board_url_tail)))
    boards_df = pd.read_json(board_json)
    boards_df.get(["id", "name"])

    board_fields_dict = boards_df[["name", "id"]].set_index("id").to_dict()["name"]
    custom_fields_frame = pd.read_json(board_json)
    field_type_table = custom_fields_frame[["id", "name", "type"]].set_index("id")

    custom_fields_outline = board_fields_dict.keys()

    return (boards_df, field_type_table, custom_fields_outline)


def get_dropdown_options(field_type_table: pd.DataFrame) -> pd.DataFrame:
    dropdown_fields = field_type_table.loc[(field_type_table["type"] == "list")][
        ["name"]
    ]

    count = 0

    for row in dropdown_fields.iterrows():
        temp_name_list = []
        temp_value_list = []
        field_id = row[0]
        options_frame = pd.DataFrame(json.loads(get_field_values_json(field_id)))
        for i in range(options_frame.shape[0]):
            temp_name_list.append(row[1]["name"])
            temp_value_list.append(options_frame["value"][i]["text"])
        options_frame.rename(columns={"value": "old_value"}, inplace=True)
        options_frame.insert(0, "name", temp_name_list, True)
        options_frame.insert(1, "value", temp_value_list, True)
        if count == 0:
            dropdown_options = pd.DataFrame(options_frame)
            del options_frame
            count += 1
        elif count >= 0:
            dropdown_options = pd.concat(
                [options_frame, dropdown_options],
                ignore_index=True,
            )
            del options_frame

    return dropdown_options


def check_and_update_description(self, field_type_table: pd.DataFrame) -> dict:
    description_field_ids, description_info_id_dict = create_description_resources(
        field_type_table,
    )

    description_template = {
        "Customer Name": "",
        "Phone": "",
        "Customer Email": "",
        "2nd Contact": "",
        "EQC Claim Number": "",
        "EQC Claim Manager": "",
    }

    self["desc"]

    card_fields = self["customFieldItems"]
    for field in card_fields:
        if field["idCustomField"] in description_info_id_dict.keys():
            field_id = field["idCustomField"]

            try:
                field_name_temp = field_type_table.loc[
                    field_type_table.index == field_id,
                    "name",
                ].values[0]
                field_value = field["value"]["text"]
                description_template[field_name_temp] = field_value

            except:
                continue

    return description_template


def create_updated_description_format(
    current_description: str,
    description_template: dict,
) -> str:
    current_description_value = current_description

    description_template_bold = {}

    for key, value in description_template.items():
        new_key = f"**{key}**"
        description_template_bold[new_key] = value

    description = f'{current_description_value}{os.linesep}{os.linesep}{tabulate.tabulate(description_template_bold.items(), tablefmt="plain")}'

    return description


def get_board_labels(board_id: str) -> pd.DataFrame:
    """Function to get the labels for the board."""
    labels_url_tail = f"boards/{board_id}/?labels=all&labels_limit=250"
    labels_json = pd.json_normalize(json.loads(Call_API(labels_url_tail)), max_level=1)
    for item in labels_json["labels"]:
        labels_df = pd.DataFrame(item)[["id", "name", "color"]].set_index("id")
    return labels_df


def update_desc_template(self, description_template: dict) -> dict:
    if self.phone is not None:
        try:
            description_template["Phone"] = self.phone
        except:
            pass
    if self.customer_email is not None:
        try:
            description_template["Customer Email"] = self.customer_email
        except:
            pass
    if self.eqc_claim_number is not None:
        try:
            description_template["EQC Claim Number"] = self.eqc_claim_number
        except:
            pass

    return description_template


class Checklist:
    def __init__(self, card_data):
        self.checklist_values = {}
        for items in card_data["checklists"]:
            self.checklist_name = items["name"]
            try:
                for item in items["checkItems"]:
                    if self.checklist_values == {}:
                        self.checklist_values[self.checklist_name] = {
                            item["checkItems"][0]["name"]: {
                                "state": item["checkItems"][0]["state"],
                                "due": item["checkItems"][0]["due"],
                            },
                        }
                    else:
                        self.checklist_values[self.checklist_name][
                            item["checkItems"][0]["name"]
                        ] = {
                            "state": item["checkItems"][0]["state"],
                            "due": item["checkItems"][0]["due"],
                        }
            except:
                pass
        self.checklist_values

    def __repr__(self):
        return f"{self.checklist_values}"


def update_card_description(
    card_id: str, new_description: str, api_key: str, api_token: str
) -> str:
    card_url = f"https://api.trello.com/1/cards/{card_id}"

    headers = {"accept": "application:json"}

    query = {"key": api_key, "token": api_token, "desc": new_description}

    card_response = requests.request("PUT", card_url, headers=headers, params=query)

    print(
        f"{card_response.url}{os.linesep}{card_response.text}{os.linesep}{card_response.status_code}",
    )


def push_to_api(field_id: str, value: dict, card_id: str) -> str:
    """Takes a dictionary of field ids that matched the regex and updates the card custom fields via the Trello API"""
    print(value)
    value = value

    card_update_url = (
        f"https://api.trello.com/1/cards/{card_id}/customField/{field_id}/item"
    )

    headers = {"accept": "application:json"}

    query = {
        "key": trello_key,
        "token": trello_token,
    }

    card_update_response = requests.request(
        "PUT",
        card_update_url,
        json=value,
        headers=headers,
        params=query,
    )

    print(
        f"{os.linesep}{card_update_response.text}{os.linesep}{card_update_response.status_code}",
    )


def push_to_api_dropdown(field_id: str, value: dict, card_id: str) -> str:
    """Takes a dictionary of field ids that matched the regex and updates the card custom fields via the Trello API"""
    value = value

    card_update_url = (
        f"https://api.trello.com/1/cards/{card_id}/customField/{field_id}/options"
    )

    headers = {"accept": "application:json"}

    query = {
        "key": trello_key,
        "token": trello_token,
    }

    card_update_response = requests.request(
        "PUT",
        card_update_url,
        json=value,
        headers=headers,
        params=query,
    )

    print(card_update_response.url)

    print(
        f"{os.linesep}{card_update_response.text}{os.linesep}{card_update_response.status_code}",
    )


class Card:
    """An object that represents cards on a board"""

    field_type_table: pd.DataFrame
    lists_dict: dict
    dropdown_options: pd.DataFrame
    name: str
    id: str
    shortLink: str
    due: datetime
    due_complete: bool
    last_update: datetime
    labels: list
    attachments: list
    card_list: str
    checklists: list[dict]
    attributes: str
    description: str

    phone = None
    customer_email = None
    eqc_claim_number = None
    temp_description_template = {}

    def __init__(self, card_data, field_type_table, lists_dict, dropdown_options):
        self.field_type_table = field_type_table
        self.lists_dict = lists_dict
        self.dropdown_options = dropdown_options

        self.name = card_data["name"]
        self.id = card_data["id"]
        self.shortLink = card_data["shortLink"]
        self.due = card_data["due"]
        self.due_complete = card_data["dueComplete"]
        self.last_update = card_data["dateLastActivity"]

        self.labels = [
            (label["name"], label["color"])
            for label in card_data["labels"]
            if len(card_data["labels"]) >= 1
        ]
        self.attachments = [
            (attachment["name"], attachment["url"])
            for attachment in card_data["attachments"]
            if len(card_data["attachments"]) >= 1
        ]

        self.card_list = lists_dict.get(card_data["idList"])

        if card_data["checklists"] == []:
            self.checklists = None
        else:
            self.checklists = get_card_checklists(card_data)

        self.description = None
        self.old_description = None
        if card_data["desc"] != "":
            self.old_description = card_data["desc"]

        card_fields = get_card_custom_fields(
            card_data,
            field_type_table,
            dropdown_options,
        )
        for field in card_fields:
            field_name_temp = field_type_table.loc[
                field_type_table.index == field,
                "name",
            ].values[0]
            field_value = card_fields[field]
            field_name = field_name_temp.casefold().replace(" ", "_")
            self.__setattr__(field_name, field_value)

    def get_field_value(self, field_name: str) -> dict:
        selected_field = {}
        field_name_lower = field_name.casefold().replace(" ", "_")
        selected_field[field_name] = self.__dict__[field_name_lower]
        return selected_field[field_name]

    def update_numerical_field(self, selected_field: dict) -> dict:
        numerical_field_update_dict = {}
        try:
            for key, value in selected_field:
                field_id = self.field_type_table.loc[
                    self.field_type_table["name"].str.contains(key, case=False)
                ].index[0]
                field_name = self.field_type_table.loc[
                    self.field_type_table["name"].str.contains("pho", case=False)
                ].values[0][0]
                field_type = self.field_type_table.loc[
                    self.field_type_table["name"] == field_name,
                    "type",
                ].values[0]
                if field_type == "number":
                    numerical_field_update_dict[field_id] = {
                        value: {"number": self.get_field_value(field_name)},
                    }
        except:
            print(f"Field {field_name} not found")

    def update_text_field(self, field_name: str) -> dict:
        """Searches for the field_id to confirm that it is a text field, builds a dictionary and then updates the field value via the API"""
        text_field_update_dict = {}
        try:
            field_id = self.field_type_table.loc[
                self.field_type_table["name"] == field_name
            ].index[0]
            if (
                self.field_type_table.loc[
                    self.field_type_table.index == field_id,
                    "type",
                ][0]
                == "text"
            ):
                text_field_update_dict[field_id] = self.__dict__[field_name]
                return text_field_update_dict
        except:
            pass

    def update_dropdown_field(self, field_name: str) -> dict:
        try:
            self.field_type_table.loc[
                self.field_type_table["name"] == field_name
            ].index[0]
        except:
            pass

    def update_date_field(self, field_name: str) -> dict:
        date_field_update_dict = {}
        try:
            field_id = self.field_type_table.loc[
                self.field_type_table["name"] == field_name
            ].index[0]
            if (
                self.field_type_table.loc[
                    self.field_type_table.index == field_id,
                    "type",
                ][0]
                == "text"
            ):
                date_field_update_dict[field_id]
        except:
            pass

    def update_checkbox_field(self, field_name: str) -> dict:
        try:
            pass
        except:
            pass

    def __repr__(self):
        parts = []
        odd_parts = ["checklists"]
        excluded_parts = ["old_description"]
        for attr, val in self.__dict__.items():
            if attr not in odd_parts and attr not in excluded_parts:
                parts.append(f"{attr}:  {val}")
        try:
            return "\n".join(parts) + "\n" + Checklist(repr(self.checklists) + "\n")
        except:
            return "\n".join(parts)

    # def update_stuff(self, field_type_table : pd.DataFrame, lists_dict : dict, dropdown_options : dict):
    #     '''This is the code used for the original API push. This is not used currently but needs to be cleaned up.!!!! MJ'''

    #     updated_fields_dict = {}

    #     '''If card has a description field and the card customer email attribute is None, then update the card customer email attribute'''
    #     if self.old_description != None and self.customer_email == None:
    #         email_re = r'(^\w*|\w*)([@]\w*[.])(\w*[.]\w*|\w*)'
    #         try:
    #             email_match = re.search(email_re, self.old_description)
    #             self.customer_email = email_match.group(0)
    #             field_id = field_type_table.loc[field_type_table['name'] == 'Customer Email'].index[0]
    #             updated_fields_dict[field_id] = { 'value' : { 'text' : self.customer_email }}
    #         except:
    #             pass

    #     '''If card has a description field and the card phone attribute is None, then update the card phone attribute'''
    #     if self.old_description != None and self.phone == None:
    #         customer_numbers_list = []
    #         for phone_number in phonenumbermatcher.PhoneNumberMatcher(self.old_description, 'NZ'):
    #             customer_numbers_list.append(phonenumbers.format_number(phone_number.number, phonenumbers.PhoneNumberFormat.NATIONAL))
    #         if customer_numbers_list != []:
    #             self.phone = customer_numbers_list[0]
    #             field_id = field_type_table.loc[field_type_table['name'] == 'Phone'].index[0]
    #             updated_fields_dict[field_id] = { 'value' : { 'text' : self.phone }}

    #     '''If card has a description field and the card EQC claim number attribute is None, then update the card EQC claim number attribute'''
    #     if self.old_description != None and self.eqc_claim_number == None:
    #         eqc_claim_number_re = r'\bCLM[/][0-9]{4}[/][0-9]*\b'
    #         try:
    #             eqc_number_match = re.search(eqc_claim_number_re, self.old_description)
    #             self.eqc_claim_number = eqc_number_match.group(0)
    #             field_id = field_type_table.loc[field_type_table['name'] == 'EQC Claim Number'].index[0]
    #             updated_fields_dict[field_id] = { 'value' : { 'text' : self.eqc_claim_number }}
    #         except:
    #             pass

    #     for field, value in updated_fields_dict.items():
    #         push_to_api(field, value, self.id)

    #     if self.old_description is not None:
    #         try:
    #             if re.search(config.desc_table_rexp, self.old_description) is None:
    #                 temp_description_template = check_and_update_description(card_data, field_type_table)
    #                 updated_desc_template = update_desc_template(self, temp_description_template)
    #                 self.description = create_updated_description_format(self.old_description, updated_desc_template)
    #                 update_card_description(card_data['id'], self.description)
    #             else:
    #                 if re.search(config.desc_table_rexp, self.old_description) is not None:
    #                     self.description = self.old_description
    #         except:
    #             pass

    #     else:
    #         self.old_description = ''
    #         temp_description_template = check_and_update_description(card_data, field_type_table)
    #         updated_desc_template = update_desc_template(self, temp_description_template)
    #         self.description = create_updated_description_format(self.old_description, updated_desc_template)
    #         update_card_description(card_data['id'], self.description)


class BoardList:
    """An object that represents the lists on a board."""

    def __init__(self, data):
        self.name = data[1]
        self.id = data[0]


if __name__ == "__main__":
    select_board()


# %%
