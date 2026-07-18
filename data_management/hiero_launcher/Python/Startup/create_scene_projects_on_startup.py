"""Build scene projects after Nuke Studio has completed startup."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from hiero.core import events


SCENE_DIRECTORY_VARIABLE = "HIERO_SCENE_DIRECTORY"
OUTPUT_DIRECTORY_VARIABLE = "HIERO_OUTPUT_DIRECTORY"
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def write_startup_log(message: str) -> None:
    log_path = os.environ.get("HIERO_BUILDER_LOG")
    if log_path:
        destination = Path(log_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("a", encoding="utf-8") as log_file:
            log_file.write(message + "\n")


def create_scene_projects_on_startup(event) -> None:
    write_startup_log("Hiero scene builder startup event received")
    repository_root = str(REPOSITORY_ROOT)
    if repository_root not in sys.path:
        sys.path.insert(0, repository_root)

    from data_management import create_scene_projects

    result = create_scene_projects(
        os.environ[SCENE_DIRECTORY_VARIABLE], os.environ[OUTPUT_DIRECTORY_VARIABLE]
    )
    print("DataFilter: {}".format(result["filter_file"]))
    for project_path, media_paths in result["created"]:
        print("Created: {} ({} .mov files)".format(project_path, len(media_paths)))
    for task_file, reason in result["skipped"]:
        print("Skipped: {} ({})".format(task_file, reason))
    for task_file, reason in result["failed"]:
        print("Failed: {} ({})".format(task_file, reason))


if os.environ.get(SCENE_DIRECTORY_VARIABLE) and os.environ.get(OUTPUT_DIRECTORY_VARIABLE):
    write_startup_log("Hiero scene builder plugin loaded")
    events.registerInterest(
        events.EventType.kStartup, create_scene_projects_on_startup
    )
