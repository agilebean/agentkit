"""Tests for agentkit.evernote — mock Thrift layer, test client and CLI."""
from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from agentkit.evernote import EvernoteClient, EvernoteError, EvernoteAuthError
from agentkit.evernote._client import _wrap_enml, _strip_enml
from agentkit.evernote._cli import main


FAKE_COOKIE = "S=s101:U=abc:E=def:C=ghi:P=123:A=en-chrome-clipper-xauth-new:V=2:H=xyz"
FAKE_NOTE_STORE_URL = "https://www.evernote.com/edam/note/s101/shared/abc123"
FAKE_USER_URLS = MagicMock(noteStoreUrl=FAKE_NOTE_STORE_URL)


def _make_fake_note(guid="note1", title="Test Note", content_html="<en-note><div>hello</div></en-note>"):
    note = MagicMock()
    note.guid = guid
    note.title = title
    note.content = content_html
    note.notebookGuid = "nb1"
    note.tagGuids = ["tag1"]
    note.created = 1700000000000
    note.updated = 1700000001000
    return note


def _make_fake_notebook(guid="nb1", name="My Notebook"):
    nb = MagicMock()
    nb.guid = guid
    nb.name = name
    return nb


def _make_tag_mock(guid, name):
    tag = MagicMock()
    tag.guid = guid
    tag.name = name
    return tag


def _make_fake_notes_metadata_result(notes):
    result = MagicMock()
    result.notes = notes
    return result


def _patch_client_instance(client):
    """Monkey-patch an EvernoteClient instance so all Thrift calls are mocked.

    Patches _make_transport, _user_store_client, and _note_store_client
    directly on the instance. Returns the mock NoteStore client.
    """
    mock_transport = MagicMock()
    mock_us = MagicMock()
    mock_us.getUserUrls.return_value = FAKE_USER_URLS
    mock_ns = MagicMock()

    client._make_transport = MagicMock(return_value=mock_transport)
    client._user_store_client = MagicMock(return_value=mock_us)
    client._note_store_client = MagicMock(return_value=mock_ns)

    client._mock_ns = mock_ns
    client._mock_us = mock_us
    client._mock_transport = mock_transport
    return mock_ns


# Client tests


class TestEvernoteClientAuth:
    def test_raises_auth_error_when_no_cookie(self, monkeypatch):
        monkeypatch.delenv("EVERNOTE_CLIPPER_SSO", raising=False)
        with pytest.raises(EvernoteAuthError):
            EvernoteClient(cookie=None, cookie_env_var="FAKE_NONEXISTENT")

    def test_accepts_explicit_cookie(self):
        client = EvernoteClient(cookie=FAKE_COOKIE)
        _patch_client_instance(client)
        assert client._cookie == FAKE_COOKIE

    def test_reads_cookie_from_env(self, monkeypatch):
        monkeypatch.setenv("TEST_EVERNOTE_COOKIE", FAKE_COOKIE)
        client = EvernoteClient(cookie_env_var="TEST_EVERNOTE_COOKIE")
        _patch_client_instance(client)
        assert client._cookie == FAKE_COOKIE

    def test_make_transport_sets_cookie_header(self):
        client = EvernoteClient(cookie=FAKE_COOKIE)
        # Don't patch _make_transport — use the real method
        transport = MagicMock()
        with patch("agentkit.evernote._client.THttpClient.THttpClient", return_value=transport):
            client._make_transport("https://example.com/path")
        transport.setCustomHeaders.assert_called_once_with(
            {"Cookie": f"clipper-sso={FAKE_COOKIE};"}
        )


