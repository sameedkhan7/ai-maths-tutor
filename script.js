// ==========================================

// AI Maths Tutor — Complete Frontend Logic

// ==========================================



// 🌐 Dynamic API URL (Automatically connects to local 8000 on laptop, phone Wi-Fi LAN IP, or custom tunnel)

function getApiBaseUrl() {

    const saved = localStorage.getItem('customApiBaseUrl');

    if (saved && saved.trim()) return saved.trim().replace(/\/+$/, '');

    if (window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost') {

        return 'http://127.0.0.1:8000';

    }

    if (window.location.protocol === 'http:' && /^(\d{1,3}\.){3}\d{1,3}$/.test(window.location.hostname)) {

        return `http://${window.location.hostname}:8000`;

    }

    return (window.location.protocol === 'https:') ? '' : 'http://127.0.0.1:8000';

}

const API_BASE_URL = getApiBaseUrl();



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

        card.onclick = (e) => {

            if (e) {

                e.preventDefault();

                e.stopPropagation();

            }

            const question = card.getAttribute('data-question');

            const inputEl = document.getElementById('user-input');

            if (question && inputEl) {

                if (typeof hasUserDismissedModeSelector !== 'undefined') hasUserDismissedModeSelector = false;

                if (typeof hasSelectedStyleForConversation !== 'undefined') hasSelectedStyleForConversation = false;

                inputEl.value = question;

                inputEl.focus();

                if (typeof autoResizeInput === 'function') autoResizeInput();

                // Instantly pop open the Smart Teaching Style Selector so student can choose their mode!

                if (typeof showModeSelector === 'function') showModeSelector();

                const sel = document.getElementById('smart-tutor-mode-selector');

                if (sel) {

                    sel.style.display = 'block';

                    sel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

                    sel.classList.add('pulse-highlight');

                    setTimeout(() => sel.classList.remove('pulse-highlight'), 1500);

                }

            }

        };

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

// Global State (Restored from persistent storage)

let currentStyle = localStorage.getItem('defaultStyle') || 'simple';

let currentLanguage = localStorage.getItem('tutorLanguage') || 'hinglish';

let currentChatId = null;

let allChatsCache = [];



const navTutorLangBtn = document.getElementById('nav-tutor-lang-btn');

const navClassBadge = document.getElementById('nav-class-badge');

const navStyleBadge = document.getElementById('nav-style-badge');

const navLangBadge = document.getElementById('nav-lang-badge');



const quickStyleSelect = document.getElementById('quick-style-select');

const quickLangSelect = document.getElementById('quick-lang-select');



const STYLE_NAMES_MAP = {

    'quick': 'Quick Answer',

    'simple': 'Concept First',

    'step_by_step': 'Step-by-Step',

    'exam': 'Exam-Oriented',

    'sports': 'Sports Mode',

    'analogy': 'Real-Life Mode',

    'story': 'Story Mode',

    'social': 'Social Mode',

    'socratic': 'Socratic Mode'

};



const STYLE_ICONS_MAP = {

    'quick': '⚡',

    'simple': '💡',

    'step_by_step': '🔢',

    'exam': '🎯',

    'sports': '🏏',

    'analogy': '🌍',

    'story': '📖',

    'social': '💬',

    'socratic': '🧭'

};



const LANG_NAMES_MAP = {

    'hinglish': 'Hinglish',

    'english': 'English',

    'hindi': 'हिंदी',

    'urdu': 'اردو',

    'arabic': 'العربية'

};



function updateStyleEverywhere(styleKey) {

    if (!STYLE_NAMES_MAP[styleKey]) {

        if (styleKey === 'concept' || styleKey === 'intuition') styleKey = 'simple';

        else if (styleKey === 'steps' || styleKey === 'step-by-step') styleKey = 'step_by_step';

        else if (styleKey === 'real_life' || styleKey === 'real-life') styleKey = 'analogy';

        else if (styleKey === 'conversational') styleKey = 'social';

        else styleKey = 'simple';

    }



    currentStyle = styleKey;

    localStorage.setItem('defaultStyle', styleKey);



    const displayName = STYLE_NAMES_MAP[styleKey] || 'Quick Answer';

    const displayIcon = STYLE_ICONS_MAP[styleKey] || '⚡';



    // 1. Sidebar Badge

    if (navStyleBadge) {

        navStyleBadge.innerText = displayName;

    }

    // 2. Dropdowns

    if (quickStyleSelect) {

        quickStyleSelect.value = styleKey;

    }

    const settingStyleSelect = document.getElementById('setting-default-style-select');

    if (settingStyleSelect) {

        settingStyleSelect.value = styleKey;

    }



    // 3. Smart Mode Selector Active Card Highlight

    document.querySelectorAll('.mode-card').forEach(card => {

        const cStyle = card.getAttribute('data-style');

        if (cStyle === styleKey) {

            card.classList.add('active');

            card.setAttribute('aria-checked', 'true');

        } else {

            card.classList.remove('active');

            card.setAttribute('aria-checked', 'false');

        }

    });



    // 4. Selector Footer Pill Badge

    const modeBadge = document.getElementById('mode-selected-badge');

    if (modeBadge) {

        modeBadge.innerText = `${displayIcon} ${displayName}`;

    }



    // 5. Active Mode Bar Chip (Above Input)

    const chipIcon = document.getElementById('active-mode-chip-icon');

    const chipName = document.getElementById('active-mode-chip-name');

    if (chipIcon) chipIcon.innerText = displayIcon;

    if (chipName) chipName.innerText = displayName;

}



function updateLangEverywhere(langKey) {

    currentLanguage = langKey;

    localStorage.setItem('tutorLanguage', langKey);

    if (navLangBadge) {

        navLangBadge.innerText = LANG_NAMES_MAP[langKey] || 'Hinglish';

    }

    if (quickLangSelect) {

        quickLangSelect.value = langKey;

    }

    const settingLangSelect = document.getElementById('setting-language-select');

    if (settingLangSelect) {

        settingLangSelect.value = langKey;

    }

}



// 🧠 Smart Tutor Mode Selector Controller

const smartModeSelector = document.getElementById('smart-tutor-mode-selector');

const modeSelectorCloseBtn = document.getElementById('mode-selector-close-btn');

const activeModeToggleBtn = document.getElementById('active-mode-toggle-btn');

const modeSolveBtn = document.getElementById('mode-solve-btn');

const modeCards = document.querySelectorAll('.mode-card');



let hasUserDismissedModeSelector = false;

let hasSelectedStyleForConversation = false;

let isSubmittingMessage = false;



function showModeSelector() {

    if (!smartModeSelector) return;

    smartModeSelector.style.display = 'block';

    smartModeSelector.setAttribute('aria-hidden', 'false');

    const chevron = document.querySelector('.mode-chip-chevron');

    if (chevron) chevron.style.transform = 'rotate(180deg)';

}



function hideModeSelector() {

    if (!smartModeSelector) return;

    smartModeSelector.style.display = 'none';

    smartModeSelector.setAttribute('aria-hidden', 'true');

    const chevron = document.querySelector('.mode-chip-chevron');

    if (chevron) chevron.style.transform = 'rotate(0deg)';

}



function toggleModeSelector() {

    if (!smartModeSelector) return;

    if (smartModeSelector.style.display === 'none' || !smartModeSelector.style.display) {

        showModeSelector();

    } else {

        hideModeSelector();

    }

}



// Toggle on active mode chip click

if (activeModeToggleBtn) {

    activeModeToggleBtn.addEventListener('click', (e) => {

        e.preventDefault();

        e.stopPropagation();

        toggleModeSelector();

    });

}



// Dismiss button inside selector

if (modeSelectorCloseBtn) {

    modeSelectorCloseBtn.addEventListener('click', (e) => {

        e.preventDefault();

        e.stopPropagation();

        hideModeSelector();

        hasUserDismissedModeSelector = true; // Dismissed: do not reopen on keystroke

        if (userInput) userInput.focus();

    });

}



// Mode cards click & keyboard selection

modeCards.forEach(card => {

    const handleSelect = (e) => {

        e.preventDefault();

        const styleKey = card.getAttribute('data-style');

        if (styleKey) {

            updateStyleEverywhere(styleKey);

            hasSelectedStyleForConversation = true;

            hideModeSelector();

            // If question is entered (from card click or typing), automatically submit with this chosen style!

            if (userInput && (userInput.value.trim().length > 0 || currentAttachedFileName)) {

                submitUserMessage(true);

            }

        }

    };



    card.addEventListener('click', handleSelect);

    card.addEventListener('keydown', (e) => {

        if (e.key === 'Enter' || e.key === ' ') {

            handleSelect(e);

        }

    });

});



// Primary Solve Button inside selector

if (modeSolveBtn) {

    modeSolveBtn.addEventListener('click', (e) => {

        e.preventDefault();

        e.stopPropagation();

        hasSelectedStyleForConversation = true;

        hideModeSelector();

        submitUserMessage(true);

    });

}



// Close selector when clicking outside (without clearing input or resetting state)

document.addEventListener('click', (e) => {

    if (!smartModeSelector || smartModeSelector.style.display === 'none') return;

    if (

        smartModeSelector.contains(e.target) || 

        (activeModeToggleBtn && activeModeToggleBtn.contains(e.target)) ||

        (e.target && e.target.closest && (e.target.closest('.topic-card') || e.target.closest('.chat-input-container')))

    ) {

        return;

    }

    hideModeSelector();

});



// Close selector on Escape key

document.addEventListener('keydown', (e) => {

    if (e.key === 'Escape' && smartModeSelector && smartModeSelector.style.display !== 'none') {

        hideModeSelector();

        if (userInput) userInput.focus();

    }

});



// Initial Sync

updateStyleEverywhere(currentStyle);

updateLangEverywhere(currentLanguage);



if (quickStyleSelect) {

    quickStyleSelect.addEventListener('change', (e) => {

        hasSelectedStyleForConversation = true;

        updateStyleEverywhere(e.target.value);

    });

}



if (quickLangSelect) {

    quickLangSelect.addEventListener('change', (e) => {

        updateLangEverywhere(e.target.value);

    });

}



