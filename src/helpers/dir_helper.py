from os import path

#####################
#    DIRECTORIES    #
#####################


class DirectoryHelper:
    """A class for handling directory operations for the chatbot project."""

    PROJECT_DIR = path.dirname(path.abspath(__file__ + "/../"))
    # Storage directory paths
    STORAGE_DIR = PROJECT_DIR + "/storage"
    LOGS_DIR = STORAGE_DIR + "/logs"

    def __init__(self):
        pass












