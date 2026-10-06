// ==========================================
// AI Maths Tutor — Complete Frontend Logic
// ==========================================

// Global State
let currentStyle = 'simple';
let currentChatId = null;
let allChatsCache = [];

// 🌐 Dynamic API URL (Automatically switches to public HTTPS tunnel on GitHub Pages / Phone)
const API_BASE_URL = (window.location.protocol === 'https:' || (window.location.hostname !== '127.0.0.1' && window.location.hostname !== 'localhost'))
    ? 'https://since-energy-coated-minus.trycloudflare.com'
    : 'http://127.0.0.1:8000';

// 0. Student Profile Initialization (ChatGPT & Claude Style)
const currentStudentName = localStorage.getItem('studentName') || 'Sameed Khan';
const userDisplayNameEl = document.getElementById('user-display-name');
if (userDisplayNameEl) {
    userDisplayNameEl.innerText = currentStudentName;
}

// Calculate User Initials (e.g. Sameed Khan -> SK, Ali -> AL, Alex -> AS)
const avatarCircleEl = document.getElementById('user-avatar-circle');
if (avatarCircleEl) {
    const parts = currentStudentName.replace(/[^a-zA-Z\s]/g, '').trim().split(' ').filter(p => p.length > 0);
    let initials = 'SK';
    if (parts.length >= 2) {
        initials = (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    } else if (parts.length === 1) {
        initials = parts[0].slice(0, 2).toUpperCase();
    }
    avatarCircleEl.innerText = initials;
}

const savedGrade = localStorage.getItem('studentGrade') || 'Class 11';
const userPlanTagEl = document.getElementById('user-plan-tag');
if (userPlanTagEl) {
    userPlanTagEl.innerText = `Student · ${savedGrade}`;
}

const welcomeGreetingEl = document.getElementById('welcome-greeting');
if (welcomeGreetingEl) {
    welcomeGreetingEl.innerText = `Hello ${currentStudentName}!`;
}

// Function to bind click on Pinterest Topic Starter Cards
function bindTopicCards() {
    const topicCards = document.querySelectorAll('.topic-card');
    topicCards.forEach(card => {
        card.addEventListener('click', () => {
            const question = card.getAttribute('data-question');
            if (question && userInput) {
                userInput.value = question;
                if (chatForm) {
                    chatForm.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
                }
            }
        });
    });
}
bindTopicCards();

const badgeEl = document.querySelector('.chat-header span');
if (badgeEl && savedGrade) {
    badgeEl.innerText = `NCERT ${savedGrade}`;
}

// 🧭 ChatGPT Style Sidebar Navigation Menu
const navNcertClassesBtn = document.getElementById('nav-ncert-classes-btn');
const navTutorStyleBtn = document.getElementById('nav-tutor-style-btn');
const navClassBadge = document.getElementById('nav-class-badge');
const navStyleBadge = document.getElementById('nav-style-badge');

if (navClassBadge && savedGrade) {
    navClassBadge.innerText = savedGrade;
}

if (navStyleBadge) {
    const currentStyleVal = localStorage.getItem('defaultStyle') || 'simple';
    navStyleBadge.innerText = currentStyleVal === 'sports' ? 'Cricket' : currentStyleVal === 'step-by-step' ? 'Steps' : 'Intuition';
}

if (navNcertClassesBtn) {
    navNcertClassesBtn.addEventListener('click', () => {
        openSettingsToTab('tab-education');
    });
}

if (navTutorStyleBtn) {
    navTutorStyleBtn.addEventListener('click', () => {
        openSettingsToTab('tab-style');
    });
}




// 1. Math Shortcuts Toolbar (x², √, π etc.)
const symButtons = document.querySelectorAll('.sym-btn');
const userInput = document.getElementById('user-input');

symButtons.forEach(button => {
    button.addEventListener('click', () => {
        if (userInput) {
            userInput.value += button.innerText;
            userInput.focus();
        }
    });
});

// ⌨️ Enter Key to Send Message (Shift+Enter for newline)
if (userInput) {
    userInput.addEventListener('keydown', function (e) {
        if ((e.key === 'Enter' || e.keyCode === 13) && !e.shiftKey && !e.ctrlKey && !e.altKey) {
            e.preventDefault();
            submitUserMessage();
        }
    });
}


// 2. Plus Button (+ Photo / File Upload)
const plusBtn = document.getElementById('plus-btn');
const fileInput = document.getElementById('file-input');
const photoTag = document.getElementById('photo-preview-tag');
const photoName = document.getElementById('photo-name');
const removePhoto = document.getElementById('remove-photo');

if (plusBtn && fileInput) {
    plusBtn.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            photoName.innerText = e.target.files[0].name;
            photoTag.style.display = 'inline-flex';
        }
    });
}

if (removePhoto && fileInput) {
    removePhoto.addEventListener('click', () => {
        fileInput.value = '';
        photoTag.style.display = 'none';
    });
}


// 3. Groq LLM Model Picker Menu
const modelPillBtn = document.getElementById('model-pill-btn');
const modelDropdown = document.getElementById('model-dropdown-menu');
const selectedModelText = document.getElementById('selected-model-text');
const menuItems = document.querySelectorAll('.model-dropdown-menu .menu-item');

let currentModel = localStorage.getItem('tutorModel') || 'openai/gpt-oss-120b';

// Restore saved model on load
if (selectedModelText && currentModel) {
    let found = false;
    menuItems.forEach(item => {
        if (item.getAttribute('data-model') === currentModel) {
            menuItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            selectedModelText.innerText = item.getAttribute('data-text');
            found = true;
        }
    });
    if (!found) {
        currentModel = 'openai/gpt-oss-120b';
        localStorage.setItem('tutorModel', currentModel);
    }
}

if (modelPillBtn && modelDropdown) {
    modelPillBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const isHidden = modelDropdown.style.display === 'none' || modelDropdown.style.display === '';
        modelDropdown.style.display = isHidden ? 'block' : 'none';
    });

    document.addEventListener('click', () => {
        modelDropdown.style.display = 'none';
    });
}

menuItems.forEach(item => {
    item.addEventListener('click', () => {
        menuItems.forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        currentModel = item.getAttribute('data-model') || 'openai/gpt-oss-120b';
        localStorage.setItem('tutorModel', currentModel);
        if (selectedModelText) {
            selectedModelText.innerText = item.getAttribute('data-text');
        }
        modelDropdown.style.display = 'none';
    });
});


// 4. Voice Mic Button (Speech-to-Text)
const micBtn = document.getElementById('mic-btn');
if (micBtn) {
    micBtn.addEventListener('click', () => {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognition = new SpeechRecognition();
            recognition.lang = 'en-IN';
            micBtn.style.color = '#ef4444'; // Red recording indicator
            recognition.start();

            recognition.onresult = (event) => {
                userInput.value += event.results[0][0].transcript;
                micBtn.style.color = 'inherit';
            };
            recognition.onerror = () => { micBtn.style.color = 'inherit'; };
            recognition.onend = () => { micBtn.style.color = 'inherit'; };
        } else {
            alert('Voice recording supported in Chrome & Edge browsers.');
        }
    });
}


