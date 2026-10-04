#!/usr/bin/env python3
"""
generate_wave.py - builds an animated ASCII "wave" SVG for a GitHub profile README.

A wave sweeps across a little terminal and, column by column, the text it
passes over flips into the next representation:
    HELLO (blocks) -> HELLO in binary -> HELLO in hex -> WORLD -> ...

It's pure SVG + CSS animation (no JavaScript), so GitHub renders it.

Usage:
    python generate_wave.py          # writes wave.svg
"""

from html import escape

# ------------------------------------------------------------------ config --

FRAMES = [
    # text  : the word to draw with the block font below
    # fill  : which characters make up the letters:
    #         "solid", "binary", "hex", "decimal", or any custom string
    #         (a custom string is repeated to fill the shape)
    # label : the "command" shown at the bottom of the terminal
    # color : text color for this frame
    {"text": "HELLO", "fill": "solid",  "label": "$ echo hello",          "color": "#e6edf3"},
    {"text": "HELLO", "fill": "binary", "label": "$ echo hello | xxd -b", "color": "#3fb950"},
    {"text": "HELLO", "fill": "hex",    "label": "$ echo hello | xxd -p", "color": "#d29922"},
    {"text": "WORLD", "fill": "solid",  "label": "$ echo world",          "color": "#bc8cff"},
]

OUTPUT = "wave.svg"
TITLE = "hello.sh"

STEP = 0.035        # seconds for the wave to advance one column (lower = faster)
HOLD = 2.4          # seconds each frame stays fully visible
WAVE_W = 8          # wave width in columns
X_SCALE = 2         # each font pixel is this many characters wide
LETTER_GAP = 2      # blank columns between letters
MARGIN = 4          # blank columns left/right of the text
PAD_TOP, PAD_BOTTOM = 2, 1   # blank rows above/below the text (room for the wave)

FONT_SIZE = 14
CHAR_W = 8.6        # horizontal distance between columns, px
LINE_H = 17         # vertical distance between rows, px

COLORS = {
    "bg": "#0d1117", "border": "#30363d", "title": "#7d8590", "label": "#7d8590",
    "surface": "#79c0ff", "body": "#1f6feb", "spray": "#cae8ff",
}

# ------------------------------------------------------- 5x5 block font --

