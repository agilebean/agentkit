"""private_term_check: a staged file that holds a listed term stops the commit, and the term is never printed."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "private_term_check.py"


def _repo(tmp_path: Path, text: str) -> Path:
    repo = tmp_path / "r"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    (repo / "a.md").write_text(text, encoding="utf-8")
    subprocess.run(["git", "add", "a.md"], cwd=repo, check=True)
    return repo


def _run(repo: Path, lst: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), str(lst)], cwd=repo, input="a.md\n",
                          capture_output=True, text=True)


def test_a_listed_term_fails_and_is_not_printed(tmp_path):
    lst = tmp_path / "list.txt"
    lst.write_text("regex:zorbl(ian)?==>Kim\nliteral:Quexa==>Lee\n", encoding="utf-8")
    out = _run(_repo(tmp_path, "met a Zorblian and quexa\n"), lst)
    assert out.returncode == 1
    assert "list rule 1" in out.stderr and "list rule 2" in out.stderr
    assert "orbl" not in out.stderr.lower() and "quexa" not in out.stderr.lower()


def test_a_clean_file_passes(tmp_path):
    lst = tmp_path / "list.txt"
    lst.write_text("literal:Quexa==>Lee\n", encoding="utf-8")
    assert _run(_repo(tmp_path, "nothing here\n"), lst).returncode == 0


def test_no_list_means_no_check(tmp_path):
    assert _run(_repo(tmp_path, "Quexa\n"), tmp_path / "missing.txt").returncode == 0
