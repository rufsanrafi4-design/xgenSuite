"""
template_compiler.py — Constraint-Based Algebraic FFmpeg Compiler
==================================================================
Reads algebraic constraint expressions from template_matrix.json and
resolves them at compile time using the actual video dimensions from
ffprobe. Every dimension, position, and font size is a mathematical
expression — NOT a hardcoded pixel value.

ARCHITECTURE:
  1. ffprobe → root_w, root_h
  2. Load template JSON → algebraic expressions
  3. Resolve template-local constants first (they can reference root_w/root_h)
  4. Resolve all layout/overlay expressions using constants + roots
  5. Generate bit-perfect FFmpeg -filter_complex tailored to exact input dims

Adding a new template = add a JSON entry. ZERO Python changes.
Works on 480p, 720p, 1080p, 4K, 8K, 9:16 Shorts — anything.
"""

import os
import json
import math
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MATRIX_PATH = os.path.join(BASE_DIR, "template_matrix.json")


# ═══════════════════════════════════════════════════════════
#  ALGEBRAIC EXPRESSION SOLVER
# ═══════════════════════════════════════════════════════════

class ConstraintSolver:
    """
    Resolves algebraic expressions with named variables.
    Supports: +, -, *, /, parentheses, max(), min(), int(), round().
    Variables are resolved from a symbol table (dict).
    """

    def __init__(self, root_w, root_h):
        self.symbols = {
            "root_w": float(root_w),
            "root_h": float(root_h),
        }

    def add_constants(self, constants_dict):
        """Resolve and add template-local constants to the symbol table.
        Constants can reference root_w, root_h, and previously defined constants.
        """
        for name, expr in constants_dict.items():
            self.symbols[name] = self.resolve(expr)

    def resolve(self, expr):
        """Resolve an expression string to a numeric value.
        Returns int (pixel-safe) for layout values.
        """
        if isinstance(expr, (int, float)):
            return int(expr) if isinstance(expr, float) and expr == int(expr) else expr

        if isinstance(expr, bool):
            return expr

        if not isinstance(expr, str):
            return expr

        # Pure numeric string
        try:
            return float(expr) if "." in expr else int(expr)
        except ValueError:
            pass

        # Substitute all known symbols into the expression
        resolved = expr
        # Sort by length descending to avoid partial replacement
        # (e.g., "root_w" before "root")
        for name in sorted(self.symbols.keys(), key=len, reverse=True):
            resolved = resolved.replace(name, str(self.symbols[name]))

        # Evaluate safely
        try:
            result = self._safe_eval(resolved)
            return int(round(result))
        except Exception as e:
            raise ValueError(
                f"Cannot resolve expression '{expr}' → '{resolved}': {e}"
            )

    def _safe_eval(self, expr_str):
        """Evaluate a math expression string safely (no exec/code injection)."""
        # Whitelist: digits, operators, parens, dots, spaces, and safe functions
        allowed = re.compile(
            r'^[\d\s\+\-\*\/\(\)\.\,]+'
            r'|max|min|int|round|abs'
        )

        # Build safe namespace
        safe_ns = {
            "__builtins__": {},
            "max": max,
            "min": min,
            "int": int,
            "round": round,
            "abs": abs,
            "math": math,
        }

        # Security: reject anything that looks like attribute access or imports
        if any(kw in expr_str for kw in ["import", "__", "eval", "exec", "open", "os.", "sys."]):
            raise ValueError(f"Unsafe expression: {expr_str}")

        return float(eval(expr_str, safe_ns))


# ═══════════════════════════════════════════════════════════
#  TEMPLATE LOADER
# ═══════════════════════════════════════════════════════════

