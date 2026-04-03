// Initialize PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

// Initialize Lucide icons
lucide.createIcons();

// State management
let currentWords = [];
let currentBilingualLines = []; 
let currentType = 'lyrics';
let isTranslationVisible = false;

// Mock Dictionary for prototype
const MOCK_DICTIONARY = {
    'apple': '苹果', 'banana': '香蕉', 'cherry': '樱桃', 'date': '枣', 'elderberry': '接骨木莓',
    'innovate': '创新', 'strategy': '策略', 'synergy': '协同', 'leverage': '杠杆/利用', 'benchmark': '基准',
    'serendipity': '意外惊喜', 'ephemeral': '转瞬即逝', 'eloquent': '雄辩的', 'ethereal': '空灵的', 'luminous': '发光的',
    'dream': '梦想', 'sun': '太阳', 'friend': '朋友', 'clouds': '云朵', 'remember': '记住', 'December': '十二月',
    'step': '步伐', 'shadows': '阴影', 'knowledge': '知识', 'passion': '激情', 'fire': '火焰',
    'person': '人', 'bag': '包包', 'alien': '外星人', 'shocked': '震惊', 'pan': '平底锅', 'monster': '怪物',
    'cat': '猫咪', 'lighter': '打火机', 'chocolate': '巧克力', 'troubles': '烦恼',
    'ocean': '海洋', 'secret': '秘密', 'light': '光芒', 'wings': '翅膀', 'forest': '森林', 'mountain': '山峦',
    'star': '星辰', 'river': '河流', 'magic': '魔法', 'journey': '旅程', 'courage': '勇气', 'future': '未来',
    'experience': '经验', 'quiet': '安静', 'dark': '黑暗', 'world': '世界',
    // 常见学习/表达类词汇（覆盖你给的示例）
    'system': '系统', 'change': '改变', 'mark': '痕迹/标记', 'culture': '文化', 'support': '支持', 'result': '结果',
    'decade': '十年', 'evidence': '证据', 'research': '研究', 'policy': '政策', 'economic': '经济',
    // 场景相关补充
    'city': '城市', 'street': '街道', 'square': '广场', 'river': '河流', 'bridge': '桥', 'station': '车站', 'platform': '站台',
    'night': '夜晚', 'morning': '早晨', 'music': '音乐', 'song': '歌曲', 'light': '灯光', 'shadow': '影子',
    // 常见通用词
    'standard': '标准'
};

// Runtime cache for dynamically fetched translations (user/session-level)
const USER_TRANSLATIONS = {};

const PALETTE_STYLES = {
    morandi: [
        { bg: 'bg-[#8ba88e]/25', border: 'border-[#8ba88e]/35', text: 'text-[#4a5d4d]' }, // Sage
        { bg: 'bg-[#8ca6b8]/25', border: 'border-[#8ca6b8]/35', text: 'text-[#3e4e59]' }, // Dusty Blue
        { bg: 'bg-[#b89c8c]/25', border: 'border-[#b89c8c]/35', text: 'text-[#5e4d44]' }, // Clay
        { bg: 'bg-[#c2b280]/25', border: 'border-[#c2b280]/35', text: 'text-[#5c543c]' }, // Sand
        { bg: 'bg-[#a39193]/25', border: 'border-[#a39193]/35', text: 'text-[#524647]' }, // Ash Rose
    ],
    vintage: [
        { bg: 'bg-[#a63a3a]/20', border: 'border-[#a63a3a]/30', text: 'text-[#611a1a]' }, // Brick Red
        { bg: 'bg-[#2b4561]/20', border: 'border-[#2b4561]/30', text: 'text-[#1a2b3d]' }, // Navy
        { bg: 'bg-[#b8860b]/20', border: 'border-[#b8860b]/30', text: 'text-[#5c4305]' }, // Mustard
        { bg: 'bg-[#2e4d2e]/20', border: 'border-[#2e4d2e]/30', text: 'text-[#1a2b1a]' }, // Forest Green
        { bg: 'bg-[#5d4037]/20', border: 'border-[#5d4037]/30', text: 'text-[#3e2723]' }, // Coffee
    ],
    macaron: [
        { bg: 'bg-[#e0f2f1]/45', border: 'border-[#b2dfdb]/55', text: 'text-[#00695c]' }, // Mint
        { bg: 'bg-[#e3f2fd]/45', border: 'border-[#bbdefb]/55', text: 'text-[#1565c0]' }, // Sky
        { bg: 'bg-[#fce4ec]/45', border: 'border-[#f8bbd0]/55', text: 'text-[#c2185b]' }, // Sakura
        { bg: 'bg-[#f3e5f5]/45', border: 'border-[#e1bee7]/55', text: 'text-[#7b1fa2]' }, // Lavender
        { bg: 'bg-[#fffde7]/45', border: 'border-[#fff9c4]/55', text: 'text-[#fbc02d]' }, // Lemon
    ],
    nordic: [
        { bg: 'bg-[#f8f9fa]/70', border: 'border-[#dee2e6]/50', text: 'text-[#495057]' }, // Off-white
        { bg: 'bg-[#e9ecef]/70', border: 'border-[#ced4da]/50', text: 'text-[#343a40]' }, // Light Gray
        { bg: 'bg-[#f1f3f5]/70', border: 'border-[#e9ecef]/50', text: 'text-[#212529]' }, // Smoke
        { bg: 'bg-[#e7f5ff]/70', border: 'border-[#d0ebff]/50', text: 'text-[#1864ab]' }, // Ice Blue
        { bg: 'bg-[#fff4e6]/70', border: 'border-[#ffe8cc]/50', text: 'text-[#d9480f]' }, // Muted Wood
    ]
};

let currentPalette = PALETTE_STYLES.macaron; // Default

function setUserTranslation(en, zh) {
    if (!en || !zh) return;
    USER_TRANSLATIONS[en.toLowerCase()] = zh;
}