// 5. Chat Submission Logic (Ask Tutor)
function submitUserMessage() {
    if (!userInput) return;
    const question = userInput.value.trim();
    if (!question && (!fileInput || !fileInput.files.length)) return;

    let displayQuestion = question;
    if (fileInput && fileInput.files.length > 0) {
        displayQuestion = `📷 [Uploaded: ${fileInput.files[0].name}]<br>` + question;
        fileInput.value = '';
        if (photoTag) photoTag.style.display = 'none';
    }

    // Student message bubble
    appendMessage('You', displayQuestion, 'user');
    userInput.value = '';

    const selectedLanguage = localStorage.getItem('tutorLanguage') || 'hinglish';
    const isNewSession = !currentChatId;

    // 🚀 Asli FastAPI Backend API Call:
    fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            question: question,
            style: currentStyle,
            language: selectedLanguage,
            model: currentModel,
            chat_id: currentChatId,
            user_id: getUserId()
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.reply) {
            appendMessage('AI Maths Tutor', data.reply, 'assistant');
        }
        if (data.chat_id) {
            currentChatId = data.chat_id;
            localStorage.setItem('activeChatId', data.chat_id);
            try {
                const url = new URL(window.location.href);
                url.searchParams.set('c', data.chat_id);
                window.history.replaceState({ chatId: data.chat_id }, '', url.toString());
            } catch (e) {}

            const topicEl = document.getElementById('current-topic');
            if (topicEl && data.question) {
                topicEl.innerText = data.question.length > 35 ? data.question.slice(0, 35) + '...' : data.question;
            }
            // Save messages to local cache
            saveMessageToCache(data.chat_id, { sender: 'user', text: displayQuestion });
            if (data.reply) {
                saveMessageToCache(data.chat_id, { sender: 'assistant', text: data.reply });
            }
        }
        fetchAndRenderSidebarChats();
    })
    .catch(error => {
        console.error('Error:', error);
        // Fallback offline simulation so user experience is never broken
        const offlineChatId = currentChatId || Date.now();
        currentChatId = offlineChatId;
        const fallbackReply = `💡 **Concept Explanation for "${question}":**\nMathematics mein kisi bhi problem ko step-by-step visualize karein!\n\nStandard Result: $$\\int x^n dx = \\frac{x^{n+1}}{n+1} + C$$\n\n🎯 **Tip:** Backend server ko connect karne ke liye Python server chalu rakhein.`;
        appendMessage('AI Maths Tutor', fallbackReply, 'assistant');

        // Cache local chat & messages
        saveMessageToCache(offlineChatId, { sender: 'user', text: displayQuestion });
        saveMessageToCache(offlineChatId, { sender: 'assistant', text: fallbackReply });

        if (isNewSession) {
            const newChatObj = {
                id: offlineChatId,
                title: question.slice(0, 35) + (question.length > 35 ? '...' : ''),
                is_pinned: 0,
                created_at: new Date().toISOString()
            };
            allChatsCache.unshift(newChatObj);
            saveCachedChats(allChatsCache);
            renderSidebarChats(allChatsCache);
        }
    });
}

const chatForm = document.getElementById('chat-form');
const messagesContainer = document.getElementById('messages-container');
const sendBtn = document.getElementById('send-btn');

if (chatForm) {
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        submitUserMessage();
    });
}

if (sendBtn) {
    sendBtn.addEventListener('click', (e) => {
        e.preventDefault();
        submitUserMessage();
    });
}


