// Словарь локализации
const i18n = {
  ru: {
    title: "⚙️ Настройки QwenTTS",
    btn_guide: "🎓 Интерактивное руководство",
    tab_settings: "Настройки и Модели",
    tab_voices: "Менеджер Голосов",
    tab_voice_design: "Дизайн Голосов",
    section_backend_title: "Вычислительный бэкенд",
    section_backend_desc: "Выберите бэкенд для вычислений. Переключение требует перезагрузки моделей (5–30 сек).",
    btn_apply_backend: "Применить бэкенд",
    status_ready: "Готов",
    status_not_built: "Не скомпилирован",
    section_params_title: "Параметры синтеза",
    section_params_desc: "Основные настройки генерации, влияющие на качество и характер голоса.",
    subtalker_collapsible: "Дополнительно: Параметры Code Predictor (Sub-Talker)",
    btn_save_settings: "Сохранить настройки",
    section_models_title: "Модели",
    btn_refresh: "↻ Обновить",
    talker_lm_title: "Talker LM (Языковая модель)",
    talker_lm_desc: "Языковая модель, которая генерирует коды речи из текста.",
    audio_codec_title: "Аудио кодек",
    audio_codec_desc: "Декодер, который восстанавливает WAV аудио из кодов речи.",
    btn_apply_models: "Применить модели",
    requires_reload_hint: "Требуется перезагрузка бэкенда (5–30 сек)",
    download_hf_title: "Скачать с HuggingFace",
    download_hf_desc: "Скачать дополнительные GGUF-модели.",
    import_skyrimnet_title: "Импорт голосов из SkyrimNet",
    import_skyrimnet_desc: "Сканировать запущенный сервер SkyrimNet для автоматического заполнения базы voice_refs.json. <br><br><strong style='color:var(--accent-color);'>⚠️ Перед запуском импорта обязательно выберите правильный язык в поле Language во вкладке настроек (например, russian). Иначе эталонные аудио будут записаны не в ту папку языка!</strong>",
    import_skyrimnet_design_title: "Импорт голосов для Voice Design из SkyrimNet",
    import_skyrimnet_design_desc: "Сканировать запущенный сервер SkyrimNet для регистрации дизайнов голосов с текстовыми описаниями (без скачивания файлов).",
    import_url_label: "Адрес SkyrimNet:",
    import_mode_label: "Режим выбора:",
    import_preserve_label: " Сохранять существующие записи (Безопасно)",
    import_force_label: " Перезаписывать файлы",
    btn_start_import: "Начать синхронизацию",
    add_voice_title: "Добавить новый голос вручную",
    add_voice_desc: "Создать запись в базе данных. WAV-файл должен физически находиться в папке speakers.",
    add_voice_design_title: "Добавить новый дизайн голоса вручную",
    add_voice_design_desc: "Создать запись для Voice Design. Укажите описание голоса вместо пути к файлу.",
    new_voice_key_label: "Имя спикера / Ключ:",
    new_voice_audio_label: "Путь к эталону WAV:",
    new_voice_design_instruct_label: "Описание голоса (атрибуты):",
    new_voice_design_instruct_tip: "Описание характера голоса через запятую, например: male, young adult, moderate pitch",
    new_voice_text_label: "Текст реплики (Точное соответствие):",
    btn_add_voice: "Добавить голос",
    registered_voices_title: "База зарегистрированных голосов (voice_refs.json)",
    registered_design_voices_title: "База зарегистрированных дизайнов голосов (voice_refs.json)",
    search_placeholder: "Поиск голосов...",
    btn_reload: "↻ Обновить список",
    th_speaker_key: "Ключ спикера",
    th_wav_path: "Путь к WAV",
    th_voice_description: "Описание голоса",
    th_transcript: "Текст реплики (Точный транскрипт)",
    th_actions: "Действия",
    btn_play: "▶ Слушать",
    btn_save: "Сохранить",
    btn_delete: "Удалить",
    voice_key_tip: "Уникальный ID спикера, например malebrute",
    voice_audio_tip: "Путь к файлу WAV относительно корня проекта",
    voice_text_tip: "Точный текст, произнесенный в аудиофайле.",
    alert_play_err: "Не удалось воспроизвести аудио. Убедитесь, что WAV файл существует на диске.",
    alert_saved: "Голос \"{key}\" успешно сохранен.",
    alert_save_err: "Ошибка сохранения голоса: ",
    alert_delete_confirm: "Вы уверены, что хотите удалить голос \"{key}\"?",
    alert_delete_err: "Ошибка удаления голоса: ",
    alert_add_empty: "Пожалуйста, заполните все поля для добавления голоса.",
    alert_added: "Голос \"{key}\" успешно добавлен.",
    alert_add_err: "Ошибка добавления голоса: ",
    no_voices_found: "Голоса не найдены.",
    import_starting: "Запуск импорта...\n",
    now_playing: "Воспроизведение:",
    label_preview_text: "Текст для прослушивания:"
  },
  en: {
    title: "⚙️ QwenTTS Settings",
    btn_guide: "🎓 Interactive Guide",
    tab_settings: "Settings & Models",
    tab_voices: "Voices Manager",
    tab_voice_design: "Voices Design",
    section_backend_title: "Compute Backend",
    section_backend_desc: "Select the compute backend. Switching requires a model reload (5–30 s).",
    btn_apply_backend: "Apply Backend",
    status_ready: "Ready",
    status_not_built: "Not built",
    section_params_title: "Synthesis Parameters",
    section_params_desc: "Core sampling settings that control voice output quality and behaviour.",
    subtalker_collapsible: "Advanced: Code Predictor (Sub-Talker) Parameters",
    btn_save_settings: "Save Settings",
    section_models_title: "Models",
    btn_refresh: "↻ Refresh",
    talker_lm_title: "Talker LM",
    talker_lm_desc: "The language model that generates speech tokens.",
    audio_codec_title: "Audio Codec",
    audio_codec_desc: "The tokenizer that converts audio codes to waveform.",
    btn_apply_models: "Apply Models",
    requires_reload_hint: "Requires backend reload (5–30 s)",
    download_hf_title: "Download from HuggingFace",
    download_hf_desc: "Download additional GGUF models.",
    import_skyrimnet_title: "Import Voices from SkyrimNet",
    import_skyrimnet_desc: "Scan a running SkyrimNet server to automatically download reference voice WAVs. <br><br><strong style='color:var(--accent-color);'>⚠️ Before starting the import, make sure to select the correct language in the 'Language' parameter on the settings tab (e.g. 'russian'). Otherwise, voice files will be exported to the wrong language directory!</strong>",
    import_skyrimnet_design_title: "Import Voices from SkyrimNet (Voice Design)",
    import_skyrimnet_design_desc: "Scan a running SkyrimNet server to register design voices with default gender attributes (without downloading files).",
    import_url_label: "SkyrimNet URL:",
    import_mode_label: "Selection Mode:",
    import_preserve_label: " Preserve existing entries (Safe)",
    import_force_label: " Overwrite files",
    btn_start_import: "Start Synchronization",
    add_voice_title: "Add new voice manually",
    add_voice_desc: "Create database record. The WAV file must physically exist in the speakers folder.",
    add_voice_design_title: "Add New Voice Reference Manually (Voice Design)",
    add_voice_design_desc: "Create a new voice reference for Voice Design. Enter attributes/description instead of a WAV path.",
    new_voice_key_label: "Speaker Name / Key:",
    new_voice_audio_label: "WAV Reference Path:",
    new_voice_design_instruct_label: "Voice Description:",
    new_voice_design_instruct_tip: "Voice attributes comma-separated, e.g. male, young adult, moderate pitch",
    new_voice_text_label: "Transcript text (Exact match):",
    btn_add_voice: "Add Voice",
    registered_voices_title: "Registered Voices Database (voice_refs.json)",
    registered_design_voices_title: "Registered Design Voices Database",
    search_placeholder: "Search voices...",
    btn_reload: "↻ Refresh List",
    th_speaker_key: "Speaker Key",
    th_wav_path: "WAV Path",
    th_voice_description: "Voice Description",
    th_transcript: "Transcript text (Exact transcript)",
    th_actions: "Actions",
    btn_play: "▶ Play",
    btn_save: "Save",
    btn_delete: "Delete",
    voice_key_tip: "Unique speaker ID, e.g. malebrute",
    voice_audio_tip: "Path to WAV file relative to the project root",
    voice_text_tip: "Exact text spoken in the audio file.",
    alert_play_err: "Failed to play audio. Make sure the WAV file exists on disk.",
    alert_saved: "Voice \"{key}\" saved successfully.",
    alert_save_err: "Error saving voice: ",
    alert_delete_confirm: "Are you sure you want to delete voice \"{key}\"?",
    alert_delete_err: "Error deleting voice: ",
    alert_add_empty: "Please fill in all fields to add a voice.",
    alert_added: "Voice \"{key}\" added successfully.",
    alert_add_err: "Error adding voice: ",
    no_voices_found: "No voices found.",
    import_starting: "Starting import...\n",
    now_playing: "Now playing:",
    label_preview_text: "Preview Text:"
  }
};

