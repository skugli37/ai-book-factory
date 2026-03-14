import { api } from '../api.js';

export function renderDashboard(container, user) {
    function getCoverBg(genre) {
        if (!genre) return 'cover-bg-default';
        const g = genre.toLowerCase();
        if (g.includes('business') || g.includes('finance')) return 'cover-bg-business';
        if (g.includes('tech')) return 'cover-bg-tech';
        if (g.includes('growth') || g.includes('self')) return 'cover-bg-growth';
        if (g.includes('fiction') || g.includes('sci')) return 'cover-bg-fiction';
        return 'cover-bg-default';
    }

    async function render() {
        const [stats, books] = await Promise.all([
            api.getStats().catch(() => ({ total_books: 0, total_words: 0 })),
            api.getBooks().catch(() => [])
        ]);

        const latest = books.length > 0 ? books[0] : null;

        container.innerHTML = `
            <div class="animate-in">
                <!-- Page Header -->
                <div style="margin-bottom: 3rem;">
                    <h1 style="font-size: 2.5rem; font-weight: 900; letter-spacing: -1.5px; margin-bottom: 0.5rem;">
                        Welcome back, <span class="glow-text">${(user && user.full_name) || (user && user.email?.split('@')[0]) || 'Author'}</span>
                    </h1>
                    <p style="color: var(--text-secondary); font-size: 1rem;">Let's create your next masterpiece.</p>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 340px; gap: 2.5rem; align-items: start;">

                    <!-- LEFT: Generate Form -->
                    <div>
                        ${latest ? `
                        <!-- Featured Latest -->
                        <section style="margin-bottom: 2.5rem;">
                            <div style="font-size: 0.7rem; font-weight: 800; letter-spacing: 3px; color: var(--text-muted); margin-bottom: 1.25rem; text-transform: uppercase;">✦ Latest Title</div>
                            <div style="background: var(--glass-bg); border: 1px solid var(--glass-border); border-radius: 16px; overflow: hidden; display: grid; grid-template-columns: 130px 1fr;">
                                <div class="book-cover ${getCoverBg(latest.genre)}" style="border-radius: 0; padding: 1.5rem 1rem; min-height: 200px;">
                                    <div class="book-spine-line"></div>
                                    <div class="cover-pattern"></div>
                                    <div class="cover-genre-badge">${latest.genre}</div>
                                    <div class="cover-title-text" style="font-size: 0.85rem;">${latest.title}</div>
                                </div>
                                <div style="padding: 2rem; display: flex; flex-direction: column; justify-content: center; gap: 0.75rem;">
                                    <span class="book-status-badge ${latest.status === 'completed' ? 'badge-done' : 'badge-pending'}">
                                        ${latest.status === 'completed' ? '✓ Complete' : `${latest.progress}% generating`}
                                    </span>
                                    <h3 style="font-size: 1.25rem;">${latest.title}</h3>
                                    <p style="font-size: 0.85rem; color: var(--text-secondary); line-height: 1.5;">
                                        ${latest.topic ? latest.topic.substring(0, 100) + '…' : 'An AI-generated masterpiece.'}
                                    </p>
                                    ${latest.status === 'completed' ? `
                                        <div style="display: flex; gap: 0.75rem; margin-top: 0.5rem;">
                                            <a href="/outputs/${latest.docx_path}" download class="btn-action" style="flex:0; padding: 10px 20px; border-radius: 10px;">Get DOCX</a>
                                            <a href="/outputs/${latest.marketing_kit_path}" download class="btn-action" style="flex:0; padding: 10px 20px; border-radius: 10px;">Marketing Kit</a>
                                        </div>
                                    ` : `
                                        <div class="progress-bar" style="margin-top: 0.5rem;">
                                            <div class="progress-fill" style="width: ${latest.progress}%;"></div>
                                        </div>
                                    `}
                                </div>
                            </div>
                        </section>
                        ` : ''}

                        <!-- Generate New -->
                        <section style="background: var(--glass-bg); border: 1px solid var(--glass-border); border-radius: 20px; padding: 2.5rem;">
                            <h2 style="font-size: 1.4rem; margin-bottom: 1.75rem; display: flex; align-items: center; gap: 12px;">
                                <span style="background: linear-gradient(135deg, var(--acc-color), #4338ca); padding: 8px 10px; border-radius: 10px; font-size: 1rem;">🚀</span>
                                Generate New Volume
                            </h2>
                            <form id="book-form">
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem;">
                                    <div class="input-group">
                                        <label>Book Title</label>
                                        <input type="text" id="book-title" placeholder="The Art of AI Strategy">
                                    </div>
                                    <div class="input-group">
                                        <label>Genre</label>
                                        <select id="book-genre">
                                            <option value="business">Business & Finance</option>
                                            <option value="technology">Technology & Future</option>
                                            <option value="self-help">Personal Growth</option>
                                            <option value="fiction">Science Fiction</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="input-group">
                                    <label>Research Topic</label>
                                    <textarea id="book-topic" rows="3" placeholder="What should this book cover? Be specific — the AI will research and write it." style="resize: none;"></textarea>
                                </div>
                                <button type="submit" style="width: 100%; height: 52px; font-size: 0.95rem;">Initialize Generation Engine →</button>
                                <div id="gen-error" style="color: #ff6b7a; text-align: center; margin-top: 1rem; font-size: 0.85rem;"></div>
                            </form>
                        </section>
                    </div>

                    <!-- RIGHT: Stats Column -->
                    <div style="display: flex; flex-direction: column; gap: 1.5rem;">
                        <div style="background: var(--glass-bg); border: 1px solid var(--glass-border); border-radius: 16px; padding: 1.75rem; text-align: center; background: linear-gradient(135deg, rgba(124,58,237,0.08), var(--glass-bg));">
                            <div style="font-size: 0.7rem; font-weight: 800; letter-spacing: 3px; color: var(--text-muted); margin-bottom: 1rem; text-transform: uppercase;">Published</div>
                            <div style="font-size: 4.5rem; font-weight: 900; font-family: 'Outfit'; line-height: 1; color: var(--acc-light);">${stats.total_books}</div>
                            <div style="color: var(--text-secondary); font-size: 0.82rem; margin-top: 0.75rem;">Volumes in Library</div>
                        </div>

                        <div style="background: var(--glass-bg); border: 1px solid var(--glass-border); border-radius: 16px; padding: 1.75rem; text-align: center;">
                            <div style="font-size: 0.7rem; font-weight: 800; letter-spacing: 3px; color: var(--text-muted); margin-bottom: 1rem; text-transform: uppercase;">Words Written</div>
                            <div style="font-size: 2.75rem; font-weight: 900; font-family: 'Outfit'; line-height: 1;">${(stats.total_words || 0).toLocaleString()}</div>
                            <div style="color: var(--text-secondary); font-size: 0.82rem; margin-top: 0.75rem;">AI-crafted words</div>
                        </div>

                        <button onclick="app.navigate('library')"
                            style="background: var(--glass-bg); border: 1px solid var(--glass-border); color: white; font-size: 0.85rem; text-transform: none; letter-spacing: 0; box-shadow: none; padding: 0.9rem; border-radius: 12px;">
                            Browse Library →
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.getElementById('book-form').onsubmit = async (e) => {
            e.preventDefault();
            const btn = e.target.querySelector('button[type="submit"]');
            const errDiv = document.getElementById('gen-error');
            errDiv.innerText = '';
            btn.disabled = true;
            btn.innerText = 'Initializing...';

            try {
                const topic = document.getElementById('book-topic').value;
                if (!topic.trim()) throw new Error('Please describe the topic of your book.');

                const result = await api.createBook({
                    title: document.getElementById('book-title').value || topic,
                    topic,
                    genre: document.getElementById('book-genre').value,
                    chapters: 10
                });
                window.app.navigate('progress', result.job_id);
            } catch (err) {
                errDiv.innerText = err.message;
                btn.disabled = false;
                btn.innerText = 'Initialize Generation Engine →';
            }
        };
    }

    render();
}
