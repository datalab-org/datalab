"""MkDocs build hooks.

The changelog is a symlink to the repo's `CHANGELOG.md`, which is assembled from
GitHub's generated release notes. Each release carries a "What's Changed" list of
every merged PR, which is worth keeping but buries the hand-written summary above
it. Rather than editing the changelog itself — it has to stay readable on GitHub,
and every future release would need the same treatment by hand — fold those lists
into collapsible blocks as the page is rendered.
"""

import re

# GitHub's callout syntax has no notion of a title: `> [!WARNING]` must sit alone
# on its line, and anything after it makes the whole block degrade to a plain
# blockquote — on GitHub as well as under the `github-callouts` extension. Both
# spellings below are promoted to a titled Material admonition instead.
CALLOUT = re.compile(
    r"^>\s*\[!(?P<kind>NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*(?P<title>.*?)\s*$",
    re.IGNORECASE,
)
BOLD_TITLE = re.compile(r"^\*\*(?P<title>.+?)\*\*\s*$")
# Material has no `important` admonition, and names GitHub's `caution` `danger`.
CALLOUT_TYPES = {
    "note": "note",
    "tip": "tip",
    "important": "info",
    "warning": "warning",
    "caution": "danger",
}

# Release notes have been pasted in at various heading levels and spellings over
# the years, so match any of them rather than assuming the `### What's Changed`
# used by recent releases.
CHANGES_HEADING = re.compile(r"^#{2,4}\s+What's changed\??\s*$", re.IGNORECASE)
CONTRIBUTORS_HEADING = re.compile(r"^#{2,4}\s+New contributors\s*$", re.IGNORECASE)
# `* @user made their first contribution in <url>`, as GitHub generates it.
CONTRIBUTOR = re.compile(
    r"^\*\s+@(?P<user>[\w-]+) made their first contribution in "
    r"https://github\.com/(?P<repo>[\w.-]+/[\w.-]+)/pull/(?P<pull>\d+)\s*$"
)
ANY_HEADING = re.compile(r"^#{1,6}\s")
# Kept outside the collapsed block: it is one line, and it is the link people
# actually follow when they want the full diff for a release.
FULL_CHANGELOG = re.compile(r"^\*\*Full Changelog\*\*")
# The same line, parsed: GitHub writes it as a bare compare URL between two tags.
COMPARE_LINK = re.compile(
    r"^\*\*Full Changelog\*\*:\s*"
    r"(?P<url>https://github\.com/(?P<repo>[\w.-]+/[\w.-]+)/compare/"
    r"(?P<base>[^.\s]\S*?)\.\.\.(?P<head>\S+))\s*$"
)

# Any Material admonition type works here: `info`, `abstract`, `example`, `quote`,
# `tip`, `question`… It only sets the colour and icon of the collapsed box.
ADMONITION = "abstract"


def _titled_callouts(markdown: str) -> str:
    """Promote titled GitHub callouts to Material admonitions.

    Two spellings are accepted: the title on the marker line itself, or a bold
    first line inside the callout. The latter is the one worth using in files that
    are also read on GitHub, since GitHub renders it as a proper alert with a bold
    lead. Untitled callouts are left for the `github-callouts` extension.
    """
    lines = markdown.splitlines()
    out: list[str] = []
    index = 0

    while index < len(lines):
        match = CALLOUT.match(lines[index])
        if match is None:
            out.append(lines[index])
            index += 1
            continue

        start = index
        index += 1
        body = []
        while index < len(lines) and lines[index].startswith(">"):
            body.append(re.sub(r"^>\s?", "", lines[index]))
            index += 1

        title = match["title"]
        if not title:
            for position, entry in enumerate(body):
                if not entry.strip():
                    continue
                bold = BOLD_TITLE.match(entry)
                if bold:
                    title = bold["title"]
                    del body[position]
                break

        if not title:
            # Untitled: hand it back verbatim for the extension to deal with.
            out.extend(lines[start:index])
            continue

        while body and not body[0].strip():
            body.pop(0)
        while body and not body[-1].strip():
            body.pop()

        kind = CALLOUT_TYPES[match["kind"].lower()]
        out.append(f'!!! {kind} "{title.replace(chr(34), "&quot;")}"')
        out.append("")
        out.extend(f"    {entry}" if entry.strip() else "" for entry in body)
        out.append("")

    return "\n".join(out)


