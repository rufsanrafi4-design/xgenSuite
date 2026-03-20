"""
seo_generator.py - YouTube SEO Content Generator
=================================================
Generate premium SEO assets for ANY video topic:
Keywords, Titles, Descriptions, Tags, Hashtags,
Hooks, CTAs, and Thumbnail Prompts.
Outputs a premium HTML page.
"""

import os
import sys
import random
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox

try:
    import customtkinter as ctk
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    HAS_CTK = True
except ImportError:
    HAS_CTK = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ─── SEO GENERATION ENGINE ──────────────────────────────────

# Keyword patterns for different content types
KEYWORD_TEMPLATES = [
    "{topic} highlights",
    "{topic} best moments",
    "{topic} funny moments",
    "{topic} compilation",
    "{topic} {year}",
    "best of {topic}",
    "{topic} clips",
    "{topic} scenes",
    "{topic} reactions",
    "{topic} review",
    "{topic} top moments",
    "{topic} must watch",
    "watch {topic}",
    "{topic} fan favorite",
    "{topic} most popular",
    "{show} {character} moments",
    "{show} {character} funny",
    "{topic} viral clips",
    "{topic} unforgettable",
    "{topic} legendary moments",
]

TITLE_FORMULAS = [
    "The Time {character} Actually {action}...",
    "Why {character} {action} (And How {subject} Found Out)",
    "{character}'s Secret {noun} Exposed: The {event} Scandal!",
    "{character} vs. {subject}: The Ultimate {event}",
    "The Chaos of {character}'s \"{event}\" – You Won't Believe the Ending",
    "{show}'s Wildest {noun} Adventure Explained",
    "The \"{event}\" Disaster: When {action} Goes Hilariously Wrong",
    "{character}'s Shocking {noun} at {location}",
    "Best of {character}: The Most {adjective} Moments You Forgot",
    "Top 10 {adjective} Moments from {show} That Broke the Internet",
]

HOOK_TEMPLATES = [
    "Did {character} really {action}?",
    "{character}'s secret just got leaked—and {subject} isn't ready.",
    "You'll never guess why {character} is {action}.",
    "This is the one {show} moment that went too far—see why.",
    "What happens when {character} tries to {action}? Pure chaos.",
]

CTA_TEMPLATES = [
    "Subscribe for more legendary {show} clips!",
    "Which {show} character is your favorite? Tell us in the comments!",
    "Smash that like button if {character} is the real MVP!",
    "Share this with a friend who loves {show}!",
    "Hit the bell so you never miss a {show} moment!",
]

HASHTAG_TEMPLATES = [
    "#{show_tag}", "#BestMoments", "#FunnyMoments", "#Highlights",
    "#Compilation", "#MustWatch", "#Viral", "#{character_tag}",
    "#Comedy", "#Entertainment", "#Trending", "#FYP",
    "#WatchThis", "#TopMoments", "#Legendary"
]

THUMBNAIL_PROMPT_TEMPLATES = [
    "A dramatic close-up of {character} with a shocked expression, mouth open, eyes wide. Bold yellow text overlay '{title_short}'. Red border. Dark cinematic background with motion blur.",
    "Split composition: {character} on the left looking angry/confused, {subject} on the right smirking. Bold white text at bottom. Neon purple lighting accents. High contrast.",
    "Action shot of {character} mid-{action}, with comic-style zoom lines radiating from center. Large bold text '{show}' at top. Fire emoji overlays. Saturated colors.",
    "{character} pointing directly at viewer with surprised face. Background is blurred dramatic scene. Red arrow pointing at something interesting. Text: '{hook_short}' in bold yellow.",
    "Cinematic wide shot of {location} with {character} silhouetted. Moody blue/purple color grading. Minimalist white text overlay. Premium YouTube thumbnail aesthetic.",
]

ADJECTIVES = ["Ridiculous", "Insane", "Hilarious", "Iconic", "Unbelievable",
              "Legendary", "Epic", "Crazy", "Wild", "Shocking"]

