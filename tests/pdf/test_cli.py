"""Tests for agentkit.pdf CLI — mock subprocess, verify JSON output."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from agentkit.pdf.cli import main


class TestRenameCLI:
    def test_rename_prints_json(self, tmp_path, capsys):
        src = tmp_path / "original.pdf"
        src.write_text("bytes")
        rc = main([
            "rename", str(src),
            "--date", "2026-07-08",
            "--provider", "Riham",
            "--price", "3220",
        ])
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert "2026-07-08 Riham Quote $3220.pdf" in out["renamed_to"]
        assert not src.exists()

    def test_rename_to_output_dir(self, tmp_path, capsys):
        src = tmp_path / "original.pdf"
        src.write_text("bytes")
        out_dir = tmp_path / "renamed"
        out_dir.mkdir()
        rc = main([
            "rename", str(src),
            "--date", "2026-07-07",
            "--provider", "Far Eastern",
            "--price", "$3500",
            "--output-dir", str(out_dir),
        ])
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert str(out_dir) in out["renamed_to"]
        assert (out_dir / "2026-07-07 Far Eastern Quote $3500.pdf").exists()


class TestConvertCLI:
    def test_convert_success_prints_json(self, tmp_path, capsys):
        input_pdf = tmp_path / "input.pdf"
        input_pdf.write_text("fake pdf bytes")
        output_md = tmp_path / "output.md"

        def fake_run(cmd, **kwargs):
            output_md.write_text("Extracted text from PDF\n" * 100)
            return MagicMock(returncode=0, stderr="", stdout="")

        with patch("subprocess.run", side_effect=fake_run):
            rc = main(["convert", str(input_pdf), "-o", str(output_md)])

        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert out["status"] == "ok"
        assert out["chars"] > 0
        assert out["input"] == str(input_pdf)
        assert out["output"] == str(output_md)

    def test_convert_empty_output_warns(self, tmp_path, capsys):
        input_pdf = tmp_path / "input.pdf"
        input_pdf.write_text("fake pdf bytes")
        output_md = tmp_path / "output.md"

        def fake_run(cmd, **kwargs):
            output_md.write_text("")
            return MagicMock(returncode=0, stderr="", stdout="")

        with patch("subprocess.run", side_effect=fake_run):
            rc = main(["convert", str(input_pdf), "-o", str(output_md)])

        assert rc == 2
        out = json.loads(capsys.readouterr().out)
        assert out["status"] == "empty"
        assert "image-only" in out["warning"]

    def test_convert_missing_input_errors(self, tmp_path, capsys):
        rc = main(["convert", str(tmp_path / "nonexistent.pdf"),
                   "-o", str(tmp_path / "out.md")])
        assert rc == 1
        err = capsys.readouterr().err
        assert "not found" in err.lower()

    def test_convert_markitdown_failure_errors(self, tmp_path, capsys):
        input_pdf = tmp_path / "input.pdf"
        input_pdf.write_text("fake pdf bytes")
        output_md = tmp_path / "output.md"

        with patch("subprocess.run",
                   return_value=MagicMock(returncode=1, stderr="markitdown error", stdout="")):
            rc = main(["convert", str(input_pdf), "-o", str(output_md)])
        assert rc == 1
        err = capsys.readouterr().err
        assert "markitdown error" in err

    def test_convert_markitdown_not_on_path(self, tmp_path, capsys):
        input_pdf = tmp_path / "input.pdf"
        input_pdf.write_text("fake pdf bytes")
        output_md = tmp_path / "output.md"

        with patch("shutil.which", return_value=None):
            rc = main(["convert", str(input_pdf), "-o", str(output_md)])
        assert rc == 1
        err = capsys.readouterr().err
        assert "not found on PATH" in err

    def test_convert_short_output_warns(self, tmp_path, capsys):
        input_pdf = tmp_path / "input.pdf"
        input_pdf.write_text("fake pdf bytes")
        output_md = tmp_path / "output.md"

        def fake_run(cmd, **kwargs):
            output_md.write_text("hi")
            return MagicMock(returncode=0, stderr="", stdout="")

        with patch("subprocess.run", side_effect=fake_run):
            rc = main(["convert", str(input_pdf), "-o", str(output_md)])

        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert "incomplete" in out["warning"].lower()
