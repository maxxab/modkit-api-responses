"""Prove installed behavior in clean venvs outside the source checkout."""

import argparse
import os
import shutil
import subprocess
import tempfile
import venv
import zipfile
from email.parser import Parser
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("wheel", type=Path)
    parser.add_argument("--core-only", action="store_true")
    args = parser.parse_args()
    wheel = args.wheel.resolve()
    root = Path(__file__).resolve().parents[1]
    with zipfile.ZipFile(wheel) as archive:
        metadata_file = next(n for n in archive.namelist() if n.endswith(".dist-info/METADATA"))
        version = Parser().parsestr(archive.read(metadata_file).decode())["Version"]
    for extras in [False] if args.core_only else [False, True]:
        with tempfile.TemporaryDirectory(prefix="modkit-wheel-") as temporary:
            temp = Path(temporary)
            environment = temp / "venv"
            venv.EnvBuilder(with_pip=True).create(environment)
            python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            env = dict(os.environ)
            env.pop("PYTHONPATH", None)
            env["PYTHONNOUSERSITE"] = "1"

            def run(*command):
                subprocess.run([str(python), *command], cwd=temp, env=env, check=True)

            target = str(wheel) + ("[fastapi,pydantic]" if extras else "")
            run(
                "-m",
                "pip",
                "install",
                "--index-url",
                "https://pypi.org/simple",
                target,
                "pytest==9.2.0",
                *(["httpx==0.28.1"] if extras else []),
            )
            (temp / "examples").mkdir()
            shutil.copy(root / "examples/sample_app.py", temp / "examples/sample_app.py")
            (temp / "tests").mkdir()
            for path in (root / "tests").glob("test_*.py"):
                if not extras and path.name == "test_adapters.py":
                    continue
                shutil.copy(path, temp / "tests" / path.name)
            run(
                "-c",
                f"import pathlib,sys,importlib.metadata as m; import modkit_api_responses as p; assert pathlib.Path(p.__file__).is_relative_to(pathlib.Path(sys.prefix)); assert m.version('modkit-api-responses') == {version!r}; assert not any(d.metadata['Name'].lower().replace('_','-') in ('modkit-events','modkit-diagnostics','modkit-api-versioning') for d in m.distributions())",
            )
            if not extras:
                run(
                    "-c",
                    "import importlib.util; assert all(importlib.util.find_spec(n) is None for n in ('fastapi','pydantic','starlette'))",
                )
            run("-m", "pip", "check")
            run("examples/sample_app.py")
            run("-m", "pytest", "-q", "tests")
    print("Clean installed-wheel behavior verified")


if __name__ == "__main__":
    main()