if (navClassBadge && savedGrade) {

    navClassBadge.innerText = savedGrade;

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



if (navTutorLangBtn) {

    navTutorLangBtn.addEventListener('click', () => {

        openSettingsToTab('tab-general');

    });

}









// 1. Math Shortcuts Toolbar (x², √, π etc.)

const symButtons = document.querySelectorAll('.sym-btn');

const userInput = document.getElementById('user-input');



symButtons.forEach(button => {

    button.addEventListener('click', () => {

        if (userInput) {

            userInput.value += button.innerText;

            autoResizeInput();

            userInput.focus();

        }

    });

});



// 📝 Auto-Expanding Dynamic Textarea (Compact 1-row default <-> Full-width Multiline)

function autoResizeInput() {

    if (!userInput) return;

    const form = document.getElementById('chat-form');

    

    // Temporarily reset height to measure true scrollHeight

    userInput.style.height = 'auto';

    const scrollH = userInput.scrollHeight;

    const val = userInput.value;

    const hasLineBreak = val.includes('\n');

    

    // Multiline triggers ONLY when line break exists or text has wrapped beyond single-line height

    const isMulti = (hasLineBreak || scrollH > 32) && val.trim().length > 0;



    if (form) {

        if (isMulti) {

            form.classList.add('multiline-mode');

            const targetH = Math.min(scrollH, 160);

            userInput.style.height = targetH + 'px';

            userInput.style.overflowY = scrollH > 160 ? 'auto' : 'hidden';

        } else {

            form.classList.remove('multiline-mode');

            userInput.style.height = '24px';

            userInput.style.overflowY = 'hidden';

        }

    }

}



// ⌨️ Enter Key to Send Message (Shift+Enter for newline)

if (userInput) {

    userInput.addEventListener('input', () => {

        autoResizeInput();

        const val = userInput.value.trim();

        // Show smart mode selector when student enters question (if not previously dismissed or already selected)

        if (val.length > 0 && !hasUserDismissedModeSelector && !hasSelectedStyleForConversation) {

            showModeSelector();

        }

    });

    userInput.addEventListener('keydown', function (e) {

        if ((e.key === 'Enter' || e.keyCode === 13) && !e.shiftKey && !e.ctrlKey && !e.altKey) {

            e.preventDefault();

            submitUserMessage();

        }

    });

}





// 2. Plus Button (+ ChatGPT Style Attachment Popup Menu & Multi-format File Upload)

const plusBtn = document.getElementById('plus-btn');

const attachDropdown = document.getElementById('attach-dropdown-menu');

const fileInput = document.getElementById('file-input');

const attachedFilesContainer = document.getElementById('attached-files-container');

const fileChipIcon = document.getElementById('file-chip-icon');

const fileChipName = document.getElementById('file-chip-name');

const fileChipMeta = document.getElementById('file-chip-meta');

const fileChipRemove = document.getElementById('file-chip-remove');



let currentAttachedFileName = "";

let currentAttachedFileText = "";

let currentAttachedImageSrc = "";

let ocrExtractedText = "";



function clearAttachedFile() {

    currentAttachedFileName = "";

    currentAttachedFileText = "";

    currentAttachedImageSrc = "";

    ocrExtractedText = "";

    if (fileInput) fileInput.value = '';

    const cameraInput = document.getElementById('camera-capture-input');

    if (cameraInput) cameraInput.value = '';

    const chipThumb = document.getElementById('file-chip-thumb');

    if (chipThumb) {

        chipThumb.src = '';

        chipThumb.style.display = 'none';

    }

    if (fileChipIcon) fileChipIcon.style.display = 'inline-block';

    if (attachedFilesContainer) attachedFilesContainer.style.display = 'none';

}



if (fileChipRemove) {

    fileChipRemove.addEventListener('click', (e) => {

        e.stopPropagation();

        clearAttachedFile();

    });

}



// Toggle ChatGPT Attachment Popup Menu

if (plusBtn && attachDropdown) {

    plusBtn.addEventListener('click', (e) => {

        e.stopPropagation();

        const isHidden = attachDropdown.style.display === 'none' || attachDropdown.style.display === '';

        attachDropdown.style.display = isHidden ? 'block' : 'none';

    });



    // Close when clicking outside

    document.addEventListener('click', (e) => {

        if (!attachDropdown.contains(e.target) && e.target !== plusBtn) {

            attachDropdown.style.display = 'none';

        }

    });

}



// 📸 Reusable Attachment Handler (Processes both camera snaps & uploaded files)

function isMeaningfulMathText(text) {

    if (!text || text.trim().length < 2) return false;

    const t = text.trim();

    const mathSymbolsMatch = t.match(/[\d\+\-\*/\=\^\(\)\[\]\{\}\<\>\%\√\∫\π\θ\±\÷\×]/g);

    const mathKeywordsMatch = t.match(/\b(solve|find|evaluate|simplify|prove|equation|triangle|angle|ratio|polynomial|root|derivative|integral|matrix|probability|surface|volume|circle|class|ncert|theorem|formula|radius|area|perimeter|factor|lcm|hcf|fraction|algebra|geometry)\b/i);

    

    const mathCharCount = mathSymbolsMatch ? mathSymbolsMatch.length : 0;

    const hasMathKeyword = !!mathKeywordsMatch;



    // Reject garbled noisy OCR (e.g. text consisting mostly of random 1-2 letter fragments)

    const words = t.split(/\s+/).filter(w => w.length > 0);

    const shortWords = words.filter(w => w.length <= 2).length;

    const shortRatio = words.length > 0 ? (shortWords / words.length) : 0;



    if (words.length >= 5 && shortRatio > 0.55 && !hasMathKeyword) {

        return false;

    }



    if (hasMathKeyword && mathCharCount >= 1) return true;

    if (mathCharCount >= 3) return true;

    

    return false;

}



async function handleAttachedFile(file) {

    if (!file) return;

    currentAttachedFileName = file.name || 'math_photo.jpg';



    // Show attached preview chip

    if (attachedFilesContainer) attachedFilesContainer.style.display = 'block';

    if (fileChipName) fileChipName.innerText = currentAttachedFileName;



    const lower = currentAttachedFileName.toLowerCase();

    const isImage = file.type.startsWith('image/') || /\.(png|jpg|jpeg|webp|gif)$/i.test(lower);

    const chipThumb = document.getElementById('file-chip-thumb');



    let icon = "📄";

    let typeLabel = "Document";

    if (lower.endsWith('.pdf')) {

        icon = "📄";

        typeLabel = "PDF";

    } else if (isImage) {

        icon = "🖼️";

        typeLabel = "Photo";

    } else if (lower.endsWith('.zip')) {

        icon = "📦";

        typeLabel = "ZIP";

    } else if (/\.(txt|md|csv)$/i.test(lower)) {

        icon = "📝";

        typeLabel = "Text";

    }



    if (fileChipIcon) fileChipIcon.innerText = icon;

    const sizeKb = Math.round(file.size / 1024);

    const sizeStr = sizeKb < 1024 ? `${sizeKb} KB` : `${(sizeKb / 1024).toFixed(1)} MB`;



    // If Image, generate thumbnail preview & read Data URL

    if (isImage) {

        const reader = new FileReader();

        reader.onload = (re) => {

            currentAttachedImageSrc = re.target.result;

            if (chipThumb) {

                chipThumb.src = currentAttachedImageSrc;

                chipThumb.style.display = 'block';

            }

            if (fileChipIcon) fileChipIcon.style.display = 'none';

        };

        reader.readAsDataURL(file);

    } else {

        if (chipThumb) chipThumb.style.display = 'none';

        if (fileChipIcon) fileChipIcon.style.display = 'inline-block';

    }



    if (fileChipMeta) fileChipMeta.innerText = `${typeLabel} · ${sizeStr}`;



    // 1. Call Backend /api/chat/parse-file

    try {

        const formData = new FormData();

        formData.append('file', file);

        const parseRes = await fetch(`${API_BASE_URL}/api/chat/parse-file`, {

            method: 'POST',

            body: formData

        });

        const parseData = await parseRes.json();

        if (parseData.success && parseData.extracted_text) {

            currentAttachedFileText = parseData.extracted_text;

            if (fileChipMeta) fileChipMeta.innerText = `${typeLabel} · ${parseData.size_str} (Parsed & Ready)`;

        }

    } catch (err) {

        console.warn('Backend file parse failed (client fallback used):', err);

    }



    // 2. If Image, run Tesseract OCR for Math formulas

    if (isImage) {

        if (fileChipMeta) fileChipMeta.innerText = `Photo · ${sizeStr} (⌛ Scanning for Math...)`;

        try {

            if (window.Tesseract) {

                const res = await Tesseract.recognize(file, 'eng');

                if (res && res.data && res.data.text.trim()) {

                    ocrExtractedText = res.data.text.trim();

                    const cleanOcr = ocrExtractedText.replace(/\n+/g, ' ').trim();

                    

                    if (isMeaningfulMathText(cleanOcr)) {

                        currentAttachedFileText = cleanOcr;

                        if (fileChipMeta) fileChipMeta.innerText = `Math Detected · "${cleanOcr.slice(0, 22)}..."`;

                        if (userInput && !userInput.value.trim()) {

                            userInput.value = `Solve: ${cleanOcr}`;

                            autoResizeInput();

                            userInput.focus();

                        }

                    } else {

                        // Non-math or noisy scan (keyboard, background, blurred):

                        // Do NOT dump gibberish text into user input! Keep clean & optimized prompt.

                        currentAttachedFileText = "Student attached an image/photo of a problem.";

                        if (fileChipMeta) fileChipMeta.innerText = `Photo Ready · Click Send to solve`;

                        if (userInput && !userInput.value.trim()) {

                            userInput.value = `Solve and explain this math question step by step`;

                            autoResizeInput();

                        }

                    }

                } else {

                    currentAttachedFileText = "Student attached an image/photo of a problem.";

                    if (fileChipMeta) fileChipMeta.innerText = `Photo Ready · Click Send to solve`;

                    if (userInput && !userInput.value.trim()) {

                        userInput.value = `Solve and explain this math question step by step`;

                        autoResizeInput();

                    }

                }

            }

        } catch (ocrErr) {

            console.warn('OCR error:', ocrErr);

            currentAttachedFileText = "Student attached an image/photo of a problem.";

            if (fileChipMeta) fileChipMeta.innerText = `Photo Ready · Click Send to solve`;

            if (userInput && !userInput.value.trim()) {

                userInput.value = `Solve and explain this math question step by step`;

                autoResizeInput();

            }

        }

    }

}



// 📸 Live Camera & Scanner Viewfinder Controller

let activeCameraStream = null;

let currentCameraFacingMode = 'environment'; // Default rear camera for scanning notebooks/books



const cameraModal = document.getElementById('camera-modal-backdrop');

const cameraCloseBtn = document.getElementById('camera-modal-close-btn');

const cameraSnapBtn = document.getElementById('camera-snap-btn');

const cameraFlipBtn = document.getElementById('camera-flip-btn');

const cameraNativeBtn = document.getElementById('camera-native-btn');

const cameraCaptureInput = document.getElementById('camera-capture-input');

const menuCameraSnap = document.getElementById('menu-camera-snap');



async function openLiveCamera() {

    if (attachDropdown) attachDropdown.style.display = 'none';



    // If mediaDevices not supported or on insecure HTTP, trigger native camera

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {

        if (cameraCaptureInput) cameraCaptureInput.click();

        return;

    }



    try {

        if (activeCameraStream) {

            activeCameraStream.getTracks().forEach(t => t.stop());

        }

        const constraints = {

            video: {

                facingMode: { ideal: currentCameraFacingMode },

                width: { ideal: 1280 },

                height: { ideal: 720 }

            },

            audio: false

        };

        activeCameraStream = await navigator.mediaDevices.getUserMedia(constraints);

        const videoEl = document.getElementById('camera-video-stream');

        if (videoEl) {

            videoEl.srcObject = activeCameraStream;

            videoEl.play();

        }

        if (cameraModal) cameraModal.style.display = 'flex';

    } catch (err) {

        console.warn('getUserMedia stream not available or permission denied, using native camera app:', err);

        if (cameraCaptureInput) cameraCaptureInput.click();

    }

}



function closeLiveCamera() {

    if (activeCameraStream) {

        activeCameraStream.getTracks().forEach(t => t.stop());

        activeCameraStream = null;

    }

    if (cameraModal) cameraModal.style.display = 'none';

}



if (menuCameraSnap) {

    menuCameraSnap.addEventListener('click', openLiveCamera);

}



if (cameraCloseBtn) {

    cameraCloseBtn.addEventListener('click', closeLiveCamera);

}



if (cameraModal) {

    cameraModal.addEventListener('click', (e) => {

        if (e.target === cameraModal) closeLiveCamera();

    });

}



// Flip Camera (Front / Rear)

if (cameraFlipBtn) {

    cameraFlipBtn.addEventListener('click', () => {

        currentCameraFacingMode = (currentCameraFacingMode === 'environment') ? 'user' : 'environment';

        openLiveCamera();

    });

}



// Native Camera App Trigger

if (cameraNativeBtn && cameraCaptureInput) {

    cameraNativeBtn.addEventListener('click', () => {

        closeLiveCamera();

        cameraCaptureInput.click();

    });

}



// Snap Photo from Video Stream

if (cameraSnapBtn) {

    cameraSnapBtn.addEventListener('click', () => {

        const videoEl = document.getElementById('camera-video-stream');

        const canvas = document.getElementById('camera-capture-canvas');

        if (videoEl && canvas && videoEl.videoWidth) {

            canvas.width = videoEl.videoWidth;

            canvas.height = videoEl.videoHeight;

            const ctx = canvas.getContext('2d');

            ctx.drawImage(videoEl, 0, 0, canvas.width, canvas.height);

            canvas.toBlob(blob => {

                if (blob) {

                    const photoFile = new File([blob], `math_camera_${Date.now()}.jpg`, { type: 'image/jpeg' });

                    handleAttachedFile(photoFile);

                    closeLiveCamera();

                }

            }, 'image/jpeg', 0.92);

        } else {

            closeLiveCamera();

            if (cameraCaptureInput) cameraCaptureInput.click();

        }

    });

}



// Mobile Native Camera Input Handler

if (cameraCaptureInput) {

    cameraCaptureInput.addEventListener('change', (e) => {

        if (e.target.files && e.target.files.length > 0) {

            handleAttachedFile(e.target.files[0]);

        }

    });

}



// Popup Menu Item: Upload Photos & Files (PDF, Image, ZIP, Docs)

const menuUploadFiles = document.getElementById('menu-upload-photos-files');

if (menuUploadFiles && fileInput) {

    menuUploadFiles.addEventListener('click', () => {

        if (attachDropdown) attachDropdown.style.display = 'none';

        fileInput.click();

    });

}



if (fileInput) {

    fileInput.addEventListener('change', (e) => {

        if (e.target.files.length > 0) {

            handleAttachedFile(e.target.files[0]);

        }

    });

}



// Popup Menu Item: NCERT Book Library

const menuNcertLibrary = document.getElementById('menu-ncert-library');

if (menuNcertLibrary) {

    menuNcertLibrary.addEventListener('click', () => {

        if (attachDropdown) attachDropdown.style.display = 'none';

        const devModal = document.getElementById('dev-admin-modal-backdrop');

        if (devModal) {

            devModal.style.display = 'flex';

            if (typeof fetchRagStats === 'function') fetchRagStats();

        } else if (userInput) {

            userInput.value = "Explain NCERT Class 10/11/12 key concept: ";

            autoResizeInput();

            userInput.focus();

        }

    });

}



// Popup Menu Item: Board Exam Formulas

const menuBoardFormulas = document.getElementById('menu-board-formulas');

if (menuBoardFormulas) {

    menuBoardFormulas.addEventListener('click', () => {

        if (attachDropdown) attachDropdown.style.display = 'none';

        if (userInput) {

            userInput.value = "Provide the complete Board Exam Formula Sheet with theorems and scoring tips for: ";

            autoResizeInput();

            userInput.focus();

        }

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

            selectedModelText.innerText = 'Groq';

            if (modelPillBtn) modelPillBtn.title = `Current Model: ${item.innerText.trim()}`;

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

            selectedModelText.innerText = 'Groq';

        }

        if (modelPillBtn) {

            modelPillBtn.title = `Current Model: ${item.innerText.trim()}`;

        }

        modelDropdown.style.display = 'none';

    });

});





// 4. Voice Mic Button (Speech-to-Text - Real-time Continuous Voice Recognition)

const micBtn = document.getElementById('mic-btn');

let activeSpeechRecognition = null;

let isVoiceRecording = false;

let sessionFinalTranscript = "";

let initialVoiceInputValue = "";



function stopRecordingUI() {

    isVoiceRecording = false;

    if (micBtn) {

        micBtn.classList.remove('recording-active');

        micBtn.title = "Speak to Tutor";

    }

    if (userInput) {

        userInput.placeholder = "Ask any math equation or concept...";

    }

}



function stopVoiceRecognition() {

    isVoiceRecording = false;

    if (activeSpeechRecognition) {

        try {

            activeSpeechRecognition.stop();

        } catch (e) {

            console.warn('Recognition stop error:', e);

        }

    }

    stopRecordingUI();

}



if (micBtn) {

    micBtn.addEventListener('click', () => {

        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {

            alert('Voice recognition is supported in Chrome, Edge, and Android web browsers.');

            return;

        }



        // Toggle Stop if already recording (Manual Stop on clicking mic button)

        if (isVoiceRecording) {

            stopVoiceRecognition();

            return;

        }



        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        activeSpeechRecognition = new SpeechRecognition();

        

        // Use active tutor language (fallback safely)

        const selectedLang = (typeof currentLanguage !== 'undefined' ? currentLanguage : (localStorage.getItem('tutorLanguage') || 'hinglish')).toLowerCase();



        if (selectedLang === 'hi' || selectedLang === 'hindi') {

            activeSpeechRecognition.lang = 'hi-IN';

        } else if (selectedLang === 'en' || selectedLang === 'english') {

            activeSpeechRecognition.lang = 'en-US';

        } else if (selectedLang === 'ur' || selectedLang === 'urdu') {

            activeSpeechRecognition.lang = 'ur-PK';

        } else if (selectedLang === 'ar' || selectedLang === 'arabic') {

            activeSpeechRecognition.lang = 'ar-SA';

        } else {

            activeSpeechRecognition.lang = 'en-IN'; // Default Hinglish / Indian English

        }



        // CONTINUOUS MODE: Do not stop when user pauses for breath!

        activeSpeechRecognition.continuous = true;

        activeSpeechRecognition.interimResults = true;



        initialVoiceInputValue = userInput ? userInput.value : "";

        sessionFinalTranscript = "";



        activeSpeechRecognition.onstart = () => {

            isVoiceRecording = true;

            micBtn.classList.add('recording-active');

            micBtn.title = "Listening (Continuous)... Click mic button to stop";

            if (userInput) {

                userInput.placeholder = "🎙️ Listening... Speak freely, pause anytime (Click mic to stop)...";

                userInput.focus();

            }

        };



        activeSpeechRecognition.onresult = (event) => {

            let interimTranscript = "";

            for (let i = event.resultIndex; i < event.results.length; ++i) {

                if (event.results[i].isFinal) {

                    sessionFinalTranscript += event.results[i][0].transcript + " ";

                } else {

                    interimTranscript += event.results[i][0].transcript;

                }

            }

            const currentSessionText = (sessionFinalTranscript + interimTranscript).trim();

            if (userInput && currentSessionText) {

                const spacePrefix = (initialVoiceInputValue && !initialVoiceInputValue.endsWith(' ')) ? ' ' : '';

                userInput.value = initialVoiceInputValue + spacePrefix + currentSessionText;

                if (typeof autoResizeInput === 'function') autoResizeInput();

            }

        };



        activeSpeechRecognition.onerror = (e) => {

            console.warn('Speech recognition notice:', e.error);

            if (e.error === 'not-allowed' || e.error === 'service-not-allowed') {

                alert('Microphone access blocked hai! Browser ke address bar me mic/lock icon par click karke Microphone "Allow" karein.');

                stopRecordingUI();

            } else if (e.error === 'network') {

                alert('Speech recognition network notice: Voice recognition ke liye active internet connection chahiye.');

                stopRecordingUI();

            }

            // Non-critical errors like 'no-speech' or aborted are ignored in continuous mode

        };



        activeSpeechRecognition.onend = () => {

            // If user did NOT manually click stop, keep continuous listening active across silence!

            if (isVoiceRecording) {

                try {

                    initialVoiceInputValue = userInput ? userInput.value : "";

                    sessionFinalTranscript = "";

                    activeSpeechRecognition.start();

                    return;

                } catch (err) {

                    console.warn('Continuous recognition restart notice:', err);

                }

            }

            stopRecordingUI();

        };



        try {

            isVoiceRecording = true;

            activeSpeechRecognition.start();

        } catch (err) {

            console.warn('Recognition start error:', err);

            stopRecordingUI();

        }

    });

}



// 5. Chat Submission Logic (Ask Tutor)