class TestEvernoteClientOperations:
    @pytest.fixture
    def client(self):
        c = EvernoteClient(cookie=FAKE_COOKIE)
        _patch_client_instance(c)
        return c

    def test_list_notebooks(self, client):
        nb1 = _make_fake_notebook("nb1", "Home")
        nb2 = _make_fake_notebook("nb2", "Work")
        client._mock_ns.listNotebooks.return_value = [nb1, nb2]

        result = client.list_notebooks()
        assert result == [
            {"guid": "nb1", "name": "Home"},
            {"guid": "nb2", "name": "Work"},
        ]
        client._mock_ns.listNotebooks.assert_called_once_with(FAKE_COOKIE)

    def test_list_tags(self, client):
        tag1 = _make_tag_mock("t1", "tag-one")
        tag2 = _make_tag_mock("t2", "tag-two")
        client._mock_ns.listTags.return_value = [tag1, tag2]

        result = client.list_tags()
        assert result == [
            {"guid": "t1", "name": "tag-one"},
            {"guid": "t2", "name": "tag-two"},
        ]

    def test_find_notes(self, client):
        note_meta = MagicMock()
        note_meta.guid = "n1"
        note_meta.title = "Hello"
        note_meta.contentLength = 100
        note_meta.created = 1700000000000
        note_meta.updated = 1700000001000
        note_meta.notebookGuid = "nb1"

        result_mock = _make_fake_notes_metadata_result([note_meta])
        client._mock_ns.findNotesMetadata.return_value = result_mock

        result = client.find_notes(query="Hello")
        assert len(result) == 1
        assert result[0]["guid"] == "n1"
        assert result[0]["title"] == "Hello"

    def test_find_notes_empty(self, client):
        result_mock = _make_fake_notes_metadata_result([])
        client._mock_ns.findNotesMetadata.return_value = result_mock

        result = client.find_notes()
        assert result == []

    def test_get_note(self, client):
        note = _make_fake_note()
        client._mock_ns.getNote.return_value = note

        result = client.get_note("note1")
        assert result["guid"] == "note1"
        assert result["title"] == "Test Note"
        assert result["content"] == "hello"
        assert result["notebookGuid"] == "nb1"

    def test_get_note_raw_content(self, client):
        note = _make_fake_note(content_html="<en-note><div>raw</div></en-note>")
        client._mock_ns.getNote.return_value = note

        result = client.get_note("note1", raw_content=True)
        assert "raw" in result["content"]
        assert "<en-note>" in result["content"]

    def test_create_note(self, client):
        note = _make_fake_note(guid="new1", title="Fresh")
        client._mock_ns.createNote.return_value = note

        result = client.create_note(title="Fresh", content="my content")
        assert result["guid"] == "new1"
        assert result["title"] == "Fresh"
        client._mock_ns.createNote.assert_called_once()

    def test_update_note(self, client):
        original = _make_fake_note(guid="n1", title="Old")
        updated = _make_fake_note(guid="n1", title="New")
        client._mock_ns.getNote.return_value = original
        client._mock_ns.updateNote.return_value = updated

        result = client.update_note("n1", title="New")
        assert result["guid"] == "n1"
        assert result["title"] == "New"
        client._mock_ns.updateNote.assert_called_once()

    def test_update_note_partial(self, client):
        """Only specified fields should change. Unspecified fields stay as-is."""
        original = _make_fake_note(guid="n1", title="Old Title")
        updated = _make_fake_note(guid="n1", title="Old Title")
        updated.content = "<en-note><div>new body</div></en-note>"
        client._mock_ns.getNote.return_value = original
        client._mock_ns.updateNote.return_value = updated

        result = client.update_note("n1", content="new body")
        assert result["content"] == "new body"
        assert result["title"] == "Old Title"

    def test_get_notebook_guid_by_name_found(self, client):
        nb1 = _make_fake_notebook("nb1", "Home")
        nb2 = _make_fake_notebook("nb2", "Work")
        client._mock_ns.listNotebooks.return_value = [nb1, nb2]

        assert client.get_notebook_guid_by_name("Work") == "nb2"

    def test_get_notebook_guid_by_name_not_found(self, client):
        client._mock_ns.listNotebooks.return_value = []

        assert client.get_notebook_guid_by_name("Nope") is None

    def test_operations_wrapped_in_evernote_error(self, client):
        client._mock_ns.listNotebooks.side_effect = RuntimeError("boom")
        with pytest.raises(EvernoteError, match="listNotebooks failed"):
            client.list_notebooks()

    def test_auth_error_on_get_user_urls_failure(self):
        client = EvernoteClient(cookie=FAKE_COOKIE)
        mock_transport = MagicMock()
        mock_us = MagicMock()
        mock_us.getUserUrls.side_effect = Exception("bad cookie")
        client._make_transport = MagicMock(return_value=mock_transport)
        client._user_store_client = MagicMock(return_value=mock_us)
        # Don't patch _note_store_client so it calls _resolve_note_store_url
        with pytest.raises(EvernoteAuthError, match="cookie invalid"):
            client._note_store_client()