const tutorialStepsI18n = {
  ru: [
    { title: "🚀 Добро пожаловать в Qwen3-TTS!", target: null, onShow: () => switchTab('settings'), content: "Этот интерактивный гид поможет вам быстро настроить <strong>Qwen3-TTS SkyrimNet Adapter</strong>.<br><br>QwenTTS — это передовая нейросетевая модель генерации речи с клонированием голоса на лету (In-Context Learning)." },
    { title: "⚙️ Выбор вычислительного бэкенда (Backend)", target: "section-backend", onShow: () => switchTab('settings'), content: "Бэкенд определяет, на каком оборудовании выполняются расчеты нейросети (CPU, CUDA или Vulkan). CUDA (для карт NVIDIA) крайне рекомендуется для быстрой работы." },
    { title: "🧠 Модели Talker LM и Codec", target: "section-models", onShow: () => switchTab('settings'), content: "Синтез речи QwenTTS основан на языковой модели Talker LM и декодере Audio Codec. Выберите нужные GGUF файлы и примените их." },
    { title: "🎛️ Параметры генерации", target: "section-params", onShow: () => switchTab('settings'), content: "Регуляторы характера звучания голоса: Seed (зерно для повторяемости), Temperature (выразительность/стабильность) и Repetition Penalty." },
    { title: "👥 Менеджер голосов", target: "tab-voices", onShow: () => switchTab('voices'), content: "Здесь вы синхронизируете базу с сервером SkyrimNet. База автоматически наполнится записями для точного клонирования голосов NPC.<br><br><strong>⚠️ ВАЖНО: Перед запуском импорта обязательно выберите правильный язык в поле Language во вкладке настроек (например, russian). Иначе эталонные аудио будут записаны не в ту папку языка!</strong>" }
  ],
  en: [
    { title: "🚀 Welcome to Qwen3-TTS!", target: null, onShow: () => switchTab('settings'), content: "This interactive guide will help you configure the <strong>Qwen3-TTS SkyrimNet Adapter</strong>." },
    { title: "⚙️ Select Compute Backend", target: "section-backend", onShow: () => switchTab('settings'), content: "Choose between CPU, CUDA (NVIDIA), or Vulkan. CUDA is highly recommended for real-time synthesis." },
    { title: "🧠 Talker LM & Codec Models", target: "section-models", onShow: () => switchTab('settings'), content: "Select your active language model and acoustic codec architecture, then click Apply Models." },
    { title: "🎛️ Sampling parameters", target: "section-params", onShow: () => switchTab('settings'), content: "Tweak Seed, Temperature, and Repetition settings to adjust vocal stability and emotional diversity." },
    { title: "👥 Voices Manager", target: "tab-voices", onShow: () => switchTab('voices'), content: "Sync and download reference audio data from a running SkyrimNet node to automatically build cloning mappings.<br><br><strong>⚠️ IMPORTANT: Before starting the import, make sure to select the correct language in the 'Language' parameter on the settings tab (e.g. 'russian'). Otherwise, voice files will be exported to the wrong language directory!</strong>" }
  ]
};

