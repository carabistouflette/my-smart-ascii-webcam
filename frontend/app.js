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
    
    // Simple heuristic: Font Size = Viewport Width / Resolution
    // But we need to account for padding/margin
    const vw = document.body.clientWidth;
    // const vh = document.body.clientHeight;
    
    // We want the text block to mostly fill the screen or be centered.
    // Let's stick to width fitting.
    // A char is roughly 0.6em wide.
    // font-size * 0.6 * res = vw
    // font-size = vw / (0.6 * res)
    
    const fontSize = Math.max(4, Math.floor(vw / (0.6 * data.resolution)));
    output.style.fontSize = `${fontSize}px`;
    output.style.lineHeight = `${fontSize}px`; // Square-ish cells? No, fonts have height.
    
    resText.innerText = `RES: ${data.resolution}x${data.ascii.length}`;
};
