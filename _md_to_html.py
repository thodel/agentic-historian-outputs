#!/usr/bin/env python3
"""Markdown-to-HTML converter for test fixtures. Strips frontmatter, resolves
Jekyll relative_url liquid tags, and wraps output in a minimal HTML document."""
import re
import sys
import markdown

content = sys.stdin.read()

# Strip YAML frontmatter
content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)

# Replace Jekyll relative_url liquid tags (single and double brace variants)
content = re.sub(r"\{\{ '/assets/([^']+)' \| relative_url \}\}", r'/assets/\1', content)
content = re.sub(r"\{\{\{ '/assets/([^']+)' \| relative_url \}\}\}", r'/assets/\1', content)

# Convert markdown to HTML
html = markdown.markdown(content)

# Wrap in minimal HTML document
doc = f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Test Fixture</title>
</head>
<body>
{html}
</body>
</html>"""
sys.stdout.write(doc)
