import sys

if __name__ == "__main__":
    with open("test_file.txt", "w") as f:
        f.write("This is a test file.\n")
        f.write(f"Argument received: {sys.argv[1]}\n")