NOUNS = ["Transformation", "Discovery", "Reveal", "Mission", "Plan",
         "Stunt", "Challenge", "Secret", "Move", "Performance"]

ACTIONS = ["Did Something Unforgivable", "Crossed the Line", "Lost Everything",
           "Made a Huge Mistake", "Shocked Everyone", "Broke All the Rules",
           "Went Too Far", "Changed Forever", "Got Caught", "Pulled Off the Impossible"]


def generate_seo_assets(topic, show_name="", character="", key_moments=""):
    """Generate complete SEO assets for any video topic."""

    # Parse inputs
    topic = topic.strip()
    show = show_name.strip() or topic.split()[0] if topic else "Show"
    char = character.strip() or "The Main Character"
    moments = [m.strip() for m in key_moments.split("\n") if m.strip()] if key_moments else []

    year = "2026"
    show_tag = show.replace(" ", "")
    char_tag = char.replace(" ", "")
    subject = "Everyone"
    location = "the Studio"

    adj = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    action = random.choice(ACTIONS)
    event = moments[0] if moments else random.choice(NOUNS)
    hook_short = f"{char} {action.lower()}"
    title_short = f"Best of {show}"

    ctx = {
        "topic": topic, "show": show, "character": char,
        "subject": subject, "year": year, "location": location,
        "adjective": adj, "noun": noun, "action": action,
        "event": event, "show_tag": show_tag, "character_tag": char_tag,
        "hook_short": hook_short, "title_short": title_short,
    }

    # Generate Keywords
    keywords = []
    for t in KEYWORD_TEMPLATES[:15]:
        try:
            keywords.append(t.format(**ctx))
        except:
            keywords.append(t.format(topic=topic, show=show, character=char, year=year))
    keywords = list(dict.fromkeys(keywords))[:15]  # dedupe

    # Generate Titles
    titles = []
    random.shuffle(TITLE_FORMULAS)
    for t in TITLE_FORMULAS[:10]:
        try:
            titles.append(t.format(**ctx))
        except:
            titles.append(t.format(show=show, character=char, action=action,
                                    subject=subject, event=event, noun=noun,
                                    adjective=adj, location=location))

    # Generate Short Description
    moment_text = f"From {moments[0]} to {moments[-1]}" if len(moments) >= 2 else f"Featuring the most {adj.lower()} moments"
    short_desc = (
        f"Relive the funniest and most chaotic moments from {show}! "
        f"{moment_text}, we've got the ultimate highlights of {char} and more."
    )
    if len(short_desc) > 180:
        short_desc = short_desc[:177] + "..."

    # Generate Long Description
    long_desc = (
        f"Welcome to the ultimate deep dive into the wildest moments of {show}! "
        f"Whether you're a long-time fan of {char} or just looking for the best in "
        f"entertainment, this collection has it all.\n\n"
    )
    if moments:
        long_desc += (
            f"We cover iconic storylines including "
            f"{', '.join(moments[:3])}{'and more' if len(moments) > 3 else ''}. "
        )
    long_desc += (
        f"Watch as the most {adj.lower()} scenes unfold with sharp wit and unforgettable comedy. "
        f"Don't miss these premium highlights that showcase why {show} remains a fan favorite.\n\n"
        f"📌 Topics covered: {', '.join(keywords[:5])}\n"
        f"🔔 Subscribe for more {show} content!"
    )
    if len(long_desc) > 900:
        long_desc = long_desc[:897] + "..."

    # Generate Tags
    tags = [show, char, topic, f"{show} highlights", f"{char} moments",
            f"best of {show}", f"{show} compilation", f"{show} funny",
            "comedy highlights", "best moments", f"{show} clips",
            "entertainment", "trending", f"{show} {year}", "must watch"]
    tags = list(dict.fromkeys(tags))[:15]

    # Generate Hashtags
    hashtags = []
    for h in HASHTAG_TEMPLATES:
        try:
            hashtags.append(h.format(**ctx))
        except:
            hashtags.append(h.format(show_tag=show_tag, character_tag=char_tag))
    hashtags = list(dict.fromkeys(hashtags))[:10]

    # Generate Hooks
    hooks = []
    random.shuffle(HOOK_TEMPLATES)
    for h in HOOK_TEMPLATES[:5]:
        try:
            hooks.append(h.format(**ctx))
        except:
            hooks.append(h.format(show=show, character=char, action=action.lower(), subject=subject))

    # Generate CTAs
    ctas = []
    for c in CTA_TEMPLATES[:5]:
        try:
            ctas.append(c.format(**ctx))
        except:
            ctas.append(c.format(show=show, character=char))

    # Generate Thumbnail Prompts
    thumb_prompts = []
    for p in THUMBNAIL_PROMPT_TEMPLATES:
        try:
            thumb_prompts.append(p.format(**ctx))
        except:
            thumb_prompts.append(p.format(show=show, character=char, action=action.lower(),
                                           subject=subject, location=location,
                                           title_short=title_short, hook_short=hook_short))

    return {
        "topic": topic,
        "show": show,
        "keywords": keywords,
        "titles": titles,
        "short_desc": short_desc,
        "long_desc": long_desc,
        "tags": tags,
        "hashtags": hashtags,
        "hooks": hooks,
        "ctas": ctas,
        "thumbnail_prompts": thumb_prompts,
    }


