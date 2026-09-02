import logging
from pathlib import Path

import context


def test_download_context_data_uses_safe_log_metadata(tmp_path, monkeypatch, caplog):
    def fake_download(url, output, quiet):
        Path(output).write_bytes(b"%PDF-test")
        return output

    monkeypatch.setattr(context.gdown, "download", fake_download)

    with caplog.at_level(logging.INFO):
        context.download_context_data(
            [{"url": "https://example.test/show.pdf", "filename": "show.pdf"}],
            tmp_path,
        )

    assert (tmp_path / "show.pdf").exists()
    assert any(
        getattr(record, "document_filename", None) == "show.pdf"
        for record in caplog.records
    )
