#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Simple data validator for Toolverse tools.yaml files."""

import re
from urllib.parse import urlparse

REQUIRED_FIELDS = ["name", "url", "description", "category"]
VALID_CATEGORIES = {
    "text", "image", "video", "audio",
    "workflow", "robotics", "multimodal", "other",
}

URL_REGEX = re.compile(r"^https?://")


def validate_tool(tool):
    """Validate a single tool dictionary."""
    # Rule 1: id must be unique - uniqueness should be checked externally
    # Rule 2: required fields must exist
    for field in REQUIRED_FIELDS:
        if not tool.get(field):
            return False, f"missing required field: {field}"

    # Rule 3: url must be valid
    url = tool["url"]
    if not URL_REGEX.match(url):
        return False, "invalid url"

    # Rule 4: category must be one of predefined categories
    if tool.get("category") not in VALID_CATEGORIES:
        return False, f"invalid category: {tool.get('category')}"

    # Rule 5: if open_source true, github_repo must be provided
    if tool.get("open_source") and not tool.get("github_repo"):
        return False, "open_source set but github_repo missing"

    # Rule 6: rating must be between 1 and 5 if provided
    if "experience" in tool and isinstance(tool["experience"], dict):
        rating = tool["experience"].get("rating")
        if rating is not None and not (1 <= float(rating) <= 5):
            return False, "rating out of range"

    return True, None


def main():
    import argparse
    import yaml
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Validate tools YAML file")
    parser.add_argument("path", help="Path to tools.yaml")
    args = parser.parse_args()

    data_path = Path(args.path)
    tools = yaml.safe_load(data_path.read_text())
    errors = []
    for idx, tool in enumerate(tools):
        valid, message = validate_tool(tool)
        if not valid:
            errors.append(f"Item {idx}: {message}")

    if errors:
        print("Validation failed:\n" + "\n".join(errors))
        exit(1)
    else:
        print("All tools validated successfully.")


if __name__ == "__main__":
    main()
