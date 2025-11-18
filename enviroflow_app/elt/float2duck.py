import asyncio
import os
from datetime import date

import httpx
import orjson as json
import polars as pl

try:
    from streamlit import secrets as st_secrets
except ImportError:
    st_secrets = None


def _get_float_auth() -> str:
    """Get Float authorization from environment or Streamlit secrets."""
    float_auth = os.getenv("FLOAT_AUTH")
    if float_auth:
        return float_auth

    if st_secrets and "float" in st_secrets and "float_auth" in st_secrets["float"]:
        return st_secrets["float"]["float_auth"]

    raise ValueError("Float authorization not found in environment or secrets")


def _get_user_agent() -> str:
    """Get User Agent from environment or Streamlit secrets."""
    user_agent = os.getenv("FLOAT_USER_AGENT")
    if user_agent:
        return user_agent

    if st_secrets and "float" in st_secrets and "user_agent" in st_secrets["float"]:
        return st_secrets["float"]["user_agent"]

    return "Enviroflo Float Integration (andrew@enviroflo.co.nz)"  # Default fallback


async def get_number_of_pages_API_tasks() -> int:
    """Makes a call to the tasks API end point and returns the header value for the total number of pages returned as an integer."""
    API_url = "https://api.float.com/v3/tasks?"

    API_headers = {
        "Accept": "application/json",
        "Authorization": _get_float_auth(),
        "User-Agent": _get_user_agent(),
    }

    API_data = {"end_date": str(date.today())}

    async with httpx.AsyncClient() as client:
        API_json = await client.get(API_url, headers=API_headers, params=API_data)
        API_json.raise_for_status()
        return int(API_json.headers["x-pagination-page-count"])


async def get_number_of_pages_API_people() -> int:
    """Makes a call to the people API end point and returns the header value for the total number of pages returned as an integer."""
    API_url = "https://api.float.com/v3/people?"

    API_headers = {
        "Accept": "application/json",
        "Authorization": _get_float_auth(),
        "User-Agent": _get_user_agent(),
    }

    API_data = {"end_date": str(date.today())}

    async with httpx.AsyncClient() as client:
        API_json = await client.get(API_url, headers=API_headers, params=API_data)
        API_json.raise_for_status()
        return int(API_json.headers["x-pagination-page-count"])


async def get_people_data_API(people_api_pages_count: int) -> dict:
    """Function to call the people API endpoint and returns a dictionary of staff members where the key is the people_id and the value is the name."""
    people_url = "https://api.float.com/v3/people"

    headers = {
        "Accept": "application/json",
        "Authorization": _get_float_auth(),
        "User-Agent": _get_user_agent(),
    }

    people_params = {}

    people_data = {}

    async with httpx.AsyncClient() as client:
        if people_api_pages_count == 1:
            api_return = await client.get(people_url, headers=headers)
            api_return.raise_for_status()
            data_block = json.loads(api_return.text)
            for person_item in data_block:
                people_data[person_item["people_id"]] = person_item["name"]

        else:
            for i in range(people_api_pages_count):
                people_params["page"] = str(i)
                api_return = await client.get(
                    people_url, headers=headers, params=people_params
                )
                api_return.raise_for_status()
                data_block = json.loads(api_return.text)
                # Retrieved people records from API page
                for person_item in data_block:
                    people_data[person_item["people_id"]] = person_item["name"]

    return people_data


async def get_project_names():
    projects_url = "https://api.float.com/v3/projects"

    headers = {
        "Accept": "application/json",
        "Authorization": _get_float_auth(),
        "User-Agent": _get_user_agent(),
    }

    projects_data = {}
    async with httpx.AsyncClient() as client:
        api_return = await client.get(projects_url, headers=headers)
        api_return.raise_for_status()
        data_block = json.loads(api_return.text)
        for project in data_block:
            projects_data[project["project_id"]] = project["name"]

        return projects_data


