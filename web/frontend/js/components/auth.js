import { api } from '../api.js';

export function renderAuth(container, onSuccess) {
    let mode = 'login';

    function render() {
        container.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; min-height: calc(100vh - 72px); padding: 2rem;" class="animate-in">
                <div style="width: 100%; max-width: 460px;">

                    <!-- Logo & Branding -->
                    <div style="text-align: center; margin-bottom: 3rem;">
                        <div style="font-size: 2.5rem; margin-bottom: 1rem;">📔</div>
                        <h1 style="font-size: 2rem; font-weight: 900; letter-spacing: -1px; margin-bottom: 0.5rem;">
                            ${mode === 'login' ? 'Sign in to your account' : 'Create your account'}
                        </h1>
                        <p style="color: var(--text-secondary); font-size: 0.95rem;">
                            ${mode === 'login' ? 'Your AI publishing studio awaits.' : 'Join and start publishing AI-generated books.'}
                        </p>
                    </div>

                    <!-- Card -->
                    <div style="background: var(--glass-bg); border: 1px solid var(--glass-border); border-radius: 20px; padding: 2.5rem;">
                        <form id="auth-form">
                            ${mode === 'signup' ? `
                                <div class="input-group">
                                    <label>Full Name</label>
                                    <input type="text" id="name" placeholder="Your full name" required>
                                </div>
                            ` : ''}
                            <div class="input-group">
                                <label>Email Address</label>
                                <input type="email" id="email" placeholder="your@email.com" required>
                            </div>
                            <div class="input-group">
                                <label>Password</label>
                                <input type="password" id="password" placeholder="••••••••" required>
                            </div>
                            <button type="submit" style="width: 100%; height: 52px; margin-top: 0.5rem; font-size: 0.95rem;">
                                ${mode === 'login' ? 'Sign In' : 'Create Account'}
                            </button>
                            <div id="auth-error" style="color: #ff6b7a; text-align: center; margin-top: 1rem; font-size: 0.85rem; font-weight: 600; min-height: 20px;"></div>
                        </form>
                    </div>

                    <!-- Toggle -->
                    <p style="text-align: center; color: var(--text-secondary); margin-top: 1.75rem; font-size: 0.9rem;">
                        ${mode === 'login' ? "Don't have an account?" : "Already have an account?"}
                        <span id="toggle-mode" style="color: var(--acc-light); cursor: pointer; font-weight: 700; margin-left: 4px;">
                            ${mode === 'login' ? 'Sign Up' : 'Sign In'}
                        </span>
                    </p>
                </div>
            </div>
        `;

        document.getElementById('toggle-mode').onclick = () => {
            mode = mode === 'login' ? 'signup' : 'login';
            render();
        };

        document.getElementById('auth-form').onsubmit = async (e) => {
            e.preventDefault();
            const btn = e.target.querySelector('button');
            const errDiv = document.getElementById('auth-error');
            errDiv.innerText = '';
            btn.disabled = true;
            btn.innerText = 'Please wait...';

            try {
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;
                let user;

                if (mode === 'login') {
                    user = await api.login(email, password);
                } else {
                    const name = document.getElementById('name').value;
                    await api.signup(email, password, name);
                    user = await api.login(email, password);
                }

                onSuccess(user);
            } catch (err) {
                errDiv.innerText = err.message;
                btn.disabled = false;
                btn.innerText = mode === 'login' ? 'Sign In' : 'Create Account';
            }
        };
    }

    render();
}
