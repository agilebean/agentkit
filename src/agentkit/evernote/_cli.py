"""CLI for Evernote note operations via clipper-sso cookie auth.

Usage:
    python -m agentkit.evernote._cli <command> [args...]

    export EVERNOTE_CLIPPER_SSO="S=s101:U=...:E=...:C=...:P=...:A=...:V=2:H=..."

    python -m agentkit.evernote._cli list-notebooks
    python -m agentkit.evernote._cli search "intitle:recipe"
    python -m agentkit.evernote._cli get <note_guid>
    python -m agentkit.evernote._cli create --title "Shopping list" --content "milk, eggs"
    python -m agentkit.evernote._cli update <note_guid> --title "Updated title"
    python -m agentkit.evernote._cli update <note_guid> --content "$(cat body.txt)"
    python -m agentkit.evernote._cli list-tags
"""
from __future__ import annotations

import argparse
import json
import sys

from agentkit.evernote._client import (
    EvernoteClient,
    EvernoteError,
    EvernoteAuthError,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evernote CLI — read/write notes via clipper-sso cookie.",
    )
    parser.add_argument(
        "--cookie-env",
        default="EVERNOTE_CLIPPER_SSO",
        help="Env var holding the clipper-sso cookie (default: EVERNOTE_CLIPPER_SSO).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON (default: human-readable text).",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # list-notebooks
    sub.add_parser("list-notebooks", help="List all notebooks.")

    # list-tags
    sub.add_parser("list-tags", help="List all tags.")

    # search
    p_search = sub.add_parser("search", help="Find notes.")
    p_search.add_argument("query", nargs="?", default="", help="Evernote search grammar query.")
    p_search.add_argument("--notebook", dest="notebook_name", default=None, help="Limit to notebook by name.")
    p_search.add_argument("--max", type=int, default=50, help="Max results (default 50).")

    # get
    p_get = sub.add_parser("get", help="Fetch a note by GUID.")
    p_get.add_argument("guid", help="Note GUID.")
    p_get.add_argument("--raw", action="store_true", help="Keep ENML body (default: strip to plaintext).")

    # create
    p_create = sub.add_parser("create", help="Create a new note.")
    p_create.add_argument("--title", required=True, help="Note title.")
    p_create.add_argument("--content", default="", help="Note body (plaintext or HTML).")
    p_create.add_argument("--notebook", dest="notebook_name", default=None, help="Target notebook by name.")
    p_create.add_argument("--tag", dest="tag_names", action="append", default=[], help="Tag by name (repeatable).")

    # update
    p_update = sub.add_parser("update", help="Update an existing note.")
    p_update.add_argument("guid", help="Note GUID.")
    p_update.add_argument("--title", default=None, help="New title.")
    p_update.add_argument("--content", default=None, help="New body text. Use '-' to read from stdin.")
    p_update.add_argument("--notebook", dest="notebook_name", default=None, help="Move to notebook by name.")
    p_update.add_argument("--tag", dest="tag_names", action="append", default=[], help="Replace tags by name (repeatable).")

    return parser


def _resolve_tags(args: argparse.Namespace, client: EvernoteClient) -> list[str] | None:
    tag_names = getattr(args, "tag_names", [])
    if not tag_names:
        return None
    tags = client.list_tags()
    tag_map = {t["name"]: t["guid"] for t in tags}
    resolved = []
    for name in tag_names:
        guid = tag_map.get(name)
        if not guid:
            raise EvernoteError(f"Tag '{name}' not found. Available: {sorted(tag_map.keys())}")
        resolved.append(guid)
    return resolved


def _resolve_notebook(args: argparse.Namespace, client: EvernoteClient) -> str | None:
    name = getattr(args, "notebook_name", None)
    if not name:
        return None
    guid = client.get_notebook_guid_by_name(name)
    if guid is None:
        nb_names = [nb["name"] for nb in client.list_notebooks()]
        raise EvernoteError(f"Notebook '{name}' not found. Available: {sorted(nb_names)}")
    return guid


def _read_content(arg_content: str | None) -> str | None:
    if arg_content is None:
        return None
    if arg_content == "-":
        return sys.stdin.read()
    return arg_content


def _print_output(data, *, use_json: bool) -> None:
    if use_json:
        json.dump(data, sys.stdout, indent=2, default=str)
        sys.stdout.write("\n")
    else:
        _print_human(data)


def _print_human(data) -> None:
    if isinstance(data, list):
        if not data:
            print("(no results)")
            return
        for item in data:
            if isinstance(item, dict):
                _print_dict(item)
                print("---")
            else:
                print(f"- {item}")
    elif isinstance(data, dict):
        _print_dict(data)
    else:
        print(data)


def _print_dict(d: dict) -> None:
    for k, v in d.items():
        if k == "content" and v and len(str(v)) > 500:
            print(f"{k}:")
            print("-" * 40)
            print(v)
            print("-" * 40)
        else:
            print(f"{k}: {v}")


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        client = EvernoteClient(cookie_env_var=args.cookie_env)
    except EvernoteAuthError as exc:
        print(f"Auth error: {exc}", file=sys.stderr)
        sys.exit(1)

    cmd = args.command
    try:
        if cmd == "list-notebooks":
            data = client.list_notebooks()
        elif cmd == "list-tags":
            data = client.list_tags()
        elif cmd == "search":
            nb_guid = _resolve_notebook(args, client)
            data = client.find_notes(
                query=args.query,
                notebook_guid=nb_guid,
                max_notes=args.max,
            )
        elif cmd == "get":
            data = client.get_note(args.guid, raw_content=args.raw)
        elif cmd == "create":
            nb_guid = _resolve_notebook(args, client)
            tag_guids = _resolve_tags(args, client)
            data = client.create_note(
                title=args.title,
                content=args.content,
                notebook_guid=nb_guid,
                tag_guids=tag_guids,
            )
        elif cmd == "update":
            content = _read_content(args.content)
            nb_guid = _resolve_notebook(args, client)
            tag_guids = _resolve_tags(args, client)
            if tag_guids is not None:
                pass  # tag_guids resolved above, only applied if --tag used
            arg_dict = {"guid": args.guid}
            if args.title is not None:
                arg_dict["title"] = args.title
            if content is not None:
                arg_dict["content"] = content
            if nb_guid is not None:
                arg_dict["notebook_guid"] = nb_guid
            if tag_guids is not None:
                arg_dict["tag_guids"] = tag_guids
            data = client.update_note(**arg_dict)
        else:
            parser.print_help()
            sys.exit(1)
    except EvernoteError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    _print_output(data, use_json=args.json)


if __name__ == "__main__":
    main()
