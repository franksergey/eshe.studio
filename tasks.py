"""Файл задач для утилиты `invoke`.

Чтобы узнать, как пользоваться `invoke`, напишите:

    $ invoke --help
    # Или
    $ inv --help

Для списка команд:

    $ inv --help

https://www.pyinvoke.org/
"""
# prints are okay here # ruff: noqa: T201

import os
import shlex
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Literal, TypedDict

from invoke.context import Context
from invoke.tasks import task

if TYPE_CHECKING:
    from collections.abc import Iterable


type DockerTarget = Literal["prod", "dev", "report"]


class Target(TypedDict):
    """Цель для запуска в Docker."""

    displayed_name: str
    compose_files: Iterable[Path]
    main_service: str


DOCKER_FOLDER = Path(__file__).parent / "docker"
PROJECT_ROOT = DOCKER_FOLDER
TARGETS: dict[DockerTarget, Target] = {
    "dev": {
        "compose_files": [
            DOCKER_FOLDER / "./compose.yaml",
            DOCKER_FOLDER / "./compose.dev.yaml",
        ],
        "displayed_name": "The development container",
        "main_service": "backend",
    },
    "prod": {
        "compose_files": [
            DOCKER_FOLDER / "./compose.yaml",
            DOCKER_FOLDER / "./compose.sqlite.yaml",
            # TIP: Write an nginx configuration for your site
            # DOCKER_FOLDER / "./compose.nginx.yaml",
        ],
        "displayed_name": "The production container",
        "main_service": "backend",
    },
}
TARGET_OPT_HELP = (
    "Цель для выполнения команды. Доступные цели: "
    f"{', '.join(TARGETS.keys())}. По умолчанию 'prod'."
)


# ====================
# Docker-related tasks
# ====================


def get_docker_compose(target: Target) -> list[str]:
    compose_files = target["compose_files"]
    command = ["docker", "compose", "--project-directory", str(PROJECT_ROOT)]

    for file in compose_files:
        command.append("-f")
        command.append(str(file))

    return command


def get_target(target: DockerTarget) -> Target:
    try:
        return TARGETS[target]
    except KeyError as e:
        msg = f"There's no such target {target!r}"
        raise ValueError(msg) from e


def start_message(message: str, target: Target) -> None:
    print(message % target["displayed_name"].lower(), end="\n\n")


@task(
    help={
        "target": TARGET_OPT_HELP,
        "port": "Порт, если цель – это сервер. По умолчанию 8000.",
        "build": "Собирать цель или нет? По умолчанию да.",
        "start": "Запустить контейнер или нет? По умолчанию да.",
    }
)
def up(  # noqa: PLR0913
    ctx: Context,
    target: DockerTarget = "prod",
    port: int = 8000,
    version: Literal["1"] = "1",
    *,
    build: bool = True,
    start: bool = True,
) -> None:
    """Docker: Собирает, создаёт и запускает контейнер."""
    os.environ["APP_PORT"] = str(port)
    os.environ["FEST_SITE_VERSION"] = version

    try:
        target_obj = get_target(target)
    except ValueError as e:
        print(e)
        return

    start_message("Bringing up %s", target_obj)

    docker_compose = get_docker_compose(target_obj)
    args = ["--detach", "--build" if build else "--no-build"]

    if not start:
        args.append("--no-start")

    subprocess.run([*docker_compose, "up", *args], check=False)  # noqa: S603


@task(
    help={
        "target": TARGET_OPT_HELP,
        "push": "Пушить образы или нет? По умолчанию нет.",
    }
)
def build(
    ctx: Context, target: DockerTarget = "prod", *, push: bool = False
) -> None:
    """Docker: Собирает контейнер."""
    try:
        target_obj = get_target(target)
    except ValueError as e:
        print(e)
        return

    start_message("Building the images of %s", target_obj)

    docker_compose = get_docker_compose(target_obj)
    args = ("--push",) if push else ()

    subprocess.run([*docker_compose, "build", *args], check=False)  # noqa: S603


@task(help={"target": TARGET_OPT_HELP})
def start(ctx: Context, target: DockerTarget = "prod") -> None:
    """Docker: Запускает контейнер."""
    try:
        target_obj = get_target(target)
    except ValueError as e:
        print(e)
        return

    start_message("Starting %s", target_obj)

    docker_compose = get_docker_compose(target_obj)
    subprocess.run([*docker_compose, "start"], check=False)  # noqa: S603


@task()
def start_debug(ctx: Context) -> None:
    """Docker: Запускает дебаггинг в dev контейнере."""
    target_obj = get_target("dev")

    start_message("Starting debugging session for %s", target_obj)

    docker_compose = get_docker_compose(target_obj)
    subprocess.run([*docker_compose, "up", "-d", "--no-recreate"], check=False)  # noqa: S603

    service = target_obj["main_service"]
    command = ["bash", "./src/scripts/start-debug.sh"]
    subprocess.run([*docker_compose, "exec", service, *command], check=False)  # noqa: S603


