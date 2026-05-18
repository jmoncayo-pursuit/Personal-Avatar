import re
from pathlib import Path

TARGET = Path(__file__).parent / "webapp.py"
content = TARGET.read_text(encoding="utf-8")

NEW_INDEX_HTML = r'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Avatar Clone Studio Wizard</title>
  <style>
    :root {
      --bg: #fdfcfa;
      --panel: #ffffff;
      --ink: #1f2937;
      --muted: #6b7280;
      --line: #e5e7eb;
      --accent: #0f766e;
      --accent-hover: #0d645d;
      --good: #166534;
      --bad: #991b1b;
      --shadow: 0 10px 25px rgba(0,0,0,0.05);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      color: var(--ink);
      background: var(--bg);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding-top: 40px;
    }
    .wizard-container {
      width: min(800px, calc(100% - 32px));
      background: var(--panel);
      border-radius: 20px;
      box-shadow: var(--shadow);
      border: 1px solid var(--line);
      overflow: hidden;
    }
    .header {
      padding: 30px;
      border-bottom: 1px solid var(--line);
      text-align: center;
      background: #fafaf9;
    }
    .header h1 { margin: 0; font-size: 1.8rem; font-weight: 600; letter-spacing: -0.02em; }
    .header p { margin: 8px 0 0; color: var(--muted); }
    
    .progress {
      display: flex;
      padding: 20px 30px;
      background: white;
      border-bottom: 1px solid var(--line);
      gap: 8px;
    }
    .step-dot {
      flex: 1;
      height: 6px;
      background: var(--line);
      border-radius: 3px;
      transition: background 0.3s;
    }
    .step-dot.active { background: var(--accent); }
    .step-dot.done { background: #99f6e4; }
    
    .step-pane {
      display: none;
      padding: 30px;
      animation: fadein 0.3s;
    }
    .step-pane.active { display: block; }
    
    @keyframes fadein { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    
    h2 { margin: 0 0 12px; font-size: 1.4rem; font-weight: 600; }
    p.desc { margin: 0 0 24px; color: var(--muted); line-height: 1.5; }
    
    .card-choice {
      border: 2px solid var(--line);
      border-radius: 12px;
      padding: 20px;
      cursor: pointer;
      margin-bottom: 16px;
      transition: all 0.2s;
    }
    .card-choice:hover { border-color: #99f6e4; background: #f0fdfa; }
    .card-choice.selected { border-color: var(--accent); background: #f0fdfa; box-shadow: 0 4px 12px rgba(15,118,110,0.1); }
    .card-title { font-weight: 600; font-size: 1.1rem; margin-bottom: 6px; }
    .card-sub { color: var(--muted); font-size: 0.9rem; line-height: 1.4; }
    
    .asset-staged {
      background: #f8fafc;
      border: 1px dashed #cbd5e1;
      padding: 20px;
      border-radius: 12px;
      margin-bottom: 20px;
      text-align: center;
    }
    .asset-staged img, .asset-staged video { max-width: 100%; max-height: 300px; border-radius: 8px; margin-top: 10px; }
    .asset-staged audio { width: 100%; margin-top: 10px; }
    
    label { display: block; font-weight: 500; margin-bottom: 8px; font-size: 0.95rem; }
    input[type="file"], input[type="text"], textarea {
      width: 100%; border: 1px solid var(--line); border-radius: 8px; padding: 12px; font: inherit; margin-bottom: 16px;
    }
    textarea { min-height: 120px; resize: vertical; }
    
    .nav-buttons {
      display: flex;
      justify-content: space-between;
      padding: 20px 30px;
      background: #fafaf9;
      border-top: 1px solid var(--line);
    }
    button {
      appearance: none; border: 0; border-radius: 8px; padding: 12px 24px; font-weight: 600; font-size: 1rem;
      cursor: pointer; transition: all 0.2s;
    }
    button:disabled { opacity: 0.5; cursor: not-allowed; }
    .btn-back { background: transparent; color: var(--muted); border: 1px solid var(--line); }
    .btn-back:hover:not(:disabled) { background: white; color: var(--ink); }
    .btn-next { background: var(--accent); color: white; }
    .btn-next:hover:not(:disabled) { background: var(--accent-hover); }
    
    .row { display: flex; gap: 10px; margin-bottom: 16px; align-items: center; }
    .status { padding: 12px; border-radius: 8px; margin-bottom: 16px; display: none; }
    .status.show { display: block; }
    .status.good { background: #dcfce7; color: #166534; }
    .status.bad { background: #fee2e2; color: #991b1b; }
    .logs { background: #111827; color: #e5e7eb; padding: 16px; border-radius: 8px; font-family: monospace; font-size: 0.85rem; max-height: 200px; overflow-y: auto; margin-top: 16px; white-space: pre-wrap; }
    .fine { font-size: 0.85rem; color: var(--muted); }
    .hidden { display: none !important; }
  </style>
</head>
<body>
  <div class="wizard-container">
    <div class="header">
      <h1>Avatar Studio Wizard</h1>
      <p>Create your talking head in 4 easy steps.</p>
    </div>
    
    <div class="progress" id="progress-bar">
      <div class="step-dot active" id="dot-1"></div>
      <div class="step-dot" id="dot-2"></div>
      <div class="step-dot" id="dot-3"></div>
      <div class="step-dot" id="dot-4"></div>
      <div class="step-dot" id="dot-5"></div>
    </div>
    
    <!-- STEP 1: STYLE -->
    <div class="step-pane active" id="step-1">
      <h2>1. Choose Style</h2>
      <p class="desc">How do you want your avatar to behave?</p>
      
      <div class="card-choice selected" id="choice-sadtalker" onclick="setStyle('sadtalker')">
        <div class="card-title">Standard (SadTalker)</div>
        <div class="card-sub">Simple lip-sync on a still portrait. Fast and clean.</div>
      </div>
      
      <div class="card-choice" id="choice-liveportrait" onclick="setStyle('liveportrait')">
        <div class="card-title">Dynamic (LivePortrait)</div>
        <div class="card-sub">Highly realistic. Transfers expressions and head movement from a short webcam clip.</div>
      </div>
    </div>

    <!-- STEP 2: VOICE -->
    <div class="step-pane" id="step-2">
      <h2>2. Voice Reference</h2>
      <p class="desc">The AI needs to hear your voice to clone it.</p>
      
      <div id="staged-voice-area" class="asset-staged hidden">
        <strong>Ready: Pre-recorded Voice</strong>
        <audio id="staged-voice-player" controls></audio>
        <div class="fine" style="margin-top: 8px;">We'll use this clip. To use a different one, upload or record below.</div>
      </div>
      
      <div style="border: 1px solid var(--line); padding: 20px; border-radius: 12px;">
        <label>Provide New Voice</label>
        <div class="row">
          <button type="button" class="btn-back" onclick="document.getElementById('voice-file').click()">Upload Audio</button>
          <span>or</span>
          <button type="button" class="btn-back" id="voice-record-btn">Record Webcam Audio</button>
        </div>
        <input type="file" id="voice-file" accept="audio/*" class="hidden">
        <span id="voice-file-name" class="fine"></span>
        
        <div id="voice-record-ui" class="hidden" style="margin-top: 16px;">
          <div class="row">
            <button id="voice-stop-btn" type="button" class="btn-back" style="color:red;" disabled>Stop Recording</button>
            <span id="voice-timer"></span>
          </div>
        </div>
        
        <div style="margin-top: 16px;">
          <label>Exact Transcript of the Audio</label>
          <textarea id="voice-transcript" placeholder="Type exactly what is said in the clip..."></textarea>
          <button type="button" class="btn-back" id="btn-prep-voice">Prepare Voice File</button>
          <div id="voice-prep-status" class="status" style="margin-top:12px;"></div>
        </div>
      </div>
    </div>

    <!-- STEP 3: PORTRAIT -->
    <div class="step-pane" id="step-3">
      <h2>3. Portrait Image</h2>
      <p class="desc">Provide a clear, front-facing headshot.</p>
      
      <div id="staged-portrait-area" class="asset-staged hidden">
        <strong>Ready: Staged Portrait</strong>
        <img id="staged-portrait-preview" src="">
        <div class="fine" style="margin-top: 8px;">We'll use this image. To use a different one, upload below.</div>
      </div>
      
      <div style="border: 1px solid var(--line); padding: 20px; border-radius: 12px;">
        <label>Upload New Portrait</label>
        <input type="file" id="portrait-file" accept="image/*">
        <img id="new-portrait-preview" class="hidden" style="max-width: 100%; max-height: 300px; border-radius: 8px; margin-top: 10px;">
      </div>
    </div>

    <!-- STEP 4: DRIVING VIDEO (LivePortrait ONLY) -->
    <div class="step-pane" id="step-4">
      <h2>4. Driving Video</h2>
      <p class="desc">A 5-second video of yourself blinking and looking around naturally.</p>
      
      <div id="staged-driving-area" class="asset-staged hidden">
        <strong>Ready: Staged Driving Video</strong>
        <video id="staged-driving-player" controls loop muted playsinline></video>
        <div class="fine" style="margin-top: 8px;">We'll use this video. To use a different one, provide it below.</div>
      </div>
      
      <div style="border: 1px solid var(--line); padding: 20px; border-radius: 12px;">
        <label>Provide New Driving Video</label>
        <div class="row">
          <button type="button" class="btn-back" onclick="document.getElementById('driving-file').click()">Upload Video</button>
          <span>or</span>
          <button type="button" class="btn-back" id="driving-record-btn">Record via Webcam</button>
        </div>
        <input type="file" id="driving-file" accept="video/*" class="hidden">
        <span id="driving-file-name" class="fine"></span>
        
        <div id="driving-record-ui" class="hidden" style="margin-top: 16px;">
          <video id="driving-webcam-preview" autoplay muted playsinline style="width:100%; border-radius:8px; transform: scaleX(-1); border:2px solid #cbd5e1;"></video>
          <div class="row" style="margin-top: 12px;">
            <button id="driving-stop-btn" type="button" class="btn-back" style="color:red;">Stop Recording</button>
            <span id="driving-timer"></span>
          </div>
        </div>
        
        <video id="new-driving-preview" controls hidden style="width: 100%; border-radius: 8px; margin-top: 12px;"></video>
      </div>
    </div>

    <!-- STEP 5: RENDER -->
    <div class="step-pane" id="step-5">
      <h2>5. Speech & Generate</h2>
      <p class="desc">What should your avatar say?</p>
      
      <textarea id="render-text" placeholder="Hello, I am a digital avatar. Nice to meet you!"></textarea>
      
      <div id="render-status" class="status"></div>
      <div id="render-output" class="hidden" style="text-align: center; margin-bottom: 20px;">
        <!-- Player injected here -->
      </div>
      <div id="render-logs" class="logs hidden"></div>
    </div>

    <!-- NAVIGATION -->
    <div class="nav-buttons">
      <button id="btn-back" class="btn-back" onclick="goBack()" disabled>Back</button>
      <button id="btn-next" class="btn-next" onclick="goNext()">Next</button>
    </div>
  </div>

  <script>
    // --- WIZARD STATE ---
    let currentStep = 1;
    let maxSteps = 5;
    let selectedStyle = "sadtalker";
    
    // Globals for assets
    let isVoicePrepared = false;
    let stagedVoicePath = "";
    let stagedTranscriptPath = "";
    let stagedPortraitPath = "";
    let stagedDrivingPath = "";
    
    // Recorders
    let voiceRecorder = null;
    let voiceStream = null;
    let voiceChunks = [];
    let voiceFile = null;
    
    let drivingRecorder = null;
    let drivingStream = null;
    let drivingChunks = [];
    let drivingFile = null;

    // --- INIT ---
    async function init() {
      const res = await fetch("/api/defaults");
      const data = await res.json();
      
      if (data.staged_audio_url && data.staged_transcript_path) {
        document.getElementById("staged-voice-area").classList.remove("hidden");
        document.getElementById("staged-voice-player").src = data.staged_audio_url;
        document.getElementById("voice-transcript").value = data.staged_transcript_content || "";
        isVoicePrepared = true;
        stagedVoicePath = data.staged_audio_path;
        stagedTranscriptPath = data.staged_transcript_path;
      }
      
      if (data.default_portrait_url) {
        document.getElementById("staged-portrait-area").classList.remove("hidden");
        document.getElementById("staged-portrait-preview").src = data.default_portrait_url;
        stagedPortraitPath = data.default_portrait_path;
      }
      
      if (data.staged_driving_url) {
        document.getElementById("staged-driving-area").classList.remove("hidden");
        document.getElementById("staged-driving-player").src = data.staged_driving_url;
        stagedDrivingPath = data.staged_driving_path;
      }
      
      if (!document.getElementById("voice-transcript").value && data.reference_script) {
        document.getElementById("voice-transcript").value = data.reference_script;
      }
      
      updateUI();
    }
    
    // --- NAVIGATION ---
    function setStyle(style) {
      selectedStyle = style;
      document.getElementById("choice-sadtalker").classList.remove("selected");
      document.getElementById("choice-liveportrait").classList.remove("selected");
      document.getElementById(`choice-${style}`).classList.add("selected");
      
      // LivePortrait needs step 4. SadTalker skips step 4.
      if (style === "sadtalker") {
        document.getElementById("dot-4").classList.add("hidden");
      } else {
        document.getElementById("dot-4").classList.remove("hidden");
      }
    }
    
    function updateUI() {
      // Manage panes
      for (let i = 1; i <= 5; i++) {
        document.getElementById(`step-${i}`).classList.remove("active");
        if (i <= currentStep) document.getElementById(`dot-${i}`).classList.add("active");
        else document.getElementById(`dot-${i}`).classList.remove("active");
        
        if (i < currentStep) document.getElementById(`dot-${i}`).classList.add("done");
        else document.getElementById(`dot-${i}`).classList.remove("done");
      }
      document.getElementById(`step-${currentStep}`).classList.add("active");
      
      // Manage buttons
      document.getElementById("btn-back").disabled = (currentStep === 1);
      
      const btnNext = document.getElementById("btn-next");
      if (currentStep === 5) {
        btnNext.textContent = "Generate Avatar!";
        btnNext.onclick = runRender;
      } else {
        btnNext.textContent = "Next";
        btnNext.onclick = goNext;
      }
    }
    
    function goNext() {
      // Validations
      if (currentStep === 2 && !isVoicePrepared) {
        alert("Please prepare a voice file first.");
        return;
      }
      if (currentStep === 3) {
        const hasPortrait = stagedPortraitPath || document.getElementById('portrait-file').files[0];
        if (!hasPortrait) {
          alert("Please upload a portrait.");
          return;
        }
      }
      if (currentStep === 4 && selectedStyle === "liveportrait") {
        const hasDriving = stagedDrivingPath || drivingFile || document.getElementById('driving-file').files[0];
        if (!hasDriving) {
          alert("LivePortrait requires a driving video. Please upload or record one.");
          return;
        }
      }
      
      if (currentStep === 3 && selectedStyle === "sadtalker") {
        currentStep = 5; // skip driving
      } else {
        currentStep++;
      }
      updateUI();
    }
    
    function goBack() {
      if (currentStep === 5 && selectedStyle === "sadtalker") {
        currentStep = 3;
      } else {
        currentStep--;
      }
      updateUI();
    }
    
    function statusMsg(elId, msg, type) {
      const el = document.getElementById(elId);
      el.textContent = msg;
      el.className = `status show ${type}`;
    }

    // --- VOICE LOGIC ---
    document.getElementById("voice-file").onchange = (e) => {
      if (e.target.files[0]) {
        document.getElementById("voice-file-name").textContent = e.target.files[0].name;
        voiceFile = null; // clear recorded
        isVoicePrepared = false;
      }
    };
    
    document.getElementById("voice-record-btn").onclick = async () => {
      try {
        voiceStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        document.getElementById("voice-record-ui").classList.remove("hidden");
        document.getElementById("voice-stop-btn").disabled = false;
        voiceRecorder = new MediaRecorder(voiceStream);
        voiceChunks = [];
        
        voiceRecorder.ondataavailable = e => { if (e.data.size > 0) voiceChunks.push(e.data); };
        voiceRecorder.onstop = () => {
          const blob = new Blob(voiceChunks, { type: "audio/webm" });
          voiceFile = new File([blob], "voice_record.webm", { type: "audio/webm" });
          document.getElementById("voice-file-name").textContent = "Recorded WebCam Audio";
          document.getElementById("voice-file").value = ""; // clear upload
          isVoicePrepared = false;
        };
        voiceRecorder.start();
        document.getElementById("voice-record-btn").disabled = true;
      } catch (err) { alert("Mic error: " + err); }
    };
    
    document.getElementById("voice-stop-btn").onclick = () => {
      if (voiceRecorder && voiceRecorder.state === "recording") {
        voiceRecorder.stop();
        voiceStream.getTracks().forEach(t => t.stop());
        document.getElementById("voice-record-ui").classList.add("hidden");
        document.getElementById("voice-record-btn").disabled = false;
      }
    };
    
    document.getElementById("btn-prep-voice").onclick = async () => {
      const file = voiceFile || document.getElementById("voice-file").files[0];
      const txt = document.getElementById("voice-transcript").value.trim();
      
      if (!file && !stagedVoicePath) return alert("No audio provided.");
      if (file && !txt) return alert("Transcript is required for new audio.");
      
      if (!file && stagedVoicePath) {
        // already prepped
        isVoicePrepared = true;
        statusMsg("voice-prep-status", "Using staged voice.", "good");
        return;
      }
      
      statusMsg("voice-prep-status", "Prepping voice...", "good");
      const fd = new FormData();
      fd.append("audio", file);
      fd.append("transcript", txt);
      
      try {
        const res = await fetch("/api/prep-audio", { method: "POST", body: fd });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);
        stagedVoicePath = data.audio_path;
        stagedTranscriptPath = data.transcript_path;
        isVoicePrepared = true;
        statusMsg("voice-prep-status", "Audio prepared! You can go Next.", "good");
        
        document.getElementById("staged-voice-area").classList.remove("hidden");
        document.getElementById("staged-voice-player").src = data.audio_url;
      } catch (e) {
        statusMsg("voice-prep-status", e.message, "bad");
      }
    };

    // --- PORTRAIT LOGIC ---
    document.getElementById("portrait-file").onchange = (e) => {
      if (e.target.files[0]) {
        document.getElementById("new-portrait-preview").src = URL.createObjectURL(e.target.files[0]);
        document.getElementById("new-portrait-preview").classList.remove("hidden");
      }
    };

    // --- DRIVING LOGIC ---
    document.getElementById("driving-file").onchange = (e) => {
      if (e.target.files[0]) {
        document.getElementById("driving-file-name").textContent = e.target.files[0].name;
        drivingFile = null;
        document.getElementById("new-driving-preview").src = URL.createObjectURL(e.target.files[0]);
        document.getElementById("new-driving-preview").hidden = false;
      }
    };
    
    document.getElementById("driving-record-btn").onclick = async () => {
      try {
        drivingStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        document.getElementById("driving-record-ui").classList.remove("hidden");
        document.getElementById("driving-webcam-preview").srcObject = drivingStream;
        drivingRecorder = new MediaRecorder(drivingStream);
        drivingChunks = [];
        
        drivingRecorder.ondataavailable = e => { if (e.data.size > 0) drivingChunks.push(e.data); };
        drivingRecorder.onstop = () => {
          const blob = new Blob(drivingChunks, { type: "video/webm" });
          drivingFile = new File([blob], "driving_record.webm", { type: "video/webm" });
          document.getElementById("driving-file-name").textContent = "Recorded Webcam Video";
          document.getElementById("driving-file").value = "";
          
          document.getElementById("new-driving-preview").src = URL.createObjectURL(drivingFile);
          document.getElementById("new-driving-preview").hidden = false;
        };
        drivingRecorder.start();
        document.getElementById("driving-record-btn").disabled = true;
      } catch (err) { alert("Camera error: " + err); }
    };
    
    document.getElementById("driving-stop-btn").onclick = () => {
      if (drivingRecorder && drivingRecorder.state === "recording") {
        drivingRecorder.stop();
        drivingStream.getTracks().forEach(t => t.stop());
        document.getElementById("driving-record-ui").classList.add("hidden");
        document.getElementById("driving-record-btn").disabled = false;
      }
    };

    // --- RENDER LOGIC ---
    async function runRender() {
      const text = document.getElementById("render-text").value.trim();
      if (!text) return alert("Please enter speech text.");
      
      const btn = document.getElementById("btn-next");
      btn.disabled = true;
      btn.textContent = "Rendering...";
      
      statusMsg("render-status", "Render starting...", "good");
      document.getElementById("render-logs").classList.remove("hidden");
      document.getElementById("render-output").classList.add("hidden");
      
      const fd = new FormData();
      fd.append("prepared_audio_path", stagedVoicePath);
      fd.append("transcript_path", stagedTranscriptPath);
      fd.append("gen_text", text);
      fd.append("video_backend", selectedStyle);
      
      const portFile = document.getElementById("portrait-file").files[0];
      if (portFile) fd.append("portrait", portFile);
      
      if (selectedStyle === "liveportrait") {
        const drv = drivingFile || document.getElementById("driving-file").files[0];
        if (drv) fd.append("driving_video", drv);
        // if no new upload/record, backend uses staged driving if available? 
        // Wait, backend doesn't automatically use staged driving. We should pass staged path or handle it.
        // I will append staged_driving_path if no file is provided.
        if (!drv && stagedDrivingPath) fd.append("staged_driving_path", stagedDrivingPath);
      }
      
      try {
        const res = await fetch("/api/render", { method: "POST", body: fd });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);
        pollJob(data.job_id);
      } catch (e) {
        statusMsg("render-status", e.message, "bad");
        btn.disabled = false;
        btn.textContent = "Generate Avatar!";
      }
    }
    
    async function pollJob(jobId) {
      const res = await fetch(`/api/jobs/${jobId}`);
      const data = await res.json();
      
      document.getElementById("render-logs").textContent = (data.logs || []).join("");
      
      if (data.status === "running" || data.status === "queued") {
        setTimeout(() => pollJob(jobId), 2000);
      } else {
        const btn = document.getElementById("btn-next");
        btn.disabled = false;
        btn.textContent = "Done!";
        
        if (data.status === "done") {
          statusMsg("render-status", "Render complete!", "good");
          
          let outHtml = "";
          if (data.result.video_url) {
            outHtml = `<video controls src="${data.result.video_url}" style="width:100%; max-width:400px; border-radius:12px; border:2px solid var(--accent);"></video><br>
                       <a href="${data.result.video_url}" download style="display:inline-block; margin-top:8px; color:var(--accent); font-weight:600;">Download Video</a>`;
          } else if (data.result.voice_url) {
            outHtml = `<audio controls src="${data.result.voice_url}" style="width:100%;"></audio>`;
          }
          document.getElementById("render-output").innerHTML = outHtml;
          document.getElementById("render-output").classList.remove("hidden");
        } else {
          statusMsg("render-status", data.error || "Failed", "bad");
        }
      }
    }

    init();
  </script>
</body>
</html>
'''

# We need to replace INDEX_HTML definition
# We also need to update the python routes for /api/defaults and /api/render to handle staged driving.

import re

# Replace INDEX_HTML
new_content = re.sub(r'INDEX_HTML\s*=\s*"""(.*?)"""', 'INDEX_HTML = """' + NEW_INDEX_HTML.replace('\\', '\\\\') + '"""', content, flags=re.DOTALL)

# Add staged driving to defaults
def_api = """    @app.get("/api/defaults")
    def defaults() -> Response:
        staged_audio = ""
        staged_audio_url = ""
        staged_transcript = ""
        staged_transcript_content = ""
        staged_driving = ""
        staged_driving_url = ""

        try:
            wavs = sorted(prepared_audio_dir.glob("prepared_*.wav"), key=lambda p: p.stat().st_mtime, reverse=True)
            if wavs:
                latest_wav = wavs[0]
                staged_audio = str(latest_wav)
                staged_audio_url = rel_file_url(latest_wav)
                latest_txt = latest_wav.with_suffix(".txt")
                if latest_txt.exists():
                    staged_transcript = str(latest_txt)
                    staged_transcript_content = latest_txt.read_text(encoding="utf-8").strip()
        except Exception:
            pass
            
        try:
            drv = sorted(uploads_driving_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
            if drv:
                staged_driving = str(drv[0])
                staged_driving_url = rel_file_url(drv[0])
        except Exception:
            pass

        payload = {
            "default_portrait_path": str(default_portrait) if default_portrait else "",
            "default_portrait_url": rel_file_url(default_portrait) if default_portrait else "",
            "reference_script": reference_script,
            "staged_audio_path": staged_audio,
            "staged_audio_url": staged_audio_url,
            "staged_transcript_path": staged_transcript,
            "staged_transcript_content": staged_transcript_content,
            "staged_driving_path": staged_driving,
            "staged_driving_url": staged_driving_url,
        }
        return jsonify(payload)"""

new_content = re.sub(r'    @app\.get\("/api/defaults"\).*?return jsonify\(payload\)', def_api, new_content, flags=re.DOTALL)


# Add handling for staged driving in /api/render
render_driving_old = """        if video_backend == "liveportrait":
            driving_upload = request.files.get("driving_video")
            if driving_upload is None or not driving_upload.filename:
                return jsonify({"error": "LivePortrait requires a driving video."}), 400
            driving_name = f"driving_{timestamp_slug()}{_safe_suffix(driving_upload.filename)}"
            driving_path = uploads_driving_dir / driving_name
            _save_upload(driving_upload, driving_path)
            command.extend(["--driving-video", str(driving_path)])"""

render_driving_new = """        if video_backend == "liveportrait":
            driving_upload = request.files.get("driving_video")
            staged_drv = request.form.get("staged_driving_path")
            
            if driving_upload and driving_upload.filename:
                driving_name = f"driving_{timestamp_slug()}{_safe_suffix(driving_upload.filename)}"
                driving_path = uploads_driving_dir / driving_name
                _save_upload(driving_upload, driving_path)
                command.extend(["--driving-video", str(driving_path)])
            elif staged_drv and Path(staged_drv).exists():
                command.extend(["--driving-video", staged_drv])
            else:
                return jsonify({"error": "LivePortrait requires a driving video."}), 400"""

new_content = new_content.replace(render_driving_old, render_driving_new)

TARGET.write_text(new_content, encoding="utf-8")
print("Done writing rewritten webapp.py")
