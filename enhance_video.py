import os
import argparse
import subprocess

def main():
    parser = argparse.ArgumentParser(description="AI video upscaler")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--esrgan", required=True)
    args = parser.parse_args()
    
    subprocess.run(["ffmpeg", "-i", args.input, "frame_%06d.png"])
    # Run Real-ESRGAN
    subprocess.run([os.path.join(args.esrgan, "realesrgan-ncnn-vulkan"), "-i", "original_frames", "-o", "enhanced_frames"])

if __name__ == "__main__":
    main()
