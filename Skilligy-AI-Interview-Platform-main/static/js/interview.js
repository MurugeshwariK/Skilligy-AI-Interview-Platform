console.log("✅ interview.js loaded");

/* =====================================================
   SAFETY GUARD
===================================================== */
if (!document.getElementById("questionText")) {
  console.log("⛔ Not interview page – JS halted safely");
  throw new Error("Not interview page");
}

/* =====================================================
   GLOBAL STATE
===================================================== */

let activeMode = "text";

let recorder = null;
let audioChunks = [];

let videoRecorder = null;
let videoChunks = [];
let videoStream = null;

function scoreColor(score) {
  if (score >= 8) return "score-good";
  if (score >= 6) return "score-medium";
  return "score-bad";
}

/* =====================================================
   INITIAL LOAD
===================================================== */

document.addEventListener("DOMContentLoaded", () => {

  forceShowMode("text");

  const feedbackBox = document.querySelector(".feedback-box");
  const nextBtn = document.getElementById("nextBtn");

  if (feedbackBox && nextBtn) {
    nextBtn.style.display = "block";
  }

});


/* =====================================================
   MODE SWITCHING
===================================================== */

function forceShowMode(mode) {

  activeMode = mode;

  const text = document.getElementById("textMode");
  const voice = document.getElementById("voiceMode");
  const video = document.getElementById("videoMode");

  if (!text || !voice || !video) return;

  text.style.display = "none";
  voice.style.display = "none";
  video.style.display = "none";

  if (mode === "text") text.style.display = "block";
  if (mode === "voice") voice.style.display = "block";
  if (mode === "video") video.style.display = "block";

  ["textBtn","voiceBtn","videoBtn"].forEach(id=>{
    const btn = document.getElementById(id);
    if(btn) btn.classList.remove("active");
  });

  const activeBtn = document.getElementById(mode + "Btn");
  if(activeBtn) activeBtn.classList.add("active");

  console.log("🔄 Mode switched to:", mode);
}

function setMode(mode){
  forceShowMode(mode);
}


/* =====================================================
   FEEDBACK RENDERING
===================================================== */

function renderFeedback(html){

  const container = document.getElementById("feedbackContainer");
  const nextBtn = document.getElementById("nextBtn");

  if(container){
    container.innerHTML = html;
  }

  if(nextBtn){
    nextBtn.style.display = "block";
  }

}


/* =====================================================
   VOICE RECORDING
===================================================== */

async function startRecording(){

  const stream = await navigator.mediaDevices.getUserMedia({audio:true});

  recorder = new MediaRecorder(stream);
  audioChunks = [];

  recorder.ondataavailable = e => audioChunks.push(e.data);

  recorder.start();

  document.getElementById("status").innerText = "🎙 Recording...";
  document.getElementById("warning").innerText = "";

}


