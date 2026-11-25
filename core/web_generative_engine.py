import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.config import DEFAULT_WATERMARK, FORMAT_SPECS, OUTPUT_DIR, VIDEO_FPS, VIDEO_HEIGHT, VIDEO_WIDTH
from core.palette_engine import resolve_studio_world

_PROBE_RESULT: Optional[Tuple[bool, Optional[str]]] = None

_BROWSER_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/google-chrome",
]


def _is_streamlit_cloud() -> bool:
    return os.path.exists("/mount/src") or os.environ.get("STREAMLIT_SHARING_MODE") == "true"


def detect_web_engine() -> Tuple[bool, Optional[str]]:
    """Checks once whether Playwright + headless Chromium/Edge works cleanly without OOM."""
    global _PROBE_RESULT
    if _PROBE_RESULT is not None:
        return _PROBE_RESULT
    if _is_streamlit_cloud():
        _PROBE_RESULT = (False, None)
        return _PROBE_RESULT
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except Exception:
        _PROBE_RESULT = (False, None)
        return _PROBE_RESULT

    exe_path: Optional[str] = None
    for p in _BROWSER_PATHS:
        if os.path.exists(p):
            exe_path = p
            break
    try:
        from playwright.sync_api import sync_playwright
        p = sync_playwright().start()
        kwargs: Dict[str, Any] = {"headless": True, "args": ["--no-sandbox", "--disable-dev-shm-usage"]}
        if exe_path:
            kwargs["executable_path"] = exe_path
        browser = p.chromium.launch(**kwargs)
        browser.close()
        p.stop()
        _PROBE_RESULT = (True, exe_path)
    except Exception:
        _PROBE_RESULT = (False, None)
    return _PROBE_RESULT


def is_web_engine_available() -> bool:
    return detect_web_engine()[0]


def _rgb_css(rgb: Tuple[int, ...]) -> str:
    return f"rgb({int(rgb[0])},{int(rgb[1])},{int(rgb[2])})"


def _rgba_css(rgb: Tuple[int, ...], alpha: float) -> str:
    return f"rgba({int(rgb[0])},{int(rgb[1])},{int(rgb[2])},{alpha:.2f})"


