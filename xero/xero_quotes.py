from datetime import datetime
import re
import json
import pandas as pd


# import sqlalchemy


class Xero_Quote:
    source_dict: dict
    quote_id: str
    quote_number: str
    quote_ref: str
    quote_contact_id: str
    quote_contact_name: str
    quote_contact_email: str
    quote_status: str
    quote_created: datetime
    quote_updated: datetime
    quote_total_ex_tax: str
    quote_lines_dict: dict
    quote_lines_df: pd.DataFrame
    quote_lines_df_human: pd.DataFrame

    def __init__(self, xero_quote_dict: dict):
        self.source_dict = xero_quote_dict
        self.error_list = []
        self.quote_id = self.source_dict["QuoteID"]
        self.quote_number = self.source_dict["QuoteNumber"]
        self.quote_contact_id = self.source_dict["Contact"]["ContactID"]
        self.quote_contact_name = self.source_dict["Contact"]["Name"]
        self.quote_status = xero_quote_dict["Status"]
        self.quote_total_ex_tax = self.source_dict["SubTotal"]
        self.quote_created = datetime.strptime(
            self.source_dict["DateString"], "%Y-%m-%dT%H:%M:%S"
        )
        try:
            self.quote_ref = self.source_dict["Reference"]
        except:
            err_str = f"no reference found for quote: {self.quote_number}"
            self.quote_ref = None
            self.error_list.append(err_str)
            print(err_str)
        try:
            self.quote_contact_email = xero_quote_dict["Contact"]["EmailAddress"]
        except:
            err_str = f"no email address for quote: {self.quote_number}"
            self.error_list.append(err_str)
            print(err_str)

        def parse_xero_date_string(date_string):
            utc_string = re.findall(r"\d{13}", date_string)[0]
            time = datetime.utcfromtimestamp(int(utc_string) / 1000)
            return time

        try:
            self.quote_updated = parse_xero_date_string(
                self.source_dict["UpdatedDateUTC"]
            )
        except:
            err_str = f"failed to parse updated date for quote: {self.quote_number}"
            self.error_list.append(err_str)
            print(err_str)

        self.quote_lines_dict = self.source_dict["LineItems"]

        def decode_xero_quote_lines(self):
            # DONE extract the line percentages from the quote , pre prepared regex (\d[0-9]*[.]\d[0-9]{0,3}[%])| |(\d[0-9][%])
            i_code = []
            desc = []
            line_id = []
            qty = []
            unit_price = []
            line_total = []

            def try_decode_quote_line(item, list_to_append, key):
                try:
                    list_to_append.append(item[key])
                except:
                    list_to_append.append(None)
                    err_str = f"no {key} for line {item['LineItemID']} in quote {self.quote_number}"
                    self.error_list.append(err_str)
                    print(err_str)

            for i in self.quote_lines_dict:
                try_decode_quote_line(i, i_code, "ItemCode")
                try_decode_quote_line(i, desc, "Description")
                try_decode_quote_line(i, line_id, "LineItemID")
                try_decode_quote_line(i, qty, "Quantity")
                try_decode_quote_line(i, unit_price, "UnitAmount")
                try_decode_quote_line(i, line_total, "LineAmount")

            lines_dict = {
                "item_code": i_code,
                "item_desc": desc,
                "line_id": line_id,
                "quantity": qty,
                "unit_price": unit_price,
                "line_total": line_total,
            }
            lines_df = pd.DataFrame(lines_dict)

            line_pct = lines_df["item_desc"].str.extract(
                r"(\d[0-9]*[.]\d[0-9]{0,3}[%])|(\d[0-9][%])", expand=False
            )
            line_pct.fillna("", inplace=True)
            line_pct = (
                line_pct.iloc[:, [0, 1]]
                .agg("".join, axis=1)
                .str.rstrip("%")
                .replace("", "100")
                .astype(float)
                .div(100)
                .round(2)
            )
            lines_df.insert(0, "line_pct", line_pct)
            lines_df.insert(0, "updated", self.quote_updated)
            lines_df.insert(0, "created", self.quote_created)
            lines_df.insert(0, "quote_status", self.quote_status)
            lines_df.insert(0, "contact_id", self.quote_contact_id)
            lines_df.insert(0, "quote_id", self.quote_id)
            lines_df.insert(0, "customer", self.quote_contact_name)
            lines_df.insert(0, "quote_ref", self.quote_ref)
            lines_df.insert(0, "quote_no", self.quote_number)
            return lines_df

        self.quote_lines_df = decode_xero_quote_lines(self)
        self.quote_lines_df["created"] = self.quote_lines_df["created"].apply(
            lambda x: x.date()
        )
        self.quote_lines_df["updated"] = self.quote_lines_df["updated"].apply(
            lambda x: x.date()
        )
        self.quote_lines_df_human = self.quote_lines_df.drop(
            ["quote_id", "contact_id", "line_id"], axis=1
        )

    def __repr__(self):
        return f"""
-----------
Quote : {self.quote_number}
quote_ID = {self.quote_id}
quote_ref = {self.quote_ref}
quote_contact_ID = {self.quote_contact_id}
quote_contact_name = {self.quote_contact_name}
quote_contact_email = {self.quote_contact_email}
quote_status = {self.quote_status}
quote_created_date = {self.quote_created}
quote_last_updates = {self.quote_updated}
quote_total_ex_tax = {self.quote_total_ex_tax}
number of errors = {len(self.error_list)}
number of lines in quote = {len(self.quote_lines_df.index)}
-----------\n
                """

    def get_quote_info(self):
        return {
            "QuoteID": self.quote_id,
            "QuoteNumber": self.quote_number,
            "Reference": self.quote_ref,
            "ContactID": self.quote_contact_id,
            "ContactName": self.quote_contact_name,
            "ContactEmail": self.quote_contact_email,
            "Status": self.quote_status,
            "DateString": self.quote_created,
            "UpdatedDateUTC": self.quote_updated,
            "SubTotal": self.quote_total_ex_tax,
        }

    def print_errors(self):
        for i in self.error_list:
            print(i)


