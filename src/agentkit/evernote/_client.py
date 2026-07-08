"""Evernote client using clipper-sso cookie auth via Thrift layer.

No OAuth, no developer token — the clipper-sso cookie IS the auth.
Extract it from Chrome DevTools > Application > Cookies >
www.evernote.com > clipper-sso. Store in env var EVERNOTE_CLIPPER_SSO.

Uses the Thrift transport/protocol layer directly because
evernote.api.client.EvernoteClient requires oauth2 which is broken.
"""
from __future__ import annotations

import json
import os
import re
import sys
from typing import Any

from thrift.transport import THttpClient
from thrift.protocol import TBinaryProtocol
from evernote2.edam.userstore import UserStore
from evernote2.edam.notestore import NoteStore
from evernote2.edam.type import ttypes as Types
from evernote2.edam.notestore.ttypes import (
    NoteFilter,
    NotesMetadataResultSpec,
)
from evernote2.edam.userstore.constants import (
    EDAM_VERSION_MAJOR,
    EDAM_VERSION_MINOR,
)


# XML-safe container names from the prod Evernote instance
_EVERNOTE_USER_STORE_URL = "https://www.evernote.com/edam/user"
_ENML_HEADER = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">\n'
)
_ENML_WRAPPER_START = '<en-note style="word-wrap: break-word; -webkit-nbsp-mode: space; -webkit-line-break: after-white-space;">'
_ENML_WRAPPER_END = "</en-note>"

# Exceptions


class EvernoteError(Exception):
    """Base for Evernote-related errors."""


class EvernoteAuthError(EvernoteError):
    """Authentication failure — bad cookie or expired session."""


