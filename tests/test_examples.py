import subprocess as sp
from pathlib import Path

import pytest


@pytest.fixture(
    params=[
        "hello-world-provider-highlevel",
        "hello-world-provider-highlevel-async",
    ]
)
def example_dir(request) -> Path:
    return Path("examples") / request.param


# TODO currently, this only works if the user has configured ~/.terraformrc
#   to point to the providers => fix


def test_plan(example_dir: Path) -> None:
    tf_project_dir = example_dir / "terraform-project-using-provider"
    sp.run(["terraform", "plan"], cwd=tf_project_dir, check=True)


def test_destroy_apply(example_dir: Path) -> None:
    tf_project_dir = example_dir / "terraform-project-using-provider"
    # destroy (idempotent)
    sp.run(
        ["terraform", "destroy", "-auto-approve"],
        cwd=tf_project_dir,
        check=True,
    )
    # apply
    sp.run(
        ["terraform", "apply", "-auto-approve"], cwd=tf_project_dir, check=True
    )
