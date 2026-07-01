"""HTML renderer for story maps — a dynamic, interactive story map web page."""

from __future__ import annotations

from html import escape

from .models import StoryMap


def render_html(storymap: StoryMap) -> str:
    """Render story map as a self-contained HTML page.

    Features:
    - Colored columns per activity
    - Colored release rows matching sprint colors
    - Clickable ticket links
    - Responsive grid layout
    - Print-friendly
    """
    activities_html = ""
    for activity in storymap.activities:
        desc = f'<div class="activity-desc">{escape(activity.description)}</div>' if activity.description else ""
        activities_html += f"    <th class=\"activity-header\">{escape(activity.title)}{desc}</th>\n"

    releases_html = ""
    for release in storymap.releases:
        release_stories = ""
        for activity in storymap.activities:
            stories = storymap.stories_for_cell(release.id, activity.id)
            if stories:
                cell_stories = ""
                for s in stories:
                    ticket_html = ""
                    if s.ticket and not storymap.new_ticket(s.ticket):
                        url = storymap.ticket_url(s.ticket)
                        if url:
                            ticket_html = f' <a href="{escape(url)}" class="ticket" target="_blank">[{escape(s.ticket)}]</a>'
                        else:
                            ticket_html = f' <span class="ticket">[{escape(s.ticket)}]</span>'
                    estimate_html = ""
                    if s.estimate:
                        estimate_html = f' <span class="estimate">{s.estimate}pt</span>'
                    new_badge = ' <span class="new-badge">NEW</span>' if s.new else ""
                    cell_stories += f"        <div class=\"story\">{escape(s.title)}{ticket_html}{estimate_html}{new_badge}</div>\n"
                release_stories += f"    <td class=\"story-cell has-stories\" style=\"--release-color: {escape(release.color)}\">\n{cell_stories}    </td>\n"
            else:
                release_stories += f"    <td class=\"story-cell empty\">—</td>\n"

        releases_html += f"""  <tr class="release-row" style="--release-color: {escape(release.color)}">
    <td class="sprint-cell" style="background: {escape(release.color)}">
      <div class="sprint-id">{escape(release.id)}</div>
      <div class="sprint-label">{escape(release.label)}</div>
      <div class="sprint-goal">{escape(release.goal)}</div>
    </td>
{release_stories}  </tr>
"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(storymap.title)} — Story Map</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #f8f9fa;
    color: #1a1a1a;
    padding: 24px;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}

  h1 {{
    font-size: 1.5rem;
    margin-bottom: 4px;
  }}

  .meta {{
    font-size: 0.85rem;
    color: #666;
    margin-bottom: 16px;
  }}

  .narrative {{
    font-style: italic;
    color: #555;
    margin-bottom: 24px;
    padding: 12px 16px;
    background: #f0f0f0;
    border-radius: 8px;
    font-size: 0.9rem;
  }}

  .storymap-info {{
    font-size: 0.75rem;
    color: #999;
    margin-top: 24px;
    padding-top: 12px;
    border-top: 1px solid #e0e0e0;
  }}

  .storymap-info a {{
    color: #2563eb;
    text-decoration: none;
  }}

  table {{
    border-collapse: collapse;
    width: 100%;
    table-layout: fixed;
  }}

    th, td {{
    border: 1px solid #d0d0d0;
    vertical-align: top;
    padding: 10px;
  }}

  .activity-header {{
    background: #2c3e50;
    color: white;
    font-size: 0.8rem;
    font-weight: 600;
    text-align: center;
    padding: 12px 8px;
    line-height: 1.3;
  }}

  .activity-desc {{
    font-size: 0.7rem;
    font-weight: 400;
    color: #b0c4de;
    margin-top: 4px;
    line-height: 1.3;
  }}

  .sprint-cell {{
    width: 180px;
    min-width: 180px;
    padding: 12px;
    border-right: 2px solid #b0b0b0;
  }}

  .sprint-id {{
    font-weight: 800;
    font-size: 1.1rem;
    margin-bottom: 2px;
  }}

  .sprint-label {{
    font-weight: 600;
    font-size: 0.85rem;
    margin-bottom: 8px;
  }}

  .sprint-goal {{
    font-size: 0.78rem;
    color: #444;
    line-height: 1.4;
    border-top: 1px solid rgba(0,0,0,0.1);
    padding-top: 8px;
    margin-top: 8px;
  }}

  .story-cell {{
    padding: 8px;
  }}

  .story-cell.empty {{
    text-align: center;
    color: #ccc;
    font-size: 1.2rem;
  }}

  .story {{
    background: var(--release-color, #f0f0f0);
    border-radius: 6px;
    padding: 6px 10px;
    margin-bottom: 6px;
    font-size: 0.82rem;
    line-height: 1.3;
    border: 1px solid rgba(0,0,0,0.08);
    transition: box-shadow 0.15s;
  }}

  .story:hover {{
    box-shadow: 0 2px 6px rgba(0,0,0,0.15);
  }}

  .ticket {{
    font-family: 'SF Mono', Monaco, Consolas, monospace;
    font-size: 0.72rem;
    color: #2563eb;
    text-decoration: none;
    font-weight: 600;
    white-space: nowrap;
  }}

  .ticket:hover {{
    text-decoration: underline;
  }}

  .estimate {{
    font-size: 0.7rem;
    color: #888;
    margin-left: 4px;
    font-weight: 500;
  }}

  .new-badge {{
    font-size: 0.62rem;
    background: #2563eb;
    color: #fff;
    padding: 1px 5px;
    border-radius: 3px;
    margin-left: 4px;
    font-weight: 700;
    vertical-align: middle;
  }}

  @media print {{
    body {{ padding: 0; background: white; }}
    .story {{ break-inside: avoid; }}
  }}

  @media (max-width: 1200px) {{
    table {{ table-layout: auto; }}
    .sprint-cell {{ width: 140px; min-width: 140px; }}
  }}
</style>
</head>
<body>

<h1>{escape(storymap.title)}</h1>
<div class="meta"><strong>Persona:</strong> {escape(storymap.persona)}</div>
<div class="narrative">{escape(storymap.narrative)}</div>

<table>
  <thead>
    <tr>
    <th class="activity-header" style="background: #1a1a2e">Sprint / Goal</th>
{activities_html}    </tr>
  </thead>
  <tbody>
{releases_html}  </tbody>
</table>

<div class="storymap-info">
  Generated with <a href="https://github.com/yonie/storymap-gen">storymap-gen</a> — based on <a href="https://jpattonassociates.com/user-story-mapping/" target="_blank">User Story Mapping</a> by Jeff Patton.
</div>

</body>
</html>"""