function submitUserMessage(forceSend = false) {

    if (typeof stopVoiceRecognition === 'function') {

        stopVoiceRecognition();

    }

    if (isSubmittingMessage) return; // Prevent double submission

    if (!userInput) return;

    const question = userInput.value.trim();

    if (!question && !currentAttachedFileName) return;



    // Whenever user presses Enter or clicks Send, lock in chosen style, dismiss selector, and send immediately!

    hideModeSelector();

    hasSelectedStyleForConversation = true;



    isSubmittingMessage = true;

    if (sendBtn) sendBtn.disabled = true;

    if (modeSolveBtn) modeSolveBtn.disabled = true;



    let displayQuestion = question;

    if (currentAttachedImageSrc) {

        displayQuestion = `<div style="margin-bottom: 8px;"><img src="${currentAttachedImageSrc}" alt="Math Question Photo" style="max-width: 260px; max-height: 200px; border-radius: 8px; border: 1px solid #334155; object-fit: contain; background: #0b0f19; display: block;" /></div>` + (question || "Solve and explain this math question step by step");

    } else if (currentAttachedFileName) {

        displayQuestion = `📎 [Attached: ${currentAttachedFileName}]<br>` + (question || "Solve and explain the problems in this file step by step");

    }



    const sendingFileName = currentAttachedFileName;

    const sendingFileText = currentAttachedFileText;



    // Student message bubble

    appendMessage('You', displayQuestion, 'user');

    userInput.value = '';

    const formEl = document.getElementById('chat-form');

    if (formEl) formEl.classList.remove('multiline-mode');

    userInput.style.height = '24px';

    userInput.style.overflowY = 'hidden';

    clearAttachedFile();



    // ⏳ Animated Thinking Indicator

    const thinkingEl = document.createElement('div');

    thinkingEl.id = 'ai-thinking-indicator';

    thinkingEl.className = 'message assistant thinking-bubble-msg';

    thinkingEl.innerHTML = `

        <div class="avatar">👩‍🏫</div>

        <div class="message-content">

            <h4>AI Maths Tutor</h4>

            <div class="thinking-row">

                <span class="thinking-dot"></span>

                <span class="thinking-dot"></span>

                <span class="thinking-dot"></span>

                <span class="thinking-label">Thinking & searching NCERT...</span>

            </div>

        </div>

    `;

    if (messagesContainer) {

        messagesContainer.appendChild(thinkingEl);

        messagesContainer.scrollTop = messagesContainer.scrollHeight;

    }



    const selectedLanguage = localStorage.getItem('tutorLanguage') || 'hinglish';

    const isNewSession = !currentChatId;



    const userAuthToken = localStorage.getItem('authToken');

    const authHeaders = { 'Content-Type': 'application/json' };

    if (userAuthToken) {

        authHeaders['Authorization'] = `Bearer ${userAuthToken}`;

    }



    // 🚀 Asli FastAPI Backend API Call:

    fetch(`${API_BASE_URL}/api/chat`, {

        method: 'POST',

        headers: authHeaders,

        body: JSON.stringify({

            question: question,

            style: currentStyle,

            language: selectedLanguage,

            model: currentModel,

            grade: localStorage.getItem('studentGrade') || 'Class 10',

            chat_id: currentChatId,

            user_id: getUserId(),

            attachment_name: sendingFileName,

            attachment_text: sendingFileText,

        })

    })

    .then(async response => {

        const ind = document.getElementById('ai-thinking-indicator');

        if (ind) ind.remove();



        if (!response.ok) {

            const errData = await response.json().catch(() => ({}));

            throw new Error(errData.detail || `Server error ${response.status}`);

        }

        return response.json();

    })

    .then(data => {



        if (data.reply) {

            appendMessage('AI Maths Tutor', data.reply, 'assistant', data.image_url, data.image_prompt, data.image_provider);

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

        isSubmittingMessage = false;

        if (sendBtn) sendBtn.disabled = false;

        if (modeSolveBtn) modeSolveBtn.disabled = false;

    })

    .catch(error => {

        isSubmittingMessage = false;

        if (sendBtn) sendBtn.disabled = false;

        if (modeSolveBtn) modeSolveBtn.disabled = false;

        console.error('Error:', error);

        // Remove thinking indicator

        const ind = document.getElementById('ai-thinking-indicator');

        if (ind) ind.remove();



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

        submitUserMessage(true);

    });

}





// Helper: Markdown, SVG, and Math Formatter

function renderMarkdown(rawText) {

    if (!rawText) return '';

    let html = rawText;



    // Deduplicate any repeated consecutive blockquote notes (from old stored chats)

    html = html.replace(/(?:>\s*\*\([ℹ️\s]*Note:[^\n]+\*\s*\n*){2,}/gi, (match) => {

        const lines = match.trim().split('\n');

        return lines[0] + '\n\n';

    });



    // 0. Extract and protect LaTeX math blocks from markdown corruption

    // Protect $$...$$, \[...\], \(...\), and $...$

    const mathBlocks = [];



    // Display math: $$...$$

    html = html.replace(/\$\$([\s\S]*?)\$\$/g, (match) => {

        const placeholder = `___MATH_BLOCK_${mathBlocks.length}___`;

        mathBlocks.push(match);

        return placeholder;

    });



    // Display math: \[...\]

    html = html.replace(/\\\[([\s\S]*?)\\\]/g, (match) => {

        const placeholder = `___MATH_BLOCK_${mathBlocks.length}___`;

        mathBlocks.push(match);

        return placeholder;

    });



    // Inline math: \(...\)

    html = html.replace(/\\\(([\s\S]*?)\\\)/g, (match) => {

        const placeholder = `___MATH_BLOCK_${mathBlocks.length}___`;

        mathBlocks.push(match);

        return placeholder;

    });



    // Inline math: $...$ (ensure not an escaped \$ or currency)

    html = html.replace(/(^|[^\\])\$([^\$\n]+?)\$/g, (match, prefix, mathContent) => {

        const placeholder = `___MATH_BLOCK_${mathBlocks.length}___`;

        mathBlocks.push(`$${mathContent}$`);

        return `${prefix}${placeholder}`;

    });



    // Standalone LaTeX environments not yet enclosed in delimiters

    html = html.replace(/\\begin\{(?:aligned|gathered|cases|matrix|bmatrix|pmatrix)\}[\s\S]*?\\end\{(?:aligned|gathered|cases|matrix|bmatrix|pmatrix)\}/g, (match) => {

        const placeholder = `___MATH_BLOCK_${mathBlocks.length}___`;

        mathBlocks.push(`$$\n${match}\n$$`);

        return placeholder;

    });



    // 1. First extract and preserve SVG code blocks ```svg ... ```

    const svgs = [];

    html = html.replace(/```(?:svg|xml)?\s*(<svg[\s\S]*?<\/svg>)\s*```/gi, (match, svgContent) => {

        const placeholder = `__SVG_DIAGRAM_${svgs.length}__`;

        svgs.push(svgContent);

        return placeholder;

    });



    // 2. Direct inline <svg> ... </svg> preservation

    html = html.replace(/(<svg[\s\S]*?<\/svg>)/gi, (match, svgContent) => {

        const placeholder = `__SVG_DIAGRAM_${svgs.length}__`;

        svgs.push(svgContent);

        return placeholder;

    });



    // 3. Code blocks ```...```

    html = html.replace(/```([\s\S]*?)```/g, (match, p1) => {

        return `<div class="math-code-block"><pre>${p1.trim()}</pre></div>`;

    });



    // 4. Blockquotes (> ...)

    html = html.replace(/^>\s*(.*$)/gim, '<blockquote class="chat-blockquote">$1</blockquote>');



    // 5. Headers #####, ####, ###, ##, #

    html = html.replace(/^##### (.*$)/gim, '<h6 class="chat-h6">$1</h6>');

    html = html.replace(/^#### (.*$)/gim, '<h5 class="chat-h5">$1</h5>');

    html = html.replace(/^### (.*$)/gim, '<h5 class="chat-h5">$1</h5>');

    html = html.replace(/^## (.*$)/gim, '<h4 class="chat-h4">$1</h4>');

    html = html.replace(/^# (.*$)/gim, '<h3 class="chat-h3">$1</h3>');



    // 6. Bold **text**

    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');



    // 7. Italic *text*

    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');



        // 7a. Markdown Images ![Alt](URL)

    html = html.replace(/!\[([^\]]*)\]\((https?:\/\/[^\s\)]+)\)/g, `

        <div class="chat-diagram-img-wrap" title="$1">

            <img src="$2" alt="$1" class="chat-diagram-img" loading="lazy" />

            <div class="diagram-caption">🎨 $1</div>

        </div>

    `);



    // 7b. Clickable Markdown Links [Text](URL)

    html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="chat-ncert-btn">$1</a>');



    // 8. Bullet points

    html = html.replace(/^\s*[-•]\s+(.*)$/gim, '<li class="chat-list-item">$1</li>');



    // 9. Numbered lists

    html = html.replace(/^\s*(\d+)\.\s+(.*)$/gim, '<li class="chat-num-item"><strong>$1.</strong> $2</li>');



    // 10. Horizontal rules (---)

    html = html.replace(/^\s*---\s*$/gim, '<hr class="chat-divider">');



    // 11. Clean up line breaks around headings and list items

    html = html.replace(/\n{3,}/g, '\n\n');

    html = html.replace(/\n\n/g, '<div class="chat-gap"></div>');

    html = html.replace(/\n/g, '<br>');

    html = html.replace(/(?:<br>)+<div class="chat-gap"><\/div>/g, '<div class="chat-gap"></div>');

    html = html.replace(/<div class="chat-gap"><\/div>(?:<br>)+/g, '<div class="chat-gap"></div>');

    // Remove redundant <br> tags immediately preceding or following headings/dividers/blockquotes

    html = html.replace(/<br>\s*(<(?:h[3-6]|blockquote|hr|li|div class="chat-gap"))/gi, '$1');

    html = html.replace(/(<\/(?:h[3-6]|blockquote|hr|li)>)\s*<br>/gi, '$1');



    // 12. Restore SVGs into responsive, styled visual containers (use function to prevent $ replacement issues)

    svgs.forEach((svgStr, idx) => {

        let cleanSvg = svgStr.replace(/<br>/g, '').replace(/<div class="chat-gap"><\/div>/g, '');

        

        // Context-Aware Multi-Theme Visualizer (Coding, Space, Finance, Football, Badminton, Car, Cricket, Standard)
        const combinedContext = cleanSvg + ' ' + html;
        const isTrigonometry = /Trig|Trigonometry|sin|cos|tan|hypotenuse|angle|theta|right[- ]angled/i.test(combinedContext);
        const isCalculus = !isTrigonometry && /Derivative|Calculus|Instant|Speed|Rate of change|Trajectory|s\(t\)|v\(t\)|\/dt|ds\/dt|lim|tangent/i.test(combinedContext);
        
        const isCoding = /Code|Coding|Python|Algorithm|Binary|Developer|Software|Terminal/i.test(combinedContext);
        const isSpace = !isCoding && /Rocket|Space|Orbit|Satellite|Astronomy|Planet|NASA|Gravity/i.test(combinedContext);
        const isFinance = !isCoding && !isSpace && /Stock|Finance|Market|Trading|Profit|Loss/i.test(combinedContext);
        const isFootball = !isCoding && !isSpace && !isFinance && /Football|Soccer|Striker|Goal|Penalty|Free-?kick/i.test(combinedContext);
        const isBadminton = !isCoding && !isSpace && !isFinance && !isFootball && /Badminton|Shuttle|Shuttlecock|Racket|Smash/i.test(combinedContext);
        const isCar = !isCoding && !isSpace && !isFinance && !isFootball && !isBadminton && /Car|Speedometer|Racing|Driving|Vehicle/i.test(combinedContext);
        const isCricket = !isCoding && !isSpace && !isFinance && !isFootball && !isBadminton && !isCar && (/Batsman|Boundary|Flight Path|Pitch|Cricket|circket|bowler/i.test(combinedContext) || (html.includes('Sports Mode') && !isFootball));

        if (isCoding) {
            cleanSvg = `<svg viewBox="0 0 450 250" width="100%" xmlns="http://www.w3.org/2000/svg" class="math-svg-diagram">
  <defs>
    <linearGradient id="codeTermGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#090d16"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#codeTermGrad)" rx="12" stroke="#0284c7" stroke-width="1.5"/>
  <!-- Terminal Top Bar -->
  <rect width="100%" height="28" fill="#1e293b" rx="12"/>
  <rect y="18" width="100%" height="10" fill="#1e293b"/>
  <circle cx="18" cy="14" r="4.5" fill="#ef4444"/>
  <circle cx="32" cy="14" r="4.5" fill="#f59e0b"/>
  <circle cx="46" cy="14" r="4.5" fill="#10b981"/>
  <text x="70" y="18" fill="#94a3b8" font-size="10.5" font-family="monospace">terminal · algorithm_derivative_visualizer.py</text>
  <!-- Left Side: Code Editor -->
  <rect x="12" y="38" width="200" height="198" rx="8" fill="#0b1120" stroke="#334155" stroke-width="1"/>
  <text x="22" y="58" fill="#38bdf8" font-size="10.5" font-family="monospace"># Rate of Change Algorithm</text>
  <text x="22" y="78" fill="#f43f5e" font-size="10.5" font-family="monospace">def <tspan fill="#fde047">instantaneous_rate</tspan>(t):</text>
  <text x="36" y="96" fill="#94a3b8" font-size="10" font-family="monospace">h = 0.0001</text>
  <text x="36" y="114" fill="#94a3b8" font-size="10" font-family="monospace">ds = s(t + h) - s(t)</text>
  <text x="36" y="132" fill="#22c55e" font-size="10" font-family="monospace">return ds / h  <tspan fill="#64748b"># v(t)</tspan></text>
  <text x="22" y="160" fill="#a855f7" font-size="10.5" font-family="monospace"># Complexity Curve O(n)</text>
  <text x="22" y="180" fill="#38bdf8" font-size="10" font-family="monospace">v = derivative(f, t=2.0)</text>
  <rect x="22" y="196" width="180" height="26" rx="4" fill="rgba(34, 197, 94, 0.15)" stroke="#22c55e" stroke-width="1"/>
  <text x="30" y="213" fill="#22c55e" font-size="10.5" font-weight="bold" font-family="monospace">⚡ Output: v(2.0) = 48.0 m/s</text>
  <!-- Right Side: Mathematical Coordinate Curve -->
  <rect x="222" y="38" width="216" height="198" rx="8" fill="#0b1120" stroke="#334155" stroke-width="1"/>
  <!-- Axes -->
  <line x1="240" y1="210" x2="420" y2="210" stroke="#475569" stroke-width="1.5"/>
  <line x1="240" y1="210" x2="240" y2="52" stroke="#475569" stroke-width="1.5"/>
  <text x="415" y="222" fill="#64748b" font-size="9" font-family="monospace">t</text>
  <text x="232" y="52" fill="#64748b" font-size="9" font-family="monospace">s(t)</text>
  <!-- Function Curve -->
  <path d="M 245 200 Q 310 170 340 120 T 410 65" fill="none" stroke="#38bdf8" stroke-width="2.5"/>
  <!-- Tangent Line at point (340, 120) -->
  <line x1="285" y1="170" x2="395" y2="70" stroke="#22c55e" stroke-width="2.5"/>
  <circle cx="340" cy="120" r="5" fill="#fde047" stroke="#ffffff" stroke-width="1.5"/>
  <!-- Callout Badge -->
  <rect x="250" y="55" width="170" height="34" rx="4" fill="rgba(15, 23, 42, 0.95)" stroke="#22c55e" stroke-width="1"/>
  <text x="258" y="70" fill="#22c55e" font-size="9.5" font-weight="bold">⚡ Tangent Slope = s'(t)</text>
  <text x="258" y="83" fill="#94a3b8" font-size="9">Rate of Change dx/dt</text>
</svg>`;
        } else if (isSpace) {
            cleanSvg = `<svg viewBox="0 0 450 250" width="100%" xmlns="http://www.w3.org/2000/svg" class="math-svg-diagram">
  <defs>
    <linearGradient id="spaceGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#030712"/>
      <stop offset="60%" stop-color="#0b1120"/>
      <stop offset="100%" stop-color="#1e1b4b"/>
    </linearGradient>
    <linearGradient id="planetGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1e40af"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#spaceGrad)" rx="12"/>
  <!-- Stars -->
  <circle cx="40" cy="30" r="1.5" fill="#ffffff" opacity="0.9"/>
  <circle cx="120" cy="45" r="1.2" fill="#ffffff" opacity="0.8"/>
  <circle cx="280" cy="25" r="1.5" fill="#ffffff" opacity="0.9"/>
  <circle cx="360" cy="40" r="1.2" fill="#ffffff" opacity="0.7"/>
  <circle cx="410" cy="80" r="1.5" fill="#ffffff" opacity="0.8"/>
  <!-- Curved Earth Horizon -->
  <path d="M -50 250 Q 225 180 500 250" fill="url(#planetGrad)" stroke="#38bdf8" stroke-width="1.5"/>
  <text x="225" y="235" fill="#93c5fd" font-size="11" font-weight="bold" text-anchor="middle">🌍 Planetary Gravitational Field</text>
  <!-- Rocket Launch Trajectory -->
  <path d="M 90 205 Q 160 90 320 60" fill="none" stroke="#f59e0b" stroke-width="3" stroke-dasharray="6,4"/>
  <text x="140" y="110" fill="#f59e0b" font-size="10.5" font-weight="bold">Flight Path r(t)</text>
  <!-- Rocket Icon at (240, 75) -->
  <circle cx="240" cy="75" r="6" fill="#ef4444"/>
  <!-- Escape Velocity Tangent Line -->
  <line x1="170" y1="92" x2="330" y2="52" stroke="#22c55e" stroke-width="3"/>
  <polygon points="330,52 318,46 320,58" fill="#22c55e"/>
  <!-- Formula Card -->
  <rect x="230" y="95" width="205" height="50" rx="6" fill="rgba(15, 23, 42, 0.95)" stroke="#22c55e" stroke-width="1.2"/>
  <text x="240" y="115" fill="#22c55e" font-size="11" font-weight="bold">🚀 Escape Velocity Tangent</text>
  <text x="240" y="133" fill="#f8fafc" font-size="10">v(t) = dr/dt | a(t) = d²r/dt² [Thrust]</text>
</svg>`;
        } else if (isFootball) {
            cleanSvg = `<svg viewBox="0 0 450 250" width="100%" xmlns="http://www.w3.org/2000/svg" class="math-svg-diagram">
  <defs>
    <linearGradient id="skyGradFB" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#0b1120"/>
      <stop offset="60%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
    <linearGradient id="grassGradFB" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#15803d"/>
      <stop offset="50%" stop-color="#166534"/>
      <stop offset="100%" stop-color="#14532d"/>
    </linearGradient>
    <pattern id="netPattern" width="10" height="10" patternUnits="userSpaceOnUse">
      <path d="M 0 0 L 10 10 M 10 0 L 0 10" fill="none" stroke="rgba(255,255,255,0.22)" stroke-width="1"/>
    </pattern>
  </defs>
  <rect width="100%" height="100%" fill="url(#skyGradFB)" rx="12"/>
  <circle cx="60" cy="15" r="45" fill="rgba(56, 189, 248, 0.08)" />
  <circle cx="390" cy="15" r="45" fill="rgba(56, 189, 248, 0.08)" />
  <rect x="0" y="195" width="450" height="55" fill="url(#grassGradFB)"/>
  <line x1="0" y1="195" x2="450" y2="195" stroke="#22c55e" stroke-width="2.5"/>
  <line x1="100" y1="195" x2="100" y2="245" stroke="#ffffff" stroke-width="2" opacity="0.7"/>
  <circle cx="85" cy="205" r="3" fill="#ffffff"/>
  <!-- Goal Post & Net -->
  <polygon points="370,195 370,75 425,110 425,195" fill="url(#netPattern)" stroke="rgba(255,255,255,0.3)" stroke-width="1.5"/>
  <line x1="370" y1="195" x2="370" y2="75" stroke="#ffffff" stroke-width="4.5" stroke-linecap="round"/>
  <line x1="370" y1="75" x2="425" y2="110" stroke="#ffffff" stroke-width="3.5" stroke-linecap="round"/>
  <line x1="425" y1="110" x2="425" y2="195" stroke="#ffffff" stroke-width="3" stroke-linecap="round"/>
  <rect x="360" y="52" width="78" height="18" rx="4" fill="rgba(15, 23, 42, 0.9)" stroke="#22c55e" stroke-width="1"/>
  <text x="399" y="65" fill="#22c55e" font-size="10" font-weight="bold" text-anchor="middle">🥅 Top Corner Goal</text>
  <!-- Footballer Striker Character -->
  <path d="M 64 165 Q 60 180 58 197" stroke="#1e293b" stroke-width="6.5" stroke-linecap="round" fill="none"/>
  <circle cx="58" cy="197" r="3.5" fill="#f59e0b"/>
  <path d="M 68 165 Q 82 175 96 160" stroke="#1e293b" stroke-width="6.5" stroke-linecap="round" fill="none"/>
  <circle cx="96" cy="160" r="4" fill="#ef4444"/>
  <path d="M 58 135 L 72 138 L 70 166 L 56 164 Z" fill="#ef4444"/>
  <circle cx="64" cy="124" r="8.5" fill="#fde047"/>
  <path d="M 58 120 Q 64 114 70 120" stroke="#78350f" stroke-width="4" fill="none"/>
  <path d="M 56 140 L 46 148 M 70 142 L 80 150" stroke="#fde047" stroke-width="3" stroke-linecap="round"/>
  <rect x="30" y="92" width="70" height="18" rx="4" fill="rgba(15, 23, 42, 0.9)" stroke="#38bdf8" stroke-width="1"/>
  <text x="65" y="105" fill="#38bdf8" font-size="10" font-weight="bold" text-anchor="middle">⚽ Striker (Kick)</text>
  <!-- Math Trajectory & Tangent -->
  <path d="M 102 156 Q 220 30 370 82" fill="none" stroke="#38bdf8" stroke-width="2.5" stroke-dasharray="6,4" opacity="0.9"/>
  <text x="215" y="44" fill="#38bdf8" font-size="11.5" font-weight="bold">Ball Flight Curve s(t)</text>
  <circle cx="215" cy="62" r="8" fill="#ffffff" stroke="#000000" stroke-width="1.5"/>
  <polygon points="215,58 219,61 217,65 213,65 211,61" fill="#0f172a"/>
  <polygon points="220,60 223,61 223,58" fill="#0f172a"/>
  <polygon points="210,60 207,61 207,58" fill="#0f172a"/>
  <line x1="160" y1="48" x2="275" y2="76" stroke="#22c55e" stroke-width="3"/>
  <polygon points="275,76 263,68 266,80" fill="#22c55e"/>
  <rect x="130" y="88" width="195" height="42" rx="6" fill="rgba(15, 23, 42, 0.92)" stroke="#22c55e" stroke-width="1.5"/>
  <text x="140" y="105" fill="#22c55e" font-size="11" font-weight="bold">⚡ Tangent Slope = Derivative</text>
  <text x="140" y="122" fill="#f8fafc" font-size="10.5" font-weight="600">v(t) = s'(t) = lim (Δs / Δt) [Kick Speed]</text>
</svg>`;
        } else if (isBadminton) {
            cleanSvg = `<svg viewBox="0 0 450 250" width="100%" xmlns="http://www.w3.org/2000/svg" class="math-svg-diagram">
  <defs>
    <linearGradient id="skyGradBM" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#090d16"/>
      <stop offset="100%" stop-color="#1e1b4b"/>
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#skyGradBM)" rx="12"/>
  <rect x="0" y="195" width="450" height="55" fill="#047857"/>
  <line x1="0" y1="195" x2="450" y2="195" stroke="#34d399" stroke-width="2.5"/>
  <line x1="225" y1="195" x2="225" y2="140" stroke="#f8fafc" stroke-width="3"/>
  <rect x="220" y="140" width="10" height="55" fill="rgba(255,255,255,0.3)" stroke="#f8fafc" stroke-width="1"/>
  <rect x="195" y="118" width="60" height="18" rx="4" fill="rgba(15, 23, 42, 0.9)" stroke="#34d399" stroke-width="1"/>
  <text x="225" y="131" fill="#34d399" font-size="10" font-weight="bold" text-anchor="middle">🏸 Court Net</text>
  <path d="M 60 150 L 52 185 M 70 150 L 78 185" stroke="#f8fafc" stroke-width="5" stroke-linecap="round"/>
  <path d="M 54 125 L 68 128 L 65 152 L 52 150 Z" fill="#8b5cf6"/>
  <circle cx="62" cy="115" r="8" fill="#fde047"/>
  <path d="M 64 128 L 78 110" stroke="#fde047" stroke-width="3" stroke-linecap="round"/>
  <circle cx="85" cy="102" r="8" fill="none" stroke="#f59e0b" stroke-width="2"/>
  <line x1="78" y1="110" x2="82" y2="106" stroke="#ef4444" stroke-width="3"/>
  <rect x="30" y="80" width="70" height="18" rx="4" fill="rgba(15, 23, 42, 0.9)" stroke="#a78bfa" stroke-width="1"/>
  <text x="65" y="93" fill="#a78bfa" font-size="10" font-weight="bold" text-anchor="middle">🏸 Jump Smash</text>
  <path d="M 88 100 Q 225 90 380 195" fill="none" stroke="#38bdf8" stroke-width="2.5" stroke-dasharray="5,4"/>
  <circle cx="210" cy="102" r="6" fill="#f8fafc" stroke="#38bdf8" stroke-width="1.5"/>
  <line x1="165" y1="92" x2="270" y2="120" stroke="#22c55e" stroke-width="3"/>
  <polygon points="270,120 258,112 261,124" fill="#22c55e"/>
  <rect x="140" y="52" width="185" height="38" rx="6" fill="rgba(15, 23, 42, 0.92)" stroke="#22c55e" stroke-width="1.5"/>
  <text x="150" y="68" fill="#22c55e" font-size="11" font-weight="bold">⚡ Smash Speed = Derivative</text>
  <text x="150" y="83" fill="#f8fafc" font-size="10" font-weight="600">v(t) = s'(t) [Instant Shuttle Velocity]</text>
</svg>`;
        } else if (isCar) {
            cleanSvg = `<svg viewBox="0 0 450 250" width="100%" xmlns="http://www.w3.org/2000/svg" class="math-svg-diagram">
  <defs>
    <linearGradient id="skyGradCar" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#030712"/>
      <stop offset="100%" stop-color="#111827"/>
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#skyGradCar)" rx="12"/>
  <rect x="0" y="180" width="450" height="70" fill="#1f2937"/>
  <line x1="0" y1="180" x2="450" y2="180" stroke="#f59e0b" stroke-width="2"/>
  <line x1="0" y1="215" x2="450" y2="215" stroke="#ffffff" stroke-width="2.5" stroke-dasharray="25,20"/>
  <path d="M 60 178 L 85 160 L 140 160 L 170 178 L 180 190 L 50 190 Z" fill="#ef4444"/>
  <circle cx="75" cy="192" r="11" fill="#0f172a" stroke="#94a3b8" stroke-width="3"/>
  <circle cx="155" cy="192" r="11" fill="#0f172a" stroke="#94a3b8" stroke-width="3"/>
  <rect x="65" y="132" width="95" height="18" rx="4" fill="rgba(15, 23, 42, 0.9)" stroke="#ef4444" stroke-width="1"/>
  <text x="112" y="145" fill="#f87171" font-size="10" font-weight="bold" text-anchor="middle">🏎️ Racing Car s(t)</text>
  <circle cx="340" cy="100" r="50" fill="#0f172a" stroke="#38bdf8" stroke-width="3"/>
  <path d="M 305 115 A 40 40 0 1 1 375 115" fill="none" stroke="#334155" stroke-width="6"/>
  <path d="M 305 115 A 40 40 0 0 1 350 63" fill="none" stroke="#22c55e" stroke-width="6"/>
  <line x1="340" y1="100" x2="355" y2="70" stroke="#ef4444" stroke-width="3.5" stroke-linecap="round"/>
  <circle cx="340" cy="100" r="5" fill="#ffffff"/>
  <text x="340" y="125" fill="#f8fafc" font-size="12" font-weight="bold" text-anchor="middle">140 km/h</text>
  <rect x="260" y="155" width="160" height="20" rx="4" fill="rgba(15, 23, 42, 0.9)" stroke="#22c55e" stroke-width="1"/>
  <text x="340" y="169" fill="#22c55e" font-size="10" font-weight="bold" text-anchor="middle">⚡ Speedometer = v(t) = ds/dt</text>
</svg>`;
        } else if (isCricket) {
            if (isCalculus) {
                cleanSvg = `<svg viewBox="0 0 450 250" width="100%" xmlns="http://www.w3.org/2000/svg" class="math-svg-diagram">
  <defs>
    <linearGradient id="skyGradC" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#0b1120"/>
      <stop offset="60%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
    <linearGradient id="pitchGradC" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#854d0e"/>
      <stop offset="50%" stop-color="#a16207"/>
      <stop offset="100%" stop-color="#78350f"/>
    </linearGradient>
    <linearGradient id="batGradC" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#f59e0b"/>
      <stop offset="50%" stop-color="#d97706"/>
      <stop offset="100%" stop-color="#b45309"/>
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#skyGradC)" rx="12"/>
  <circle cx="50" cy="15" r="45" fill="rgba(56, 189, 248, 0.08)" />
  <circle cx="400" cy="15" r="45" fill="rgba(56, 189, 248, 0.08)" />
  <rect x="0" y="195" width="450" height="55" fill="#064e3b"/>
  <line x1="0" y1="195" x2="450" y2="195" stroke="#10b981" stroke-width="2.5"/>
  <rect x="15" y="195" width="135" height="18" fill="url(#pitchGradC)" rx="3" opacity="0.9"/>
  <line x1="82" y1="195" x2="82" y2="213" stroke="#ffffff" stroke-width="2"/>
  <line x1="32" y1="162" x2="32" y2="197" stroke="#d97706" stroke-width="2.5"/>
  <line x1="37" y1="162" x2="37" y2="197" stroke="#d97706" stroke-width="2.5"/>
  <line x1="42" y1="162" x2="42" y2="197" stroke="#d97706" stroke-width="2.5"/>
  <line x1="30" y1="162" x2="44" y2="162" stroke="#fef08a" stroke-width="2.5"/>
  <path d="M 64 165 Q 60 180 58 197" stroke="#f8fafc" stroke-width="7.5" stroke-linecap="round" fill="none"/>
  <circle cx="58" cy="197" r="3.5" fill="#334155"/>
  <path d="M 72 165 Q 82 180 90 197" stroke="#f8fafc" stroke-width="7.5" stroke-linecap="round" fill="none"/>
  <circle cx="90" cy="197" r="3.5" fill="#334155"/>
  <path d="M 62 138 L 76 141 L 73 166 L 60 164 Z" fill="#2563eb"/>
  <path d="M 67 138 L 72 139 L 70 144 Z" fill="#fbbf24"/>
  <circle cx="69" cy="127" r="9.5" fill="#1e3a8a"/>
  <path d="M 72 128 L 81 130 L 76 135 Z" fill="#94a3b8"/>
  <path d="M 65 142 L 77 146 L 88 138" stroke="#fde047" stroke-width="3.5" stroke-linecap="round" fill="none"/>
  <line x1="84" y1="142" x2="92" y2="134" stroke="#ef4444" stroke-width="3.5" stroke-linecap="round"/>
  <polygon points="92,134 96,130 122,96 116,92" fill="url(#batGradC)" stroke="#78350f" stroke-width="1.2"/>
  <line x1="100" y1="120" x2="111" y2="106" stroke="#ef4444" stroke-width="2"/>
  <rect x="36" y="94" width="64" height="18" rx="4" fill="rgba(15, 23, 42, 0.9)" stroke="#38bdf8" stroke-width="1"/>
  <text x="68" y="107" fill="#38bdf8" font-size="10" font-weight="bold" text-anchor="middle">🏏 Batsman</text>
  <path d="M 118 94 Q 220 18 390 195" fill="none" stroke="#38bdf8" stroke-width="2.5" stroke-dasharray="6,4" opacity="0.85"/>
  <text x="215" y="36" fill="#38bdf8" font-size="11.5" font-weight="bold">Flight Trajectory s(t)</text>
  <circle cx="205" cy="54" r="7" fill="#ef4444" stroke="#ffffff" stroke-width="1.5"/>
  <path d="M 201 51 Q 205 54 209 57" stroke="#ffffff" stroke-width="1" fill="none"/>
  <line x1="145" y1="42" x2="265" y2="66" stroke="#22c55e" stroke-width="3"/>
  <polygon points="265,66 253,59 256,71" fill="#22c55e"/>
  <rect x="135" y="78" width="188" height="42" rx="6" fill="rgba(15, 23, 42, 0.92)" stroke="#22c55e" stroke-width="1.5"/>
  <text x="145" y="95" fill="#22c55e" font-size="11" font-weight="bold">⚡ Tangent Slope = Derivative</text>
  <text x="145" y="112" fill="#f8fafc" font-size="10.5" font-weight="600">v(t) = s'(t) = lim (Δs / Δt) [Speed]</text>
  <rect x="365" y="174" width="72" height="22" rx="5" fill="#1e293b" stroke="#f59e0b" stroke-width="1.5"/>
  <text x="401" y="189" fill="#f59e0b" font-size="11" font-weight="bold" text-anchor="middle">6️⃣ Boundary</text>
</svg>`;
            } else {
                cleanSvg = `<svg viewBox="0 0 450 250" width="100%" xmlns="http://www.w3.org/2000/svg" class="math-svg-diagram">
  <defs>
    <linearGradient id="skyGradT" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#0b1120"/>
      <stop offset="60%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
    <linearGradient id="pitchGradT" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#854d0e"/>
      <stop offset="50%" stop-color="#a16207"/>
      <stop offset="100%" stop-color="#78350f"/>
    </linearGradient>
    <linearGradient id="batGradT" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#f59e0b"/>
      <stop offset="50%" stop-color="#d97706"/>
      <stop offset="100%" stop-color="#b45309"/>
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#skyGradT)" rx="12"/>
  <circle cx="50" cy="15" r="45" fill="rgba(56, 189, 248, 0.08)" />
  <circle cx="400" cy="15" r="45" fill="rgba(56, 189, 248, 0.08)" />
  <rect x="0" y="195" width="450" height="55" fill="#064e3b"/>
  <line x1="0" y1="195" x2="450" y2="195" stroke="#10b981" stroke-width="2.5"/>
  <rect x="15" y="195" width="135" height="18" fill="url(#pitchGradT)" rx="3" opacity="0.9"/>
  <line x1="82" y1="195" x2="82" y2="213" stroke="#ffffff" stroke-width="2"/>
  <line x1="32" y1="162" x2="32" y2="197" stroke="#d97706" stroke-width="2.5"/>
  <line x1="37" y1="162" x2="37" y2="197" stroke="#d97706" stroke-width="2.5"/>
  <line x1="42" y1="162" x2="42" y2="197" stroke="#d97706" stroke-width="2.5"/>
  <line x1="30" y1="162" x2="44" y2="162" stroke="#fef08a" stroke-width="2.5"/>
  <path d="M 64 165 Q 60 180 58 197" stroke="#f8fafc" stroke-width="7.5" stroke-linecap="round" fill="none"/>
  <circle cx="58" cy="197" r="3.5" fill="#334155"/>
  <path d="M 72 165 Q 82 180 90 197" stroke="#f8fafc" stroke-width="7.5" stroke-linecap="round" fill="none"/>
  <circle cx="90" cy="197" r="3.5" fill="#334155"/>
  <path d="M 62 138 L 76 141 L 73 166 L 60 164 Z" fill="#2563eb"/>
  <path d="M 67 138 L 72 139 L 70 144 Z" fill="#fbbf24"/>
  <circle cx="69" cy="127" r="9.5" fill="#1e3a8a"/>
  <path d="M 72 128 L 81 130 L 76 135 Z" fill="#94a3b8"/>
  <path d="M 65 142 L 77 146 L 88 138" stroke="#fde047" stroke-width="3.5" stroke-linecap="round" fill="none"/>
  <line x1="84" y1="142" x2="92" y2="134" stroke="#ef4444" stroke-width="3.5" stroke-linecap="round"/>
  <polygon points="92,134 96,130 122,96 116,92" fill="url(#batGradT)" stroke="#78350f" stroke-width="1.2"/>
  <line x1="100" y1="120" x2="111" y2="106" stroke="#ef4444" stroke-width="2"/>
  <rect x="36" y="94" width="64" height="18" rx="4" fill="rgba(15, 23, 42, 0.9)" stroke="#38bdf8" stroke-width="1"/>
  <text x="68" y="107" fill="#38bdf8" font-size="10" font-weight="bold" text-anchor="middle">🏏 Batsman</text>
  <circle cx="320" cy="50" r="7" fill="#ef4444" stroke="#ffffff" stroke-width="1.5"/>
  <path d="M 316 47 Q 320 50 324 53" stroke="#ffffff" stroke-width="1" fill="none"/>
  <text x="320" y="36" fill="#f87171" font-size="11" font-weight="bold" text-anchor="middle">⚾ Ball at Peak (C)</text>
  <line x1="90" y1="195" x2="320" y2="50" stroke="#fbbf24" stroke-width="3"/>
  <text x="180" y="112" fill="#fbbf24" font-size="11.5" font-weight="bold" transform="rotate(-32, 180, 112)">Flight Path (h)</text>
  <line x1="90" y1="195" x2="320" y2="195" stroke="#38bdf8" stroke-width="2.5"/>
  <text x="205" y="214" fill="#38bdf8" font-size="11.5" font-weight="bold" text-anchor="middle">Ground Distance (b)</text>
  <line x1="320" y1="195" x2="320" y2="50" stroke="#f43f5e" stroke-width="2.5" stroke-dasharray="5,4"/>
  <text x="332" y="125" fill="#f43f5e" font-size="11.5" font-weight="bold">Height (p)</text>
  <path d="M 305 195 L 305 180 L 320 180" fill="none" stroke="#f43f5e" stroke-width="2"/>
  <path d="M 120 195 A 30 30 0 0 0 115 178" fill="none" stroke="#38bdf8" stroke-width="2.5"/>
  <text x="128" y="186" fill="#38bdf8" font-size="13" font-weight="bold">θ</text>
  <rect x="350" y="174" width="85" height="22" rx="5" fill="#1e293b" stroke="#10b981" stroke-width="1.5"/>
  <text x="392" y="189" fill="#10b981" font-size="11" font-weight="bold" text-anchor="middle">6️⃣ Boundary (B)</text>
</svg>`;
            }
        } else if (/Perpendicular/i.test(cleanSvg) && /Hypotenuse/i.test(cleanSvg)) {

            const isStandardConceptual = /Base\s*\([bB]\)/i.test(cleanSvg) && /Perpendicular\s*\([pP]\)/i.test(cleanSvg);

            if (isStandardConceptual) {

                cleanSvg = `<svg viewBox="0 0 340 210" width="100%" xmlns="http://www.w3.org/2000/svg">

  <rect width="100%" height="100%" fill="#0f172a" rx="10"/>

  <polygon points="50,160 240,160 240,40" fill="rgba(56, 189, 248, 0.08)" stroke="#38bdf8" stroke-width="2.5" stroke-linejoin="round"/>

  <path d="M 225,160 L 225,145 L 240,145" fill="none" stroke="#f43f5e" stroke-width="2"/>

  <path d="M 76,160 A 26 26 0 0 0 72,143" fill="none" stroke="#fbbf24" stroke-width="2"/>

  <text x="82" y="154" fill="#fbbf24" font-size="13" font-weight="bold">θ</text>

  <text x="32" y="165" fill="#94a3b8" font-size="13" font-weight="bold">A</text>

  <text x="248" y="172" fill="#94a3b8" font-size="13" font-weight="bold">B (90°)</text>

  <text x="240" y="28" fill="#94a3b8" font-size="13" font-weight="bold" text-anchor="middle">C</text>

  <text x="145" y="185" fill="#38bdf8" font-size="13" font-weight="600" text-anchor="middle">Base (b)</text>

  <text x="252" y="105" fill="#38bdf8" font-size="13" font-weight="600">Perpendicular (p)</text>

  <text x="125" y="90" fill="#a78bfa" font-size="13" font-weight="600" transform="rotate(-32, 125, 90)">Hypotenuse (h)</text>

</svg>`;

            }

        }



        if (!cleanSvg.includes('width=')) {

            cleanSvg = cleanSvg.replace('<svg', '<svg width="100%"');

        }

        const wrapper = `<div class="math-svg-container" title="Mathematical Diagram">${cleanSvg}</div>`;

        html = html.replace(`__SVG_DIAGRAM_${idx}__`, () => wrapper);

    });



    // 13. Restore untouched LaTeX math blocks (use function to prevent $$ and $' pattern substitution)

    mathBlocks.forEach((mathStr, idx) => {

        html = html.replace(`___MATH_BLOCK_${idx}___`, () => mathStr);

    });



    return html;

}



// ==========================================================

// 🔊 AI VOICE READ-ALOUD (TTS with Natural Indian Voice & Math)

// ==========================================================

let cachedVoices = [];



function populateVoices() {

    if (!('speechSynthesis' in window)) return;

    cachedVoices = window.speechSynthesis.getVoices();

}



if ('speechSynthesis' in window) {

    populateVoices();

    if (window.speechSynthesis.onvoiceschanged !== undefined) {

        window.speechSynthesis.onvoiceschanged = populateVoices;

    }

}



function getBestIndianVoice() {

    if (!cachedVoices.length && ('speechSynthesis' in window)) {

        cachedVoices = window.speechSynthesis.getVoices();

    }

    if (!cachedVoices.length) return null;



    let voice = cachedVoices.find(v => (v.lang === 'en-IN' || v.lang === 'en_IN') && (v.name.includes('India') || v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('Heera') || v.name.includes('Neerja') || v.name.includes('Ravi')));

    if (!voice) voice = cachedVoices.find(v => v.lang === 'en-IN' || v.lang === 'en_IN');

    if (!voice) voice = cachedVoices.find(v => v.lang === 'hi-IN' || v.lang === 'hi_IN');

    if (!voice) voice = cachedVoices.find(v => (v.name.includes('Google') || v.name.includes('Natural')) && v.lang.startsWith('en'));

    if (!voice) voice = cachedVoices.find(v => v.lang.startsWith('en'));

    return voice || cachedVoices[0];

}



function speakableFormula(f) {

    if (!f) return '';

    let s = f.trim();



    // LaTeX formatting artifacts

    s = s.replace(/\\text\{([^}]+)\}/g, '$1');

    s = s.replace(/\\mathbf\{([^}]+)\}/g, '$1');

    s = s.replace(/\\mathrm\{([^}]+)\}/g, '$1');

    s = s.replace(/\\left|\\right/g, '');



    // 1. Function notation in math: f(x), g(x), s(t), v(t), etc. -> "f of x", "s of t"

    s = s.replace(/\b([a-zA-Z])\s*'+(\s*\(\s*([^)]+)\s*\))/g, '$1 dash of $3');

    s = s.replace(/\b([a-zA-Z])\s*\(\s*([^)]+)\s*\)/g, '$1 of $2');



    // 2. Specific derivatives: \frac{ds}{dt} -> "d s upon d t", \frac{dy}{dx} -> "d y upon d x"

    s = s.replace(/\\frac\{d([a-zA-Z])\}\{d([a-zA-Z])\}/g, ' d $1 upon d $2 ');

    s = s.replace(/\\frac\{d\}\{d([a-zA-Z])\}/g, ' derivative with respect to $1 ');

    s = s.replace(/\bd([a-zA-Z])\/d([a-zA-Z])\b/g, ' d $1 upon d $2 ');



    // 3. Units inside formula: m/s -> meters per second, s -> seconds

    s = s.replace(/\b(\d+)\s*(?:m\/s|meters\/second)\b/gi, '$1 meters per second');

    s = s.replace(/\b(\d+)\s*(?:km\/h|kmph)\b/gi, '$1 kilometers per hour');

    s = s.replace(/\b(\d+)\s*cm\b/gi, '$1 centimeters');

    s = s.replace(/\b(\d+)\s*m\b/gi, '$1 meters');

    s = s.replace(/\b(\d+)\s*s\b/gi, '$1 seconds');



    // 4. Fractions: \frac{a}{b} -> "a upon b"

    s = s.replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, ' $1 upon $2 ');



    // 5. Roots & Powers

    s = s.replace(/\\sqrt\[([^\]]+)\]\{([^}]+)\}/g, ' $1th root of $2 ');

    s = s.replace(/\\sqrt\{([^}]+)\}/g, ' square root of $1 ');

    s = s.replace(/\^2/g, ' square ');

    s = s.replace(/\^3/g, ' cube ');

    s = s.replace(/\^\{?([0-9a-zA-Z]+)\}?/g, ' to the power $1 ');



    // 6. Trigonometric powers & ratios

    s = s.replace(/\\sin\^2|\bsin\^2/g, ' sine square ');

    s = s.replace(/\\cos\^2|\bcos\^2/g, ' cos square ');

    s = s.replace(/\\tan\^2|\btan\^2/g, ' tan square ');

    s = s.replace(/\\sec\^2|\bsec\^2/g, ' sec square ');

    s = s.replace(/\\csc\^2|\bcosec\^2/g, ' cosec square ');

    s = s.replace(/\\cot\^2|\bcot\^2/g, ' cot square ');



    s = s.replace(/\\sin\b|\bsin\b/g, ' sine ');

    s = s.replace(/\\cos\b|\bcos\b/g, ' cos ');

    s = s.replace(/\\tan\b|\btan\b/g, ' tan ');

    s = s.replace(/\\sec\b|\bsec\b/g, ' sec ');

    s = s.replace(/\\csc\b|\bcosec\b/g, ' cosec ');

    s = s.replace(/\\cot\b|\bcot\b/g, ' cot ');



    // 7. Greek letters & symbols

    s = s.replace(/\\theta|\btheta\b/gi, ' theeta ');

    s = s.replace(/\\pi|\bpi\b/gi, ' pie ');

    s = s.replace(/\\alpha|\balpha\b/gi, ' alpha ');

    s = s.replace(/\\beta|\bbeta\b/gi, ' beeta ');

    s = s.replace(/\\gamma|\bgamma\b/gi, ' gamma ');

    s = s.replace(/\\Delta|\\delta/g, ' delta ');

    s = s.replace(/\^\\circ|\^circ|\\circ/g, ' degrees ');



    s = s.replace(/\\approx/g, ' approximately equal to ');

    s = s.replace(/\\neq|!=/g, ' is not equal to ');

    s = s.replace(/\\le|<=/g, ' is less than or equal to ');

    s = s.replace(/\\ge|>=/g, ' is greater than or equal to ');

    s = s.replace(/\\pm|\+-/g, ' plus or minus ');

    s = s.replace(/\\times|\*/g, ' multiplied by ');

    s = s.replace(/\\div|\//g, ' divided by ');

    s = s.replace(/=/g, ' equals ');

    s = s.replace(/\+/g, ' plus ');

    s = s.replace(/-/g, ' minus ');



    // 8. Eliminate all brackets and braces so TTS never literally speaks "bracket" or "curly bracket"

    s = s.replace(/[{}\[\]\(\)]/g, ' ');



    return ' ' + s + ' ';

}



