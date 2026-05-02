#!/usr/bin/env python3
"""Generate Builder Digest HTML slides from tweet JSON data.

Structure: HEAD (CSS, brand config) + BODY (title slide, N content slides, closing slide) + FOOT (JS)
Brand: NiuXueLi AI . #35c1be . Teal Minimal on Dark
Fonts: Bodoni Moda (display) + DM Sans (body)
"""

import json
import os
import re
import base64
import subprocess
import sys
from datetime import date
from html import escape

# ===========================================
# CONFIGURATION
# ===========================================
DATA_DIR = os.path.expanduser("~/.hermes/skills/builder-digest/data/tweets")
OUTPUT_DIR = os.path.expanduser("~/.hermes/skills/builder-digest/data/output")
SLIDES_CSS_PATH = os.path.expanduser("~/.hermes/skills/builder-digest/data/slides-css.txt")
LOGO_PATH = os.path.expanduser("~/.hermes/skills/builder-digest/data/logo.svg")

TODAY = "2026-04-30"
DATE_OBJ = date(2026, 4, 30)
DATE_DISPLAY = DATE_OBJ.strftime("%B %-d, %Y")  # "April 30, 2026"

TCO_RE = re.compile(r'https?://t\.co/\S+')

# ===========================================
# HELPERS
# ===========================================
def clean_title(text):
    """Strip t.co links from title, preserve emoji."""
    if not text:
        return ""
    return TCO_RE.sub('', text).strip()

def get_title(item):
    """Get best available title: title_zh -> text_zh -> text."""
    t = item.get('title_zh', '') or ''
    if t:
        t = clean_title(t)
        if t.strip():
            return t.strip()
    t = item.get('text_zh', '') or ''
    if t:
        t = TCO_RE.sub('', t).strip()
        # For Chinese, truncate by character count, avoid mid-word split
        if len(t) <= 25:
            return t
        # Try to break at a punctuation or space, otherwise just first 25 chars
        break_chars = ['。', '！', '？', '，', '；', '：', '.', '!', '?', ',', ' ']
        truncated = t[:25]
        # If the 25th char is mid-word (Chinese character), just end cleanly
        return truncated.strip() + '...'
    t = item.get('text', '') or ''
    if t:
        t = TCO_RE.sub('', t).strip()
        words = t[:30].rsplit(' ', 1)[0] if ' ' in t[:30] else t[:25]
        if words.strip():
            return words.strip() + '...'
    return ""

def get_initial(name):
    """Extract initial letter from a name for avatar."""
    name = name.strip()
    if not name:
        return "?"
    parts = name.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return name[0].upper()

def load_logo_b64():
    """Load and base64-encode the logo SVG."""
    with open(LOGO_PATH, 'rb') as f:
        return base64.b64encode(f.read()).decode()

def read_css():
    """Read the slides CSS file."""
    with open(SLIDES_CSS_PATH) as f:
        return f.read()


# ===========================================
# BUILD SLIDES HTML
# ===========================================
def build_head():
    """Build HTML head with CSS, fonts, and brand bar."""
    css_content = read_css()
    logo_b64 = load_logo_b64()

    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Builder Digest - ''' + DATE_DISPLAY + '''</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Bodoni+Moda:opsz,wght@6..12,500;6..12,600;6..12,700&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&display=swap" rel="stylesheet">

    <style>
''' + css_content + '''
    </style>
</head>
<body>

<!-- Progress bar -->
<div class="progress-bar"></div>

<!-- Navigation dots -->
<nav class="nav-dots"></nav>

<!-- Brand bar (global, appears on every slide) -->
<div class="brand-bar">
    <img class="brand-logo" src="data:image/svg+xml;base64,''' + logo_b64 + '''" alt="Logo">
    <span class="brand-name">\u725b\u96ea\u68a8AI</span>