class EvernoteClient:
    """Evernote Thrift client authenticated with a clipper-sso cookie.

    Args:
        cookie: The raw clipper-sso cookie string (S=s101:U=...).
            If None, reads from EVERNOTE_CLIPPER_SSO env var.
        cookie_env_var: Name of the env var holding the cookie.
        user_store_url: Override the UserStore Thrift endpoint.
    """

    def __init__(
        self,
        cookie: str | None = None,
        *,
        cookie_env_var: str = "EVERNOTE_CLIPPER_SSO",
        user_store_url: str = _EVERNOTE_USER_STORE_URL,
    ) -> None:
        self._cookie = self._resolve_cookie(cookie, cookie_env_var)
        self._user_store_url = user_store_url
        self._note_store_url: str | None = None
        self._shard_id: str | None = None

    @staticmethod
    def _resolve_cookie(cookie: str | None, env_var: str) -> str:
        if cookie:
            return cookie.strip()
        val = os.environ.get(env_var, "").strip()
        if not val:
            raise EvernoteAuthError(
                f"No cookie provided. Set {env_var} or pass cookie= explicitly."
            )
        return val

    # Transport helpers

    def _make_transport(self, url: str) -> THttpClient.THttpClient:
        transport = THttpClient.THttpClient(url)
        transport.setCustomHeaders({"Cookie": f"clipper-sso={self._cookie};"})
        return transport

    def _user_store_client(self) -> UserStore.Client:
        transport = self._make_transport(self._user_store_url)
        proto = TBinaryProtocol.TBinaryProtocol(transport)
        return UserStore.Client(proto)

    def _note_store_client(self) -> NoteStore.Client:
        if not self._note_store_url:
            self._resolve_note_store_url()
        transport = self._make_transport(self._note_store_url)
        proto = TBinaryProtocol.TBinaryProtocol(transport)
        return NoteStore.Client(proto)

    def _resolve_note_store_url(self) -> None:
        """Fetch the user's personal NoteStore URL via getUserUrls."""
        try:
            client = self._user_store_client()
            urls = client.getUserUrls(self._cookie)
        except Exception as exc:
            raise EvernoteAuthError(
                f"Failed to get user URLs — cookie invalid? {exc}"
            ) from exc

        self._note_store_url = urls.noteStoreUrl
        match = re.search(r"/edam/note/(s\d+)", self._note_store_url)
        if match:
            self._shard_id = match.group(1)

    # Public API

    @property
    def shard_id(self) -> str | None:
        if self._note_store_url is None:
            self._resolve_note_store_url()
        return self._shard_id

    def list_notebooks(self) -> list[dict[str, str]]:
        """Return all notebooks as a list of {guid, name} dicts."""
        try:
            ns = self._note_store_client()
            notebooks = ns.listNotebooks(self._cookie)
        except Exception as exc:
            raise EvernoteError(f"listNotebooks failed: {exc}") from exc

        return [
            {"guid": nb.guid, "name": nb.name}
            for nb in notebooks
        ]

    def find_notes(
        self,
        query: str = "",
        notebook_guid: str | None = None,
        offset: int = 0,
        max_notes: int = 50,
    ) -> list[dict[str, Any]]:
        """Search notes, returning metadata for each match.

        Args:
            query: Evernote search grammar query (empty = all notes).
            notebook_guid: Limit to a specific notebook.
            offset: Pagination offset.
            max_notes: Max results (1-250, default 50).
        """
        filt = NoteFilter()
        if query:
            filt.words = query
        if notebook_guid:
            filt.notebookGuid = notebook_guid
        filt.order = Types.NoteSortOrder.UPDATED
        filt.ascending = False

        spec = NotesMetadataResultSpec()
        spec.includeTitle = True
        spec.includeContentLength = True
        spec.includeCreated = True
        spec.includeUpdated = True
        spec.includeNotebookGuid = True
        spec.includeTagGuids = True

        try:
            ns = self._note_store_client()
            result = ns.findNotesMetadata(
                self._cookie, filt, offset, max_notes, spec
            )
        except Exception as exc:
            raise EvernoteError(f"findNotes failed: {exc}") from exc

        notes = []
        for note_meta in result.notes:
            d = {
                "guid": note_meta.guid,
                "title": note_meta.title or "",
                "contentLength": note_meta.contentLength or 0,
                "created": str(note_meta.created),
                "updated": str(note_meta.updated),
                "notebookGuid": note_meta.notebookGuid or "",
            }
            notes.append(d)
        return notes

    def get_note(
        self,
        guid: str,
        *,
        with_content: bool = True,
        raw_content: bool = False,
    ) -> dict[str, Any]:
        """Fetch a note by guid.

        Args:
            guid: Note GUID.
            with_content: Include note body content.
            raw_content: Return raw ENML instead of stripped plaintext.

        Returns:
            dict with keys: guid, title, content, notebookGuid, tagGuids,
            created, updated.
        """
        try:
            ns = self._note_store_client()
            note = ns.getNote(
                self._cookie,
                guid,
                with_content,
                False,  # withResourcesData
                False,  # withResourcesRecognition
                False,  # withResourcesAlternateData
            )
        except Exception as exc:
            raise EvernoteError(f"getNote({guid}) failed: {exc}") from exc

        content = note.content or ""
        if content and not raw_content:
            content = _strip_enml(content)

        return {
            "guid": note.guid,
            "title": note.title or "",
            "content": content,
            "notebookGuid": note.notebookGuid or "",
            "tagGuids": list(note.tagGuids) if note.tagGuids else [],
            "created": str(note.created),
            "updated": str(note.updated),
        }

    def update_note(
        self,
        guid: str,
        title: str | None = None,
        content: str | None = None,
        notebook_guid: str | None = None,
        tag_guids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Update a note's fields. Only provided fields are changed.

        Args:
            guid: Note GUID to update.
            title: New title (None = unchanged).
            content: New body text in plaintext or HTML (wrapped as ENML).
            notebook_guid: Move note to a different notebook.
            tag_guids: Replace tags with these GUIDs.

        Returns:
            The updated note metadata dict.
        """
        ns = self._note_store_client()
        note = ns.getNote(
            self._cookie,
            guid,
            True,
            False,
            False,
            False,
        )

        if title is not None:
            note.title = title
        if content is not None:
            note.content = _wrap_enml(content)
        if notebook_guid is not None:
            note.notebookGuid = notebook_guid
        if tag_guids is not None:
            note.tagGuids = tag_guids

        try:
            updated = ns.updateNote(self._cookie, note)
        except Exception as exc:
            raise EvernoteError(f"updateNote({guid}) failed: {exc}") from exc

        body = updated.content or ""
        body = _strip_enml(body)
        return {
            "guid": updated.guid,
            "title": updated.title or "",
            "content": body,
            "notebookGuid": updated.notebookGuid or "",
            "tagGuids": list(updated.tagGuids) if updated.tagGuids else [],
            "created": str(updated.created),
            "updated": str(updated.updated),
        }

    def create_note(
        self,
        title: str,
        content: str = "",
        notebook_guid: str | None = None,
        tag_guids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a new note.

        Args:
            title: Note title.
            content: Plaintext or HTML body (wrapped as ENML).
            notebook_guid: Target notebook GUID (None = default notebook).
            tag_guids: Tag GUIDs to apply.

        Returns:
            The created note metadata dict with GUID.
        """
        note = Types.Note()
        note.title = title
        note.content = _wrap_enml(content)

        if notebook_guid:
            note.notebookGuid = notebook_guid
        if tag_guids:
            note.tagGuids = tag_guids

        try:
            ns = self._note_store_client()
            created = ns.createNote(self._cookie, note)
        except Exception as exc:
            raise EvernoteError(f"createNote failed: {exc}") from exc

        body = created.content or ""
        body = _strip_enml(body)
        return {
            "guid": created.guid,
            "title": created.title or "",
            "content": body,
            "notebookGuid": created.notebookGuid or "",
            "tagGuids": list(created.tagGuids) if created.tagGuids else [],
            "created": str(created.created),
            "updated": str(created.updated),
        }

    def list_tags(self) -> list[dict[str, str]]:
        """Return all tags as a list of {guid, name} dicts."""
        try:
            ns = self._note_store_client()
            tags = ns.listTags(self._cookie)
        except Exception as exc:
            raise EvernoteError(f"listTags failed: {exc}") from exc

        return [{"guid": t.guid, "name": t.name} for t in tags]

    def get_notebook_guid_by_name(self, name: str) -> str | None:
        """Look up a notebook GUID by its exact name."""
        for nb in self.list_notebooks():
            if nb["name"] == name:
                return nb["guid"]
        return None


def _wrap_enml(text: str) -> str:
    if text.strip().startswith("<en-note"):
        return text
    if text.strip().startswith("<?xml"):
        return text
    escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    lines = escaped.split("\n")
    paragraphs = []
    for line in lines:
        if line.strip():
            paragraphs.append(f"<div>{line}</div>")
        else:
            paragraphs.append("<div><br/></div>")
    body = "\n".join(paragraphs)
    return f"{_ENML_HEADER}{_ENML_WRAPPER_START}\n{body}\n{_ENML_WRAPPER_END}"


def _strip_enml(enml: str) -> str:
    text = re.sub(r"<style[^>]*>.*?</style>", "", enml, flags=re.DOTALL)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</div>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    entities = {
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&quot;": '"',
        "&#39;": "'",
        "&apos;": "'",
        "&nbsp;": " ",
    }
    for entity, char in entities.items():
        text = text.replace(entity, char)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
