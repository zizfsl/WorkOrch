// =====================================================
// WorkOrch — Frontend Application Logic
// =====================================================

const API = {
  user: '/api/user',
  chat: '/api/chat',
  logout: '/auth/logout',
};

let isWaiting = false;

// ── Initialize ──
document.addEventListener('DOMContentLoaded', async () => {
  await loadUserProfile();
  hideLoading();
});

// ── Load User Profile ──
async function loadUserProfile() {
  try {
    const res = await fetch(API.user);
    if (!res.ok) {
      window.location.href = '/auth/login';
      return;
    }
    const data = await res.json();
    if (!data.authenticated) {
      window.location.href = '/auth/login';
      return;
    }

    // Update sidebar profile
    const profileName = document.getElementById('profileName');
    const profileEmail = document.getElementById('profileEmail');
    const avatarImage = document.getElementById('avatarImage');
    const avatarPlaceholder = document.getElementById('avatarPlaceholder');

    profileName.textContent = data.name || 'User';
    profileEmail.textContent = data.email || '';

    if (data.picture) {
      avatarImage.src = data.picture;
      avatarImage.style.display = 'block';
      avatarPlaceholder.style.display = 'none';
    } else {
      avatarPlaceholder.textContent = (data.name || 'U').charAt(0).toUpperCase();
      avatarImage.style.display = 'none';
      avatarPlaceholder.style.display = 'flex';
    }

    // Update welcome banner
    const firstName = (data.name || 'there').split(' ')[0];
    document.getElementById('welcomeTitle').textContent = `Welcome back, ${firstName}! 👋`;
    document.getElementById('welcomeSubtitle').textContent = `Let's make today productive. What would you like to do?`;

  } catch (err) {
    console.error('Failed to load user profile:', err);
  }
}

// ── Hide Loading Overlay ──
function hideLoading() {
  const overlay = document.getElementById('loadingOverlay');
  overlay.classList.add('hidden');
  setTimeout(() => overlay.remove(), 500);
}

// ── View Switching ──
function switchView(view) {
  // Update nav
  document.querySelectorAll('.nav-item[data-view]').forEach(item => {
    item.classList.toggle('active', item.dataset.view === view);
  });

  const quickActions = document.getElementById('quickActions');
  const welcomeBanner = document.getElementById('welcomeBanner');

  if (view === 'chat') {
    quickActions.style.display = 'none';
    welcomeBanner.style.display = 'none';
  } else {
    quickActions.style.display = 'grid';
    welcomeBanner.style.display = 'block';
  }
}

// ── Send Quick Action ──
function sendQuickAction(message) {
  switchView('chat');
  document.getElementById('chatInput').value = message;
  sendMessage();
}

// ── Handle Enter Key ──
function handleInputKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
}

// ── Send Message ──
async function sendMessage() {
  const input = document.getElementById('chatInput');
  const message = input.value.trim();
  if (!message || isWaiting) return;

  // Clear empty state
  const emptyState = document.getElementById('chatEmpty');
  if (emptyState) emptyState.remove();

  // Add user bubble
  addChatBubble(message, 'user');
  input.value = '';

  // Show typing indicator
  isWaiting = true;
  updateSendButton();
  const typingEl = showTypingIndicator();

  try {
    const res = await fetch(API.chat, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });

    const data = await res.json();

    // Remove typing indicator
    typingEl.remove();

    if (data.error) {
      addChatBubble(`⚠️ Error: ${data.error}`, 'agent');
    } else {
      addChatBubble(data.response || 'No response received.', 'agent');
    }
  } catch (err) {
    typingEl.remove();
    addChatBubble(`⚠️ Network error: ${err.message}`, 'agent');
  } finally {
    isWaiting = false;
    updateSendButton();
  }
}

// ── Add Chat Bubble ──
function addChatBubble(text, role) {
  const container = document.getElementById('chatMessages');

  const wrapper = document.createElement('div');
  wrapper.className = role === 'user' ? 'user-bubble-wrapper' : 'agent-bubble-wrapper';

  const label = document.createElement('div');
  label.className = 'chat-bubble-label';
  label.textContent = role === 'user' ? 'You' : 'WorkOrch';

  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${role}`;

  if (role === 'agent') {
    bubble.innerHTML = formatMarkdown(text);
  } else {
    bubble.textContent = text;
  }

  wrapper.appendChild(label);
  wrapper.appendChild(bubble);
  container.appendChild(wrapper);

  // Scroll to bottom
  container.scrollTop = container.scrollHeight;
}

// ── Typing Indicator ──
function showTypingIndicator() {
  const container = document.getElementById('chatMessages');
  const typing = document.createElement('div');
  typing.className = 'typing-indicator';
  typing.id = 'typingIndicator';
  typing.innerHTML = `
    <div class="typing-dot"></div>
    <div class="typing-dot"></div>
    <div class="typing-dot"></div>
  `;
  container.appendChild(typing);
  container.scrollTop = container.scrollHeight;
  return typing;
}

// ── Update Send Button State ──
function updateSendButton() {
  const btn = document.getElementById('sendBtn');
  btn.disabled = isWaiting;
}

// ── Simple Markdown Formatter ──
function formatMarkdown(text) {
  if (!text) return '';

  // Escape HTML first
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Code blocks (```)
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Bold (**text**)
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

  // Italic (*text*)
  html = html.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '<em>$1</em>');

  // Unordered lists (- item)
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

  // Ordered lists (1. item)
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

  // Headings
  html = html.replace(/^### (.+)$/gm, '<h4>$1</h4>');
  html = html.replace(/^## (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^# (.+)$/gm, '<h2>$1</h2>');

  // Line breaks
  html = html.replace(/\n/g, '<br>');

  // Clean up double <br> in lists
  html = html.replace(/<\/li><br>/g, '</li>');
  html = html.replace(/<\/ul><br>/g, '</ul>');
  html = html.replace(/<\/h(\d)><br>/g, '</h$1>');

  return html;
}

// ── Sidebar Toggle (Mobile) ──
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  sidebar.classList.toggle('open');
}

// ── Logout ──
function handleLogout() {
  if (confirm('Are you sure you want to sign out?')) {
    window.location.href = API.logout;
  }
}
