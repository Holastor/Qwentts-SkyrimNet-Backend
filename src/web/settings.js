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
    import_skyrimnet_desc: "Сканировать запущенный сервер SkyrimNet для автоматического заполнения базы voice_refs.json. <br><br><strong style='color:var(--accent-color);'>⚠️ ВАЖНОЕ ПРЕДУПРЕЖДЕНИЕ ПЕРЕД ИМПОРТОМ:</strong><br>1. <strong>Процесс занимает 10-15 минут:</strong> сканирование и добавление требуют времени на стороне самого SkyrimNet, так как ему необходимо найти файлы внутри игровых архивов (BSA/FUZ) и распаковать их.<br>2. <strong>Проверяйте язык озвучки сэмплов:</strong> иногда текст в базе данных отображается на одном языке, а само аудио звучит на другом. Если QwenTTS получит такой рассинхрон текста и звука, генерация сломается.<br>3. Если вы обнаружили, что выбранный NPC говорит на неподходящем языке, перейдите во вкладку <strong>Voice · Samples & Effects</strong> в интерфейсе SkyrimNet и вручную выберите правильный рабочий аудио-сэмпл для этого персонажа.",
    import_skyrimnet_design_title: "Импорт голосов для Voice Design из SkyrimNet",
    import_skyrimnet_design_desc: "Сканировать запущенный server SkyrimNet для регистрации дизайнов голосов с текстовыми описаниями (без скачивания файлов).<br><br><strong style='color:var(--accent-color);'>⚠️ ВАЖНОЕ ПРИМЕЧАНИЕ:</strong> Модель лучше всего понимает промпты на <strong>английском или китайском языках</strong>. Текстовые инструкции на русском языке работают, но использование английских тегов и описаний обеспечивает максимальную точность попадания в нужный тембр и интонацию.<br><br><strong style='color:var(--accent-color);'>💡 КОНСТРУКТОР ОПИСАНИЯ ГОЛОСА (ШПАРГАЛКА):</strong><br>Вы можете комбинировать любые параметры из таблицы ниже в свободной текстовой форме (рекомендуется составлять итоговый промпт на английском):<br><br><table style='width:100%; border-collapse: collapse; margin: 10px 0; font-size: 13px; line-height: 1.4; border: 1px solid #444;'><thead><tr style='background: #222; color: var(--accent-color);'><th style='padding: 6px; border: 1px solid #444;'>Параметр (Тег)</th><th style='padding: 6px; border: 1px solid #444;'>Доступные варианты / Опции</th></tr></thead><tbody><tr><td style='padding: 6px; border: 1px solid #444;'><strong>Пол (Gender)</strong></td><td style='padding: 6px; border: 1px solid #444;'>Male (Мужской) / Female (Женский)</td></tr><tr style='background: #1a1a1a;'><td style='padding: 6px; border: 1px solid #444;'><strong>Возраст (Age)</strong></td><td style='padding: 6px; border: 1px solid #444;'>Child (Ребенок / Лоли), Teenage (Подросток), Young adult (Молодой), Middle-aged (Средних лет), Elderly (Пожилой)</td></tr><tr><td style='padding: 6px; border: 1px solid #444;'><strong>Тон / Высота (Pitch)</strong></td><td style='padding: 6px; border: 1px solid #444;'>Low (Низкий / Баритон), Mid-range (Средний), High-pitched (Высокий), Stable (Стабильный), Upward inflections (Резкие взлеты тона)</td></tr><tr style='background: #1a1a1a;'><td style='padding: 6px; border: 1px solid #444;'><strong>Скорость (Speed)</strong></td><td style='padding: 6px; border: 1px solid #444;'>Slow (Медленный), Measured (Размеренный), Fast-paced (Быстрый), Rapid (Захлебывающийся)</td></tr><tr><td style='padding: 6px; border: 1px solid #444;'><strong>Громкость (Volume)</strong></td><td style='padding: 6px; border: 1px solid #444;'>Whisper (Шепот), Soft (Тихий), Conversational (Разговорный), Loud / Projecting (Громкий), Shouting (Крик)</td></tr><tr style='background: #1a1a1a;'><td style='padding: 6px; border: 1px solid #444;'><strong>Текстура (Texture)</strong></td><td style='padding: 6px; border: 1px solid #444;'>Clear (Чистый), Resonant (Глубокий / Резонирующий), Gravelly / Raspy (Хриплый / Сиплый / Грубый), Nasal (Гнусавый / В нос)</td></tr><tr><td style='padding: 6px; border: 1px solid #444;'><strong>Эмоция (Emotion)</strong></td><td style='padding: 6px; border: 1px solid #444;'>Calm (Спокойный), Sarcastic (Саркастичный), Angry / Resentment (Злой / Раздраженный), Crying (Плачущий), Enthusiastic / Laughing (Живой / Смеющийся)</td></tr><tr style='background: #1a1a1a;'><td style='padding: 6px; border: 1px solid #444;'><strong>Динамика (Gradual)</strong></td><td style='padding: 6px; border: 1px solid #444;'>Переходы в процессе речи: <code>Starts loud, transitions to a soft whisper</code> (Начинает громко, переходит в тихий шепот) или <code>Shifts abruptly from calm to intense anger</code></td></tr></tbody></table><br><strong>Пример идеальной сборки (на английском):</strong><br><code>gender: Male. age: Middle-aged. pitch: Low male pitch. speed: Deliberate pace. volume: Conversational. texture: Gravelly and raspy quality. emotion: Sarcastic. A deep, gravelly middle-aged male voice. Speaks slowly with a heavy layer of cynicism and sarcasm, gradually lowering the volume towards the end of the sentence.</code>",
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
    import_skyrimnet_desc: "Scan the running SkyrimNet server to automatically populate the voice_refs.json database. <br><br><strong style='color:var(--accent-color);'>⚠️ IMPORTANT PRE-IMPORT WARNING:</strong><br>1. <strong>The process takes 10-15 minutes:</strong> scanning and addition take time on the SkyrimNet side because it needs to locate files inside game packages (BSA/FUZ) and unpack them.<br>2. <strong>Check the sample audio language:</strong> sometimes the text in the database is displayed in one language, but the audio itself plays in another. If QwenTTS encounters such a text-to-audio mismatch, the generation will break.<br>3. If you find that the selected NPC speaks the wrong language, go to the <strong>Voice · Samples & Effects</strong> tab in the SkyrimNet interface and manually select the correct working audio sample for that character.",
    import_skyrimnet_design_title: "Import Voices from SkyrimNet (Voice Design)",
    import_skyrimnet_design_desc: "Scan the running SkyrimNet server to register voice designs with text descriptions (without downloading files).<br><br><strong style='color:var(--accent-color);'>⚠️ IMPORTANT NOTE:</strong> The model understands prompts best in <strong>English or Chinese</strong>. While text instructions in Russian work, using English tags and descriptions ensures maximum accuracy in hitting the desired timbre and intonation.<br><br><strong style='color:var(--accent-color);'>💡 VOICE DESCRIPTION CONSTRUCTOR (CHEAT SHEET):</strong><br>You can combine any parameters from the table below in free-form text (it is highly recommended to compose the final prompt in English):<br><br><table style='width:100%; border-collapse: collapse; margin: 10px 0; font-size: 13px; line-height: 1.4; border: 1px solid #444;'><thead><tr style='background: #222; color: var(--accent-color);'><th style='padding: 6px; border: 1px solid #444;'>Parameter (Tag)</th><th style='padding: 6px; border: 1px solid #444;'>Available Options / Variants</th></tr></thead><tbody><tr><td style='padding: 6px; border: 1px solid #444;'><strong>Gender</strong></td><td style='padding: 6px; border: 1px solid #444;'>Male / Female</td></tr><tr style='background: #1a1a1a;'><td style='padding: 6px; border: 1px solid #444;'><strong>Age</strong></td><td style='padding: 6px; border: 1px solid #444;'>Child (Loli), Teenage, Young adult, Middle-aged, Elderly</td></tr><tr><td style='padding: 6px; border: 1px solid #444;'><strong>Pitch / Tone</strong></td><td style='padding: 6px; border: 1px solid #444;'>Low (Baritone / Deep), Mid-range, High-pitched, Stable, Upward inflections (Sharp pitch jumps)</td></tr><tr style='background: #1a1a1a;'><td style='padding: 6px; border: 1px solid #444;'><strong>Speed</strong></td><td style='padding: 6px; border: 1px solid #444;'>Slow, Measured, Fast-paced, Rapid (Choking with emotion)</td></tr><tr><td style='padding: 6px; border: 1px solid #444;'><strong>Volume</strong></td><td style='padding: 6px; border: 1px solid #444;'>Whisper, Soft, Conversational, Loud / Projecting, Shouting</td></tr><tr style='background: #1a1a1a;'><td style='padding: 6px; border: 1px solid #444;'><strong>Texture</strong></td><td style='padding: 6px; border: 1px solid #444;'>Clear, Resonant (Deep), Gravelly / Raspy (Hoarse / Rough), Nasal</td></tr><tr><td style='padding: 6px; border: 1px solid #444;'><strong>Emotion</strong></td><td style='padding: 6px; border: 1px solid #444;'>Calm, Sarcastic, Angry / Resentment, Crying, Enthusiastic / Laughing</td></tr><tr style='background: #1a1a1a;'><td style='padding: 6px; border: 1px solid #444;'><strong>Gradual Control</strong></td><td style='padding: 6px; border: 1px solid #444;'>Transitions during speech: e.g., <code>Starts loud, transitions to a soft whisper</code> or <code>Shifts abruptly from calm to intense anger</code></td></tr></tbody></table><br><strong>An ideal prompt example (in English):</strong><br><code>gender: Male. age: Middle-aged. pitch: Low male pitch. speed: Deliberate pace. volume: Conversational. texture: Gravelly and raspy quality. emotion: Sarcastic. A deep, gravelly middle-aged male voice. Speaks slowly with a heavy layer of cynicism and sarcasm, gradually lowering the volume towards the end of the sentence.</code>",
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
  },
  zh: {
    title: "⚙️ QwenTTS 设置",
    btn_guide: "🎓 互动指南",
    tab_settings: "设置与模型",
    tab_voices: "声音管理器",
    tab_voice_design: "声音设计",
    section_backend_title: "计算后端",
    section_backend_desc: "选择计算后端。切换后端需要重新加载模型（需 5-30 秒）。",
    btn_apply_backend: "应用后端",
    status_ready: "就绪",
    status_not_built: "未构建",
    section_params_title: "推理参数",
    section_params_desc: "控制语音输出质量和行为的核心采样设置。",
    subtalker_collapsible: "高级：代码预测器 (Sub-Talker) 参数",
    btn_save_settings: "保存设置",
    section_models_title: "模型",
    btn_refresh: "↻ 刷新",
    talker_lm_title: "Talker LM",
    talker_lm_desc: "生成语音 Token 的语言模型。",
    audio_codec_title: "音频编解码器",
    audio_codec_desc: "将音频代码转换为波形的 Tokenizer。",
    btn_apply_models: "应用模型",
    requires_reload_hint: "需要重新加载后端（需 5-30 秒）",
    download_hf_title: "从 HuggingFace 下载",
    download_hf_desc: "下载额外的 GGUF 模型。",
    import_skyrimnet_title: "从 SkyrimNet 导入声音",
    import_skyrimnet_desc: "扫描正在运行的 SkyrimNet 服务器以自动填充 voice_refs.json 数据库。<br><br><strong style='color:var(--accent-color);'>⚠️ 导入前重要警告：</strong><br>1. <strong>该过程需要 10-15 分钟：</strong> 扫描和添加在 SkyrimNet 端需要一些时间，因为它需要定位游戏包（BSA/FUZ）内部的文件并进行解压。<br>2. <strong>检查样本音频语言：</strong> 有时数据库中的文本显示为一种语言，但音频本身却以另一种语言播放。如果 QwenTTS 遇到这种文本与音频不匹配的情况，生成将会失败。<br>3. 如果您发现所选的 NPC 说的语言不正确，请前往 SkyrimNet 界面中的 <strong>Voice · Samples & Effects</strong> 标签页，为该角色手动选择正确的可用音频样本。",
    import_skyrimnet_design_title: "从 SkyrimNet 导入声音 (声音设计)",
    import_skyrimnet_design_desc: "扫描正在运行的 SkyrimNet 服务器以注册带有文本描述的声音设计（不下载文件）。<br><br><strong style='color:var(--accent-color);'>⚠️ 重要提示：</strong> 该模型对 <strong>英文或中文</strong> 的 Prompt 理解最为出色。虽然俄文的文本指令也能工作，但使用英文标签和描述可以确保最准确地契合所需的音色和语调。<br><br><strong style='color:var(--accent-color);'>💡 声音描述构造器 (备忘单)：</strong><br>您可以在自由文本中组合下表中的任何参数（强烈建议用意文撰写最终的 Prompt）：<br><br><table style='width:100%; border-collapse: collapse; margin: 10px 0; font-size: 13px; line-height: 1.4; border: 1px solid #444;'><thead><tr style='background: #222; color: var(--accent-color);'><th style='padding: 6px; border: 1px solid #444;'>参数 (标签)</th><th style='padding: 6px; border: 1px solid #444;'>可用选项 / 变体</th></tr></thead><tbody><tr><td style='padding: 6px; border: 1px solid #444;'><strong>Gender (性别)</strong></td><td style='padding: 6px; border: 1px solid #444;'>Male (男性) / Female (女性)</td></tr><tr style='background: #1a1a1a;'><td style='padding: 6px; border: 1px solid #444;'><strong>Age (年龄)</strong></td><td style='padding: 6px; border: 1px solid #444;'>Child (儿童/萝莉), Teenage (青少年), Young adult (青年), Middle-aged (中年), Elderly (老年)</td></tr><tr><td style='padding: 6px; border: 1px solid #444;'><strong>Pitch / Tone (音高/语调)</strong></td><td style='padding: 6px; border: 1px solid #444;'>Low (低沉/男低音), Mid-range (中音), High-pitched (高音), Stable (稳定), Upward inflections (尖锐的音高起伏)</td></tr><tr style='background: #1a1a1a;'><td style='padding: 6px; border: 1px solid #444;'><strong>Speed (语速)</strong></td><td style='padding: 6px; border: 1px solid #444;'>Slow (慢速), Measured (沉稳), Fast-paced (快速), Rapid (情绪激动的急促语速)</td></tr><tr><td style='padding: 6px; border: 1px solid #444;'><strong>Volume (音量)</strong></td><td style='padding: 6px; border: 1px solid #444;'>Whisper (耳语), Soft (轻柔), Conversational (对话音量), Loud / Projecting (响亮), Shouting (呐喊)</td></tr><tr style='background: #1a1a1a;'><td style='padding: 6px; border: 1px solid #444;'><strong>Texture (音质)</strong></td><td style='padding: 6px; border: 1px solid #444;'>Clear (清澈), Resonant (洪亮/共鸣), Gravelly / Raspy (沙哑/粗粝), Nasal (鼻音)</td></tr><tr><td style='padding: 6px; border: 1px solid #444;'><strong>Emotion (情感)</strong></td><td style='padding: 6px; border: 1px solid #444;'>Calm (平静), Sarcastic (讽刺), Angry / Resentment (愤怒/怨恨), Crying (哭腔), Enthusiastic / Laughing (热情/带笑意)</td></tr><tr style='background: #1a1a1a;'><td style='padding: 6px; border: 1px solid #444;'><strong>Gradual Control (渐变控制)</strong></td><td style='padding: 6px; border: 1px solid #444;'>说话过程中的转换：例如 <code>Starts loud, transitions to a soft whisper</code> (开始时很响亮，随后转化为轻柔的耳语) 或 <code>Shifts abruptly from calm to intense anger</code></td></tr></tbody></table><br><strong>完美的 Prompt 示例 (英文)：</strong><br><code>gender: Male. age: Middle-aged. pitch: Low male pitch. speed: Deliberate pace. volume: Conversational. texture: Gravelly and raspy quality. emotion: Sarcastic. A deep, gravelly middle-aged male voice. Speaks slowly with a heavy layer of cynicism and sarcasm, gradually lowering the volume towards the end of the sentence.</code>",
    import_url_label: "SkyrimNet URL:",
    import_mode_label: "选择模式:",
    import_preserve_label: " 保留现有条目 (安全)",
    import_force_label: " 覆盖文件",
    btn_start_import: "开始同步",
    add_voice_title: "手动添加新声音",
    add_voice_desc: "创建数据库记录。WAV 文件必须物理存在于 speakers 文件夹中。",
    add_voice_design_title: "手动添加新声音参考 (声音设计)",
    add_voice_design_desc: "为声音设计创建一个新的语音参考。输入属性/描述以代替 WAV 路径。",
    new_voice_key_label: "说话人名称 / Key:",
    new_voice_audio_label: "WAV 参考路径:",
    new_voice_design_instruct_label: "声音描述:",
    new_voice_design_instruct_tip: "声音属性用逗号分隔，例如：male, young adult, moderate pitch",
    new_voice_text_label: "文本回录 (需精确匹配):",
    btn_add_voice: "添加声音",
    registered_voices_title: "已注册声音数据库 (voice_refs.json)",
    registered_design_voices_title: "已注册声音设计数据库",
    search_placeholder: "搜索声音...",
    btn_reload: "↻ 刷新列表",
    th_speaker_key: "说话人 Key",
    th_wav_path: "WAV 路径",
    th_voice_description: "声音描述",
    th_transcript: "文本回录 (精确副本)",
    th_actions: "操作",
    btn_play: "▶ 播放",
    btn_save: "保存",
    btn_delete: "删除",
    voice_key_tip: "唯一的说话人 ID，例如：malebrute",
    voice_audio_tip: "WAV 文件相对于项目根目录的路径",
    voice_text_tip: "音频文件中所说的精确文本。",
    alert_play_err: "播放音频失败。请确保磁盘上存在该 WAV 文件。",
    alert_saved: "声音 \"{key}\" 保存成功。",
    alert_save_err: "保存声音时出错: ",
    alert_delete_confirm: "您确定要删除声音 \"{key}\" 吗？",
    alert_delete_err: "删除声音时出错: ",
    alert_add_empty: "请填写所有字段以添加声音。",
    alert_added: "声音 \"{key}\" 添加成功。",
    alert_add_err: "添加声音时出错: ",
    no_voices_found: "未找到声音。",
    import_starting: "正在开始导入...\n",
    now_playing: "当前播放:",
    label_preview_text: "预览文本:"
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
  ],
  zh: [
    { title: "🚀 欢迎使用 Qwen3-TTS！", target: null, onShow: () => switchTab('settings'), content: "本互动指南将协助您配置 <strong>Qwen3-TTS SkyrimNet Adapter</strong>。" },
    { title: "⚙️ 选择计算后端", target: "section-backend", onShow: () => switchTab('settings'), content: "在 CPU、CUDA (NVIDIA) 或 Vulkan 之间进行选择。强烈建议使用 CUDA 以实现实时语音合成。" },
    { title: "🧠 Talker LM 与编解码器模型", target: "section-models", onShow: () => switchTab('settings'), content: "选择您启用的语言模型与声音编解码器架构，然后点击“应用模型”。" },
    { title: "🎛️ 采样参数", target: "section-params", onShow: () => switchTab('settings'), content: "微调随机种子 (Seed)、温度 (Temperature) 和重复惩罚等设置，以调整声音 lobby 的稳定性和情感丰富度。" },
    { title: "👥 声音管理器", target: "tab-voices", onShow: () => switchTab('voices'), content: "从正在运行的 SkyrimNet 节点同步并下载参考音频数据，以自动构建声音克隆映射表。<br><br><strong>⚠️ 导入前重要警告：</strong><br>1. <strong>该过程需要 10-15 分钟：</strong> 扫描和添加在 SkyrimNet 端需要一些时间，因为它需要定位游戏包（BSA/FUZ）内部的文件并进行解压。<br>2. <strong>检查样本音频语言：</strong> 有时数据库中的文本显示为一种语言，但音频本身却以另一种语言播放。如果 QwenTTS 遇到这种文本与音频不匹配的情况，生成将会失败。" }
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