// Helper: Markdown and Math Formatter
function renderMarkdown(rawText) {
    if (!rawText) return '';
    let html = rawText;

    // Code blocks ```...```
    html = html.replace(/```([\s\S]*?)```/g, (match, p1) => {
        return `<div class="math-code-block"><pre>${p1.trim()}</pre></div>`;
    });

    // Headers #####, ####, ###, ##, #
    html = html.replace(/^##### (.*$)/gim, '<h6 class="chat-h6">$1</h6>');
    html = html.replace(/^#### (.*$)/gim, '<h5 class="chat-h5">$1</h5>');
    html = html.replace(/^### (.*$)/gim, '<h5 class="chat-h5">$1</h5>');
    html = html.replace(/^## (.*$)/gim, '<h4 class="chat-h4">$1</h4>');
    html = html.replace(/^# (.*$)/gim, '<h3 class="chat-h3">$1</h3>');

    // Bold **text**
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Italic *text*
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Bullet points
    html = html.replace(/^\s*[-•]\s+(.*)$/gim, '<li class="chat-list-item">$1</li>');

    // Numbered lists
    html = html.replace(/^\s*(\d+)\.\s+(.*)$/gim, '<li class="chat-num-item"><strong>$1.</strong> $2</li>');

    // Paragraph line breaks
    html = html.replace(/\n\n/g, '<div class="chat-gap"></div>');
    html = html.replace(/\n/g, '<br>');

    return html;
}

// Helper: Append Message Bubble
function appendMessage(sender, text, type) {
    const welcomeHero = document.getElementById('welcome-hero');
    if (welcomeHero) welcomeHero.remove();

    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${type}`;
    const avatar = type === 'user' ? '🎓' : '👩‍🏫';

    msgDiv.innerHTML = `
        <div class="avatar">${avatar}</div>
        <div class="message-content">
            <h4>${sender}</h4>
            <div class="message-body">${type === 'assistant' ? renderMarkdown(text) : text.replace(/\n/g, '<br>')}</div>
        </div>
    `;

    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // Message aate hi LaTeX math formulas ko sundar equation me render karo
    if (window.renderMathInElement) {
        renderMathInElement(msgDiv, {
            delimiters: [
                {left: '$$', right: '$$', display: true},
                {left: '$', right: '$', display: false},
                {left: '\\[', right: '\\]', display: true},
                {left: '\\(', right: '\\)', display: false}
            ],
            throwOnError: false
        });
    }
}


// 6. ChatGPT & Claude Style Chat History & Session Switcher
const newChatBtn = document.getElementById('new-chat-btn');
const historyList = document.getElementById('history-list');
const pinnedList = document.getElementById('pinned-list');

// Helper: Render Welcome Hero & Topic Starter Cards
function renderWelcomeHero() {
    if (!messagesContainer) return;
    messagesContainer.innerHTML = `
        <div class="welcome-hero" id="welcome-hero">
            <h2 class="welcome-greeting" id="welcome-greeting">Hello ${currentStudentName}!</h2>
            <p class="welcome-subtitle">How can I help with <strong>NCERT Maths</strong> today?</p>
            
            <!-- 🔮 Center 3D Holographic Math Orb with Orbiting Math Symbols -->
            <div class="math-orb-system">
                <div class="math-orb-core"></div>
                <div class="math-orb-glow"></div>

                <!-- Outer Floating Mathematical Operator Particles -->
                <div class="orbit-particle p-plus">+</div>
                <div class="orbit-particle p-minus">−</div>
                <div class="orbit-particle p-multiply">×</div>
                <div class="orbit-particle p-divide">÷</div>
                <div class="orbit-particle p-infinity">∞</div>
                <div class="orbit-particle p-delta">Δ</div>

                <!-- 1st Rotating Ring (Horizontal-ish) -->
                <div class="math-orb-ring ring-horizontal">
                    <span class="orbit-symbol sym-pi">π</span>
                    <span class="orbit-symbol sym-sqrt">√</span>
                    <span class="orbit-symbol sym-plus">+</span>
                </div>

                <!-- 2nd Rotating Ring (Inclined Right) -->
                <div class="math-orb-ring ring-inclined">
                    <span class="orbit-symbol sym-sigma">Σ</span>
                    <span class="orbit-symbol sym-integral">∫</span>
                    <span class="orbit-symbol sym-theta">θ</span>
                    <span class="orbit-symbol sym-minus">−</span>
                </div>

                <!-- 3rd Rotating Ring (Inclined Left) -->
                <div class="math-orb-ring ring-vertical">
                    <span class="orbit-symbol sym-multiply">×</span>
                    <span class="orbit-symbol sym-divide">÷</span>
                    <span class="orbit-symbol sym-infinity">∞</span>
                </div>
            </div>

            <div class="topic-cards-grid">
                <div class="topic-card" data-question="What is a derivative and why do we use it in calculus?">
                    <div class="topic-card-icon">📐</div>
                    <div class="topic-card-body">
                        <h5>Calculus & Derivatives</h5>
                        <span>Speedometer analogy & dy/dx rate of change</span>
                    </div>
                    <div class="topic-card-arrow">→</div>
                </div>

                <div class="topic-card" data-question="Explain trigonometry sin, cos, tan with real-life examples">
                    <div class="topic-card-icon">🔺</div>
                    <div class="topic-card-body">
                        <h5>Trigonometry & Heights</h5>
                        <span>Understand sin, cos, tan & triangle angles</span>
                    </div>
                    <div class="topic-card-arrow">→</div>
                </div>

                <div class="topic-card" data-question="How to solve Quadratic Equations using formula step by step?">
                    <div class="topic-card-icon">🔢</div>
                    <div class="topic-card-body">
                        <h5>Quadratic Equations</h5>
                        <span>Step-by-step formula & finding roots easily</span>
                    </div>
                    <div class="topic-card-arrow">→</div>
                </div>

                <div class="topic-card" data-question="Give me an important Class 11 NCERT practice question with step-by-step explanation">
                    <div class="topic-card-icon">🎯</div>
                    <div class="topic-card-body">
                        <h5>NCERT Board Practice</h5>
                        <span>Key formulas & scoring tips for exams</span>
                    </div>
                    <div class="topic-card-arrow">→</div>
                </div>
            </div>
        </div>
    `;
    bindTopicCards();
}

// User Identification Helper (Guarantees every account has a unique user_id)
function getUserId() {
    const savedId = localStorage.getItem('userId');
    if (savedId) return parseInt(savedId);
    const email = (localStorage.getItem('studentEmail') || 'sameedkhan7@gmail.com').toLowerCase().trim();
    let hash = 0;
    for (let i = 0; i < email.length; i++) {
        hash = (hash << 5) - hash + email.charCodeAt(i);
        hash |= 0;
    }
    const derivedId = Math.abs(hash) % 1000000 + 1;
    localStorage.setItem('userId', String(derivedId));
    return derivedId;
}

// LocalStorage helpers for per-user chat caching
function getCachedChats() {
    try {
        const uid = getUserId();
        const raw = localStorage.getItem(`cachedChats_${uid}`);
        return raw ? JSON.parse(raw) : [];
    } catch (e) {
        return [];
    }
}

function saveCachedChats(chats) {
    try {
        const uid = getUserId();
        localStorage.setItem(`cachedChats_${uid}`, JSON.stringify(chats));
    } catch (e) {
        console.warn('Could not save chats to localStorage', e);
    }
}

function getCachedMessages(chatId) {
    try {
        const raw = localStorage.getItem(`cachedMessages_${chatId}`);
        return raw ? JSON.parse(raw) : [];
    } catch (e) {
        return [];
    }
}

function saveMessageToCache(chatId, msg) {
    try {
        const msgs = getCachedMessages(chatId);
        msgs.push(msg);
        localStorage.setItem(`cachedMessages_${chatId}`, JSON.stringify(msgs));
    } catch (e) {
        console.warn('Could not save message to localStorage', e);
    }
}

function setCachedMessages(chatId, msgs) {
    try {
        localStorage.setItem(`cachedMessages_${chatId}`, JSON.stringify(msgs));
    } catch (e) {
        console.warn('Could not save messages to localStorage', e);
    }
}

// Render chats directly to DOM
function renderSidebarChats(chats) {
    if (!historyList || !pinnedList) return;

    historyList.innerHTML = '';
    pinnedList.innerHTML = '';

    const list = Array.isArray(chats) ? chats : [];
    const pinnedChats = list.filter(c => c.is_pinned === 1 || c.is_pinned === true);
    const recentChats = list.filter(c => !c.is_pinned);

    if (pinnedChats.length === 0) {
        pinnedList.innerHTML = '<div class="chat-empty-state">No pinned chats</div>';
    } else {
        pinnedChats.forEach(chat => {
            pinnedList.appendChild(createChatHistoryItemEl(chat));
        });
    }

    if (recentChats.length === 0) {
        historyList.innerHTML = '<div class="chat-empty-state">No recent chats</div>';
    } else {
        recentChats.forEach(chat => {
            historyList.appendChild(createChatHistoryItemEl(chat));
        });
    }
}

// Fetch all chats and render in Pinned and Recents (Filtered per User ID)
async function fetchAndRenderSidebarChats() {
    try {
        const uid = getUserId();
        const res = await fetch(`${API_BASE_URL}/api/chats?user_id=${uid}`);
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();
        if (data && Array.isArray(data.chats)) {
            allChatsCache = data.chats;
            saveCachedChats(allChatsCache);
            renderSidebarChats(allChatsCache);
            return;
        }
    } catch (err) {
        console.warn('Could not fetch chats from backend API, using cached chats:', err);
    }
    // Fallback: render from cache if not already rendered
    allChatsCache = getCachedChats();
    renderSidebarChats(allChatsCache);
}

// Create individual ChatGPT/Claude history row element
function createChatHistoryItemEl(chat) {
    const item = document.createElement('div');
    const isActive = currentChatId && String(currentChatId) === String(chat.id);
    item.className = `history-item ${isActive ? 'active' : ''}`;
    item.setAttribute('data-chat-id', chat.id);

    item.innerHTML = `
        <div class="chat-item-main" title="${chat.title}">
            <span class="chat-item-icon">💬</span>
            <span class="chat-item-title">${chat.title}</span>
        </div>
        <div class="chat-item-actions">
            <button type="button" class="chat-action-btn pin-btn" title="${chat.is_pinned ? 'Unpin chat' : 'Pin to top'}">${chat.is_pinned ? '📌' : '📍'}</button>
            <button type="button" class="chat-action-btn rename-btn" title="Rename title">✏️</button>
            <button type="button" class="chat-action-btn delete-btn" title="Delete chat">🗑️</button>
        </div>
    `;

    // Click Main: Restore Conversation
    item.querySelector('.chat-item-main').addEventListener('click', () => {
        loadChatSession(chat.id, chat.title);
    });

    // Toggle Pin
    item.querySelector('.pin-btn').addEventListener('click', async (e) => {
        e.stopPropagation();
        await togglePinChat(chat.id);
    });

    // Rename
    item.querySelector('.rename-btn').addEventListener('click', async (e) => {
        e.stopPropagation();
        await renameChatPrompt(chat.id, chat.title);
    });

    // Delete
    item.querySelector('.delete-btn').addEventListener('click', async (e) => {
        e.stopPropagation();
        if (confirm(`Delete chat "${chat.title}"?`)) {
            await deleteChatSession(chat.id);
        }
    });

    return item;
}

// Restore all messages of a chat session
async function loadChatSession(chatId, title) {
    currentChatId = chatId;
    try {
        localStorage.setItem('activeChatId', String(chatId));
        const url = new URL(window.location.href);
        url.searchParams.set('c', String(chatId));
        window.history.replaceState({ chatId: String(chatId) }, '', url.toString());
    } catch (e) {}

    const topicEl = document.getElementById('current-topic');
    if (topicEl && title) topicEl.innerText = title;

    // Highlight active item in sidebar
    document.querySelectorAll('.history-item').forEach(el => {
        if (String(el.getAttribute('data-chat-id')) === String(chatId)) {
            el.classList.add('active');
        } else {
            el.classList.remove('active');
        }
    });

    // 1. Immediately render cached messages if available
    const cachedMsgs = getCachedMessages(chatId);
    if (cachedMsgs && cachedMsgs.length > 0) {
        if (messagesContainer) messagesContainer.innerHTML = '';
        cachedMsgs.forEach(msg => {
            const senderName = msg.sender === 'user' ? 'You' : 'AI Maths Tutor';
            appendMessage(senderName, msg.text, msg.sender);
        });
    } else if (messagesContainer) {
        messagesContainer.innerHTML = '<div style="text-align:center; padding:30px; color:#94a3b8; font-size:13px;">Loading conversation...</div>';
    }

    // 2. Fetch fresh messages from API
    try {
        const res = await fetch(`${API_BASE_URL}/api/chats/${chatId}/messages`);
        if (res.ok) {
            const data = await res.json();
            if (data.messages && Array.isArray(data.messages)) {
                setCachedMessages(chatId, data.messages);
                if (messagesContainer) messagesContainer.innerHTML = '';
                if (data.messages.length > 0) {
                    data.messages.forEach(msg => {
                        const senderName = msg.sender === 'user' ? 'You' : 'AI Maths Tutor';
                        appendMessage(senderName, msg.text, msg.sender);
                    });
                } else {
                    messagesContainer.innerHTML = '<div style="text-align:center; padding:30px; color:#94a3b8; font-size:13px;">No messages in this chat yet. Ask anything below!</div>';
                }
            }
        }
    } catch (err) {
        console.warn('Error loading chat session from API, fallback to cache:', err);
    }
}

// Start New Chat (Clean Slate)
function startNewChat() {
    currentChatId = null;
    try {
        localStorage.removeItem('activeChatId');
        const url = new URL(window.location.href);
        url.searchParams.delete('c');
        url.searchParams.delete('chat');
        window.history.replaceState({}, '', url.toString());
    } catch (e) {}

    const topicEl = document.getElementById('current-topic');
    if (topicEl) topicEl.innerText = "New Maths Question";

    document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
    renderWelcomeHero();
    if (userInput) {
        userInput.value = '';
        userInput.focus();
    }
}

if (newChatBtn) {
    newChatBtn.addEventListener('click', startNewChat);
}

// Pin / Unpin
async function togglePinChat(chatId) {
    // Optimistic local update
    allChatsCache = allChatsCache.map(c => {
        if (String(c.id) === String(chatId)) {
            return { ...c, is_pinned: (c.is_pinned === 1 || c.is_pinned === true) ? 0 : 1 };
        }
        return c;
    });
    saveCachedChats(allChatsCache);
    renderSidebarChats(allChatsCache);

    try {
        await fetch(`${API_BASE_URL}/api/chats/${chatId}/pin`, { method: 'PUT' });
    } catch (err) {
        console.warn('Network issue while toggling pin:', err);
    }
}

// Delete Chat
async function deleteChatSession(chatId) {
    // Optimistic local update
    allChatsCache = allChatsCache.filter(c => String(c.id) !== String(chatId));
    saveCachedChats(allChatsCache);
    try { localStorage.removeItem(`cachedMessages_${chatId}`); } catch (e) {}
    renderSidebarChats(allChatsCache);

    if (currentChatId && String(currentChatId) === String(chatId)) {
        startNewChat();
    }

    try {
        await fetch(`${API_BASE_URL}/api/chats/${chatId}`, { method: 'DELETE' });
    } catch (err) {
        console.warn('Network issue while deleting chat:', err);
    }
}

// Rename Chat
async function renameChatPrompt(chatId, currentTitle) {
    const newTitle = prompt('Enter new title for this chat:', currentTitle);
    if (newTitle && newTitle.trim() && newTitle.trim() !== currentTitle) {
        const trimmed = newTitle.trim();
        // Optimistic local update
        allChatsCache = allChatsCache.map(c => {
            if (String(c.id) === String(chatId)) {
                return { ...c, title: trimmed };
            }
            return c;
        });
        saveCachedChats(allChatsCache);
        renderSidebarChats(allChatsCache);

        if (currentChatId && String(currentChatId) === String(chatId)) {
            const topicEl = document.getElementById('current-topic');
            if (topicEl) topicEl.innerText = trimmed;
        }

        try {
            await fetch(`${API_BASE_URL}/api/chats/${chatId}/title`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: trimmed })
            });
        } catch (err) {
            console.warn('Network issue while renaming chat:', err);
        }
    }
}

// Restore active chat session if user refreshed the page (like ChatGPT & Claude)
function restoreActiveSessionOnInit() {
    try {
        const urlParams = new URLSearchParams(window.location.search);
        const urlChatId = urlParams.get('c') || urlParams.get('chat');
        const savedActiveChatId = urlChatId || localStorage.getItem('activeChatId');

        if (savedActiveChatId) {
            const chats = allChatsCache.length > 0 ? allChatsCache : getCachedChats();
            const found = chats.find(c => String(c.id) === String(savedActiveChatId));
            const chatTitle = found ? found.title : "Maths Session";
            loadChatSession(savedActiveChatId, chatTitle);
            return true;
        }
    } catch (e) {
        console.warn('Error restoring session on init:', e);
    }
    return false;
}

// Browser Back / Forward Navigation Support
window.addEventListener('popstate', (e) => {
    try {
        const urlParams = new URLSearchParams(window.location.search);
        const urlChatId = urlParams.get('c') || urlParams.get('chat');
        if (urlChatId) {
            const found = allChatsCache.find(c => String(c.id) === String(urlChatId));
            loadChatSession(urlChatId, found ? found.title : "Maths Session");
        } else {
            startNewChat();
        }
    } catch (err) {}
});

// Initial Instant Render from Cache, then fetch from API
allChatsCache = getCachedChats();
if (allChatsCache.length > 0) {
    renderSidebarChats(allChatsCache);
}
// 🔄 Restore previous active chat on page refresh!
const hasRestored = restoreActiveSessionOnInit();

fetchAndRenderSidebarChats().then(() => {
    // If an active session is currently running, keep its title and sidebar highlight synced
    if (currentChatId) {
        const freshFound = allChatsCache.find(c => String(c.id) === String(currentChatId));
        if (freshFound) {
            const topicEl = document.getElementById('current-topic');
            if (topicEl) topicEl.innerText = freshFound.title;
        }
        document.querySelectorAll('.history-item').forEach(el => {
            if (String(el.getAttribute('data-chat-id')) === String(currentChatId)) {
                el.classList.add('active');
            } else {
                el.classList.remove('active');
            }
        });
    }
});

// 7. Profile Popup Menu (ChatGPT & Claude Style)
const userProfileCard = document.getElementById('user-profile-card');
const profilePopupMenu = document.getElementById('profile-popup-menu');
const popupUserEmail = document.getElementById('popup-user-email');
const popupPlanBadge = document.getElementById('popup-plan-badge');

if (popupUserEmail) {
    popupUserEmail.innerText = localStorage.getItem('studentEmail') || `${currentStudentName.toLowerCase().replace(/\s+/g, '')}@gmail.com`;
}
if (popupPlanBadge) {
    popupPlanBadge.innerText = `Student · ${savedGrade}`;
}

if (userProfileCard && profilePopupMenu) {
    userProfileCard.addEventListener('click', (e) => {
        e.stopPropagation();
        const isHidden = profilePopupMenu.style.display === 'none' || profilePopupMenu.style.display === '';
        profilePopupMenu.style.display = isHidden ? 'block' : 'none';
    });

    profilePopupMenu.addEventListener('click', (e) => {
        e.stopPropagation();
    });

    document.addEventListener('click', (e) => {
        if (!profilePopupMenu.contains(e.target) && !userProfileCard.contains(e.target)) {
            profilePopupMenu.style.display = 'none';
        }
    });
}

// 8. Dark / Light Theme Toggle inside Profile Popup
const popupThemeItem = document.getElementById('popup-theme-item');
const popupThemeIcon = document.getElementById('popup-theme-icon');
const popupThemeText = document.getElementById('popup-theme-text');

function updateThemeUI(isDark) {
    if (isDark) {
        document.body.classList.add('dark-mode');
        if (popupThemeIcon) popupThemeIcon.innerText = '☀️';
        if (popupThemeText) popupThemeText.innerText = 'Light Mode';
    } else {
        document.body.classList.remove('dark-mode');
        if (popupThemeIcon) popupThemeIcon.innerText = '🌙';
        if (popupThemeText) popupThemeText.innerText = 'Dark Mode';
    }
}

// Initial theme check (Default: Dark Mode)
const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'light') {
    updateThemeUI(false);
} else {
    // Default to Dark Mode for new users & initial load
    updateThemeUI(true);
    if (!savedTheme) {
        localStorage.setItem('theme', 'dark');
    }
}

if (popupThemeItem) {
    popupThemeItem.addEventListener('click', () => {
        const isCurrentlyDark = document.body.classList.contains('dark-mode');
        const newIsDark = !isCurrentlyDark;
        updateThemeUI(newIsDark);
        localStorage.setItem('theme', newIsDark ? 'dark' : 'light');
    });
}

// 9. Logout Button Handler inside Profile Popup
const popupLogoutItem = document.getElementById('popup-logout-item');
if (popupLogoutItem) {
    popupLogoutItem.addEventListener('click', () => {
        localStorage.removeItem('studentName');
        localStorage.removeItem('studentEmail');
        localStorage.removeItem('userRole');
        localStorage.removeItem('userId');
        window.location.href = 'login.html';
    });
}

// 10. Settings Modal Dialog (ChatGPT Style)
const popupSettingsItem = document.getElementById('popup-settings-item');
const settingsModalBackdrop = document.getElementById('settings-modal-backdrop');
const settingsCloseBtn = document.getElementById('settings-close-btn');
const settingsTabBtns = document.querySelectorAll('.settings-tab-btn');
const settingsTabPanes = document.querySelectorAll('.settings-tab-pane');

// Settings Controls
const settingAppearanceSelect = document.getElementById('setting-appearance-select');
const settingLanguageSelect = document.getElementById('setting-language-select');
const settingGradeSelect = document.getElementById('setting-grade-select');
const settingDefaultStyleSelect = document.getElementById('setting-default-style-select');
const settingsStudentInfo = document.getElementById('settings-student-info');
const clearAllChatsBtn = document.getElementById('clear-all-chats-btn');
const settingsLogoutBtn = document.getElementById('settings-logout-btn');

// Text Size Controls
const fontDecreaseBtn = document.getElementById('font-decrease-btn');
const fontIncreaseBtn = document.getElementById('font-increase-btn');
const fontResetBtn = document.getElementById('font-reset-btn');
const fontSizeDisplay = document.getElementById('font-size-display');

let currentFontSizeLevel = parseInt(localStorage.getItem('tutorFontSizeLevel') || '1'); // 0: Small, 1: Normal, 2: Large
const fontLevels = [
    { label: 'Small', size: '13.5px' },
    { label: 'Normal', size: '15px' },
    { label: 'Large', size: '16.5px' }
];

function applyFontSize(level) {
    if (level < 0) level = 0;
    if (level > 2) level = 2;
    currentFontSizeLevel = level;
    localStorage.setItem('tutorFontSizeLevel', level);
    
    if (fontSizeDisplay) {
        fontSizeDisplay.innerText = fontLevels[level].label;
    }
    document.documentElement.style.setProperty('--chat-font-size', fontLevels[level].size);
    if (messagesContainer) {
        messagesContainer.style.fontSize = fontLevels[level].size;
    }
}

// Open Settings to a specific tab directly
function openSettingsToTab(tabId) {
    openSettingsModal();
    const targetBtn = document.querySelector(`.settings-tab-btn[data-tab="${tabId}"]`);
    if (targetBtn) {
        targetBtn.click();
    }
}

// Open Settings Modal
function openSettingsModal() {
    if (profilePopupMenu) profilePopupMenu.style.display = 'none';
    closeMobileSidebar();
    if (settingsModalBackdrop) {
        settingsModalBackdrop.style.display = 'flex';
    }

    // Sync current values
    const currentTheme = localStorage.getItem('theme') || 'dark';
    if (settingAppearanceSelect) {
        settingAppearanceSelect.value = currentTheme;
    }

    const currentLang = localStorage.getItem('tutorLanguage') || 'hinglish';
    if (settingLanguageSelect) {
        settingLanguageSelect.value = currentLang;
    }

    const currentGradeVal = localStorage.getItem('studentGrade') || 'Class 11';
    if (settingGradeSelect) {
        settingGradeSelect.value = currentGradeVal;
    }

    const currentStyleVal = localStorage.getItem('defaultStyle') || 'simple';
    if (settingDefaultStyleSelect) {
        settingDefaultStyleSelect.value = currentStyleVal;
    }

    if (settingsStudentInfo) {
        const studentEmail = localStorage.getItem('studentEmail') || `${currentStudentName.toLowerCase().replace(/\s+/g, '')}@gmail.com`;
        settingsStudentInfo.innerText = `${currentStudentName} (${studentEmail})`;
    }

    applyFontSize(currentFontSizeLevel);
}

// Close Settings Modal
function closeSettingsModal() {
    if (settingsModalBackdrop) {
        settingsModalBackdrop.style.display = 'none';
    }
}

if (popupSettingsItem) {
    popupSettingsItem.addEventListener('click', openSettingsModal);
}

if (settingsCloseBtn) {
    settingsCloseBtn.addEventListener('click', closeSettingsModal);
}

if (settingsModalBackdrop) {
    settingsModalBackdrop.addEventListener('click', (e) => {
        if (e.target === settingsModalBackdrop) {
            closeSettingsModal();
        }
    });
}

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeSettingsModal();
    }
});

// Tab Switching
settingsTabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        settingsTabBtns.forEach(b => b.classList.remove('active'));
        settingsTabPanes.forEach(p => p.classList.remove('active'));

        btn.classList.add('active');
        const targetTabId = btn.getAttribute('data-tab');
        const targetPane = document.getElementById(targetTabId);
        if (targetPane) {
            targetPane.classList.add('active');
        }
    });
});

// 1. Appearance / Theme Change
if (settingAppearanceSelect) {
    settingAppearanceSelect.addEventListener('change', (e) => {
        const val = e.target.value;
        if (val === 'dark') {
            updateThemeUI(true);
            localStorage.setItem('theme', 'dark');
        } else if (val === 'light') {
            updateThemeUI(false);
            localStorage.setItem('theme', 'light');
        } else if (val === 'system') {
            const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            updateThemeUI(systemPrefersDark);
            localStorage.setItem('theme', systemPrefersDark ? 'dark' : 'light');
        }
    });
}

// 2. Language Change
if (settingLanguageSelect) {
    settingLanguageSelect.addEventListener('change', (e) => {
        const val = e.target.value;
        localStorage.setItem('tutorLanguage', val);
    });
}

// 3. Class / Grade Change
if (settingGradeSelect) {
    settingGradeSelect.addEventListener('change', (e) => {
        const newGrade = e.target.value;
        localStorage.setItem('studentGrade', newGrade);

        // Update UI everywhere
        if (userPlanTagEl) userPlanTagEl.innerText = `Student · ${newGrade}`;
        if (popupPlanBadge) popupPlanBadge.innerText = `Student · ${newGrade}`;
        if (badgeEl) badgeEl.innerText = `NCERT ${newGrade}`;
        if (navClassBadge) navClassBadge.innerText = newGrade;
    });
}

// 4. Default Teaching Style Change
if (settingDefaultStyleSelect) {
    settingDefaultStyleSelect.addEventListener('change', (e) => {
        const newStyle = e.target.value;
        localStorage.setItem('defaultStyle', newStyle);
        currentStyle = newStyle;

        if (navStyleBadge) {
            navStyleBadge.innerText = newStyle === 'sports' ? 'Cricket' : newStyle === 'step-by-step' ? 'Steps' : 'Intuition';
        }

        // Sync pill dropdown text
        const matchingMenuItem = document.querySelector(`.menu-item[data-style="${newStyle}"]`);
        if (matchingMenuItem && selectedModelText) {
            menuItems.forEach(i => i.classList.remove('active'));
            matchingMenuItem.classList.add('active');
            selectedModelText.innerText = matchingMenuItem.getAttribute('data-text');
        }
    });
}

// 5. Font Size Controls
if (fontDecreaseBtn) {
    fontDecreaseBtn.addEventListener('click', () => {
        applyFontSize(currentFontSizeLevel - 1);
    });
}

if (fontIncreaseBtn) {
    fontIncreaseBtn.addEventListener('click', () => {
        applyFontSize(currentFontSizeLevel + 1);
    });
}

if (fontResetBtn) {
    fontResetBtn.addEventListener('click', () => {
        applyFontSize(1); // Normal
    });
}

// Initial font size restore
applyFontSize(currentFontSizeLevel);

// 6. Clear All Chats
if (clearAllChatsBtn) {
    clearAllChatsBtn.addEventListener('click', async () => {
        if (confirm("Are you sure you want to clear your entire chat history?")) {
            allChatsCache = [];
            saveCachedChats([]);
            // Clear message caches
            try {
                Object.keys(localStorage).forEach(key => {
                    if (key.startsWith('cachedMessages_')) {
                        localStorage.removeItem(key);
                    }
                });
            } catch (e) {}
            startNewChat();
            renderSidebarChats([]);
            closeSettingsModal();

            try {
                await fetch(`${API_BASE_URL}/api/chats`, { method: 'DELETE' });
            } catch (err) {
                console.warn('Error clearing chats on server:', err);
            }
        }
    });
}

// 7. Logout from inside Settings
if (settingsLogoutBtn) {
    settingsLogoutBtn.addEventListener('click', () => {
        localStorage.removeItem('studentName');
        localStorage.removeItem('studentEmail');
        window.location.href = 'login.html';
    });
}

// 9. Sidebar Collapse / Expand Toggle
const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
const sidebar = document.querySelector('.sidebar');

if (sidebarToggleBtn && sidebar) {
    sidebarToggleBtn.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
    });
}

// 10. ChatGPT Floating Popup for Pinned & Recents
const pinnedHeaderBtn = document.getElementById('pinned-header-btn');
const recentsHeaderBtn = document.getElementById('recents-header-btn');

if (pinnedHeaderBtn && pinnedList) {
    pinnedHeaderBtn.addEventListener('click', (e) => {
        if (sidebar.classList.contains('collapsed')) {
            e.stopPropagation();
            if (historyList) historyList.classList.remove('show-flyout');
            pinnedList.classList.toggle('show-flyout');
            pinnedList.style.top = '90px'; // 📌 Icon ke bagal me position
        }
    });
}

if (recentsHeaderBtn && historyList) {
    recentsHeaderBtn.addEventListener('click', (e) => {
        if (sidebar.classList.contains('collapsed')) {
            e.stopPropagation();
            if (pinnedList) pinnedList.classList.remove('show-flyout');
            historyList.classList.toggle('show-flyout');
            historyList.style.top = '140px'; // 🕒 Icon ke bagal me position
        }
    });
}

// Bahar click karne par floating popup band ho jaye
document.addEventListener('click', () => {
    if (pinnedList) pinnedList.classList.remove('show-flyout');
    if (historyList) historyList.classList.remove('show-flyout');
});

// 11. Mobile Drawer Menu (Slide-in Sidebar on Phones)
const mobileMenuBtn = document.getElementById('mobile-menu-btn');
const sidebarBackdrop = document.getElementById('sidebar-backdrop');

function openMobileSidebar() {
    if (sidebar) sidebar.classList.add('mobile-open');
    if (sidebarBackdrop) sidebarBackdrop.classList.add('active');
}

function closeMobileSidebar() {
    if (sidebar) sidebar.classList.remove('mobile-open');
    if (sidebarBackdrop) sidebarBackdrop.classList.remove('active');
}

if (mobileMenuBtn) {
    mobileMenuBtn.addEventListener('click', openMobileSidebar);
}

if (sidebarBackdrop) {
    sidebarBackdrop.addEventListener('click', closeMobileSidebar);
}

// Mobile par sidebar toggle button (◨) se bhi drawer close ho sake
if (sidebarToggleBtn) {
    sidebarToggleBtn.addEventListener('click', () => {
        if (window.innerWidth <= 768) {
            closeMobileSidebar();
        }
    });
}

// ===================================================
// ⚡ DEVELOPER RAG CONTROL CENTER & ROLE MANAGEMENT
// ===================================================
const userRole = localStorage.getItem('userRole') || 'student';
const popupDevItem = document.getElementById('popup-dev-item');

// Developer Profile Badge & Menu Item Visibility (ONLY for developer accounts)
if (userRole === 'developer') {
    if (popupDevItem) {
        popupDevItem.style.display = 'flex';
    }
    if (userPlanTagEl) {
        userPlanTagEl.innerHTML = `⚡ <strong style="color:#c084fc;">Developer Admin</strong> · RAG Manager`;
    }
    const popupBadgeEl = document.getElementById('popup-plan-badge');
    if (popupBadgeEl) {
        popupBadgeEl.innerHTML = `⚡ Developer Admin · Full RAG Access`;
        popupBadgeEl.style.color = `#c084fc`;
    }
} else {
    if (popupDevItem) {
        popupDevItem.style.display = 'none';
    }
}

// Dev Modal Controls
const devModalBackdrop = document.getElementById('dev-modal-backdrop');
const devModalCloseBtn = document.getElementById('dev-modal-close');

function openDevModal() {
    if (userRole !== 'developer') return; // Strict guard: Only developer role can open panel
    if (devModalBackdrop) {
        devModalBackdrop.style.display = 'flex';
        fetchRagStats();
    }
}

function closeDevModal() {
    if (devModalBackdrop) {
        devModalBackdrop.style.display = 'none';
    }
}

if (popupDevItem) {
    popupDevItem.addEventListener('click', () => {
        if (profilePopupMenu) profilePopupMenu.style.display = 'none';
        openDevModal();
    });
}

if (devModalCloseBtn) {
    devModalCloseBtn.addEventListener('click', closeDevModal);
}

if (devModalBackdrop) {
    devModalBackdrop.addEventListener('click', (e) => {
        if (e.target === devModalBackdrop) closeDevModal();
    });
}

// Keyboard Shortcut: Ctrl + Shift + D opens Dev Modal ONLY for developer role
document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.shiftKey && (e.key === 'D' || e.key === 'd')) {
        if (userRole === 'developer') {
            e.preventDefault();
            openDevModal();
        }
    }
});

// Dev Tab Switcher
const devTabBtns = document.querySelectorAll('.dev-tab-btn');
const devTabPanes = document.querySelectorAll('.dev-tab-pane');

devTabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const targetTab = btn.getAttribute('data-dev-tab');
        
        devTabBtns.forEach(b => {
            b.classList.remove('active');
            b.style.background = 'transparent';
            b.style.color = '#cbd5e1';
        });
        devTabPanes.forEach(p => p.style.display = 'none');

        btn.classList.add('active');
        btn.style.background = '#1e293b';
        btn.style.color = '#c084fc';

        const pane = document.getElementById(targetTab);
        if (pane) pane.style.display = 'block';

        if (targetTab === 'dev-tab-stats') {
            fetchRagStats();
        }
    });
});

