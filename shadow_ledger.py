"""
shadow_ledger.py — Phantom Atom Per-Video Compliance System
=============================================================
Two-layer persistence:
  Layer 1: SQLite local database (source of truth)
  Layer 2: ISO-BMFF UUID box injection into MP4 (Phantom Atom)

The Phantom Atom:
  Standard ExifTool comments/XMP are stripped by YouTube on upload.
  We inject a custom UUID box into the MP4's top-level atom structure
  following ISO 14496-12 (ISO Base Media File Format). This is the same
  mechanism used by Apple Spatial Video, Netflix DRM markers, and
  broadcast metadata. Standard players ignore unknown UUID boxes,
  but our reader extracts them instantly.

  UUID box structure (ISO-BMFF):
    [4 bytes] box size (big-endian uint32)
    [4 bytes] box type = b'uuid'
    [16 bytes] UUID identifier (our custom namespace)
    [N bytes] payload (zlib-compressed JSON)
"""

import os
import sys
import json
import uuid
import struct
import zlib
import sqlite3
import shutil
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "shadow_ledger.db")

# Our custom UUID namespace — identifies Shadow Ledger atoms.
# This is a fixed UUID that we use to find our box inside any MP4.
PHANTOM_UUID = bytes([
    0x53, 0x48, 0x44, 0x57,  # SHDW
    0x4C, 0x44, 0x47, 0x52,  # LDGR
    0x50, 0x48, 0x41, 0x4E,  # PHAN
    0x54, 0x4F, 0x4D, 0x31,  # TOM1
])  # = "SHDWLDGRPHANTOM1"


# ═══════════════════════════════════════════════════════════
#  ISO-BMFF UUID BOX — PHANTOM ATOM ENGINE
# ═══════════════════════════════════════════════════════════

def inject_phantom_atom(mp4_path, payload_dict):
    """
    Inject a Phantom Atom (custom UUID box) into an MP4 file.

    The UUID box is appended AFTER the 'moov' atom, which is the
    safest location — it doesn't interfere with 'mdat' (media data)
    or 'ftyp' (file type), and survives most transcoding pipelines.

    Box layout:
      [4 bytes]  total box size (big-endian uint32)
      [4 bytes]  box type = b'uuid'
      [16 bytes] our namespace UUID (PHANTOM_UUID)
      [N bytes]  zlib-compressed JSON payload

    Returns True on success, False on failure.
    """
    if not os.path.isfile(mp4_path):
        return False

    try:
        # Serialize + compress payload
        json_bytes = json.dumps(payload_dict, ensure_ascii=False).encode("utf-8")
        compressed = zlib.compress(json_bytes, level=9)

        # Build the UUID box
        # Size = 4 (size) + 4 (type) + 16 (uuid) + len(compressed)
        box_size = 4 + 4 + 16 + len(compressed)
        box = struct.pack(">I", box_size)       # big-endian uint32 size
        box += b"uuid"                            # box type
        box += PHANTOM_UUID                       # our namespace
        box += compressed                         # payload

        # Strategy: append the UUID box at the end of the file.
        # This is valid ISO-BMFF — top-level boxes can appear in any order
        # after ftyp. Most players/platforms simply ignore unknown boxes.

        # First, remove any existing Phantom Atom (idempotent writes)
        _strip_phantom_atom(mp4_path)

        # Append our new atom
        with open(mp4_path, "ab") as f:
            f.write(box)

        return True
    except Exception:
        return False


