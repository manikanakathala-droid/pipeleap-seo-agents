"""Convert config.yaml from flow mapping to block-style YAML."""

import ast
import re
import yaml


def main():
    path = "config.yaml"
    with open(path, encoding="utf-8") as f:
        content = f.read()

    # Remove comment lines
    content = re.sub(r"(?m)^[ \t]*#.*\n?", "", content)

    # Remove inline comments after , or {
    content = re.sub(r",\s*#.*", ",", content)
    content = re.sub(r"\{\s*#.*", "{", content)

    # Replace single-quote strings with double-quote (Python dict style allows both)
    # This is needed because ast.literal_eval requires strings to be quoted

    # Try to parse as Python literal (handles trailing commas)
    try:
        data = ast.literal_eval(content)
    except SyntaxError as e:
        print(f"Parse error: {e}")
        # Show the problematic area
        lines = content.split("\n")
        if e.lineno:
            for i in range(max(0, e.lineno - 3), min(len(lines), e.lineno + 3)):
                print(f"  {i+1}: {lines[i]}")
        return

    print(f"Parsed OK. Top keys: {list(data.keys())}")

    # Write as block-style YAML
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # Validate
    with open(path, encoding="utf-8") as f:
        validated = yaml.safe_load(f)
    print(f"Validated OK. Top keys: {list(validated.keys())}")
    print("config.yaml converted to block-style YAML successfully.")


if __name__ == "__main__":
    main()
