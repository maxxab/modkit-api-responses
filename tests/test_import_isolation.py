import os
import subprocess
import sys
from pathlib import Path


def test_core_does_not_import_optional_or_sibling_packages():
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).parents[1] / "src"))
    script = "import sys; import modkit_api_responses; assert not any(n.split('.')[0] in ('fastapi','pydantic','starlette','operations_erp','modkit_events','modkit_diagnostics','modkit_api_versioning') for n in sys.modules)"
    subprocess.run([sys.executable, "-c", script], check=True, env=env)
