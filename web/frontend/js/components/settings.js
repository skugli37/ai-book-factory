import { api } from '../api.js';

export async function renderSettings(container) {
    let savedKeys = [];

    async function load() {
        container.innerHTML = `<div class="animate-in" style="padding: 2rem; text-align: center;"><h1>Syncing your configurations...</h1></div>`;
        try {
            savedKeys = await api.getKeys();
            render();
        } catch (err) {
            container.innerHTML = `<div class="glass-panel" style="padding: 2rem; color: #ff4757;">Error: ${err.message}</div>`;
        }
    }

    function render() {
        container.innerHTML = `
            <div class="animate-in">
                <header style="margin-bottom: 3.5rem;">
                    <h1 style="font-size: 3rem; margin-bottom: 0.5rem; letter-spacing: -1.5px;">Control <span class="glow-text">Center</span></h1>
                    <p style="font-size: 1.2rem; color: var(--text-secondary);">Manage your AI engines, security, and interface branding.</p>
                </header>

                <div class="grid" style="display: grid; grid-template-columns: 1.5fr 1fr; gap: 3rem;">
                    <section class="glass-panel" style="padding: 3rem;">
                        <h2 style="font-size: 1.5rem; margin-bottom: 2rem; display: flex; align-items: center; gap: 15px;">
                            <span style="background: var(--acc-color); padding: 8px; border-radius: 10px; font-size: 1rem;">🔑</span>
                            Neural Engine Access
                        </h2>
                        <div id="keys-list" style="margin-bottom: 2.5rem; display: flex; flex-direction: column; gap: 1rem;">
                            ${['hf', 'groq'].map(service => {
                                const isSaved = savedKeys.find(k => k.service === service);
                                return `
                                    <div class="glass-panel" style="display: flex; justify-content: space-between; align-items: center; padding: 1.25rem 1.5rem; background: rgba(255,255,255,0.02); border-radius: 14px;">
                                        <div style="display: flex; align-items: center; gap: 15px;">
                                            <div style="width: 40px; height: 40px; background: ${isSaved ? 'rgba(46, 213, 115, 0.1)' : 'rgba(255, 71, 87, 0.1)'}; color: ${isSaved ? '#2ed573' : '#ff4757'}; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.7rem;">
                                                ${service.toUpperCase()}
                                            </div>
                                            <div>
                                                <div style="font-weight: 700; font-size: 1rem;">${service === 'hf' ? 'Hugging Face' : 'Groq Cloud'}</div>
                                                <div style="font-size: 0.75rem; color: ${isSaved ? '#2ed573' : '#ff4757'}; font-weight: 600;">
                                                    ${isSaved ? 'CONNECTION SECURED' : 'ACTION REQUIRED'}
                                                </div>
                                            </div>
                                        </div>
                                        ${isSaved ? `<button class="delete-key" data-service="${service}" style="background: rgba(255,71,87,0.1); color: #ff4757; text-transform: none; font-size: 0.75rem; padding: 8px 15px; box-shadow: none;">Disconnect</button>` : '<div style="font-size: 0.75rem; color: var(--text-muted);">NOT CONFIGURED</div>'}
                                    </div>
                                `;
                            }).join('')}
                        </div>

                        <div class="glass-panel" style="padding: 2rem; background: rgba(0,0,0,0.2);">
                            <h3 style="margin-bottom: 1.5rem; font-size: 1rem; color: var(--text-primary);">Update Engine Credentials</h3>
                            <form id="key-form">
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
                                    <div>
                                        <label>Service</label>
                                        <select id="key-service">
                                            <option value="hf">Hugging Face (Vision/Assets)</option>
                                            <option value="groq">Groq (LLM Generator)</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label>API Key</label>
                                        <input type="password" id="key-value" placeholder="gsk_••••••••" required>
                                    </div>
                                </div>
                                <div style="display: flex; gap: 15px;">
                                    <button type="submit" style="flex: 2;">Provision Key</button>
                                    <button type="button" id="test-key-btn" style="flex: 1; background: var(--glass-bg); text-transform: none; border: 1px solid var(--glass-border);">Test Uplink</button>
                                </div>
                            </form>
                            <div id="key-status" style="margin-top: 1.5rem; text-align: center; font-size: 0.9rem; font-weight: 600;"></div>
                        </div>
                    </section>

                    <section class="stagger-children">
                        <div class="glass-panel" style="padding: 2.5rem; background: linear-gradient(135deg, rgba(124, 58, 237, 0.1), transparent);">
                            <h2 style="font-size: 1.5rem; margin-bottom: 1.5rem;">🎨 Interface</h2>
                            <div style="display: flex; flex-direction: column; gap: 1.5rem;">
                                <div>
                                    <label>Primary Brand Accents</label>
                                    <input type="color" id="brand-color" value="${localStorage.getItem('brandColor') || '#7c3aed'}" style="height: 60px; padding: 8px; border-radius: 12px; cursor: pointer;">
                                </div>
                                <button id="save-branding" style="width: 100%;">Sync Appearance</button>
                            </div>
                        </div>
                    </section>
                </div>
            </div>
        `;

        document.getElementById('key-form').onsubmit = async (e) => {
            e.preventDefault();
            const service = document.getElementById('key-service').value;
            const key = document.getElementById('key-value').value;
            await api.saveKey(service, key);
            load();
        };

        document.getElementById('test-key-btn').onclick = async () => {
            const service = document.getElementById('key-service').value;
            const key = document.getElementById('key-value').value;
            const statusDiv = document.getElementById('key-status');
            statusDiv.innerText = 'Initializing handshake...';
            statusDiv.style.color = 'white';
            
            try {
                const res = await api.testKey(service, key);
                if (res.valid) {
                    statusDiv.innerText = '✅ UPLINK ESTABLISHED';
                    statusDiv.style.color = '#2ed573';
                } else {
                    statusDiv.innerText = '❌ HANDSHAKE FAILED: ' + res.error;
                    statusDiv.style.color = '#ff4757';
                }
            } catch (err) {
                statusDiv.innerText = '❌ CONNECTION ERROR: ' + err.message;
                statusDiv.style.color = '#ff4757';
            }
        };

        document.getElementById('save-branding').onclick = () => {
            const color = document.getElementById('brand-color').value;
            localStorage.setItem('brandColor', color);
            document.documentElement.style.setProperty('--acc-color', color);
            alert('Visual matrix updated. Premium theme synced!');
        };

        document.querySelectorAll('.delete-key').forEach(btn => {
            btn.onclick = async (e) => {
                const service = e.target.dataset.service;
                if (confirm(`Revoke access for ${service.toUpperCase()}?`)) {
                    await api.deleteKey(service);
                    load();
                }
            };
        });
    }

    load();
}