@task()
def stop_debug(ctx: Context) -> None:
    """Docker: Завершает дебаггинг в dev контейнере."""
    target_obj = get_target("dev")

    start_message("Stopping debugging session for %s", target_obj)

    docker_compose = get_docker_compose(target_obj)

    service = target_obj["main_service"]
    command = ["pkill", "-INT", "-u", "appuser", "-f", "python.*app"]
    subprocess.run([*docker_compose, "exec", service, *command], check=False)  # noqa: S603


@task(
    help={
        "target": TARGET_OPT_HELP,
        "command": "Команда, которую нужно запустить.",
        "build": "Собирать цель или нет? По умолчанию да.",
    }
)
def run(
    ctx: Context,
    command: str,
    target: DockerTarget = "prod",
    *,
    build: bool = True,
) -> None:
    """Docker: Запускает команду для выбранного контейнера."""
    try:
        target_obj = get_target(target)
    except ValueError as e:
        print(e)
        return

    start_message("Running command for %s", target_obj)

    docker_compose = get_docker_compose(target_obj)
    args = ["--rm", target_obj["main_service"], *shlex.split(command)]

    if build:
        args.insert(0, "--build")

    run_command = [*docker_compose, "run", *args]
    subprocess.run(run_command, check=False)  # noqa: S603


@task(help={"target": TARGET_OPT_HELP})
def stop(ctx: Context, target: DockerTarget = "prod") -> None:
    """Docker: Останавливает контейнер."""
    try:
        target_obj = get_target(target)
    except ValueError as e:
        print(e)
        return

    start_message("Stopping %s", target_obj)

    docker_compose = get_docker_compose(target_obj)
    subprocess.run([*docker_compose, "stop"], check=False)  # noqa: S603


@task(help={"target": TARGET_OPT_HELP})
def down(ctx: Context, target: DockerTarget = "prod") -> None:
    """Docker: Удаляет контейнер."""
    try:
        target_obj = get_target(target)
    except ValueError as e:
        print(e)
        return

    start_message("Bringing down %s", target_obj)

    docker_compose = get_docker_compose(target_obj)
    subprocess.run([*docker_compose, "down", "--remove-orphans"], check=False)  # noqa: S603


@task(
    help={
        "target": TARGET_OPT_HELP,
        "since": "С какого момента логи? "
        "Например, 2013-01-02T13:23:37Z или 42m (42 минуты назад).",
        "tail": "Сколько строчек показать (с конца логов)? По умолчанию все.",
    }
)
def logs(
    ctx: Context,
    target: DockerTarget = "prod",
    since: str | None = None,
    tail: int = -1,
) -> None:
    """Docker: Показывает логи контейнера."""
    try:
        target_obj = get_target(target)
    except ValueError as e:
        print(e)
        return

    start_message("Showing logs of %s", target_obj)

    docker_compose = get_docker_compose(target_obj)
    args = ["--follow", "--tail=all" if tail == -1 else f"--tail={tail}"]

    if since is not None:
        args.extend(["--since", since])

    subprocess.run([*docker_compose, "logs", *args], check=False)  # noqa: S603


def _get_uid_gid_pair(ctx: Context) -> tuple[int, int]:
    uid = ctx.run("id -u", hide=True)
    gid = ctx.run("id -g", hide=True)

    if uid is None or gid is None:
        raise ValueError

    return int(uid.stdout), int(gid.stdout)


@task
def export(ctx: Context) -> None:
    """Docker: Запустить скрипт экспорта email адресов."""
    target_obj = get_target("prod")

    start_message("Starting debugging session for %s", target_obj)

    uid, gid = _get_uid_gid_pair(ctx)
    ctx.run("touch ./emails.txt")
    docker_compose = get_docker_compose(target_obj)
    args = [
        "--rm",
        "--build",
        "-v=./emails.txt:/data/export.txt",
        f"--user={uid}:{gid}",
        target_obj["main_service"],
        "export-emails",
    ]

    run_command = [*docker_compose, "run", *args]
    subprocess.run(run_command, check=False)  # noqa: S603


@task
def report(ctx: Context) -> None:
    """Docker: Запустить скрипт отчёта почт."""
    target_obj = get_target("report")
    start_message("Starting debugging session for %s", target_obj)

    docker_compose = get_docker_compose(target_obj)
    args = ["--rm", target_obj["main_service"], "report-emails"]

    run_command = [*docker_compose, "run", *args]
    subprocess.run(run_command, check=False)  # noqa: S603