</div>
'''

def build_title_slide(total):
    """Build the title/cover slide."""
    subtitle = "今日创造者精选 \u00b7 " + DATE_DISPLAY
    return '''<section class="slide title-slide">
    <div class="geo-accent"></div>
    <div class="slide-content">
        <h1 class="reveal">Builder Digest</h1>
        <p class="subtitle reveal">''' + subtitle + '''</p>
        <p class="source-credit reveal">精选 ''' + str(total) + ''' 条推文 \u00b7 源自 X/Twitter</p>
    </div>
</section>
'''

def build_content_slide(item, idx, total):
    """Build a single content slide from tweet data."""
    title = get_title(item)
    text = item.get('text', '') or ''
    text_zh = item.get('text_zh', '') or ''
    author = item.get('author_name', '') or ''
    handle = item.get('author_handle', '') or ''
    url = item.get('url', '') or ''
    initial = get_initial(author)

    # Escape for HTML
    title_esc = escape(title)
    text_esc = escape(text)
    text_zh_esc = escape(text_zh)
    author_esc = escape(author)
    handle_esc = escape(handle)

    # Convert newlines to <br>
    text_esc = text_esc.replace('\n', '<br>')
    text_zh_esc = text_zh_esc.replace('\n', '<br>')

    # Determine compact classes based on text length
    is_compact_zh = len(text_zh) > 200
    is_compact_text = len(text) > 200

    # Build HTML parts
    html = '''<section class="slide content-slide">
    <div class="geo-accent"></div>
    <div class="slide-content">
        <span class="slide-number reveal">''' + f"{idx:02d} / {total:02d}" + '''</span>
        <h2 class="slide-headline reveal">''' + title_esc + '''</h2>
'''

    # English text with compact class
    if text_esc:
        text_class = "tweet-original reveal"
        if is_compact_text:
            text_class += " compact-text"
        html += '        <div class="' + text_class + '">' + text_esc + '</div>\n'

    # Chinese text with compact class
    if text_zh_esc:
        zh_class = "tweet-chinese reveal"
        if is_compact_zh:
            zh_class += " compact-zh"
        html += '        <div class="' + zh_class + '">' + text_zh_esc + '</div>\n'

    # Author bar
    html += '''        <div class="author-bar reveal">
            <div class="author-avatar">''' + initial + '''</div>
            <div class="author-info">
                <div class="author-name">''' + author_esc + '''</div>
                <div class="author-handle">@''' + handle_esc + '''</div>
            </div>
            <a href=\"''' + escape(url) + '''\" class=\"source-link\" target=\"_blank\" rel=\"noopener\">
                <span>''' + escape(url) + '''</span>
            </a>
        </div>
    </div>
</section>
'''

    return html


def build_closing_slide():
    """Build the closing/ending slide."""
    return '''<section class="slide closing-slide">
    <div class="geo-accent"></div>
    <div class="slide-content">
        <div class="brand-dot"></div>
        <h2 class="reveal">\u660e\u5929\u89c1</h2>
        <p class="reveal">\u725b\u96ea\u68a8AI \u00b7 Builder Digest</p>
        <div class="contact-section reveal">
            <div class="contact-title">\u8ba2\u9605 &amp; \u5408\u4f5c</div>
            <div class="contact-row">
                <span class="contact-icon">\u2715</span>
                <span class="contact-text">@niuxueli_ai</span>
            </div>
            <div class="contact-row">
                <span class="contact-icon">\u2709</span>
                <span class="contact-text">915746437@qq.com</span>
            </div>
            <div class="qr-note">\u626b\u7801\u5173\u6ce8 \u00b7 \u6bcf\u65e5\u63a8\u9001\u521b\u9020\u8005\u7cbe\u534e</div>
        </div>
    </div>
</section>
'''


def build_js():
    """Build the JavaScript for slide presentation with navigation and animation."""
    return '''<script>
/*
 * SlidePresentation v1.0
 * Handles keyboard nav, touch/swipe, wheel nav, progress bar, nav dots
 */
class SlidePresentation {
    constructor() {
        this.slides = document.querySelectorAll(".slide");
        this.totalSlides = this.slides.length;
        this.currentSlide = 0;
        this.setupIntersectionObserver();
        this.setupKeyboardNav();
        this.setupTouchNav();
        this.setupWheelNav();
        this.setupProgressBar();
        this.setupNavDots();
    }