let currentLang = localStorage.getItem('qwentts_site_lang') || (navigator.language.startsWith('ru') ? 'ru' : 'en');

function applyTranslations() {
  const dict = i18n[currentLang] || i18n.en;
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (dict[key]) el.innerHTML = dict[key];
  });
  document.querySelectorAll('[data-i18n-tip]').forEach(el => {
    const key = el.getAttribute('data-i18n-tip');
    if (dict[key]) el.setAttribute('data-tip', dict[key]);
  });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    if (dict[key]) el.setAttribute('placeholder', dict[key]);
  });
  document.querySelectorAll('[data-i18n-status]').forEach(el => {
    const status = el.getAttribute('data-i18n-status');
    el.textContent = status === 'ready' ? (dict['status_ready'] || 'Ready') : (dict['status_not_built'] || 'Not built');
  });
  const previewTextInput = document.getElementById('design-preview-text');
  if (previewTextInput) {
    const isRussian = currentLang === 'ru';
    if (previewTextInput.value === "Привет! Это проверка синтеза речи в режиме дизайна голоса." || 
        previewTextInput.value === "Hello! This is a speech synthesis test in voice design mode.") {
      previewTextInput.value = isRussian 
        ? "Привет! Это проверка синтеза речи в режиме дизайна голоса." 
        : "Hello! This is a speech synthesis test in voice design mode.";
    }
  }
  if (typeof tutorialSteps !== 'undefined') {
    const tSteps = tutorialStepsI18n[currentLang] || tutorialStepsI18n.en;
    for (let i = 0; i < tutorialSteps.length; i++) {
      if (tSteps[i]) {
        tutorialSteps[i].title = tSteps[i].title;
        tutorialSteps[i].content = tSteps[i].content;
      }
    }
  }
}

function changeSiteLang(lang) {
  currentLang = lang;
  localStorage.setItem('qwentts_site_lang', lang);
  applyTranslations();
  loadVoices();
  loadDesignVoices();
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('lang-select').value = currentLang;
  applyTranslations();
});

async function postJson(url, payload) {
  const r = await fetch(url, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload || {})
  });
  const d = await r.json();
  if (!r.ok) throw new Error(d.detail || d.error || 'Request failed');
  return d;
}

function showMessage(id, text, type) {
  const msg = document.getElementById(id);
  msg.textContent = text;
  msg.className = 'message ' + type;
  setTimeout(() => { msg.className = 'message'; msg.textContent = ''; }, 8000);
}

// Переключение вкладок
function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.id === 'btn-' + tabId);
  });
  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.toggle('active-content', content.id === 'tab-' + tabId);
  });
}