function cleanMathTextForSpeech(text, persona) {

    if (!text) return '';

    let str = text;



    // Remove emojis

    str = str.replace(/[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{1F100}-\u{1F1FF}\u{1F600}-\u{1F64F}\u{1F680}-\u{1F6FF}]/gu, '');

    

    // HTML line breaks to sentence pause

    str = str.replace(/<br\s*\/?>/gi, '. ');

    str = str.replace(/<\/p>/gi, '. ');

    str = str.replace(/<\/li>/gi, '. ');

    str = str.replace(/<[^>]+>/g, ' ');



    // Markdown cleanup

    str = str.replace(/```[\s\S]*?```/g, '');

    str = str.replace(/###|##|#/g, '');

    str = str.replace(/\*\*/g, '').replace(/\*/g, '');



    // Step labels

    str = str.replace(/Intuition\s*:/gi, 'Step 1 . Intuition . ');

    str = str.replace(/Analogy\s*:/gi, 'Step 2 . Analogy . ');

    str = str.replace(/Math Steps\s*:/gi, 'Step 3 . Math steps . ');

    str = str.replace(/Example\s*:/gi, 'Step 4 . Example . ');

    str = str.replace(/Final Answer\s*:/gi, 'Final Answer . ');

    str = str.replace(/Interactive Practice\s*:/gi, 'Practice Question . ');



    // 1. Process LaTeX delimited blocks ($$...$$, $...$, \[...\], \(...\)) first

    str = str.replace(/\$\$(.*?)\$\$/g, (m, f) => speakableFormula(f));

    str = str.replace(/\$(.*?)\$/g, (m, f) => speakableFormula(f));

    str = str.replace(/\\\[(.*?)\\\]/g, (m, f) => speakableFormula(f));

    str = str.replace(/\\\((.*?)\\\)/g, (m, f) => speakableFormula(f));



    // 2. Bare LaTeX artifacts in prose (e.g. \text{ s}, \frac{ds}{dt})

    str = str.replace(/\\text\{([^}]+)\}/g, ' $1 ');

    str = str.replace(/\\mathbf\{([^}]+)\}/g, ' $1 ');

    str = str.replace(/\\mathrm\{([^}]+)\}/g, ' $1 ');

    str = str.replace(/\\left|\\right/g, '');



    // 3. Derivatives in prose (e.g. \frac{ds}{dt}, \frac{dy}{dx}, ds/dt)

    str = str.replace(/\\frac\{d([a-zA-Z])\}\{d([a-zA-Z])\}/g, ' d $1 upon d $2 ');

    str = str.replace(/\\frac\{d\}\{d([a-zA-Z])\}/g, ' derivative with respect to $1 ');

    str = str.replace(/\bd([a-zA-Z])\/d([a-zA-Z])\b/g, ' d $1 upon d $2 ');

    str = str.replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, ' $1 upon $2 ');



    // 4. Function notation in prose: f(x), s(t), v(t), f'(x) -> "f of x", "s of t"

    str = str.replace(/\b([a-zA-Z])\s*'+(\s*\(\s*([^)]+)\s*\))/g, '$1 dash of $3');

    str = str.replace(/\b([a-zA-Z])\s*\(\s*([^)]+)\s*\)/g, '$1 of $2');



    // 5. Units in prose: 3 s -> 3 seconds, 6 m/s -> 6 meters per second

    str = str.replace(/\b(\d+)\s*(?:m\/s|meters\/second)\b/gi, '$1 meters per second');

    str = str.replace(/\b(\d+)\s*(?:km\/h|kmph)\b/gi, '$1 kilometers per hour');

    str = str.replace(/\b(\d+)\s*cm\b/gi, '$1 centimeters');

    str = str.replace(/\b(\d+)\s*m\b/gi, '$1 meters');

    str = str.replace(/\b(\d+)\s*s\b/gi, '$1 seconds');



    // 6. Calculus & math terms in prose

    str = str.replace(/\\sum\b|\bSUM\b|\bsum\b/g, ' summation ');

    str = str.replace(/\\int\b|\bINT\b|\bint\b/g, ' integration ');

    str = str.replace(/\\lim\b|\bLIM\b|\blim\b/g, ' limit ');

    str = str.replace(/\bdy\/dx\b|\bd\/dx\b/g, ' derivative with respect to x ');



    // 7. Powers & equals in prose

    str = str.replace(/\^2/g, ' square ');

    str = str.replace(/\^3/g, ' cube ');

    str = str.replace(/\^\{?([0-9a-zA-Z]+)\}?/g, ' to the power $1 ');

    str = str.replace(/=/g, ' equals ');

    str = str.replace(/\+/g, ' plus ');

    str = str.replace(/-/g, ' minus ');



    // 8. If active persona is a Hindi neural voice (Swara / Madhur), polish tricky English terms

    const isHindiVoice = persona && persona.neuralVoice && persona.neuralVoice.startsWith('hi-IN');

    if (isHindiVoice) {

        str = str.replace(/\btrigonometry\b/gi, 'ट्रिगोनोमेट्री');

        str = str.replace(/\btrigonometric\b/gi, 'ट्रिगोनोमेट्रिक');

        str = str.replace(/\bderivative\b/gi, 'डेरिवेटिव');

        str = str.replace(/\bderivatives\b/gi, 'डेरिवेटिव्स');

        str = str.replace(/\bfunction\b/gi, 'फ़ंक्शन');

        str = str.replace(/\bcalculus\b/gi, 'कैलकुलस');

        str = str.replace(/\bvelocity\b/gi, 'वेलोसिटी');

        str = str.replace(/\binstantaneous\b/gi, 'इंस्टेंटेनियस');

        str = str.replace(/\bdistance\b/gi, 'डिस्टेंस');

        str = str.replace(/\bformula\b/gi, 'फॉर्मूला');

        str = str.replace(/\bformulas\b/gi, 'फॉर्मूले');

        str = str.replace(/\bratios\b/gi, 'रेश्यो');

        str = str.replace(/\bratio\b/gi, 'रेश्यो');

        str = str.replace(/\bupon\b/gi, 'अपॉन');

        str = str.replace(/\bequals\b/gi, 'इक्वल्स');

        str = str.replace(/\bsquare\b/gi, 'स्क्वायर');

        str = str.replace(/\bcube\b/gi, 'क्यूब');

        str = str.replace(/\bseconds\b/gi, 'सेकंड्स');

        str = str.replace(/\bmeters per second\b/gi, 'मीटर पर सेकंड');

        str = str.replace(/\bof\b/gi, 'ऑफ़');

    }



    // 9. CRITICAL: Remove all brackets, braces, and parens so TTS NEVER says "bracket" or "curly bracket"

    str = str.replace(/[{}\[\]\(\)]/g, ' ');

    str = str.replace(/[_~|\\\\]/g, ' ');



    str = str.replace(/,\s*,+/g, ',');

    str = str.replace(/\.\s*\.+/g, '.');

    str = str.replace(/;+/g, ',');

    str = str.replace(/\s+/g, ' ').trim();



    return str;

}



