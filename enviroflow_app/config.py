import sys

TR = {
    "org_name": "envirofloplan",
    "org_id": "61f726805d8aca291b8ede9f",
    "headers": {"accept": "application:json"},
    "relevant_trello_boards": {
        "Completed Jobs": "635753f48bcde802f6f7fa33",
        "Current Drainage Work": "62686d7b293b206044cc7bf3",
        "EQC Workflow": "621423ca4376a871d0f938a1",
        "Survey Workflow": "64fed7b6d9d2e1aec311844e",
        "Cancelled Jobs": "667260e54126196a6d920fbd",
        "Old Completed Jobs": "67ce4d2c26b7ff221d8f3340",
    },
}

CLI_LOG_CONF = {
    "handlers": [
        {"sink": sys.stdout},
        {"sink": "logs/cli.log", "rotation": "7 days", "retention": "30 days"},
    ],
    "extra": {"user": "andrew"},
}
FLOAT_LOG_CONF = {
    "handlers": [
        {"sink": sys.stdout},
        {"sink": "logs/ddb.log", "rotation": "7 days", "retention": "30 days"},
    ],
    "extra": {"user": "andrew"},
}

DDB_LOG_CONF = {
    "handlers": [
        {"sink": sys.stdout},
        {"sink": "logs/ddb.log", "rotation": "7 days", "retention": "30 days"},
    ],
    "extra": {"user": "andrew"},
}

TR_LOG_CONF = {
    "handlers": [
        {"sink": sys.stdout},
        {"sink": "logs/trello.log", "rotation": "7 days", "retention": "30 days"},
    ],
    "extra": {"user": "andrew"},
}


ELT_LOG_CONF = {
    "handlers": [
        {"sink": sys.stdout},
        {"sink": "logs/etl.log", "rotation": "7 days", "retention": "30 days"},
    ],
    "extra": {"user": "andrew"},
}

APP_LOG_CONF = {
    "handlers": [
        {"sink": sys.stdout, "format": "{time} | {level} | {message}"},
        {"sink": "logs/app.log", "rotation": "7 days", "retention": "30 days"},
    ],
    "extra": {"user": "andrew"},
}
