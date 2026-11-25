import difflib
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from core.config import OUTPUT_DIR

_DEV_TO_ASCII_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
_HAS_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")

# High-frequency Hindi, Marathi, month, unit, and tech loanwords -> clean readable Hinglish/English
_HINGLISH_LEXICON: Dict[str, str] = {
    # Common Hindi grammar / conversational words
    "मैं": "main", "मेरा": "mera", "मेरी": "meri", "मेरे": "mere", "मुझे": "mujhe", "मुझको": "mujhko",
    "हम": "hum", "हमारा": "humara", "हमारी": "humari", "हमारे": "humare", "हमें": "humein",
    "आप": "aap", "आपका": "aapka", "आपकी": "aapki", "आपके": "aapke", "आपको": "aapko",
    "तुम": "tum", "तुम्हारा": "tumhara", "तुम्हे": "tumhe", "यार": "yaar", "दोस्त": "dost", "भाई": "bhai",
    "यह": "yeh", "ये": "yeh", "वह": "woh", "वो": "woh", "इस": "is", "उस": "us", "इन": "in", "उन": "un",
    "इसका": "iska", "इसकी": "iski", "इसके": "iske", "इसमें": "ismein", "इससे": "isse",
    "उसका": "uska", "उसकी": "uski", "उसके": "uske", "उसमें": "usmein", "उससे": "usse",
    "का": "ka", "की": "ki", "के": "ke", "को": "ko", "में": "mein", "से": "se", "पर": "par", "पे": "pe",
    "तक": "tak", "लिए": "liye", "साथ": "saath", "बिना": "bina", "बाद": "baad", "पहले": "pehle",
    "अंदर": "andar", "बाहर": "bahar", "ऊपर": "upar", "नीचे": "neeche", "बीच": "beech", "पास": "paas",
    "और": "aur", "या": "ya", "तो": "toh", "ही": "hi", "भी": "bhi", "नहीं": "nahi", "नही": "nahi", "ना": "na", "मत": "mat",
    "है": "hai", "हैं": "hain", "था": "tha", "थी": "thi", "थे": "the", "हो": "ho", "हूँ": "hoon", "हूं": "hoon",
    "होता": "hota", "होती": "hoti", "होते": "hote", "होगा": "hoga", "होगी": "hogi", "होंगे": "honge",
    "हुआ": "hua", "हुई": "hui", "हुए": "hue", "गया": "gaya", "गई": "gayi", "गए": "gaye",
    "कर": "kar", "करो": "karo", "करना": "karna", "करने": "karne", "करते": "karte", "करता": "karta", "करती": "karti",
    "किया": "kiya", "किए": "kiye", "करेंगे": "karenge", "करेगा": "karega", "रहा": "raha", "रही": "rahi", "रहे": "rahe",
    "सकता": "sakta", "सकती": "sakti", "सकते": "sakte", "चाहिए": "chahiye", "पड़ता": "padta", "पड़ेगा": "padega",
    "देता": "deta", "देती": "deti", "देते": "dete", "दिया": "diya", "लेता": "leta", "लिया": "liya",
    "जाता": "jaata", "जाती": "jaati", "जाते": "jaate", "आता": "aata", "आती": "aati", "आते": "aate", "आया": "aaya",
    "लगता": "lagta", "लगती": "lagti", "लगते": "lagte", "लगा": "laga", "बनता": "banta", "बनती": "banti", "बनते": "bante",
    "चलता": "chalta", "चलती": "chalti", "चलते": "chalte", "मिलता": "milta", "मिलती": "milti", "मिलते": "milte",
    "देखो": "dekho", "देखते": "dekhte", "देखेंगे": "dekhenge", "सोचो": "socho", "ज़रा": "zara", "जरा": "zara",
    "समझो": "samjho", "समझते": "samajhte", "समझेंगे": "samjhenge", "जानते": "jaante", "मान": "maan", "लो": "lo",
    "क्या": "kya", "क्यों": "kyun", "कैसे": "kaise", "कब": "kab", "कहाँ": "kahan", "कौन": "kaun", "कितना": "kitna",
    "जब": "jab", "तब": "tab", "अब": "ab", "अभी": "abhi", "आज": "aaj", "कल": "kal", "फिर": "phir",
    "अगर": "agar", "लेकिन": "lekin", "मगर": "magar", "परंतु": "par", "क्योंकि": "kyunki", "इसीलिए": "isiliye",
    "मतलब": "matlab", "यानी": "yaani", "जैसे": "jaise", "वैसे": "waise", "सब": "sab", "सभी": "sabhi", "हर": "har",
    "एक": "ek", "दो": "two", "तीन": "three", "चार": "four", "पांच": "five", "दस": "ten", "सौ": "hundred",
    "सिर्फ": "sirf", "बस": "bas", "बहुत": "bahut", "ज़्यादा": "zyada", "ज्यादा": "zyada", "कम": "kam",
    "अच्छा": "accha", "सही": "sahi", "गलत": "galat", "सीधा": "seedha", "आसान": "aasan", "तेज़": "tez",
    "तेज": "tez", "धीमा": "dheema", "नया": "naya", "पुराना": "purana", "बड़ा": "bada", "छोटा": "chota",
    "पहला": "pehla", "दूसरा": "doosra", "तीसरा": "teesra", "आखिरी": "aakhiri", "पूरा": "poora", "पूरी": "poori",
    "वाला": "wala", "वाली": "wali", "वाले": "wale", "यहाँ": "yahan", "यहीं": "yahin", "वहाँ": "wahan",
    "जल्दी": "jaldi", "तुरंत": "turant", "हमेशा": "hamesha", "कभी": "kabhi", "बिल्कुल": "bilkul",
    # Common Marathi conversational words
    "मित्रांनो": "mitrano", "आपण": "aapan", "मी": "mi", "तुम्ही": "tumhi", "तू": "tu", "त्याचा": "tyacha",
    "त्याची": "tyachi", "त्याचे": "tyache", "त्याला": "tyala", "त्यात": "tyat", "याला": "yala", "यात": "yat",
    "आहे": "aahe", "आहेत": "aahet", "नाही": "nahi", "नाहीत": "nahit", "होते": "hote", "होता": "hota",
    "होती": "hoti", "होईल": "hoil", "झाली": "jhali", "झाला": "jhala", "झाले": "jhale", "होतो": "hoto",
    "पाहणार": "pahnar", "आहोत": "aahot", "बघू": "baghu", "बघा": "bagha", "समजू": "samju", "समजून": "samjun",
    "कसे": "kase", "कसा": "kasa", "कशी": "kashi", "काय": "kay", "का": "ka", "केव्हा": "kevha", "कुठे": "kuthe",
    "पण": "pan", "आणि": "ani", "किंवा": "kinva", "तर": "tar", "म्हणजे": "mhanje", "म्हणून": "mhanun",
    "कारण": "karan", "जर": "jar", "मग": "mag", "आता": "aata", "नंतर": "nantar", "आधी": "aadhi",
    "साठी": "saathi", "मध्ये": "madhe", "वर": "var", "खाली": "khali", "ला": "la", "चे": "che", "ची": "chi", "चा": "cha",
    "ने": "ne", "शी": "shi", "सह": "sobat", "सोबत": "sobat", "बरोबर": "barobar", "सर्व": "sarva", "सगळे": "sagle",
    "लक्षात": "lakshat", "ठेवा": "theva", "घ्या": "ghya", "करा": "kara", "वापरा": "vapra", "करते": "karte",
    "करतो": "karto", "होतात": "hotat", "लागतात": "lagtat", "दोन": "two", "पाच": "five", "दहा": "ten", "शंभर": "hundred",
    # Months, Units & Common English Tech Loanwords transcribed by Whisper in Devanagari
    "जनवरी": "January", "जानेवारी": "January", "फरवरी": "February", "फेब्रुवारी": "February",
    "मार्च": "March", "अप्रैल": "April", "एप्रिल": "April", "मई": "May", "मे": "May", "जून": "June",
    "जुलाई": "July", "जुलै": "July", "अगस्त": "August", "ऑगस्ट": "August",
    "सितंबर": "September", "सप्टेंबर": "September", "अक्टूबर": "October", "ऑक्टोबर": "October",
    "नवंबर": "November", "नोव्हेंबर": "November", "नोवेंबर": "November", "दिसंबर": "December", "डिसेंबर": "December",
    "प्रतिशत": "percent", "टक्के": "percent", "पर्सेंट": "percent",
    "मिली": "milli", "मिलिसेकॉंड": "milliseconds", "मिलीसेकंड": "milliseconds", "सेकंड": "seconds", "सेकंद": "seconds", "सेकॉन्स": "seconds",
    "मिनट": "minutes", "मिनिट": "minutes", "मिनिटे": "minutes", "घंटे": "hours", "तास": "hours",
    "जीरो": "zero", "ज़ीरो": "zero", "झिरो": "zero", "शून्य": "zero",
    "हज़ार": "thousand", "हजार": "thousand", "लाख": "lakh", "करोड़": "crore", "कोटी": "crore",
    "डेटाबेस": "database", "डाटाबेस": "database", "डेटा": "data", "डाटा": "data",
    "सर्व्हर": "server", "सर्वर": "server", "सर्वर्स": "servers",
    "लेटेंसी": "latency", "लॅटन्सी": "latency", "थ्रूपुट": "throughput",
    "कैश": "cache", "कैशिंग": "caching", "कॅशे": "cache",
    "थ्रेड": "thread", "थ्रेड्स": "threads", "मल्टीथ्रेडिंग": "multithreading",
    "इंटरव्यू": "interview", "इंटरव्ह्यू": "interview", "प्रोडक्शन": "production",
    "डाउनटाइम": "downtime", "माइग्रेशन": "migration", "मायग्रेशन": "migration",
    "सिस्टम": "system", "सिस्टम्स": "systems", "आर्किटेक्चर": "architecture",
    "परफॉर्मेंस": "performance", "प्रॉब्लम": "problem", "सॉल्यूशन": "solution",
    "कोड": "code", "क्वेरी": "query", "क्वेरीज़": "queries", "टेबल": "table", "इंडेक्स": "index",
    "यूज़र": "user", "यूजर": "user", "यूज़र्स": "users", "यूजर्स": "users",
    "रिक्वेस्ट": "request", "रिक्वेस्ट्स": "requests", "रिस्पॉन्स": "response",
    "पैकेट": "packet", "नेटवर्क": "network", "बफर": "buffer", "मेमोरी": "memory",
    "प्रोसेस": "process", "कंटेनर": "container", "क्लस्टर": "cluster", "मॉडल": "model",
    "टोकन": "token", "डिफ़ॉल्ट": "default", "डिफॉल्ट": "default", "लॉक": "lock", "लॉक्स": "locks",
    "डेडलॉक": "deadlock", "स्केल": "scale", "ट्रैफिक": "traffic", "बॉटलनेक": "bottleneck",
    "एपीआई": "API", "एसक्यूएल": "SQL", "रेडिस": "Redis", "काफ्का": "Kafka", "डॉकर": "Docker",
    "पायथन": "Python", "जावा": "Java", "क्लाउड": "cloud", "बैकएंड": "backend", "फ्रंटएंड": "frontend",
}