// Изменение бэкенда
document.getElementById('backend-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const selected = document.querySelector('input[name="backend"]:checked');
  if (!selected) return;
  showMessage('backend-message', 'Switching backend, please wait...', 'info');
  try {
    const d = await postJson('/settings/api/set-backend', {backend: selected.value});
    showMessage('backend-message', 'Backend switched to ' + d.backend + '. Reloading...', 'ok');
    setTimeout(() => location.reload(), 1500);
  } catch (err) {
    showMessage('backend-message', 'Error: ' + err.message, 'err');
  }
});

// Сохранение настроек
document.getElementById('settings-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const payload = {};
  for (const [k, v] of fd) {
    if (v === 'on') payload[k] = true;
    else if (v === 'off') payload[k] = false;
    else if (!isNaN(Number(v)) && v !== '') payload[k] = Number(v);
    else payload[k] = v;
  }
  ['do_sample','subtalker_do_sample','use_fa','clamp_fp16','append_ending_pause','debug_save_text'].forEach(k => {
    if (!(k in payload)) payload[k] = false;
  });
  try {
    await postJson('/settings/api/update', payload);
    showMessage('settings-message', 'Settings saved successfully.', 'ok');
  } catch (err) {
    showMessage('settings-message', 'Error: ' + err.message, 'err');
  }
});

// Спойлер суб-талкера
const subToggle = document.getElementById('subtalker-toggle');
const subContent = document.getElementById('subtalker-content');
subToggle.addEventListener('click', () => {
  subToggle.classList.toggle('open');
  subContent.classList.toggle('open');
});

// Применение моделей
document.getElementById('apply-models-btn').addEventListener('click', async () => {
  const talkerRadio = document.querySelector('input[name="talker_model"]:checked');
  const codecRadio = document.querySelector('input[name="codec_model"]:checked');
  if (!talkerRadio || !codecRadio) return;
  showMessage('model-message', 'Applying models, please wait...', 'info');
  try {
    await postJson('/models/api/select', {name: talkerRadio.getAttribute('data-name'), kind: 'talker'});
    await postJson('/models/api/select', {name: codecRadio.getAttribute('data-name'), kind: 'codec'});
    const backendRadio = document.querySelector('input[name="backend"]:checked');
    if (backendRadio) {
      await postJson('/settings/api/set-backend', {backend: backendRadio.value});
    }
    showMessage('model-message', 'Models applied and backend reloaded.', 'ok');
    setTimeout(() => location.reload(), 2000);
  } catch (err) {
    showMessage('model-message', 'Error: ' + err.message, 'err');
  }
});

// Загрузка удаленных моделей HuggingFace
(async function() {
  try {
    const d = await fetch('/models/api/list').then(r => r.json());
    const div = document.getElementById('hf-models');
    let html = '';
    if (d.remote && d.remote.length) {
      d.remote.forEach(m => {
        const sizeStr = m.size_bytes ? ' (' + (m.size_bytes / 1e9).toFixed(1) + ' GB)' : '';
        html += `<div style="display:flex; justify-content:space-between; align-items:center; padding:10px; border-bottom:1px solid var(--border-color);">
          <span style="font-family:monospace; font-size:13px;">${m.name}${sizeStr}</span>
          <button onclick="downloadModel('${m.download_url}','${m.name}')" style="padding:4px 12px; font-size:12px;">Download</button>
        </div>`;
      });
    } else {
      html = '<p style="color:var(--text-muted);font-size:14px;">No remote models found.</p>';
    }
    div.innerHTML = html;
  } catch(e) {
    document.getElementById('hf-models').innerHTML = '<p style="color:var(--danger);font-size:14px;">Failed to load model list.</p>';
  }
})();

function downloadModel(url, name) {
  showMessage('download-message', 'Downloading ' + name + '...', 'info');
  fetch('/models/api/download', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({url, name})
  })
  .then(r => r.json())
  .then(d => {
    if (d.success) showMessage('download-message', 'Downloaded ' + name + '. Refresh page.', 'ok');
    else showMessage('download-message', 'Download failed: ' + (d.error || 'unknown'), 'err');
  })
  .catch(e => showMessage('download-message', 'Download error: ' + e.message, 'err'));
}

// Воспроизведение аудио с фиксацией в нижнем плеере
let currentAudio = null;
function playAudio(path) {
  if (!path) return;
  
  const dict = i18n[currentLang] || i18n.en;
  const playerBar = document.getElementById('footer-audio-player');
  const pathEl = document.getElementById('player-file-path');
  const audioEl = document.getElementById('player-audio-element');
  
  if (pathEl) pathEl.textContent = path;
  if (playerBar) playerBar.style.display = 'flex';
  
  if (audioEl) {
    audioEl.src = `/voices/api/play?path=${encodeURIComponent(path)}`;
    audioEl.play().catch(err => {
      alert(dict.alert_play_err || "Could not play audio. Make sure the WAV file exists on disk.");
    });
    currentAudio = audioEl;
  } else {
    if (currentAudio) currentAudio.pause();
    currentAudio = new Audio(`/voices/api/play?path=${encodeURIComponent(path)}`);
    currentAudio.play().catch(err => {
      alert(dict.alert_play_err || "Could not play audio. Make sure the WAV file exists on disk.");
    });
  }
}