class TestWrapEnml:
    def test_plaintext_wraps_in_enml(self):
        result = _wrap_enml("hello")
        assert "<en-note" in result
        assert "hello" in result
        assert "<?xml" in result

    def test_preserves_existing_enml(self):
        existing = '<en-note><div>hi</div></en-note>'
        assert _wrap_enml(existing) == existing

    def test_preserves_xml_declaration(self):
        existing = '<?xml version="1.0"?>\n<en-note>x</en-note>'
        assert _wrap_enml(existing) == existing

    def test_escapes_html_entities(self):
        result = _wrap_enml("x < y & z > w")
        assert "&lt;" in result
        assert "&gt;" in result
        assert "&amp;" in result

    def test_multiline_paragraphs(self):
        result = _wrap_enml("line one\n\nline two")
        assert "<div>line one</div>" in result
        assert "<div>line two</div>" in result


class TestStripEnml:
    def test_strips_enml_tags(self):
        enml = '<en-note><div>Hello World</div></en-note>'
        assert _strip_enml(enml) == "Hello World"

    def test_strips_style_tags(self):
        enml = '<en-note><style>css</style><div>text</div></en-note>'
        assert _strip_enml(enml) == "text"

    def test_converts_br_to_newline(self):
        enml = '<en-note><div>line1<br>line2</div></en-note>'
        result = _strip_enml(enml)
        assert "line1" in result
        assert "line2" in result

    def test_decodes_html_entities(self):
        enml = '<en-note><div>x &amp; y &lt; z</div></en-note>'
        result = _strip_enml(enml)
        assert "x & y < z" in result

    def test_handles_empty_content(self):
        assert _strip_enml("") == ""

    def test_handles_none_content(self):
        assert _strip_enml("") == ""


# CLI tests


