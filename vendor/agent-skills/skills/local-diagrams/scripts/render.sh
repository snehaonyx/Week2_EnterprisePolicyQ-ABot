#!/usr/bin/env bash
# Renders a diagram source file to an image, picking the renderer by input
# extension: .mmd -> Mermaid CLI, .puml -> PlantUML jar, .dot/.gv -> Graphviz.
# Output format is inferred from OUTPUT_FILE's extension (svg/png/pdf).
#
# Usage: render.sh diagram.mmd diagram.svg
set -euo pipefail

INPUT_FILE="$1"
OUTPUT_FILE="$2"
IN_EXT="${INPUT_FILE##*.}"
OUT_EXT="${OUTPUT_FILE##*.}"

find_dot() {
  if command -v dot >/dev/null 2>&1; then
    command -v dot
    return
  fi
  for d in "/c/Program Files/Graphviz"*/bin/dot.exe "/mingw64/bin/dot.exe"; do
    if [ -x "$d" ]; then
      echo "$d"
      return
    fi
  done
  echo "Graphviz's dot not found on PATH. Install it (winget install -e --id Graphviz.Graphviz on Windows, apt/brew install graphviz elsewhere)." >&2
  exit 1
}

find_chrome() {
  if [ -n "${LOCAL_DIAGRAMS_CHROME_PATH:-}" ] && [ -x "$LOCAL_DIAGRAMS_CHROME_PATH" ]; then
    echo "$LOCAL_DIAGRAMS_CHROME_PATH"
    return
  fi
  for c in google-chrome google-chrome-stable chromium chromium-browser microsoft-edge \
           "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
           "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"; do
    if command -v "$c" >/dev/null 2>&1; then
      command -v "$c"
      return
    elif [ -x "$c" ]; then
      echo "$c"
      return
    fi
  done
  echo "No Chrome/Edge/Chromium found. Set LOCAL_DIAGRAMS_CHROME_PATH." >&2
  exit 1
}

case "$IN_EXT" in
  mmd)
    chrome="$(find_chrome)"
    config="$(mktemp -t local-diagrams-puppeteer-config.XXXXXX.json)"
    printf '{"executablePath": "%s"}' "$chrome" > "$config"
    mmdc -i "$INPUT_FILE" -o "$OUTPUT_FILE" -p "$config"
    ;;
  puml)
    jar="${PLANTUML_JAR:-$HOME/.local/share/plantuml/plantuml.jar}"
    if [ ! -f "$jar" ]; then
      echo "PlantUML jar not found at $jar. Set PLANTUML_JAR or download from https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar" >&2
      exit 1
    fi
    out_dir="$(dirname "$OUTPUT_FILE")"
    mkdir -p "$out_dir"
    base_name="$(basename "$INPUT_FILE" .puml)"
    java -jar "$jar" "-t${OUT_EXT}" -o "$out_dir" "$INPUT_FILE"
    generated="$out_dir/$base_name.$OUT_EXT"
    wanted_leaf="$(basename "$OUTPUT_FILE")"
    if [ "$wanted_leaf" != "$base_name.$OUT_EXT" ]; then
      mv -f "$generated" "$OUTPUT_FILE"
    fi
    ;;
  dot|gv)
    dot_bin="$(find_dot)"
    "$dot_bin" "-T${OUT_EXT}" "$INPUT_FILE" -o "$OUTPUT_FILE"
    ;;
  *)
    echo "Unknown diagram extension '.$IN_EXT'. Expected .mmd, .puml, .dot, or .gv." >&2
    exit 1
    ;;
esac

echo "Rendered $INPUT_FILE -> $OUTPUT_FILE"