// Загрузка голосов
async function loadVoices() {
  try {
    const list = await fetch('/voices/api/list').then(r => r.json());
    const tableBody = document.getElementById('voice-table-body');
    let html = '';
    const customList = list.custom || {};
    const keys = Object.keys(customList).sort();
    const dict = i18n[currentLang] || i18n.en;
    
    if (keys.length === 0) {
      html = `<tr><td colspan="4" style="text-align:center; color:var(--text-muted); padding:20px;">${dict.no_voices_found}</td></tr>`;
    } else {
      keys.forEach(key => {
        const v = customList[key];
        const safeAudioPath = (v.ref_audio || '').replace(/\\/g, '/');
        html += `
          <tr id="row-${key}">
            <td style="font-weight:600; color:var(--accent);">${key}</td>
            <td><input type="text" id="audio-${key}" value="${v.ref_audio || ''}"></td>
            <td><textarea id="text-${key}">${v.ref_text || ''}</textarea></td>
            <td>
              <div class="actions-cell">
                <button class="action-btn play" onclick="playAudio('${safeAudioPath}')">${dict.btn_play}</button>
                <button class="action-btn primary" onclick="saveVoice('${key}')">${dict.btn_save}</button>
                <button class="action-btn danger" onclick="deleteVoice('${key}')">${dict.btn_delete}</button>
              </div>
            </td>
          </tr>
        `;
      });
    }
    tableBody.innerHTML = html;
  } catch (err) { console.error(err); }
}

async function saveVoice(key) {
  const ref_audio = document.getElementById(`audio-${key}`).value.trim();
  const ref_text = document.getElementById(`text-${key}`).value.trim();
  const dict = i18n[currentLang] || i18n.en;
  try {
    await postJson('/voices/api/save', { key, ref_audio, ref_text, db_type: 'custom' });
    alert((dict.alert_saved || 'Saved.').replace('{key}', key));
  } catch (err) { alert(dict.alert_save_err + err.message); }
}

async function deleteVoice(key) {
  const dict = i18n[currentLang] || i18n.en;
  if (!confirm((dict.alert_delete_confirm || 'Delete?').replace('{key}', key))) return;
  try {
    await postJson('/voices/api/delete', { key, db_type: 'custom' });
    const row = document.getElementById(`row-${key}`);
    if (row) row.remove();
  } catch (err) { alert(dict.alert_delete_err + err.message); }
}

async function addVoice(e) {
  e.preventDefault();
  const key = document.getElementById('new-voice-key').value.trim();
  const ref_audio = document.getElementById('new-voice-audio').value.trim();
  const ref_text = document.getElementById('new-voice-text').value.trim();
  const dict = i18n[currentLang] || i18n.en;
  try {
    await postJson('/voices/api/save', { key, ref_audio, ref_text, db_type: 'custom' });
    document.getElementById('add-voice-form').reset();
    await loadVoices();
    alert((dict.alert_added || 'Added.').replace('{key}', key));
  } catch (err) { alert(dict.alert_add_err + err.message); }
}

// Импорт SkyrimNet
let importInterval = null;
async function startImport(e) {
  e.preventDefault();
  const consoleEl = document.getElementById('import-console');
  consoleEl.style.display = 'block';
  consoleEl.textContent = "Starting import...\n";

  const progContainer = document.getElementById('import-progress-container');
  if (progContainer) {
    progContainer.style.display = 'block';
    document.getElementById('import-progress-bar').style.width = '0%';
    document.getElementById('import-progress-percentage').textContent = '0%';
    document.getElementById('import-progress-status').textContent = (currentLang === 'ru') ? 'Подготовка...' : 'Preparing...';
    document.getElementById('import-progress-counts').textContent = (currentLang === 'ru') ? 'Обработано: 0 из 0' : 'Processed: 0 / 0';
    document.getElementById('import-progress-remaining').textContent = (currentLang === 'ru') ? 'Осталось: 0' : 'Remaining: 0';
  }

  try {
    await postJson('/voices/api/import', {
      base_url: document.getElementById('import-url').value.trim(),
      selection_mode: document.getElementById('import-mode').value,
      force: document.getElementById('import-force').checked,
      preserve_existing: document.getElementById('import-preserve').checked
    });
    if (importInterval) clearInterval(importInterval);
    importInterval = setInterval(pollImportStatus, 1000);
  } catch (err) { consoleEl.textContent += "Error: " + err.message + "\n"; }
}