def _release_tags(match: re.Match) -> str:
    """Render a compare URL as two linked release tags either side of an arrow.

    GitHub's generated notes end each release with a bare compare URL, which
    renders as a wall of link text. The two tags either side of the `...` are the
    useful part, so show those as chips linking to their own release pages, and
    keep the comparison itself on a trailing link.
    """
    repo, url = match["repo"], match["url"]

    def tag(ref: str) -> str:
        release = f"https://github.com/{repo}/releases/tag/{ref}"
        return f"[:octicons-tag-24: {ref}]({release}){{ .changelog-tag }}"

    return (
        f"{tag(match['base'])} :octicons-arrow-right-24: {tag(match['head'])} "
        f"[:octicons-git-compare-24: compare]({url}){{ .changelog-compare }}"
    )


def _contributor_bubbles(entries: list[str]) -> list[str]:
    """Render "new contributor" lines as a row of linked avatars.

    Twelve near-identical sentences say much less than twelve faces, so drop the
    prose (and the heading above it) and keep the names and avatars. The row is
    labelled for screen readers, which would otherwise be left with no clue as to
    what the links are, now that the heading is gone.
    """
    bubbles = []
    for entry in entries:
        match = CONTRIBUTOR.match(entry)
        if match is None:
            # Anything that does not fit the generated wording is left alone.
            return entries
        user, repo, pull = match["user"], match["repo"], match["pull"]
        bubbles.append(
            f'<li><a class="contributor" href="https://github.com/{user}"'
            f' title="@{user} — first contribution in {repo}#{pull}">'
            f'<img src="https://github.com/{user}.png?size=64" alt="" loading="lazy"'
            f' width="48" height="48">{user}</a></li>'
        )

    if not bubbles:
        return entries

    return [
        # A plain label rather than a heading: it names the row for sighted
        # readers without putting another entry per release into the table of
        # contents, which is what dropping the original heading achieved.
        '<p class="contributors-label">New contributors</p>',
        '<ul class="contributors" aria-label="New contributors">',
        *bubbles,
        "</ul>",
        "",
    ]


def on_page_markdown(markdown: str, page, config, files) -> str | None:
    """Wrap each release's "What's Changed" list in a collapsed `details` block."""
    markdown = _titled_callouts(markdown)
    if page.file.src_uri != "CHANGELOG.md":
        return markdown

    lines = markdown.splitlines()
    out: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        if CONTRIBUTORS_HEADING.match(line):
            index += 1
            entries: list[str] = []
            while index < len(lines):
                if ANY_HEADING.match(lines[index]) or FULL_CHANGELOG.match(lines[index]):
                    break
                if lines[index].strip():
                    entries.append(lines[index])
                index += 1
            out.extend(_contributor_bubbles(entries))
            continue

        if not CHANGES_HEADING.match(line):
            compare = COMPARE_LINK.match(line)
            out.append(_release_tags(compare) if compare else line)
            index += 1
            continue

        # Collect the list itself, stopping at whatever comes next in the release.
        index += 1
        body: list[str] = []
        while index < len(lines):
            if ANY_HEADING.match(lines[index]) or FULL_CHANGELOG.match(lines[index]):
                break
            body.append(lines[index])
            index += 1

        while body and not body[-1].strip():
            body.pop()

        out.append(f'??? {ADMONITION} "What\'s Changed"')
        out.append("")
        # `pymdownx.details` takes its content as an indented block.
        out.extend(f"    {entry}" if entry.strip() else "" for entry in body)
        out.append("")

    return "\n".join(out)
