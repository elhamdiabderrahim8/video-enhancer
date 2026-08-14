document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const inputPathEl = document.getElementById('input_path');
    const outputPathEl = document.getElementById('output_path');
    const modeFastBtn = document.getElementById('mode_fast');
    const modeSlowBtn = document.getElementById('mode_slow');
    const deviceGpuBtn = document.getElementById('device_gpu');
    const deviceCpuBtn = document.getElementById('device_cpu');
    const gammaSlider = document.getElementById('gamma');
    const gammaValEl = document.getElementById('gamma_val');
    const crfSlider = document.getElementById('crf');
    const crfValEl = document.getElementById('crf_val');
    const btnAction = document.getElementById('btn_action');
    const consoleEl = document.getElementById('console');
    const progressBarContainer = document.getElementById('progress_container');
    const progressBar = document.getElementById('progress_bar');
    
    // Status Indicators
    const cpuValEl = document.getElementById('cpu_val');
    const gpuValEl = document.getElementById('gpu_val');
    const ffmpegStatusEl = document.getElementById('ffmpeg_status');
    const esrganStatusEl = document.getElementById('esrgan_status');
    
    // Estimate Badge Elements
    const estimateValEl = document.getElementById('estimate_value');
    
    // Application State
    let state = {
        inputPath: '',
        outputPath: '',
        mode: 'fast', // 'fast' | 'slow'
        device: 'gpu', // 'gpu' | 'cpu'
        gamma: 1.5,
        crf: 15,
        systemReady: false,
        processing: false,
        totalFrames: 300, // Fallback default
        esrganPath: null,
        eventSource: null
    };

    // Initialize System Information
    async function loadSystemInfo() {
        try {
            addLogLine('🔍 Diagnostic matériel en cours...', 'system');
            const res = await fetch('/api/system-info');
            const data = await res.json();
            
            cpuValEl.textContent = data.cpu || 'Non détecté';
            gpuValEl.textContent = data.gpus.join(' / ') || 'Non détecté';
            
            // FFmpeg Status
            if (data.ffmpeg) {
                ffmpegStatusEl.innerHTML = '<span class="status-indicator ready"></span> Installé';
            } else {
                ffmpegStatusEl.innerHTML = '<span class="status-indicator error"></span> Manquant';
                addLogLine('⚠️ Avertissement : FFmpeg est requis pour le bon fonctionnement.', 'error');
            }
            
            // Real-ESRGAN Status
            if (data.esrgan_path) {
                esrganStatusEl.innerHTML = '<span class="status-indicator ready"></span> Détecté';
                state.esrganPath = data.esrgan_path;
            } else {
                esrganStatusEl.innerHTML = '<span class="status-indicator error"></span> Introuvable';
                addLogLine('⚠️ Avertissement : répertoires ou binaire Real-ESRGAN introuvables.', 'error');
            }
            
            state.systemReady = data.is_ready;
            updateActionButtonState();
            updateEstimations();
            
        } catch (err) {
            addLogLine('❌ Erreur lors du chargement des informations système : ' + err.message, 'error');
        }
    }

    // Add line to console
    function addLogLine(text, type = 'info') {
        const line = document.createElement('div');
        line.className = `log-entry ${type}`;
        line.textContent = `[${new Date().toLocaleTimeString()}] ${text}`;
        consoleEl.appendChild(line);
        consoleEl.scrollTop = consoleEl.scrollHeight;
    }

    // Clear console
    function clearConsole() {
        consoleEl.innerHTML = '';
    }

    // Toggle Buttons Management
    modeFastBtn.addEventListener('click', () => {
        state.mode = 'fast';
        modeFastBtn.classList.add('active');
        modeSlowBtn.classList.remove('active');
        updateEstimations();
    });

    modeSlowBtn.addEventListener('click', () => {
        state.mode = 'slow';
        modeSlowBtn.classList.add('active');
        modeFastBtn.classList.remove('active');
        updateEstimations();
    });

    deviceGpuBtn.addEventListener('click', () => {
        state.device = 'gpu';
        deviceGpuBtn.classList.add('active');
        deviceCpuBtn.classList.remove('active');
        updateEstimations();
    });

    deviceCpuBtn.addEventListener('click', () => {
        state.device = 'cpu';
        deviceCpuBtn.classList.add('active');
        deviceGpuBtn.classList.remove('active');
        updateEstimations();
    });

    // Slider Listeners
    gammaSlider.addEventListener('input', (e) => {
        state.gamma = parseFloat(e.target.value);
        gammaValEl.textContent = state.gamma.toFixed(1);
    });

    crfSlider.addEventListener('input', (e) => {
        state.crf = parseInt(e.target.value);
        crfValEl.textContent = state.crf;
    });

    // File Input Validation and Auto Output Naming
    let checkTimeout;
    inputPathEl.addEventListener('input', (e) => {
        clearTimeout(checkTimeout);
        const path = e.target.value.trim();
        state.inputPath = path;
        
        if (path === '') {
            outputPathEl.value = '';
            state.outputPath = '';
            updateActionButtonState();
            return;
        }
        
        // Debounce file check to avoid hitting the endpoint too fast
        checkTimeout = setTimeout(async () => {
            try {
                const res = await fetch('/api/check-file', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ path: path })
                });
                const data = await res.json();
                
                if (data.exists && data.isFile) {
                    outputPathEl.value = data.suggested_output;
                    state.outputPath = data.suggested_output;
                    addLogLine(`📁 Vidéo d'entrée détectée : ${path}`, 'success');
                    
                    // Attempt to parse duration and frames for better estimation
                    if (data.duration && data.nb_frames) {
                        state.totalFrames = data.nb_frames;
                    }
                    updateEstimations();
                } else {
                    addLogLine(`⚠️ Le chemin d'entrée n'existe pas ou n'est pas un fichier valide.`, 'error');
                }
                updateActionButtonState();
            } catch (err) {
                console.error(err);
            }
        }, 500);
    });

    outputPathEl.addEventListener('input', (e) => {
        state.outputPath = e.target.value.trim();
        updateActionButtonState();
    });

    // Estimate processing time
    function updateEstimations() {
        // Benchmarks per frame in seconds
        // Fast GPU = 0.5s, CPU = 12s
        // Slow GPU = 67s, CPU = 300s
        let timePerFrame = 0;
        
        if (state.mode === 'fast') {
            timePerFrame = state.device === 'gpu' ? 0.5 : 12;
        } else {
            timePerFrame = state.device === 'gpu' ? 67 : 300;
        }
        
        const totalSeconds = state.totalFrames * timePerFrame;
        const minutes = Math.floor(totalSeconds / 60);
        const hours = Math.floor(minutes / 60);
        const remMinutes = minutes % 60;
        
        let displayStr = '';
        if (hours > 0) {
            displayStr = `~${hours}h ${remMinutes}m`;
        } else if (minutes > 0) {
            displayStr = `~${minutes}m`;
        } else {
            displayStr = `~${Math.round(totalSeconds)}s`;
        }
        
        // Add a notice if CPU and slow mode is selected
        if (state.device === 'cpu' && state.mode === 'slow') {
            displayStr += ' ⚠️ Extrêmement long en CPU !';
        }
        
        estimateValEl.textContent = `${displayStr} (${state.totalFrames} frames)`;
    }

    // Action button state
    function updateActionButtonState() {
        const canStart = state.systemReady && state.inputPath && state.outputPath && !state.processing;
        btnAction.disabled = !canStart;
    }

    // Start/Cancel Action
    btnAction.addEventListener('click', async () => {
        if (state.processing) {
            // Cancel Action
            cancelEnhancement();
        } else {
            // Start Action
            startEnhancement();
        }
    });

    async function startEnhancement() {
        clearConsole();
        addLogLine('🚀 Lancement de l\'amélioration vidéo...', 'info');
        
        state.processing = true;
        btnAction.textContent = '⏹️ Annuler le traitement';
        btnAction.classList.add('btn-cancel');
        btnAction.classList.add('pulse-glow');
        progressBarContainer.style.display = 'block';
        progressBar.style.width = '0%';
        
        try {
            const res = await fetch('/api/enhance', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    input_path: state.inputPath,
                    output_path: state.outputPath,
                    mode: state.mode,
                    device: state.device,
                    esrgan_dir: state.esrganPath
                })
            });
            const data = await res.json();
            
            if (data.status === 'success') {
                addLogLine(data.message, 'success');
                setupLogsStream();
            } else {
                addLogLine('❌ Échec du lancement : ' + data.message, 'error');
                resetUIState();
            }
        } catch (err) {
            addLogLine('❌ Erreur de connexion : ' + err.message, 'error');
            resetUIState();
        }
    }

    async function cancelEnhancement() {
        addLogLine('⏹️ Demande d\'annulation...', 'warning');
        try {
            const res = await fetch('/api/cancel', { method: 'POST' });
            const data = await res.json();
            addLogLine(data.message, 'system');
        } catch (err) {
            addLogLine('❌ Erreur lors de l\'annulation : ' + err.message, 'error');
        }
        resetUIState();
    }

    function setupLogsStream() {
        if (state.eventSource) {
            state.eventSource.close();
        }
        
        state.eventSource = new EventSource('/api/logs-stream');
        
        state.eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            // Determine log entry type based on content
            let logType = 'info';
            if (data.log.includes('❌') || data.log.includes('failed') || data.log.includes('Command failed')) {
                logType = 'error';
            } else if (data.log.includes('🎉') || data.log.includes('SUCCESS') || data.log.includes('success')) {
                logType = 'success';
            } else if (data.log.includes('Step') || data.log.includes('Starting')) {
                logType = 'info';
            } else if (data.log.startsWith('frame=') || data.log.includes('%')) {
                logType = 'system';
                // Try to parse progress
                parseProgress(data.log);
            }
            
            addLogLine(data.log, logType);
            
            // Check process completion
            if (data.status === 'success' || data.status === 'failed') {
                state.eventSource.close();
                resetUIState();
            }
        };
        
        state.eventSource.onerror = () => {
            state.eventSource.close();
            resetUIState();
        };
    }

    function parseProgress(logLine) {
        // Parse frame count if present (e.g. "frame=  120 fps=..." or "16/302 frames enhanced")
        if (logLine.includes('frames enhanced')) {
            const match = logLine.match(/(\d+)\/(\d+)/);
            if (match) {
                const current = parseInt(match[1]);
                const total = parseInt(match[2]);
                updateProgress(current, total);
            }
        } else if (logLine.startsWith('frame=')) {
            // FFmpeg standard output progress
            const match = logLine.match(/frame=\s*(\d+)/);
            if (match) {
                const current = parseInt(match[1]);
                // Estimating based on total expected frames
                updateProgress(current, state.totalFrames);
            }
        }
    }

    function updateProgress(current, total) {
        const percent = Math.min(Math.round((current / total) * 100), 100);
        progressBar.style.width = `${percent}%`;
        progressBar.setAttribute('title', `${percent}% (${current}/${total})`);
    }

    function resetUIState() {
        state.processing = false;
        btnAction.textContent = '🚀 Lancer l\'amélioration';
        btnAction.className = 'btn-action';
        btnAction.classList.remove('pulse-glow');
        progressBarContainer.style.display = 'none';
        updateActionButtonState();
    }

    // Load initial info
    loadSystemInfo();
});
