def read_notes(file_path):
    with open(file_path, "r") as file:
        return file.readlines()