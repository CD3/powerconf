import pathlib
import re
import sys


def title_to_anchor(title: str):
    return title.lower().replace(" ", "-")


def main():
    markdown_file = sys.argv[1]
    markdown_file = pathlib.Path(markdown_file)

    patterns = ["^\s*(#+)( .*)$"]
    with markdown_file.open() as f:
        for line in f:
            line = line.strip()
            for pattern in patterns:
                m = re.match(pattern, line)
                if m:
                    level = m.group(1).strip()
                    title = m.group(2).strip()
                    anchor = title_to_anchor(title)
                    prefix = level.replace("#", "  ")
                    print(f"{prefix}- [{title}]({anchor})")


if __name__ == "__main__":
    main()
