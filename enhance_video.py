import os
import argparse

def main():
    parser = argparse.ArgumentParser(description="Basic video extractor")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(f"Processing {args.input}...")

if __name__ == "__main__":
    main()
