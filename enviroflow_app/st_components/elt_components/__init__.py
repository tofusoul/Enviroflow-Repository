from .labour import add_labour_hours_to_jobs, build_labour_hours_from_float_data
from .projects import build_projects
from .trello import load_trello_data_to_md

if __name__ == "__main__":
    print(help(load_trello_data_to_md))
    print(help(build_projects))
    print(help(build_labour_hours_from_float_data))
    print(help(add_labour_hours_to_jobs))