async function pollImportStatus() {
  try {
    const res = await fetch('/voices/api/import/status').then(r => r.json());
    const consoleEl = document.getElementById('import-console');
    if (res.log) { consoleEl.textContent = res.log; consoleEl.scrollTop = consoleEl.scrollHeight; }

    if (res.total > 0) {
      const processed = res.processed || 0;
      const total = res.total;
      const remaining = Math.max(0, total - processed);
      const percent = Math.round((processed / total) * 100);
      const isRu = (currentLang === 'ru');

      document.getElementById('import-progress-bar').style.width = percent + '%';
      document.getElementById('import-progress-percentage').textContent = percent + '%';
      document.getElementById('import-progress-counts').textContent = isRu ? `Обработано: ${processed} из ${total}` : `Processed: ${processed} / ${total}`;
      document.getElementById('import-progress-remaining').textContent = isRu ? `Осталось: ${remaining}` : `Remaining: ${remaining}`;

      const statusEl = document.getElementById('import-progress-status');
      if (res.running) {
        statusEl.textContent = isRu ? `Импорт голосов...` : `Importing voice types...`;
      } else {
        statusEl.textContent = isRu ? `Импорт завершен!` : `Import completed!`;
      }
    }

    if (!res.running) {
      clearInterval(importInterval);
      importInterval = null;
      await loadVoices();
      if (res.total > 0) {
        const isRu = (currentLang === 'ru');
        document.getElementById('import-progress-bar').style.width = '100%';
        document.getElementById('import-progress-percentage').textContent = '100%';
        document.getElementById('import-progress-status').textContent = isRu ? `Импорт завершен!` : `Import completed!`;
        document.getElementById('import-progress-counts').textContent = isRu ? `Обработано: ${res.total} из ${res.total}` : `Processed: ${res.total} / ${res.total}`;
        document.getElementById('import-progress-remaining').textContent = isRu ? `Осталось: 0` : `Remaining: 0`;
      }
    }
  } catch (err) { console.error(err); }
}

function filterVoices() {
  const query = document.getElementById('voice-search').value.toLowerCase().trim();
  document.querySelectorAll('#voice-table-body tr').forEach(row => {
    if (row.id && row.id.startsWith('row-')) {
      row.style.display = row.id.replace('row-', '').toLowerCase().includes(query) ? '' : 'none';
    }
  });
}

// Загрузка голосов дизайна
async function loadDesignVoices() {
  try {
    const list = await fetch('/voices/api/list').then(r => r.json());
    const tableBody = document.getElementById('voice-design-table-body');
    let html = '';
    const designList = list.design || {};
    const keys = Object.keys(designList).sort();
    const dict = i18n[currentLang] || i18n.en;
    
    if (keys.length === 0) {
      html = `<tr><td colspan="3" style="text-align:center; color:var(--text-muted); padding:20px;">${dict.no_voices_found}</td></tr>`;
    } else {
      keys.forEach(key => {
        const v = designList[key];
        html += `
          <tr id="row-design-${key}">
            <td style="font-weight:600; color:var(--accent);">${key}</td>
            <td><input type="text" id="instruct-${key}" value="${v.instruct || ''}"></td>
            <td>
              <div class="actions-cell">
                <button class="action-btn play" onclick="playVoiceDesign('${key}')">${dict.btn_play}</button>
                <button class="action-btn primary" onclick="saveVoiceDesign('${key}')">${dict.btn_save}</button>
                <button class="action-btn danger" onclick="deleteVoiceDesign('${key}')">${dict.btn_delete}</button>
              </div>
            </td>
          </tr>
        `;
      });
    }
    tableBody.innerHTML = html;
  } catch (err) { console.error(err); }
}

async function playVoiceDesign(key) {
  const dict = i18n[currentLang] || i18n.en;
  
  // 1. Check if voicedesign model is loaded
  try {
    const status = await fetch('/settings/api/status').then(r => r.json());
    const talkerPath = (status.talker_path || '').toLowerCase();
    if (!talkerPath.includes('voicedesign')) {
      const errMsgs = {
        ru: "Ошибка: Для прослушивания дизайна голоса должна быть выбрана модель voicedesign (например, qwen-talker-1.7b-voicedesign-Q8_0.gguf)!",
        en: "Error: A voicedesign model must be selected (e.g., qwen-talker-1.7b-voicedesign-Q8_0.gguf) to play voice designs!"
      };
      alert(errMsgs[currentLang] || errMsgs.en);
      return;
    }
  } catch (err) {
    console.error("Failed to check backend status:", err);
  }

  // 2. Select preview text and language from settings inputs
  const previewInput = document.getElementById('design-preview-text');
  const previewText = previewInput ? previewInput.value.trim() : "";
  if (!previewText) {
    alert(currentLang === 'ru' ? "Пожалуйста, введите текст для теста!" : "Please enter a test phrase!");
    return;
  }

  const activeLang = (document.getElementById('lang') ? document.getElementById('lang').value.trim() : 'russian');

  // 3. Trigger synthesis and play the audio
  const playerBar = document.getElementById('footer-audio-player');
  const pathEl = document.getElementById('player-file-path');
  const audioEl = document.getElementById('player-audio-element');

  if (pathEl) pathEl.textContent = `[VoiceDesign Generation] ${key}`;
  if (playerBar) playerBar.style.display = 'flex';

  try {
    const response = await fetch('/tts_to_audio/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: previewText,
        speaker_wav: key,
        language: activeLang
      })
    });
    
    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.detail || 'Synthesis failed');
    }

    const blob = await response.blob();
    const blobUrl = URL.createObjectURL(blob);
    
    if (audioEl) {
      audioEl.src = blobUrl;
      audioEl.play().catch(err => {
        alert(dict.alert_play_err || "Could not play audio.");
      });
      currentAudio = audioEl;
    } else {
      if (currentAudio) currentAudio.pause();
      currentAudio = new Audio(blobUrl);
      currentAudio.play().catch(err => {
        alert(dict.alert_play_err || "Could not play audio.");
      });
    }
  } catch (err) {
    alert((currentLang === 'ru' ? "Ошибка генерации: " : "Generation error: ") + err.message);
  }
}

