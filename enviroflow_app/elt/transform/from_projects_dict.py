from collections.abc import Mapping
from dataclasses import dataclass
from functools import cached_property

import polars as pl
from loguru import logger

from enviroflow_app.model import Project, Raw_Project


@dataclass
class From_Raw_Projects_Dict:
    projects: Mapping[str, Raw_Project]

    @cached_property
    def projects_table(self) -> pl.DataFrame:
        logger.info("loading project_dicts..")
        projects_dicts = []
        for i in self.projects.values():
            logger.info(f"adding project {i.name}")
            projects_dicts.append(i.dict_for_persist)
        logger.info(f"total projects: {len(projects_dicts)}")
        logger.info("building projects table...")
        project_df = pl.from_dicts(projects_dicts, infer_schema_length=100_000)
        logger.info("projects table built")
        return project_df


@dataclass
class From_Project_Dicts:
    projects: Mapping[str, Project]

    @cached_property
    def projects_table(self) -> pl.DataFrame:
        logger.info("loading project_dicts..")
        projects_dicts = []
        for i in self.projects.values():
            logger.info(f"adding project {i.name}")
            projects_dicts.append(i.dict_for_persist)
        logger.info(f"total projects: {len(projects_dicts)}")
        logger.info("building projects table...")
        project_df = pl.from_dicts(projects_dicts, infer_schema_length=100_000)
        logger.info("projects table built")
        return project_df