// Dev Status Alert Helper
function showDevAlert(msg, type = 'success') {
    const alertEl = document.getElementById('dev-status-alert');
    if (!alertEl) return;
    alertEl.style.display = 'block';
    alertEl.innerText = msg;
    if (type === 'success') {
        alertEl.style.background = 'rgba(34, 197, 94, 0.15)';
        alertEl.style.color = '#4ade80';
        alertEl.style.border = '1px solid #22c55e';
    } else {
        alertEl.style.background = 'rgba(239, 68, 68, 0.15)';
        alertEl.style.color = '#f87171';
        alertEl.style.border = '1px solid #ef4444';
    }
}

// File Name Display on Selection
const pdfFileInput = document.getElementById('dev-pdf-file');
const pdfFilenameDisplay = document.getElementById('dev-pdf-filename');

if (pdfFileInput && pdfFilenameDisplay) {
    pdfFileInput.addEventListener('change', () => {
        if (pdfFileInput.files.length > 0) {
            pdfFilenameDisplay.innerText = `Selected: ${pdfFileInput.files[0].name} (${(pdfFileInput.files[0].size / 1024).toFixed(1)} KB)`;
            pdfFilenameDisplay.style.color = '#a855f7';
        } else {
            pdfFilenameDisplay.innerText = 'No file selected';
            pdfFilenameDisplay.style.color = '#cbd5e1';
        }
    });
}

