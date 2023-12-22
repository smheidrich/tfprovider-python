import subprocess as sp
from os import environ
from pathlib import Path
from textwrap import dedent

import pytest


@pytest.fixture(
    params=[
        "hello-world-provider-highlevel",
        "hello-world-provider-highlevel-async",
    ]
)
def example_dir(request) -> Path:
    return Path("examples") / request.param


@pytest.fixture()
def tf_cli_config(tmp_path: Path) -> Path:
    config_path = tmp_path / ".terraformrc"
    config_contents = dedent(
        f"""\
    provider_installation {{
      dev_overrides {{
        "local/hello-world-provider-highlevel-async" = "{Path('examples/hello-world-provider-highlevel-async').absolute()}/terraform-plugin"
        "local/hello-world-provider-highlevel" = "{Path('examples/hello-world-provider-highlevel').absolute()}/terraform-plugin"
        "local/hello-world-provider-lowlevel" = "{Path('examples/hello-world-provider-lowlevel').absolute()}/terraform-plugin"
      }}
    }}
    """.rstrip()
    )
    config_path.write_text(config_contents)
    return config_path


@pytest.fixture()
def tf_cli_env(tf_cli_config: Path) -> dict[str, str]:
    return {"TF_CLI_CONFIG_FILE": str(tf_cli_config)}


def test_plan(example_dir: Path, tf_cli_env: dict[str, str]) -> None:
    tf_project_dir = example_dir / "terraform-project-using-provider"
    env = environ.copy()
    env.update(tf_cli_env)
    sp.run(["terraform", "plan"], cwd=tf_project_dir, check=True, env=env)


def test_destroy_apply(example_dir: Path, tf_cli_env: dict[str, str]) -> None:
    tf_project_dir = example_dir / "terraform-project-using-provider"
    env = environ.copy()
    env.update(tf_cli_env)
    # destroy (idempotent)
    sp.run(
        ["terraform", "destroy", "-auto-approve"],
        cwd=tf_project_dir,
        check=True,
        env=env,
    )
    # apply
    sp.run(
        ["terraform", "apply", "-auto-approve"], cwd=tf_project_dir,
        check=True, env=env,
    )
