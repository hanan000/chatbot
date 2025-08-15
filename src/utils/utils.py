"""Projects utils"""
import io
import os
from os import path
from typing import Any

from dotenv import dotenv_values, load_dotenv

from src.logger import LOG

PROJECT_DIR = path.dirname(path.abspath(__file__)).replace("/src/utils", "")
LOGS_DIR = os.path.join(PROJECT_DIR, "storage", "")


def get_project_dir() -> str:
    """Get project directory for binary file, so it can modify the file from the project directory.
       instead from binary temp directory. Like: logs file, csv file.

    Returns:
        Project Directory by using project environment execution path
    """
    return os.path.dirname(os.path.abspath(__file__)).replace("/src/utils", "")




def load_config() -> dict:
    """Loads the environment variables from the '.env' file.

    Returns:
        A dictionary containing the loaded environment variables.
    """
    # Load environment variables from the .env file
    env_file_path = os.environ.get("SECRET_NAME") or path.join(get_project_dir(), ".env")
    temp_dir = path.join(get_project_dir(), ".env")

    project_env = os.environ.get("PROJECT_ENV")
    try:
        if project_env == "prod":
            with open(temp_dir, "w") as temp_file:
                temp_file.write(io.StringIO(env_file_path).getvalue())

            env_vars = dotenv_values(dotenv_path=temp_dir)

            for key, value in env_vars.items():
                os.environ[key] = str(value)

            if path.exists(temp_dir):
                os.remove(temp_dir)
            dict_env = dict(os.environ)
            return dict_env

        elif path.exists(env_file_path):
            load_dotenv(env_file_path)

        dict_env = dict(os.environ)
        return dict_env

    except (
        FileNotFoundError,
        PermissionError,
        IsADirectoryError,
        UnicodeDecodeError,
    ) as e:
        LOG.exception(f"Error loading .env file: {e}")
    except Exception as e:
        LOG.exception(f"Unexpected error loading .env file: {e}")

    return {}


config = load_config()

def get_conf(key: str, default_value=None) -> Any:
    """Gets the value for a given key in the configuration file."""
    try:
        return config[key]
    except KeyError:
        LOG.exception(f"`{key}` env variable not found")
        return default_value