// ==========================================================

// 5 ULTRA-REALISTIC NEURAL AI TEACHER PERSONAS

// ==========================================================

const CHATGPT_VOICE_PERSONAS = [

    {

        id: 'arjun',

        name: 'Arjun',

        vibe: 'Savvy, relaxed & articulate',

        role: 'Senior Math Mentor',

        neuralVoice: 'en-IN-PrabhatNeural',

        browserVoiceLang: 'en-IN',

        gradient: 'radial-gradient(circle at 35% 28%, #e0e7ff 0%, #a5b4fc 25%, #6366f1 52%, #3b82f6 78%, #1e1b4b 100%)',

        glow: 'rgba(99, 102, 241, 0.55)',

        sample: 'Namaste! Main Arjun hoon. Savvy and relaxed — trigonometry aur maths ke tricky questions ko full clarity ke sath solve karenge.'

    },

    {

        id: 'priya',

        name: 'Priya',

        vibe: 'Warm, expressive & encouraging',

        role: 'Class Teacher (Hinglish & English)',

        neuralVoice: 'en-IN-NeerjaExpressiveNeural',

        browserVoiceLang: 'en-IN',

        gradient: 'radial-gradient(circle at 35% 28%, #fce7f3 0%, #f472b6 25%, #ec4899 52%, #8b5cf6 78%, #4c1d95 100%)',

        glow: 'rgba(236, 72, 153, 0.55)',

        sample: 'Namaste! Main Priya hoon. Har formula aur concept aaraam se samjhenge, bina kisi pressure ke. Aap kabhi bhi koi bhi doubt pooch sakte hain.'

    },

    {

        id: 'swara',

        name: 'Swara',

        vibe: 'Sweet, natural & fluent Hindi',

        role: 'Hindi Medium Expert',

        neuralVoice: 'hi-IN-SwaraNeural',

        browserVoiceLang: 'hi-IN',

        gradient: 'radial-gradient(circle at 35% 28%, #fef3c7 0%, #f59e0b 25%, #d97706 52%, #b45309 78%, #78350f 100%)',

        glow: 'rgba(245, 158, 11, 0.55)',

        sample: 'नमस्ते! मैं स्वरा हूँ। गणित और त्रिकोणमिति के कठिन सवालों को एकदम सरल और स्पष्ट तरीक़े से समझेंगे।'

    },

    {

        id: 'madhur',

        name: 'Madhur',

        vibe: 'Deep, patient & structured',

        role: 'Concept Specialist',

        neuralVoice: 'hi-IN-MadhurNeural',

        browserVoiceLang: 'hi-IN',

        gradient: 'radial-gradient(circle at 35% 28%, #e0f2fe 0%, #38bdf8 25%, #0284c7 52%, #2563eb 78%, #0f172a 100%)',

        glow: 'rgba(2, 132, 199, 0.55)',

        sample: 'नमस्ते! मैं मधुर हूँ। थ्योरम, फॉर्मूला और स्टेप्स को गहराई से और लॉजिक के साथ सीखेंगे।'

    },

    {

        id: 'kavya',

        name: 'Kavya',

        vibe: 'Energetic, crisp & confident',

        role: 'Board Exam Speed Tutor',

        neuralVoice: 'en-IN-NeerjaNeural',

        browserVoiceLang: 'en-IN',

        gradient: 'radial-gradient(circle at 35% 28%, #ffedd5 0%, #fb923c 25%, #ea580c 52%, #c026d3 78%, #431407 100%)',

        glow: 'rgba(234, 88, 12, 0.55)',

        sample: 'Hey there! Main Kavya hoon. High energy ke sath board exam formulas, tricky derivations aur speed tricks master karenge!'

    }

];



