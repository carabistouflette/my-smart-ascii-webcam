const output = document.getElementById('ascii-output');
const statusText = document.getElementById('status-text');
const resText = document.getElementById('resolution-text');

const ws = new WebSocket(`ws://${window.location.host}/ws`);

// If running static file separate from backend (e.g. VS Code Live Server + Python Backend)
// const ws = new WebSocket('ws://localhost:8000/ws'); 
// But we will likely serve this via FastAPI or open file directly.
// If opening file directly, window.location.host is empty.
// Let's assume localhost:8000 for now if protocol is file:
const wsUrl = (window.location.protocol === 'file:')
    ? 'ws://localhost:8000/ws'
    : `ws://${window.location.host}/ws`;

const socket = new WebSocket(wsUrl);

socket.onopen = () => {
    statusText.innerText = "SYSTEM: CONNECTED";
    statusText.style.color = "#00ff41";
};

socket.onclose = () => {
    statusText.innerText = "SYSTEM: DISCONNECTED";
    statusText.style.color = "red";
};

socket.onmessage = (event) => {
    const data = JSON.parse(event.data);

    // Update ASCII content
    // use join('\n') is efficient enough?
    output.innerText = data.ascii.join('\n');

    // Update Theme
    output.className = 'ascii-container'; // Reset
    if (data.theme) {
        output.classList.add(`theme-${data.theme}`);
    }

    // Update Resolution (Font Size)
    // Resolution = width in chars.
    // Screen width / char width.
    // We want to fit 'res' chars into screen width.
    // approximate font aspect ratio is 0.6

    // approximate font aspect ratio is 0.6
    // We want to fit 'res' chars into screen width.
    const vw = document.body.clientWidth;
    const vh = document.body.clientHeight;

    // Safety factor 0.95 to avoid edge wrapping
    const charWidth = vw / data.resolution * 0.95;

    // Most mono fonts: Width ~ 0.6 * Height => Height ~ Width / 0.6
    // We want to maximize size but fit width.
    const fontSize = Math.max(4, charWidth / 0.6);

    output.style.fontSize = `${fontSize}px`;
    // Let CSS handle line-height (set to ~1.15 or 1.2) to match python aspect ratio correction
    output.style.lineHeight = 'normal';
    output.style.letterSpacing = 'normal'; // standard spacing

    resText.innerText = `RES: ${data.resolution}x${data.ascii.length}`;
};
