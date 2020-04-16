#!/usr/bin/env python3

"""Sorts glossary entries in lexographic order."""

import re
import sys


class Entry:
    def __init__(self, term, fields):
        """Construct an Entry

        Keyword arguments:
        term -- glossary term
        fields -- dictionary of field types and values
        """
        self.term = term
        self.fields = fields

    def __lt__(self, other):
        return self.term < other.term


# Example:
# \newglossaryentry{agent}{
#   name={agent},
#   description={An independent actor being controlled through autonomy or
#     human-in-the-loop (e.g., a robot, aircraft, etc.).}
# }
entry_regex = re.compile(
    r"\\newglossaryentry \s* \{ (?P<term>[\w ]+) \} \s* \{", re.VERBOSE,
)

with open("glossary-entries.tex") as f:
    contents = f.read()

entries = []
for entry_match in entry_regex.finditer(contents):
    i = entry_match.end()
    brace_count = 1
    while brace_count > 0:
        if contents[i] == "{":
            brace_count += 1
        elif contents[i] == "}":
            brace_count -= 1
        if brace_count > 0:
            i += 1
    entry_contents = contents[entry_match.end() : i]

    fields = {}

    j = 0
    while j < len(entry_contents):
        for key_match in re.finditer(r"(\w+)\s*=\s*\{", entry_contents):
            key = key_match.group(1)
            value_start = i + key_match.end()
            brace_count = 1
            while brace_count > 0:
                print(f"entry_contents={entry_contents}")
                if entry_contents[i] == "{":
                    brace_count += 1
                elif entry_contents[i] == "}":
                    brace_count -= 1
                if brace_count > 0:
                    j += 1
            value = entry_contents[value_start:j]
            print("key=", key)
            print("value=", value)
            fields[key] = value

    entries.append(Entry(entry_match.group("term"), fields))
entries.sort()

# Write formatted bibliography entries back out
output = ""
for i, entry in enumerate(entries):
    if i != 0:
        output += "\n"

    output += "\\newglossaryentry{"
    output += f"{entry.term}"
    output += "}{\n"
    keys = sorted(entry.fields.keys())
    for j, key in enumerate(keys):
        output += f"  {key} = "
        output += "{"
        output += f"{entry.fields[key]}"
        output += "}"
        if j < len(keys) - 1:
            output += ",\n"
        else:
            output += "\n}\n"

with open("glossary-entries.tex", "w") as f:
    f.write(output)