let activePersonaIndex = parseInt(localStorage.getItem('selectedVoicePersonaIndex') || '0', 10);

if (isNaN(activePersonaIndex) || activePersonaIndex < 0 || activePersonaIndex >= CHATGPT_VOICE_PERSONAS.length) {

    activePersonaIndex = 0;

}



// Global active audio state (Neural audio + Browser fallback)

let activeTtsAudio = null;

let activeTtsBtn = null;

let isSpeakingActive = false;

let isSampleAudioPlaying = false;

window.currentUtteranceRef = null;



function stopCurrentSpeech() {

    isSpeakingActive = false;

    isSampleAudioPlaying = false;



    if (activeTtsAudio) {

        activeTtsAudio.pause();

        activeTtsAudio.currentTime = 0;

        activeTtsAudio = null;

    }

    if ('speechSynthesis' in window) {

        window.speechSynthesis.cancel();

    }

    if (activeTtsBtn) {

        activeTtsBtn.classList.remove('tts-btn-active');

        activeTtsBtn.innerHTML = '🔊 <span>Listen</span>';

        activeTtsBtn = null;

    }

    const orbTrigger = document.getElementById('voice-orb-trigger');

    if (orbTrigger) orbTrigger.classList.remove('speaking');

    const sampleIcon = document.getElementById('voice-sample-icon');

    if (sampleIcon) sampleIcon.textContent = '▶';

    const sampleText = document.getElementById('voice-sample-text');

    if (sampleText) sampleText.textContent = 'Sample voice';

}



// Play Ultra-Lifelike Neural Audio via backend /api/tts

async function playNeuralOrBrowserSpeech(cleanText, persona, onStart, onEnd, onError) {

    stopCurrentSpeech();



    const speedVal = localStorage.getItem('voiceSpeed') || '0.85';

    let edgeRate = '+0%';

    const speedFloat = parseFloat(speedVal);

    if (speedFloat <= 0.80) edgeRate = '-12%';

    else if (speedFloat >= 1.0) edgeRate = '+12%';



    try {

        if (onStart) onStart();

        const res = await fetch(`${API_BASE_URL}/api/tts`, {

            method: 'POST',

            headers: { 'Content-Type': 'application/json' },

            body: JSON.stringify({

                text: cleanText,

                voice: persona.neuralVoice || 'en-IN-NeerjaExpressiveNeural',

                rate: edgeRate

            })

        });



        if (!res.ok) {

            throw new Error(`TTS server responded with ${res.status}`);

        }



        const blob = await res.blob();

        const audioUrl = URL.createObjectURL(blob);

        const audio = new Audio(audioUrl);

        activeTtsAudio = audio;



        audio.onended = () => {

            activeTtsAudio = null;

            URL.revokeObjectURL(audioUrl);

            if (onEnd) onEnd();

        };



        audio.onerror = (e) => {

            console.warn('Neural audio playback error, falling back to browser speech:', e);

            activeTtsAudio = null;

            URL.revokeObjectURL(audioUrl);

            fallbackBrowserSpeech(cleanText, persona, onStart, onEnd, onError);

        };



        await audio.play();

    } catch (err) {

        console.warn('Neural TTS API notice, using fallback:', err);

        fallbackBrowserSpeech(cleanText, persona, onStart, onEnd, onError);

    }

}



function fallbackBrowserSpeech(cleanText, persona, onStart, onEnd, onError) {

    if (!('speechSynthesis' in window)) {

        if (onError) onError();

        return;

    }

    window.speechSynthesis.cancel();

    if (onStart) onStart();



    const utterance = new SpeechSynthesisUtterance(cleanText);

    utterance.rate = parseFloat(localStorage.getItem('voiceSpeed') || '0.85');

    utterance.pitch = 1.0;

    const voice = getBestIndianVoice();

    if (voice) utterance.voice = voice;



    window.currentUtteranceRef = utterance;

    utterance.onend = () => {

        window.currentUtteranceRef = null;

        if (onEnd) onEnd();

    };

    utterance.onerror = (e) => {

        console.warn('Browser TTS error:', e);

        window.currentUtteranceRef = null;

        if (onError) onError();

    };



    if (window.speechSynthesis.paused) window.speechSynthesis.resume();

    window.speechSynthesis.speak(utterance);

}



// 🔊 Listen button on chat messages

function toggleSpeech(rawText, btnElement) {

    if (activeTtsBtn === btnElement && isSpeakingActive) {

        stopCurrentSpeech();

        return;

    }



    const persona = CHATGPT_VOICE_PERSONAS[activePersonaIndex] || CHATGPT_VOICE_PERSONAS[0];

    const cleanText = cleanMathTextForSpeech(rawText, persona);

    if (!cleanText) return;



    playNeuralOrBrowserSpeech(

        cleanText,

        persona,

        // onStart

        () => {

            isSpeakingActive = true;

            activeTtsBtn = btnElement;

            btnElement.classList.add('tts-btn-active');

            btnElement.innerHTML = '⏹️ <span>Stop</span>';

        },

        // onEnd

        () => {

            stopCurrentSpeech();

        },

        // onError

        () => {

            stopCurrentSpeech();

        }

    );

}



// 🔮 Orb / Sample button click

function sampleActivePersona() {

    const persona = CHATGPT_VOICE_PERSONAS[activePersonaIndex] || CHATGPT_VOICE_PERSONAS[0];

    const orbTrigger = document.getElementById('voice-orb-trigger');

    const sampleIcon = document.getElementById('voice-sample-icon');

    const sampleText = document.getElementById('voice-sample-text');



    if (isSampleAudioPlaying) {

        stopCurrentSpeech();

        return;

    }



    playNeuralOrBrowserSpeech(

        persona.sample,

        persona,

        // onStart

        () => {

            isSampleAudioPlaying = true;

            if (orbTrigger) orbTrigger.classList.add('speaking');

            if (sampleIcon) sampleIcon.textContent = '⏹️';

            if (sampleText) sampleText.textContent = 'Stop sample';

        },

        // onEnd

        () => {

            isSampleAudioPlaying = false;

            if (orbTrigger) orbTrigger.classList.remove('speaking');

            if (sampleIcon) sampleIcon.textContent = '▶';

            if (sampleText) sampleText.textContent = 'Sample voice';

        },

        // onError

        () => {

            isSampleAudioPlaying = false;

            if (orbTrigger) orbTrigger.classList.remove('speaking');

            if (sampleIcon) sampleIcon.textContent = '▶';

            if (sampleText) sampleText.textContent = 'Sample voice';

        }

    );

}



function updateVoicePersonaUI(playSampleAfterChange = false) {

    const persona = CHATGPT_VOICE_PERSONAS[activePersonaIndex] || CHATGPT_VOICE_PERSONAS[0];

    localStorage.setItem('selectedVoicePersonaIndex', activePersonaIndex.toString());

    localStorage.setItem('selectedVoicePersonaId', persona.id);



    const nameEl = document.getElementById('voice-persona-name');

    const vibeEl = document.getElementById('voice-persona-vibe');

    const orbEl = document.getElementById('voice-orb-celestial');

    const dotsContainer = document.getElementById('voice-carousel-dots');



    if (nameEl) nameEl.textContent = persona.name;

    if (vibeEl) vibeEl.textContent = `${persona.vibe} • ${persona.role}`;

    if (orbEl) {

        orbEl.style.background = persona.gradient;

        orbEl.style.boxShadow = `0 0 45px ${persona.glow}, inset 0 -12px 24px rgba(15, 23, 42, 0.45), inset 0 10px 18px rgba(255, 255, 255, 0.6)`;

    }



    if (dotsContainer) {

        dotsContainer.innerHTML = '';

        CHATGPT_VOICE_PERSONAS.forEach((p, idx) => {

            const dot = document.createElement('div');

            dot.className = 'voice-dot' + (idx === activePersonaIndex ? ' active' : '');

            dot.title = `${p.name} (${p.vibe})`;

            dot.onclick = () => {

                if (activePersonaIndex !== idx) {

                    activePersonaIndex = idx;

                    updateVoicePersonaUI(true);

                }

            };

            dotsContainer.appendChild(dot);

        });

    }



    if (playSampleAfterChange) {

        sampleActivePersona();

    }

}



function initChatGPTVoiceSettings() {

    updateVoicePersonaUI(false);



    const prevBtn = document.getElementById('voice-prev-arrow');

    const nextBtn = document.getElementById('voice-next-arrow');

    const orbTrigger = document.getElementById('voice-orb-trigger');

    const sampleBtn = document.getElementById('voice-sample-btn');



    if (prevBtn) {

        prevBtn.onclick = () => {

            activePersonaIndex = (activePersonaIndex - 1 + CHATGPT_VOICE_PERSONAS.length) % CHATGPT_VOICE_PERSONAS.length;

            updateVoicePersonaUI(true);

        };

    }



    if (nextBtn) {

        nextBtn.onclick = () => {

            activePersonaIndex = (activePersonaIndex + 1) % CHATGPT_VOICE_PERSONAS.length;

            updateVoicePersonaUI(true);

        };

    }



    if (orbTrigger) {

        orbTrigger.onclick = () => sampleActivePersona();

    }



    if (sampleBtn) {

        sampleBtn.onclick = () => sampleActivePersona();

    }



    const voiceSpeedSelect = document.getElementById('setting-voice-speed-select');

    if (voiceSpeedSelect) {

        const savedSpeed = localStorage.getItem('voiceSpeed') || '0.85';

        voiceSpeedSelect.value = savedSpeed;

        voiceSpeedSelect.onchange = () => {

            localStorage.setItem('voiceSpeed', voiceSpeedSelect.value);

        };

    }



    const autoReadToggle = document.getElementById('setting-auto-read-toggle');

    if (autoReadToggle) {

        const savedAuto = localStorage.getItem('voiceAutoRead') === 'true';

        autoReadToggle.checked = savedAuto;

        autoReadToggle.onchange = () => {

            localStorage.setItem('voiceAutoRead', autoReadToggle.checked ? 'true' : 'false');

        };

    }

}



if (document.readyState === 'loading') {

    document.addEventListener('DOMContentLoaded', initChatGPTVoiceSettings);

} else {

    initChatGPTVoiceSettings();

}