    setupIntersectionObserver() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("visible");
                    const idx = Array.from(this.slides).indexOf(entry.target);
                    if (idx >= 0) {
                        this.currentSlide = idx;
                        this.updateProgress();
                        this.updateNavDots();
                    }
                }
            });
        }, { threshold: 0.3 });

        this.slides.forEach(slide => observer.observe(slide));
    }

    setupKeyboardNav() {
        document.addEventListener("keydown", (e) => {
            if (e.key === "ArrowDown" || e.key === "ArrowRight" || e.key === " ") {
                e.preventDefault();
                this.next();
            } else if (e.key === "ArrowUp" || e.key === "ArrowLeft") {
                e.preventDefault();
                this.prev();
            } else if (e.key === "Home") {
                e.preventDefault();
                this.goTo(0);
            } else if (e.key === "End") {
                e.preventDefault();
                this.goTo(this.totalSlides - 1);
            } else if (e.key === "PageDown") {
                e.preventDefault();
                this.next(3);
            } else if (e.key === "PageUp") {
                e.preventDefault();
                this.prev(3);
            }
        });
    }

    setupTouchNav() {
        let startY = 0;
        let startX = 0;
        document.addEventListener("touchstart", (e) => {
            startY = e.touches[0].clientY;
            startX = e.touches[0].clientX;
        }, { passive: true });
        document.addEventListener("touchend", (e) => {
            const endY = e.changedTouches[0].clientY;
            const endX = e.changedTouches[0].clientX;
            const dy = endY - startY;
            const dx = endX - startX;
            if (Math.abs(dy) > Math.abs(dx) && Math.abs(dy) > 50) {
                if (dy < 0) this.next();
                else this.prev();
            } else if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 50) {
                if (dx < 0) this.next();
                else this.prev();
            }
        }, { passive: true });
    }

    setupWheelNav() {
        let wheelTimeout = false;
        document.addEventListener("wheel", (e) => {
            if (wheelTimeout) return;
            wheelTimeout = true;
            setTimeout(() => { wheelTimeout = false; }, 800);
            if (e.deltaY > 0) this.next();
            else this.prev();
        }, { passive: true });
    }

    setupProgressBar() {
        const existing = document.querySelector(".progress-bar");
        if (existing) {
            existing.innerHTML = '<div class="progress-fill"></div>';
            this.progressFill = existing.querySelector(".progress-fill");
            return;
        }
        const bar = document.createElement("div");
        bar.className = "progress-bar";
        bar.innerHTML = '<div class="progress-fill"></div>';
        document.body.prepend(bar);
        this.progressFill = bar.querySelector(".progress-fill");
    }

    updateProgress() {
        if (this.progressFill) {
            const pct = ((this.currentSlide + 1) / this.totalSlides) * 100;
            this.progressFill.style.width = pct + "%";
        }
    }

    setupNavDots() {
        this.navDotsContainer = document.querySelector(".nav-dots");
        if (!this.navDotsContainer) return;
        this.navDotsContainer.innerHTML = "";
        for (let i = 0; i < this.totalSlides; i++) {
            const dot = document.createElement("button");
            dot.className = "nav-dot" + (i === 0 ? " active" : "");
            dot.setAttribute("aria-label", "Go to slide " + (i + 1));
            dot.addEventListener("click", () => this.goTo(i));
            this.navDotsContainer.appendChild(dot);
        }
    }

    updateNavDots() {
        const dots = document.querySelectorAll(".nav-dot");
        dots.forEach((dot, i) => {
            dot.classList.toggle("active", i === this.currentSlide);
        });
    }

    next(n) {
        if (n === undefined) n = 1;
        const idx = Math.min(this.currentSlide + n, this.totalSlides - 1);
        this.goTo(idx);
    }

    prev(n) {
        if (n === undefined) n = 1;
        const idx = Math.max(this.currentSlide - n, 0);
        this.goTo(idx);
    }

    goTo(idx) {
        if (idx < 0 || idx >= this.totalSlides) return;
        this.slides[idx].scrollIntoView({ behavior: "smooth" });
    }
}