async function saveVoiceDesign(key) {
  const instruct = document.getElementById(`instruct-${key}`).value.trim();
  const dict = i18n[currentLang] || i18n.en;
  try {
    await postJson('/voices/api/save', { key, instruct, ref_text: "", db_type: 'design' });
    alert((dict.alert_saved || 'Saved.').replace('{key}', key));
  } catch (err) { alert(dict.alert_save_err + err.message); }
}

async function deleteVoiceDesign(key) {
  const dict = i18n[currentLang] || i18n.en;
  if (!confirm((dict.alert_delete_confirm || 'Delete?').replace('{key}', key))) return;
  try {
    await postJson('/voices/api/delete', { key, db_type: 'design' });
    const row = document.getElementById(`row-design-${key}`);
    if (row) row.remove();
  } catch (err) { alert(dict.alert_delete_err + err.message); }
}

async function addVoiceDesign(e) {
  e.preventDefault();
  const key = document.getElementById('new-voice-design-key').value.trim();
  const instruct = document.getElementById('new-voice-design-instruct').value.trim();
  const dict = i18n[currentLang] || i18n.en;
  try {
    await postJson('/voices/api/save', { key, instruct, ref_text: "", db_type: 'design' });
    document.getElementById('add-voice-design-form').reset();
    await loadDesignVoices();
    alert((dict.alert_added || 'Added.').replace('{key}', key));
  } catch (err) { alert(dict.alert_add_err + err.message); }
}

function filterDesignVoices() {
  const query = document.getElementById('voice-design-search').value.toLowerCase().trim();
  document.querySelectorAll('#voice-design-table-body tr').forEach(row => {
    if (row.id && row.id.startsWith('row-design-')) {
      row.style.display = row.id.replace('row-design-', '').toLowerCase().includes(query) ? '' : 'none';
    }
  });
}

// Импорт SkyrimNet Design
let importDesignInterval = null;
async function startDesignImport(e) {
  e.preventDefault();
  const consoleEl = document.getElementById('import-design-console');
  consoleEl.style.display = 'block';
  consoleEl.textContent = "Starting design voices import...\n";

  const progContainer = document.getElementById('import-design-progress-container');
  if (progContainer) {
    progContainer.style.display = 'block';
    document.getElementById('import-design-progress-bar').style.width = '0%';
    document.getElementById('import-design-progress-percentage').textContent = '0%';
    document.getElementById('import-design-progress-status').textContent = (currentLang === 'ru') ? 'Подготовка...' : 'Preparing...';
    document.getElementById('import-design-progress-counts').textContent = (currentLang === 'ru') ? 'Обработано: 0 из 0' : 'Processed: 0 / 0';
    document.getElementById('import-design-progress-remaining').textContent = (currentLang === 'ru') ? 'Осталось: 0' : 'Remaining: 0';
  }

  try {
    await postJson('/voices/api/import', {
      base_url: document.getElementById('import-design-url').value.trim(),
      selection_mode: 'qwentts-safe',
      force: false,
      preserve_existing: document.getElementById('import-design-preserve').checked,
      design_mode: true
    });
    if (importDesignInterval) clearInterval(importDesignInterval);
    importDesignInterval = setInterval(pollDesignImportStatus, 1000);
  } catch (err) { consoleEl.textContent += "Error: " + err.message + "\n"; }
}

