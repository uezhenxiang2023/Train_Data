"""Create a project when the one-shot launcher supplies a destination."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import hiero.core
from hiero.core import events


PROJECT_PATH_VARIABLE = "HIERO_PROJECT_SAVE_PATH"
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def create_requested_project(event) -> None:
    """Create and save the requested project after Hiero has started."""
    repository_root = str(REPOSITORY_ROOT)
    if repository_root not in sys.path:
        sys.path.insert(0, repository_root)

    from data_management import create_project

    project = create_project(os.environ[PROJECT_PATH_VARIABLE])
    print("Created Hiero project: {}".format(project))
    hiero.core.quit()


if os.environ.get(PROJECT_PATH_VARIABLE):
    events.registerInterest(events.EventType.kStartup, create_requested_project)