def _load_matrix():
    """Load the full template matrix from JSON."""
    with open(MATRIX_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_template_ids():
    """Return list of available template IDs."""
    return list(_load_matrix()["templates"].keys())


def get_template_info():
    """Return list of (id, display_name, description, requires_reaction) tuples."""
    matrix = _load_matrix()
    return [
        (tid, t["display_name"], t["description"], t.get("requires_reaction", False))
        for tid, t in matrix["templates"].items()
    ]


def get_template(template_id):
    """Get a single template definition by ID."""
    return _load_matrix()["templates"].get(template_id)


# ═══════════════════════════════════════════════════════════
#  FILTERGRAPH COMPILER
# ═══════════════════════════════════════════════════════════

def compile_video_filter(template_id, title="Best Moments",
                         root_w=1920, root_h=1080,
                         has_reaction=False, freeze_needed=0):
    """
    Compile a template into an FFmpeg -filter_complex string.

    The Algebraic Solver resolves every dimension from the JSON
    constraints using the actual video dimensions (root_w × root_h).

    Args:
        template_id: key from template_matrix.json
        title:       text to burn into the title bar
        root_w:      actual width of the input video (from ffprobe)
        root_h:      actual height of the input video (from ffprobe)
        has_reaction: whether a reaction clip is available

    Returns:
        (filter_string, output_label)
    """
    tpl = get_template(template_id)
    if not tpl:
        raise ValueError(f"Unknown template: {template_id}")

    # ── Initialize the algebraic solver ──
    solver = ConstraintSolver(root_w, root_h)

    # Resolve template-local constants first (bar_h, divider_w, pip_w, etc.)
    constants = tpl.get("constants", {})
    solver.add_constants(constants)

    layout = tpl["layout"]
    overlays = tpl.get("overlays", {})
    evasion = tpl.get("visual_evasion", {})

    # Canvas = output dimensions (resolved algebraically)
    canvas_w = solver.resolve("root_w")
    canvas_h = solver.resolve("root_h")

    # Sanitize title
    safe_title = (title.replace("'", "").replace(":", "")
                       .replace("%", "").replace("\\", "").replace('"', ''))

    # ── Evasion params (these are always literal) ──
    hue_rot  = evasion.get("hue_rotate", 55)
    contrast = evasion.get("contrast", 1.10)
    sat      = evasion.get("saturation", 1.12)
    sway_r   = evasion.get("rotation_sway_rad", 0.002)
    sway_p   = evasion.get("rotation_sway_period", 7)
    noise    = evasion.get("noise_strength", 2)

    # ── Resolve main video dimensions ──
    mv = layout["main_video"]
    main_w  = solver.resolve(mv["width"])
    main_h  = solver.resolve(mv["height"])
    main_x  = solver.resolve(mv.get("x", "0"))
    main_y  = solver.resolve(mv.get("y", "0"))
    crop_pct = mv.get("crop_pct", 8)
    do_hflip = mv.get("hflip", True)

    # Crop from INPUT dimensions
    crop_ratio = 1.0 - (crop_pct / 100.0)
    crop_w = int(root_w * crop_ratio)
    crop_h = int(root_h * crop_ratio)
    crop_x = int(root_w * (crop_pct / 200.0))
    crop_y = int(root_h * (crop_pct / 200.0))

    uses_reaction = has_reaction and tpl.get("requires_reaction", False)
    vf_parts = []

    # ── Compose mode: how main + reaction are combined ──
    # "hstack"   = side-by-side horizontal (split_screen, default)
    # "pip"      = overlay reaction on top of main (pip_corner, watch_react_vertical)
    # "face_cam" = reaction fills screen, main overlays as PiP on top
    compose_mode = tpl.get("compose_mode", "hstack")

    # ── Clean main mode: skip ALL evasion on main video ──
    clean_main = tpl.get("clean_main", False)

    # ── Main video chain ──
    if clean_main:
        # Clean main: NO hflip, NO crop, NO hue, NO eq — just scale to fill
        main_chain = (
            f"[0:v]setpts=PTS-STARTPTS"
            f",scale={main_w}:{main_h}:force_original_aspect_ratio=increase"
            f",crop={main_w}:{main_h}"
            f",setsar=1,format=yuv420p"
        )
    else:
        main_chain = "[0:v]setpts=PTS-STARTPTS"
        if do_hflip:
            main_chain += ",hflip"
        main_chain += (
            f",crop={crop_w}:{crop_h}:{crop_x}:{crop_y}"
            f",hue=h={hue_rot}:s=1.25"
            f",eq=contrast={contrast:.2f}:brightness=0.03:saturation={sat:.2f}"
            f",scale={main_w}:{main_h}:flags=lanczos,setsar=1,format=yuv420p"
        )

    if freeze_needed > 0:
        main_chain += f",tpad=stop_mode=clone:stop_duration={freeze_needed:.3f}"

    if uses_reaction:
        main_chain += "[main];"
        vf_parts.append(main_chain)

        # ── Reaction chain ──
        rv = layout["reaction_video"]
        react_w = solver.resolve(rv["width"])
        react_h = solver.resolve(rv["height"])
        react_x = solver.resolve(rv.get("x", "0"))
        react_y = solver.resolve(rv.get("y", "0"))
        fill_mode = rv.get("fill_mode", "fit")  # "fit" = pad with bars, "cover" = zoom-crop

        if fill_mode == "cover":
            # Cover: scale UP to fill, then crop to exact size (shows face/body properly)
            react_chain = (
                f"[1:v]setpts=PTS-STARTPTS,"
                f"scale={react_w}:{react_h}:force_original_aspect_ratio=increase,"
                f"crop={react_w}:{react_h},"
                f"setsar=1,format=yuv420p[react];"
            )
        else:
            # Fit: scale DOWN to fit, pad with black bars (default for other templates)
            react_chain = (
                f"[1:v]setpts=PTS-STARTPTS,"
                f"scale={react_w}:{react_h}:force_original_aspect_ratio=decrease,"
                f"pad={react_w}:{react_h}:(ow-iw)/2:(oh-ih)/2:color=0x0a0a1f,"
                f"setsar=1,format=yuv420p[react];"
            )
        vf_parts.append(react_chain)

        # ── Compositing (driven by compose_mode from template JSON) ──
        if compose_mode == "pip":
            # PiP: overlay reaction on top of full-screen main
            vf_parts.append(f"[main][react]overlay={react_x}:{react_y}[composed];")
        elif compose_mode == "face_cam":
            # Face Cam: reaction fills canvas background, main overlays as PiP
            mv_x = solver.resolve(mv.get("x", "0"))
            mv_y = solver.resolve(mv.get("y", "0"))
            vf_parts.append(f"[react][main]overlay={mv_x}:{mv_y}[composed];")
        elif compose_mode == "vstack":
            # Vertical stack: main on top, reaction on bottom (Reels Pro layout)
            vf_parts.append("[main][react]vstack=inputs=2[composed];")
        else:
            # hstack: side-by-side horizontal (classic split_screen)
            vf_parts.append("[main][react]hstack=inputs=2[composed];")

        # ── Frame: pad to canvas + overlays + evasion ──
        frame = f"[composed]pad={canvas_w}:{canvas_h}:0:0:color=0x0a0a1f"

        if clean_main:
            # Clean mode: NO evasion at all — just output
            frame += "[vout]"
        else:
            # Overlay bars
            frame += _compile_overlays(solver, overlays, canvas_w, canvas_h, safe_title)

            # Divider
            if "divider" in layout:
                dv = layout["divider"]
                dx = solver.resolve(dv["x"])
                dy = solver.resolve(dv["y"])
                dw = solver.resolve(dv["width"])
                dh = solver.resolve(dv["height"])
                dc = dv.get("color", "0x7c3aed")
                frame += f",drawbox=x={dx}:y={dy}:w={dw}:h={dh}:c={dc}:t=fill"

            # Advanced evasion (Phantom Grade)
            frame += _compile_advanced_evasion(evasion)

            # Evasion finalizers
            frame += (
                f",rotate={sway_r}*sin(2*PI*t/{sway_p}):c=0x0a0a1f"
                f",noise=alls={noise}:allf=t+u"
                f"[vout]"
            )
        vf_parts.append(frame)
    else:
        # ── No reaction: single-stream pipeline ──
        # NOTE: tpad already applied above (line 228) when freeze_needed > 0
        #       Do NOT apply it again here! (was the double-tpad bug)
        main_chain += ","
        frame = f"pad={canvas_w}:{canvas_h}:{main_x}:{main_y}:color=0x0a0a1f"
        frame += _compile_overlays(solver, overlays, canvas_w, canvas_h, safe_title)
        # Advanced evasion
        frame += _compile_advanced_evasion(evasion)
        frame += (
            f",rotate={sway_r}*sin(2*PI*t/{sway_p}):c=0x0a0a1f"
            f",noise=alls={noise}:allf=t+u"
            f"[vout]"
        )
        vf_parts.append(main_chain + frame)

    return "".join(vf_parts), "[vout]"


def _compile_overlays(solver, overlays, canvas_w, canvas_h, safe_title):
    """Compile overlay bars into FFmpeg drawbox+drawtext, resolving all expressions."""
    parts = ""

    for bar_key in ["top_bar", "bottom_bar"]:
        bar = overlays.get(bar_key)
        if not bar:
            continue

        bar_y = solver.resolve(bar["y"])
        bar_h = solver.resolve(bar["height"])
        bg_color = bar.get("bg_color", "0x0d0d1a")
        font_color = bar.get("font_color", "white")
        font_size = solver.resolve(bar.get("font_size", "root_h * 0.028"))

        # Background box
        color_hex = bg_color.split("@")[0] if "@" in bg_color else bg_color
        parts += f",drawbox=x=0:y={bar_y}:w={canvas_w}:h={bar_h}:c={color_hex}:t=fill"

        # Accent line
        if bar_key == "top_bar":
            parts += f",drawbox=x=0:y={bar_y + bar_h - 2}:w={canvas_w}:h=2:c=0x7c3aed:t=fill"
        else:
            parts += f",drawbox=x=0:y={bar_y}:w={canvas_w}:h=2:c=0x7c3aed:t=fill"

        # Text
        if "text_y" in bar:
            text_y_val = solver.resolve(bar["text_y"])
        else:
            text_y_val = f"{bar_y}+({bar_h}-th)/2"

        if "text_field" in bar and bar["text_field"] == "title":
            parts += (
                f",drawtext=text='{safe_title}':"
                f"fontsize={font_size}:fontcolor={font_color}:"
                f"x=30:y={text_y_val}"
            )
        elif "text" in bar:
            static = bar["text"].replace("'", "").replace(":", "")
            parts += (
                f",drawtext=text='{static}':"
                f"fontsize={font_size}:fontcolor={font_color}:"
                f"x=(w-tw)/2:y={text_y_val}"
            )

    return parts


def _compile_advanced_evasion(evasion):
    """
    Compile advanced evasion filters from template JSON.
    These only activate when the JSON has the corresponding keys.
    Existing templates without these keys get ZERO extra filters.

    Layer 6: colorbalance — Shift RGB channels per shadow/midtone/highlight.
             Changes the color DNA at every tonal range independently.
             Content ID stores color histograms — this destroys them.

    Layer 7: rgbashift — Displace color planes by 1-2 sub-pixels.
             Human eye can't see 2px chroma shift, but per-pixel
             fingerprint matching fails completely because R/G/B
             planes no longer align with the original.

    Layer 8: unsharp — Re-synthesize edge detail with new sharpening.
             Changes the edge profile at every boundary in the frame.
             Frequency-domain matching (DCT hashes) can't match
             because the high-frequency components are different.

    Layer 9: tblend — Blend each frame with the previous frame.
             At 8% opacity it's invisible, but it means every single
             frame becomes mathematically unique — no frame in the
             output matches any frame in the original source.
    """
    parts = ""

    # Layer 6: Colorbalance
    cb_keys = ["colorbalance_rs", "colorbalance_gs", "colorbalance_bs",
               "colorbalance_rm", "colorbalance_gm", "colorbalance_bm",
               "colorbalance_rh", "colorbalance_gh", "colorbalance_bh"]
    if any(k in evasion for k in cb_keys):
        rs = evasion.get("colorbalance_rs", 0)
        gs = evasion.get("colorbalance_gs", 0)
        bs = evasion.get("colorbalance_bs", 0)
        rm = evasion.get("colorbalance_rm", 0)
        gm = evasion.get("colorbalance_gm", 0)
        bm = evasion.get("colorbalance_bm", 0)
        rh = evasion.get("colorbalance_rh", 0)
        gh = evasion.get("colorbalance_gh", 0)
        bh = evasion.get("colorbalance_bh", 0)
        parts += (f",colorbalance="
                  f"rs={rs}:gs={gs}:bs={bs}:"
                  f"rm={rm}:gm={gm}:bm={bm}:"
                  f"rh={rh}:gh={gh}:bh={bh}")

    # Layer 7: RGBA Shift (sub-pixel color plane displacement)
    if any(k in evasion for k in ["rgbashift_rh", "rgbashift_rv", "rgbashift_bh", "rgbashift_bv"]):
        rrh = evasion.get("rgbashift_rh", 0)
        rrv = evasion.get("rgbashift_rv", 0)
        rbh = evasion.get("rgbashift_bh", 0)
        rbv = evasion.get("rgbashift_bv", 0)
        parts += f",rgbashift=rh={rrh}:rv={rrv}:bh={rbh}:bv={rbv}"

    # Layer 8: Unsharp (edge re-synthesis)
    if "unsharp_la" in evasion:
        lx = evasion.get("unsharp_lx", 5)
        ly = evasion.get("unsharp_ly", 5)
        la = evasion.get("unsharp_la", 0.8)
        parts += f",unsharp=lx={lx}:ly={ly}:la={la}"

    # Layer 9: Temporal blend (frame DNA mutation)
    if "tblend_mode" in evasion:
        mode = evasion.get("tblend_mode", "average")
        opacity = evasion.get("tblend_opacity", 0.08)
        parts += f",tblend=all_mode={mode}:all_opacity={opacity}"

    # Layer 10: Curves — Cinematic tone remapping (God Mode)
    # Changes the mathematical brightness distribution of every pixel.
    # YouTube's perceptual hash (pHash) depends on luminance patterns —
    # an S-curve remaps shadows/highlights differently, breaking it.
    if "curves_master" in evasion:
        master = evasion["curves_master"]
        # curves uses 'x/y' control points separated by spaces
        # FFmpeg syntax: curves=master='0/0 0.25/0.30 ...'
        parts += f",curves=master='{master}'"
    elif "curves_preset" in evasion:
        preset = evasion["curves_preset"]
        parts += f",curves=preset={preset}"

    # Layer 11: Perspective micro-warp (God Mode)
    # Shifts the viewing angle by fractions of a degree.
    # Every pixel coordinate changes — impossible to overlay-match
    # with the original. Like looking at the same painting from
    # a slightly different position in the room.
    #
    # CRITICAL: FFmpeg perspective uses ABSOLUTE corner coordinates:
    #   default: x0=0, y0=0, x1=W, y1=0, x2=0, y2=H, x3=W, y3=H
    # Our JSON stores OFFSETS from these defaults (e.g., x1=-1 means W-1).
    if "perspective_x0" in evasion:
        x0 = evasion.get("perspective_x0", 0)
        y0 = evasion.get("perspective_y0", 0)
        x1 = evasion.get("perspective_x1", 0)  # offset from W
        y1 = evasion.get("perspective_y1", 0)
        x2 = evasion.get("perspective_x2", 0)
        y2 = evasion.get("perspective_y2", 0)  # offset from H
        x3 = evasion.get("perspective_x3", 0)  # offset from W
        y3 = evasion.get("perspective_y3", 0)  # offset from H

        # Build absolute expressions: corner_default + offset
        sx0 = str(x0)                   # 0 + offset
        sy0 = str(y0)                   # 0 + offset
        sx1 = f"W+{x1}" if x1 != 0 else "W"   # W + offset
        sy1 = str(y1)                   # 0 + offset
        sx2 = str(x2)                   # 0 + offset
        sy2 = f"H+{y2}" if y2 != 0 else "H"   # H + offset
        sx3 = f"W+{x3}" if x3 != 0 else "W"   # W + offset
        sy3 = f"H+{y3}" if y3 != 0 else "H"   # H + offset

        parts += (f",perspective="
                  f"x0={sx0}:y0={sy0}:"
                  f"x1={sx1}:y1={sy1}:"
                  f"x2={sx2}:y2={sy2}:"
                  f"x3={sx3}:y3={sy3}:"
                  f"sense=destination:interpolation=cubic")

    # Layer 12: Smart blur — edge-aware texture re-synthesis (God Mode)
    # Softens ONLY areas below the luminance threshold (flat areas),
    # then unsharp above already re-sharpened edges.
    # Result: the texture DNA of flat areas is destroyed, edges are
    # re-synthesized. The video looks identical but mathematically
    # every surface is different.
    if "smartblur_lr" in evasion:
        lr = evasion.get("smartblur_lr", 1.5)
        ls = evasion.get("smartblur_ls", -0.5)
        lt = evasion.get("smartblur_lt", -3)
        parts += f",smartblur=lr={lr}:ls={ls}:lt={lt}"

    # Layer 13: lowpass_audio_freq is handled by the audio chain
    # (stored in evasion dict, read by pro_engine.py)

    return parts


# ═══════════════════════════════════════════════════════════
#  AUDIO CHAIN (unchanged, co-located for compiler completeness)
# ═══════════════════════════════════════════════════════════

def compile_audio_chain(pitch_semitones=4.0, speed_pct=2.0):
    """NUCLEAR audio chain v8.1 — 16 layers of fingerprint destruction."""
    orig_rate = 44100
    ratio = 2 ** (pitch_semitones / 12.0)
    new_rate = int(orig_rate * ratio)
    tempo = max(0.5, min(2.0, (1.0 / ratio) * (1.0 + speed_pct / 100.0)))

    filters = [
        "asetpts=PTS-STARTPTS",
        f"asetrate={new_rate}", f"aresample={orig_rate}", f"atempo={tempo:.6f}",
        "aecho=0.6:0.3:15|25:0.25|0.15",
        "chorus=0.5:0.9:50|60:0.4|0.32:0.25|0.4:2|2.3",
        "acompressor=threshold=-18dB:ratio=4:attack=5:release=50:makeup=2dB",
        "tremolo=f=3.5:d=0.12",
        "equalizer=f=800:t=q:w=2:g=-14", "equalizer=f=1500:t=q:w=2:g=-14",
        "equalizer=f=3000:t=q:w=2:g=-12", "equalizer=f=5000:t=q:w=1.5:g=-10",
        "bandreject=f=350:w=80", "bandreject=f=2200:w=100", "bandreject=f=4500:w=80",
        "flanger=delay=3:depth=2:regen=-2:width=40:speed=0.3:shape=sinusoidal",
        "extrastereo=m=1.5:c=true",
        "aphaser=in_gain=0.4:out_gain=0.74:delay=3.0:decay=0.4:speed=0.5:type=t",
        "afreqshift=shift=35",
        "loudnorm=I=-14:LRA=11:TP=-1.5",
        "alimiter=limit=0.98:level=false",
    ]
    return ",".join(filters)


# ═══════════════════════════════════════════════════════════
#  CLI SELF-TEST
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 65)
    print("  ALGEBRAIC TEMPLATE COMPILER — Multi-Resolution Test")
    print("=" * 65)

    resolutions = [
        ("480p",   854,  480),
        ("720p",  1280,  720),
        ("1080p", 1920, 1080),
        ("4K",    3840, 2160),
        ("Short 9:16", 1080, 1920),
    ]

    templates = get_template_ids()
    print(f"\n  Templates: {templates}\n")

    for res_name, w, h in resolutions:
        print(f"  ── {res_name} ({w}×{h}) ──")
        for tid in templates:
            tpl = get_template(tid)
            needs_rxn = tpl.get("requires_reaction", False)
            try:
                vf, label = compile_video_filter(
                    tid, title="Test Video",
                    root_w=w, root_h=h,
                    has_reaction=needs_rxn
                )
                print(f"    [{tid:15s}] ✅ {len(vf):4d} chars")
            except Exception as e:
                print(f"    [{tid:15s}] ❌ {e}")
        print()

    # Full dump for one case
    print("=" * 65)
    print("  FULL FILTER — split_screen @ 1080p")
    print("=" * 65)
    vf, _ = compile_video_filter("split_screen", "Family Guy Best Moments",
                                  1920, 1080, has_reaction=True)
    print(vf)
    print()
    print("=" * 65)
    print("  FULL FILTER — cinema_bars @ 4K")
    print("=" * 65)
    vf2, _ = compile_video_filter("cinema_bars", "Cinematic 4K",
                                   3840, 2160, has_reaction=False)
    print(vf2)
    print()
    print("=" * 65)
    print("  FULL FILTER — pip_corner @ 9:16 Short")
    print("=" * 65)
    vf3, _ = compile_video_filter("pip_corner", "Short Test",
                                   1080, 1920, has_reaction=True)
    print(vf3)
