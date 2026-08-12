import os
import argparse
import subprocess

def main():
    parser = argparse.ArgumentParser(description="Basic video extractor")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    
    # Simple extraction
    subprocess.run(["ffmpeg", "-i", args.input, "frame_%06d.png"])

if __name__ == "__main__":
    main()