_DEV_VOWELS = {
    "अ": "a", "आ": "aa", "इ": "i", "ई": "ee", "उ": "u", "ऊ": "oo", "ऋ": "ri",
    "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au", "ऑ": "o", "ऍ": "a",
}
_DEV_MATRAS = {
    "ा": "aa", "ि": "i", "ी": "ee", "ु": "u", "ू": "oo", "ृ": "ri",
    "े": "e", "ै": "ai", "ो": "o", "ौ": "au", "ॉ": "o", "ॅ": "a",
}
_DEV_CONSONANTS = {
    "क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "ng",
    "च": "ch", "छ": "chh", "ज": "j", "झ": "jh", "ञ": "ny",
    "ट": "t", "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n",
    "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n",
    "प": "p", "फ": "ph", "ब": "b", "भ": "bh", "म": "m",
    "य": "y", "र": "r", "ल": "l", "व": "v", "श": "sh",
    "ष": "sh", "स": "s", "ह": "h", "ळ": "l",
    "क़": "q", "ख़": "kh", "ग़": "gh", "ज़": "z", "ड़": "d", "ढ़": "dh", "फ़": "f",
}
_DEV_CONJUNCTS = {"क्ष": "ksh", "ज्ञ": "gya", "त्र": "tr", "श्र": "shr"}


