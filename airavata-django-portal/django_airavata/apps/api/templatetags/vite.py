"""Serve Vite build assets from Vite's native manifest.

Each page-bundle app's ``vite build`` writes ``<outDir>/.vite/manifest.json``.
These tags resolve a logical bundle name (the manifest entry's ``name``, which
equals the app's ``rollupOptions.input`` object key) to its emitted
``<script>`` / ``<link>`` tags. Apps are configured via ``settings.VITE_MANIFESTS``:
``{APP: {"manifest": <abs path>, "base": <public URL prefix>}}``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()


def _load(app: str) -> tuple[dict[str, Any], str]:
    cfg = settings.VITE_MANIFESTS[app]
    # ponytail: re-read per call; cache if render latency matters
    manifest: dict[str, Any] = json.loads(Path(cfg["manifest"]).read_text())
    base: str = cfg["base"]
    return manifest, base


def _entry(manifest: dict[str, Any], name: str, app: str) -> tuple[str, dict[str, Any]]:
    for key, chunk in manifest.items():
        if chunk.get("isEntry") and chunk.get("name") == name:
            return key, chunk
    raise ValueError(f"Vite entry {name!r} not found in {app} manifest")


@register.simple_tag
def vite_js(name: str, app: str) -> str:
    manifest, base = _load(app)
    _, chunk = _entry(manifest, name, app)
    # Only the entry file: the browser fetches its static imports itself (ESM).
    return mark_safe(f'<script type="module" src="{base}{chunk["file"]}"></script>')


@register.simple_tag
def vite_css(name: str, app: str) -> str:
    manifest, base = _load(app)
    key, _ = _entry(manifest, name, app)
    css: list[str] = []
    visited: set[str] = set()

    # Recurse imports first, then this chunk's own CSS, so shared-chunk CSS lands
    # before the entry's own CSS (preserves cascade), deduped across the closure.
    def walk(chunk_key: str) -> None:
        if chunk_key in visited:
            return
        visited.add(chunk_key)
        chunk = manifest.get(chunk_key)
        if chunk is None:
            return
        for imp in chunk.get("imports", []):
            walk(imp)
        for href in chunk.get("css", []):
            if href not in css:
                css.append(href)

    walk(key)
    return mark_safe(
        "\n".join(f'<link rel="stylesheet" href="{base}{href}">' for href in css)
    )