FONT = {
    "A": [".###.", "#...#", "#####", "#...#", "#...#"],
    "B": ["####.", "#...#", "####.", "#...#", "####."],
    "C": [".####", "#....", "#....", "#....", ".####"],
    "D": ["####.", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "####.", "#....", "#####"],
    "F": ["#####", "#....", "####.", "#....", "#...."],
    "G": [".####", "#....", "#..##", "#...#", ".###."],
    "H": ["#...#", "#...#", "#####", "#...#", "#...#"],
    "I": ["#####", "..#..", "..#..", "..#..", "#####"],
    "J": ["..###", "...#.", "...#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "###..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "####.", "#....", "#...."],
    "Q": [".###.", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "####.", "#..#.", "#...#"],
    "S": [".####", "#....", ".###.", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#.#.#", "##.##", "#...#"],
    "X": ["#...#", ".#.#.", "..#..", ".#.#.", "#...#"],
    "Y": ["#...#", ".#.#.", "..#..", "..#..", "..#.."],
    "Z": ["#####", "...#.", "..#..", ".#...", "#####"],
    "0": [".###.", "#..##", "#.#.#", "##..#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", ".###."],
    "2": ["####.", "....#", ".###.", "#....", "#####"],
    "3": ["####.", "....#", ".###.", "....#", "####."],
    "4": ["#...#", "#...#", "#####", "....#", "....#"],
    "5": ["#####", "#....", "####.", "....#", "####."],
    "6": [".###.", "#....", "####.", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", "..#.."],
    "8": [".###.", "#...#", ".###.", "#...#", ".###."],
    "9": [".###.", "#...#", ".####", "....#", ".###."],
    " ": [".....", ".....", ".....", ".....", "....."],
    "!": ["..#..", "..#..", "..#..", ".....", "..#.."],
    "?": [".###.", "#...#", "..##.", ".....", "..#.."],
    ".": [".....", ".....", ".....", ".....", "..#.."],
    "-": [".....", ".....", ".###.", ".....", "....."],
    "'": ["..#..", "..#..", ".....", ".....", "....."],
    ":": [".....", "..#..", ".....", "..#..", "....."],
}
FONT_H = 5


# ----------------------------------------------------------------- build --

def word_mask(text):
    """Draw a word with the block font -> list of rows of '#'/'.'."""
    rows = [""] * FONT_H
    chars = text.upper()
    for i, ch in enumerate(chars):
        glyph = FONT.get(ch, FONT["?"])
        for r in range(FONT_H):
            rows[r] += "".join(px * X_SCALE for px in glyph[r])
            if i < len(chars) - 1:
                rows[r] += "." * LETTER_GAP
    return rows


def fill_stream(text, fill):
    data = text.lower().encode()
    if fill == "solid":
        return "█"
    if fill == "binary":
        return "".join(f"{b:08b}" for b in data)
    if fill == "hex":
        return data.hex()
    if fill == "decimal":
        return "".join(str(b) for b in data)
    return fill.replace(" ", "") or "#"


def frame_grid(frame, width):
    """Return a ROWS x width grid of characters (' ' = empty) for one frame."""
    mask = word_mask(frame["text"])
    left = (width - len(mask[0])) // 2
    stream = fill_stream(frame["text"], frame["fill"])
    grid, k = [], 0
    for _ in range(PAD_TOP):
        grid.append([" "] * width)
    for row in mask:
        line = [" "] * width
        for c, px in enumerate(row):
            if px == "#":
                line[left + c] = stream[k % len(stream)]
                k += 1
        grid.append(line)
    for _ in range(PAD_BOTTOM):
        grid.append([" "] * width)
    return grid


def wave_cells(rows, w):
    """The wave shape: (col, row, char, css_class). Column w-1 is the leading edge."""
    cells = []
    for j in range(w):
        h = max(1, round(rows * (j + 1) / w))   # taller toward the front
        top = rows - h
        for r in range(rows):
            d = r - top
            if d < 0:
                if d == -1 and j >= w - 3:
                    cells.append((j, r, "." if j < w - 1 else "'", "sp"))
                continue
            if d == 0:
                cells.append((j, r, "~", "su"))
            else:
                cells.append((j, r, "░▒▓"[min(2, j * 3 // w)], "bo"))
    return cells


def neg_delay(start, period):
    """CSS animation-delay so an infinite animation is already in phase at load."""
    return (start % period) - period


def build():
    text_w = max(len(word_mask(f["text"])[0]) for f in FRAMES)
    cols = text_w + 2 * MARGIN
    rows = PAD_TOP + FONT_H + PAD_BOTTOM
    n = len(FRAMES)

    n_steps = cols + WAVE_W - 1          # columns the wave front travels
    sweep = n_steps * STEP
    segment = sweep + HOLD
    period = n * segment
    shift = sweep                        # start just after frame 0 has swept in

    content_d = segment - WAVE_W * STEP  # how long a column shows one frame

    pad_x, bar_h = 20, 34
    x0, y0 = pad_x, bar_h + 6
    grid_w, grid_h = cols * CHAR_W, rows * LINE_H
    label_y = y0 + grid_h + 22
    W, H = grid_w + 2 * pad_x, label_y + 16

    def cx(c):
        return x0 + c * CHAR_W

    def cy(r):
        return y0 + (r + 1) * LINE_H - 4

    out = []
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.1f} {H:.1f}" '
        f'width="{W:.0f}" height="{H:.0f}" role="img" aria-label="{escape(FRAMES[0]["text"].lower())}">'
    )
    out.append(f"<title>{escape(' / '.join(f['text'].lower() for f in FRAMES))}</title>")

    pc = lambda d, p: 100 * d / p
    show = pc(content_d, period)
    lab = pc(segment, period)
    sw = pc(sweep, segment)
    css = f"""
text{{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;font-size:{FONT_SIZE}px;white-space:pre}}
.L{{opacity:0;animation:show {period:.3f}s infinite}}
.lab{{opacity:0;font-size:12px;animation:lab {period:.3f}s infinite}}
.wave{{opacity:0;animation:sweep {segment:.3f}s infinite}}
.su{{fill:{COLORS['surface']}}}.bo{{fill:{COLORS['body']}}}.sp{{fill:{COLORS['spray']}}}
@keyframes show{{0%,{show:.4f}%{{opacity:1}}{show + 0.001:.4f}%,100%{{opacity:0}}}}
@keyframes lab{{0%,{lab - 0.001:.4f}%{{opacity:1}}{lab:.4f}%,100%{{opacity:0}}}}
@keyframes sweep{{
0%{{opacity:1;transform:translateX(0px);animation-timing-function:steps({n_steps},end)}}
{sw:.4f}%{{opacity:1;transform:translateX({n_steps * CHAR_W:.2f}px)}}
{sw + 0.001:.4f}%,100%{{opacity:0;transform:translateX({n_steps * CHAR_W:.2f}px)}}}}
@media (prefers-reduced-motion:reduce){{.L,.lab,.wave{{animation:none}}.f0{{opacity:1}}}}
"""
    out.append(f"<style>{css}</style>")
    out.append(
        f'<defs><clipPath id="clip"><rect x="{x0}" y="{y0}" width="{grid_w:.1f}" height="{grid_h}"/></clipPath></defs>'
    )

    # terminal window
    out.append(
        f'<rect x="0.5" y="0.5" width="{W - 1:.1f}" height="{H - 1:.1f}" rx="10" '
        f'fill="{COLORS["bg"]}" stroke="{COLORS["border"]}"/>'
    )
    for i, col in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        out.append(f'<circle cx="{20 + i * 18}" cy="17" r="5.5" fill="{col}"/>')
    out.append(
        f'<text x="{W / 2:.1f}" y="21" text-anchor="middle" fill="{COLORS["title"]}" '
        f'style="font-size:12px">{escape(TITLE)}</text>'
    )

    # content: one <text> per (frame, column), each with its own time window
    for f, frame in enumerate(FRAMES):
        grid = frame_grid(frame, cols)
        for c in range(cols):
            spans = [
                f'<tspan x="{cx(c):.1f}" y="{cy(r)}">{escape(grid[r][c])}</tspan>'
                for r in range(rows) if grid[r][c] != " "
            ]
            if not spans:
                continue
            start = f * segment + (c + WAVE_W) * STEP - shift
            out.append(
                f'<text class="L f{f}" fill="{frame["color"]}" '
                f'style="animation-delay:{neg_delay(start, period):.3f}s">{"".join(spans)}</text>'
            )

    # the wave: one shape, slid across in column-sized steps once per segment
    spans = [
        f'<tspan class="{cls}" x="{cx(j - (WAVE_W - 1)):.1f}" y="{cy(r)}">{ch}</tspan>'
        for j, r, ch, cls in wave_cells(rows, WAVE_W)
    ]
    out.append(
        f'<g clip-path="url(#clip)"><g class="wave" '
        f'style="animation-delay:{neg_delay(-shift, segment):.3f}s"><text>{"".join(spans)}</text></g></g>'
    )

    # labels at the bottom, switching when each wave starts
    for f, frame in enumerate(FRAMES):
        start = f * segment - shift
        out.append(
            f'<text class="lab f{f}" x="{x0}" y="{label_y:.1f}" fill="{COLORS["label"]}" '
            f'style="animation-delay:{neg_delay(start, period):.3f}s">{escape(frame["label"])}</text>'
        )

    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    svg = build()
    with open(OUTPUT, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"wrote {OUTPUT} ({len(svg) / 1024:.1f} KB)")