function stopRecording(){

  if(!recorder) return;

  recorder.stop();

  recorder.onstop = async ()=>{

    const blob = new Blob(audioChunks,{type:"audio/webm"});

    const question = document.getElementById("questionText").innerText;

    const formData = new FormData();
    formData.append("file",blob,"voice.webm");
    formData.append("question",question);

    document.getElementById("status").innerText = "🧠 Analyzing...";

    const res = await fetch("/voice-upload",{
      method:"POST",
      body:formData
    });

    const data = await res.json();

    const scores = data.scores || {};
    const speech = data.speech || {};

    if(data.error){
      document.getElementById("warning").innerText = data.error;
      return;
    }
    const speaking = data.speaking_feedback || {};

    const pace = speaking.pace_comment || "Speaking pace analysis not available.";
    const fluencyComment = speaking.fluency_comment || "Fluency feedback not generated.";
    const confidenceComment = speaking.confidence_comment || "Confidence feedback not generated.";


renderFeedback(`

<div class="panel feedback-box">

  <div class="results-header">
    <div>
      <h2 class="results-title">
        <i data-lucide="bar-chart-3"></i>
        Voice Interview Analysis
      </h2>
      <p class="results-subtitle">
        Detailed breakdown of your content quality and speaking performance.
      </p>
    </div>

    <div class="score-card-large">
      <span>Overall Score</span>
      <h1>${Number(data.overall_score || 0).toFixed(1)}/10</h1>
    </div>
  </div>

  <div class="metric-grid section-spacing">

    <div class="metric-card">
      <div class="metric-label">Content Score</div>
      <div class="metric-value ${scoreColor(scores.content_score || 0)}">
         ${(scores.content_score || 0).toFixed(1)}/10
      </div>
    </div>

    <div class="metric-card">
      <div class="metric-label">Fluency</div>
      <div class="metric-value ${scoreColor(speech.fluency || 0)}">
       ${Number(speech.fluency || 0).toFixed(1)}/10
      </div>
    </div>

    <div class="metric-card">
      <div class="metric-label">Confidence</div>
      <div class="metric-value ${scoreColor(speech.confidence || 0)}">
${Number(speech.confidence || 0).toFixed(1)}/10
</div>
    </div>

    <div class="metric-card">
      <div class="metric-label">Speaking Pace</div>
      <div class="metric-value">${speech.wpm || 0} WPM</div>
    </div>

  </div>
  

  <div class="report-section neutral section-spacing">
    <h3>
      <i data-lucide="file-text"></i>
      Transcript
    </h3>
    <p>${data.transcript || "-"}</p>
  </div>

  <div class="analytics-box section-spacing">

    <div class="summary-box">
      <h4>Relevance</h4>
      <p>${scores.relevance || 0}/10</p>
    </div>

    <div class="summary-box">
      <h4>Clarity</h4>
      <p>${scores.clarity || 0}/10</p>
    </div>

    <div class="summary-box">
      <h4>Structure</h4>
      <p>${scores.structure || 0}/10</p>
    </div>

  </div>

  <div class="report-section neutral section-spacing">
    <h3>
      <i data-lucide="mic"></i>
      Speech Analysis
    </h3>
    <div class="speech-grid">

      <div class="speech-item">
        <span>Words Per Minute</span>
        <strong>${speech.wpm || 0}</strong>
      </div>

      <div class="speech-item">
        <span>Filler Words</span>
        <strong>${speech.fillers || 0}</strong>
      </div>

      <div class="speech-item">
        <span>Thinking Pauses</span>
        <strong>${speech.thinking_pauses || 0}</strong>
      </div>

      <div class="speech-item">
        <span>Hesitation Pauses</span>
        <strong>${speech.hesitation_pauses || 0}</strong>
      </div>

    </div>
  </div>

  <div class="feedback-grid section-spacing">

    <div class="report-section positive">
      <h3>
        <i data-lucide="thumbs-up"></i>
        Strengths
      </h3>
      <ul>
        ${(data.strengths || []).map(s => `<li>${s}</li>`).join("")}
      </ul>
    </div>

    <div class="report-section negative">
      <h3>
        <i data-lucide="triangle-alert"></i>
        Areas for Improvement
      </h3>
      <ul>
        ${(data.improvements || []).map(i => `<li>${i}</li>`).join("")}
      </ul>
    </div>

  </div>

  <div class="report-section neutral section-spacing">
    <h3>
      <i data-lucide="lightbulb"></i>
      Coaching Tip
    </h3>
    <p>${data.tip || "Continue practicing to improve your interview performance."}</p>
  </div>

</div>

`);

lucide.createIcons();


 }
  }

/* =====================================================
   VIDEO RECORDING
===================================================== */

