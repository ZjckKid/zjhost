"""
QR Generator Module
URL: /qr-generator
Visibility: public
"""

from flask import Blueprint, render_template_string, request, send_file, jsonify
import qrcode
from qrcode.image.styledpil import StyledPilImage
from io import BytesIO

blueprint = Blueprint('qr_generator', __name__)

PAGE_HTML = """<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>QR Generator — ZJH</title>
<link rel="icon" href="/photo/oblachko.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&family=Syne:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #0a0a0f;
    --surface: #111118;
    --border: #1e1e2e;
    --accent: #7c6af7;
    --accent2: #f76a8c;
    --text: #e8e8f0;
    --muted: #6b6b80;
    --success: #4ade80;
  }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Syne', sans-serif;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  body::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
      linear-gradient(rgba(124, 106, 247, 0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(124, 106, 247, 0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
  }

  header {
    position: relative;
    z-index: 1;
    padding: 1.25rem 2rem;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    backdrop-filter: blur(12px);
    background: rgba(10, 10, 15, 0.8);
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    text-decoration: none;
    color: var(--text);
    font-weight: 700;
    font-size: 1.1rem;
    letter-spacing: -0.02em;
  }

  .logo-icon {
    width: 32px; height: 32px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border-radius: 8px;
    display: grid;
    place-items: center;
    font-size: 16px;
  }

  .back-link {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    color: var(--muted);
    text-decoration: none;
    display: flex;
    align-items: center;
    gap: 0.4rem;
    transition: color 0.2s;
  }
  .back-link:hover { color: var(--text); }

  main {
    flex: 1;
    position: relative;
    z-index: 1;
    display: flex;
    align-items: flex-start;
    justify-content: center;
    padding: 3rem 1.5rem;
    gap: 2.5rem;
    flex-wrap: wrap;
  }

  .controls {
    flex: 1;
    min-width: 300px;
    max-width: 480px;
  }

  .page-title {
    font-size: 2.5rem;
    font-weight: 800;
    letter-spacing: -0.04em;
    line-height: 1.1;
    margin-bottom: 0.5rem;
    background: linear-gradient(135deg, var(--text) 30%, var(--accent));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .page-sub {
    font-family: 'DM Mono', monospace;
    font-size: 0.8rem;
    color: var(--muted);
    margin-bottom: 2.5rem;
    letter-spacing: 0.04em;
  }

  .field { margin-bottom: 1.5rem; }

  label {
    display: block;
    font-size: 0.7rem;
    font-family: 'DM Mono', monospace;
    color: var(--muted);
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
  }

  textarea, input[type="text"], input[type="url"], select {
    width: 100%;
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--text);
    border-radius: 10px;
    padding: 0.85rem 1rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.875rem;
    transition: border-color 0.2s, box-shadow 0.2s;
    outline: none;
    appearance: none;
  }
  textarea { resize: vertical; min-height: 80px; }

  textarea:focus, input:focus, select:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(124, 106, 247, 0.15);
  }

  select option { background: #1a1a2e; }

  .row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }

  .color-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }

  .color-field {
    position: relative;
  }

  .color-input-wrap {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.6rem 0.9rem;
    transition: border-color 0.2s, box-shadow 0.2s;
    cursor: pointer;
  }
  .color-input-wrap:focus-within {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(124, 106, 247, 0.15);
  }

  .color-swatch {
    width: 24px; height: 24px;
    border-radius: 6px;
    border: 1px solid rgba(255,255,255,0.1);
    flex-shrink: 0;
  }

  .color-hex {
    font-family: 'DM Mono', monospace;
    font-size: 0.8rem;
    color: var(--text);
    background: transparent;
    border: none;
    outline: none;
    width: 100%;
    cursor: pointer;
  }

  input[type="color"] {
    position: absolute;
    opacity: 0;
    width: 1px;
    height: 1px;
  }

  .range-wrap {
    position: relative;
  }

  input[type="range"] {
    width: 100%;
    height: 6px;
    background: var(--border);
    border-radius: 999px;
    border: none;
    padding: 0;
    cursor: pointer;
    accent-color: var(--accent);
  }

  .range-value {
    position: absolute;
    right: 0;
    top: -1.5rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    color: var(--accent);
  }

  .presets {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-top: 0.6rem;
  }

  .preset-btn {
    width: 28px; height: 28px;
    border-radius: 7px;
    border: 2px solid transparent;
    cursor: pointer;
    transition: transform 0.15s, border-color 0.15s;
  }
  .preset-btn:hover { transform: scale(1.15); }
  .preset-btn.active { border-color: var(--text); }

  .generate-btn {
    width: 100%;
    padding: 1rem;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border: none;
    border-radius: 12px;
    color: #fff;
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 1rem;
    letter-spacing: 0.02em;
    cursor: pointer;
    transition: opacity 0.2s, transform 0.15s;
    position: relative;
    overflow: hidden;
    margin-top: 0.5rem;
  }
  .generate-btn::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.1), transparent);
    opacity: 0;
    transition: opacity 0.2s;
  }
  .generate-btn:hover::before { opacity: 1; }
  .generate-btn:hover { transform: translateY(-1px); }
  .generate-btn:active { transform: translateY(0); }
  .generate-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

  .preview-panel {
    flex: 0 0 320px;
    position: sticky;
    top: 2rem;
  }

  .preview-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 2rem;
    text-align: center;
  }

  .qr-canvas-wrap {
    background: #fff;
    border-radius: 12px;
    padding: 1rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 1.25rem;
    transition: box-shadow 0.3s;
    min-width: 180px;
    min-height: 180px;
  }
  .qr-canvas-wrap.glow {
    box-shadow: 0 0 40px rgba(124, 106, 247, 0.3);
  }

  #qrImage {
    display: block;
    max-width: 240px;
    max-height: 240px;
    border-radius: 4px;
    transition: opacity 0.3s;
  }

  .placeholder-icon {
    width: 80px; height: 80px;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0.2;
  }

  .placeholder-icon svg {
    width: 100%; height: 100%;
  }

  .preview-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    color: var(--muted);
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 1rem;
  }

  .download-btn {
    width: 100%;
    padding: 0.85rem;
    background: transparent;
    border: 1px solid var(--border);
    border-radius: 10px;
    color: var(--text);
    font-family: 'Syne', sans-serif;
    font-weight: 600;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    text-decoration: none;
  }
  .download-btn:hover {
    border-color: var(--accent);
    color: var(--accent);
    background: rgba(124, 106, 247, 0.08);
  }
  .download-btn:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }

  .status-msg {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    margin-top: 0.75rem;
    min-height: 1.2em;
    transition: color 0.3s;
  }
  .status-msg.ok { color: var(--success); }
  .status-msg.err { color: var(--accent2); }
  .status-msg.loading { color: var(--muted); }

  .spinner {
    display: inline-block;
    width: 14px; height: 14px;
    border: 2px solid var(--muted);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
    vertical-align: middle;
    margin-right: 4px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  .size-info {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    color: var(--muted);
    margin-top: 0.5rem;
  }

  @media (max-width: 700px) {
    main { flex-direction: column; align-items: stretch; }
    .preview-panel { flex: none; position: static; }
    .page-title { font-size: 1.8rem; }
  }
</style>
</head>
<body>

<header>
  <a href="/" class="logo">
    <div class="logo-icon">⚡</div>
    ZJH Host
  </a>
  <a href="/" class="back-link">← На головну</a>
</header>

<main>
  <!-- Controls -->
  <div class="controls">
    <h1 class="page-title">QR<br>Generator</h1>
    <p class="page-sub">// generate · customize · download</p>

    <div class="field">
      <label>Текст або посилання</label>
      <textarea id="inputText" placeholder="https://host.zjck.eu або будь-який текст..."></textarea>
    </div>

    <div class="field">
      <label>Розмір (пікселів)</label>
      <div class="range-wrap">
        <span class="range-value" id="sizeVal">300</span>
        <input type="range" id="sizeRange" min="100" max="800" step="50" value="300">
      </div>
      <div class="presets" style="margin-top:0.8rem;">
        <button class="preset-btn active" style="background:#e5e5ea; color:#000; width:auto; padding:3px 10px; font-size:11px; font-family:monospace;" data-size="150">S</button>
        <button class="preset-btn" style="background:#e5e5ea; color:#000; width:auto; padding:3px 10px; font-size:11px; font-family:monospace;" data-size="300">M</button>
        <button class="preset-btn" style="background:#e5e5ea; color:#000; width:auto; padding:3px 10px; font-size:11px; font-family:monospace;" data-size="500">L</button>
        <button class="preset-btn" style="background:#e5e5ea; color:#000; width:auto; padding:3px 10px; font-size:11px; font-family:monospace;" data-size="800">XL</button>
      </div>
    </div>

    <div class="field">
      <div class="color-row">
        <div>
          <label>Колір QR</label>
          <div class="color-input-wrap" onclick="document.getElementById('fgColorPicker').click()">
            <div class="color-swatch" id="fgSwatch" style="background:#000000"></div>
            <span class="color-hex" id="fgHex">#000000</span>
            <input type="color" id="fgColorPicker" value="#000000">
          </div>
          <div class="presets" id="fgPresets">
            <div class="preset-btn active" style="background:#000000" data-color="#000000" data-target="fg"></div>
            <div class="preset-btn" style="background:#7c6af7" data-color="#7c6af7" data-target="fg"></div>
            <div class="preset-btn" style="background:#f76a8c" data-color="#f76a8c" data-target="fg"></div>
            <div class="preset-btn" style="background:#1e40af" data-color="#1e40af" data-target="fg"></div>
            <div class="preset-btn" style="background:#065f46" data-color="#065f46" data-target="fg"></div>
            <div class="preset-btn" style="background:#7c2d12" data-color="#7c2d12" data-target="fg"></div>
          </div>
        </div>
        <div>
          <label>Фон QR</label>
          <div class="color-input-wrap" onclick="document.getElementById('bgColorPicker').click()">
            <div class="color-swatch" id="bgSwatch" style="background:#ffffff"></div>
            <span class="color-hex" id="bgHex">#ffffff</span>
            <input type="color" id="bgColorPicker" value="#ffffff">
          </div>
          <div class="presets" id="bgPresets">
            <div class="preset-btn active" style="background:#ffffff; border:1px solid #ccc" data-color="#ffffff" data-target="bg"></div>
            <div class="preset-btn" style="background:#f8f8f8; border:1px solid #ccc" data-color="#f8f8f8" data-target="bg"></div>
            <div class="preset-btn" style="background:#fef3c7" data-color="#fef3c7" data-target="bg"></div>
            <div class="preset-btn" style="background:#ede9fe" data-color="#ede9fe" data-target="bg"></div>
            <div class="preset-btn" style="background:#d1fae5" data-color="#d1fae5" data-target="bg"></div>
            <div class="preset-btn" style="background:#0a0a0f" data-color="#0a0a0f" data-target="bg"></div>
          </div>
        </div>
      </div>
    </div>

    <button class="generate-btn" id="generateBtn" onclick="generateQR()">
      Згенерувати QR
    </button>
  </div>

  <!-- Preview -->
  <div class="preview-panel">
    <div class="preview-card">
      <p class="preview-label">Попередній перегляд</p>
      <div class="qr-canvas-wrap" id="qrWrap">
        <div class="placeholder-icon" id="placeholder">
          <svg viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="4" y="4" width="30" height="30" rx="3" stroke="white" stroke-width="4"/>
            <rect x="46" y="4" width="30" height="30" rx="3" stroke="white" stroke-width="4"/>
            <rect x="4" y="46" width="30" height="30" rx="3" stroke="white" stroke-width="4"/>
            <rect x="12" y="12" width="14" height="14" fill="white" rx="1"/>
            <rect x="54" y="12" width="14" height="14" fill="white" rx="1"/>
            <rect x="12" y="54" width="14" height="14" fill="white" rx="1"/>
            <rect x="46" y="46" width="8" height="8" fill="white" rx="1"/>
            <rect x="58" y="46" width="8" height="8" fill="white" rx="1"/>
            <rect x="46" y="58" width="8" height="8" fill="white" rx="1"/>
            <rect x="62" y="62" width="8" height="8" fill="white" rx="1"/>
          </svg>
        </div>
        <img id="qrImage" src="" alt="QR Code" style="display:none;">
      </div>
      <div class="size-info" id="sizeInfo"></div>
      <div class="status-msg" id="statusMsg"></div>

      <a href="#" class="download-btn" id="downloadBtn" download="qrcode.png"
         style="pointer-events:none; opacity:0.3; margin-top:1rem;"
         onclick="return false;">
        <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path d="M12 15V3m0 12l-4-4m4 4l4-4M2 17l.621 2.485A2 2 0 0 0 4.561 21h14.878a2 2 0 0 0 1.94-1.515L22 17"/>
        </svg>
        Завантажити PNG
      </a>
    </div>
  </div>
</main>

<script>
  let currentDataUrl = null;

  const sizeRange = document.getElementById('sizeRange');
  const sizeVal = document.getElementById('sizeVal');
  sizeRange.addEventListener('input', () => {
    sizeVal.textContent = sizeRange.value;
    document.querySelectorAll('[data-size]').forEach(b => b.classList.remove('active'));
  });

  document.querySelectorAll('[data-size]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-size]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      sizeRange.value = btn.dataset.size;
      sizeVal.textContent = btn.dataset.size;
    });
  });

  function setupColor(pickerId, swatchId, hexId, presetsId, target) {
    const picker = document.getElementById(pickerId);
    const swatch = document.getElementById(swatchId);
    const hex = document.getElementById(hexId);
    const presets = document.getElementById(presetsId);

    picker.addEventListener('input', () => {
      swatch.style.background = picker.value;
      hex.textContent = picker.value;
      presets.querySelectorAll('[data-color]').forEach(b => b.classList.remove('active'));
    });

    if (presets) {
      presets.querySelectorAll('[data-color]').forEach(btn => {
        btn.addEventListener('click', () => {
          presets.querySelectorAll('[data-color]').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          picker.value = btn.dataset.color;
          swatch.style.background = btn.dataset.color;
          hex.textContent = btn.dataset.color;
        });
      });
    }
  }

  setupColor('fgColorPicker', 'fgSwatch', 'fgHex', 'fgPresets', 'fg');
  setupColor('bgColorPicker', 'bgSwatch', 'bgHex', 'bgPresets', 'bg');

  async function generateQR() {
    const text = document.getElementById('inputText').value.trim();
    if (!text) {
      setStatus('Введіть текст або посилання', 'err');
      return;
    }

    const btn = document.getElementById('generateBtn');
    btn.disabled = true;
    btn.textContent = 'Генерація...';
    setStatus('<span class="spinner"></span> Генерація...', 'loading');

    const size = parseInt(sizeRange.value);
    const fg = document.getElementById('fgColorPicker').value;
    const bg = document.getElementById('bgColorPicker').value;

    try {
      const resp = await fetch('/qr-generator/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, size, fg_color: fg, bg_color: bg })
      });

      if (!resp.ok) throw new Error('Server error');

      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      currentDataUrl = url;

      const img = document.getElementById('qrImage');
      img.src = url;
      img.style.display = 'block';
      img.style.maxWidth = Math.min(size, 240) + 'px';
      img.style.maxHeight = Math.min(size, 240) + 'px';
      document.getElementById('placeholder').style.display = 'none';
      document.getElementById('qrWrap').classList.add('glow');
      document.getElementById('sizeInfo').textContent = `${size} × ${size} px`;

      const dlBtn = document.getElementById('downloadBtn');
      dlBtn.href = url;
      dlBtn.style.pointerEvents = 'auto';
      dlBtn.style.opacity = '1';
      dlBtn.onclick = null;
      dlBtn.download = `qr-${Date.now()}.png`;

      setStatus('✓ Готово', 'ok');
    } catch (e) {
      setStatus('Помилка генерації. Спробуйте ще.', 'err');
    } finally {
      btn.disabled = false;
      btn.textContent = 'Згенерувати QR';
    }
  }

  function setStatus(msg, cls) {
    const el = document.getElementById('statusMsg');
    el.innerHTML = msg;
    el.className = 'status-msg ' + cls;
  }

  document.getElementById('inputText').addEventListener('keydown', e => {
    if (e.key === 'Enter' && e.ctrlKey) generateQR();
  });
</script>
</body>
</html>
"""


@blueprint.route('/')
def index():
    return render_template_string(PAGE_HTML)


@blueprint.route('/api/generate', methods=['POST'])
def generate():
    data = request.get_json()
    if not data or not data.get('text'):
        return jsonify({'error': 'No text provided'}), 400

    text = data['text']
    size = max(100, min(800, int(data.get('size', 300))))
    fg_color = data.get('fg_color', '#000000')
    bg_color = data.get('bg_color', '#ffffff')

    # Validate colors
    def valid_color(c):
        import re
        return bool(re.match(r'^#[0-9a-fA-F]{6}$', c))

    if not valid_color(fg_color):
        fg_color = '#000000'
    if not valid_color(bg_color):
        bg_color = '#ffffff'

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(text)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fg_color, back_color=bg_color)
    img = img.resize((size, size))

    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    return send_file(buf, mimetype='image/png', as_attachment=False)
