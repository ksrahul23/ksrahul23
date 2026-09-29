#!/usr/bin/env python3
"""Generate boot.svg — a README-safe, auto-scrolling terminal session.

A fixed terminal window (clipped viewport) with content laid out at absolute
y positions, plus ONE SMIL animateTransform that pans the content upward in
sync with when each line appears. Result: commands type, output scrolls up and
off-screen, the next prompt enters — like watching a live terminal recording.
Ends frozen on a blinking prompt. The whoami section renders the profile photo.

Pure SMIL: no scripts / no events, so it animates inside GitHub's <img>.

Two render modes:
  (default) TALL fill-down: svg is as tall as all content; lines appear
     sequentially top-to-bottom, like a long terminal screenshot being typed.
  scroll:   fixed terminal window (clipped viewport) that pans up as content
     flows — like watching a live terminal recording.

Usage: python3 make_boot_svg.py [tall|scroll]
"""
import base64
import os
import random
import sys
from collections import Counter
from html import escape

MODE = sys.argv[1] if len(sys.argv) > 1 else "tall"   # "tall" | "scroll"
OUT = "boot.svg" if MODE == "tall" else "boot-scroll.svg"

W = 980
VP_TOP = 36          # first baseline of content inside viewport
VP_H = 640           # viewport height
BOTTOM_KEEP = VP_TOP + VP_H - 40   # content yb that triggers scroll
H = VP_TOP + VP_H + 4              # total svg height

X0 = 24
LH = 21
FONT = "'DejaVu Sans Mono','Menlo','Consolas','Liberation Mono',monospace"
FG = "#d4d4d4"; DIM = "#7a7a7a"; GRN = "#26c281"
BLU = "#569cd6"; YEL = "#ffcb6b"; WHT = "#ffffff"

svg = []             # content elements (absolute coords, will be scrolled)
defs_list = []       # custom defs (clipPath, etc.)
SCROLL = []          # (time, content_bottom_yb) samples
y = 66               # content flow cursor (absolute baseline)
X0_save = X0
random.seed(7)


def esc(s):
    return escape(s, quote=False)


def note(t, yb):
    SCROLL.append((t, yb))


def txt(x, yy, s, fill=FG, size=13.5, begin=None, bold=False):
    b = CUR[0] if begin is None else begin
    svg.append(
        f'<text x="{x}" y="{yy}" font-family="{FONT}" font-size="{size}" '
        f'fill="{fill}"{" font-weight=\"bold\"" if bold else ""} xml:space="preserve" '
        f'opacity="0"><animate attributeName="opacity" to="1" begin="{b:.2f}s" '
        f'dur="0.35s" fill="freeze"/>{esc(s)}</text>'
    )
    note(b, yy + LH)


def type_cmd(s, char_gap=0.055):
    global y
    n = len(s)
    start = CUR[0]
    ch_w = 8.1
    for i, ch in enumerate(s):
        svg.append(
            f'<text x="{X0 + i * ch_w:.1f}" y="{y}" font-family="{FONT}" '
            f'font-size="13.5" fill="{WHT}" xml:space="preserve" opacity="0">'
            f'<animate attributeName="opacity" to="1" begin="{start + i * char_gap:.2f}s" '
            f'dur="0.05s" fill="freeze"/>{esc(ch)}</text>'
        )
    note(start, y + LH)
    CUR[0] = start + n * char_gap + 0.55
    y += LH


def out(lines, fill=FG, stagger=0.10, gap_lh=LH, size=13.5, x=X0):
    global y
    start = CUR[0]
    for i, line in enumerate(lines):
        yy = y + i * gap_lh
        svg.append(
            f'<text x="{x}" y="{yy:.1f}" font-family="{FONT}" font-size="{size}" '
            f'fill="{fill}" xml:space="preserve" opacity="0">'
            f'<animate attributeName="opacity" to="1" begin="{start + i * stagger:.2f}s" '
            f'dur="0.25s" fill="freeze"/>{esc(line)}</text>'
        )
        note(start + i * stagger, yy + LH)
    CUR[0] = start + len(lines) * stagger + 0.35
    y += len(lines) * gap_lh


def prompt_line(label="┌──[rahul@iem-cst]─[~]", money="└─$ "):
    global y
    txt(X0, y, label, GRN); CUR[0] += 0.12
    txt(X0, y + LH, money, GRN)
    return y + LH


def blank(n=1):
    global y
    y += n * LH
    CUR[0] += 0.15


def norm(rows):
    target = Counter(len(r) for r in rows).most_common(1)[0][0]
    fixed = []
    for r in rows:
        while len(r) > target:
            r = r.replace("────", "───", 1)
        if len(r) < target and r.endswith("│"):
            r = r[:-1].ljust(target - 1) + "│"
        fixed.append(r)
    return fixed


