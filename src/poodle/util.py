import re
from pathlib import Path


def files_list_for_folder(glob: str, filters: list[str], folder: Path):
    files = [x for x in folder.rglob(glob)]

    for filter in filters:
        files = [file for file in files if not re.match(filter, file.name)]

    return files