class Xero_Quotes_List:
    def __init__(self, quotes_list_json):
        self.quotes_list_json = quotes_list_json
        self.quote_index = []
        self.quotes_list = []
        self.quotes_list_human = []
        self.error_list = []
        for x in self.quotes_list_json:
            try:
                decoded_quote = Xero_Quote(x)
                self.quotes_list.append(decoded_quote)
                self
                self.error_list = self.error_list + decoded_quote.error_list
            except:
                print(f"failed to read: {x['QuoteNumber']}")
        try:
            qdf = pd.concat(
                [x.quote_lines_df for x in self.quotes_list], ignore_index=True
            )
            qdf.drop(qdf[qdf["quote_status"] == "DELETED"].index, inplace=True)
            self.quotes_df = qdf
        except:
            print("failed to concatenate quotes")
            self.quotes_df = None

        try:
            qdfh = pd.concat(
                [x.quote_lines_df_human for x in self.quotes_list], ignore_index=True
            )
            qdfh.drop(qdfh[qdfh["quote_status"] == "DELETED"].index, inplace=True)
            self.quotes_df_human = qdfh
        except:
            print("failed to concatenate quotes")
            self.quotes_df_human = None

    def __repr__(self):
        return f"""
List of Xero Quotes
-----------
{len(self.quotes_list)} quotes were parsed
{len(self.error_list)} errors were found
-----------
                """

    def print_errors(self):
        for i in self.error_list:
            print(i)


def read_single_quote_from_file(file_path: str) -> Xero_Quote:
    with open(file_path) as f:
        quote_dict = json.load(f)
    return Xero_Quote(quote_dict)


def read_quotes_list_json_from_file(file_path: str) -> dict:
    with open(file_path) as f:
        quotes_list_json = json.load(f)["Quotes"]

    return quotes_list_json


def read_quotes_list_multi_page_json(data: dict) -> tuple[int, dict]:
    """
    Reads the the json file containing the list of quotes when it is a multi-page jason query
    """
    quotes_list_json = []
    pages_read = 0
    for key in data:
        if data[key]["Quotes"] != []:
            quotes_list_json = quotes_list_json + data[key]["Quotes"]
            pages_read += 1

    return (pages_read, quotes_list_json)


def from_file_read_quotes_list_multi_page_json(file_path: str) -> tuple[int, dict]:
    """
    Reads the the json file containing the list of quotes when it is a multi-page jason query
    """
    quotes_list_json = []
    pages_read = 0
    with open(file_path) as f:
        read_json = json.load(f)
    for key in read_json:
        if read_json[key]["Quotes"] != []:
            quotes_list_json = quotes_list_json + read_json[key]["Quotes"]
            pages_read += 1

    return (pages_read, quotes_list_json)


# quote = read_single_quote("single_quote.json")
# quote.quote_lines_df

# quotes = Xero_Quotes_List(read_quotes_list_multi_page_json("xero_quotes_list.json")[1])

# quotes.quotes_df.to_parquet("./quotes_df.parquet")
# quotes.quotes_df_human.to_parquet("./quotes_df_human.parquet")
