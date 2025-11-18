import re


def to_lower_snake_case(string: str) -> str:
    return (
        string.replace(" ", "_")
        .replace("(", "_")
        .replace(")", "")
        .replace("+", "_")
        .replace("/", "-")
        .replace("__", "_")
        .casefold()
    )


def clean_field_name(string: str) -> str:
    return to_lower_snake_case(string).replace(":", "").replace("2nd", "second")


def check_sql_entity_names(entity_name: str) -> str:
    """Checks if a string value consists only of alphanumeric characters and underscores,
    if so: returns the string
    if not: raises a ValueError.
    """
    if not re.match("^[a-zA-Z_][a-zA-Z0-9_]*$", entity_name):
        raise ValueError(f"Invalid table name: {entity_name}")
    return entity_name


def clean_address_suffix(address: str) -> str:
    """Function removes street suffixes from addresses to create a cleaner looking project title"""
    street_name_to_remove = [
        " Ave",
        " Avenue",
        " Close",
        " Cres",
        " Crescent",
        " Drive",
        #  "Grove",
        " Lane",
        " Parade",
        " Pde",
        " Pl",
        " Place",
        " Rd",
        " Road",
        " Sqr",
        " Square",
        " St",
        " St.",
        " Street",
        " Tce",
        " Terrace",
        " avenue",
        " close",
        " cres",
        " lane",
        " ln",
        " place",
        " rd",
        " road",
        " sq",
        " square",
        " st",
        " street",
    ]
    x = address.split(",")[0].strip()

    for i in street_name_to_remove:
        x = x.removesuffix(i)
    return x.strip()


def clean_multi_address(address: str):
    # Use regex to clean up the address
    # Match the main number and any characters, then the street name
    match = re.match(r"(\d+)[a-zA-Z]*[\/\-]?(\d*)\s*(.*)", address)
    if match:
        if match.group(2):
            return f"{match.group(2)} {match.group(3)}"
        return f"{match.group(1)} {match.group(3)}"
    return address
