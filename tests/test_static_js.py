"""Every app script parses. A syntax error in one of them leaves the whole app blank, and the Python tests can't see it."""

import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPTS = sorted((Path(__file__).parent.parent / "src" / "beanagileorg").glob("*/static/*.js"))


@pytest.mark.skipif(not shutil.which("node"), reason="needs node")
@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: f"{p.parent.parent.name}/{p.name}")
def test_script_parses(script):
    r = subprocess.run(["node", "--check", str(script)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