def _transliterate_devanagari_token(word: str) -> str:
    """Phonetic schwa-aware Devanagari -> readable Roman Hinglish fallback."""
    s = word.translate(_DEV_TO_ASCII_DIGITS)
    out: List[str] = []
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        # Skip Nukta if already combined or stray
        if ch == "\u093C":
            i += 1
            continue
        if ch == "्":
            i += 1
            continue
        if ch in ("ं", "ँ"):
            next_ch = s[i + 1] if i + 1 < n else ""
            out.append("m" if next_ch in ("प", "फ", "ब", "भ", "म") else "n")
            i += 1
            continue
        if ch == "ः":
            out.append("h")
            i += 1
            continue
        if ch in _DEV_VOWELS:
            out.append(_DEV_VOWELS[ch])
            i += 1
            continue
        if ch in _DEV_MATRAS:
            out.append(_DEV_MATRAS[ch])
            i += 1
            continue

        # Check 2-char Nukta consonant (e.g. ज़, फ़) or 3-char conjunct (e.g. क्ष, त्र)
        base_rom = ""
        step = 1
        if i + 2 < n and s[i:i + 3] in _DEV_CONJUNCTS:
            base_rom = _DEV_CONJUNCTS[s[i:i + 3]]
            step = 3
        elif i + 1 < n and s[i:i + 2] in _DEV_CONSONANTS:
            base_rom = _DEV_CONSONANTS[s[i:i + 2]]
            step = 2
        elif ch in _DEV_CONSONANTS:
            base_rom = _DEV_CONSONANTS[ch]
        else:
            if 32 <= ord(ch) <= 126:
                out.append(ch)
            i += 1
            continue

        out.append(base_rom)
        j = i + step
        if j < n and s[j] == "्":
            i = j + 1
            continue
        if j < n and s[j] in _DEV_MATRAS:
            out.append(_DEV_MATRAS[s[j]])
            i = j + 1
            continue
        # Inherent schwa 'a': suppress word-final schwa unless single-letter syllable or after conjunct
        has_more_dev = any(k < n and (s[k] in _DEV_CONSONANTS or s[k] in _DEV_VOWELS) for k in range(j, n))
        if has_more_dev or len(out) == 1:
            out.append("a")
        i = j

    res = "".join(out)
    res = re.sub(r"aa$", "a", res) if len(res) > 3 and res.endswith("aa") and not word.endswith(("आ", "ा")) else res
    return res


