// ==========================================
// AI Maths Tutor — Complete Frontend Logic
// ==========================================

// Global State
let currentStyle = 'simple';

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




// 1. Math Shortcuts Toolbar (x², √, π etc.)
const symButtons = document.querySelectorAll('.sym-btn');
const userInput = document.getElementById('user-input');

symButtons.forEach(button => {
    button.addEventListener('click', () => {
        userInput.value += button.innerText;
        userInput.focus();
    });
});


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


// 3. Antigravity Model / Style Popup Menu
const modelPillBtn = document.getElementById('model-pill-btn');
const modelDropdown = document.getElementById('model-dropdown-menu');
const selectedModelText = document.getElementById('selected-model-text');
const menuItems = document.querySelectorAll('.menu-item');

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
        currentStyle = item.getAttribute('data-style');
        selectedModelText.innerText = item.getAttribute('data-text');
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


// 5. Chat Form Submit (Ask Tutor)
const chatForm = document.getElementById('chat-form');
const messagesContainer = document.getElementById('messages-container');

if (chatForm) {
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
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

           // 🚀 Asli FastAPI Backend API Call:
        fetch('http://127.0.0.1:8000/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: question,
                style: currentStyle,
                model: 'llama3.1'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.reply) {
                appendMessage('AI Maths Tutor', data.reply, 'assistant');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            appendMessage('AI Maths Tutor', '⚠️ Backend server connect nahi ho pa raha hai. Make sure FastAPI server chal raha hai!', 'assistant');
        });
    });
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
            <p>${text.replace(/\n/g, '<br>')}</p>
        </div>
    `;

    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Message aate hi LaTeX math formulas ko sundar equation me render karo
    if (window.renderMathInElement) {
        renderMathInElement(msgDiv, {
            delimiters: [
                {left: '$$', right: '$$', display: true},
                {left: '$', right: '$', display: false}
            ]
        });
    }
}


// 6. New Chat, History Restore & 📌 Pin/Unpin Feature
const newChatBtn = document.getElementById('new-chat-btn');
const historyList = document.getElementById('history-list');
const pinnedList = document.getElementById('pinned-list');

if (newChatBtn && historyList) {
    newChatBtn.addEventListener('click', () => {
        const topicEl = document.getElementById('current-topic');
        const currentTopic = topicEl ? topicEl.innerText : 'New Maths Question';
        const savedHTML = messagesContainer.innerHTML;

        // History item with Title + Pin Button
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        
        historyItem.innerHTML = `
            <span class="chat-item-title">💬 ${currentTopic}</span>
            <button type="button" class="pin-toggle-btn" title="Pin to top">📌</button>
        `;

        // Click Title: Purani chat wapas khule
        historyItem.querySelector('.chat-item-title').addEventListener('click', () => {
            if (topicEl) topicEl.innerText = currentTopic;
            messagesContainer.innerHTML = savedHTML;
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        });

        // Click Pin Icon: Pinned aur Recents ke beech move ho
        const pinBtn = historyItem.querySelector('.pin-toggle-btn');
        pinBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (historyItem.parentElement === historyList) {
                if (pinnedList) pinnedList.appendChild(historyItem);
                pinBtn.title = "Unpin chat";
            } else {
                historyList.appendChild(historyItem);
                pinBtn.title = "Pin to top";
            }
        });

        // By default Recents me daalo
        historyList.appendChild(historyItem);

        // Fresh Pinterest-style welcome hero with Topic Cards
        messagesContainer.innerHTML = `
            <div class="welcome-hero" id="welcome-hero">
                <div class="welcome-avatar-badge">👩‍🏫</div>
                <h2 class="welcome-greeting" id="welcome-greeting">Hello ${currentStudentName}!</h2>
                <p class="welcome-subtitle">I am your <strong>AI Maths Tutor</strong>. Ready for a new question! Aaj kaunsa concept intuitively samajhna chahte hain?</p>
                
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

        if (topicEl) topicEl.innerText = "New Maths Question";
        userInput.value = '';
        userInput.focus();
    });
}

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

// Initial theme check
const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'dark') {
    updateThemeUI(true);
} else {
    updateThemeUI(false);
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

// Open Settings Modal
function openSettingsModal() {
    if (profilePopupMenu) profilePopupMenu.style.display = 'none';
    if (settingsModalBackdrop) {
        settingsModalBackdrop.style.display = 'flex';
    }

    // Sync current values
    const currentTheme = localStorage.getItem('theme') || 'light';
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
    });
}

// 4. Default Teaching Style Change
if (settingDefaultStyleSelect) {
    settingDefaultStyleSelect.addEventListener('change', (e) => {
        const newStyle = e.target.value;
        localStorage.setItem('defaultStyle', newStyle);
        currentStyle = newStyle;

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
    clearAllChatsBtn.addEventListener('click', () => {
        if (confirm("Are you sure you want to clear your chat history?")) {
            if (historyList) historyList.innerHTML = '';
            if (pinnedList) pinnedList.innerHTML = '';
            
            if (messagesContainer) {
                messagesContainer.innerHTML = `
                    <div class="message assistant">
                        <div class="avatar">👩‍🏫</div>
                        <div class="message-content">
                            <h4>Hello ${currentStudentName}! I am your AI Maths Tutor.</h4>
                            <p>History cleared! Aap mujhse koi bhi mathematics ka concept, formula ya problem puch sakte hain.</p>
                        </div>
                    </div>
                `;
            }
            closeSettingsModal();
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