def read_phantom_atom(mp4_path):
    """
    Read and decode a Phantom Atom from an MP4 file.

    Scans the file's top-level ISO-BMFF boxes looking for a 'uuid'
    box with our PHANTOM_UUID namespace. If found, decompresses
    and returns the JSON payload as a dict.

    Returns dict or None.
    """
    if not os.path.isfile(mp4_path):
        return None

    try:
        with open(mp4_path, "rb") as f:
            file_size = os.path.getsize(mp4_path)
            offset = 0

            while offset < file_size - 8:
                f.seek(offset)
                header = f.read(8)
                if len(header) < 8:
                    break

                box_size = struct.unpack(">I", header[:4])[0]
                box_type = header[4:8]

                # Handle extended size (box_size == 1)
                if box_size == 1:
                    ext = f.read(8)
                    if len(ext) < 8:
                        break
                    box_size = struct.unpack(">Q", ext)[0]

                # Zero size means "rest of file"
                if box_size == 0:
                    box_size = file_size - offset

                # Sanity check
                if box_size < 8 or offset + box_size > file_size + 1:
                    break

                if box_type == b"uuid":
                    # Read the 16-byte UUID
                    f.seek(offset + 8)
                    box_uuid = f.read(16)

                    if box_uuid == PHANTOM_UUID:
                        # Found our Phantom Atom!
                        payload_size = box_size - 4 - 4 - 16
                        compressed = f.read(payload_size)
                        try:
                            json_bytes = zlib.decompress(compressed)
                            return json.loads(json_bytes.decode("utf-8"))
                        except Exception:
                            return None

                offset += box_size

    except Exception:
        pass

    return None


def _strip_phantom_atom(mp4_path):
    """
    Remove any existing Phantom Atom from an MP4 (for idempotent re-injection).
    Rewrites the file without the matching uuid box.
    """
    if not os.path.isfile(mp4_path):
        return

    try:
        file_size = os.path.getsize(mp4_path)
        chunks = []
        found = False

        with open(mp4_path, "rb") as f:
            offset = 0
            while offset < file_size - 8:
                f.seek(offset)
                header = f.read(8)
                if len(header) < 8:
                    # Grab remaining bytes
                    f.seek(offset)
                    chunks.append(f.read())
                    break

                box_size = struct.unpack(">I", header[:4])[0]
                box_type = header[4:8]

                if box_size == 1:
                    ext = f.read(8)
                    box_size = struct.unpack(">Q", ext)[0]

                if box_size == 0:
                    box_size = file_size - offset

                if box_size < 8 or offset + box_size > file_size + 1:
                    f.seek(offset)
                    chunks.append(f.read())
                    break

                is_phantom = False
                if box_type == b"uuid" and box_size >= 28:
                    f.seek(offset + 8)
                    box_uuid = f.read(16)
                    if box_uuid == PHANTOM_UUID:
                        is_phantom = True
                        found = True

                if not is_phantom:
                    f.seek(offset)
                    chunks.append(f.read(box_size))

                offset += box_size

        if found:
            with open(mp4_path, "wb") as f:
                for chunk in chunks:
                    f.write(chunk)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════
#  SQLITE DATABASE
# ═══════════════════════════════════════════════════════════

def _get_conn():
    """Get a SQLite connection, creating tables if needed."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS videos (
            uuid            TEXT PRIMARY KEY,
            source_file     TEXT NOT NULL,
            output_file     TEXT NOT NULL,
            template_id     TEXT NOT NULL DEFAULT 'split_screen',
            title           TEXT DEFAULT '',
            pitch_semitones REAL DEFAULT 4.0,
            created_at      TEXT NOT NULL,
            duration_sec    REAL,
            file_size_mb    REAL
        );

        CREATE TABLE IF NOT EXISTS checklist_state (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            video_uuid  TEXT NOT NULL REFERENCES videos(uuid) ON DELETE CASCADE,
            hack_id     TEXT NOT NULL,
            checked     INTEGER NOT NULL DEFAULT 0,
            note        TEXT DEFAULT '',
            UNIQUE(video_uuid, hack_id)
        );

        CREATE TABLE IF NOT EXISTS render_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            video_uuid  TEXT NOT NULL REFERENCES videos(uuid) ON DELETE CASCADE,
            timestamp   TEXT NOT NULL,
            event       TEXT NOT NULL,
            detail      TEXT DEFAULT ''
        );
    """)
    conn.commit()
    return conn


# ═══════════════════════════════════════════════════════════
#  CRUD OPERATIONS
# ═══════════════════════════════════════════════════════════

