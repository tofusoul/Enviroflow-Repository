from dataclasses import dataclass
from functools import cached_property
from typing import Tuple, TypeAlias

import polars as pl
from loguru import logger

from enviroflow_app import config
from enviroflow_app.elt.transform.from_jobs import From_Jobs_Df
from enviroflow_app.model import Job, Quote, Raw_Project

logger.configure(**config.ELT_LOG_CONF)


@dataclass
class From_Jobs_With_Labour:
    df: pl.DataFrame
    quotes_dict: dict[str, Quote]

    @cached_property
    def job_analytics_table(self) -> pl.DataFrame:
        job_dict = self.df.to_dicts()
        for job in job_dict:
            for k, v in job["qty_from_card"].items():
                job[k] = v
            for k, v in job["timeline"].items():
                job[k] = v
        return pl.from_dicts(job_dict, infer_schema_length=10_000)

    job_name: TypeAlias = str

    @cached_property
    def jobs_dict(self) -> dict[job_name, Job]:
        # raw_jobs_list = self.df.to_dicts()
        # for i in raw_jobs_list:
        # del i["suburb"]
        jobs = From_Jobs_Df(self.df).jobs_dict(self.quotes_dict)
        return jobs  # {i["name"]: Job(**i) for i in raw_jobs_list}

    @cached_property
    def split_shared_drains_jobs(
        self,
    ) -> Tuple[dict[job_name, Job], dict[job_name, Job]]:
        """TODO probabaly faster to do this by spliting the dataframe rather than itterating through a dict"""
        shared = {}
        standalone = {}
        for k, v in self.jobs_dict.items():
            if v.shared_drains:
                shared[k] = v
            else:
                standalone[k] = v
        return shared, standalone

    group_name: TypeAlias = str

    @cached_property
    def shared_drains_groups(self) -> dict[group_name, dict[job_name, Job]]:
        shared = self.split_shared_drains_jobs[0]
        jobs = self.jobs_dict
        checked = []
        grouped = []
        grouped_dict = {}
        for name, job in shared.items():
            if job.name not in checked:
                group = {name: job}
                checked.append(job.name)
                logger.debug(f"{job.name} added to group {len(grouped)}")
                for i in job.shared_with:
                    try:
                        group[i] = jobs[i]
                        logger.debug(f"{i} added to group {len(grouped)}")
                        checked.append(i)
                    except KeyError:
                        logger.error(f"{i} not found in jobs")
                grouped.append(group)
            else:
                logger.debug(f"{name} already added to a group")

        if len(checked) < len(shared):
            logger.warning(
                f"{len(shared) - len(grouped)} jobs not accounted for in grouped shared drain jobs",
            )

        for i in grouped:
            i = dict(sorted(i.items()))
            group_name = " ".join([f"+ {item}" for item in list(i.keys())])[2:]
            grouped_dict[group_name] = i

        for k, v in grouped_dict.items():
            for i in v:
                try:
                    grouped_dict[k].update({i: self.jobs_dict[i]})
                except KeyError:
                    logger.error(f"{i} is not a name for a job, check {k}")
                    # grouped_dict[k].update({i: "Job_not_found"})

        return grouped_dict

    @cached_property
    def projects(self) -> dict[str, Raw_Project]:
        def parse_standalone_project(project_dict: dict) -> dict[str, Raw_Project]:
            jobs = self.split_shared_drains_jobs[1]
            for name, job in jobs.items():
                project_dict[name] = Raw_Project(
                    name=name,
                    jobs=[job],
                    shared_drains=False,
                )

            return project_dict

        def parse_shared_drain_projects(project_dict: dict) -> dict[str, Raw_Project]:
            for name, group in self.shared_drains_groups.items():
                project_dict[name] = Raw_Project(
                    name=name,
                    jobs=[i for i in group.values()],
                    shared_drains=True,
                )
            return project_dict

        projects = {}
        shared_projects = parse_shared_drain_projects(projects)
        projects = parse_standalone_project(shared_projects)
        return projects