// 1. PDF Upload Form Submit
const devPdfForm = document.getElementById('dev-pdf-form');
const devPdfBtn = document.getElementById('dev-pdf-submit-btn');

if (devPdfForm) {
    devPdfForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!pdfFileInput.files.length) {
            showDevAlert('Please select a PDF file first!', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', pdfFileInput.files[0]);

        if (devPdfBtn) {
            devPdfBtn.disabled = true;
            devPdfBtn.innerText = '⌛ Ingesting PDF into Chroma Vector DB...';
        }

        try {
            const res = await fetch(`${API_BASE_URL}/api/dev/upload-pdf`, {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            if (res.ok && data.success) {
                showDevAlert(`🎉 ${data.message}`, 'success');
                devPdfForm.reset();
                if (pdfFilenameDisplay) pdfFilenameDisplay.innerText = 'No file selected';
            } else {
                showDevAlert(`⚠️ Upload failed: ${data.detail || data.error}`, 'error');
            }
        } catch (err) {
            showDevAlert(`⚠️ Backend Connection Error: ${err.message}`, 'error');
        } finally {
            if (devPdfBtn) {
                devPdfBtn.disabled = false;
                devPdfBtn.innerText = '⚡ Upload & Ingest PDF into RAG';
            }
        }
    });
}

// .TXT / .MD File Selection & Auto-Reading
const txtFileInput = document.getElementById('dev-txt-file');
const txtFilenameDisplay = document.getElementById('dev-txt-filename');
const textTitleInput = document.getElementById('dev-text-title');
const textContentInput = document.getElementById('dev-text-content');

if (txtFileInput) {
    txtFileInput.addEventListener('change', () => {
        if (txtFileInput.files.length > 0) {
            const file = txtFileInput.files[0];
            if (txtFilenameDisplay) {
                txtFilenameDisplay.innerText = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
                txtFilenameDisplay.style.color = '#a5b4fc';
            }
            
            // Auto-fill title with clean filename
            if (textTitleInput) {
                const nameWithoutExt = file.name.replace(/\.[^/.]+$/, '').replace(/[_\-]/g, ' ');
                textTitleInput.value = nameWithoutExt.charAt(0).toUpperCase() + nameWithoutExt.slice(1);
            }

            // Read text file contents into textarea using FileReader
            const reader = new FileReader();
            reader.onload = (e) => {
                if (textContentInput) {
                    textContentInput.value = e.target.result;
                    textContentInput.focus();
                }
            };
            reader.readAsText(file);
        } else {
            if (txtFilenameDisplay) {
                txtFilenameDisplay.innerText = 'No file chosen';
                txtFilenameDisplay.style.color = '#94a3b8';
            }
        }
    });
}

// 2. Text Notes Form Submit
const devTextForm = document.getElementById('dev-text-form');
const devTextBtn = document.getElementById('dev-text-submit-btn');

if (devTextForm) {
    devTextForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const title = document.getElementById('dev-text-title').value.trim();
        const content = document.getElementById('dev-text-content').value.trim();

        if (!title || !content) return;

        if (devTextBtn) {
            devTextBtn.disabled = true;
            devTextBtn.innerText = '⌛ Ingesting text into RAG...';
        }

        try {
            const res = await fetch(`${API_BASE_URL}/api/dev/upload-text`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, content })
            });
            const data = await res.json();
            if (res.ok && data.success) {
                showDevAlert(`🎉 ${data.message}`, 'success');
                devTextForm.reset();
            } else {
                showDevAlert(`⚠️ Ingestion failed: ${data.detail || data.error}`, 'error');
            }
        } catch (err) {
            showDevAlert(`⚠️ Backend Connection Error: ${err.message}`, 'error');
        } finally {
            if (devTextBtn) {
                devTextBtn.disabled = false;
                devTextBtn.innerText = 'Save & Ingest Text Document';
            }
        }
    });
}

