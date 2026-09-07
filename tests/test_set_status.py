import json
import os

from conftest import run_script


def _status(proj):
    with open(os.path.join(proj, "project.json"), encoding="utf-8") as f:
        return json.load(f)["status"]


def test_set_status_basic(built_project):
    assert _status(built_project) == "split"
    rc, out, err = run_script("set_status.py", "--project", built_project, "--status", "analyzed")
    assert rc == 0, f"{out}\n{err}"
    assert _status(built_project) == "analyzed"


def test_set_status_rejects_unknown(built_project):
    rc, out, err = run_script("set_status.py", "--project", built_project, "--status", "bogus")
    assert rc == 1


def test_set_status_missing_project(tmp_path):
    rc, out, err = run_script("set_status.py", "--project", str(tmp_path / "nope"), "--status", "planned")
    assert rc == 1