async def get_tasks_data_API(tasks_api_pages_count: int) -> list[dict]:
    """Function to call the people API and return a list of dictionaries. Each dictionary contains the people_id, name and email address."""
    tasks_url = "https://api.float.com/v3/tasks"

    headers = {
        "Accept": "application/json",
        "Authorization": _get_float_auth(),
        "User-Agent": _get_user_agent(),
    }

    tasks_params = {}

    tasks_data = []

    async with httpx.AsyncClient() as client:
        if tasks_api_pages_count == 1:
            api_return = await client.get(tasks_url, headers=headers)
            api_return.raise_for_status()
            data_block = json.loads(api_return.text)
            for task_item in data_block:
                member_dict = {
                    "project_id": task_item["project_id"],
                    "name": task_item["name"],
                    "start_date": task_item["start_date"],
                    "end_date": task_item["end_date"],
                    "people_id": task_item["people_id"],
                    "people_ids": task_item["people_ids"],
                    "hours": task_item["hours"],
                }
                tasks_data.append(member_dict)

        else:
            for i in range(tasks_api_pages_count):
                tasks_params["page"] = str(i)
                api_return = await client.get(
                    tasks_url, headers=headers, params=tasks_params
                )
                api_return.raise_for_status()
                data_block = json.loads(api_return.text)

                for task_item in data_block:
                    member_dict = {
                        "project_id": task_item["project_id"],
                        "name": task_item["name"],
                        "start_date": task_item["start_date"],
                        "end_date": task_item["end_date"],
                        "people_id": task_item["people_id"],
                        "people_ids": task_item["people_ids"],
                        "hours": task_item["hours"],
                    }
                    tasks_data.append(member_dict)

        return tasks_data


def get_final_table(people_dict: dict, task_list: list, project_dict: dict):
    """Takes the lists of tasks and people dictionaries and creates a dataframe. Jobs that have more than 1 person in the time entry are split
    in to seperate lines so that the total time for each job can be easily calculated.
    """
    final_column_names = {
        "people_id": "employee",
        "job_duration": "num_days",
        "hours": "daily_hours",
    }

    tasks_list_final = []

    for task in task_list:
        if task["people_ids"] is not None:
            for person_id in task["people_ids"]:
                new_dict = task.copy()
                new_dict["people_id"] = person_id
                del new_dict["people_ids"]
                new_dict["people_id"] = people_dict[person_id]
                tasks_list_final.append(new_dict)

        else:
            new_dict = task.copy()
            new_dict["people_id"] = people_dict[task["people_id"]]
            del new_dict["people_ids"]
            tasks_list_final.append(new_dict)

    for task in tasks_list_final:
        if task["name"] == "":
            task["name"] = project_dict[task["project_id"]]
            del task["project_id"]
        else:
            del task["project_id"]

    tasks_time_df = pl.from_dicts(tasks_list_final).with_columns(
        pl.col(["start_date", "end_date"]).str.strptime(pl.Date),
    )
    tasks_time_df = tasks_time_df.with_columns(
        job_duration=(
            pl.col("end_date").dt.offset_by(pl.format("{}d", 1)) - pl.col("start_date")  # type: ignore
        ).dt.total_days(),
    )
    tasks_time_df = tasks_time_df.with_columns(
        total_hours=(pl.col("job_duration")) * pl.col("hours"),
    )

    tasks_time_df_final = tasks_time_df.rename(final_column_names)

    return tasks_time_df_final


async def build_project_labour_hours_table() -> pl.DataFrame:
    get_task_page_num = asyncio.create_task(get_number_of_pages_API_tasks())
    get_project_page_num = asyncio.create_task(get_number_of_pages_API_people())
    page_nums = await asyncio.gather(*[get_task_page_num, get_project_page_num])

    people_dict = asyncio.create_task(get_people_data_API(page_nums[1]))
    task_dict = asyncio.create_task(get_tasks_data_API(page_nums[0]))
    project_dict = asyncio.create_task(get_project_names())

    args = await asyncio.gather(*[people_dict, task_dict, project_dict])
    df = get_final_table(args[0], args[1], args[2])
    return df


if __name__ == "__main__":
    df = asyncio.run(build_project_labour_hours_table())

    print(df)
