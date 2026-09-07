import json
import os
import shutil
import subprocess
import sys

import pytest

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(SKILL_DIR, "scripts")
FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
SAMPLE_NOVEL = os.path.join(FIXTURES, "sample_novel.txt")


def run_script(script_name, *args, env=None):
    """在子进程中运行脚本, 返回 (返回码, stdout, stderr)。"""
    py = sys.executable
    cmd = [py, os.path.join(SCRIPTS_DIR, script_name)] + list(args)
    base_env = os.environ.copy()
    if env:
        base_env.update(env)
    base_env.setdefault("PYTHONIOENCODING", "utf-8")
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=base_env)
    return proc.returncode, proc.stdout, proc.stderr


@pytest.fixture
def skill_dir():
    return SKILL_DIR


@pytest.fixture
def scripts_dir():
    return SCRIPTS_DIR


@pytest.fixture(scope="session")
def sample_novel():
    return SAMPLE_NOVEL


@pytest.fixture
def built_project(tmp_path):
    """创建并构建一个完整的测试项目(初始化→导入→切分)。"""
    proj = str(tmp_path / "testnovel")
    rc, out, err = run_script("init_project.py", "--name", "testnovel", "--output", proj)
    assert rc == 0, err
    rc, out, err = run_script("import_novel.py", "--input", SAMPLE_NOVEL, "--project", proj)
    assert rc == 0, err
    rc, out, err = run_script("split_chapters.py", "--project", proj)
    assert rc == 0, err
    return proj
