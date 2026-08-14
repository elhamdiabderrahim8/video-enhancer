import os
import sys
import json
import time
import shutil
import subprocess
import threading
import platform
from pathlib import Path
from flask import Flask, render_template, jsonify, request, Response

app = Flask(__name__, template_folder='templates', static_folder='static')

# Global variable to hold the reference to the active process
current_process = None
process_lock = threading.Lock()
process_logs = []

def get_gpu_info():
    """Detect GPU devices on the system."""
    system = platform.system()
    gpus = []
    
    if system == "Linux":
        try:
            # Check lspci for common GPUs (Intel, NVIDIA, AMD)
            lspci_out = subprocess.check_output("lspci", shell=True, text=True)
            for line in lspci_out.splitlines():
                if "VGA compatible controller" in line or "3D controller" in line:
                    # Clean up string
                    gpu_name = line.split(": ")[-1].strip()
                    gpus.append(gpu_name)
        except Exception:
            pass
            
    elif system == "Darwin": # macOS
        try:
            system_profiler = subprocess.check_output(
                ["system_profiler", "SPDisplaysDataType"], text=True
            )
            for line in system_profiler.splitlines():
                if "Chipset Model" in line:
                    gpus.append(line.split(": ")[-1].strip())
        except Exception:
            pass
            
    elif system == "Windows":
        try:
            wmic_out = subprocess.check_output(
                "wmic path win32_VideoController get name", shell=True, text=True
            )
            lines = [line.strip() for line in wmic_out.splitlines() if line.strip()]
            if len(lines) > 1:
                gpus = lines[1:]
        except Exception:
            pass
            
    return gpus if gpus else ["Generic CPU Rendering (No dedicated GPU detected)"]

def get_cpu_info():
    """Detect CPU device on the system."""
    system = platform.system()
    if system == "Linux":
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line:
                        return line.split(":")[1].strip()
        except Exception:
            pass
    elif system == "Darwin":
        try:
            return subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
        except Exception:
            pass
    elif system == "Windows":
        try:
            wmic_out = subprocess.check_output("wmic cpu get name", shell=True, text=True)
            lines = [line.strip() for line in wmic_out.splitlines() if line.strip()]
            if len(lines) > 1:
                return lines[1]
        except Exception:
            pass
    return platform.processor() or "Unknown CPU"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/system-info', methods=['GET'])
def system_info():
    """Returns detected CPU, GPU, and checks if binary/ffmpeg are present."""
    gpus = get_gpu_info()
    cpu = get_cpu_info()
    
    # Check if FFmpeg is installed
    ffmpeg_installed = shutil.which("ffmpeg") is not None
    
    # Locate Real-ESRGAN binary
    # We check the local 'bin/' directory first
    base_dir = os.path.dirname(os.path.abspath(__file__))
    local_bin_path = os.path.join(base_dir, "bin", "realesrgan-ncnn-vulkan")
    
    # Check common fallback locations
    potential_paths = [
        local_bin_path,
        os.path.join(local_bin_path, "realesrgan-ncnn-vulkan"),
        "/home/abderrahim/Téléchargements/realesrgan-ncnn/realesrgan-ncnn-vulkan",
        "/home/abderrahim/Téléchargements/realesrgan-ncnn",
    ]
    
    real_esrgan_path = None
    for p in potential_paths:
        # Check both binary itself and folder containing it
        if os.path.isfile(p) and os.access(p, os.X_OK):
            real_esrgan_path = p
            break
        elif os.path.isdir(p):
            bin_file = os.path.join(p, "realesrgan-ncnn-vulkan")
            if os.path.isfile(bin_file) and os.access(bin_file, os.X_OK):
                real_esrgan_path = p
                break
                
    return jsonify({
        "cpu": cpu,
        "gpus": gpus,
        "ffmpeg": ffmpeg_installed,
        "esrgan_path": real_esrgan_path,
        "is_ready": ffmpeg_installed and (real_esrgan_path is not None)
    })