class TestCli:
    def _run(self, *args, env=None):
        """Run main() with given args; capture stdout/stderr."""
        import io
        import sys

        saved_stdout = sys.stdout
        saved_stderr = sys.stderr
        saved_environ = os.environ.copy()

        try:
            out = io.StringIO()
            err = io.StringIO()
            sys.stdout = out
            sys.stderr = err

            if env is not None:
                os.environ.clear()
                os.environ.update(env)

            try:
                main(list(args) if args else [])
                code = 0
            except SystemExit as e:
                code = e.code if isinstance(e.code, int) else 1

            return code, out.getvalue(), err.getvalue()
        finally:
            sys.stdout = saved_stdout
            sys.stderr = saved_stderr
            os.environ.clear()
            os.environ.update(saved_environ)

    def test_help_shows_usage(self):
        code, out, err = self._run("--help")
        assert "usage" in out.lower() or "list-notebooks" in out

    def test_list_notebooks_json(self):
        env = {"TEST_COOKIE": FAKE_COOKIE}
        with patch.object(EvernoteClient, "_make_transport", return_value=MagicMock()), \
             patch.object(EvernoteClient, "_resolve_note_store_url"), \
             patch.object(EvernoteClient, "_note_store_client") as mock_ns_ctor:
            mock_ns = MagicMock()
            nb1 = _make_fake_notebook("nb1", "Home")
            nb2 = _make_fake_notebook("nb2", "Work")
            mock_ns.listNotebooks.return_value = [nb1, nb2]
            mock_ns_ctor.return_value = mock_ns

            code, out, err = self._run(
                "--cookie-env", "TEST_COOKIE",
                "--json",
                "list-notebooks",
                env=env,
            )

        assert code == 0, f"stderr: {err}"
        data = json.loads(out)
        assert len(data) == 2
        assert data[0]["name"] == "Home"

    def test_get_note(self):
        env = {"TEST_COOKIE": FAKE_COOKIE}
        with patch.object(EvernoteClient, "_make_transport", return_value=MagicMock()), \
             patch.object(EvernoteClient, "_resolve_note_store_url"), \
             patch.object(EvernoteClient, "_note_store_client") as mock_ns_ctor:
            mock_ns = MagicMock()
            mock_ns.getNote.return_value = _make_fake_note(guid="abc123")
            mock_ns_ctor.return_value = mock_ns

            code, out, err = self._run(
                "--cookie-env", "TEST_COOKIE",
                "--json", "get", "abc123",
                env=env,
            )

        assert code == 0, f"stderr: {err}"
        data = json.loads(out)
        assert data["guid"] == "abc123"

    def test_search_empty_returns_list(self):
        env = {"TEST_COOKIE": FAKE_COOKIE}
        with patch.object(EvernoteClient, "_make_transport", return_value=MagicMock()), \
             patch.object(EvernoteClient, "_resolve_note_store_url"), \
             patch.object(EvernoteClient, "_note_store_client") as mock_ns_ctor:
            mock_ns = MagicMock()
            mock_ns.findNotesMetadata.return_value = _make_fake_notes_metadata_result([])
            mock_ns_ctor.return_value = mock_ns

            code, out, err = self._run(
                "--cookie-env", "TEST_COOKIE",
                "--json", "search",
                env=env,
            )

        assert code == 0, f"stderr: {err}"
        data = json.loads(out)
        assert data == []

    def test_missing_command_exits_nonzero(self):
        env = {"TEST_COOKIE": FAKE_COOKIE}
        code, out, err = self._run(env=env)
        assert code != 0

    def test_auth_error_exits_nonzero(self, monkeypatch):
        monkeypatch.setenv("FAKE_VAR", "")
        code, out, err = self._run("--cookie-env", "FAKE_VAR", "list-notebooks")
        assert code == 1
        assert "Auth" in err or "auth" in err.lower() or "cookie" in err.lower()

    def test_create_note(self):
        env = {"TEST_COOKIE": FAKE_COOKIE}
        with patch.object(EvernoteClient, "_make_transport", return_value=MagicMock()), \
             patch.object(EvernoteClient, "_resolve_note_store_url"), \
             patch.object(EvernoteClient, "_note_store_client") as mock_ns_ctor:
            mock_ns = MagicMock()
            mock_ns.createNote.return_value = _make_fake_note(guid="new", title="Shopping")
            mock_ns_ctor.return_value = mock_ns

            code, out, err = self._run(
                "--cookie-env", "TEST_COOKIE",
                "--json", "create", "--title", "Shopping", "--content", "milk",
                env=env,
            )

        assert code == 0, f"stderr: {err}"
        data = json.loads(out)
        assert data["guid"] == "new"

    def test_update_note(self):
        env = {"TEST_COOKIE": FAKE_COOKIE}
        with patch.object(EvernoteClient, "_make_transport", return_value=MagicMock()), \
             patch.object(EvernoteClient, "_resolve_note_store_url"), \
             patch.object(EvernoteClient, "_note_store_client") as mock_ns_ctor:
            mock_ns = MagicMock()
            original = _make_fake_note(guid="n1", title="Old")
            updated = _make_fake_note(guid="n1", title="New Title")
            mock_ns.getNote.return_value = original
            mock_ns.updateNote.return_value = updated
            mock_ns_ctor.return_value = mock_ns

            code, out, err = self._run(
                "--cookie-env", "TEST_COOKIE",
                "--json", "update", "n1", "--title", "New Title",
                env=env,
            )

        assert code == 0, f"stderr: {err}"
        data = json.loads(out)
        assert data["title"] == "New Title"

    def test_list_tags(self):
        env = {"TEST_COOKIE": FAKE_COOKIE}
        with patch.object(EvernoteClient, "_make_transport", return_value=MagicMock()), \
             patch.object(EvernoteClient, "_resolve_note_store_url"), \
             patch.object(EvernoteClient, "_note_store_client") as mock_ns_ctor:
            mock_ns = MagicMock()
            t1 = _make_tag_mock("t1", "urgent")
            t2 = _make_tag_mock("t2", "later")
            mock_ns.listTags.return_value = [t1, t2]
            mock_ns_ctor.return_value = mock_ns

            code, out, err = self._run(
                "--cookie-env", "TEST_COOKIE",
                "--json", "list-tags",
                env=env,
            )

        assert code == 0, f"stderr: {err}"
        data = json.loads(out)
        assert len(data) == 2
        assert data[0]["name"] == "urgent"

    def test_human_output_mode(self):
        env = {"TEST_COOKIE": FAKE_COOKIE}
        with patch.object(EvernoteClient, "_make_transport", return_value=MagicMock()), \
             patch.object(EvernoteClient, "_resolve_note_store_url"), \
             patch.object(EvernoteClient, "_note_store_client") as mock_ns_ctor:
            mock_ns = MagicMock()
            nb = _make_fake_notebook("nb1", "Home")
            mock_ns.listNotebooks.return_value = [nb]
            mock_ns_ctor.return_value = mock_ns

            code, out, err = self._run(
                "--cookie-env", "TEST_COOKIE",
                "list-notebooks",
                env=env,
            )

        assert code == 0, f"stderr: {err}"
        assert "Home" in out
        assert "guid" in out