document.addEventListener("DOMContentLoaded", function() {
    new SlidePresentation();
});
</script>

</body>
</html>'''


def main():
    # Read data files
    data_path = os.path.join(DATA_DIR, TODAY)
    if not os.path.isdir(data_path):
        print(f"ERROR: Data directory not found: {data_path}")
        return

    files = sorted([f for f in os.listdir(data_path) if f.endswith('.json')])
    if not files:
        print(f"ERROR: No JSON files found in {data_path}")
        return

    items = []
    for f in files:
        with open(os.path.join(data_path, f)) as fp:
            try:
                items.append(json.load(fp))
            except json.JSONDecodeError:
                print(f"WARNING: Skipping invalid JSON: {f}")
                continue

    total_items = len(items)
    print(f"Loaded {total_items} items from {data_path}")

    # Build output HTML
    parts = []
    parts.append(build_head())
    parts.append(build_title_slide(total_items))

    for idx, item in enumerate(items):
        parts.append(build_content_slide(item, idx + 1, total_items))

    parts.append(build_closing_slide())
    parts.append(build_js())

    full_html = '\n'.join(parts)

    # Write output
    output_path = os.path.join(OUTPUT_DIR, TODAY, "slides")
    os.makedirs(output_path, exist_ok=True)
    output_file = os.path.join(output_path, f"slides-{TODAY}.html")

    with open(output_file, 'w') as f:
        f.write(full_html)

    total_slides = total_items + 2
    print(f"Generated {total_slides} slides -> {output_file}")
    print(f"  - 1 title slide")
    print(f"  - {total_items} content slides")
    print(f"  - 1 closing slide")

    # ===========================================
    # Phase 2: Generate PDF via export-pdf.sh
    # ===========================================
    print("")
    print("=== Phase 2: Exporting PDF ===")
    pdf_script = os.path.expanduser("~/.hermes/skills/builder-digest/scripts/export-pdf.sh")
    pdf_output = os.path.join(OUTPUT_DIR, TODAY, "slides", f"slides-{TODAY}.pdf")

    if os.path.isfile(pdf_script):
        try:
            result = subprocess.run(
                ["bash", pdf_script, output_file, pdf_output],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                print(f"PDF generated: {pdf_output}")
            else:
                print(f"PDF export failed (exit code {result.returncode})")
                if result.stderr:
                    print(f"  stderr: {result.stderr[:500]}")
                if result.stdout:
                    print(f"  stdout: {result.stdout[:500]}")
        except subprocess.TimeoutExpired:
            print("PDF export timed out after 300s")
        except FileNotFoundError:
            print("export-pdf.sh not found or bash not available")
    else:
        print(f"PDF script not found: {pdf_script}")

    # ===========================================
    # Phase 3: Generate PPTX via gen-pptx.py
    # ===========================================
    print("")
    print("=== Phase 3: Generating PPTX ===")
    pptx_script = os.path.expanduser("~/.hermes/skills/builder-digest/scripts/gen-pptx.py")
    pptx_output = os.path.join(OUTPUT_DIR, TODAY, "slides", f"slides-{TODAY}.pptx")

    if os.path.isfile(pptx_script):
        try:
            result = subprocess.run(
                [sys.executable, pptx_script],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                print(f"PPTX generated: {pptx_output}")
            else:
                print(f"PPTX generation failed (exit code {result.returncode})")
                if result.stderr:
                    print(f"  stderr: {result.stderr[:500]}")
                if result.stdout:
                    print(f"  stdout: {result.stdout[:500]}")
        except subprocess.TimeoutExpired:
            print("PPTX generation timed out after 120s")
    else:
        print(f"PPTX script not found: {pptx_script}")

    print("")
    print("=== All Done ===")
    print(f"  HTML: {output_file}")
    print(f"  PDF:  {pdf_output}")
    print(f"  PPTX: {pptx_output}")


if __name__ == "__main__":
    main()