@app.route('/api/check-file', methods=['POST'])
def check_file():
    data = request.json
    path = data.get('path', '')
    exists = os.path.exists(path)
    is_file = os.path.isfile(path)
    
    suggested_output = ""
    duration = None
    nb_frames = None
    
    if exists and is_file:
        file_path = Path(path)
        suggested_output = str(file_path.parent / f"{file_path.stem}_enhanced{file_path.suffix}")
        
        # Extract video metadata
        try:
            # Get duration
            cmd_dur = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path]
            dur_str = subprocess.check_output(cmd_dur, text=True).strip()
            if dur_str:
                duration = float(dur_str)
            
            # Get FPS
            cmd_fps = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of", "default=noprint_wrappers=1:nokey=1", path]
            fps_str = subprocess.check_output(cmd_fps, text=True).strip()
            fps = 25.0
            if "/" in fps_str:
                num, den = map(int, fps_str.split("/"))
                if den > 0:
                    fps = num / den
            elif fps_str:
                fps = float(fps_str)
                
            if duration:
                nb_frames = int(duration * fps)
        except Exception as e:
            print(f"Error querying video metadata: {str(e)}")
        
    return jsonify({
        "exists": exists,
        "isFile": is_file,
        "suggested_output": suggested_output,
        "duration": duration,
        "nb_frames": nb_frames
    })

@app.route('/api/enhance', methods=['POST'])
def enhance():
    global current_process, process_logs
    data = request.json
    
    input_path = data.get('input_path')
    output_path = data.get('output_path')
    mode = data.get('mode', 'fast') # 'fast' or 'slow'
    device = data.get('device', 'gpu') # 'gpu' or 'cpu'
    esrgan_dir = data.get('esrgan_dir')
    
    # Determine the model based on mode
    model_name = "realesr-animevideov3-x4" if mode == "fast" else "realesrgan-x4plus"
    
    # Determine if GPU or CPU should be used
    # realesrgan uses -g -1 for CPU, and auto/0/1 for GPU
    # we default to gpu auto
    
    # Build run command
    base_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(base_dir, "enhance_video.py")
    
    cmd = [
        sys.executable, "-u", script_path,
        "--input", input_path,
        "--output", output_path,
        "--esrgan", esrgan_dir,
        "--model", model_name,
    ]
    
    # If the user forced CPU, we need to pass a special argument or let realesrgan handle it.
    # Currently enhance_video.py doesn't expose a gpu flag, let's make sure it handles -g options
    # We will modify enhance_video.py to accept --gpu flag
    if device == "cpu":
        cmd += ["--gpu", "-1"]
    else:
        cmd += ["--gpu", "0"]
        
    with process_lock:
        if current_process and current_process.poll() is None:
            return jsonify({"status": "error", "message": "Un processus d'amélioration est déjà en cours."}), 400
            
        process_logs = ["🚀 Démarrage du processus d'amélioration..."]
        try:
            current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
        except Exception as e:
            return jsonify({"status": "error", "message": f"Impossible de lancer le script: {str(e)}"}), 500
            
    return jsonify({"status": "success", "message": "Amélioration lancée ! Lisez les logs pour suivre l'avancement."})

@app.route('/api/cancel', methods=['POST'])
def cancel():
    global current_process
    with process_lock:
        if current_process and current_process.poll() is None:
            current_process.terminate()
            current_process.wait()
            return jsonify({"status": "success", "message": "Processus annulé par l'utilisateur."})
        return jsonify({"status": "error", "message": "Aucun processus en cours."}), 400

@app.route('/api/logs-stream')
def logs_stream():
    """Stream subprocess logs to frontend using Server-Sent Events (SSE)."""
    def generate():
        global current_process, process_logs
        # First send historical logs
        for log in list(process_logs):
            yield f"data: {json.dumps({'log': log})}\n\n"
            
        while True:
            if current_process is None:
                break
                
            line = current_process.stdout.readline()
            if not line:
                if current_process.poll() is not None:
                    # Process completed
                    code = current_process.returncode
                    status = "success" if code == 0 else "failed"
                    msg = f"🎉 Processus terminé avec le code {code}." if code == 0 else f"❌ Le processus a échoué avec le code {code}."
                    yield f"data: {json.dumps({'log': msg, 'status': status})}\n\n"
                    break
                time.sleep(0.5)
                continue
                
            stripped = line.strip()
            if stripped:
                process_logs.append(stripped)
                # Keep log size reasonable
                if len(process_logs) > 500:
                    process_logs.pop(0)
                yield f"data: {json.dumps({'log': stripped})}\n\n"
                
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    # Parse port from command line if any
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    app.run(host='0.0.0.0', port=port, debug=False)