async function pollDesignImportStatus() {
  try {
    const res = await fetch('/voices/api/import/status').then(r => r.json());
    const consoleEl = document.getElementById('import-design-console');
    if (res.log) { consoleEl.textContent = res.log; consoleEl.scrollTop = consoleEl.scrollHeight; }

    if (res.total > 0) {
      const processed = res.processed || 0;
      const total = res.total;
      const remaining = Math.max(0, total - processed);
      const percent = Math.round((processed / total) * 100);
      const isRu = (currentLang === 'ru');

      document.getElementById('import-design-progress-bar').style.width = percent + '%';
      document.getElementById('import-design-progress-percentage').textContent = percent + '%';
      document.getElementById('import-design-progress-counts').textContent = isRu ? `Обработано: ${processed} из ${total}` : `Processed: ${processed} / ${total}`;
      document.getElementById('import-design-progress-remaining').textContent = isRu ? `Осталось: ${remaining}` : `Remaining: ${remaining}`;

      const statusEl = document.getElementById('import-design-progress-status');
      if (res.running) {
        statusEl.textContent = isRu ? `Импорт голосов...` : `Importing voice types...`;
      } else {
        statusEl.textContent = isRu ? `Импорт завершен!` : `Import completed!`;
      }
    }

    if (!res.running) {
      clearInterval(importDesignInterval);
      importDesignInterval = null;
      await loadDesignVoices();
      if (res.total > 0) {
        const isRu = (currentLang === 'ru');
        document.getElementById('import-design-progress-bar').style.width = '100%';
        document.getElementById('import-design-progress-percentage').textContent = '100%';
        document.getElementById('import-design-progress-status').textContent = isRu ? `Импорт завершен!` : `Import completed!`;
        document.getElementById('import-design-progress-counts').textContent = isRu ? `Обработано: ${res.total} из ${res.total}` : `Processed: ${res.total} / ${res.total}`;
        document.getElementById('import-design-progress-remaining').textContent = isRu ? `Осталось: 0` : `Remaining: 0`;
      }
    }
  } catch (err) { console.error(err); }
}

// Инициализация
loadVoices();
loadDesignVoices();

fetch('/voices/api/import/status').then(r => r.json()).then(res => {
  if (res.running) {
    document.getElementById('import-console').style.display = 'block';
    const progContainer = document.getElementById('import-progress-container');
    if (progContainer) progContainer.style.display = 'block';
    importInterval = setInterval(pollImportStatus, 1000);

    document.getElementById('import-design-console').style.display = 'block';
    const progDesignContainer = document.getElementById('import-design-progress-container');
    if (progDesignContainer) progDesignContainer.style.display = 'block';
    importDesignInterval = setInterval(pollDesignImportStatus, 1000);
  }
});

// Интерактивный туториал
const tutorialSteps = [
  { title: "", target: null, onShow: () => switchTab('settings'), content: "" },
  { title: "", target: "section-backend", onShow: () => switchTab('settings'), content: "" },
  { title: "", target: "section-models", onShow: () => switchTab('settings'), content: "" },
  { title: "", target: "section-params", onShow: () => switchTab('settings'), content: "" },
  { title: "", target: "section-import", onShow: () => switchTab('voices'), content: "" }
];
let currentTutorialStep = 0;

function showTutorialStep(stepIndex) {
  currentTutorialStep = stepIndex;
  const step = tutorialSteps[stepIndex];
  if (step.onShow) step.onShow();
  
  document.getElementById('tutorial-title').textContent = step.title;
  document.getElementById('tutorial-body-content').innerHTML = step.content;
  
  document.querySelectorAll('.spotlight-highlight').forEach(el => el.classList.remove('spotlight-highlight'));
  if (step.target) {
    const targetEl = document.getElementById(step.target);
    if (targetEl) {
      targetEl.classList.add('spotlight-highlight');
      setTimeout(() => { targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' }); }, 50);
    }
  } else { window.scrollTo({ top: 0, behavior: 'smooth' }); }
  
  document.getElementById('tutorial-btn-prev').style.display = stepIndex === 0 ? 'none' : 'inline-block';
  document.getElementById('tutorial-btn-next').textContent = stepIndex === tutorialSteps.length - 1 ? 'Завершить' : 'Далее';
  
  const dotsContainer = document.getElementById('tutorial-dots-container');
  dotsContainer.innerHTML = '';
  for (let i = 0; i < tutorialSteps.length; i++) {
    const dot = document.createElement('div');
    dot.className = 'tutorial-dot' + (i === stepIndex ? ' active' : '');
    dot.onclick = () => showTutorialStep(i);
    dotsContainer.appendChild(dot);
  }
}

function startTutorial() {
  document.getElementById('tutorial-overlay').classList.add('active');
  document.getElementById('tutorial-card-container').classList.add('active');
  showTutorialStep(0);
}

function closeTutorial() {
  document.getElementById('tutorial-overlay').classList.remove('active');
  document.getElementById('tutorial-card-container').classList.remove('active');
  document.querySelectorAll('.spotlight-highlight').forEach(el => el.classList.remove('spotlight-highlight'));
  localStorage.setItem('qwentts_tutorial_seen', 'true');
}

function nextStep() {
  if (currentTutorialStep < tutorialSteps.length - 1) showTutorialStep(currentTutorialStep + 1);
  else closeTutorial();
}

function prevStep() {
  if (currentTutorialStep > 0) showTutorialStep(currentTutorialStep - 1);
}

setTimeout(() => {
  if (localStorage.getItem('qwentts_tutorial_seen') !== 'true') startTutorial();
}, 1000);