# ─── HTML OUTPUT ─────────────────────────────────────────────

def generate_html(assets, output_path):
    """Generate a premium HTML page displaying the SEO assets."""
    keywords_html = "\n".join(f'            <li>{k}</li>' for k in assets["keywords"])
    titles_html = "\n".join(
        f'            <li><span class="num">{i+1:02d}</span> {t}</li>'
        for i, t in enumerate(assets["titles"])
    )
    tags_html = "\n".join(f'            <span class="tag">{t}</span>' for t in assets["tags"])
    hashtags_html = "\n".join(f'            <span class="hashtag">{h}</span>' for h in assets["hashtags"])
    hooks_html = "\n".join(f'            <li>{h}</li>' for h in assets["hooks"])
    ctas_html = "\n".join(f'            <li>{c}</li>' for c in assets["ctas"])
    prompts_html = "\n".join(f'            <li>{p}</li>' for p in assets["thumbnail_prompts"])

    long_desc_html = assets["long_desc"].replace("\n", "<br>")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Generated SEO Assets — {assets['show']}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: 'Inter', sans-serif;
      background: #0a0a14;
      color: #e2e8f0;
      line-height: 1.7;
      padding: 0;
    }}

    /* Header */
    .hero {{
      background: linear-gradient(135deg, #0f0c1a 0%, #1a1040 50%, #0f0c1a 100%);
      border-bottom: 2px solid #7c3aed;
      padding: 50px 20px 40px;
      text-align: center;
    }}
    .hero h1 {{
      font-size: 36px; font-weight: 800;
      background: linear-gradient(135deg, #a78bfa, #7c3aed, #06b6d4);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      margin-bottom: 8px;
    }}
    .hero .subtitle {{
      color: #94a3b8; font-size: 16px; font-weight: 400;
    }}

    /* Main */
    main {{
      max-width: 900px; margin: 0 auto;
      padding: 40px 24px 60px;
    }}

    /* Section */
    .section {{
      margin-bottom: 40px;
      background: #0d0d1a;
      border: 1px solid #1e1b4b;
      border-radius: 16px;
      padding: 28px 32px;
      transition: border-color 0.3s;
    }}
    .section:hover {{
      border-color: #7c3aed;
    }}
    .section h2 {{
      font-size: 18px; font-weight: 700;
      color: #a78bfa; text-transform: uppercase;
      letter-spacing: 2px; margin-bottom: 18px;
      padding-bottom: 10px;
      border-bottom: 1px solid #1e1b4b;
    }}
    .section h2 .icon {{ margin-right: 8px; }}

    /* Lists */
    .section ul {{
      list-style: none; padding: 0;
    }}
    .section ul li {{
      padding: 10px 16px; margin-bottom: 6px;
      background: #12101f;
      border-radius: 8px; border-left: 3px solid #7c3aed;
      font-size: 15px; color: #cbd5e1;
      cursor: pointer; transition: all 0.2s;
      position: relative;
    }}
    .section ul li:hover {{
      background: #1a1630; transform: translateX(4px);
      border-left-color: #a78bfa;
    }}
    .section ul li .num {{
      color: #7c3aed; font-weight: 700; margin-right: 12px;
      font-family: 'JetBrains Mono', monospace;
    }}
    .section ul li::after {{
      content: '📋'; position: absolute; right: 12px; top: 50%;
      transform: translateY(-50%); opacity: 0; transition: opacity 0.2s;
      font-size: 14px;
    }}
    .section ul li:hover::after {{ opacity: 0.5; }}

    /* Descriptions */
    .desc-text {{
      background: #12101f; border-radius: 10px;
      padding: 20px 24px; font-size: 15px;
      line-height: 1.8; color: #cbd5e1;
      border: 1px solid #1e1b4b;
      cursor: pointer; transition: all 0.2s;
    }}
    .desc-text:hover {{
      border-color: #7c3aed;
    }}

    /* Tags & Hashtags */
    .tags-grid {{
      display: flex; flex-wrap: wrap; gap: 8px;
      margin-bottom: 16px;
    }}
    .tag {{
      padding: 8px 16px; border-radius: 20px;
      background: #12101f; border: 1px solid #2d2b55;
      color: #a78bfa; font-size: 13px; font-weight: 500;
      cursor: pointer; transition: all 0.2s;
    }}
    .tag:hover {{
      background: #7c3aed; color: white; border-color: #7c3aed;
      transform: translateY(-2px);
    }}
    .hashtag {{
      padding: 8px 16px; border-radius: 20px;
      background: rgba(6, 182, 212, 0.1);
      border: 1px solid rgba(6, 182, 212, 0.3);
      color: #06b6d4; font-size: 13px; font-weight: 500;
      cursor: pointer; transition: all 0.2s;
    }}
    .hashtag:hover {{
      background: #06b6d4; color: white;
      transform: translateY(-2px);
    }}

    .tags-label {{
      font-size: 13px; font-weight: 600; color: #64748b;
      text-transform: uppercase; letter-spacing: 1px;
      margin-bottom: 10px; margin-top: 16px;
    }}

    /* Copy tooltip */
    .copied {{
      position: fixed; top: 20px; right: 20px;
      background: #22c55e; color: white;
      padding: 10px 20px; border-radius: 8px;
      font-weight: 600; font-size: 14px;
      opacity: 0; transition: opacity 0.3s;
      z-index: 999; pointer-events: none;
    }}
    .copied.show {{ opacity: 1; }}

    /* Footer */
    .footer {{
      text-align: center; padding: 30px;
      color: #4a4a6a; font-size: 13px;
      border-top: 1px solid #1e1b4b;
    }}

    @media (max-width: 768px) {{
      main {{ padding: 20px 16px; }}
      .section {{ padding: 20px; }}
      .hero h1 {{ font-size: 26px; }}
    }}
  </style>
</head>
<body>
  <div class="hero">
    <h1>Generated SEO Assets</h1>
    <p class="subtitle">Premium optimized content for <strong>{assets['topic']}</strong> — Click any item to copy</p>
  </div>

  <div class="copied" id="copiedToast">✓ Copied to clipboard!</div>

  <main>
    <!-- Keywords -->
    <div class="section">
      <h2><span class="icon">🔑</span>Keywords</h2>
      <ul>
{keywords_html}
      </ul>
    </div>

    <!-- Title Ideas -->
    <div class="section">
      <h2><span class="icon">💡</span>Title Ideas</h2>
      <ul>
{titles_html}
      </ul>
    </div>

    <!-- Short Description -->
    <div class="section">
      <h2><span class="icon">📝</span>Short Description</h2>
      <div class="desc-text" onclick="copyText(this)">{assets['short_desc']}</div>
    </div>

    <!-- Long Description -->
    <div class="section">
      <h2><span class="icon">📄</span>Long Description</h2>
      <div class="desc-text" onclick="copyText(this)">{long_desc_html}</div>
    </div>

    <!-- Tags & Hashtags -->
    <div class="section">
      <h2><span class="icon">🏷️</span>Tags & Hashtags</h2>
      <div class="tags-label">Search Tags</div>
      <div class="tags-grid">
{tags_html}
      </div>
      <div class="tags-label">Social Hashtags</div>
      <div class="tags-grid">
{hashtags_html}
      </div>
    </div>

    <!-- Hooks & CTA -->
    <div class="section">
      <h2><span class="icon">🎣</span>Hooks & Call to Action</h2>
      <div class="tags-label">Attention Hooks</div>
      <ul>
{hooks_html}
      </ul>
      <div class="tags-label" style="margin-top:20px;">Conversion CTAs</div>
      <ul>
{ctas_html}
      </ul>
    </div>

    <!-- Thumbnail Prompts -->
    <div class="section">
      <h2><span class="icon">🖼️</span>5 Thumbnail Prompts</h2>
      <ul>
{prompts_html}
      </ul>
    </div>
  </main>

  <div class="footer">
    Generated by SEO Content Generator — Pro Video Processor Suite
  </div>

  <script>
    // Click to copy any list item
    document.querySelectorAll('.section ul li').forEach(li => {{
      li.addEventListener('click', () => {{
        const text = li.textContent.trim().replace(/^\\d{{2}}\\s*/, '');
        navigator.clipboard.writeText(text);
        showCopied();
      }});
    }});

    // Click to copy tags/hashtags
    document.querySelectorAll('.tag, .hashtag').forEach(el => {{
      el.addEventListener('click', () => {{
        navigator.clipboard.writeText(el.textContent.trim());
        showCopied();
      }});
    }});

    function copyText(el) {{
      const text = el.innerText || el.textContent;
      navigator.clipboard.writeText(text.trim());
      showCopied();
    }}

    function showCopied() {{
      const toast = document.getElementById('copiedToast');
      toast.classList.add('show');
      setTimeout(() => toast.classList.remove('show'), 1500);
    }}

    // Copy all tags button
    function copyAllTags() {{
      const tags = [...document.querySelectorAll('.tag')].map(t => t.textContent.trim());
      navigator.clipboard.writeText(tags.join(', '));
      showCopied();
    }}
  </script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path


# ─── GUI ─────────────────────────────────────────────────────

class SEOGeneratorApp:
    def __init__(self):
        if HAS_CTK:
            self.root = ctk.CTk()
        else:
            self.root = tk.Tk()

        self.root.title("YouTube SEO Content Generator")
        self.root.geometry("860x700")
        self.root.minsize(700, 600)
        self.root.configure(bg="#0d0d1a")

        self.topic_var = tk.StringVar(value="")
        self.show_var = tk.StringVar(value="")
        self.character_var = tk.StringVar(value="")

        self._build_ui()
        self.root.mainloop()

    def _build_ui(self):
        # ── Header ──
        header = self._frame(self.root)
        header.pack(fill="x", padx=20, pady=(15, 5))
        self._label(header, "SEO CONTENT GENERATOR", size=22, bold=True, color="#a78bfa").pack(side="left")
        self._label(header, "v1.0 | Any Topic → Premium SEO Assets", size=12, color="#64748b").pack(side="left", padx=15)

        # ── Topic ──
        sec1 = self._frame(self.root)
        sec1.pack(fill="x", padx=20, pady=8)
        self._label(sec1, "Video Topic / Content Title", size=14, bold=True).pack(anchor="w")
        self._entry(sec1, self.topic_var).pack(fill="x", pady=4)
        self._label(sec1, 'Example: "The Cleveland Show highlights" or "React to Marvel trailer"',
                    size=11, color="#64748b").pack(anchor="w")

        # ── Show Name ──
        sec2 = self._frame(self.root)
        sec2.pack(fill="x", padx=20, pady=8)

        row2 = self._frame(sec2)
        row2.pack(fill="x")

        col1 = self._frame(row2)
        col1.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._label(col1, "Show / Brand Name", size=13, bold=True).pack(anchor="w")
        self._entry(col1, self.show_var).pack(fill="x", pady=4)

        col2 = self._frame(row2)
        col2.pack(side="left", fill="x", expand=True, padx=(8, 0))
        self._label(col2, "Main Character / Subject", size=13, bold=True).pack(anchor="w")
        self._entry(col2, self.character_var).pack(fill="x", pady=4)

        # ── Key Moments ──
        sec3 = self._frame(self.root)
        sec3.pack(fill="x", padx=20, pady=8)
        self._label(sec3, "Key Moments / Scenes (one per line, optional)", size=13, bold=True).pack(anchor="w")

        if HAS_CTK:
            self.moments_box = ctk.CTkTextbox(sec3, height=120,
                                               fg_color="#1a1a2e", text_color="#e2e8f0",
                                               font=("Consolas", 12), corner_radius=8,
                                               border_color="#2d2b55", border_width=1)
        else:
            self.moments_box = tk.Text(sec3, height=6, bg="#1a1a2e", fg="#e2e8f0",
                                        font=("Consolas", 12), relief="flat", bd=4)
        self.moments_box.pack(fill="x", pady=4)

        self._label(sec3, "Example: egg murder scene, Comic-Con scandal, Cool Olympics",
                    size=11, color="#64748b").pack(anchor="w")

        # ── Generate Buttons ──
        btn_frame = self._frame(self.root)
        btn_frame.pack(fill="x", padx=20, pady=14)

        self._button(btn_frame, "⚡ GENERATE SEO ASSETS", self._generate,
                     width=260, height=48, color="#7c3aed").pack(side="left")
        self._button(btn_frame, "📂 Open Last Output", self._open_last,
                     width=180, height=48, color="#2d2b55").pack(side="left", padx=12)

        # ── Status ──
        self.status_label = self._label(self.root, "Ready — Enter a topic and generate", size=13, color="#64748b")
        self.status_label.pack(padx=20, anchor="w", pady=(5, 5))

        # ── Preview Log ──
        log_frame = self._frame(self.root)
        log_frame.pack(fill="both", expand=True, padx=20, pady=(5, 15))
        self._label(log_frame, "Preview", size=12, bold=True, color="#a78bfa").pack(anchor="w", pady=(0, 4))

        if HAS_CTK:
            self.log_box = ctk.CTkTextbox(log_frame, height=150,
                                           fg_color="#0a0a14", text_color="#c8c8e0",
                                           font=("Consolas", 11), corner_radius=8)
        else:
            self.log_box = tk.Text(log_frame, height=8, bg="#0a0a14", fg="#c8c8e0",
                                    font=("Consolas", 11), relief="flat", bd=0)
        self.log_box.pack(fill="both", expand=True)

        self.last_output = None

    # ── UI Helpers ──
    def _frame(self, parent):
        if HAS_CTK:
            return ctk.CTkFrame(parent, fg_color="transparent")
        return tk.Frame(parent, bg="#0d0d1a")

    def _label(self, parent, text, size=12, bold=False, color="white"):
        weight = "bold" if bold else "normal"
        if HAS_CTK:
            return ctk.CTkLabel(parent, text=text, font=("Segoe UI", size, weight), text_color=color)
        return tk.Label(parent, text=text, font=("Segoe UI", size, weight), fg=color, bg="#0d0d1a")

    def _entry(self, parent, var, width=None):
        if HAS_CTK:
            e = ctk.CTkEntry(parent, textvariable=var, height=36,
                              fg_color="#1a1a2e", border_color="#2d2b55",
                              text_color="white", font=("Consolas", 12), corner_radius=6)
            if width: e.configure(width=width)
            return e
        e = tk.Entry(parent, textvariable=var, bg="#1a1a2e", fg="white",
                     font=("Consolas", 12), relief="flat", bd=4)
        if width: e.configure(width=width // 7)
        return e

    def _button(self, parent, text, command, width=120, height=36, color="#2d2b55"):
        if HAS_CTK:
            return ctk.CTkButton(parent, text=text, command=command,
                                  width=width, height=height,
                                  fg_color=color, hover_color="#5b21b6",
                                  font=("Segoe UI", 13, "bold"), corner_radius=8)
        return tk.Button(parent, text=text, command=command,
                         bg=color, fg="white", font=("Segoe UI", 12, "bold"),
                         relief="flat", bd=0, padx=12, pady=6)

    def _log(self, msg):
        if HAS_CTK:
            self.log_box.insert("end", msg + "\n")
            self.log_box.see("end")
        else:
            self.log_box.insert("end", msg + "\n")
            self.log_box.see("end")

    def _set_status(self, msg, color="#64748b"):
        self.status_label.configure(text=msg)
        if HAS_CTK:
            self.status_label.configure(text_color=color)
        else:
            self.status_label.configure(fg=color)

    # ── Actions ──
    def _generate(self):
        topic = self.topic_var.get().strip()
        if not topic:
            messagebox.showerror("Error", "Please enter a video topic.")
            return

        show = self.show_var.get().strip()
        char = self.character_var.get().strip()

        # Get moments from textbox
        if HAS_CTK:
            moments = self.moments_box.get("0.0", "end").strip()
        else:
            moments = self.moments_box.get("1.0", "end").strip()

        # Clear log
        if HAS_CTK:
            self.log_box.delete("0.0", "end")
        else:
            self.log_box.delete("1.0", "end")

        self._set_status("Generating SEO assets...", "#f59e0b")
        self._log(f"📝 Topic: {topic}")
        self._log(f"🎬 Show: {show or '(auto-detected)'}")
        self._log(f"👤 Character: {char or '(auto-detected)'}")
        self._log("")

        # Generate
        assets = generate_seo_assets(topic, show, char, moments)

        # Log preview
        self._log("═" * 50)
        self._log("  GENERATED SEO ASSETS")
        self._log("═" * 50)
        self._log(f"\n🔑 Keywords ({len(assets['keywords'])})")
        for k in assets['keywords'][:5]:
            self._log(f"  • {k}")
        self._log(f"  ... +{len(assets['keywords'])-5} more")

        self._log(f"\n💡 Title Ideas ({len(assets['titles'])})")
        for i, t in enumerate(assets['titles'][:3]):
            self._log(f"  {i+1}. {t}")
        self._log(f"  ... +{len(assets['titles'])-3} more")

        self._log(f"\n📝 Short Description")
        self._log(f"  {assets['short_desc'][:80]}...")

        self._log(f"\n🏷️ Tags: {', '.join(assets['tags'][:5])}...")
        self._log(f"# Hashtags: {' '.join(assets['hashtags'][:5])}...")

        # Save HTML
        output_dir = os.path.join(BASE_DIR, "seo_output")
        os.makedirs(output_dir, exist_ok=True)
        safe_topic = "".join(c if c.isalnum() or c in " -_" else "" for c in topic)[:40].strip()
        output_path = os.path.join(output_dir, f"SEO_{safe_topic}.html")

        generate_html(assets, output_path)
        self.last_output = output_path

        self._log(f"\n✅ Saved to: {output_path}")
        self._set_status(f"✅ Generated! Opening in browser...", "#22c55e")

        # Auto-open in browser
        webbrowser.open(f"file:///{output_path.replace(os.sep, '/')}")

    def _open_last(self):
        if self.last_output and os.path.isfile(self.last_output):
            webbrowser.open(f"file:///{self.last_output.replace(os.sep, '/')}")
        else:
            messagebox.showinfo("Info", "Generate SEO assets first.")


if __name__ == "__main__":
    SEOGeneratorApp()