def _extract_scene_roman_vocab(scene: Dict[str, Any]) -> List[str]:
    """Collects clean Roman/English tech & Hinglish words from scene metadata for fuzzy phonetic rescue."""
    chunks = [
        str(scene.get("narration_hinglish") or ""),
        str(scene.get("narration") or ""),
    ]
    vd = scene.get("visual_data") or {}
    if isinstance(vd, dict):
        for k in ("title", "badge", "question", "problem_title", "code_snippet", "kicker", "statement"):
            if vd.get(k):
                chunks.append(str(vd.get(k)))
    raw = " ".join(chunks)
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9_.-]{1,}", raw)
    seen: Set[str] = set()
    vocab: List[str] = []
    for t in tokens:
        tl = t.lower()
        if tl not in seen:
            seen.add(tl)
            vocab.append(t)
    return vocab


def devanagari_word_to_hinglish(word: str, scene_vocab: Optional[List[str]] = None) -> str:
    """
    Converts any word (including Devanagari words or digits) into clean, understandable
    Roman Hinglish / English with zero Devanagari characters left.
    """
    w = str(word or "").translate(_DEV_TO_ASCII_DIGITS).strip()
    if not w:
        return ""
    if not _HAS_DEVANAGARI_RE.search(w):
        return w

    # Preserve leading/trailing punctuation while translating core Devanagari word
    m = re.match(r"^([^A-Za-z0-9\u0900-\u097F]*)(.*?)([^A-Za-z0-9\u0900-\u097F]*)$", w)
    lead, core, trail = m.groups() if m else ("", w, "")
    if not core:
        return lead + trail

    # Direct dictionary lookup
    if core in _HINGLISH_LEXICON:
        return f"{lead}{_HINGLISH_LEXICON[core]}{trail}"

    # Split mixed tokens cleanly and transliterate Devanagari parts
    parts = re.findall(r"[\u0900-\u097F]+|[^\u0900-\u097F]+", core)
    conv_parts: List[str] = []
    for p in parts:
        if not _HAS_DEVANAGARI_RE.search(p):
            conv_parts.append(p)
            continue
        if p in _HINGLISH_LEXICON:
            conv_parts.append(_HINGLISH_LEXICON[p])
            continue
        rom = _transliterate_devanagari_token(p)
        # Phonetic fuzzy match against scene's known English/Hinglish vocabulary
        if scene_vocab and len(rom) >= 4:
            rom_l = rom.lower()
            best_tok, best_score = "", 0.0
            for cand in scene_vocab:
                cl = cand.lower()
                if abs(len(cl) - len(rom_l)) > 4:
                    continue
                sc = difflib.SequenceMatcher(None, rom_l, cl).ratio()
                if sc > best_score:
                    best_score = sc
                    best_tok = cand
            if best_score >= 0.74 and best_tok:
                rom = best_tok
        conv_parts.append(rom)

    out = "".join(conv_parts)
    out = "".join(ch for ch in out if 32 <= ord(ch) <= 126)
    return f"{lead}{out}{trail}".strip()


