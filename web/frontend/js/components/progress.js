export function renderProgress(container, jobId) {
    container.innerHTML = `
        <div class="animate-in" style="max-width: 900px; margin: 0 auto;">
            <header style="text-align: center; margin-bottom: 4rem;">
                <div style="display: inline-block; padding: 1.5rem; background: var(--acc-glow); border-radius: 30px; margin-bottom: 2rem; border: 1px solid var(--acc-color);">
                    <div class="loader-diamond" style="font-size: 3rem; animation: pulse 2s infinite;">💎</div>
                </div>
                <h1 style="font-size: 3.5rem; letter-spacing: -2px; margin-bottom: 1rem;">Forging Your <span class="glow-text">Masterpiece</span></h1>
                <p id="progress-stage" style="color: var(--text-secondary); font-size: 1.2rem; text-transform: uppercase; letter-spacing: 4px;">Initializing Neural Engines...</p>
            </header>
            
            <div class="glass-panel" style="padding: 3rem; margin-bottom: 3rem;">
                <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 15px;">
                    <div style="font-weight: 800; font-family: 'Outfit'; font-size: 1.1rem; color: var(--text-primary);">GENERATION PROGRESS</div>
                    <div id="progress-percent" style="font-weight: 900; font-size: 2rem; color: var(--acc-light);">0%</div>
                </div>
                <div class="progress-bar" style="height: 16px; border-radius: 8px;">
                    <div id="progress-fill" class="progress-fill" style="width: 0%; box-shadow: 0 0 20px var(--acc-glow);"></div>
                </div>
            </div>

            <div class="glass-panel" style="background: rgba(0,0,0,0.4); border-radius: 12px; height: 350px; display: flex; flex-direction: column;">
                <div style="padding: 1rem 1.5rem; border-bottom: 1px solid var(--glass-border); display: flex; align-items: center; gap: 10px;">
                    <div style="width: 10px; height: 10px; background: #2ed573; border-radius: 50%;"></div>
                    <div style="font-size: 0.8rem; font-weight: 800; color: var(--text-muted); letter-spacing: 1px;">LIVE ENGINE HEARTBEAT</div>
                </div>
                <div id="live-logs" style="flex-grow: 1; padding: 1.5rem; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; overflow-y: auto; line-height: 1.8; color: #a5b4fc;">
                    <span style="color: var(--text-muted);">> Establishing secure uplink...</span><br>
                </div>
            </div>

            <div style="text-align: center; margin-top: 3rem;">
                <button id="back-to-lib" style="display: none; height: 60px; padding: 0 3rem;">Access Finished Volume</button>
            </div>
        </div>
    `;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${jobId}`;
    const ws = new WebSocket(wsUrl);

    const logDiv = document.getElementById('live-logs');
    const fill = document.getElementById('progress-fill');
    const stage = document.getElementById('progress-stage');
    const percent = document.getElementById('progress-percent');

    function addLog(msg) {
        const line = document.createElement('div');
        line.innerText = `> ${msg}`;
        logDiv.appendChild(line);
        logDiv.scrollTop = logDiv.scrollHeight;
    }

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.stage && data.percent !== -1) stage.innerText = data.stage.toUpperCase() + "...";
        if (data.percent !== undefined && data.percent > -1) {
            fill.style.width = data.percent + '%';
            percent.innerText = data.percent + '%';
        }
        if (data.latest_text) {
            addLog(data.latest_text);
        }

        if (data.percent === 100 || data.stage === 'complete') {
            addLog("✅ Generation complete! Packaging assets...");
            document.getElementById('back-to-lib').style.display = 'inline-block';
            ws.close();
        }

        if (data.stage === 'failed') {
            addLog("❌ Error: " + (data.latest_text || "Unknown failure"));
            document.getElementById('back-to-lib').style.display = 'inline-block';
            stage.style.color = '#ff4757';
        }
    };

    ws.onerror = () => addLog("⚠️ WebSocket error. Check server logs.");
    ws.onclose = () => addLog("📡 Connection ended.");

    document.getElementById('back-to-lib').onclick = () => window.app.navigate('library');
}