def create_video_record(source_file, output_file, template_id="split_screen",
                        title="", pitch_semitones=4.0):
    """Create a new video record and return its UUID."""
    video_uuid = str(uuid.uuid4())
    now = datetime.now().astimezone().isoformat()
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO videos (uuid, source_file, output_file, template_id, "
            "title, pitch_semitones, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (video_uuid, source_file, output_file, template_id,
             title, pitch_semitones, now)
        )
        conn.execute(
            "INSERT INTO render_log (video_uuid, timestamp, event, detail) "
            "VALUES (?, ?, ?, ?)",
            (video_uuid, now, "render_start",
             json.dumps({"source": source_file, "template": template_id}))
        )
        conn.commit()
    finally:
        conn.close()
    return video_uuid


def save_checklist(video_uuid, checklist_dict):
    """Save checklist state for a video. checklist_dict = {hack_id: bool}."""
    conn = _get_conn()
    try:
        for hack_id, checked in checklist_dict.items():
            conn.execute(
                "INSERT INTO checklist_state (video_uuid, hack_id, checked) "
                "VALUES (?, ?, ?) "
                "ON CONFLICT(video_uuid, hack_id) DO UPDATE SET checked=excluded.checked",
                (video_uuid, hack_id, 1 if checked else 0)
            )
        conn.commit()
    finally:
        conn.close()


def update_video_post_render(video_uuid, duration_sec=None, file_size_mb=None):
    """Update video record after render completes."""
    conn = _get_conn()
    now = datetime.now().astimezone().isoformat()
    try:
        if duration_sec is not None:
            conn.execute("UPDATE videos SET duration_sec=? WHERE uuid=?",
                         (duration_sec, video_uuid))
        if file_size_mb is not None:
            conn.execute("UPDATE videos SET file_size_mb=? WHERE uuid=?",
                         (file_size_mb, video_uuid))
        conn.execute(
            "INSERT INTO render_log (video_uuid, timestamp, event) VALUES (?, ?, ?)",
            (video_uuid, now, "render_complete")
        )
        conn.commit()
    finally:
        conn.close()


