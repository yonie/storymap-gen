"""Smoke tests: render all examples in all formats and validate schema."""

import sys
from pathlib import Path

import pytest

from storymapgen.models import StoryMap, StoryMapError
from storymapgen.ascii_renderer import render_ascii
from storymapgen.html_renderer import render_html
from storymapgen.markdown_renderer import render_markdown


EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"
EXAMPLE_FILES = sorted(EXAMPLES_DIR.glob("*.json"))


@pytest.fixture(params=EXAMPLE_FILES, ids=lambda p: p.stem)
def storymap(request):
    return StoryMap.from_json(str(request.param))


def test_all_examples_load_and_validate(storymap):
    assert storymap.title
    assert len(storymap.activities) > 0
    assert len(storymap.releases) > 0
    assert len(storymap.stories) > 0


def test_ascii_renders(storymap):
    result = render_ascii(storymap)
    assert "┌" in result
    assert "└" in result
    assert storymap.activities[0].title.split()[0] in result


def test_html_renders(storymap):
    result = render_html(storymap)
    assert "<!DOCTYPE html>" in result
    assert storymap.title in result
    assert "storymap-gen" in result
    assert "jpattonassociates.com" in result


def test_markdown_renders(storymap):
    result = render_markdown(storymap)
    assert "|" in result
    assert "---" in result
    assert storymap.activities[0].title in result


def test_ticket_links(storymap):
    html = render_html(storymap)
    if storymap.ticket_url_template:
        for s in storymap.stories:
            if s.ticket and not storymap.new_ticket(s.ticket):
                url = storymap.ticket_url(s.ticket)
                assert url and url in html


def test_activity_ids_are_unique(storymap):
    ids = [a.id for a in storymap.activities]
    assert len(ids) == len(set(ids))


def test_release_ids_are_unique(storymap):
    ids = [r.id for r in storymap.releases]
    assert len(ids) == len(set(ids))


def test_story_ids_are_unique(storymap):
    ids = [s.id for s in storymap.stories]
    assert len(ids) == len(set(ids))


def test_stories_reference_valid_activities(storymap):
    activity_ids = {a.id for a in storymap.activities}
    for s in storymap.stories:
        assert s.activity in activity_ids, f"Story {s.id} -> bad activity {s.activity}"


def test_stories_reference_valid_releases(storymap):
    release_ids = {r.id for r in storymap.releases}
    for s in storymap.stories:
        if s.release is not None:
            assert s.release in release_ids, f"Story {s.id} -> bad release {s.release}"


# --- Error cases ---

def test_missing_title_raises():
    with pytest.raises(StoryMapError, match="title"):
        StoryMap.from_dict({"activities": [], "releases": [], "stories": []})


def test_bad_activity_ref_raises():
    data = {
        "title": "T",
        "activities": [{"id": "a1", "title": "A"}],
        "releases": [{"id": "R1", "label": "M", "goal": "g"}],
        "stories": [{"id": "S1", "activity": "bad", "release": "R1", "title": "x"}],
    }
    with pytest.raises(StoryMapError, match="unknown activity"):
        StoryMap.from_dict(data)


def test_bad_release_ref_raises():
    data = {
        "title": "T",
        "activities": [{"id": "a1", "title": "A"}],
        "releases": [{"id": "R1", "label": "M", "goal": "g"}],
        "stories": [{"id": "S1", "activity": "a1", "release": "bad", "title": "x"}],
    }
    with pytest.raises(StoryMapError, match="unknown release"):
        StoryMap.from_dict(data)


def test_duplicate_story_id_raises():
    data = {
        "title": "T",
        "activities": [{"id": "a1", "title": "A"}],
        "releases": [{"id": "R1", "label": "M", "goal": "g"}],
        "stories": [
            {"id": "S1", "activity": "a1", "release": "R1", "title": "x"},
            {"id": "S1", "activity": "a1", "release": "R1", "title": "y"},
        ],
    }
    with pytest.raises(StoryMapError, match="Duplicate story id"):
        StoryMap.from_dict(data)


def test_missing_story_id_raises():
    data = {
        "title": "T",
        "activities": [{"id": "a1", "title": "A"}],
        "releases": [{"id": "R1", "label": "M", "goal": "g"}],
        "stories": [{"activity": "a1", "release": "R1", "title": "x"}],
    }
    with pytest.raises(StoryMapError, match="missing required 'id'"):
        StoryMap.from_dict(data)