function splitSenses(zh) {
    if (!zh) return [];
    // 支持以 / 、； ; 、， 分隔的多义项
    const parts = zh.split(/[\/；;、，]/).map(s => s.trim()).filter(Boolean);
    // 去重并限制最多 4 个，避免 tooltip 过长
    const uniq = [];
    for (const p of parts) {
        if (!uniq.includes(p)) uniq.push(p);
        if (uniq.length >= 4) break;
    }
    return uniq.length ? uniq : [zh];
}

function getSenses(word) {
    const zh = getTranslation(word);
    if (!zh) return [];
    return splitSenses(zh);
}

function getTranslation(word) {
    if (!word) return '';
    const w = word.toLowerCase();
    if (USER_TRANSLATIONS[w]) return USER_TRANSLATIONS[w];
    if (MOCK_DICTIONARY[w]) return MOCK_DICTIONARY[w];
    // 轻量级词形还原尝试（提升命中率）
    const tryBases = [];
    if (w.endsWith('ies')) tryBases.push(w.slice(0, -3) + 'y');      // policies -> policy
    if (w.endsWith('es'))  tryBases.push(w.slice(0, -2));            // changes -> change
    if (w.endsWith('s'))   tryBases.push(w.slice(0, -1));            // results -> result
    if (w.endsWith('ing')) {
        tryBases.push(w.slice(0, -3));                               // learning -> learn
        if (w.length > 4 && w.slice(0, -3).endsWith('e')) {
            tryBases.push(w.slice(0, -3));                            // making -> make (already same)
        } else {
            tryBases.push(w.slice(0, -3) + 'e');                      // coming -> come
        }
    }
    if (w.endsWith('ed')) {
        tryBases.push(w.slice(0, -2));                               // changed -> chang(e)d -> change (approx)
        tryBases.push(w.slice(0, -1));                               // walked -> walke -> walk (approx)
    }
    for (const b of tryBases) {
        if (USER_TRANSLATIONS[b]) return USER_TRANSLATIONS[b];
        if (MOCK_DICTIONARY[b]) return MOCK_DICTIONARY[b];
    }
    return `[${word}]`;
}

// Try to fetch CN translation from a public endpoint for missing words
async function fetchZhFromPublicAPI(en) {
    const hasCJK = (s) => /[\u4e00-\u9fff]/.test(s);
    const isNoisy = (s) => {
        // 超过一半是数字或标点，判定为噪声
        const pure = s.replace(/\s+/g, '');
        if (!pure.length) return true;
        const noisyCount = (pure.match(/[0-9.,:;/%\-]/g) || []).length;
        return noisyCount / pure.length > 0.5;
    };
    try {
        const q = encodeURIComponent(en);
        const url = `https://api.mymemory.translated.net/get?q=${q}&langpair=en|zh-CN`;
        const resp = await fetch(url, { method: 'GET' });
        if (!resp.ok) return null;
        const data = await resp.json();
        const text = data?.responseData?.translatedText;
        if (!text) return null;
        // Filter obviously invalid echoes
        if (text.toLowerCase() === en.toLowerCase()) return null;
        // 过滤纯数字/无中文/噪声返回
        if (!hasCJK(text) || isNoisy(text)) return null;
        return text;
    } catch (_) {
        return null;
    }
}

async function preloadTranslations(words) {
    const tasks = [];
    const toFetch = [];
    for (const w of words) {
        const zh = getTranslation(w);
        if (zh.startsWith('[')) {
            toFetch.push(w);
        }
    }
    // Limit concurrency to avoid throttling
    const concurrency = 4;
    let idx = 0;
    async function worker() {
        while (idx < toFetch.length) {
            const current = toFetch[idx++];
            const zh = await fetchZhFromPublicAPI(current);
            if (zh) setUserTranslation(current, zh);
        }
    }
    for (let i = 0; i < concurrency; i++) tasks.push(worker());
    await Promise.all(tasks);
}

// DOM Elements
const wordInput = document.getElementById('word-input');
const wordUpload = document.getElementById('word-upload');
const pdfUpload = document.getElementById('pdf-upload');
const btnGenLyrics = document.getElementById('btn-gen-lyrics');
const btnGenStory = document.getElementById('btn-gen-story');
const resultSection = document.getElementById('result-section');
const resultTitle = document.getElementById('result-title');
const resultContent = document.getElementById('result-content');
const btnCopyLyrics = document.getElementById('btn-copy-lyrics');
const btnShareImage = document.getElementById('btn-share-image');
const btnTranslate = document.getElementById('btn-translate');
const btnToSuno = document.getElementById('btn-to-suno');
const editableLyrics = document.getElementById('editable-lyrics');
const songGenerationStatus = document.getElementById('song-generation-status');
const songLoading = document.getElementById('song-loading');
const songError = document.getElementById('song-error');
const btnRetrySong = document.getElementById('btn-retry-song');
const manualAudioUrlInput = document.getElementById('manual-audio-url');
const btnUseManualUrl = document.getElementById('btn-use-manual-url');
const songSuccess = document.getElementById('song-success');
const songAudio = document.getElementById('song-audio');
const songDownload = document.getElementById('song-download');
const toast = document.getElementById('toast');
const toastMessage = document.getElementById('toast-message');
let lastSongRequest = null;

// Utility: Show Toast
function showToast(message) {
    toastMessage.textContent = message;
    toast.classList.remove('translate-x-full');
    toast.classList.add('translate-x-0');
    setTimeout(() => {
        toast.classList.remove('translate-x-0');
        toast.classList.add('translate-x-full');
    }, 3000);
}

function getOriginalLyricsText() {
    return currentBilingualLines
        .filter(l => l.en)
        .map(l => l.en)
        .join('\n');
}

function fillEditableLyrics() {
    editableLyrics.value = getOriginalLyricsText();
}