function exportChatToPDF() {

    const messages = document.querySelectorAll('#messages-container .message');

    if (!messages || messages.length === 0) {

        alert('No chat messages available to export as notes!');

        return;

    }



    const studentName = localStorage.getItem('studentName') || 'Student';

    const studentGrade = localStorage.getItem('studentGrade') || 'Class 11';

    const topicEl = document.getElementById('current-topic');

    const topicTitle = topicEl ? topicEl.innerText : 'NCERT Maths Notes';

    const dateStr = new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });



    const pdfWrapper = document.createElement('div');

    pdfWrapper.style.padding = '24px';

    pdfWrapper.style.fontFamily = "'Inter', Arial, sans-serif";

    pdfWrapper.style.background = '#ffffff';

    pdfWrapper.style.color = '#0f172a';



    let html = `

        <div style="border-bottom: 2px solid #6366f1; padding-bottom: 14px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">

            <div>

                <h1 style="font-size: 20px; color: #4f46e5; margin: 0;">🎓 AI Maths Tutor — Exam Revision Notes</h1>

                <p style="font-size: 12.5px; color: #64748b; margin: 4px 0 0 0;">Topic: <strong>${topicTitle}</strong> | ${studentGrade}</p>

            </div>

            <div style="text-align: right; font-size: 11.5px; color: #475569;">

                <div>Student: <strong>${studentName}</strong></div>

                <div>Date: ${dateStr}</div>

            </div>

        </div>

    `;



    // Clone each message while preserving live-rendered KaTeX and SVG elements

    messages.forEach(msg => {

        const isUser = msg.classList.contains('user');

        const sender = isUser ? studentName : 'AI Maths Tutor';

        const bg = isUser ? '#f8fafc' : '#faf5ff';

        const border = isUser ? '#6366f1' : '#8b5cf6';

        

        const bodyEl = msg.querySelector('.message-body');

        if (!bodyEl) return;



        const clone = bodyEl.cloneNode(true);

        clone.querySelectorAll('.message-actions, .suggestion-chips-wrapper').forEach(el => el.remove());



        // Invert SVG text fill for white PDF background

        clone.querySelectorAll('svg').forEach(svg => {

            svg.style.maxWidth = '100%';

            svg.style.background = '#0f172a';

            svg.style.borderRadius = '8px';

            svg.style.padding = '8px';

        });



        html += `

            <div style="background: ${bg}; border-left: 4px solid ${border}; border-radius: 8px; padding: 12px 16px; margin-bottom: 14px; page-break-inside: avoid;">

                <div style="font-size: 12px; font-weight: bold; color: ${isUser ? '#334155' : '#6d28d9'}; margin-bottom: 6px;">

                    ${isUser ? '🎓 Question (' + sender + '):' : '👩‍🏫 AI Tutor Solution & Steps:'}

                </div>

                <div style="font-size: 13.5px; line-height: 1.6; color: #1e293b;">

                    ${clone.innerHTML}

                </div>

            </div>

        `;

    });



    html += `

        <div style="border-top: 1px solid #e2e8f0; padding-top: 12px; margin-top: 20px; text-align: center; font-size: 11px; color: #94a3b8;">

            Generated by AI Maths Tutor · NCERT Grounded Revision Notes

        </div>

    `;



    pdfWrapper.innerHTML = html;

    document.body.appendChild(pdfWrapper);



    const opt = {

        margin: [10, 10, 10, 10],

        filename: `Maths_Notes_${topicTitle.replace(/[^a-zA-Z0-9]/g, '_').slice(0, 25)}.pdf`,

        image: { type: 'jpeg', quality: 0.98 },

        html2canvas: { scale: 2, useCORS: true, letterRendering: true },

        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }

    };



    if (window.html2pdf) {

        html2pdf().set(opt).from(pdfWrapper).save().then(() => {

            pdfWrapper.remove();

        }).catch(err => {

            console.error('PDF generation error:', err);

            pdfWrapper.remove();

            alert('PDF creation completed.');

        });

    } else {

        const printWin = window.open('', '_blank');

        printWin.document.write(`<html><head><title>${topicTitle}</title></head><body>${html}</body></html>`);

        printWin.document.close();

        printWin.print();

        pdfWrapper.remove();

    }

}



// Bind Export PDF Button

const exportPdfBtn = document.getElementById('export-pdf-btn');

if (exportPdfBtn) {

    exportPdfBtn.addEventListener('click', exportChatToPDF);

}



// Helper: Append Message Bubble with Action Toolbar (TTS & Copy)

function appendMessage(sender, text, type, imageUrl = null, imagePrompt = null, imageProvider = null) {

    const welcomeHero = document.getElementById('welcome-hero');

    if (welcomeHero) welcomeHero.remove();



    const msgDiv = document.createElement('div');

    msgDiv.className = `message ${type}`;

    const avatar = type === 'user' ? '🎓' : '👩‍🏫';



    let actionToolbar = '';

    if (type === 'assistant') {

        actionToolbar = `

            <div class="message-actions">

                <button type="button" class="message-action-btn tts-btn" title="Listen to AI Teacher Voice">

                    🔊 <span>Listen</span>

                </button>

                <button type="button" class="message-action-btn copy-btn" title="Copy Solution">

                    📋 <span>Copy</span>

                </button>

                <button type="button" class="message-action-btn gen-img-btn" title="Generate AI 3D Visual for this solution">

                    🎨 <span>Visual</span>

                </button>

            </div>

        `;

    }



    // Detect if text contains actual Urdu/Arabic characters

    const hasRtlChars = /[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]/.test(text);

    const tutorLang = (localStorage.getItem('tutorLanguage') || '').toLowerCase();

    const isRtlLangMode = (tutorLang === 'ur' || tutorLang === 'urdu' || tutorLang === 'ar' || tutorLang === 'arabic');



    // Never force RTL on user's English/Hinglish question or non-RTL text

    let rtlAttr = 'dir="ltr"';

    let rtlClass = '';

    if (type === 'assistant' && (hasRtlChars || isRtlLangMode)) {

        rtlAttr = 'dir="auto"';

        rtlClass = ' rtl-message-body';

    } else if (type === 'user' && hasRtlChars) {

        rtlAttr = 'dir="rtl"';

        rtlClass = ' rtl-message-body';

    } else {

        rtlAttr = 'dir="ltr"';

    }



    let imageCardHtml = '';
    if (imageUrl) {
        imageCardHtml = `
            <div class="ai-generated-visual-card">
                <div class="ai-visual-header">
                    <span class="ai-visual-badge">🎨 Mathematical Infographic Poster</span>
                    <span class="ai-visual-provider">${imageProvider || 'Infographic Engine'}</span>
                </div>
                <div class="ai-visual-img-container" onclick="openImageModal('${imageUrl}')">
                    <img src="${imageUrl}" alt="AI Mathematical Visualization" class="ai-visual-image" loading="lazy" />
                    <div class="ai-visual-overlay">🔍 Click to Expand Fullscreen</div>
                </div>
            </div>
        `;
    }

    msgDiv.innerHTML = `

        <div class="avatar">${avatar}</div>

        <div class="message-content">

            <h4>${sender}</h4>

            <div class="message-body${rtlClass}" ${rtlAttr}>${type === 'assistant' ? renderMarkdown(text) : text.replace(/\n/g, '<br>')}${imageCardHtml}</div>

            ${actionToolbar}

        </div>

    `;



    messagesContainer.appendChild(msgDiv);

    messagesContainer.scrollTop = messagesContainer.scrollHeight;



    // Attach Action Listeners (TTS Voice, Copy & Smart Interactive Suggestion Chips)

    if (type === 'assistant') {

        const ttsBtn = msgDiv.querySelector('.tts-btn');

        if (ttsBtn) {

            ttsBtn.addEventListener('click', () => toggleSpeech(text, ttsBtn));

        }

        // 🎨 On-Demand AI 3D Visual Generator with Live Percentage Progress & In-Place Replacement
        const genImgBtn = msgDiv.querySelector('.gen-img-btn');
        if (genImgBtn) {
            genImgBtn.addEventListener('click', async () => {
                const origHtml = genImgBtn.innerHTML;
                genImgBtn.disabled = true;
                genImgBtn.innerHTML = '⏳ <span>Creating...</span>';
                
                const bodyEl = msgDiv.querySelector('.message-body');
                
                // Hide any inline SVG so there is strictly ONE visual
                const existingSvgs = bodyEl.querySelectorAll('.math-svg-diagram, svg');
                existingSvgs.forEach(s => {
                    const block = s.closest('pre') || s;
                    block.style.display = 'none';
                });

                // Find or create progress card
                let progCard = bodyEl.querySelector('.ai-image-progress-card');
                if (!progCard) {
                    progCard = document.createElement('div');
                    progCard.className = 'ai-image-progress-card';
                    bodyEl.appendChild(progCard);
                }
                
                progCard.innerHTML = `
                    <div class="ai-progress-header">
                        <span class="ai-progress-title">🎨 Creating Mathematical Infographic...</span>
                        <span class="ai-progress-percent">15%</span>
                    </div>
                    <div class="ai-progress-track">
                        <div class="ai-progress-fill" style="width: 15%;"></div>
                    </div>
                    <div class="ai-progress-hint">Analyzing coordinates and educational blueprint...</div>
                `;

                let pct = 15;
                const fillEl = progCard.querySelector('.ai-progress-fill');
                const pctEl = progCard.querySelector('.ai-progress-percent');
                const hintEl = progCard.querySelector('.ai-progress-hint');

                const progInterval = setInterval(() => {
                    if (pct < 90) {
                        pct += Math.floor(Math.random() * 12) + 7;
                        if (pct > 92) pct = 92;
                        if (fillEl) fillEl.style.width = pct + '%';
                        if (pctEl) pctEl.innerText = pct + '%';
                        if (hintEl) {
                            if (pct > 35 && pct < 65) hintEl.innerText = 'Calculating right-angled triangle, ratios & angles...';
                            else if (pct >= 65) hintEl.innerText = 'Composing SOH-CAH-TOA formulas & high-contrast theme...';
                        }
                    }
                }, 200);

                try {
                    const activeTopic = (document.getElementById('current-topic')?.innerText || text.slice(0, 80)).replace(/[^a-zA-Z0-9\s]/g, ' ').trim();
                    const resp = await fetch(`${API_BASE_URL}/api/generate-image`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ question: activeTopic, context: text, chat_id: currentChatId })
                    });
                    const resData = await resp.json();
                    
                    clearInterval(progInterval);
                    if (fillEl) fillEl.style.width = '100%';
                    if (pctEl) pctEl.innerText = '100%';
                    if (hintEl) hintEl.innerText = 'Infographic Complete!';

                    await new Promise(r => setTimeout(r, 220));

                    if (resData.image_url) {
                        // In-place replacement: remove progress card and any previous visual card
                        if (progCard && progCard.parentNode) progCard.parentNode.removeChild(progCard);
                        const existingCard = bodyEl.querySelector('.ai-generated-visual-card');
                        if (existingCard && existingCard.parentNode) existingCard.parentNode.removeChild(existingCard);

                        const cardDiv = document.createElement('div');
                        cardDiv.innerHTML = `
                            <div class="ai-generated-visual-card">
                                <div class="ai-visual-header">
                                    <span class="ai-visual-badge">🎨 Mathematical Infographic Poster</span>
                                    <span class="ai-visual-provider">${resData.provider || 'Infographic Engine'}</span>
                                </div>
                                <div class="ai-visual-img-container" onclick="openImageModal('${resData.image_url}')">
                                    <img src="${resData.image_url}" alt="AI Mathematical Visualization" class="ai-visual-image" loading="lazy" />
                                    <div class="ai-visual-overlay">🔍 Click to Expand Fullscreen</div>
                                </div>
                                ${resData.prompt ? `<div class="ai-visual-caption" style="padding: 8px 14px; font-size: 11px; color: #94a3b8; background: rgba(15,23,42,0.9); border-top: 1px solid rgba(255,255,255,0.06);">💡 <strong>Infographic Topic:</strong> <em>${resData.prompt}</em></div>` : ''}
                            </div>
                        `;
                        bodyEl.appendChild(cardDiv);
                        genImgBtn.innerHTML = '✨ <span>Regenerate</span>';
                    } else {
                        if (progCard && progCard.parentNode) progCard.parentNode.removeChild(progCard);
                        genImgBtn.innerHTML = '❌ <span>Failed</span>';
                        setTimeout(() => { genImgBtn.innerHTML = origHtml; }, 2500);
                    }
                } catch (err) {
                    clearInterval(progInterval);
                    if (progCard && progCard.parentNode) progCard.parentNode.removeChild(progCard);
                    genImgBtn.innerHTML = '❌ <span>Error</span>';
                    setTimeout(() => { genImgBtn.innerHTML = origHtml; }, 2500);
                } finally {
                    genImgBtn.disabled = false;
                }
            });
        }


        const copyBtn = msgDiv.querySelector('.copy-btn');

        if (copyBtn) {

            copyBtn.addEventListener('click', () => {

                const plainText = text.replace(/<[^>]+>/g, '');

                navigator.clipboard.writeText(plainText).then(() => {

                    copyBtn.innerHTML = '✅ <span>Copied</span>';

                    setTimeout(() => { copyBtn.innerHTML = '📋 <span>Copy</span>'; }, 2000);

                });

            });

        }



        // 💡 Interactive Suggestion Chips Renderer (Disabled in Quick and Socratic modes)

        const msgBody = msgDiv.querySelector('.message-body');

        if (msgBody && currentStyle !== 'quick' && currentStyle !== 'socratic') {

            const listItems = msgBody.querySelectorAll('li, p');

            const suggestions = [];

            const elementsToRemove = [];



            listItems.forEach(el => {

                const textVal = el.innerText.trim();

                if ((textVal.includes('?') || textVal.toLowerCase().includes('kya aap') || textVal.toLowerCase().includes('would you like')) && textVal.length < 130) {

                    const cleanQ = textVal.replace(/^[0-9\.\-\*\•\?\s💡✨]+/, '').trim();

                    if (cleanQ.length > 5 && !suggestions.includes(cleanQ)) {

                        suggestions.push(cleanQ);

                        elementsToRemove.push(el);

                    }

                }

            });



            // Remove the raw duplicate text bullet items since they become clean interactive chips

            elementsToRemove.forEach(el => el.remove());



            if (suggestions.length > 0) {

                const chipsWrapper = document.createElement('div');

                chipsWrapper.className = 'suggestion-chips-wrapper';

                chipsWrapper.innerHTML = `<div class="chips-title">💡 Follow-up Concept (Click to explore):</div><div class="chips-list"></div>`;

                const chipsList = chipsWrapper.querySelector('.chips-list');



                suggestions.slice(0, 2).forEach(q => {

                    const chipBtn = document.createElement('button');

                    chipBtn.type = 'button';

                    chipBtn.className = 'suggestion-chip';

                    chipBtn.innerHTML = `✨ ${q}`;

                    chipBtn.addEventListener('click', () => {

                        if (userInput) {

                            userInput.value = q;

                            userInput.focus();

                            submitUserMessage();

                        }

                    });

                    chipsList.appendChild(chipBtn);

                });



                msgBody.appendChild(chipsWrapper);

            }

        }

    }



    // Message aate hi LaTeX math formulas ko sundar equation me render karo

    renderMathInTarget(msgDiv);

}



// Resilient KaTeX renderer helper with async retry support

function renderMathInTarget(targetEl) {

    if (!targetEl) return;

    const delimiters = [

        {left: '$$', right: '$$', display: true},

        {left: '$', right: '$', display: false},

        {left: '\\[', right: '\\]', display: true},

        {left: '\\(', right: '\\)', display: false}

    ];



    if (window.renderMathInElement) {

        try {

            window.renderMathInElement(targetEl, {

                delimiters: delimiters,

                throwOnError: false,

                errorColor: '#f43f5e'

            });

        } catch (err) {

            console.warn('KaTeX rendering error:', err);

        }

    } else {

        let attempts = 0;

        const timer = setInterval(() => {

            attempts++;

            if (window.renderMathInElement) {

                clearInterval(timer);

                try {

                    window.renderMathInElement(targetEl, {

                        delimiters: delimiters,

                        throwOnError: false,

                        errorColor: '#f43f5e'

                    });

                } catch (e) {}

            } else if (attempts > 30) {

                clearInterval(timer);

            }

        }, 100);

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

            <p class="welcome-subtitle">Welcome to AI Maths Tutor!<br>How would you like me to teach you today?</p>

            

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

        const uid = getUserId();

        const raw = localStorage.getItem(`cachedMessages_${uid}_${chatId}`);

        return raw ? JSON.parse(raw) : [];

    } catch (e) {

        return [];

    }

}



function saveMessageToCache(chatId, msg) {

    try {

        const uid = getUserId();

        const msgs = getCachedMessages(chatId);

        msgs.push(msg);

        localStorage.setItem(`cachedMessages_${uid}_${chatId}`, JSON.stringify(msgs));

    } catch (e) {

        console.warn('Could not save message to localStorage', e);

    }

}



