from __future__ import annotations

from dataclasses import dataclass, field
import os
os.environ.pop("PYTHONHASHSEED", None)

from pathlib import Path
import secrets
import subprocess
import threading
from typing import Any

from flask import Flask, jsonify, request, Response, send_file

from .config import AppConfig
from .prep import format_audio_prep_report, prepare_reference_audio
from .utils import ensure_dir, timestamp_slug


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Avatar Clone Studio Wizard</title>
  <style>
    :root {
      --bg: #334155;
      --panel: #1e293b;
      --ink: #f8fafc;
      --muted: #94a3b8;
      --line: #475569;
      --accent: #0d9488;
      --accent-hover: #14b8a6;
      --good: #34d399;
      --bad: #f87171;
      --shadow: 0 12px 30px rgba(0,0,0,0.25);
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
      background: #0f172a;
    }
    .header h1 { margin: 0; font-size: 1.8rem; font-weight: 600; letter-spacing: -0.02em; }
    .header p { margin: 8px 0 0; color: var(--muted); }
    
    .progress {
      display: flex;
      padding: 20px 30px;
      background: var(--panel);
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
    .step-dot.done { background: #2dd4bf; }
    
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
    .card-choice:hover { border-color: #2dd4bf; background: #0f172a; }
    .card-choice.selected { border-color: var(--accent); background: #0f172a; box-shadow: 0 4px 12px rgba(13,148,136,0.25); }
    .card-title { font-weight: 600; font-size: 1.1rem; margin-bottom: 6px; }
    .card-sub { color: var(--muted); font-size: 0.9rem; line-height: 1.4; }
    
    .asset-staged {
      background: #0f172a;
      border: 1px dashed var(--line);
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
      background: #0f172a; color: var(--ink);
    }
    textarea { min-height: 120px; resize: vertical; }
    
    .nav-buttons {
      display: flex;
      justify-content: space-between;
      padding: 20px 30px;
      background: #0f172a;
      border-top: 1px solid var(--line);
    }
    button {
      appearance: none; border: 0; border-radius: 8px; padding: 12px 24px; font-weight: 600; font-size: 1rem;
      cursor: pointer; transition: all 0.2s;
    }
    button:disabled { opacity: 0.5; cursor: not-allowed; }
    .btn-back { background: transparent; color: var(--muted); border: 1px solid var(--line); }
    .btn-back:hover:not(:disabled) { background: #334155; color: var(--ink); }
    .btn-next { background: var(--accent); color: white; }
    .btn-next:hover:not(:disabled) { background: var(--accent-hover); }
    
    .row { display: flex; gap: 10px; margin-bottom: 16px; align-items: center; }
    .status { padding: 12px; border-radius: 8px; margin-bottom: 16px; display: none; }
    .status.show { display: block; }
    .status.good { background: rgba(52, 211, 153, 0.15); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.3); }
    .status.bad { background: rgba(248, 113, 113, 0.15); color: #f87171; border: 1px solid rgba(248, 113, 113, 0.3); }
    .logs { background: #111827; color: #e5e7eb; padding: 16px; border-radius: 8px; font-family: monospace; font-size: 0.85rem; max-height: 200px; overflow-y: auto; margin-top: 16px; white-space: pre-wrap; }
    .fine { font-size: 0.85rem; color: var(--muted); }
    .hidden { display: none !important; }
    
    .coach-overlay {
      position: absolute; top: 0; left: 0; right: 0; bottom: 0;
      display: flex; flex-direction: column; justify-content: flex-end;
      pointer-events: none; border-radius: 8px; overflow: hidden;
    }
    .face-guide {
      position: absolute; top: 50%; left: 50%; transform: translate(-50%, -52%);
      width: 42%; height: 62%;
      border: 2px dashed rgba(255,255,255,0.5); border-radius: 50%;
      pointer-events: none;
    }
    .face-guide-label {
      position: absolute; top: 8px; left: 50%; transform: translateX(-50%);
      color: rgba(255,255,255,0.6); font-size: 0.75rem; pointer-events: none;
      white-space: nowrap;
    }
    .coach-prompt {
      background: rgba(0,0,0,0.75); color: white; padding: 16px 20px;
      text-align: center; font-size: 1.2rem; font-weight: 600;
      animation: fadein 0.3s;
    }
    .coach-prompt .sub { font-size: 0.88rem; font-weight: 400; opacity: 0.8; margin-top: 4px; }
    .coach-actions {
      display: flex; gap: 10px; justify-content: center; margin-top: 14px;
      pointer-events: auto;
    }
    .coach-actions button {
      padding: 10px 20px; border-radius: 8px; font-weight: 600; font-size: 0.95rem; cursor: pointer; border: 0;
    }
    .coach-btn-ok { background: #16a34a; color: white; }
    .coach-btn-ok:hover { background: #15803d; }
    .coach-btn-redo { background: rgba(255,255,255,0.15); color: white; border: 1px solid rgba(255,255,255,0.3) !important; }
    .coach-btn-redo:hover { background: rgba(255,255,255,0.25); }
    .coach-checklist {
      display: flex; flex-wrap: wrap; gap: 8px; justify-content: center;
      margin-top: 12px;
    }
    .coach-check {
      background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 6px;
      padding: 6px 12px; font-size: 0.85rem; color: var(--muted);
      transition: all 0.3s;
    }
    .coach-check.done { background: #dcfce7; border-color: #86efac; color: #166534; transform: scale(1.05); }
    .coach-check.active { background: #dbeafe; border-color: #93c5fd; color: #1d4ed8; animation: pulse 1s infinite; }
    @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.7; } }
    
    .capture-flash {
      position: absolute; top: 0; left: 0; right: 0; bottom: 0;
      background: white; border-radius: 8px;
      opacity: 0; pointer-events: none;
      z-index: 10;
    }
    .capture-flash.flash {
      animation: captureFlash 0.5s ease-out;
    }
    @keyframes captureFlash {
      0% { opacity: 0.7; } 100% { opacity: 0; }
    }
    
    .capture-confirm {
      position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
      font-size: 2.5rem; opacity: 0; pointer-events: none; z-index: 11;
    }
    .capture-confirm.show {
      animation: confirmPop 0.7s ease-out;
    }
    @keyframes confirmPop {
      0% { opacity: 0; transform: translate(-50%, -50%) scale(0.5); }
      30% { opacity: 1; transform: translate(-50%, -50%) scale(1.2); }
      60% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
      100% { opacity: 0; transform: translate(-50%, -50%) scale(1); }
    }
    
    .stitch-bar-container {
      margin-top: 12px; background: #334155; border-radius: 6px; overflow: hidden; height: 28px;
      position: relative;
    }
    .stitch-bar-fill {
      height: 100%; background: linear-gradient(90deg, #0d9488, #2dd4bf);
      border-radius: 6px; transition: width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
      width: 0%;
    }
    .stitch-bar-label {
      position: absolute; top: 0; left: 0; right: 0; bottom: 0;
      display: flex; align-items: center; justify-content: center;
      color: white; font-size: 0.8rem; font-weight: 600;
    }
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
    </div>
    
    <!-- STEP 1: VOICE REFERENCE -->
    <div class="step-pane active" id="step-1">
      <h2>1. Voice Reference</h2>
      <p class="desc">The AI needs to hear your voice to clone it.</p>
      
      <div id="staged-voice-area" class="asset-staged hidden">
        <strong>Ready: Pre-recorded Voice</strong>
        <audio id="staged-voice-player" controls style="display: block; width: 100%; margin: 12px 0;"></audio>
        
        <div style="margin-top: 16px; text-align: left;">
          <label style="font-size: 0.85rem; color: var(--muted); font-weight: 600;">Staged Transcript:</label>
          <div id="staged-voice-transcript-display" style="background: rgba(255,255,255,0.03); border: 1px solid var(--line); border-radius: 8px; padding: 12px; font-size: 0.9rem; line-height: 1.5; color: var(--ink); margin-top: 6px; max-height: 150px; overflow-y: auto; white-space: pre-wrap;"></div>
        </div>
        
        <br>
        <button type="button" class="btn-back" style="font-size: 0.9rem; padding: 8px 16px;" onclick="document.getElementById('new-voice-area').classList.toggle('hidden')">Change / Override</button>
      </div>
      
      <div id="new-voice-area" style="border: 1px solid var(--line); padding: 20px; border-radius: 12px;">
        <label>Provide New Voice</label>
        <div class="row">
          <button type="button" class="btn-back" onclick="document.getElementById('voice-file').click()">Upload Audio</button>
          <span>or</span>
          <button type="button" class="btn-back" id="voice-record-btn">Record Microphone Audio</button>
        </div>
        <input type="file" id="voice-file" accept="audio/*" class="hidden">
        <span id="voice-file-name" class="fine"></span>
        
        <div id="voice-record-ui" class="hidden" style="margin-top: 16px;">
          <style>
            @keyframes pulse-red {
              0% { opacity: 0.4; transform: scale(0.9); }
              50% { opacity: 1; transform: scale(1.1); }
              100% { opacity: 0.4; transform: scale(0.9); }
            }
          </style>
          <div class="row" style="justify-content: center; background: rgba(255,255,255,0.02); border: 1px solid var(--line); padding: 16px; border-radius: 8px; align-items:center;">
            <span id="voice-recording-dot" class="hidden" style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#ef4444; margin-right:12px; box-shadow: 0 0 8px #ef4444; animation: pulse-red 1.2s infinite ease-in-out;"></span>
            <span id="voice-recording-label" style="font-size:0.9rem; color:var(--muted); font-weight:600; margin-right:16px;">Microphone ready</span>
            <button id="voice-start-record-btn" type="button" class="btn-back" style="color:var(--accent); border-color:var(--accent); font-weight:600;">🔴 Start Recording</button>
            <button id="voice-stop-btn" type="button" class="btn-back hidden" style="color:#ef4444; border-color:#ef4444; font-weight:600;">⏹ Stop</button>
            <span id="voice-timer" style="font-family:monospace; font-size: 1.2rem; font-weight:700; color:var(--ink); margin-left: 16px; background: rgba(255,255,255,0.05); padding: 4px 8px; border-radius: 4px;">00:00</span>
          </div>
        </div>

        <!-- Microphone Recording Playback Preview -->
        <div id="voice-record-preview-area" class="hidden" style="margin-top: 16px; background: rgba(13,148,136,0.04); border: 1px solid rgba(13,148,136,0.2); border-radius: 8px; padding: 12px; text-align: left;">
          <label style="font-size:0.85rem; color:var(--accent); font-weight:700; margin-bottom:6px; display:block;">Verify Your Recording:</label>
          <audio id="voice-record-preview-player" controls style="width: 100%; display:block; margin-top:6px;"></audio>
        </div>
        
        <div style="margin-top: 16px;">
          <label>Exact Transcript of the Audio</label>
          <textarea id="voice-transcript" placeholder="Type exactly what is said in the clip..."></textarea>
          <button type="button" class="btn-back" id="btn-prep-voice">Prepare Voice File</button>
          <div id="voice-prep-status" class="status" style="margin-top:12px;"></div>
        </div>
      </div>
    </div>

    <!-- STEP 2: PORTRAIT IMAGE -->
    <div class="step-pane" id="step-2">
      <h2>2. Portrait Image</h2>
      <p class="desc">Provide a clear, front-facing headshot.</p>
      
      <div id="staged-portrait-area" class="asset-staged hidden">
        <strong>Ready: Staged Portrait</strong>
        <img id="staged-portrait-preview" src="">
        <br>
        <button type="button" class="btn-back" style="margin-top: 12px; font-size: 0.9rem; padding: 8px 16px;" onclick="document.getElementById('new-portrait-area').classList.toggle('hidden')">Change / Override</button>
      </div>
      
      <div id="new-portrait-area" style="border: 1px solid var(--line); padding: 20px; border-radius: 12px;">
        <label>Upload New Portrait</label>
        <input type="file" id="portrait-file" accept="image/*">
        <img id="new-portrait-preview" class="hidden" style="max-width: 100%; max-height: 300px; border-radius: 8px; margin-top: 10px;">
      </div>
    </div>

    <!-- STEP 3: SPEECH TEXT -->
    <div class="step-pane" id="step-3">
      <h2>3. Speech Text</h2>
      <p class="desc">What should your avatar say?</p>
      
      <textarea id="render-text" placeholder="Hello, I am a digital avatar. Nice to meet you!">Hi, this is Jean speaking. I care a lot about building tools that are useful, clear, and grounded in real-life applications. I am excited to demonstrate my new high-definition digital avatar clone, featuring custom voice cloning and precise, crystal-clear lip synchronization. I look forward to sharing practical ideas, explaining technical concepts simply, and making steady, conversational progress.</textarea>
      <input type="hidden" id="voice-speed" value="0.88">
    </div>

    <!-- STEP 4: GENERATE & OUTPUT -->
    <div class="step-pane" id="step-4">
      <h2>4. Generate & Output</h2>
      <p class="desc">Watch your high-definition, perfectly lip-synced talking avatar render in real-time.</p>
      
      <div style="background: rgba(14,148,136,0.08); border: 1px solid rgba(14,148,136,0.2); border-radius: 8px; padding: 12px 14px; margin-bottom: 24px; font-size: 0.88rem; color: var(--ink); line-height: 1.5; text-align: left;">
        <strong>⏱ Accurate CPU Render Estimation:</strong>
        <span style="display: block; margin-top: 4px; color: var(--muted); font-size: 0.84rem;">
          Convolutions execute on local CPU cores at a fixed rate of <strong>~25.6 seconds per frame</strong> (25 FPS):
        </span>
        <ul style="margin: 6px 0 0 16px; padding: 0; font-size: 0.84rem; color: var(--ink); display: flex; flex-direction: column; gap: 2px;">
          <li>5-Second Audio (125 frames) ≈ <strong>53 minutes</strong></li>
          <li>12-Second Audio (300 frames) ≈ <strong>2.1 hours</strong></li>
          <li>30-Second Audio (750 frames) ≈ <strong>5.3 hours</strong></li>
        </ul>
        <div style="color: var(--accent); font-size: 0.82rem; font-weight: 600; margin-top: 8px;">Keep this browser tab open during the render.</div>
      </div>
      
      <div id="render-status" class="status"></div>
      
      <div id="render-output" class="hidden" style="text-align: center; margin-bottom: 20px;">
        <!-- Player injected here -->
      </div>
      
      <!-- VISUAL PROGRESS RADAR -->
      <div id="render-progress-card" class="hidden" style="background: rgba(15,23,42,0.4); border: 1px solid var(--line); border-radius: 12px; padding: 24px; margin-bottom: 20px; text-align: left; box-shadow: var(--shadow);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
          <span style="font-weight: 600; font-size: 1rem; color: var(--ink);">Render Pipeline Status</span>
          <span id="render-pipeline-pct" style="font-size: 0.9rem; font-weight: 700; color: var(--accent);">0%</span>
        </div>
        
        <!-- Progress Bar -->
        <div style="width: 100%; height: 8px; background: rgba(255,255,255,0.05); border-radius: 4px; overflow: hidden; margin-bottom: 24px;">
          <div id="render-pipeline-bar" style="width: 0%; height: 100%; background: linear-gradient(90deg, #0d9488, #2dd4bf); transition: width 0.5s ease-out; border-radius: 4px;"></div>
        </div>
        
        <!-- Status Stepper -->
        <div style="display: flex; flex-direction: column; gap: 16px;">
          <!-- Step 1: Voice -->
          <div class="pipeline-step" id="step-voice" style="display: flex; align-items: center; gap: 14px; opacity: 0.5; transition: all 0.3s;">
            <div class="step-indicator" id="ind-voice" style="width: 28px; height: 28px; border-radius: 50%; border: 2px solid var(--line); display: flex; align-items: center; justify-content: center; font-size: 0.85rem; font-weight: 700; color: var(--muted); background: rgba(255,255,255,0.02); transition: all 0.3s;">1</div>
            <div>
              <div style="font-weight: 600; color: var(--ink); font-size: 0.92rem;">Voice Cloning (F5-TTS)</div>
              <div style="font-size: 0.8rem; color: var(--muted); margin-top: 2px;" id="sub-voice">Waiting...</div>
            </div>
          </div>
          
          <!-- Step 2: 3DMM Coordinates Extraction -->
          <div class="pipeline-step" id="step-landmarks" style="display: flex; align-items: center; gap: 14px; opacity: 0.5; transition: all 0.3s;">
            <div class="step-indicator" id="ind-landmarks" style="width: 28px; height: 28px; border-radius: 50%; border: 2px solid var(--line); display: flex; align-items: center; justify-content: center; font-size: 0.85rem; font-weight: 700; color: var(--muted); background: rgba(255,255,255,0.02); transition: all 0.3s;">2</div>
            <div>
              <div style="font-weight: 600; color: var(--ink); font-size: 0.92rem;">3D Facial Shape Reconstruction (3DMM)</div>
              <div style="font-size: 0.8rem; color: var(--muted); margin-top: 2px;" id="sub-landmarks">Waiting...</div>
            </div>
          </div>
          
          <!-- Step 3: Neural Lip Sync Animate -->
          <div class="pipeline-step" id="step-animation" style="display: flex; align-items: center; gap: 14px; opacity: 0.5; transition: all 0.3s;">
            <div class="step-indicator" id="ind-animation" style="width: 28px; height: 28px; border-radius: 50%; border: 2px solid var(--line); display: flex; align-items: center; justify-content: center; font-size: 0.85rem; font-weight: 700; color: var(--muted); background: rgba(255,255,255,0.02); transition: all 0.3s;">3</div>
            <div>
              <div style="font-weight: 600; color: var(--ink); font-size: 0.92rem;">Phonetic Lip-Sync Animation (SadTalker-HD)</div>
              <div style="font-size: 0.8rem; color: var(--muted); margin-top: 2px;" id="sub-animation">Waiting...</div>
            </div>
          </div>
          
          <!-- Step 4: GFPGAN Enhancement -->
          <div class="pipeline-step" id="step-stitching" style="display: flex; align-items: center; gap: 14px; opacity: 0.5; transition: all 0.3s;">
            <div class="step-indicator" id="ind-stitching" style="width: 28px; height: 28px; border-radius: 50%; border: 2px solid var(--line); display: flex; align-items: center; justify-content: center; font-size: 0.85rem; font-weight: 700; color: var(--muted); background: rgba(255,255,255,0.02); transition: all 0.3s;">4</div>
            <div>
              <div style="font-weight: 600; color: var(--ink); font-size: 0.92rem;">High-Fidelity Detail Restoration (GFPGAN HD)</div>
              <div style="font-size: 0.8rem; color: var(--muted); margin-top: 2px;" id="sub-stitching">Waiting...</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Collapsible developer log -->
      <details style="margin-top: 20px; text-align: left; background: rgba(15,23,42,0.3); border: 1px solid var(--line); border-radius: 12px; padding: 12px;">
        <summary style="cursor: pointer; font-size: 0.85rem; color: var(--muted); font-weight: 600; outline: none; user-select: none;">
          🛠️ Advanced Developer System Logs
        </summary>
        <div id="render-logs" class="logs" style="margin-top: 10px; max-height: 200px; overflow-y: auto;"></div>
      </details>
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
    let maxSteps = 4;
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
        document.getElementById("new-voice-area").classList.add("hidden");
        document.getElementById("staged-voice-player").src = data.staged_audio_url;
        document.getElementById("voice-transcript").value = data.staged_transcript_content || "";
        document.getElementById("staged-voice-transcript-display").innerText = data.staged_transcript_content || "";
        isVoicePrepared = true;
        stagedVoicePath = data.staged_audio_path;
        stagedTranscriptPath = data.staged_transcript_path;
      }
      
      if (data.default_portrait_url) {
        document.getElementById("staged-portrait-area").classList.remove("hidden");
        document.getElementById("new-portrait-area").classList.add("hidden");
        document.getElementById("staged-portrait-preview").src = data.default_portrait_url;
        stagedPortraitPath = data.default_portrait_path;
      }
      
      if (!document.getElementById("voice-transcript").value && data.reference_script) {
        document.getElementById("voice-transcript").value = data.reference_script;
      }
      
      updateUI();
    }
    
    // --- NAVIGATION ---
    function updateUI() {
      // Manage panes
      for (let i = 1; i <= 4; i++) {
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
      if (currentStep === 4) {
        btnNext.textContent = "Generate Avatar!";
        btnNext.onclick = runRender;
      } else {
        btnNext.textContent = "Next";
        btnNext.onclick = goNext;
      }
    }
    
    function goNext() {
      // Validations
      if (currentStep === 1 && !isVoicePrepared) {
        alert("Please prepare a voice file first.");
        return;
      }
      if (currentStep === 2) {
        const hasPortrait = stagedPortraitPath || document.getElementById('portrait-file').files[0];
        if (!hasPortrait) {
          alert("Please upload a portrait.");
          return;
        }
      }
      if (currentStep === 3) {
        const text = document.getElementById("render-text").value.trim();
        if (!text) {
          alert("Please enter speech text.");
          return;
        }
      }
      
      currentStep++;
      updateUI();
    }
    
    function goBack() {
      currentStep--;
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
    
    let voiceRecordingTimerId = null;
    let voiceRecordingStartTime = 0;

    document.getElementById("voice-record-btn").onclick = async () => {
      try {
        voiceStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        document.getElementById("voice-record-ui").classList.remove("hidden");
        document.getElementById("voice-start-record-btn").classList.remove("hidden");
        document.getElementById("voice-stop-btn").classList.add("hidden");
        document.getElementById("voice-timer").textContent = "00:00";
        document.getElementById("voice-recording-dot").classList.add("hidden");
        document.getElementById("voice-recording-label").textContent = "Microphone ready";
        document.getElementById("voice-recording-label").style.color = "var(--muted)";
        document.getElementById("voice-record-btn").disabled = true;
      } catch (err) { alert("Mic error: " + err); }
    };
    
    document.getElementById("voice-start-record-btn").onclick = () => {
      voiceRecorder = new MediaRecorder(voiceStream);
      voiceChunks = [];
      
      voiceRecorder.ondataavailable = e => { if (e.data.size > 0) voiceChunks.push(e.data); };
      voiceRecorder.onstop = () => {
        const blob = new Blob(voiceChunks, { type: "audio/webm" });
        voiceFile = new File([blob], "voice_record.webm", { type: "audio/webm" });
        document.getElementById("voice-file-name").textContent = "Recorded Live Microphone Audio";
        document.getElementById("voice-file").value = ""; // clear upload
        isVoicePrepared = false;
        clearInterval(voiceRecordingTimerId);
        
        // Show verification preview player
        const audioURL = URL.createObjectURL(blob);
        document.getElementById("voice-record-preview-player").src = audioURL;
        document.getElementById("voice-record-preview-area").classList.remove("hidden");
        document.getElementById("voice-recording-label").textContent = "✅ Recording captured!";
        document.getElementById("voice-recording-label").style.color = "var(--accent)";
        document.getElementById("voice-recording-dot").classList.add("hidden");
      };
      
      voiceRecorder.start();
      document.getElementById("voice-start-record-btn").classList.add("hidden");
      document.getElementById("voice-stop-btn").classList.remove("hidden");
      document.getElementById("voice-recording-dot").classList.remove("hidden");
      document.getElementById("voice-recording-label").textContent = "🔴 Recording Live...";
      document.getElementById("voice-recording-label").style.color = "#ef4444";
      
      voiceRecordingStartTime = Date.now();
      voiceRecordingTimerId = setInterval(() => {
        const s = Math.floor((Date.now() - voiceRecordingStartTime) / 1000);
        const m = String(Math.floor(s/60)).padStart(2, '0');
        const sec = String(s%60).padStart(2, '0');
        document.getElementById("voice-timer").textContent = `${m}:${sec}`;
      }, 500);
    };
    
    document.getElementById("voice-stop-btn").onclick = () => {
      if (voiceRecorder && voiceRecorder.state === "recording") {
        voiceRecorder.stop();
        voiceStream.getTracks().forEach(t => t.stop());
        document.getElementById("voice-record-ui").classList.remove("hidden"); // keep visible to review timer/preview
        document.getElementById("voice-start-record-btn").classList.add("hidden");
        document.getElementById("voice-stop-btn").classList.add("hidden");
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

    document.getElementById("portrait-file").onchange = (e) => {
      if (e.target.files[0]) {
        document.getElementById("new-portrait-preview").src = URL.createObjectURL(e.target.files[0]);
        document.getElementById("new-portrait-preview").classList.remove("hidden");
      }
    };

    // --- RENDER LOGIC ---
    let renderTimer = null;
    let renderStartTime = null;
    
    function formatElapsed(ms) {
      const s = Math.floor(ms / 1000);
      const m = Math.floor(s / 60);
      const sec = s % 60;
      return `${m}:${sec.toString().padStart(2, '0')}`;
    }
    
    function startRenderTimer() {
      renderStartTime = Date.now();
      const estimate = "10–15 min for High-Definition Face Restoration (CPU)";
      renderTimer = setInterval(() => {
        const elapsed = formatElapsed(Date.now() - renderStartTime);
        statusMsg("render-status", `Rendering… ${elapsed} elapsed (estimated ${estimate})`, "good");
      }, 1000);
    }
    
    function stopRenderTimer() {
      if (renderTimer) { clearInterval(renderTimer); renderTimer = null; }
    }
    
    async function runRender() {
      const text = document.getElementById("render-text").value.trim();
      if (!text) return alert("Please enter speech text.");
      
      const btn = document.getElementById("btn-next");
      btn.disabled = true;
      btn.textContent = "Rendering...";
      document.querySelector(".nav-buttons").style.display = "none";
      
      startRenderTimer();
      document.getElementById("render-logs").classList.remove("hidden");
      document.getElementById("render-output").classList.add("hidden");
      
      const fd = new FormData();
      fd.append("prepared_audio_path", stagedVoicePath);
      fd.append("transcript_path", stagedTranscriptPath);
      fd.append("gen_text", text);
      fd.append("video_backend", "sadtalker");
      fd.append("voice_speed", document.getElementById("voice-speed").value);
      
      const portFile = document.getElementById("portrait-file").files[0];
      if (portFile) fd.append("portrait", portFile);
      
      try {
        const res = await fetch("/api/render", { method: "POST", body: fd });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);
        pollJob(data.job_id);
      } catch (e) {
        stopRenderTimer();
        statusMsg("render-status", e.message, "bad");
        btn.disabled = false;
        btn.textContent = "Generate Avatar!";
        document.querySelector(".nav-buttons").style.display = "flex";
      }
    }
    
    function updatePipelineStatus(logsText, jobStatus) {
      const indVoice = document.getElementById("ind-voice");
      const indLandmarks = document.getElementById("ind-landmarks");
      const indAnimation = document.getElementById("ind-animation");
      const indStitching = document.getElementById("ind-stitching");
      
      const stepVoice = document.getElementById("step-voice");
      const stepLandmarks = document.getElementById("step-landmarks");
      const stepAnimation = document.getElementById("step-animation");
      const stepStitching = document.getElementById("step-stitching");
      
      const subVoice = document.getElementById("sub-voice");
      const subLandmarks = document.getElementById("sub-landmarks");
      const subAnimation = document.getElementById("sub-animation");
      const subStitching = document.getElementById("sub-stitching");
      
      const bar = document.getElementById("render-pipeline-bar");
      const pct = document.getElementById("render-pipeline-pct");
      
      function setRunning(ind, step, sub, text) {
        ind.style.borderColor = "var(--accent)";
        ind.style.background = "rgba(13,148,136,0.1)";
        ind.style.color = "var(--accent)";
        ind.innerHTML = "⏳";
        step.style.opacity = "1.0";
        sub.textContent = text;
        sub.style.color = "var(--accent)";
      }
      
      function setDone(ind, step, sub, text) {
        ind.style.borderColor = "#2dd4bf";
        ind.style.background = "#0d9488";
        ind.style.color = "#ffffff";
        ind.innerHTML = "✓";
        step.style.opacity = "1.0";
        sub.textContent = text;
        sub.style.color = "#2dd4bf";
      }
      
      function setPending(ind, step, sub, text) {
        ind.style.borderColor = "var(--line)";
        ind.style.background = "rgba(255,255,255,0.02)";
        ind.style.color = "var(--muted)";
        ind.innerHTML = ind.id === "ind-voice" ? "1" : ind.id === "ind-landmarks" ? "2" : ind.id === "ind-animation" ? "3" : "4";
        step.style.opacity = "0.5";
        sub.textContent = text;
        sub.style.color = "var(--muted)";
      }

      const hasVoiceStart = logsText.includes("F5-TTS") || logsText.includes("Vocos") || logsText.includes("infer");
      const hasLandmarksStart = logsText.includes("crop") || logsText.includes("landmark") || logsText.includes("detector") || logsText.includes("face");
      const hasAnimationStart = logsText.includes("progress") || logsText.includes("frame") || logsText.includes("rendering") || logsText.includes("LivePortrait") || logsText.includes("inference.py");
      const hasStitchingStart = logsText.includes("stitching") || logsText.includes("pasteback") || logsText.includes("stitch") || logsText.includes("ffmpeg");

      if (jobStatus === "done") {
        setDone(indVoice, stepVoice, subVoice, "Completed");
        setDone(indLandmarks, stepLandmarks, subLandmarks, "Completed");
        setDone(indAnimation, stepAnimation, subAnimation, "Completed");
        setDone(indStitching, stepStitching, subStitching, "Completed");
        bar.style.width = "100%";
        pct.textContent = "100%";
        return;
      }

      if (hasStitchingStart) {
        setDone(indVoice, stepVoice, subVoice, "Completed");
        setDone(indLandmarks, stepLandmarks, subLandmarks, "Completed");
        setDone(indAnimation, stepAnimation, subAnimation, "Completed");
        setRunning(indStitching, stepStitching, subStitching, "Blending and matching portrait lighting...");
        bar.style.width = "85%";
        pct.textContent = "85%";
      } else if (hasAnimationStart) {
        setDone(indVoice, stepVoice, subVoice, "Completed");
        setDone(indLandmarks, stepLandmarks, subLandmarks, "Completed");
        
        let label = "Generating neural animation frames (takes a while)...";
        let globalPct = 50;
        
        // Parse tqdm progress matching: "Face Renderer::  12%|█▎        | 35/294"
        const matches = [...logsText.matchAll(/Face Renderer::\\s+(\\d+)%[^\\d]*(\\d+)\\/(\\d+)/g)];
        if (matches.length > 0) {
          const last = matches[matches.length - 1];
          const percent = parseInt(last[1]);
          const current = parseInt(last[2]);
          const total = parseInt(last[3]);
          label = `Generating neural animation frames: ${current} / ${total} (${percent}%)`;
          globalPct = Math.round(50 + (percent * 0.3));
        } else {
          const pctMatches = [...logsText.matchAll(/Face Renderer::\\s+(\\d+)%/g)];
          if (pctMatches.length > 0) {
            const percent = parseInt(pctMatches[pctMatches.length - 1][1]);
            label = `Generating neural animation frames: ${percent}%`;
            globalPct = Math.round(50 + (percent * 0.3));
          }
        }
        
        setRunning(indAnimation, stepAnimation, subAnimation, label);
        setPending(indStitching, stepStitching, subStitching, "Waiting...");
        bar.style.width = `${globalPct}%`;
        pct.textContent = `${globalPct}%`;
      } else if (hasLandmarksStart) {
        setDone(indVoice, stepVoice, subVoice, "Completed");
        setRunning(indLandmarks, stepLandmarks, subLandmarks, "Detecting portrait structure & jaw alignment...");
        setPending(indAnimation, stepAnimation, subAnimation, "Waiting...");
        setPending(indStitching, stepStitching, subStitching, "Waiting...");
        bar.style.width = "25%";
        pct.textContent = "25%";
      } else if (hasVoiceStart) {
        let voiceLabel = "Cloning speaker audio (F5-TTS flow-matching)...";
        let voicePct = 10;
        
        const voiceMatches = [...logsText.matchAll(/(\\d+)%\\|[^\\d]*(\\d+)\\/(\\d+)/g)];
        if (voiceMatches.length > 0) {
          const last = voiceMatches[voiceMatches.length - 1];
          const percent = parseInt(last[1]);
          const current = parseInt(last[2]);
          const total = parseInt(last[3]);
          voiceLabel = `Cloning speaker audio: batch ${current} / ${total} (${percent}%)`;
          voicePct = Math.round(10 + (percent * 0.1));
        }
        
        setRunning(indVoice, stepVoice, subVoice, voiceLabel);
        setPending(indLandmarks, stepLandmarks, subLandmarks, "Waiting...");
        setPending(indAnimation, stepAnimation, subAnimation, "Waiting...");
        setPending(indStitching, stepStitching, subStitching, "Waiting...");
        bar.style.width = `${voicePct}%`;
        pct.textContent = `${voicePct}%`;
      } else {
        setPending(indVoice, stepVoice, subVoice, "Starting audio synthesizer...");
        setPending(indLandmarks, stepLandmarks, subLandmarks, "Waiting...");
        setPending(indAnimation, stepAnimation, subAnimation, "Waiting...");
        setPending(indStitching, stepStitching, subStitching, "Waiting...");
        bar.style.width = "3%";
        pct.textContent = "Queued...";
      }
    }

    function playDing(isError = false) {
      try {
        if (isError) return; // Silent on errors to avoid annoying beeps

        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        // Crystalline, soft success chime
        const osc1 = ctx.createOscillator();
        const gain1 = ctx.createGain();
        osc1.type = "sine";
        osc1.frequency.setValueAtTime(880.00, ctx.currentTime); // A5
        osc1.frequency.exponentialRampToValueAtTime(1046.50, ctx.currentTime + 0.12); // Smooth slide to C6
        gain1.gain.setValueAtTime(0.1, ctx.currentTime);
        gain1.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1.0);
        osc1.connect(gain1);
        gain1.connect(ctx.destination);
        osc1.start();
        osc1.stop(ctx.currentTime + 1.0);
        
        const osc2 = ctx.createOscillator();
        const gain2 = ctx.createGain();
        osc2.type = "sine";
        osc2.frequency.setValueAtTime(1318.51, ctx.currentTime + 0.08); // E6
        gain2.gain.setValueAtTime(0.05, ctx.currentTime + 0.08);
        gain2.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.7);
        osc2.connect(gain2);
        gain2.connect(ctx.destination);
        osc2.start();
        osc2.stop(ctx.currentTime + 0.7);
      } catch (err) {
        console.error("Audio ding failed:", err);
      }
    }

    async function pollJob(jobId) {
      const res = await fetch(`/api/jobs/${jobId}`);
      const data = await res.json();
      
      const logsText = (data.logs || []).join("");
      document.getElementById("render-logs").textContent = logsText;
      
      document.getElementById("render-progress-card").classList.remove("hidden");
      updatePipelineStatus(logsText, data.status);
      
      if (data.status === "running" || data.status === "queued") {
        setTimeout(() => pollJob(jobId), 2000);
      } else {
        stopRenderTimer();
        
        if (data.status === "done") {
          playDing(false); // Success chime!
          const elapsed = renderStartTime ? formatElapsed(Date.now() - renderStartTime) : "";
          statusMsg("render-status", `✅ Render complete! (${elapsed})`, "good");
          
          let outHtml = "";
          if (data.result.video_url) {
            outHtml = `
              <div style="background: rgba(45,212,191,0.06); border: 2px solid rgba(45,212,191,0.25); border-radius: 16px; padding: 32px 24px; text-align: center; box-shadow: 0 8px 32px rgba(0,0,0,0.4); margin-bottom: 24px;">
                <div style="width: 56px; height: 56px; border-radius: 50%; background: #0d9488; display: flex; align-items: center; justify-content: center; margin: 0 auto 16px; box-shadow: 0 0 20px rgba(45,212,191,0.4);">
                  <span style="font-size: 1.8rem; color: #ffffff; font-weight: bold;">✓</span>
                </div>
                <h3 style="font-size: 1.3rem; font-weight: 700; color: var(--ink); margin-bottom: 6px; font-family: 'Inter', sans-serif;">Avatar Synthesized Successfully!</h3>
                <p style="font-size: 0.88rem; color: var(--muted); margin-bottom: 24px;">Your high-definition digital clone is ready for download.</p>
                
                <div style="position: relative; display: inline-block; border-radius: 14px; overflow: hidden; box-shadow: 0 0 30px rgba(45,212,191,0.3); border: 2px solid var(--accent); margin-bottom: 24px;">
                  <video controls src="${data.result.video_url}" style="width: 100%; max-width: 440px; display: block;"></video>
                </div>
                
                <div style="display: flex; flex-direction: column; gap: 12px; max-width: 320px; margin: 0 auto;">
                  <a href="${data.result.video_url}" download style="display: flex; align-items: center; justify-content: center; gap: 8px; text-decoration: none; padding: 12px 24px; border-radius: 8px; font-weight: 700; font-size: 0.95rem; background: var(--accent); color: white; transition: all 0.2s; box-shadow: 0 4px 12px rgba(45,212,191,0.25);">
                    📥 Download Cloned Video
                  </a>
                  <button onclick="window.location.reload()" style="background: rgba(255,255,255,0.05); border: 1px solid var(--line); color: var(--ink); padding: 12px 24px; border-radius: 8px; font-weight: 600; font-size: 0.95rem; cursor: pointer; transition: all 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.1)'" onmouseout="this.style.background='rgba(255,255,255,0.05)'">
                    🔄 Create Another Avatar
                  </button>
                </div>
              </div>
            `;
          } else if (data.result.voice_url) {
            outHtml = `<audio controls src="${data.result.voice_url}" style="width:100%;"></audio>`;
          }
          document.getElementById("render-output").innerHTML = outHtml;
          document.getElementById("render-output").classList.remove("hidden");
        } else {
          const btn = document.getElementById("btn-next");
          btn.disabled = false;
          btn.textContent = "Retry Render";
          btn.onclick = runRender;
          document.querySelector(".nav-buttons").style.display = "flex";
          playDing(true); // Error tone!
          statusMsg("render-status", data.error || "Failed", "bad");
        }
      }
    }

    init();
  </script>
</body>
</html>
"""


@dataclass(slots=True)
class Job:
    id: str
    status: str = "queued"
    logs: list[str] = field(default_factory=list)
    result: dict[str, str] = field(default_factory=dict)
    error: str | None = None


def _safe_suffix(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    return suffix if suffix else ""


def _save_upload(file_storage, destination: Path) -> Path:
    ensure_dir(destination.parent)
    file_storage.save(destination)
    return destination


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def create_app(config: AppConfig) -> Flask:
    app = Flask(__name__)
    project_root = config.base_dir
    jobs: dict[str, Job] = {}
    jobs_lock = threading.Lock()

    default_portrait_candidates = [
        project_root / "data/portraits/jean_headshot_1024.png",
    ]
    default_portrait = next((path for path in default_portrait_candidates if path.exists()), None)
    reference_script_path = project_root / "data/voice_refs/jean_reference_script.txt"
    reference_script = reference_script_path.read_text(encoding="utf-8").strip() if reference_script_path.exists() else ""

    uploads_audio_dir = ensure_dir(project_root / "data/voice_refs/uploads")
    prepared_audio_dir = ensure_dir(project_root / "data/voice_refs/prepared")
    uploads_portrait_dir = ensure_dir(project_root / "data/portraits/uploads")
    uploads_driving_dir = ensure_dir(project_root / "data/driving_videos/uploads")
    output_runs_dir = ensure_dir(project_root / "data/outputs/runs")

    def rel_file_url(path: Path) -> str:
        rel = path.resolve().relative_to(project_root.resolve())
        return f"/files/{rel.as_posix()}"

    @app.get("/")
    def index() -> str:
        return INDEX_HTML

    @app.get("/api/defaults")
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
            drv = []
            for ext in ("*.webm", "*.mp4", "*.mov", "*.avi", "*.mkv"):
                drv.extend(uploads_driving_dir.glob(ext))
            drv = sorted(drv, key=lambda p: p.stat().st_mtime, reverse=True)
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
        return jsonify(payload)

    @app.post("/api/prep-audio")
    def prep_audio() -> Response:
        uploaded = request.files.get("audio")
        transcript = (request.form.get("transcript") or "").strip()

        if uploaded is None or not uploaded.filename:
            return jsonify({"error": "No audio file was uploaded."}), 400
        if not transcript:
            return jsonify({"error": "Transcript is required."}), 400

        stamp = timestamp_slug()
        raw_name = f"raw_{stamp}{_safe_suffix(uploaded.filename)}"
        prepared_name = f"prepared_{stamp}.wav"
        transcript_name = f"prepared_{stamp}.txt"

        raw_path = uploads_audio_dir / raw_name
        prepared_path = prepared_audio_dir / prepared_name
        transcript_path = prepared_audio_dir / transcript_name

        _save_upload(uploaded, raw_path)
        result = prepare_reference_audio(raw_path, prepared_path)
        transcript_path.write_text(transcript + "\n", encoding="utf-8")

        return jsonify(
            {
                "audio_path": str(prepared_path),
                "audio_url": rel_file_url(prepared_path),
                "transcript_path": str(transcript_path),
                "report": format_audio_prep_report(result),
            }
        )

    def run_pipeline_job(job: Job, *, command: list[str]) -> None:
        job.status = "running"
        try:
            process = subprocess.Popen(
                command,
                cwd=project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            assert process.stdout is not None

            for line in process.stdout:
                job.logs.append(line)

            return_code = process.wait()
            if return_code != 0:
                job.status = "error"
                job.error = f"Pipeline exited with code {return_code}."
                return

            voice_path = ""
            video_path = ""
            for line in job.logs:
                stripped = line.strip()
                if stripped.startswith("voice="):
                    voice_path = stripped.split("=", 1)[1]
                elif stripped.startswith("video="):
                    video_path = stripped.split("=", 1)[1]

            if voice_path:
                job.result["voice_path"] = voice_path
                job.result["voice_url"] = rel_file_url(Path(voice_path))
            if video_path:
                job.result["video_path"] = video_path
                job.result["video_url"] = rel_file_url(Path(video_path))
            job.status = "done"
        except Exception as exc:  # pragma: no cover - defensive server path
            job.status = "error"
            job.error = str(exc)

    @app.post("/api/render")
    def render() -> Response:
        prepared_audio_path = (request.form.get("prepared_audio_path") or "").strip()
        transcript_path = (request.form.get("transcript_path") or "").strip()
        gen_text = (request.form.get("gen_text") or "").strip()
        video_backend = (request.form.get("video_backend") or "sadtalker").strip()

        if not prepared_audio_path or not Path(prepared_audio_path).exists():
            return jsonify({"error": "Prepared audio path is missing or invalid."}), 400
        if not transcript_path or not Path(transcript_path).exists():
            return jsonify({"error": "Transcript path is missing or invalid."}), 400
        if not gen_text:
            return jsonify({"error": "Speech text is required."}), 400

        portrait_upload = request.files.get("portrait")
        if portrait_upload and portrait_upload.filename:
            portrait_name = f"portrait_{timestamp_slug()}{_safe_suffix(portrait_upload.filename)}"
            portrait_path = uploads_portrait_dir / portrait_name
            _save_upload(portrait_upload, portrait_path)
        elif default_portrait is not None:
            portrait_path = default_portrait
        else:
            return jsonify({"error": "Upload a portrait image or stage a default portrait first."}), 400

        voice_speed = (request.form.get("voice_speed") or "1.0").strip()
        command = [
            str(project_root / ".venv/bin/avatar-clone"),
            "pipeline",
            "--text",
            gen_text,
            "--ref-audio",
            prepared_audio_path,
            "--ref-text",
            _read_text(Path(transcript_path)),
            "--source-image",
            str(portrait_path),
            "--video-backend",
            video_backend,
            "--output-dir",
            str(output_runs_dir / timestamp_slug()),
            "--voice-speed",
            voice_speed,
        ]

        # Force SadTalker + GFPGAN HD Face Restoration
        command.extend(["--enhancer", "gfpgan"])

        job = Job(id=secrets.token_hex(8))
        with jobs_lock:
            jobs[job.id] = job

        thread = threading.Thread(target=run_pipeline_job, args=(job,), kwargs={"command": command}, daemon=True)
        thread.start()

        return jsonify({"job_id": job.id})

    @app.get("/api/jobs/<job_id>")
    def get_job(job_id: str) -> Response:
        with jobs_lock:
            job = jobs.get(job_id)

        if job is None:
            return jsonify({"error": "Job not found."}), 404

        payload: dict[str, Any] = {
            "id": job.id,
            "status": job.status,
            "logs": job.logs[-300:],
            "result": job.result,
            "error": job.error,
        }
        return jsonify(payload)

    @app.get("/files/<path:relative_path>")
    def open_file(relative_path: str):
        target = (project_root / relative_path).resolve()
        try:
            target.relative_to(project_root.resolve())
        except ValueError:
            return jsonify({"error": "Invalid file path."}), 400
        if not target.exists():
            return jsonify({"error": "File not found."}), 404
        return send_file(target)

    return app


def launch_ui(config: AppConfig, *, host: str, port: int, debug: bool = False) -> None:
    app = create_app(config)
    app.run(host=host, port=port, debug=debug)