function resetSongFeedback() {
    songGenerationStatus.classList.add('hidden');
    songLoading.classList.add('hidden');
    songLoading.classList.remove('flex');
    songError.classList.add('hidden');
    songError.textContent = '';
    btnRetrySong.classList.add('hidden');
    songSuccess.classList.add('hidden');
    songAudio.removeAttribute('src');
    songDownload.removeAttribute('href');
}

function showSongLoadingState() {
    songGenerationStatus.classList.remove('hidden');
    songLoading.classList.remove('hidden');
    songLoading.classList.add('flex');
    songError.classList.add('hidden');
    btnRetrySong.classList.add('hidden');
    songSuccess.classList.add('hidden');
}

function showSongErrorState(message) {
    songGenerationStatus.classList.remove('hidden');
    songLoading.classList.add('hidden');
    songLoading.classList.remove('flex');
    songError.textContent = message || '生成失败，请稍后重试';
    songError.classList.remove('hidden');
    btnRetrySong.classList.remove('hidden');
    songSuccess.classList.add('hidden');
}

function showSongSuccessState(audioUrl) {
    songGenerationStatus.classList.remove('hidden');
    songLoading.classList.add('hidden');
    songLoading.classList.remove('flex');
    songError.classList.add('hidden');
    btnRetrySong.classList.add('hidden');
    songSuccess.classList.remove('hidden');
    songAudio.src = audioUrl;
    // Ensure the browser starts loading the new media URL.
    songAudio.load();
    songDownload.href = audioUrl;
}

function wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function fetchWithTimeout(url, options = {}, timeoutMs = 140000) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
        return await fetch(url, { ...options, signal: controller.signal });
    } finally {
        clearTimeout(timer);
    }
}

function isSuccessStatus(status) {
    const s = String(status || '').toLowerCase();
    return ["success", "completed", "done", "finished"].includes(s) || s.includes("complete") || s.includes("finish");
}

function isFailureStatus(status) {
    const s = String(status || '').toLowerCase();
    return ["failed", "error", "cancelled", "canceled"].includes(s) || s.includes("fail");
}

async function pollSongStatus(taskId) {
    const maxAttempts = 60; // ~3min
    const intervalMs = 3000;
    console.log(`[DEBUG] Starting to poll song status for task: ${taskId}`);
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
        console.log(`[DEBUG] Polling attempt ${attempt + 1}/${maxAttempts}`);
        const response = await fetchWithTimeout(`/api/song-status/${encodeURIComponent(taskId)}`, {}, 60000);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            console.error(`[DEBUG] Polling failed:`, errorData);
            throw new Error(errorData.error || `查询状态失败 (${response.status})`);
        }
        const data = await response.json();
        console.log(`[DEBUG] Polling response:`, data);
        const status = String(data.status || '').toLowerCase();
        console.log(`[DEBUG] Current status: ${status}`);

        const audioUrl = data.audio_url || data.audioUrl;

        if (isSuccessStatus(status)) {
            if (!audioUrl) {
                console.error('[DEBUG] Status is success but no audio_url found');
                throw new Error('生成成功但未返回音频地址');
            }
            console.log(`[DEBUG] Song generation completed. Audio URL: ${audioUrl}`);
            return audioUrl;
        }

        if (isFailureStatus(status)) {
            console.error(`[DEBUG] Song generation failed:`, data.error);
            throw new Error(data.error || '歌曲生成失败');
        }

        // If the provider starts returning audio URL before status is normalized,
        // treat it as final when URL is present.
        if (audioUrl && (status.includes("complete") || status.includes("finish"))) {
            return audioUrl;
        }

        console.log(`[DEBUG] Still processing, waiting ${intervalMs}ms...`);
        await wait(intervalMs);
    }
    console.error(`[DEBUG] Polling timeout after ${maxAttempts} attempts`);
    throw new Error('生成超时，请点击重试');
}

async function generateSongFromLyrics(lyricsText, style = 'pop') {
    if (!lyricsText || !lyricsText.trim()) {
        showToast('请先填写歌词内容');
        return;
    }
    lastSongRequest = { lyrics: lyricsText.trim(), style };
    showSongLoadingState();
    try {
        const response = await fetchWithTimeout('/api/generate-song', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(lastSongRequest)
        }, 160000);

        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(data.error || `生成请求失败 (${response.status})`);
        }

        const audioUrl = data.audio_url || data.audioUrl;
        const taskId = data.task_id || data.taskId;

        // New contract: backend polls and tries to return audio_url directly.
        if (audioUrl) {
            showSongSuccessState(audioUrl);
            showToast('歌曲生成成功');
            return;
        }

        if (!taskId) throw new Error('未获取到任务 ID');

        const status = String(data.status || '').toLowerCase();
        if (isFailureStatus(status)) {
            throw new Error(data.error || '歌曲生成失败');
        }

        // Fallback: backend might still be processing when it hits its time budget.
        const finalAudioUrl = await pollSongStatus(taskId);
        showSongSuccessState(finalAudioUrl);
        showToast('歌曲生成成功');
    } catch (err) {
        showSongErrorState(err.message || '生成失败，请稍后重试');
    }
}

