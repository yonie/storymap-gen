"""CLI entry point for storymap-gen."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .models import StoryMap, StoryMapError
from .ascii_renderer import render_ascii
from .html_renderer import render_html
from .markdown_renderer import render_markdown


def main():
    parser = argparse.ArgumentParser(
        prog="storymapgen",
        description="Generate story maps from JSON. ASCII art, HTML, Markdown output.",
    )
    parser.add_argument("input", help="Path to story map JSON file")
    parser.add_argument(
        "--format", "-f",
        choices=["ascii", "html", "markdown", "all"],
        default="ascii",
        help="Output format (default: ascii)",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path. If --format=all, this is a directory.",
    )
    parser.add_argument(
        "--col-width", type=int, default=14,
        help="Column width for ASCII output (default: 14)",
    )
    parser.add_argument(
        "--release-width", type=int, default=22,
        help="Release column width for ASCII output (default: 22)",
    )
    parser.add_argument(
        "--serve", action="store_true",
        help="Start a local web server for HTML output (implies --format=html)",
    )
    parser.add_argument(
        "--port", type=int, default=8765,
        help="Port for web server (default: 8765)",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Validate the JSON input without producing output. Exits non-zero on error.",
    )

    args = parser.parse_args()

    try:
        storymap = StoryMap.from_json(args.input)
    except StoryMapError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    if args.check:
        print(f"OK: {args.input}")
        print(f"  title: {storymap.title}")
        print(f"  activities: {len(storymap.activities)}")
        print(f"  releases: {len(storymap.releases)}")
        print(f"  stories: {len(storymap.stories)}")
        return

    if args.serve:
        _serve_html(storymap, args.port)
        return

    if args.format == "ascii":
        result = render_ascii(storymap, col_width=args.col_width, release_width=args.release_width)
        _write_output(result, args.output)
    elif args.format == "html":
        result = render_html(storymap)
        _write_output(result, args.output)
    elif args.format == "markdown":
        result = render_markdown(storymap)
        _write_output(result, args.output)
    elif args.format == "all":
        outdir = Path(args.output or "output")
        outdir.mkdir(parents=True, exist_ok=True)
        ascii_result = render_ascii(storymap, col_width=args.col_width, release_width=args.release_width)
        (outdir / "storymap.txt").write_text(ascii_result, encoding="utf-8")
        html_result = render_html(storymap)
        (outdir / "storymap.html").write_text(html_result, encoding="utf-8")
        md_result = render_markdown(storymap)
        (outdir / "storymap.md").write_text(md_result, encoding="utf-8")
        print(f"Generated: {outdir}/storymap.txt, {outdir}/storymap.html, {outdir}/storymap.md")


def _write_output(result: str, path: str | None):
    if path:
        Path(path).write_text(result, encoding="utf-8")
        print(f"Written to {path}")
    else:
        print(result)


def _serve_html(storymap: StoryMap, port: int):
    import http.server
    import socketserver
    import tempfile

    html = render_html(storymap)
    tmpdir = tempfile.mkdtemp()
    htmlpath = Path(tmpdir) / "storymap.html"
    htmlpath.write_text(html, encoding="utf-8")

    handler = http.server.SimpleHTTPRequestHandler
    handler.directory = tmpdir

    print(f"Serving story map at http://localhost:{port}/storymap.html")
    print("Press Ctrl+C to stop.")

    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()