CUR = [0.6]  # time cursor

# ─── 1. BOOT / HEADER ───
txt(X0, y, "$ ssh visitor@ksrahul23", DIM); CUR[0] += 0.5; y += LH
out(["connection established.", "welcome to rahul@github"], fill=GRN)
blank()

pl = prompt_line(); CUR[0] += 0.3
y = pl
X0 = X0_save + 4 * 8.1
type_cmd("whoami")
X0 = X0_save

# ─── whoami → PHOTO & IDENTITY ───
photo_path = "profile.jpg" if os.path.exists("profile.jpg") else "profile.png"
if os.path.exists(photo_path):
    with open(photo_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("ascii")
    img_data_uri = f"data:image/jpeg;base64,{img_b64}"
else:
    img_data_uri = ""

img_x = X0_save + 4
img_y = y + 8
img_w = 175
img_h = 175
start = CUR[0]

defs_list.append(
    f'<clipPath id="avatar-clip">'
    f'<rect x="{img_x}" y="{img_y}" width="{img_w}" height="{img_h}" rx="14"/>'
    f'</clipPath>'
)

# Photo card backdrop & image
svg.append(
    f'<rect x="{img_x - 2}" y="{img_y - 2}" width="{img_w + 4}" height="{img_h + 4}" rx="16" '
    f'fill="#1e1e1e" stroke="#26c281" stroke-width="1.5" stroke-opacity="0.7" opacity="0">'
    f'<animate attributeName="opacity" to="1" begin="{start:.2f}s" dur="0.3s" fill="freeze"/>'
    f'</rect>'
)
if img_data_uri:
    svg.append(
        f'<image href="{img_data_uri}" x="{img_x}" y="{img_y}" width="{img_w}" height="{img_h}" '
        f'clip-path="url(#avatar-clip)" preserveAspectRatio="xMidYMid slice" opacity="0">'
        f'<animate attributeName="opacity" to="1" begin="{start:.2f}s" dur="0.35s" fill="freeze"/>'
        f'</image>'
    )

# Status indicator below photo
status_y = img_y + img_h + 20
svg.append(
    f'<circle cx="{img_x + 12}" cy="{status_y - 4}" r="4" fill="{GRN}" opacity="0">'
    f'<animate attributeName="opacity" to="1" begin="{start + 0.2:.2f}s" dur="0.2s" fill="freeze"/>'
    f'</circle>'
    f'<text x="{img_x + 22}" y="{status_y}" font-family="{FONT}" font-size="11.5" fill="{GRN}" opacity="0">'
    f'<animate attributeName="opacity" to="1" begin="{start + 0.2:.2f}s" dur="0.2s" fill="freeze"/>'
    f'active · open for roles</text>'
)
note(start, status_y + LH)

# Identity text to the RIGHT of the photo
TX = img_x + img_w + 32
ident = [
    ("Rahul Kumar Shaw", WHT, True, 16),
    ("", None, False, 0),
    ("Software Engineer · Full-Stack Developer", DIM, False, 13.5),
    ("B.Tech in Computer Science & Technology", DIM, False, 13.5),
    ("Institute of Engineering & Management, Kolkata ('23–'27)", BLU, False, 13.5),
    ("", None, False, 0),
    ("Building decentralized P2P systems, high-performance", FG, False, 13.5),
    ("algorithmic visualizers & scalable full-stack web apps.", FG, False, 13.5),
    ("", None, False, 0),
    ("LeetCode 1755 (Top 8% Global) · 400+ DSA Solved · 3★ CodeChef", GRN, False, 13),
]
ty0 = img_y + 14
for i, (s, color, bold, size) in enumerate(ident):
    if not s:
        continue
    b = start + 0.15 + i * 0.14
    svg.append(
        f'<text x="{TX}" y="{ty0 + i * LH}" font-family="{FONT}" font-size="{size}" '
        f'fill="{color}"{" font-weight=\"bold\"" if bold else ""} xml:space="preserve" '
        f'opacity="0"><animate attributeName="opacity" to="1" begin="{b:.2f}s" '
        f'dur="0.35s" fill="freeze"/>{esc(s)}</text>'
    )
    note(b, ty0 + i * LH + LH)

CUR[0] = max(CUR[0], start + 0.15 + len(ident) * 0.14 + 0.4)
photo_bottom = max(status_y + 10, ty0 + len(ident) * LH)
y = photo_bottom + LH
blank()

# ─── 2. SYSTEM INFO ───
type_cmd("$ fastfetch")
ff = [
    "┌─ SYSTEM ─────────────────────────┬─ FOCUS ───────────────────────────┐",
    "│                                  │                                   │",
    "│ user          Rahul Kumar Shaw   │ Full-Stack Web Applications       │",
    "│ degree        B.Tech in CST      │ Decentralized & P2P Architecture  │",
    "│ college       IEM Kolkata        │ Algorithmic Routing & Systems     │",
    "│ location      Kolkata, India     │ Real-Time WebRTC / WebSockets     │",
    "│ graduation    2027 (CGPA: 8.57)  │ Scalable Backend APIs & DBs       │",
    "│                                  │                                   │",
    "│ intern        legalX (PM Intern) ├─ COMPETITIVE PROGRAMMING ─────────┤",
    "│ editor        VS Code            │                                   │",
    "│ terminal      Bash / Zsh         │ LeetCode    1755 (Top 8% Global)  │",
    "│ languages     Java · Python · C++│ Codeforces  1315 (Pupil)          │",
    "│ frontend      React · Next · Vite│ CodeChef    3-Star Coder          │",
    "│ backend       Node · FastAPI     │ Problems    400+ DSA Solved       │",
    "│                                  │                                   │",
    "└──────────────────────────────────┴───────────────────────────────────┘",
]
out(norm(ff), fill=FG, stagger=0.05)
blank()

# ─── 3. PROJECTS ───
type_cmd("$ ps aux | grep rahul")
out(["PID    PROJECT               STATUS",
     "1024   wemesh-p2p            RUNNING",
     "1512   pathfinding-viz       RUNNING",
     "2048   smart-billr           RUNNING"], fill=FG, stagger=0.15)
blank()
out(["### WeMesh — Decentralized P2P File Sharing & Chat Platform"], fill=YEL)
out(["wemesh/",
     "└─ Fully decentralized peer-to-peer file sharing and real-time chat",
     "   using WebRTC data channels with zero server relays and client-side",
     "   AES E2EE encryption via CryptoJS; Node.js/Socket.IO signaling.",
     "",
     "   React · WebRTC · Node.js · Socket.IO · CryptoJS · Tailwind CSS"], fill=DIM, stagger=0.08)
blank()
out(["### Pathfinding-Visualizer — Interactive Algorithmic Routing"], fill=YEL)
out(["pathfinding-visualizer/",
     "└─ High-performance visualizer in Next.js & React 19 benchmarking",
     "   Dijkstra, BFS, DFS & SPFA algorithms on an interactive 20x40 grid;",
     "   Leaflet & OSRM API integration for planet-scale route animation.",
     "",
     "   Next.js 16 · React 19 · TypeScript · Python · Flask · Leaflet · OSRM API"], fill=DIM, stagger=0.08)
blank()
out(["### Smart-Billr — Automated SaaS Invoice & Finance Platform"], fill=YEL)
out(["smart-billr/",
     "└─ Responsive digital billing platform with asynchronous FastAPI/Celery",
     "   bulk PDF processing and sub-50ms Supabase/PostgreSQL queries.",
     "",
     "   React · Vite · Python · FastAPI · Celery · Supabase · Tailwind CSS"], fill=DIM, stagger=0.08)
blank(2)

# ─── 4. SKILLS ───
type_cmd("$ skills")
sk = [
    "┌──────────────────────┬──────────────────────────────────────────────────────────────┐",
    "│ CATEGORY             │ SKILLS                                                       │",
    "├──────────────────────┼──────────────────────────────────────────────────────────────┤",
    "│ Languages            │ Core Java · Python · C · C++ · JavaScript · TypeScript · SQL │",
    "├──────────────────────┼──────────────────────────────────────────────────────────────┤",
    "│ Frontend             │ React · Next.js · Vite · HTML5 · CSS3 · Tailwind CSS         │",
    "│                      │ Radix UI · Leaflet · Responsive UI/UX                        │",
    "├──────────────────────┼──────────────────────────────────────────────────────────────┤",
    "│ Backend & Services   │ Node.js · Express · FastAPI · Flask · Celery · Socket.IO     │",
    "│                      │ WebRTC · REST APIs · Gunicorn · E2EE Security                │",
    "├──────────────────────┼──────────────────────────────────────────────────────────────┤",
    "│ Databases & Storage  │ Supabase · PostgreSQL · MongoDB · SQL · Database Design      │",
    "├──────────────────────┼──────────────────────────────────────────────────────────────┤",
    "│ Core CS & ML         │ Data Structures & Algorithms · DBMS · Operating Systems      │",
    "│                      │ Computer Networks · OOP · Supervised & Unsupervised Learning │",
    "├──────────────────────┼──────────────────────────────────────────────────────────────┤",
    "│ Certifications       │ Cyber Security Fundamentals (Univ of London)                 │",
    "│                      │ Problem Solving Through Programming in C (IIT Kharagpur)     │",
    "└──────────────────────┴──────────────────────────────────────────────────────────────┘",
]
out(norm(sk), fill=FG, stagger=0.04)
blank()

# ─── 5. SOCIALS ───
type_cmd("$ cat ~/.config/contact")
contacts = [
    ("github", "github.com/ksrahul23"),
    ("linkedin", "linkedin.com/in/rahul-kumar-cst"),
    ("email", "ksrahul2305@gmail.com"),
    ("phone", "+91 7439446172"),
    ("location", "Kolkata, West Bengal, India"),
]
start = CUR[0]
for i, (k, v) in enumerate(contacts):
    yy = y + i * LH
    tj = start + i * 0.18
    svg.append(
        f'<text x="{X0}" y="{yy}" font-family="{FONT}" font-size="13.5" '
        f'xml:space="preserve" opacity="0"><animate attributeName="opacity" to="1" '
        f'begin="{tj:.2f}s" dur="0.25s" fill="freeze"/>'
        f'<tspan fill="{BLU}">{esc(k.ljust(12))}</tspan><tspan fill="{FG}">{esc(v)}</tspan></text>'
    )
    note(tj, yy + LH)
CUR[0] = start + len(contacts) * 0.18 + 0.5
y += len(contacts) * LH
blank(2)

# ─── final prompt + blinking cursor ───
pl = prompt_line(); CUR[0] += 0.3
cx = X0_save + 4 * 8.1
svg.append(
    f'<rect x="{cx:.1f}" y="{pl - 13}" width="8" height="16" fill="{GRN}" opacity="0">'
    f'<animate attributeName="opacity" to="1" begin="{CUR[0]:.2f}s" dur="0.05s" fill="freeze"/>'
    f'<animate attributeName="opacity" values="1;1;0" keyTimes="0;0.5;1" calcMode="discrete" '
    f'dur="1.1s" begin="{CUR[0] + 0.1:.2f}s" repeatCount="indefinite"/></rect>'
)
note(CUR[0], pl + LH)
y += LH

# ─── scroll keyframes (only used in scroll mode: monotonic upward pan) ───
TOTAL = round(CUR[0] + 0.6, 2)
SCROLL.sort(key=lambda e: e[0])
prev_off = 0
kf = [(0.0, 0)]          # (time, offset)
for t, yb in SCROLL:
    off = max(0, yb - BOTTOM_KEEP)
    if off > prev_off:
        kf.append((t, round(off, 1)))
        prev_off = off
kf.append((TOTAL, prev_off))  # hold final offset; keyTimes must end at 1
# dedupe times, clamp keyTimes to (0,1)
seen = {}
for t, off in kf:
    seen[round(min(1.0, max(0.0, t / TOTAL)), 5)] = off
times = sorted(seen)
values = "; ".join(f"0 {-seen[tt]:.1f}" for tt in times)
kt = ";".join(f"{tt:.5f}" for tt in times)
scroll_anim = (
    f'<g clip-path="url(#vp)"><g>'
    f'<animateTransform attributeName="transform" type="translate" '
    f'values="{values}" keyTimes="{kt}" calcMode="linear" '
    f'dur="{TOTAL}s" fill="freeze" repeatCount="1"/>'
)

# ─── assemble ──
extra_defs = "".join(defs_list)
if MODE == "scroll":
    HS = VP_TOP + VP_H + 4
    body_open, body_close = scroll_anim, '</g></g>'
    clipdef = ('<defs><clipPath id="vp"><rect x="6" y="%d" width="%d" height="%d" rx="6"/>'
               '</clipPath>%s</defs>' % (VP_TOP - 4, W - 12, VP_H + 2, extra_defs))
else:
    HS = int(y) + 34          # tall: one svg exactly as high as all content
    body_open, body_close = '', ''
    clipdef = f'<defs>{extra_defs}</defs>' if extra_defs else ''

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {HS}" width="{W}" height="{HS}">',
    clipdef,
    f'<rect width="{W}" height="{HS}" rx="10" fill="#0d0d0d"/>',
    f'<rect x="0" y="0" width="{W}" height="34" rx="10" fill="#161616"/>'
    f'<rect x="0" y="24" width="{W}" height="10" fill="#161616"/>',
    "".join(f'<circle cx="{20 + i * 20}" cy="17" r="6" fill="{c}"/>'
            for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"])),
    f'<text x="{W/2}" y="22" text-anchor="middle" font-family="{FONT}" font-size="12" '
    f'fill="{DIM}">rahul@github — ssh visitor@ksrahul23</text>'
    f'<line x1="0" y1="34" x2="{W}" y2="34" stroke="#222"/>',
    body_open,
    "".join(svg),
    body_close,
    '</svg>',
]
open(OUT, "w", encoding="utf-8").write("".join(parts))
print(f"wrote {OUT}: {MODE} mode, {W}x{HS}, content {int(y)}px, boot {TOTAL}s")
