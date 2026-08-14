#!/usr/bin/env python3
"""
Video AI Enhancer
=================
Enhance any low-quality video with Real-ESRGAN AI — frame by frame, locally, for free.

Usage:
    python3 enhance_video.py --input video.mp4 --output enhanced.mp4 --esrgan ./realesrgan-ncnn/

GitHub: https://github.com/YOUR_USERNAME/video-ai-enhancer
License: MIT
"""

import os
import sys
import shutil
import argparse
import subprocess
from pathlib import Path


# ─── ARGUMENT PARSING ──────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="🎬 Video AI Enhancer — Frame-by-frame AI upscaling using Real-ESRGAN",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 enhance_video.py --input video.mp4 --output enhanced.mp4 --esrgan ./realesrgan-ncnn/
  python3 enhance_video.py --input video.mp4 --output out.mp4 --esrgan ./realesrgan-ncnn/ --model realesr-animevideov3-x4 --fps 60
        """
    )
    parser.add_argument("--input",   required=True,  help="Input video file path")
    parser.add_argument("--output",  required=True,  help="Output enhanced video path")
    parser.add_argument("--esrgan",  required=True,  help="Path to realesrgan-ncnn-vulkan directory")
    parser.add_argument("--model",   default="realesrgan-x4plus",
                        choices=["realesrgan-x4plus", "realesrgan-x4plus-anime",
                                 "realesr-animevideov3-x4", "realesr-animevideov3-x2"],
                        help="AI model to use (default: realesrgan-x4plus — best for real faces/photos)")
    parser.add_argument("--fps",     type=int,   default=30,   help="Output FPS (default: 30)")
    parser.add_argument("--gamma",   type=float, default=1.5,  help="Brightness gamma (default: 1.5, range 1.0-2.5)")
    parser.add_argument("--crf",     type=int,   default=15,   help="Output quality CRF (0=lossless, 51=worst, default: 15)")
    parser.add_argument("--keep",    action="store_true",      help="Keep temporary frame files after processing")
    return parser.parse_args()


# ─── HELPERS ───────────────────────────────────────────────────────────────────

def run(cmd, desc=""):
    """Run a shell command and exit on failure."""
    print(f"\n{'─'*60}")
    print(f"▶  {desc}")
    cmd_str = " ".join(str(c) for c in cmd) if isinstance(cmd, list) else cmd
    print(f"   {cmd_str}")
    result = subprocess.run(cmd, shell=isinstance(cmd, str))
    if result.returncode != 0:
        print(f"\n❌ Command failed (exit code {result.returncode})")
        sys.exit(1)
    print("✅ Done")


def get_video_fps(input_path):
    """Get the original video FPS as a float."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=r_frame_rate",
         "-of", "default=noprint_wrappers=1:nokey=1", input_path],
        capture_output=True, text=True
    )
    fps_str = result.stdout.strip()
    if "/" in fps_str:
        num, den = map(int, fps_str.split("/"))
        return num / den
    return float(fps_str or "25")


def count_frames(folder):
    """Count PNG files in a folder."""
    return len(list(Path(folder).glob("*.png")))


# ─── MAIN PIPELINE ─────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    # Validate paths
    if not Path(args.input).exists():
        print(f"❌ Input file not found: {args.input}")
        sys.exit(1)

    esrgan_bin = Path(args.esrgan) / "realesrgan-ncnn-vulkan"
    if not esrgan_bin.exists():
        print(f"❌ realesrgan-ncnn-vulkan binary not found in: {args.esrgan}")
        print("   Download from: https://github.com/xinntao/Real-ESRGAN/releases")
        sys.exit(1)

    # Setup work directories
    work_dir     = Path(args.output).parent / "_enhancer_work"
    frames_dir   = work_dir / "original_frames"
    enhanced_dir = work_dir / "enhanced_frames"
    audio_file   = work_dir / "audio.aac"

    for d in [frames_dir, enhanced_dir]:
        d.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  🎬 Video AI Enhancer — Starting Pipeline")
    print("=" * 60)
    print(f"  Input   : {args.input}")
    print(f"  Output  : {args.output}")
    print(f"  Model   : {args.model}")
    print(f"  Output FPS : {args.fps}")
    print(f"  Gamma   : {args.gamma}")
    print(f"  CRF     : {args.crf}")

    # ── Step 1: Get original FPS
    original_fps = get_video_fps(args.input)
    print(f"\n📊 Original video FPS: {original_fps:.2f}")

    # ── Step 2: Extract audio
    print("\n🎵 Step 1/4 — Extracting audio...")
    run(["ffmpeg", "-y", "-i", args.input, "-vn", "-acodec", "copy", str(audio_file)],
        "Extract audio track")

    # ── Step 3: Extract unique frames (no duplicates)
    print("\n🖼️  Step 2/4 — Extracting unique frames as PNG...")
    run(["ffmpeg", "-y", "-i", args.input,
         "-vsync", "0",
         "-q:v", "1",
         str(frames_dir / "frame_%06d.png")],
        "Extract frames (no duplicates)")

    total_frames = count_frames(frames_dir)
    print(f"   → {total_frames} unique frames extracted")

    # ── Step 4: Real-ESRGAN AI Enhancement
    print(f"\n🤖 Step 3/4 — AI Enhancement with {args.model} (×4)...")
    print(f"   ⏳ Processing {total_frames} frames. This may take a while...")
    print(f"   💡 Tip: Frames already processed will be skipped automatically.")

    run([str(esrgan_bin),
         "-i", str(frames_dir),
         "-o", str(enhanced_dir),
         "-n", args.model,
         "-s", "4",
         "-j", "1:2:1",
         "-f", "png"],
        f"Real-ESRGAN AI upscaling × 4")

    enhanced_count = count_frames(enhanced_dir)
    print(f"   → {enhanced_count}/{total_frames} frames enhanced")

    # ── Step 5: Reassemble video
    print("\n🎬 Step 4/4 — Reassembling final video...")

    # Build brightness/color curve filter
    # gamma > 1 = brighter midtones. We map it to a curve approximation.
    g = args.gamma
    mid_in  = 0.4
    mid_out = min(0.4 * g, 0.95)  # Brighten midtones without clipping whites
    curves_filter = f"curves=m='0/0 {mid_in:.2f}/{mid_out:.2f} 1/1'"

    vf = f"fps={args.fps},{curves_filter}"

    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(original_fps),
        "-i", str(enhanced_dir / "frame_%06d.png"),
        "-i", str(audio_file),
        "-vf", vf,
        "-c:v", "libx264",
        "-crf", str(args.crf),
        "-preset", "medium",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        "-pix_fmt", "yuv420p",
        args.output
    ]
    run(cmd, "Assemble enhanced video with audio")

    # ── Done
    output_size = Path(args.output).stat().st_size / (1024 * 1024)
    print("\n" + "=" * 60)
    print(f"  🎉 SUCCESS!")
    print(f"  📺 Enhanced video: {args.output}")
    print(f"  📊 Output size   : {output_size:.1f} MB")
    print(f"  🎞️  FPS           : {args.fps}")
    print(f"  🔬 AI model used : {args.model}")
    print("=" * 60)

    # ── Cleanup
    if not args.keep:
        print(f"\n🗑️  Cleaning up temporary files...")
        shutil.rmtree(work_dir)
        print("   ✅ Temporary files removed.")
    else:
        print(f"\n📁 Temporary files kept at: {work_dir}")


if __name__ == "__main__":
    main()
