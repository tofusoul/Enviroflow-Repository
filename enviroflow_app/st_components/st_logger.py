"""provides a function to log to both streamlit's toast and loguru"""

from enum import Enum

import streamlit as st
from loguru import logger

from enviroflow_app import config

logger.configure(**config.APP_LOG_CONF)


class Log_Level(Enum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    SUCCESS = 4


def st_logger(level: Log_Level, message: str) -> None:
    """Logs a message to both streamlit's toast and loguru"""
    match level:
        case Log_Level.DEBUG:
            st.toast(f"🐞 {message}")
            logger.debug(message)
        case Log_Level.INFO:
            st.toast(f"ℹ️ {message}")
            logger.info(message)
        case Log_Level.WARNING:
            st.toast(f"⚠️ {message}")
            logger.warning(message)
        case Log_Level.ERROR:
            st.toast(f"🚨 {message}")
            logger.error(message)
        case Log_Level.SUCCESS:
            st.toast(f"✅ {message}")
            logger.success(message)
