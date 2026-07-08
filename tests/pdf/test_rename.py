"""Tests for agentkit.pdf rename module."""
from __future__ import annotations

from pathlib import Path

import pytest

from agentkit.pdf.rename import make_quote_filename, rename_quote_pdf


class TestMakeQuoteFilename:
    def test_basic_filename(self):
        name = make_quote_filename("2026-07-08", "Riham", 3220)
        assert name == "2026-07-08 Riham Quote $3220.pdf"

    def test_price_as_string_with_dollar(self):
        name = make_quote_filename("2026-07-07", "Far Eastern", "$3500")
        assert name == "2026-07-07 Far Eastern Quote $3500.pdf"

    def test_price_as_string_without_dollar(self):
        name = make_quote_filename("2026-07-07", "Hyundai", "2676")
        assert name == "2026-07-07 Hyundai Quote $2676.pdf"

    def test_price_with_commas_stripped(self):
        name = make_quote_filename("2026-07-07", "Test", "$3,500")
        assert name == "2026-07-07 Test Quote $3500.pdf"

    def test_multi_word_provider(self):
        name = make_quote_filename("2026-07-07", "Far Eastern", 3500)
        assert name == "2026-07-07 Far Eastern Quote $3500.pdf"


class TestRenameQuotePDF:
    def test_renames_file_in_place(self, tmp_path):
        src = tmp_path / "original.pdf"
        src.write_text("bytes")
        result = rename_quote_pdf(src, "2026-07-08", "Riham", 3220)
        assert result == tmp_path / "2026-07-08 Riham Quote $3220.pdf"
        assert result.exists()
        assert not src.exists()

    def test_renames_to_output_dir(self, tmp_path):
        src = tmp_path / "input" / "original.pdf"
        src.parent.mkdir()
        src.write_text("bytes")
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        result = rename_quote_pdf(src, "2026-07-08", "Riham", 3220,
                                  output_dir=out_dir)
        assert result == out_dir / "2026-07-08 Riham Quote $3220.pdf"
        assert result.exists()
        assert not src.exists()

    def test_appends_counter_on_collision(self, tmp_path):
        target = tmp_path / "2026-07-08 Riham Quote $3220.pdf"
        target.write_text("existing file")
        src = tmp_path / "original.pdf"
        src.write_text("new file")
        result = rename_quote_pdf(src, "2026-07-08", "Riham", 3220)
        assert result == tmp_path / "2026-07-08 Riham Quote $3220 (2).pdf"
        assert result.exists()
        assert not src.exists()

    def test_increments_counter_on_multiple_collisions(self, tmp_path):
        (tmp_path / "2026-07-08 Riham Quote $3220.pdf").write_text("1")
        (tmp_path / "2026-07-08 Riham Quote $3220 (2).pdf").write_text("2")
        src = tmp_path / "original.pdf"
        src.write_text("3")
        result = rename_quote_pdf(src, "2026-07-08", "Riham", 3220)
        assert result == tmp_path / "2026-07-08 Riham Quote $3220 (3).pdf"
        assert result.read_text() == "3"
