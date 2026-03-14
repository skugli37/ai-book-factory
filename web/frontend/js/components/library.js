import { api } from '../api.js';

export async function renderLibrary(container) {
    let allBooks = [];
    let activeCategory = 'all';
    let searchQuery = '';

    const categories = [
        { id: 'all', label: 'All Titles' },
        { id: 'business', label: 'Business & Finance' },
        { id: 'technology', label: 'Technology' },
        { id: 'self-help', label: 'Personal Growth' },
        { id: 'fiction', label: 'Fiction & Sci-Fi' },
    ];

    function getCoverBg(genre) {
        if (!genre) return 'cover-bg-default';
        const g = genre.toLowerCase();
        if (g.includes('business') || g.includes('finance')) return 'cover-bg-business';
        if (g.includes('tech')) return 'cover-bg-tech';
        if (g.includes('growth') || g.includes('self')) return 'cover-bg-growth';
        if (g.includes('fiction') || g.includes('sci')) return 'cover-bg-fiction';
        if (g.includes('romance')) return 'cover-bg-romance';
        return 'cover-bg-default';
    }

    function calcReadTime(wordCount) {
        if (!wordCount) return '–';
        const m = Math.ceil(wordCount / 250);
        return m < 60 ? `${m} min` : `${(m / 60).toFixed(1)} hr`;
    }

    async function load() {
        container.innerHTML = `
            <div style="display:flex; align-items:center; justify-content:center; height:60vh; color: var(--text-muted);">
                Loading your collection...
            </div>`;
        try {
            allBooks = await api.getBooks();
            render();
        } catch (err) {
            container.innerHTML = `<p style="color:#ff6b7a; padding:2rem;">Error: ${err.message}</p>`;
        }
    }

    function render() {
        let filtered = allBooks;

        if (activeCategory !== 'all') {
            filtered = filtered.filter(b => b.genre && b.genre.toLowerCase().includes(activeCategory));
        }

        if (searchQuery) {
            const q = searchQuery.toLowerCase();
            filtered = filtered.filter(b =>
                b.title.toLowerCase().includes(q) ||
                (b.genre && b.genre.toLowerCase().includes(q))
            );
        }

        container.innerHTML = `
            <div class="animate-in">
                <div style="margin-bottom: 3rem;">
                    <h1 style="font-size: 2.5rem; font-weight: 900; letter-spacing: -1.5px; margin-bottom: 0.5rem;">
                        Your <span class="glow-text">Library</span>
                    </h1>
                    <p style="color: var(--text-secondary);">${allBooks.length} published volume${allBooks.length !== 1 ? 's' : ''} in your collection</p>
                </div>

                <div class="lib-category-bar">
                    ${categories.map(c => `
                        <button class="cat-pill ${activeCategory === c.id ? 'active' : ''}" data-cat="${c.id}">${c.label}</button>
                    `).join('')}
                    <div style="margin-left: auto; position: relative;">
                        <span style="position: absolute; left: 1rem; top: 50%; transform: translateY(-50%); color: var(--text-muted); font-size: 0.8rem;">🔍</span>
                        <input type="text" id="lib-search" placeholder="Search titles..."
                            value="${searchQuery}"
                            style="padding: 0.5rem 1rem 0.5rem 2.5rem; margin: 0; border-radius: 50px; width: 220px; font-size: 0.82rem; height: auto;">
                    </div>
                </div>

                <div class="book-grid">
                    ${filtered.length === 0 ? `
                        <div class="empty-state">
                            <div class="empty-state-icon">${searchQuery ? '🔍' : '📚'}</div>
                            <h2 style="margin-bottom: 0.75rem;">${searchQuery ? 'No results found' : 'Your library is empty'}</h2>
                            <p style="color: var(--text-secondary);">
                                ${searchQuery ? `No books matching "${searchQuery}"` : 'Start generating your first masterpiece from the Workspace.'}
                            </p>
                        </div>
                    ` : filtered.map(book => `
                        <div class="book-card">
                            <div class="book-cover-wrap">
                                <div class="book-cover ${getCoverBg(book.genre)}">
                                    <div class="book-spine-line"></div>
                                    <div class="cover-pattern"></div>
                                    <div class="cover-genre-badge">${book.genre || 'General'}</div>
                                    <div class="cover-title-text">${book.title}</div>
                                    <div class="cover-author-text">${window.app?.user?.full_name || 'AI Author'}</div>
                                </div>
                            </div>

                            <div class="book-meta">
                                <h3>${book.title}</h3>
                                <div class="book-meta-row" style="margin-bottom: 0.5rem;">
                                    <span>${new Date(book.created_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}</span>
                                    <span>${calcReadTime(book.word_count)} read</span>
                                </div>
                                <div>
                                    <span class="book-status-badge ${book.status === 'completed' ? 'badge-done' : 'badge-pending'}">
                                        ${book.status === 'completed' ? '✓ Complete' : `${book.progress}% generating`}
                                    </span>
                                </div>

                                <div class="book-actions">
                                    ${book.status === 'completed' ? `
                                        <a href="/outputs/${book.docx_path}" download class="btn-action">DOCX</a>
                                        <a href="/outputs/${book.marketing_kit_path}" download class="btn-action">KIT</a>
                                    ` : `
                                        <div class="btn-action" style="opacity:0.4; cursor:default;">DOCX</div>
                                        <div class="btn-action" style="opacity:0.4; cursor:default;">KIT</div>
                                    `}
                                    <button class="btn-action danger delete-book" data-id="${book.id}">✕</button>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        // Category filter
        container.querySelectorAll('.cat-pill').forEach(btn => {
            btn.onclick = () => {
                activeCategory = btn.dataset.cat;
                render();
            };
        });

        // Search
        const si = document.getElementById('lib-search');
        si.oninput = (e) => {
            searchQuery = e.target.value;
            render();
            const newSi = document.getElementById('lib-search');
            if (newSi) {
                newSi.focus();
                newSi.setSelectionRange(searchQuery.length, searchQuery.length);
            }
        };

        // Delete
        container.querySelectorAll('.delete-book').forEach(btn => {
            btn.onclick = async (e) => {
                e.stopPropagation();
                const id = e.currentTarget.dataset.id;
                if (confirm('Permanently remove this title from your library?')) {
                    await api.deleteBook(id);
                    load();
                }
            };
        });
    }

    load();
}
