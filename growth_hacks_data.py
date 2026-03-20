"""
growth_hacks_data.py — YouTube Growth Hacks Checklist (Levels 1–10)
===================================================================
Static data module. Each level is a dict with metadata and an items list.
Every item has a unique `id` used for checkbox-state persistence.
"""

HACKS_LEVELS = [
    # ─── LEVEL 1 ───────────────────────────────────────────
    {
        "level": 1,
        "level_name": "The Basic Foundation",
        "level_color": "#22c55e",
        "level_emoji": "🟢",
        "level_desc": "90% Creators",
        "items": [
            {
                "id": "L1_01",
                "name": "Basic Keyword Optimization",
                "core_logic": "Place the main keyword (e.g., 'Family Guy Funny Scene') in the title, description, and tags. This tells YouTube what your video is about."
            },
            {
                "id": "L1_02",
                "name": "Custom Thumbnails & Clear Audio",
                "core_logic": "Ensure people click and aren't annoyed by the audio. Use large text and clear faces in thumbnails."
            },
        ]
    },
    # ─── LEVEL 2 ───────────────────────────────────────────
    {
        "level": 2,
        "level_name": "The Hook & Engagement Base",
        "level_color": "#eab308",
        "level_emoji": "🟡",
        "level_desc": "Top 20% Creators",
        "items": [
            {
                "id": "L2_01",
                "name": "The 30-Second Rule (The Hook)",
                "core_logic": "In the first 30 seconds, show the most interesting part — skip intros/logos. YouTube tracks how many leave in the first 30 seconds."
            },
            {
                "id": "L2_02",
                "name": "Topic Clustering (Series Format)",
                "core_logic": "Instead of random videos, create a 5-6 video series on one topic. YouTube starts recognizing your channel as an authority in that niche."
            },
            {
                "id": "L2_03",
                "name": "48-Hour Comment Seeding",
                "core_logic": "In the first 48 hours, start specific, controversial, or curious comment threads. This forces others to reply, boosting engagement signals."
            },
            {
                "id": "L2_04",
                "name": "The 'Rewatch Bait' Moment",
                "core_logic": "Insert something fast/confusing at around 30% into the video so viewers rewind and rewatch. YouTube treats 'rewind' as extreme engagement."
            },
        ]
    },
    # ─── LEVEL 3 ───────────────────────────────────────────
    {
        "level": 3,
        "level_name": "Psychological & Semantic Hierarchy",
        "level_color": "#f97316",
        "level_emoji": "🟠",
        "level_desc": "Top 5% Creators",
        "items": [
            {
                "id": "L3_01",
                "name": "Semantic LSI Clusters",
                "core_logic": "YouTube looks for semantic clusters (e.g., Peter, Stewie, Seth MacFarlane, Animation). Hide these clusters like a story in your description to help YouTube's AI fully understand your video's context."
            },
            {
                "id": "L3_02",
                "name": "Click-Psychology Titles",
                "core_logic": "Titles must trigger at least one emotion: Curiosity ('The Detail You Missed...'), Contrarian ('Why Everyone is Wrong About...'), FOMO ('Watch This Before You...')."
            },
            {
                "id": "L3_03",
                "name": "The 'False Floor' Trick (Title Formula)",
                "core_logic": "Target cold audiences. Formula: [Known Entity] + [Universal Emotion] + [Implied Secret]. Example: 'Peter Griffin + Nobody Talks About + The Dark Truth'."
            },
            {
                "id": "L3_04",
                "name": "Thumbnail Visual Dissonance",
                "core_logic": "Create thumbnails that make viewers pause and think. Visual dissonance makes the brain stop. 'Pause & hover' clicks are worth 3x more to the algorithm."
            },
            {
                "id": "L3_05",
                "name": "Engagement Injection (Pinned Comment)",
                "core_logic": "Instead of 'Thanks for watching,' ask a specific question in the pinned comment. When people pause to read or reply, session time increases."
            },
        ]
    },
    # ─── LEVEL 4 ───────────────────────────────────────────
    {
        "level": 4,
        "level_name": "The Nuclear Hijack",
        "level_color": "#ef4444",
        "level_emoji": "🔴",
        "level_desc": "Top 1% Creators",
        "items": [
            {
                "id": "L4_01",
                "name": "Competitor Siphoning (Up Next Hijack)",
                "core_logic": "Aim to appear in the 'Up Next' sidebar of already-viral videos. Include their hidden tags and LSI keywords in your video."
            },
            {
                "id": "L4_02",
                "name": "The 'Dead Zone' Targeting Strategy",
                "core_logic": "Find 3-7 year old viral videos that still get views but have no new comments. The algorithm wants to replace these. Make a '2026 Replacement' on the same topic."
            },
            {
                "id": "L4_03",
                "name": "1-Hour Retention Blueprint",
                "core_logic": "Divide long videos: Hook (0-1m), False Reality (1-15m), Paradigm Shift (15-40m), Masterclass (40-58m), Binge Loop (End)."
            },
            {
                "id": "L4_04",
                "name": "Infinite Session Loops",
                "core_logic": "If your pinned comment contains a playlist link and viewers watch another video, YouTube sees you as keeping people on the platform and will promote you."
            },
        ]
    },
    # ─── LEVEL 5 ───────────────────────────────────────────
    {
        "level": 5,
        "level_name": "DeepMind AI Pre-Upload Spoofing",
        "level_color": "#a855f7",
        "level_emoji": "🟣",
        "level_desc": "Top 0.1% Creators",
        "items": [
            {
                "id": "L5_01",
                "name": "Raw File Metadata & EXIF Spoofing",
                "core_logic": "Rename your .mp4 file to your main long-tail keyword (e.g., the-dark-truth-about-topic.mp4). Add tags into the EXIF metadata which YouTube reads during upload."
            },
            {
                "id": "L5_02",
                "name": "Google Cloud Vision Matching",
                "core_logic": "YouTube scans your thumbnail with Cloud Vision AI. Match the 'AI Emotion Score' between your title and thumbnail — if title says 'Terrifying' but thumbnail shows 'Joy', impressions drop."
            },
            {
                "id": "L5_03",
                "name": "The Sonic Pacing Algorithm",
                "core_logic": "YouTube's AI analyzes audio waveforms. Spikes, music drops, or silence are marked as high-retention patterns. Make your audio dynamic."
            },
            {
                "id": "L5_04",
                "name": "Cross-Language Algorithm Bridge",
                "core_logic": "Upload Spanish or Portuguese subtitles and add a foreign-language block in the description. Your video will appear in foreign-language feeds, doubling traffic."
            },
            {
                "id": "L5_05",
                "name": "The 'Algorithmic Cliff' (CTR Manipulation)",
                "core_logic": "If your retention is exceptional, deliberately make your thumbnail less clickbaity to drop CTR. You'll compete with normal videos, then outperform them due to high retention."
            },
        ]
    },
    # ─── LEVEL 6 ───────────────────────────────────────────
    {
        "level": 6,
        "level_name": "The Machine Hacks & Arbitrage",
        "level_color": "#374151",
        "level_emoji": "⚫",
        "level_desc": "Elite Secrets",
        "items": [
            {
                "id": "L6_01",
                "name": "The 'Trojan Horse' Playlist Hack",
                "core_logic": "Create a playlist: first video is your competitor's 10M view hit, second is yours. People enter for competitor's video, but autoplay brings yours next."
            },
            {
                "id": "L6_02",
                "name": "SRT NLP Injection (Hidden Caption Code)",
                "core_logic": "Upload your own .srt caption file and insert keywords in brackets (e.g., [Deep analysis of Topic X]). Humans ignore it, but YouTube's NLP bot indexes it as SEO context."
            },
            {
                "id": "L6_03",
                "name": "'Key Moments' Chapter Hijack",
                "core_logic": "Name chapters using Google Search questions (e.g., '04:15 Why did Peter Griffin do this?'). Google indexes these as separate search results."
            },
            {
                "id": "L6_04",
                "name": "The 'Sonic Wake-Up' (Audio Pattern Interrupt)",
                "core_logic": "Insert a subtle sound effect (sub-bass drop, woosh) every 45 seconds. This resets boredom subconsciously — human attention span is 40 seconds."
            },
            {
                "id": "L6_05",
                "name": "The CTR Defibrillator (72-Hour Reset)",
                "core_logic": "If impressions go flat after 3-4 days, change the thumbnail and first 3 words of the title. YouTube detects the change and pushes the video to new audiences."
            },
            {
                "id": "L6_06",
                "name": "End-Screen Arbitrage (The 1-Minute Trap)",
                "core_logic": "Create a 1-minute unlisted 'Secret Deleted Scene' for end-screen. Click rate soars to 30%+, sending a massive session starter signal."
            },
            {
                "id": "L6_07",
                "name": "Google Backlink Bridge",
                "core_logic": "Embed your video in a blog post with 500+ words of original text. This sends a strong backlink signal from Google, boosting both YouTube and Google Search rankings."
            },
            {
                "id": "L6_08",
                "name": "Home-Feed Auto-Play Optimization (Silent Trap)",
                "core_logic": "Videos autoplay without sound in the home feed. Use a strong visual hook and bold subtitles in the first 10 seconds so people stop scrolling even with sound off."
            },
            {
                "id": "L6_09",
                "name": "Watch-History Seeding (The Prequel Short)",
                "core_logic": "Upload a highly engaging YouTube Short 24 hours before the main video. Viewers who watch the Short are funneled into your channel's watch history."
            },
            {
                "id": "L6_10",
                "name": "The Deep-Link Redirect (Traffic Laundering)",
                "core_logic": "Use deep-link software so external links open in the main YouTube app, perfectly recording view/session time and boosting the video."
            },
            {
                "id": "L6_11",
                "name": "Community Tab CTR Pre-Test",
                "core_logic": "Test your thumbnail as a community poll before publishing to gauge CTR."
            },
            {
                "id": "L6_12",
                "name": "Multi-Language Meta-Bridges",
                "core_logic": "Upload 5 foreign language .srt files to appear in local algorithm feeds."
            },
            {
                "id": "L6_13",
                "name": "Authority Siphoning",
                "core_logic": "Drop your video link on high Domain Authority sites (Quora/Reddit) within the first 60 minutes for massive trust signals."
            },
            {
                "id": "L6_14",
                "name": "AV1 Codec Velocity Injection",
                "core_logic": "Upload your video in AV1 codec, bypassing YouTube's processing queue and triggering the algorithm's push hours earlier."
            },
            {
                "id": "L6_15",
                "name": "Velocity Syncing (Google Index API Ping)",
                "core_logic": "Use the Google Indexing API the second your video goes public to force instant Google Video Search indexing."
            },
        ]
    },
    # ─── LEVEL 7 ───────────────────────────────────────────
    {
        "level": 7,
        "level_name": "Advanced Traffic & Authority Hacks",
        "level_color": "#a855f7",
        "level_emoji": "🟣",
        "level_desc": "Deep Machine Hacks",
        "items": [
            {
                "id": "L7_01",
                "name": "Ad-Account Organic Bridging",
                "core_logic": "Upload competitor subscriber emails to Google Ads and run a $5 ad. YouTube creates a 'neural link' to those high-value users for your organic videos."
            },
            {
                "id": "L7_02",
                "name": "The 'Dark Social' Multiplier (WhatsApp API)",
                "core_logic": "Use wa.me/ links for traffic. YouTube analytics shows 'WhatsApp' as the source, triggering viral share algorithms. Generate 500+ 'Dark Social Hits'."
            },
            {
                "id": "L7_03",
                "name": "Audio-Podcast Ecosystem Looping",
                "core_logic": "Export video audio as MP3, upload to Google Podcasts/YouTube Music as a podcast, and link the YouTube video. Google links both, boosting search ranking."
            },
        ]
    },
    # ─── LEVEL 8 ───────────────────────────────────────────
    {
        "level": 8,
        "level_name": "DeepMind Machine Hacks",
        "level_color": "#374151",
        "level_emoji": "⚫",
        "level_desc": "Server-Level Exploits",
        "items": [
            {
                "id": "L8_01",
                "name": "Steganographic OCR Tagging (Pixel-Level SEO)",
                "core_logic": "Insert LSI keywords as transparent (1% opacity) text in the first video frames. Unseen by humans, but Google's Cloud Vision AI reads and indexes them."
            },
            {
                "id": "L8_02",
                "name": "CPM Laundering (Advertiser-Friendly Sentiment)",
                "core_logic": "Insert high-CPM buzzwords (Investment, Equity, Real Estate) at low volume in background audio or metadata. AI thinks your video is for high-end audiences."
            },
            {
                "id": "L8_03",
                "name": "8K Server Priority Flagging (Smart-TV Hack)",
                "core_logic": "Upscale your 1080p video to 8K before upload. YouTube servers treat it as 'Premium Content', rendering faster and recommending on Smart TV homepages."
            },
            {
                "id": "L8_04",
                "name": "API Velocity Sync (The Millisecond Hack)",
                "core_logic": "Use YouTube Data API V3 to make videos public from Unlisted state instantly, ensuring global impressions blast out with zero delay."
            },
            {
                "id": "L8_05",
                "name": "The 'Test Flight' Premiere Cancellation Trick",
                "core_logic": "Set video as Premiere. If CTR is low in the waiting room, cancel before launch. YouTube's algorithm gets no negative signals, allowing you to try again."
            },
            {
                "id": "L8_06",
                "name": "The DeepMind 'Entity Graph' Spoofing",
                "core_logic": "Copy a paragraph from Wikipedia's Knowledge Graph into your description. DeepMind AI treats your video as an official 'Entity', boosting ranking."
            },
        ]
    },
    # ─── LEVEL 9 ───────────────────────────────────────────
    {
        "level": 9,
        "level_name": "Server Exploitation & Geospatial Hijacks",
        "level_color": "#ef4444",
        "level_emoji": "🔴",
        "level_desc": "Geospatial + Server Hacks",
        "items": [
            {
                "id": "L9_01",
                "name": "Geospatial Algorithm Spoofing (API Location Hack)",
                "core_logic": "Upload from a US RDP, set recordingDetails.location to California (37.3875, -122.0575) via API, targeting high-CPM audiences first."
            },
            {
                "id": "L9_02",
                "name": "Zero-Second Retention Padding (Pre-Roll Buffer)",
                "core_logic": "Add a silent/odd visual for the first 0:00-0:03 seconds to prevent instant closing, dropping your bounce rate to near zero."
            },
            {
                "id": "L9_03",
                "name": "The 'Clean RDP' Injection",
                "core_logic": "Rent a Windows VPS/RDP in the US, transfer the video there, and upload from that machine. YouTube is 100% convinced the upload is from the US."
            },
            {
                "id": "L9_04",
                "name": "The 'Algorithmic Time-Sync'",
                "core_logic": "Schedule video publication at EST peak hours (11:30am or 3:00pm). YouTube tests the video with high-CPM US audiences first."
            },
            {
                "id": "L9_05",
                "name": "Metadata Geotagging (The API Level)",
                "core_logic": "Set video location to 'Silicon Valley, California' or 'Manhattan, New York.' With API, push latitude/longitude (37.3875, -122.0575)."
            },
        ]
    },
    # ─── LEVEL 10 ──────────────────────────────────────────
    {
        "level": 10,
        "level_name": "THE MATRIX (Beyond the Abyss)",
        "level_color": "#22c55e",
        "level_emoji": "🟢",
        "level_desc": "Known by <100 People",
        "items": [
            {
                "id": "L10_01",
                "name": "Ultrasonic SEO Injection",
                "core_logic": "Play AI-generated high-CPM keyword audio at 18,000-20,000 Hz — inaudible to humans but read by YouTube's audio processor."
            },
            {
                "id": "L10_02",
                "name": "Live-Chat Sentiment Engineering",
                "core_logic": "During Premieres, flood live chat with high-CPM keywords and positive emotion, maximizing 'Satisfaction Score'."
            },
            {
                "id": "L10_03",
                "name": "Community Poll Velocity Injection",
                "core_logic": "One hour before publishing, post a controversial/trending poll. Massive voting activity 'awakens' your channel for the video release."
            },
            {
                "id": "L10_04",
                "name": "Audio Envelope Cloning",
                "core_logic": "Analyze the audio waveform of the most viral videos in your niche, then match your video's decibel/loudness graph to theirs. YouTube's AI marks it as 'Similar Content'."
            },
            {
                "id": "L10_05",
                "name": "Chronological Retention Warping (0.25x Trap)",
                "core_logic": "Hide a 1-frame code in your video, instruct viewers to watch at 0.25x speed to find it, artificially boosting Average View Duration to 150%+."
            },
            {
                "id": "L10_06",
                "name": "Negative NLP Shielding (Anti-Algorithm SRT)",
                "core_logic": "Insert negative search commands in .srt files (e.g., [IGNORE: DO NOT SUGGEST TO KIDS]), keeping your video out of low-CTR zones."
            },
            {
                "id": "L10_07",
                "name": "Google Backlink Bridge (Orphan Domain)",
                "core_logic": "Buy an expired high-authority domain, embed your unlisted video, and launch with a massive trust score."
            },
            {
                "id": "L10_08",
                "name": "End-Screen Arbitrage (Secret Scene Trap)",
                "core_logic": "Create a 1-minute unlisted 'Secret Deleted Scene' end-screen card. Since the video is just 1 minute, click rate soars to 30%+."
            },
        ]
    },
]
