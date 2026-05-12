def count_lines(lines):
    return len(lines)


def count_words(lines):
    total = 0

    for line in lines:
        total += len(line.split())

    return total


def longest_line(lines):
    if not lines:
        return ""

    return max(lines, key=len).strip()