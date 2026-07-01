"""Story map data model — schema v2 (id-based references, validated)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


class StoryMapError(ValueError):
    """Raised when the JSON does not conform to the story map schema."""


@dataclass
class Story:
    """A single user story in the map."""
    id: str
    activity: str
    release: Optional[str]
    title: str
    ticket: Optional[str] = None
    estimate: Optional[int] = None
    new: bool = False
    metadata: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> "Story":
        sid = d.get("id")
        if not sid:
            raise StoryMapError(f"Story missing required 'id' field: {d}")
        activity = d.get("activity")
        if activity is None:
            raise StoryMapError(f"Story '{sid}' missing required 'activity' field")
        title = d.get("title")
        if not title:
            raise StoryMapError(f"Story '{sid}' missing required 'title' field")
        known = {"id", "activity", "release", "title", "ticket", "estimate", "new"}
        return cls(
            id=sid,
            activity=activity,
            release=d.get("release"),
            title=title,
            ticket=d.get("ticket"),
            estimate=d.get("estimate"),
            new=d.get("new", False),
            metadata={k: v for k, v in d.items() if k not in known},
        )


@dataclass
class Release:
    """A horizontal slice through the map — a release."""
    id: str
    label: str
    goal: str
    color: str = "#e0e0e0"

    @classmethod
    def from_dict(cls, d: dict) -> "Release":
        rid = d.get("id")
        if not rid:
            raise StoryMapError(f"Release missing required 'id' field: {d}")
        label = d.get("label")
        if not label:
            raise StoryMapError(f"Release '{rid}' missing required 'label' field")
        return cls(
            id=rid,
            label=label,
            goal=d.get("goal", ""),
            color=d.get("color", "#e0e0e0"),
        )


@dataclass
class Activity:
    """A backbone activity — a step in the user journey."""
    id: str
    title: str
    description: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "Activity":
        aid = d.get("id")
        if not aid:
            raise StoryMapError(f"Activity missing required 'id' field: {d}")
        title = d.get("title")
        if not title:
            raise StoryMapError(f"Activity '{aid}' missing required 'title' field")
        return cls(id=aid, title=title, description=d.get("description", ""))


@dataclass
class StoryMap:
    """The complete story map."""
    title: str
    persona: str
    narrative: str
    activities: list[Activity]
    releases: list[Release]
    stories: list[Story]
    ticket_url_template: Optional[str] = None

    @property
    def activity_ids(self) -> list[str]:
        return [a.id for a in self.activities]

    @property
    def activity_titles(self) -> list[str]:
        return [a.title for a in self.activities]

    @property
    def release_ids(self) -> list[str]:
        return [r.id for r in self.releases]

    def stories_for_release(self, release_id: str) -> list[Story]:
        return [s for s in self.stories if s.release == release_id]

    def stories_for_activity(self, activity_id: str) -> list[Story]:
        return [s for s in self.stories if s.activity == activity_id]

    def stories_for_cell(self, release_id: str, activity_id: str) -> list[Story]:
        return [
            s for s in self.stories
            if s.release == release_id and s.activity == activity_id
        ]

    def activity_by_id(self, activity_id: str) -> Optional[Activity]:
        for a in self.activities:
            if a.id == activity_id:
                return a
        return None

    def release_by_id(self, release_id: str) -> Optional[Release]:
        for r in self.releases:
            if r.id == release_id:
                return r
        return None

    @classmethod
    def from_dict(cls, d: dict) -> "StoryMap":
        title = d.get("title")
        if not title:
            raise StoryMapError("Missing required 'title' field")

        activities_raw = d.get("activities")
        if not activities_raw or not isinstance(activities_raw, list):
            raise StoryMapError("'activities' must be a non-empty list")
        activities = [Activity.from_dict(a) for a in activities_raw]

        releases_raw = d.get("releases")
        if not releases_raw or not isinstance(releases_raw, list):
            raise StoryMapError("'releases' must be a non-empty list")
        releases = [Release.from_dict(r) for r in releases_raw]

        stories_raw = d.get("stories")
        if not isinstance(stories_raw, list):
            raise StoryMapError("'stories' must be a list")
        stories = [Story.from_dict(s) for s in stories_raw]

        # Validate references
        activity_ids = set(a.id for a in activities)
        release_ids = set(r.id for r in releases)

        seen_story_ids = set()
        for s in stories:
            if s.id in seen_story_ids:
                raise StoryMapError(f"Duplicate story id: '{s.id}'")
            seen_story_ids.add(s.id)
            if s.activity not in activity_ids:
                raise StoryMapError(
                    f"Story '{s.id}' references unknown activity '{s.activity}'. "
                    f"Valid activities: {sorted(activity_ids)}"
                )
            if s.release is not None and s.release not in release_ids:
                raise StoryMapError(
                    f"Story '{s.id}' references unknown release '{s.release}'. "
                    f"Valid releases: {sorted(release_ids)}"
                )

        seen_activity_ids = set()
        for a in activities:
            if a.id in seen_activity_ids:
                raise StoryMapError(f"Duplicate activity id: '{a.id}'")
            seen_activity_ids.add(a.id)

        seen_release_ids = set()
        for r in releases:
            if r.id in seen_release_ids:
                raise StoryMapError(f"Duplicate release id: '{r.id}'")
            seen_release_ids.add(r.id)

        return cls(
            title=title,
            persona=d.get("persona", ""),
            narrative=d.get("narrative", ""),
            activities=activities,
            releases=releases,
            stories=stories,
            ticket_url_template=d.get("ticket_url_template"),
        )

    @classmethod
    def from_json(cls, path: str) -> "StoryMap":
        import json
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    def ticket_url(self, ticket: str) -> Optional[str]:
        if not ticket or self.new_ticket(ticket):
            return None
        if self.ticket_url_template:
            return self.ticket_url_template.replace("{ticket}", ticket)
        return None

    @staticmethod
    def new_ticket(ticket: str) -> bool:
        return not ticket or ticket.upper() == "NEW"