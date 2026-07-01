"""ASCII art renderer for story maps."""

from __future__ import annotations

from .models import StoryMap


def _wrap(text: str, width: int) -> list[str]:
    """Wrap text to fit within width chars, splitting on spaces."""
    if len(text) <= width:
        return [text]
    lines = []
    words = text.split()
    current = ""
    for word in words:
        if len(current) + len(word) + (1 if current else 0) <= width:
            current = (current + " " + word) if current else word
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _pad(text: str, width: int) -> str:
    """Center-pad text to exactly width chars."""
    if len(text) > width:
        text = text[:width]
    return text.center(width)


def _build_story_lines(stories, col_width: int) -> list[str]:
    """Build lines for a story cell: title + ticket, wrapped."""
    lines = []
    for s in stories:
        for line in _wrap(s.title, col_width):
            lines.append(line)
        if s.ticket and not s.new and not StoryMap.new_ticket(s.ticket):
            lines.append(f"[{s.ticket}]")
    return lines


def _build_release_lines(release, release_width: int) -> list[str]:
    """Build lines for the release cell: ID, label, blank, goal."""
    lines = [release.id]
    for line in _wrap(release.label, release_width):
        lines.append(line)
    lines.append("")
    for line in _wrap(release.goal, release_width):
        lines.append(line)
    return lines


def _row(cells: list[list[str]], col_widths: list[int]) -> list[str]:
    """Build row lines from cells."""
    max_lines = max(len(c) for c in cells)
    padded = []
    for ci, c in enumerate(cells):
        p = list(c)
        w = col_widths[ci]
        while len(p) < max_lines:
            p.append(" " * w)
        padded.append(p)
    out = []
    for i in range(max_lines):
        parts = []
        for j, c in enumerate(padded):
            w = col_widths[j]
            parts.append(c[i][:w].ljust(w))
        out.append("│" + "│".join(parts) + "│")
    return out


def _cell(lines: list[str], width: int) -> list[str]:
    """Pad each line to width, centered."""
    return [_pad(line, width) for line in lines]


def render_ascii(storymap: StoryMap, col_width: int = 14, release_width: int = 22) -> str:
    """Render story map as ASCII art table.

    Args:
        storymap: The story map to render.
        col_width: Width of each activity column.
        release_width: Width of the release/goal column.

    Returns:
        ASCII art string with code block fences.
    """
    num_activities = len(storymap.activities)
    all_widths = [release_width] + [col_width] * num_activities

    def top_line():
        return "┌" + "┬".join(["─" * w for w in all_widths]) + "┐"

    def sep_line():
        return "├" + "┼".join(["─" * w for w in all_widths]) + "┤"

    def bottom_line():
        return "└" + "┴".join(["─" * w for w in all_widths]) + "┘"

    out = []
    out.append("```")

    # Header: activity titles
    header_cells = [_cell(["Release / Goal"], release_width)]
    for activity in storymap.activities:
        header_cells.append(_cell(_wrap(activity.title, col_width), col_width))

    out.append(top_line())
    for line in _row(header_cells, all_widths):
        out.append(line)

    # Release rows
    for release in storymap.releases:
        out.append(sep_line())

        release_cell = _cell(_build_release_lines(release, release_width), release_width)
        cells = [release_cell]
        for activity in storymap.activities:
            stories = storymap.stories_for_cell(release.id, activity.id)
            if stories:
                story_lines = _build_story_lines(stories, col_width)
                cells.append(_cell(story_lines, col_width))
            else:
                cells.append(_cell(["—"], col_width))

        for line in _row(cells, all_widths):
            out.append(line)

    out.append(bottom_line())
    out.append("```")
    return "\n".join(out)