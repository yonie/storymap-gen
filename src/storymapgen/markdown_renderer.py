"""Markdown table renderer for story maps — renders natively in Notion and other markdown viewers."""

from __future__ import annotations

from html import escape

from .models import StoryMap


def render_markdown(storymap: StoryMap) -> str:
    """Render story map as a markdown table.

    Activities are columns, releases are rows. Sprint goal is in the first column.
    Stories are listed as bullet points in each cell. Ticket IDs link to the ticket system.
    """
    lines = []

    # Header row
    header = "| Sprint / Goal |"
    separator = "| --- |"
    for activity in storymap.activities:
        desc = f"<br><small>{escape(activity.description)}</small>" if activity.description else ""
        header += f" {activity.title}{desc} |"
        separator += " --- |"
    lines.append(header)
    lines.append(separator)

    # Release rows
    for release in storymap.releases:
        # Sprint cell: ID, label, goal
        sprint_cell = f"**{release.id}** — {release.label}<br><br>*{release.goal}*"

        row = f"| {sprint_cell} |"
        for activity in storymap.activities:
            stories = storymap.stories_for_cell(release.id, activity.id)
            if stories:
                cell_parts = []
                for s in stories:
                    ticket_link = ""
                    if s.ticket and not storymap.new_ticket(s.ticket):
                        url = storymap.ticket_url(s.ticket)
                        if url:
                            ticket_link = f" [{s.ticket}]({url})"
                        else:
                            ticket_link = f" [{s.ticket}]"
                    estimate_str = f" · {s.estimate}pt" if s.estimate else ""
                    new_badge = " `NEW`" if s.new else ""
                    cell_parts.append(f"- {s.title}{ticket_link}{estimate_str}{new_badge}")
                cell = "<br>".join(cell_parts)
                row += f" {cell} |"
            else:
                row += " — |"
        lines.append(row)

    return "\n".join(lines)