function setCachedMessages(chatId, msgs) {

    try {

        const uid = getUserId();

        localStorage.setItem(`cachedMessages_${uid}_${chatId}`, JSON.stringify(msgs));

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



let devShowAllUsersHistory = false;



// Fetch chats and render in Pinned and Recents (Filtered per User ID by default, or all if Developer toggles)

async function fetchAndRenderSidebarChats() {

    try {

        const uid = getUserId();

        const showAllParam = (userRole === 'developer' && devShowAllUsersHistory) ? '&show_all=true' : '';

        const res = await fetch(`${API_BASE_URL}/api/chats?user_id=${uid}${showAllParam}`);

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



    hasSelectedStyleForConversation = true;

    hasUserDismissedModeSelector = false;

    hideModeSelector();



    // 1. Immediately render cached messages if available

    const cachedMsgs = getCachedMessages(chatId);

    if (cachedMsgs && cachedMsgs.length > 0) {

        if (messagesContainer) messagesContainer.innerHTML = '';

        if (!hasSelectedStyleForConversation) {

            const lastMsgWithStyle = [...cachedMsgs].reverse().find(m => m.style);

            if (lastMsgWithStyle && lastMsgWithStyle.style) {

                updateStyleEverywhere(lastMsgWithStyle.style);

            }

        }

        cachedMsgs.forEach(msg => {

            const senderName = msg.sender === 'user' ? 'You' : 'AI Maths Tutor';

            appendMessage(senderName, msg.text, msg.sender);

        });

    } else if (messagesContainer) {

        messagesContainer.innerHTML = '<div style="text-align:center; padding:30px; color:#94a3b8; font-size:13px;">Loading conversation...</div>';

    }



    // 2. Fetch fresh messages from API (User isolated)

    try {

        const uid = getUserId();

        const userAuthToken = localStorage.getItem('authToken');

        const authHeaders = userAuthToken ? { 'Authorization': `Bearer ${userAuthToken}` } : {};

        const res = await fetch(`${API_BASE_URL}/api/chats/${chatId}/messages?user_id=${uid}`, { headers: authHeaders });

        if (res.status === 403 || res.status === 404) {

            console.warn('Unauthorized or non-existent chat session. Resetting to clean new chat.');

            startNewChat();

            return;

        }

        if (res.ok) {

            const data = await res.json();

            if (data.messages && Array.isArray(data.messages)) {

                setCachedMessages(chatId, data.messages);

                if (messagesContainer) messagesContainer.innerHTML = '';

                if (data.messages.length > 0) {

                    if (!hasSelectedStyleForConversation) {

                        const lastMsgWithStyle = [...data.messages].reverse().find(m => m.style);

                        if (lastMsgWithStyle && lastMsgWithStyle.style) {

                            updateStyleEverywhere(lastMsgWithStyle.style);

                        }

                    }

                    data.messages.forEach(msg => {

                        const senderName = msg.sender === 'user' ? 'You' : 'AI Maths Tutor';

                        appendMessage(senderName, msg.text, msg.sender, msg.image_url, msg.image_prompt);

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

    hasUserDismissedModeSelector = false;

    hasSelectedStyleForConversation = false;

    hideModeSelector();



    // Re-initialize to configured default style

    currentStyle = localStorage.getItem('defaultStyle') || 'quick';

    updateStyleEverywhere(currentStyle);



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



// Restore active chat session ONLY if explicit ?c= query parameter is in the URL

function restoreActiveSessionOnInit() {

    try {

        const urlParams = new URLSearchParams(window.location.search);

        const urlChatId = urlParams.get('c') || urlParams.get('chat');



        // Only restore if user explicitly requested a specific chat in the URL bar

        if (urlChatId) {

            const chats = allChatsCache.length > 0 ? allChatsCache : getCachedChats();

            const found = chats.find(c => String(c.id) === String(urlChatId));

            if (found) {

                loadChatSession(urlChatId, found.title);

                return true;

            }

        }

    } catch (e) {

        console.warn('Error restoring session on init:', e);

    }

    // Clean default landing: always show fresh welcome hero on re-login

    startNewChat();

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



// Sync Profile / Grade updates to MySQL DB

async function syncUserProfileToBackend(name, grade) {

    const uid = getUserId();

    const token = localStorage.getItem('authToken');

    try {

        await fetch(`${API_BASE_URL}/api/user/profile`, {

            method: 'POST',

            headers: {

                'Content-Type': 'application/json',

                ...(token ? { 'Authorization': `Bearer ${token}` } : {})

            },

            body: JSON.stringify({

                user_id: uid,

                name: name || undefined,

                grade: grade || undefined

            })

        });

    } catch (e) {

        console.warn('Backend profile sync notice:', e);

    }

}



// Clean App Logout Handler (Resets JWT, User, and Session Cache)

function performAppLogout() {

    localStorage.removeItem('studentName');

    localStorage.removeItem('studentEmail');

    localStorage.removeItem('userRole');

    localStorage.removeItem('userId');

    localStorage.removeItem('authToken');

    localStorage.removeItem('studentGrade');

    localStorage.removeItem('activeChatId');

    localStorage.removeItem('authProvider');

    window.location.href = 'login.html';

}



// 9. Logout Button Handler inside Profile Popup

const popupLogoutItem = document.getElementById('popup-logout-item');

if (popupLogoutItem) {

    popupLogoutItem.addEventListener('click', performAppLogout);

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



    // Account tab inputs

    const accNameInput = document.getElementById('setting-account-name');

    const accUserInput = document.getElementById('setting-account-username');

    const accEmailEl = document.getElementById('setting-account-email');



    if (accNameInput) accNameInput.value = localStorage.getItem('studentName') || currentStudentName;

    if (accUserInput) accUserInput.value = localStorage.getItem('studentUsername') || `@${currentStudentName.toLowerCase().replace(/\s+/g, '')}`;

    if (accEmailEl) accEmailEl.innerText = localStorage.getItem('studentEmail') || `${currentStudentName.toLowerCase().replace(/\s+/g, '')}@gmail.com`;



    const customApiInput = document.getElementById('setting-custom-api-url');

    if (customApiInput) customApiInput.value = localStorage.getItem('customApiBaseUrl') || '';



    applyFontSize(currentFontSizeLevel);

}



// Save Custom Backend API URL (Cloudflare Tunnel or Local LAN)

const saveCustomApiBtn = document.getElementById('save-custom-api-btn');

if (saveCustomApiBtn) {

    saveCustomApiBtn.addEventListener('click', () => {

        const customApiInput = document.getElementById('setting-custom-api-url');

        const val = customApiInput ? customApiInput.value.trim() : '';

        if (val) {

            localStorage.setItem('customApiBaseUrl', val.replace(/\/+$/, ''));

            alert('🚀 Custom Backend API URL saved! Reloading...');

            window.location.reload();

        } else {

            localStorage.removeItem('customApiBaseUrl');

            alert('Custom API URL cleared! Using default auto-detect.');

            window.location.reload();

        }

    });

}



// Save Account Details

const saveAccountNameBtn = document.getElementById('save-account-name-btn');

if (saveAccountNameBtn) {

    saveAccountNameBtn.addEventListener('click', () => {

        const accNameInput = document.getElementById('setting-account-name');

        const accUserInput = document.getElementById('setting-account-username');

        if (accNameInput && accNameInput.value.trim()) {

            const newName = accNameInput.value.trim();

            localStorage.setItem('studentName', newName);

            if (userDisplayNameEl) userDisplayNameEl.innerText = newName;

            if (welcomeGreetingEl) welcomeGreetingEl.innerText = `Hello ${newName}!`;

            syncUserProfileToBackend(newName, null);

        }

        if (accUserInput && accUserInput.value.trim()) {

            localStorage.setItem('studentUsername', accUserInput.value.trim());

        }

        alert('🎉 Account settings updated!');

    });

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

        updateLangEverywhere(e.target.value);

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



        syncUserProfileToBackend(null, newGrade);

    });

}



// 4. Default Teaching Style Change

if (settingDefaultStyleSelect) {

    settingDefaultStyleSelect.addEventListener('change', (e) => {

        hasSelectedStyleForConversation = true;

        updateStyleEverywhere(e.target.value);

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

    settingsLogoutBtn.addEventListener('click', performAppLogout);

}



// 9. Sidebar Collapse / Expand Toggle & Drag-to-Resize (Claude & ChatGPT Style)

const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');

const sidebar = document.querySelector('.sidebar');

const sidebarResizer = document.getElementById('sidebar-resizer');



const DEFAULT_SIDEBAR_WIDTH = 285;



// Restore saved sidebar width on page load

const savedSidebarWidth = localStorage.getItem('sidebarCustomWidth');

if (savedSidebarWidth && sidebar && !sidebar.classList.contains('collapsed')) {

    const widthNum = parseInt(savedSidebarWidth, 10);

    if (widthNum >= 220 && widthNum <= 520) {

        sidebar.style.width = `${widthNum}px`;

    } else {

        sidebar.style.width = `${DEFAULT_SIDEBAR_WIDTH}px`;

    }

} else if (sidebar && !sidebar.classList.contains('collapsed')) {

    sidebar.style.width = `${DEFAULT_SIDEBAR_WIDTH}px`;

}



function toggleSidebarCollapse() {

    if (!sidebar) return;

    const isCollapsed = sidebar.classList.toggle('collapsed');

    if (isCollapsed) {

        sidebar.style.removeProperty('width');

    } else {

        const savedW = localStorage.getItem('sidebarCustomWidth');

        const targetW = (savedW && parseInt(savedW, 10) >= 240) ? parseInt(savedW, 10) : DEFAULT_SIDEBAR_WIDTH;

        sidebar.style.width = `${targetW}px`;

    }

}



if (sidebarToggleBtn) {

    sidebarToggleBtn.addEventListener('click', toggleSidebarCollapse);

}



// Keyboard Shortcut: Ctrl+B or Cmd+B to toggle sidebar

document.addEventListener('keydown', (e) => {

    if ((e.ctrlKey || e.metaKey) && (e.key === 'b' || e.key === 'B')) {

        e.preventDefault();

        toggleSidebarCollapse();

    }

});



// Drag to Resize Sidebar Handle

if (sidebarResizer && sidebar) {

    let isDragging = false;

    let startX = 0;

    let hasMoved = false;



    sidebarResizer.addEventListener('mousedown', (e) => {

        isDragging = true;

        hasMoved = false;

        startX = e.clientX;

        sidebarResizer.classList.add('is-dragging');

        document.body.style.cursor = 'col-resize';

        document.body.style.userSelect = 'none';

    });



    document.addEventListener('mousemove', (e) => {

        if (!isDragging) return;

        const delta = Math.abs(e.clientX - startX);

        if (delta > 3) hasMoved = true;



        const newWidth = e.clientX;

        if (newWidth < 120) {

            if (!sidebar.classList.contains('collapsed')) {

                sidebar.classList.add('collapsed');

                sidebar.style.removeProperty('width');

            }

        } else {

            if (sidebar.classList.contains('collapsed')) {

                sidebar.classList.remove('collapsed');

            }

            const clampedWidth = Math.max(170, Math.min(520, newWidth));

            sidebar.style.width = `${clampedWidth}px`;

        }

    });



    document.addEventListener('mouseup', () => {

        if (isDragging) {

            isDragging = false;

            sidebarResizer.classList.remove('is-dragging');

            document.body.style.cursor = '';

            document.body.style.userSelect = '';



            if (!hasMoved) {

                toggleSidebarCollapse();

            } else if (!sidebar.classList.contains('collapsed')) {

                localStorage.setItem('sidebarCustomWidth', sidebar.offsetWidth);

            }

        }

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

    if (popupDevItem) popupDevItem.style.display = 'flex';

    if (userPlanTagEl) {

        userPlanTagEl.innerHTML = `⚡ <strong style="color:#c084fc;">Developer Admin</strong> · RAG Manager`;

    }

    const popupBadgeEl = document.getElementById('popup-plan-badge');

    if (popupBadgeEl) {

        popupBadgeEl.innerHTML = `⚡ Developer Admin · Full RAG Access`;

        popupBadgeEl.style.color = `#c084fc`;

    }

} else {

    if (popupDevItem) popupDevItem.style.display = 'none';

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



// 5. Change Developer Admin Email & Password Handler

const devPasswordForm = document.getElementById('dev-password-form');

const devPasswordBtn = document.getElementById('dev-password-submit-btn');



if (devPasswordForm) {

    // Populate current saved dev email if present

    const devEmailInput = document.getElementById('dev-email-input');

    const savedDevEmail = localStorage.getItem('developerEmail') || localStorage.getItem('studentEmail') || 'dev@mathstutor.com';

    if (devEmailInput && savedDevEmail) {

        devEmailInput.value = savedDevEmail;

    }



    devPasswordForm.addEventListener('submit', async (e) => {

        e.preventDefault();

        const newEmail = devEmailInput ? devEmailInput.value.trim() : '';

        const currentPass = document.getElementById('dev-current-password') ? document.getElementById('dev-current-password').value.trim() : '';

        const newPass = document.getElementById('dev-new-password') ? document.getElementById('dev-new-password').value.trim() : '';

        const confirmPass = document.getElementById('dev-confirm-password') ? document.getElementById('dev-confirm-password').value.trim() : '';



        // 1. Current/Old password is strictly required for any change

        if (!currentPass) {

            showDevAlert('Purana/Current password enter karna anivarya (required) hai.', 'error');

            return;

        }



        // 2. Either new email or new password must be provided

        if (!newEmail && !newPass) {

            showDevAlert('Kripya naya Gmail ya naya Password enter karein.', 'error');

            return;

        }



        // 3. If new password is provided, verify matching and length

        if (newPass) {

            if (newPass !== confirmPass) {

                showDevAlert('Naya password aur confirm password match nahi kar rahe hain! Dono same hone chahiye.', 'error');

                return;

            }

            if (newPass.length < 4) {

                showDevAlert('Naya password kam se kam 4 characters ka hona chahiye.', 'error');

                return;

            }

        }



        if (devPasswordBtn) {

            devPasswordBtn.disabled = true;

            devPasswordBtn.innerText = '⏳ Updating Credentials...';

        }



        try {

            const res = await fetch(`${API_BASE_URL}/api/dev/update-credentials`, {

                method: 'POST',

                headers: { 'Content-Type': 'application/json' },

                body: JSON.stringify({

                    current_password: currentPass,

                    new_email: newEmail,

                    new_password: newPass,

                    confirm_password: confirmPass

                })

            });

            const data = await res.json();

            if (res.ok && data.success) {

                if (newEmail) {

                    localStorage.setItem('developerEmail', newEmail);

                    localStorage.setItem('studentEmail', newEmail);

                }

                if (newPass) {

                    localStorage.setItem('devAdminPassword', newPass);

                }

                showDevAlert(`🎉 ${data.message || 'Developer credentials updated successfully!'}`, 'success');

                // Clear password fields for security

                if (document.getElementById('dev-current-password')) {

                    document.getElementById('dev-current-password').value = '';

                }

                if (document.getElementById('dev-new-password')) {

                    document.getElementById('dev-new-password').value = '';

                }

                if (document.getElementById('dev-confirm-password')) {

                    document.getElementById('dev-confirm-password').value = '';

                }

            } else {

                showDevAlert(data.detail || 'Failed to update developer credentials.', 'error');

            }

        } catch (err) {

            showDevAlert(`Network notice: ${err.message}`, 'error');

        } finally {

            if (devPasswordBtn) {

                devPasswordBtn.disabled = false;

                devPasswordBtn.innerText = '💾 Update Developer Credentials';

            }

        }

    });

}



// ========================================================
// 🔍 AI Image Fullscreen Modal / Lightbox Functions
// ========================================================
function openImageModal(imgUrl) {
    let backdrop = document.getElementById('ai-lightbox-modal');
    if (!backdrop) {
        backdrop = document.createElement('div');
        backdrop.id = 'ai-lightbox-modal';
        backdrop.className = 'ai-image-modal-backdrop';
        backdrop.innerHTML = `
            <div class="ai-image-modal-content">
                <button type="button" class="ai-image-modal-close" onclick="closeImageModal()">✕</button>
                <img id="ai-lightbox-img" src="" alt="Expanded AI Simulation" />
            </div>
        `;
        backdrop.addEventListener('click', (e) => {
            if (e.target === backdrop) closeImageModal();
        });
        document.body.appendChild(backdrop);
    }
    const imgEl = document.getElementById('ai-lightbox-img');
    if (imgEl) imgEl.src = imgUrl;
    backdrop.style.display = 'flex';
}

function closeImageModal() {
    const backdrop = document.getElementById('ai-lightbox-modal');
    if (backdrop) backdrop.style.display = 'none';
}
window.openImageModal = openImageModal;
window.closeImageModal = closeImageModal;