// Utility: Parse words from input
function parseWords(text) {
    const stopwords = new Set([
        'a', 'an', 'the', 'and', 'or', 'but', 'if', 'then', 'than',
        'in', 'on', 'at', 'of', 'to', 'for', 'with', 'from', 'by', 'as', 'into', 'over', 'under', 'between', 'through',
        'is', 'are', 'am', 'was', 'were', 'be', 'been', 'being',
        'it', 'this', 'that', 'these', 'those',
        'i', 'you', 'he', 'she', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
        'my', 'your', 'his', 'her', 'our', 'their',
        'not', 'no', 'yes', 'so', 'just', 'like', 'very', 'really'
    ]);

    const matches = text.match(/[A-Za-z]+(?:'[A-Za-z]+)?/g) || [];
    const seen = new Set();
    const result = [];

    for (const raw of matches) {
        const normalized = raw.toLowerCase();
        if (normalized.length < 2) continue;
        if (stopwords.has(normalized)) continue;
        if (seen.has(normalized)) continue;
        seen.add(normalized);
        result.push(raw);
    }

    return result;
}

// Clean Highlight: ONLY highlight user's input words, no extra text injection
function applyHighlight(text, targetWords, isChinese = false) {
    if (!targetWords || targetWords.length === 0) return text;
    
    let wordsToMatch = isChinese 
        ? targetWords.map(w => getTranslation(w))
        : targetWords;

    // Filter out empty translations
    wordsToMatch = wordsToMatch.filter(w => w && w.length > 0);
    
    const sorted = [...new Set(wordsToMatch)].sort((a, b) => b.length - a.length);
    const pattern = sorted.map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|');
    
    // For English, use word boundary \b
    const regex = isChinese 
        ? new RegExp(`(${pattern})`, 'g')
        : new RegExp(`\\b(${pattern})\\b`, 'gi');
    
    if (!isChinese) {
        // English line: show tooltip with CN translation
        return text.replace(regex, (match) => {
            const senses = getSenses(match);
            const title = senses.join('；');
            return `<span class="highlight" title="${title}">${match}</span>`;
        });
    } else {
        // Chinese line: tooltip shows original EN words that map to this translation
        const transToEn = new Map();
        for (const en of targetWords) {
            const zh = getTranslation(en);
            if (!zh) continue;
            if (!transToEn.has(zh)) transToEn.set(zh, new Set());
            transToEn.get(zh).add(en);
        }
        return text.replace(regex, (match) => {
            const ens = transToEn.get(match);
            let title = '';
            if (ens) {
                const enList = Array.from(ens);
                // 只选第一个英文词取义项，避免 tooltip 过长
                const sensePreview = getSenses(enList[0] || '');
                title = enList.join('/') + (sensePreview.length ? ` ｜ 义：${sensePreview.join('；')}` : '');
            }
            return `<span class="highlight" title="${title}">${match}</span>`;
        });
    }
}

// 1. File Upload: Word (.docx)
wordUpload.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (event) => {
        const arrayBuffer = event.target.result;
        try {
            const result = await mammoth.extractRawText({ arrayBuffer });
            wordInput.value = result.value;
            showToast('Word 文件解析成功！');
        } catch (err) {
            console.error(err);
            showToast('Word 文件解析失败');
        }
    };
    reader.readAsArrayBuffer(file);
});

// 2. File Upload: PDF
pdfUpload.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (event) => {
        const typedarray = new Uint8Array(event.target.result);
        try {
            const pdf = await pdfjsLib.getDocument(typedarray).promise;
            let fullText = '';
            for (let i = 1; i <= pdf.numPages; i++) {
                const page = await pdf.getPage(i);
                const textContent = await page.getTextContent();
                fullText += textContent.items.map(item => item.str).join(' ') + '\n';
            }
            wordInput.value = fullText;
            showToast('PDF 文件解析成功！');
        } catch (err) {
            console.error(err);
            showToast('PDF 文件解析失败');
        }
    };
    reader.readAsArrayBuffer(file);
});

function isImageFile(f) {
    return f && f.type && f.type.startsWith('image/');
}

async function ocrImageFiles(files) {
    const imgs = Array.from(files).filter(isImageFile);
    if (imgs.length === 0) {
        showToast('未检测到图片文件');
        return;
    }
    let result = '';
    for (const img of imgs) {
        try {
            const r = await Tesseract.recognize(img, 'eng');
            result += '\n' + (r?.data?.text || '');
        } catch (_) {}
    }
    if (result.trim().length > 0) {
        const prefix = wordInput.value.trim().length > 0 ? '\n' : '';
        wordInput.value += prefix + result.trim();
        showToast('图片识别完成');
    } else {
        showToast('未识别到文本');
    }
}

wordInput.addEventListener('dragover', (e) => {
    e.preventDefault();
    wordInput.classList.add('ring-2', 'ring-pink-200');
});
wordInput.addEventListener('dragleave', () => {
    wordInput.classList.remove('ring-2', 'ring-pink-200');
});
wordInput.addEventListener('drop', async (e) => {
    e.preventDefault();
    wordInput.classList.remove('ring-2', 'ring-pink-200');
    const files = e.dataTransfer?.files || [];
    if (!files.length) return;
    showToast('正在识别图片文字...');
    await ocrImageFiles(files);
});

wordInput.addEventListener('paste', async (e) => {
    const items = e.clipboardData?.items;
    if (!items || items.length === 0) return;
    const images = [];
    for (const item of items) {
        if (item.type && item.type.startsWith('image/')) {
            const file = item.getAsFile();
            if (file) images.push(file);
        }
    }
    if (images.length === 0) return;
    e.preventDefault();
    showToast('正在识别剪贴板图片...');
    await ocrImageFiles(images);
});

