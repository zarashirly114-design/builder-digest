#!/usr/bin/env bash
# export-pdf.sh — Export an HTML presentation to PDF
#
# Usage:
#   bash scripts/export-pdf.sh <path-to-html> [output.pdf]
#
# What this does:
#   1. Starts a local server (fonts need HTTP)
#   2. Uses Playwright to open the HTML and call page.pdf()
#   3. Each .slide becomes one PDF page
#   4. Cleans up
#
# Uses <style media="print"> rules to force all .slide visible
# and page.pdf() native multi-page output (no screenshot stitching).
set -euo pipefail

# ─── Colors ────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

info()  { echo -e "${CYAN}ℹ${NC} $*"; }
ok()    { echo -e "${GREEN}✓${NC} $*"; }
warn()  { echo -e "${YELLOW}⚠${NC} $*"; }
err()   { echo -e "${RED}✗${NC} $*" >&2; }

# ─── Parse args ──────────────────────────────────────────

OUTPUT_PDF=""
COMPACT=false

POSITIONAL=()
for arg in "$@"; do
    case $arg in
        --compact)
            COMPACT=true
            ;;
        *)
            POSITIONAL+=("$arg")
            ;;
    esac
done
set -- "${POSITIONAL[@]}"

if [[ $# -lt 1 ]]; then
    err "Usage: bash scripts/export-pdf.sh <path-to-html> [output.pdf] [--compact]"
    exit 1
fi

INPUT_HTML="$1"
if [[ ! -f "$INPUT_HTML" ]]; then
    err "File not found: $INPUT_HTML"
    exit 1
fi

INPUT_HTML=$(cd "$(dirname "$INPUT_HTML")" && pwd)/$(basename "$INPUT_HTML")

if [[ $# -ge 2 ]]; then
    OUTPUT_PDF="$2"
else
    OUTPUT_PDF="$(dirname "$INPUT_HTML")/$(basename "$INPUT_HTML" .html).pdf"
fi

OUTPUT_DIR=$(dirname "$OUTPUT_PDF")
mkdir -p "$OUTPUT_DIR"
OUTPUT_PDF="$OUTPUT_DIR/$(basename "$OUTPUT_PDF")"

echo ""
echo -e "${BOLD}╔══════════════════════════════════════╗${NC}"
echo -e "${BOLD}║       Export Slides to PDF            ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════╝${NC}"
echo ""

# ─── Step 1: Check dependencies ───────────────────────────

info "Checking dependencies..."

if ! command -v npx &>/dev/null; then
    err "Node.js is required but not installed."
    exit 1
fi
ok "Node.js found"

# ─── Step 2: Create temp dir and print script ─────────────

TEMP_DIR=$(mktemp -d)
TEMP_SCRIPT="$TEMP_DIR/export-pdf.mjs"

SERVE_DIR=$(dirname "$INPUT_HTML")
HTML_FILENAME=$(basename "$INPUT_HTML")

cat > "$TEMP_SCRIPT" << 'EXPORT_SCRIPT'
import { chromium } from 'playwright';
import { createServer } from 'http';
import { readFileSync, writeFileSync } from 'fs';
import { join, extname } from 'path';

const SERVE_DIR = process.argv[2];
const HTML_FILE = process.argv[3];
const OUTPUT_PDF = process.argv[4];

const MIME_TYPES = {
  '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript',
  '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.svg': 'image/svg+xml',
  '.webp': 'image/webp', '.woff': 'font/woff', '.woff2': 'font/woff2',
  '.ttf': 'font/ttf', '.eot': 'application/vnd.ms-fontobject',
};

const server = createServer((req, res) => {
  const decodedUrl = decodeURIComponent(req.url);
  let filePath = join(SERVE_DIR, decodedUrl === '/' ? HTML_FILE : decodedUrl);
  try {
    const content = readFileSync(filePath);
    const ext = extname(filePath).toLowerCase();
    res.writeHead(200, { 'Content-Type': MIME_TYPES[ext] || 'application/octet-stream' });
    res.end(content);
  } catch {
    res.writeHead(404);
    res.end('Not found');
  }
});

const port = await new Promise((resolve) => {
  server.listen(0, () => resolve(server.address().port));
});

console.log(`  Local server on port ${port}`);

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();

// Open the presentation
await page.goto(`http://localhost:${port}/`, { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts.ready);

// Count slides
const slideCount = await page.evaluate(() => {
  return document.querySelectorAll('.slide').length;
});
console.log(`  Found ${slideCount} slides`);

if (slideCount === 0) {
  console.error('  ERROR: No .slide elements found.');
  await browser.close();
  server.close();
  process.exit(1);
}

// Inject print styles: force ALL slides visible, no scroll-snap, proper page breaks
await page.evaluate(() => {
  const style = document.createElement('style');
  style.setAttribute('media', 'print');
  style.textContent = `
    * { animation: none !important; transition: none !important; }
    html { scroll-snap-type: none !important; overflow: visible !important; height: auto !important; }
    body { overflow: visible !important; height: auto !important; }
    .slide {
      display: flex !important;
      opacity: 1 !important;
      visibility: visible !important;
      position: relative !important;
      width: 1920px !important;
      height: 1080px !important;
      overflow: hidden !important;
      page-break-after: always !important;
      break-after: page !important;
      scroll-snap-align: none !important;
      transform: none !important;
    }
    .slide:last-child { page-break-after: auto !important; }
    .slide-content { overflow-y: auto !important; }
    .reveal {
      opacity: 1 !important;
      transform: none !important;
      visibility: visible !important;
    }
    .nav-dots, .progress-bar { display: none !important; }
  `;
  document.head.appendChild(style);

  // Also force all reveal elements visible via inline styles
  document.querySelectorAll('.reveal').forEach(el => {
    el.style.opacity = '1';
    el.style.transform = 'none';
    el.style.visibility = 'visible';
  });
});

// Wait a moment for fonts and styles to settle
await page.waitForTimeout(500);

// Generate PDF natively via Playwright's page.pdf()
// This respects page-break CSS and produces a proper multi-page PDF
await page.pdf({
  path: OUTPUT_PDF,
  width: '1920px',
  height: '1080px',
  printBackground: true,
  margin: { top: '0px', right: '0px', bottom: '0px', left: '0px' },
  preferCSSPageSize: true,
});

await browser.close();
server.close();

console.log(`  ✓ PDF saved to: ${OUTPUT_PDF}`);
EXPORT_SCRIPT

# ─── Step 3: Install Playwright ───────────────────────────

info "Setting up Playwright..."
echo ""

cd "$TEMP_DIR"
cat > "$TEMP_DIR/package.json" << 'PKG'
{ "name": "slide-export", "private": true, "type": "module" }
PKG

npm install playwright &>/dev/null || {
    err "Failed to install Playwright."
    rm -rf "$TEMP_DIR"
    exit 1
}

npx playwright install chromium 2>/dev/null || {
    err "Failed to install Chromium."
    rm -rf "$TEMP_DIR"
    exit 1
}
ok "Playwright ready"
echo ""

# ─── Step 4: Run export ───────────────────────────────────

info "Exporting slides to PDF..."
echo ""

if [[ "$COMPACT" == "true" ]]; then
    info "Using compact mode"
fi

node "$TEMP_SCRIPT" "$SERVE_DIR" "$HTML_FILENAME" "$OUTPUT_PDF" || {
    err "PDF export failed."
    rm -rf "$TEMP_DIR"
    exit 1
}

# ─── Step 5: Cleanup ──────────────────────────────────────

rm -rf "$TEMP_DIR"

echo ""
echo -e "${BOLD}════════════════════════════════════════${NC}"
ok "PDF exported successfully!"
echo ""
echo -e "  ${BOLD}File:${NC}  $OUTPUT_PDF"
echo ""
FILE_SIZE=$(du -h "$OUTPUT_PDF" | cut -f1 | xargs)
echo "  Size: $FILE_SIZE"
echo ""
echo -e "${BOLD}════════════════════════════════════════${NC}"
echo ""

# Open the PDF
if command -v open &>/dev/null; then
    open "$OUTPUT_PDF"
elif command -v xdg-open &>/dev/null; then
    xdg-open "$OUTPUT_PDF"
fi