async function startVideo(){

  videoStream = await navigator.mediaDevices.getUserMedia({
    video:true,
    audio:true
  });

  document.getElementById("videoPreview").srcObject = videoStream;

  videoRecorder = new MediaRecorder(videoStream);
  videoChunks = [];

  videoRecorder.ondataavailable = e => videoChunks.push(e.data);

  videoRecorder.start();
  document.getElementById("status").innerText = "🎥 Recording...";
}


function stopVideo(){

  if(!videoRecorder) return;

  videoRecorder.stop();

  if(videoStream){
    videoStream.getTracks().forEach(t=>t.stop());
  }

}


async function submitVideo(){

  const blob = new Blob(videoChunks,{type:"video/webm"});

  const question = document.getElementById("questionText").innerText;

  const formData = new FormData();
  formData.append("file",blob,"video.webm");
  formData.append("question",question);
  document.getElementById("status").innerText = "🧠 Analyzing video...";
  const res = await fetch("/video-upload",{
    method:"POST",
    body:formData
  });

  const data = await res.json();

  const ce = data.content_evaluation || {};
  const vm = data.video_metrics || {};
  const overall = Math.min(ce.overall_score || 0, 10);

renderFeedback(`

<div class="panel feedback-box">

<h3>Performance Overview</h3>

<div class="section-spacing">
<span class="score-badge">
Overall Score: ${overall.toFixed(1)}/10
</span>
</div>

<div class="report-section neutral section-spacing">
<h3>
<i data-lucide="file-text"></i>
Transcript
</h3>
<p>${data.transcript || "-"}</p>
</div>

<div class="report-section positive section-spacing">
<h3>
<i data-lucide="bar-chart-3"></i>
Content Evaluation
</h3>

<ul>
<li>Relevance: ${ce.relevance || 0}/10</li>
<li>Clarity: ${ce.clarity || 0}/10</li>
<li>Structure: ${ce.structure || 0}/10</li>
</ul>
</div>

<div class="report-section positive section-spacing">
<h3> Strengths</h3>
<ul>
${(ce.strengths || []).map(s => `<li>${s}</li>`).join("")}
</ul>
</div>

<div class="report-section negative section-spacing">
<h3>⚠ Areas for Improvement</h3>
<ul>
${(ce.improvements || []).map(i => `<li>${i}</li>`).join("")}
</ul>
</div>

<div class="report-section neutral section-spacing">
<h3>
<i data-lucide="video"></i>
Video Presence
</h3>
<ul>
<li>Face Visibility: ${vm.face_visibility || 0}%</li>
<li>Eye Contact: ${vm.eye_contact || 0}%</li>
<li>Head Movement: ${vm.head_movement || "-"}</li>
<li>Facial Activity: ${vm.facial_activity || "-"}</li>
<li>Engagement Score: ${vm.engagement_score || 0}/10</li>
</ul>
</div>
<div class="report-section positive section-spacing">
<h3>
<i data-lucide="camera"></i>
Video Feedback
</h3>
<ul>
${(data.video_feedback || []).map(f => `<li>${f}</li>`).join("")}
</ul>
</div>
<div class="report-section negative section-spacing">
<h3>
<i data-lucide="lightbulb"></i>
Improvement Tip
</h3>
<p>${ce.tip}</p>
</div>

</div>

`);

}


/* =====================================================
   SPEAK QUESTION
===================================================== */

document.addEventListener("DOMContentLoaded", ()=>{

  const speakBtn = document.getElementById("speak-question-btn");
  const questionEl = document.getElementById("interview-question");

  if(!speakBtn || !questionEl) return;

  speakBtn.addEventListener("click",()=>{

    const text = questionEl.innerText.trim();

    if(!text) return;

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);

    utterance.rate = 0.95;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    const voices = window.speechSynthesis.getVoices();

    const voice =
      voices.find(v=>v.lang.startsWith("en") && v.name.toLowerCase().includes("female"))
      || voices.find(v=>v.lang.startsWith("en"));

    if(voice) utterance.voice = voice;

    window.speechSynthesis.speak(utterance);

  });

});