def normalize_hinglish_subtitle_words(
    word_timestamps: List[Dict[str, Any]],
    aligned_scenes: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """
    Normalizes all karaoke subtitle words to proper Roman Hinglish / English with
    ZERO Devanagari characters or Devanagari digits.
    """
    scene_vocabs: List[tuple] = []
    if aligned_scenes:
        for sc in aligned_scenes:
            scene_vocabs.append((
                float(sc.get("start_time", 0.0)),
                float(sc.get("end_time", 9999.0)),
                _extract_scene_roman_vocab(sc),
            ))

    def _vocab_for_t(t_sec: float) -> Optional[List[str]]:
        for st_t, en_t, voc in scene_vocabs:
            if st_t - 0.15 <= t_sec <= en_t + 0.15:
                return voc
        return scene_vocabs[0][2] if scene_vocabs else None

    normalized: List[Dict[str, Any]] = []
    for item in word_timestamps:
        w_copy = dict(item)
        raw_w = str(item.get("word", "")).strip()
        voc = _vocab_for_t(float(item.get("start", 0.0)))
        hing_w = devanagari_word_to_hinglish(raw_w, scene_vocab=voc)
        hing_w = "".join(ch for ch in hing_w if 32 <= ord(ch) <= 126).strip()
        if hing_w:
            w_copy["word"] = hing_w
            normalized.append(w_copy)
    return normalized


def generate_ass_subtitles(
    word_timestamps: List[Dict[str, Any]],
    output_path: Path = None,
    format_ratio: str = "9:16",
    tone: str = "auto_dynamic",
    aligned_scenes: List[Dict[str, Any]] = None,
    art_style: str = "editorial_dark"
) -> Path:
    """
    Generates an Advanced SubStation Alpha (.ass) subtitle file with viral
    TikTok / Instagram Reels style synchronized to aspect ratio, visual art_style AND script tone:
    - Dynamic highlight colors & kinetic pop matched to chosen/per-scene tone
    - High-contrast opaque pill backing when art_style == 'light_whiteboard'
    - Safe-zone positioning adapted to aspect ratio (9:16, 16:9, 1:1)
    - 100% Roman Hinglish & English rendering (zero Devanagari glyphs or numerals)
    """
    if output_path is None:
        output_path = OUTPUT_DIR / "subtitles.ass"

    word_timestamps = normalize_hinglish_subtitle_words(word_timestamps, aligned_scenes=aligned_scenes)

    if format_ratio == "16:9":
        res_x, res_y = 1920, 1080
        font_size = 52
        margin_v = 110
    elif format_ratio == "1:1":
        res_x, res_y = 1080, 1080
        font_size = 54
        margin_v = 150
    else:  # 9:16
        res_x, res_y = 1080, 1920
        font_size = 62
        margin_v = 420

    # Light-mode canvas needs solid dark pill / heavier outline so white+yellow karaoke text pops cleanly
    is_light_canvas = (str(art_style).lower().strip() in ("light_whiteboard", "studio_white"))
    border_style = 3 if is_light_canvas else 1
    outline_px = 12 if is_light_canvas else 5
    back_col = "&HC80F172A" if is_light_canvas else "&H90000000"

    # ASS Header & Styles - strictly constrained to chosen aspect ratio safe frame
    ass_content = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {res_x}",
        f"PlayResY: {res_y}",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: ReelHighlight,Nirmala UI,{font_size},&H00FFFFFF,&H0000FFFF,&H000F172A,{back_col},-1,0,0,0,100,100,1,0,{border_style},{outline_px},2,2,80,80,{margin_v},1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
    ]

    # Filter out standalone punctuation tokens & enforce smooth non-zero, non-overlapping timestamps
    filtered_words = []
    for w in word_timestamps:
        raw = str(w.get("word", "")).strip()
        cleaned = "".join(ch for ch in raw if ch.isalnum())
        if cleaned:
            w_copy = dict(w)
            w_copy["start"] = max(0.0, float(w.get("start", 0.0)))
            w_copy["end"] = max(w_copy["start"] + 0.08, float(w.get("end", w_copy["start"] + 0.12)))
            filtered_words.append(w_copy)

    filtered_words.sort(key=lambda item: item["start"])
    for idx_w in range(len(filtered_words) - 1):
        cur_w = filtered_words[idx_w]
        nxt_w = filtered_words[idx_w + 1]
        if nxt_w["start"] < cur_w["start"] + 0.05:
            nxt_w["start"] = cur_w["start"] + 0.05
            nxt_w["end"] = max(nxt_w["start"] + 0.08, nxt_w["end"])
        if cur_w["end"] > nxt_w["start"]:
            cur_w["end"] = nxt_w["start"]

    # Intelligent chunking: 1 word for long tech words (>= 8 chars), 2 words for short words
    i = 0
    chunks = []
    while i < len(filtered_words):
        current = filtered_words[i]
        curr_text = current.get("word", "").strip()
        
        # If long word, give it its own chunk to guarantee 0 overflow
        if len(curr_text) >= 8:
            chunks.append([current])
            i += 1
        elif i + 1 < len(filtered_words):
            next_w = filtered_words[i + 1]
            next_text = next_w.get("word", "").strip()
            # If combined length would be too wide, keep separate
            if len(curr_text) + len(next_text) > 13:
                chunks.append([current])
                i += 1
            else:
                chunks.append([current, next_w])
                i += 2
        else:
            chunks.append([current])
            i += 1

    # Highlight color (ASS BGR hex) & kinetic pop scale per tone
    tone_styles = {
        "trusted_dost_guide": (r"\c&H0099D334&\fscx112\fscy112", "trusted_emerald_warm"),
        "senior_hinglish_mentor": (r"\c&H00F8BD38&\fscx110\fscy110", "mentor_cyan_emphasis"),
        "purposeful_hinglish_mentor": (r"\c&H00F8BD38&\fscx110\fscy110", "purposeful_mentor_cyan"),
        "youth_friend_turbo": (r"\c&H002BF6FF&\fscx112\fscy112", "turbo_youth_pop"),
        "mentor_storyteller": (r"\c&H0099D334&\fscx112\fscy112", "mentor_emerald"),
        "fireship_octane": (r"\c&H002BF6FF&\fscx114\fscy114", "electric_yellow"),
        "dramatic_performance": (r"\c&H0024BFFF&\fscx108\fscy108", "amber_drama"),
        "staff_engineer": (r"\c&H00F8BD38&\fscx105\fscy105", "cyber_cyan"),
        "interview_prep": (r"\c&H0099D334&\fscx110\fscy110", "emerald_pop"),
        "conversational_casual": (r"\c&H002BF6FF&\fscx106\fscy106", "warm_yellow"),
    }

    def _tone_for_time(t_sec: float) -> str:
        if tone != "auto_dynamic":
            return tone
        if aligned_scenes:
            for sc in aligned_scenes:
                st_t = float(sc.get("start_time", 0.0))
                en_t = float(sc.get("end_time", 9999.0))
                if st_t <= t_sec <= en_t:
                    return sc.get("scene_tone", "conversational_casual")
        return "fireship_octane"

    for chunk in chunks:
        if not chunk:
            continue

        # For each word in the chunk, generate a micro-event highlighting that word
        for w_idx, current_word in enumerate(chunk):
            w_start = current_word["start"]
            w_end = current_word["end"]
            active_tone = _tone_for_time(w_start)
            hl_tag = tone_styles.get(active_tone, tone_styles["fireship_octane"])[0]

            line_parts = []
            for j, w in enumerate(chunk):
                # Enforce pure ASCII Roman Hinglish / English (zero Devanagari characters in karaoke)
                clean_w = w["word"].upper().strip()
                clean_w = clean_w.replace("—", "-").replace("–", "-").replace("’", "'").replace("“", '"').replace("”", '"')
                # Escape ASS override braces/backslashes so literal symbols never vanish
                clean_w = clean_w.replace("{", "(").replace("}", ")").replace("\\", "/")
                clean_w = "".join(ch for ch in clean_w if 32 <= ord(ch) <= 126)
                if not clean_w:
                    continue
                if j == w_idx:
                    line_parts.append("{" + hl_tag + "}" + clean_w + r"{\r}")
                else:
                    line_parts.append(r"{\c&H00FFFFFF&}" + clean_w)

            if not line_parts:
                continue
            dialogue_text = " ".join(line_parts)
            ass_content.append(
                f"Dialogue: 0,{_format_ass_time(w_start)},{_format_ass_time(w_end)},ReelHighlight,,0,0,0,,{dialogue_text}"
            )

    output_path.write_text("\n".join(ass_content), encoding="utf-8-sig")
    return output_path

def _format_ass_time(seconds: float) -> str:
    """Formats seconds to ASS time format: H:MM:SS.CC"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis >= 100:
        centis = 99
    return f"{hrs}:{mins:02d}:{secs:02d}.{centis:02d}"