// 3. Web Scraper Form Submit
const devScrapeForm = document.getElementById('dev-scrape-form');
const devScrapeBtn = document.getElementById('dev-scrape-submit-btn');

if (devScrapeForm) {
    devScrapeForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const url = document.getElementById('dev-scrape-url').value.trim();
        if (!url) return;

        if (devScrapeBtn) {
            devScrapeBtn.disabled = true;
            devScrapeBtn.innerText = '🌐 Scraping web page & chunking...';
        }

        try {
            const res = await fetch(`${API_BASE_URL}/api/dev/scrape-url`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });
            const data = await res.json();
            if (res.ok && data.success) {
                showDevAlert(`🎉 ${data.message}`, 'success');
                devScrapeForm.reset();
            } else {
                showDevAlert(`⚠️ Scraping failed: ${data.detail || data.error}`, 'error');
            }
        } catch (err) {
            showDevAlert(`⚠️ Backend Connection Error: ${err.message}`, 'error');
        } finally {
            if (devScrapeBtn) {
                devScrapeBtn.disabled = false;
                devScrapeBtn.innerText = '🌐 Scrape Web Page & Ingest';
            }
        }
    });
}

// 4. Fetch RAG Realtime Stats
async function fetchRagStats() {
    try {
        const res = await fetch(`${API_BASE_URL}/api/dev/rag-stats`);
        const data = await res.json();
        if (data.success && data.stats) {
            const stats = data.stats;
            const docEl = document.getElementById('rag-stat-documents');
            const chunkEl = document.getElementById('rag-stat-chunks');
            const textListEl = document.getElementById('rag-text-list');
            const pdfListEl = document.getElementById('rag-pdf-list');

            if (docEl) docEl.innerText = stats.total_documents;
            if (chunkEl) chunkEl.innerText = stats.total_chunks;

            if (textListEl) {
                textListEl.innerHTML = stats.texts.length > 0 
                    ? stats.texts.map(t => `<li style="padding: 2px 0;">📄 ${t}</li>`).join('')
                    : `<li style="color:#64748b;">No text files ingested yet</li>`;
            }

            if (pdfListEl) {
                pdfListEl.innerHTML = stats.pdfs.length > 0 
                    ? stats.pdfs.map(p => `<li style="padding: 2px 0;">📕 ${p}</li>`).join('')
                    : `<li style="color:#64748b;">No PDF files uploaded yet</li>`;
            }
        }
    } catch (err) {
        console.warn('Could not load RAG stats:', err);
    }
}

const refreshStatsBtn = document.getElementById('dev-refresh-stats-btn');
if (refreshStatsBtn) {
    refreshStatsBtn.addEventListener('click', fetchRagStats);
}