// Mock AI Generation Logic
async function generateAIContent(type) {
    const text = wordInput.value.trim();
    if (!text) {
        showToast('请先输入一些单词');
        return;
    }

    currentWords = parseWords(text);
    if (currentWords.length === 0) {
        showToast('未能识别到有效的英文单词');
        return;
    }

    currentType = type;
    
    // Pick a random palette style for this generation
    let styles = Object.keys(PALETTE_STYLES);
    
    // Filter out high-saturation styles for stories as requested
    if (type === 'story') {
        styles = styles.filter(s => s === 'morandi' || s === 'nordic');
    }
    
    const randomStyle = styles[Math.floor(Math.random() * styles.length)];
    currentPalette = PALETTE_STYLES[randomStyle];
    console.log(`Using visual style: ${randomStyle} (Type: ${type})`);

    const activeBtn = type === 'lyrics' ? btnGenLyrics : btnGenStory;
    const originalBtnText = activeBtn.innerHTML;
    activeBtn.innerHTML = '<i data-lucide="loader-2" class="animate-spin"></i> 正在生成...';
    lucide.createIcons();

    resultTitle.textContent = type === 'lyrics' ? '🎶 AI 生成歌词' : '📖 AI 生成故事';
    resultContent.innerHTML = '<div class="text-slate-400 italic p-4">正在思考并创作中...</div>';
    resultSection.classList.remove('hidden');
    resultSection.scrollIntoView({ behavior: 'smooth' });

    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ words: currentWords, type })
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('API Response Error:', response.status, errorText);
            throw new Error(`API 返回错误 (${response.status}): ${errorText.substring(0, 50)}`);
        }
        
        const data = await response.json();
        if (data.error) throw new Error(data.error);
        
        // 兼容不同的 JSON 结构
        currentBilingualLines = data.results || data;
        if (!Array.isArray(currentBilingualLines)) {
            currentBilingualLines = [currentBilingualLines];
        }

        isTranslationVisible = true;
        renderResult();
        fillEditableLyrics();
        resetSongFeedback();
        showToast('生成完成！');

    } catch (err) {
        console.error('Full Error Object:', err);
        showToast(err.message || '生成失败，请检查后端服务');
        
        // Fallback to local mock
        if (type === 'lyrics') {
            currentBilingualLines = generateLyrics(currentWords);
        } else {
            currentBilingualLines = generateStory(currentWords);
        }
        renderResult();
        fillEditableLyrics();
        resetSongFeedback();
    } finally {
        activeBtn.innerHTML = originalBtnText;
        lucide.createIcons();
    }
}

function renderResult() {
    resultContent.innerHTML = '';
    
    if (currentType === 'story') {
        // Story mode: continuous paragraphs
        const style = currentPalette[Math.floor(Math.random() * currentPalette.length)]; 
        const storyCard = document.createElement('div');
        storyCard.className = `p-10 rounded-[40px] ${style.bg} border border-white/40 mb-6 shadow-sm relative overflow-hidden`;
        
        const deco = document.createElement('div');
        deco.className = `absolute -top-20 -right-20 w-64 h-64 rounded-full opacity-5 bg-current`;
        storyCard.appendChild(deco);

        const enContent = currentBilingualLines.map(l => l.en).filter(Boolean).join(' ').replace(/\*\*/g, '');
        const zhContent = currentBilingualLines.map(l => l.zh).filter(Boolean).join(' ').replace(/\*\*/g, '');

        const enDiv = document.createElement('div');
        enDiv.className = `text-xl font-bold ${style.text} leading-relaxed relative z-10 whitespace-pre-wrap`;
        enDiv.innerHTML = applyHighlight(enContent, currentWords, false);
        storyCard.appendChild(enDiv);

        if (isTranslationVisible && zhContent) {
            const zhDiv = document.createElement('div');
            zhDiv.className = `mt-6 opacity-70 font-medium text-base border-t border-current/10 pt-6 ${style.text} relative z-10 whitespace-pre-wrap`;
            zhDiv.innerHTML = applyHighlight(zhContent, currentWords, true);
            storyCard.appendChild(zhDiv);
        }
        
        resultContent.appendChild(storyCard);
    } else {
        // Lyrics mode: line by line
        currentBilingualLines.forEach((line, index) => {
            if (!line.en && !line.zh) return;
            
            const style = currentPalette[index % currentPalette.length];
            const lineDiv = document.createElement('div');
            lineDiv.className = `p-8 rounded-[32px] ${style.bg} border border-white/40 mb-6 shadow-sm relative overflow-hidden group transition-all duration-500 hover:shadow-md hover:-translate-y-1`;
            
            const deco = document.createElement('div');
            deco.className = `absolute top-0 right-0 w-32 h-32 -mr-16 -mt-16 rounded-full opacity-10 bg-current`;
            lineDiv.appendChild(deco);

            const enDiv = document.createElement('div');
            enDiv.className = `text-xl font-bold ${style.text} leading-relaxed relative z-10`;
            enDiv.innerHTML = applyHighlight(line.en, currentWords, false);
            lineDiv.appendChild(enDiv);

            if (isTranslationVisible && line.zh) {
                const zhDiv = document.createElement('div');
                zhDiv.className = `mt-4 opacity-70 font-medium text-base border-t border-current/10 pt-4 ${style.text} relative z-10`;
                zhDiv.innerHTML = applyHighlight(line.zh, currentWords, true);
                lineDiv.appendChild(zhDiv);
            }
            
            resultContent.appendChild(lineDiv);
        });
    }
}

const LINE_TRANSLATIONS = {};

function shouldTranslateLine(en) {
    if (!en) return false;
    const t = en.trim();
    if (t.length === 0) return false;
    if (/^\(.*\)$/.test(t)) return false;
    return true;
}

function cleanZh(text) {
    return String(text || '').replace(/\s+/g, ' ').trim();
}

async function translateLinesToZh(lines) {
    const toTranslate = lines.map(l => l.en).filter(shouldTranslateLine);
    if (toTranslate.length === 0) return;

    try {
        const response = await fetch('/api/translate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lines: toTranslate })
        });
        
        if (!response.ok) throw new Error('翻译 API 调用失败');
        
        const translatedLines = await response.json();
        if (translatedLines.error) throw new Error(translatedLines.error);
        
        let transIdx = 0;
        for (const line of lines) {
            if (shouldTranslateLine(line.en)) {
                line.zh = translatedLines[transIdx++] || line.zh;
            }
        }
    } catch (err) {
        console.error(err);
        showToast('翻译失败，请检查后端服务');
    }
}