def _build_default_webgl_html(
    scene: Dict[str, Any],
    world: Dict[str, Any],
    width: int,
    height: int,
    watermark: str,
) -> str:
    """
    Zero-dependency HTML5 + 3D Canvas/Shader Web Scene fallback when Gemini gives structured
    data for `dual_generative` without raw HTML — showcases interactive glass UI + live 3D particles!
    """
    vd = scene.get("visual_data") or {}
    title = json.dumps(str(vd.get("title") or scene.get("topic") or "Generative Studio").strip())
    badge = json.dumps(str(vd.get("badge") or "WEBGL STUDIO").strip().upper())
    sub = json.dumps(str(scene.get("narration") or "")[:140])
    nodes_json = json.dumps((vd.get("nodes") or vd.get("steps") or vd.get("items") or [])[:5], ensure_ascii=False)
    bg_top = _rgb_css(world["bg_top"])
    bg_bot = _rgb_css(world["bg_bot"])
    cyan = _rgb_css(world["cyan"])
    purple = _rgb_css(world["purple"])
    emerald = _rgb_css(world["emerald"])
    cyan_ring = _rgba_css(world["cyan"], 0.42)
    em_ring = _rgba_css(world["emerald"], 0.34)
    cyan_glow = _rgba_css(world["cyan"], 0.22)
    purple_glow = _rgba_css(world["purple"], 0.22)
    text_col = _rgb_css(world["text"])
    muted_col = _rgb_css(world["muted"])
    card_bg = "rgba(255,255,255,0.88)" if world.get("is_light") else "rgba(15,23,42,0.78)"
    wm_json = json.dumps(watermark or "")

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/>
<style>
*{{box-sizing:border-box;margin:0;padding:0;font-family:Inter,'Segoe UI',system-ui,sans-serif;}}
body{{width:{width}px;height:{height}px;overflow:hidden;background:linear-gradient(170deg,{bg_top},{bg_bot});color:{text_col};position:relative;}}
canvas#bg3d{{position:absolute;inset:0;width:100%;height:100%;z-index:0;}}
.stage{{position:relative;z-index:2;padding:108px 64px 80px;height:100%;display:flex;flex-direction:column;gap:28px;}}
.badge{{display:inline-flex;align-items:center;gap:12px;padding:10px 24px;border-radius:999px;border:2px solid {cyan};background:{card_bg};color:{cyan};font-weight:800;font-size:24px;width:max-content;box-shadow:0 0 28px {cyan_glow};}}
.dot{{width:12px;height:12px;border-radius:50%;background:{cyan};}}
h1{{font-size:54px;line-height:1.15;font-weight:900;letter-spacing:-0.02em;}}
.cards{{display:flex;flex-direction:column;gap:22px;margin-top:16px;}}
.card{{background:{card_bg};backdrop-filter:blur(18px);border:2px solid rgba(148,163,184,0.28);border-radius:26px;padding:28px 32px;display:flex;align-items:center;gap:24px;box-shadow:0 18px 40px rgba(0,0,0,0.28);transform-origin:center;transition:none;}}
.num{{min-width:62px;height:62px;border-radius:18px;background:linear-gradient(135deg,{cyan},{purple});color:#fff;font-size:26px;font-weight:900;display:flex;align-items:center;justify-content:center;}}
.ctitle{{font-size:30px;font-weight:800;margin-bottom:6px;}}
.csub{{font-size:22px;color:{muted_col};}}
.subbox{{margin-top:auto;margin-bottom:260px;background:{card_bg};border:2px solid {purple};border-radius:24px;padding:28px 32px;font-size:26px;line-height:1.4;box-shadow:0 0 32px {purple_glow};}}
.wm{{position:absolute;top:42px;right:40px;z-index:3;padding:8px 22px;border-radius:999px;background:{card_bg};border:2px solid {cyan};font-size:22px;font-weight:700;}}
</style></head>
<body>
<canvas id="bg3d" width="{width}" height="{height}"></canvas>
<div class="wm" id="wm"></div>
<div class="stage">
  <div class="badge"><span class="dot"></span><span id="badgeTxt"></span></div>
  <h1 id="titleTxt"></h1>
  <div class="cards" id="cardsHost"></div>
  <div class="subbox" id="subTxt"></div>
</div>
<script>
const TITLE={title}, BADGE={badge}, SUB={sub}, NODES={nodes_json}, WM={wm_json};
document.getElementById('titleTxt').textContent=TITLE;
document.getElementById('badgeTxt').textContent=BADGE;
document.getElementById('subTxt').textContent=SUB;
document.getElementById('wm').textContent=WM;
if(!WM) document.getElementById('wm').style.display='none';
const host=document.getElementById('cardsHost');
const list=(Array.isArray(NODES)&&NODES.length)?NODES:[{{name:"Generative 3D Engine",sub:"Real-time HTML5/WebGL pipeline"}},{{name:"Spring Motion",sub:"Frame-exact timeline synchronization"}}];
list.forEach((n,i)=>{{
  const obj=(typeof n==='string')?{{name:n,sub:''}}:n;
  const el=document.createElement('div'); el.className='card';
  el.innerHTML=`<div class="num">0${{i+1}}</div><div><div class="ctitle">${{obj.name||obj.title||obj.label||''}}</div><div class="csub">${{obj.sub||obj.role||obj.desc||''}}</div></div>`;
  host.appendChild(el);
}});
const cv=document.getElementById('bg3d'), ctx=cv.getContext('2d');
window.__setStudioProgress=function(p, curTime, energy){{
  ctx.clearRect(0,0,{width},{height});
  // Rotating 3D wire torus mesh projected cleanly in HTML5 Canvas
  const cx={width}*0.5, cy={height}*0.58, R=310, r=95, rotY=p*Math.PI*2.2, rotX=0.55;
  ctx.lineWidth=2;
  for(let u=0;u<24;u++){{
    const th=u*Math.PI*2/24;
    ctx.beginPath();
    for(let v=0;v<=16;v++){{
      const ph=v*Math.PI*2/16;
      let x=(R+r*Math.cos(ph))*Math.cos(th), y=r*Math.sin(ph), z=(R+r*Math.cos(ph))*Math.sin(th);
      const x1=x*Math.cos(rotY)-z*Math.sin(rotY), z1=x*Math.sin(rotY)+z*Math.cos(rotY);
      const y2=y*Math.cos(rotX)-z1*Math.sin(rotX), z2=y*Math.sin(rotX)+z1*Math.cos(rotX);
      const sc=900/(900-z2*0.6);
      const px=cx+x1*sc, py=cy+y2*sc;
      if(v===0) ctx.moveTo(px,py); else ctx.lineTo(px,py);
    }}
    ctx.strokeStyle=u%2===0?'{cyan_ring}':'{em_ring}';
    ctx.stroke();
  }}
  const cards=host.children;
  for(let i=0;i<cards.length;i++){{
    const g=Math.max(0,Math.min(1,(p - i*0.13)/0.25));
    const ease=1-Math.pow(1-g,3);
    cards[i].style.opacity=ease;
    cards[i].style.transform=`translateY(${{(1-ease)*36}}px) scale(${{0.94+0.06*ease}})`;
    cards[i].style.borderColor=(Math.floor(p*cards.length)===i)?'{cyan}':'rgba(148,163,184,0.28)';
  }}
}};
window.__setStudioProgress(0, 0, 0.5);
</script></body></html>"""


def _wrap_custom_html(raw_html: str, width: int, height: int) -> str:
    txt = str(raw_html or "").strip()
    if "<html" in txt.lower():
        if "__setStudioProgress" not in txt:
            hook = """<script>
window.__setStudioProgress=window.__setStudioProgress||function(p){
  document.documentElement.style.setProperty('--p', p);
  document.querySelectorAll('[data-stage]').forEach((el,i)=>{
    const th=Number(el.getAttribute('data-stage')||i+1)/6;
    el.style.opacity=p>=th?1:Math.max(0,(p-th+0.18)/0.18);
  });
};</script></body>"""
            return txt.replace("</body>", hook)
        return txt
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/>
<style>html,body{{margin:0;padding:0;width:{width}px;height:{height}px;overflow:hidden;background:#070B16;color:#F8FAFC;font-family:Inter,'Segoe UI',sans-serif;}}</style>
</head><body>{txt}
<script>
window.__setStudioProgress=window.__setStudioProgress||function(p){{
  document.documentElement.style.setProperty('--p', p);
}};
</script></body></html>"""


def render_web_generative_frames(
    scene: Dict[str, Any],
    scene_idx: int,
    total_scenes: int = 4,
    format_ratio: str = "9:16",
    watermark: str = DEFAULT_WATERMARK,
    scene_words: List[Dict[str, Any]] = None,
    tone: str = "auto_dynamic",
) -> Optional[List[Path]]:
    """
    Renders true HTML5 / CSS3 / Three.js / WebGL / GSAP / SVG motion graphics deterministically
    at exact 30fps via Playwright + headless Chromium/Edge. Returns None if unavailable so caller
    cleanly routes to pure-Python NumPy 3D Mesh + Shader + Keyframe SVG renderer.
    """
    ok, exe_path = detect_web_engine()
    if not ok:
        return None

    duration = max(1.5, float(scene.get("duration", 5.0)))
    total_frames = max(15, round(duration * VIDEO_FPS))
    spec = FORMAT_SPECS.get(format_ratio, FORMAT_SPECS["9:16"])
    canvas_w = spec.get("width", VIDEO_WIDTH)
    canvas_h = spec.get("height", VIDEO_HEIGHT)

    scene_frames_dir = OUTPUT_DIR / f"scene_{scene_idx:02d}_frames"
    if scene_frames_dir.exists():
        for old_f in scene_frames_dir.glob("frame_*.*"):
            try:
                old_f.unlink()
            except Exception:
                pass
    scene_frames_dir.mkdir(parents=True, exist_ok=True)

    visual_data = scene.get("visual_data") or {}
    effective_tone = (scene.get("scene_tone") or "conversational_casual") if tone == "auto_dynamic" else tone
    art_style = str(visual_data.get("art_style") or scene.get("art_style") or "editorial_dark").strip()
    topic_seed = str(scene.get("topic") or visual_data.get("title") or "").strip()
    world = resolve_studio_world(art_style=art_style, tone=effective_tone, visual_data=visual_data, topic=topic_seed)

    raw_html = str(visual_data.get("html") or visual_data.get("web_code") or "").strip()
    html_doc = _wrap_custom_html(raw_html, canvas_w, canvas_h) if raw_html else _build_default_webgl_html(scene, world, canvas_w, canvas_h, watermark)

    frame_paths: List[Path] = []
    sc_start = float(scene.get("start_time", 0.0))
    try:
        from playwright.sync_api import sync_playwright
        p = sync_playwright().start()
        kwargs: Dict[str, Any] = {"headless": True, "args": ["--no-sandbox", "--disable-dev-shm-usage"]}
        if exe_path:
            kwargs["executable_path"] = exe_path
        browser = p.chromium.launch(**kwargs)
        page = browser.new_page(viewport={"width": canvas_w, "height": canvas_h}, device_scale_factor=1)
        page.set_content(html_doc, wait_until="domcontentloaded", timeout=10000)

        for f in range(total_frames):
            lin_p = f / max(1, total_frames - 1)
            cur_t = sc_start + lin_p * duration
            energy = 0.55
            if scene_words:
                for w in scene_words:
                    ws = float(w.get("start", 0.0))
                    we = float(w.get("end", ws + 0.25))
                    if ws <= cur_t <= we:
                        energy = 0.95
                        break
            page.evaluate(f"if (window.__setStudioProgress) window.__setStudioProgress({lin_p:.5f}, {cur_t:.4f}, {energy:.3f});")
            fpath = scene_frames_dir / f"frame_{f:04d}.jpg"
            page.screenshot(path=str(fpath), type="jpeg", quality=88)
            frame_paths.append(fpath)

        browser.close()
        p.stop()
        return frame_paths
    except Exception:
        return None