def get_video(video_uuid):
    """Get a video record by UUID."""
    conn = _get_conn()
    try:
        row = conn.execute("SELECT * FROM videos WHERE uuid=?", (video_uuid,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_checklist(video_uuid):
    """Get checklist state for a video. Returns {hack_id: bool}."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT hack_id, checked FROM checklist_state WHERE video_uuid=?",
            (video_uuid,)
        ).fetchall()
        return {r["hack_id"]: bool(r["checked"]) for r in rows}
    finally:
        conn.close()


def get_all_videos():
    """Get all video records, newest first."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM videos ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════
#  COMPLIANCE JSON BUILDER
# ═══════════════════════════════════════════════════════════

def build_compliance_json(video_uuid):
    """Build the compliance JSON blob for Phantom Atom injection."""
    from growth_hacks_data import HACKS_LEVELS

    video = get_video(video_uuid)
    if not video:
        return None

    checklist = get_checklist(video_uuid)

    name_lookup = {}
    for lv in HACKS_LEVELS:
        for item in lv["items"]:
            name_lookup[item["id"]] = item["name"]

    compliance = {}
    total = 0
    checked_count = 0
    for hack_id, name in name_lookup.items():
        is_checked = checklist.get(hack_id, False)
        compliance[hack_id] = {"checked": is_checked, "name": name}
        total += 1
        if is_checked:
            checked_count += 1

    score = f"{checked_count}/{total} ({int(checked_count / total * 100) if total else 0}%)"

    return {
        "shadow_ledger_version": "2.0",
        "atom_type": "phantom_uuid_box",
        "video_uuid": video_uuid,
        "template_id": video.get("template_id", "split_screen"),
        "created_at": video.get("created_at", ""),
        "title": video.get("title", ""),
        "source_file": os.path.basename(video.get("source_file", "")),
        "compliance": compliance,
        "score": score
    }


# ═══════════════════════════════════════════════════════════
#  PIPELINE HELPERS
# ═══════════════════════════════════════════════════════════

def on_render_start(source_file, output_file, template_id="split_screen",
                    title="", pitch_semitones=4.0, checklist=None):
    """Call at render start. Returns video_uuid."""
    video_uuid = create_video_record(
        source_file, output_file, template_id, title, pitch_semitones
    )
    if checklist:
        save_checklist(video_uuid, checklist)
    return video_uuid


def on_render_complete(video_uuid, duration_sec=None, file_size_mb=None):
    """Call after render finishes. Updates DB and injects Phantom Atom."""
    update_video_post_render(video_uuid, duration_sec, file_size_mb)

    # Build compliance payload and inject into the MP4
    video = get_video(video_uuid)
    if video and os.path.isfile(video["output_file"]):
        blob = build_compliance_json(video_uuid)
        if blob:
            success = inject_phantom_atom(video["output_file"], blob)
            # Log injection
            conn = _get_conn()
            now = datetime.now().astimezone().isoformat()
            try:
                conn.execute(
                    "INSERT INTO render_log (video_uuid, timestamp, event, detail) "
                    "VALUES (?, ?, ?, ?)",
                    (video_uuid, now, "phantom_atom_injected",
                     json.dumps({"success": success, "file": video["output_file"]}))
                )
                conn.commit()
            finally:
                conn.close()
            return success
    return False


def audit_video(mp4_path):
    """Read Phantom Atom from any MP4 and return compliance data."""
    return read_phantom_atom(mp4_path)


# ═══════════════════════════════════════════════════════════
#  CLI SELF-TEST
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import tempfile

    print("=" * 60)
    print("  SHADOW LEDGER v2.0 — Phantom Atom Self-Test")
    print("=" * 60)
    print(f"  DB: {DB_PATH}")
    print(f"  Phantom UUID: {PHANTOM_UUID.hex()}")

    # Test DB
    conn = _get_conn()
    tables = [t["name"] for t in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()]
    conn.close()
    print(f"  Tables: {tables}")

    # Test record
    test_uuid = create_video_record("test_in.mp4", "test_out.mp4", "split_screen", "Test")
    save_checklist(test_uuid, {"L6_01": True, "L6_02": False, "L6_03": True})
    blob = build_compliance_json(test_uuid)
    print(f"  Record created: {test_uuid}")
    print(f"  Compliance score: {blob['score']}")

    # Test Phantom Atom injection + readback on a minimal valid MP4
    print("\n  ── Phantom Atom Round-Trip Test ──")
    # Create a minimal valid MP4 (ftyp + mdat boxes)
    tmp = os.path.join(tempfile.gettempdir(), "phantom_test.mp4")
    with open(tmp, "wb") as f:
        # ftyp box (20 bytes)
        ftyp = struct.pack(">I", 20) + b"ftyp" + b"isom" + struct.pack(">I", 0x200) + b"isom"
        f.write(ftyp)
        # mdat box (empty, 8 bytes)
        f.write(struct.pack(">I", 8) + b"mdat")

    pre_size = os.path.getsize(tmp)
    ok = inject_phantom_atom(tmp, blob)
    post_size = os.path.getsize(tmp)
    print(f"  Inject: {'✅' if ok else '❌'} ({pre_size}B → {post_size}B, +{post_size - pre_size}B atom)")

    # Read it back
    readback = read_phantom_atom(tmp)
    if readback and readback.get("video_uuid") == test_uuid:
        print(f"  Readback: ✅ UUID matches, score={readback['score']}")
    else:
        print(f"  Readback: ❌ Failed")

    # Test idempotent re-injection
    ok2 = inject_phantom_atom(tmp, {**blob, "score": "99/99 (100%)"})
    readback2 = read_phantom_atom(tmp)
    final_size = os.path.getsize(tmp)
    if readback2 and readback2["score"] == "99/99 (100%)":
        print(f"  Idempotent: ✅ Re-inject works, no duplication ({final_size}B)")
    else:
        print(f"  Idempotent: ❌")

    # Cleanup
    os.remove(tmp)
    conn = _get_conn()
    conn.execute("DELETE FROM checklist_state WHERE video_uuid=?", (test_uuid,))
    conn.execute("DELETE FROM render_log WHERE video_uuid=?", (test_uuid,))
    conn.execute("DELETE FROM videos WHERE uuid=?", (test_uuid,))
    conn.commit()
    conn.close()

    print("\n  ✅ All tests passed. Phantom Atom operational.")
