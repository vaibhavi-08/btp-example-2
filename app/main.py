from reader import read_notes
from analyzer import count_lines, count_words, longest_line


def main():
    file_path = "data/notes.txt"

    lines = read_notes(file_path)

    print(f"Total lines: {count_lines(lines)}")
    print(f"Total words: {count_words(lines)}")
    print(f"Longest line: {longest_line(lines)}")


if __name__ == "__main__":
    main()