function generateLyrics(words) {
    const lines = [];
    const unique = [...new Set(words.map(w => String(w)).filter(Boolean))];
    const shuffled = [...unique].sort(() => Math.random() - 0.5);

    const core1 = shuffled[0] || 'WordMelody';
    const core2 = shuffled[1] || core1;
    const core3 = shuffled[2] || core2;
    const core1Zh = getTranslation(core1);
    const core2Zh = getTranslation(core2);
    const core3Zh = getTranslation(core3);

    const remainingPool = shuffled.slice(3);

    const listEn = (arr) => {
        if (arr.length === 1) return arr[0];
        if (arr.length === 2) return `${arr[0]} and ${arr[1]}`;
        return `${arr.slice(0, -1).join(', ')}, and ${arr[arr.length - 1]}`;
    };
    const listZh = (arr) => {
        const zhArr = arr.map(getTranslation);
        if (zhArr.length === 1) return zhArr[0];
        if (zhArr.length === 2) return `${zhArr[0]}和${zhArr[1]}`;
        return `${zhArr.slice(0, -1).join('、')}和${zhArr[zhArr.length - 1]}`;
    };

    const take = (arr, n) => arr.splice(0, Math.min(n, arr.length));
    const clamp = (n, min, max) => Math.max(min, Math.min(max, n));

    const verseLineCount = (n) => {
        if (n <= 8) return 4;
        if (n <= 16) return 5;
        return 6;
    };

    const v1Lines = verseLineCount(remainingPool.length);
    const v2Lines = verseLineCount(Math.max(0, remainingPool.length - v1Lines * 2));

    const v1WordTarget = clamp(v1Lines * 2, 4, 14);
    const v2WordTarget = clamp(v2Lines * 2, 4, 14);

    const v1Words = take(remainingPool, v1WordTarget);
    const v2Words = take(remainingPool, v2WordTarget);

    const bridgeBaseLines = clamp(Math.ceil(remainingPool.length / 4), 6, 8);
    const bridgeCapacity = bridgeBaseLines * 5;
    const bridgeLines = remainingPool.length > bridgeCapacity ? Math.ceil(remainingPool.length / 5) : bridgeBaseLines;

    const chorus = [
        { en: `We run the late-night streets — ${core1}, ${core2}, and ${core3} in our song.`, zh: `我们穿过深夜的街——${core1Zh}、${core2Zh} 和 ${core3Zh} 在我们的歌里。` },
        { en: `Hands on the wheel, city lights repeat — I hear ${core1} between the horns.`, zh: `手握方向盘，霓虹重复——我在喇叭声里听见 ${core1Zh}。` },
        { en: `Say you'll stay when the morning comes; let ${core2} and ${core3} carry us home.`, zh: `天亮时请别走，让 ${core2Zh} 和 ${core3Zh} 带我们回家。` },
        { en: `We run, we run — the hook is your name and ${core1} that keeps me brave.`, zh: `我们一路奔跑——副歌是你的名字，还有让我勇敢的 ${core1Zh}。` }
    ];

    const verseTemplates = [
        { slots: 1, en: (w) => `The station clock was late; ${w} crossed the platform like a thought.`, zh: (w) => `站台的钟走得慢，${getTranslation(w)}像念头一样穿过站台。` },
        { slots: 1, en: (w) => `Under river bridges, ${w} floated past in the echo of our talk.`, zh: (w) => `河下桥洞里，${getTranslation(w)}在我们谈话的回声里漂过去。` },
        { slots: 1, en: (w) => `On your old street, ${w} waited at the corner where we met.`, zh: (w) => `在你旧街的拐角，${getTranslation(w)}像从前一样等着我们。` },
        { slots: 2, en: (a, b) => `We traded small jokes until ${a} slipped in and turned to ${b}.`, zh: (a, b) => `我们交换小笑话，直到 ${getTranslation(a)} 混进来，慢慢变成了 ${getTranslation(b)}。` },
        { slots: 2, en: (a, b) => `By the pier, ${a} touched the wind and ${b} answered in the waves.`, zh: (a, b) => `在码头，${getTranslation(a)}贴着风，${getTranslation(b)}在浪里回应。` },
        { slots: 2, en: (a, b) => `The hallway smelled of rain; ${a} found a seat and ${b} took the window.`, zh: (a, b) => `走廊有雨味，${getTranslation(a)}坐了内侧，${getTranslation(b)}靠了窗。` }
    ];

    const bridgeTemplates = [
        { en: (g) => `The city leaned toward midnight; ${listEn(g)} pulled the story to a turn.`, zh: (g) => `城市靠近午夜，${listZh(g)}把故事拉向拐点。` },
        { en: (g) => `We crossed the empty square, and ${listEn(g)} finally felt like a reason.`, zh: (g) => `我们穿过空旷的广场，${listZh(g)}终于像一个理由。` },
        { en: (g) => `Your voice softened; ${listEn(g)} opened the door we never tried before.`, zh: (g) => `你的声音低下来，${listZh(g)}打开我们从未试过的那扇门。` },
        { en: (g) => `Taxi lights blurred; ${listEn(g)} stitched the road into one bright line.`, zh: (g) => `出租车灯影散开，${listZh(g)}把路缝成一条亮线。` },
        { en: (g) => `We stood by the river; ${listEn(g)} made silence useful for once.`, zh: (g) => `我们站在河边，${listZh(g)}让沉默第一次变得有用。` },
        { en: (g) => `I watched your shadow turn; ${listEn(g)} found the space between goodbye and stay.`, zh: (g) => `我看你的影子转身，${listZh(g)}找到“再见”和“别走”之间的空隙。` },
        { en: (g) => `Somewhere a song began; ${listEn(g)} carried the note I couldn't reach.`, zh: (g) => `不知哪儿响起一首歌，${listZh(g)}托起我够不着的那一拍。` },
        { en: (g) => `We let the night decide; ${listEn(g)} turned a small promise into dawn.`, zh: (g) => `我们把决定交给夜色，${listZh(g)}把一个小承诺变成了清晨。` }
    ];

    const buildVerse = (titleEn, titleZh, desiredLines, wordList) => {
        lines.push({ en: titleEn, zh: titleZh });
        let i = 0;
        while (lines.length && i < desiredLines) {
            const remaining = wordList.length;
            const useTwo = remaining >= 2 && Math.random() < 0.65;
            if (useTwo) {
                const [a, b] = wordList.splice(0, 2);
                const tpls = verseTemplates.filter(t => t.slots === 2);
                const tpl = tpls[Math.floor(Math.random() * tpls.length)];
                lines.push({ en: tpl.en(a, b), zh: tpl.zh(a, b) });
            } else if (remaining >= 1) {
                const [w] = wordList.splice(0, 1);
                const tpls = verseTemplates.filter(t => t.slots === 1);
                const tpl = tpls[Math.floor(Math.random() * tpls.length)];
                lines.push({ en: tpl.en(w), zh: tpl.zh(w) });
            } else {
                break;
            }
            i++;
        }
        while (i < desiredLines) {
            lines.push({ en: `The night kept moving, and ${core1} stayed on my tongue.`, zh: `夜色一直往前走，${core1Zh}却停在我唇边。` });
            i++;
        }
        lines.push({ en: "", zh: "" });
    };

    buildVerse("(Verse 1)", "(主歌 1)", v1Lines, v1Words);

    lines.push({ en: "(Chorus)", zh: "(副歌)" });
    chorus.forEach(l => lines.push(l));
    lines.push({ en: "", zh: "" });

    buildVerse("(Verse 2)", "(主歌 2)", v2Lines, v2Words);

    lines.push({ en: "(Chorus)", zh: "(副歌)" });
    chorus.forEach(l => lines.push(l));
    lines.push({ en: "", zh: "" });

    lines.push({ en: "(Bridge)", zh: "(桥段)" });
    const bridgeWords = [...remainingPool];
    if (bridgeWords.length === 0) {
        const fallbackGroups = [
            [core1, core2, core3],
            [core2, core3, core1],
            [core3, core1, core2],
            [core1, core2, core3]
        ];
        for (let i = 0; i < 6; i++) {
            const g = fallbackGroups[i % fallbackGroups.length];
            const tpl = bridgeTemplates[i % bridgeTemplates.length];
            lines.push({ en: tpl.en(g), zh: tpl.zh(g) });
        }
    } else {
        const groups = [];
        let remainingLines = clamp(bridgeLines, 6, Math.max(8, bridgeLines));
        while (bridgeWords.length > 0) {
            const target = Math.ceil(bridgeWords.length / remainingLines);
            const size = clamp(target, 3, 5);
            groups.push(bridgeWords.splice(0, size));
            remainingLines = Math.max(1, remainingLines - 1);
        }
        const finalLineCount = clamp(groups.length, 6, 8);
        while (groups.length < finalLineCount) {
            const extra = groups[groups.length - 1] || [core1, core2, core3];
            groups.push(extra.slice(0, Math.min(5, extra.length)));
        }
        if (groups.length > 8) {
            const overflow = groups.splice(8);
            const flattened = overflow.flat();
            while (flattened.length > 0) {
                groups[7].push(...flattened.splice(0, Math.max(0, 5 - groups[7].length)));
                if (groups[7].length >= 5) break;
            }
        }
        for (let i = 0; i < groups.length; i++) {
            const tpl = bridgeTemplates[i % bridgeTemplates.length];
            lines.push({ en: tpl.en(groups[i]), zh: tpl.zh(groups[i]) });
        }
    }
    lines.push({ en: "", zh: "" });

    lines.push({ en: "(Chorus)", zh: "(副歌)" });
    chorus.forEach(l => lines.push(l));

    const used = new Set();
    for (const l of lines) {
        if (!l.en) continue;
        for (const w of unique) {
            const re = new RegExp(`\\b${w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i');
            if (re.test(l.en)) used.add(w);
        }
    }
    const missing = unique.filter(w => !used.has(w));
    if (missing.length > 0) {
        const insertAt = lines.findIndex(l => l.en === "(Bridge)");
        const bridgeInsertStart = insertAt >= 0 ? insertAt + 1 : 0;
        const groups = [];
        const poolCopy = [...missing];
        let remainingLines = 6;
        while (poolCopy.length > 0) {
            const target = Math.ceil(poolCopy.length / remainingLines);
            const size = clamp(target, 1, 5);
            groups.push(poolCopy.splice(0, size));
            remainingLines = Math.max(1, remainingLines - 1);
        }
        const extraLines = groups.map((g, i) => {
            const tpl = bridgeTemplates[i % bridgeTemplates.length];
            return { en: tpl.en(g), zh: tpl.zh(g) };
        });
        lines.splice(bridgeInsertStart, 0, ...extraLines, { en: "", zh: "" });
    }

    return lines;
}

function generateStory(words) {
    const lines = [];
    const pool = [...words].sort(() => Math.random() - 0.5);
    const next = () => pool.shift();

    const w1 = next();
    const w2 = next();
    const w3 = next();

    lines.push({ en: "It started on a late evening when the air smelled like rain on warm pavement.", zh: "故事开始在一个深夜，空气里有雨落在热地面的味道。" });
    if (w1) lines.push({ en: `I heard ${w1} in my head like a tiny bell, clear and stubborn.`, zh: `我脑海里响起了 ${getTranslation(w1)}，像一枚小铃铛，清晰又倔强。` });
    if (w2) lines.push({ en: `On the bus window, I wrote ${w2} with my fingertip and watched the fog swallow it.`, zh: `在公交车窗上，我用指尖写下 ${getTranslation(w2)}，看雾气把它吞没。` });
    lines.push({ en: "", zh: "" });

    lines.push({ en: "Outside, streetlights buzzed and a dog barked twice, then went quiet.", zh: "街灯发出嗡嗡声，一只狗叫了两声，又安静下来。" });
    if (w3) lines.push({ en: `A stranger handed me a paper cup of hot tea and said, \"Remember ${w3}.\"`, zh: `一个陌生人递给我一杯热茶，说：“记住 ${getTranslation(w3)}。”` });

    let i = 0;
    const sensoryTemplates = [
        { en: "The lid warmed my palms; I repeated ${w} softly until it sounded like a lyric.", zh: "杯盖暖着掌心，我轻声重复 ${w}，直到它像一句歌词。" },
        { en: "Wind tugged at my sleeve; ${w} slipped out between my teeth like a secret.", zh: "风扯着我的袖口，${w} 像秘密一样从齿间溜出来。" },
        { en: "Somewhere far, a train horn sighed; ${w} fell into that sound and stayed there.", zh: "远处火车鸣笛一声叹息，${w} 掉进那声音里，停在那里。" },
        { en: "I touched the cold metal pole and felt my heartbeat slow; ${w} suddenly made sense.", zh: "我摸到冰凉的扶手，心跳慢了下来；${w} 突然变得明白。" }
    ];

    while (pool.length > 0) {
        const w = next();
        const tpl = sensoryTemplates[i % sensoryTemplates.length];
        lines.push({ en: tpl.en.replace('${w}', w), zh: tpl.zh.replace('${w}', getTranslation(w)) });
        i++;
    }

    lines.push({ en: "", zh: "" });
    lines.push({ en: "When I got home, I turned on a small lamp and smiled.", zh: "回到家后，我打开一盏小灯，笑了。" });
    lines.push({ en: "Those words didn't feel like homework anymore — they felt like a scene I could step into.", zh: "那些词不再像作业——更像一幅我可以走进去的画面。" });

    return lines;
}

// Event Listeners
btnGenLyrics.addEventListener('click', () => generateAIContent('lyrics'));
btnGenStory.addEventListener('click', () => generateAIContent('story'));

btnCopyLyrics.addEventListener('click', async () => {
    const content = getOriginalLyricsText();
    try {
        await navigator.clipboard.writeText(content);
        showToast('已复制到剪贴板');
    } catch (err) {
        showToast('复制失败');
    }
});

btnShareImage.addEventListener('click', async () => {
    if (!currentBilingualLines.length) return;
    
    showToast('正在生成精致分享图...');
    
    const shareWrapper = document.createElement('div');
    // Using a more elegant background for the share image
    shareWrapper.className = 'p-12 bg-[#fcfcfc] w-[800px] absolute -left-[9999px]';
    shareWrapper.style.fontFamily = "'Inter', sans-serif";
    
    // Add Logo/Header
    const header = document.createElement('div');
    header.className = 'mb-12 flex flex-col items-center text-center';
    header.innerHTML = `
        <div class="w-16 h-16 bg-pink-100 rounded-2xl flex items-center justify-center mb-4 shadow-sm">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#ec4899" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>
        </div>
        <h1 class="text-4xl font-extrabold text-slate-800 tracking-tight mb-2">WordMelody</h1>
        <p class="text-slate-400 text-lg font-medium italic">Memory transformed into music</p>
        <div class="mt-6 px-6 py-2 bg-slate-100 rounded-full text-slate-500 font-bold text-sm tracking-widest uppercase">
            ${resultTitle.textContent.replace('AI ', '')}
        </div>
    `;
    shareWrapper.appendChild(header);
    
    const contentClone = resultContent.cloneNode(true);
    contentClone.classList.remove('max-h-[60vh]', 'overflow-y-auto');
    shareWrapper.appendChild(contentClone);
    
    const footer = document.createElement('div');
    footer.className = 'mt-16 pt-10 border-t border-slate-100 flex flex-col items-center gap-4';
    footer.innerHTML = `
        <div class="flex gap-2">
            ${currentWords.slice(0, 8).map(w => `<span class="px-3 py-1 bg-white border border-slate-100 rounded-lg text-xs text-slate-400">${w}</span>`).join('')}
            ${currentWords.length > 8 ? '<span class="text-xs text-slate-300">...</span>' : ''}
        </div>
        <p class="text-slate-300 text-sm font-medium tracking-wide">Created with WordMelody AI Assistant</p>
    `;
    shareWrapper.appendChild(footer);
    
    document.body.appendChild(shareWrapper);
    
    try {
        const canvas = await html2canvas(shareWrapper, {
            backgroundColor: '#fcfcfc',
            scale: 2,
            useCORS: true,
            logging: false,
            windowWidth: 800
        });
        
        const link = document.createElement('a');
        link.download = `WordMelody-Share-${new Date().getTime()}.png`;
        link.href = canvas.toDataURL('image/png');
        link.click();
        showToast('分享图片已保存');
    } catch (err) {
        console.error('Share image error:', err);
        showToast('生成失败');
    } finally {
        document.body.removeChild(shareWrapper);
    }
});

btnTranslate.addEventListener('click', async () => {
    isTranslationVisible = !isTranslationVisible;
    if (isTranslationVisible) {
        showToast('正在优化翻译...');
        try {
            await translateLinesToZh(currentBilingualLines);
        } catch (_) {}
    }
    renderResult();
    btnTranslate.innerHTML = isTranslationVisible 
        ? '<i data-lucide="eye-off" class="w-4 h-4"></i> 隐藏翻译' 
        : '<i data-lucide="languages" class="w-4 h-4"></i> 翻译内容';
    lucide.createIcons();
    showToast(isTranslationVisible ? '对照翻译已开启' : '对照翻译已关闭');
});

btnToSuno.addEventListener('click', async () => {
    await generateSongFromLyrics(editableLyrics.value, 'pop');
});

btnUseManualUrl.addEventListener('click', () => {
    const url = manualAudioUrlInput.value.trim();
    if (!url) {
        showToast('请输入音频链接');
        return;
    }
    showSongSuccessState(url);
    showToast('已加载手动输入的音频');
});

btnRetrySong.addEventListener('click', async () => {
    if (!lastSongRequest) {
        await generateSongFromLyrics(editableLyrics.value, 'pop');
        return;
    }
    await generateSongFromLyrics(lastSongRequest.lyrics, lastSongRequest.style || 'pop');
});
