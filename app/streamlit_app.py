from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests
import streamlit as st

# ── Default API URL: Streamlit secrets → env var → localhost ──
def _default_api_url() -> str:
    try:
        url = st.secrets.get("API_URL", "")
        if url:
            return url.rstrip("/")
    except Exception:
        pass
    import os
    return os.environ.get("API_URL", "http://127.0.0.1:8000")


# ============================================================
# Page setup
# ============================================================
st.set_page_config(
    page_title="Job Match Intelligence System",
    page_icon="💼",
    layout="wide",
)


# ============================================================
# Helpers
# ============================================================
def split_csv(text: str) -> List[str]:
    if not text or not text.strip():
        return []
    return [item.strip() for item in text.split(",") if item.strip()]


def join_list(values: Optional[List[str]]) -> str:
    if not values:
        return ""
    return ", ".join(values)



# ============================================================
# Google Analytics 4 + UTM tracking
# ============================================================
def inject_analytics() -> None:
    GA_ID = "G-NL5BPY86QT"
    # Read UTM params from URL if present
    try:
        params = st.query_params
        utm_source   = params.get("utm_source", "")
        utm_campaign = params.get("utm_campaign", "")
        utm_medium   = params.get("utm_medium", "")
    except Exception:
        utm_source = utm_campaign = utm_medium = ""

    ga_script = f"""
<!-- Google Analytics 4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{GA_ID}', {{
    'utm_source':   '{utm_source}',
    'utm_medium':   '{utm_medium}',
    'utm_campaign': '{utm_campaign}'
  }});
</script>
"""
    st.markdown(ga_script, unsafe_allow_html=True)

def init_state() -> None:
    defaults = {
        "api_url": _default_api_url(),
        "token": "",
        "user_email": "",
        "full_name": "",
        "is_logged_in": False,
        "profiles_loaded": False,
        "preferences_loaded": False,
        "all_profiles": [],          # list of ProfileListItem dicts
        "active_profile_id": None,   # candidate_id of selected profile
        "saved_profile": {},         # full profile data for active profile
        "saved_preferences": {},
        "jobs": [],
        "jobs_dataset_path": "",
        "last_match_result": None,
        "last_recommendations": None,
        "last_live_recommendations": None,
        "resume_extracted": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value



# ============================================================
# Custom CSS — Dark professional theme
# ============================================================
def inject_css() -> None:
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ══════════════════════════════════════════════
   BASE — dark canvas, colorful everything inside
   ══════════════════════════════════════════════ */
* { font-family: 'Inter', sans-serif !important; }

.stApp { background-color: #0a0e1a !important; color: #dde3f0; }
section[data-testid="stMain"] > div { background-color: #0a0e1a !important; }

/* ── Hide sidebar toggle icon TEXT but keep button clickable ── */
/* Target the span/text inside any sidebar toggle button */
[data-testid="stSidebarCollapsedControl"] span,
[data-testid="stSidebarCollapsedControl"] p,
[data-testid="collapsedControl"] span,
[data-testid="collapsedControl"] p,
button[data-testid="baseButton-header"] span,
button[kind="header"] span {
    font-size: 0 !important;
    color: transparent !important;
    visibility: hidden !important;
}

/* Replace with a proper hamburger icon via pseudo-element */
[data-testid="stSidebarCollapsedControl"] button::before,
[data-testid="collapsedControl"] button::before {
    content: "☰" !important;
    font-size: 20px !important;
    color: #a78bfa !important;
    visibility: visible !important;
}

/* Hide the duplicate arrow buttons */
button[aria-label="Close sidebar"] span,
button[aria-label="Open sidebar"] span {
    font-size: 0 !important;
    visibility: hidden !important;
}

/* Mobile layout fix */
@media (max-width: 768px) {
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-top: 1rem !important;
        max-width: 100% !important;
    }
    h1 { font-size: 1.4rem !important; }
    h2 { font-size: 1.1rem !important; }
    .stTabs [data-baseweb="tab"] {
        font-size: 0.75rem !important;
        padding: 6px 10px !important;
    }
    .jm-card { padding: 14px 12px !important; }
    .score-ring { width: 60px !important; height: 60px !important; font-size: 15px !important; }
    .apply-btn { display: block !important; text-align: center !important; width: 100% !important; }
    .stButton > button { width: 100% !important; }
    .jm-card:hover { transform: none !important; }
}

/* ── Hide "Press Enter to submit form" tooltip ── */
.stTextInput div[data-baseweb="input"] + div { display: none !important; }
small.st-emotion-cache-16idsys { display: none !important; }
.stTextInput [class*="instructions"] { display: none !important; }
.stTextArea [class*="instructions"] { display: none !important; }
/* Universal: hide any helper text that says "Press Enter" */
div[class*="InputInstructions"] { display: none !important; }
p[class*="instructions"] { display: none !important; }
[data-testid="InputInstructions"] { display: none !important; }
small[id*="instructions"] { display: none !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f1322 0%, #111827 100%) !important;
    border-right: 1px solid rgba(99,102,241,0.25) !important;
}
[data-testid="stSidebar"] * { color: #cbd5e1 !important; }

/* ── Header bar ── */
header[data-testid="stHeader"] {
    background-color: #0a0e1a !important;
    border-bottom: 1px solid rgba(99,102,241,0.2);
}

/* ── App title ── */
h1 {
    background: linear-gradient(135deg, #a78bfa, #60a5fa, #34d399) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    font-weight: 800 !important;
    font-size: 2rem !important;
}
h2 { color: #e2e8f0 !important; font-weight: 700 !important; }
h3 { color: #cbd5e1 !important; font-weight: 600 !important; }
p, li, label { color: #94a3b8; }
.stCaption, small { color: #64748b !important; }
hr { border: none !important; border-top: 1px solid rgba(99,102,241,0.2) !important; }

/* ══════════════════════════════════════
   TABS — pill style, gradient active
   ══════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(15,19,35,0.8);
    border-radius: 14px;
    padding: 5px 7px;
    gap: 4px;
    border: 1px solid rgba(99,102,241,0.2);
    backdrop-filter: blur(8px);
}
.stTabs [data-baseweb="tab"] {
    background-color: transparent !important;
    color: #64748b !important;
    border-radius: 10px;
    font-weight: 600;
    font-size: 0.85rem;
    padding: 8px 22px;
    transition: all 0.2s;
    letter-spacing: 0.2px;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #a78bfa !important;
    background: rgba(167,139,250,0.08) !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: #ffffff !important;
    box-shadow: 0 4px 14px rgba(99,102,241,0.45);
}

/* ══════════════════════════════════════
   BUTTONS
   ══════════════════════════════════════ */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    letter-spacing: 0.3px;
    padding: 10px 24px !important;
    transition: all 0.2s ease;
    box-shadow: 0 2px 10px rgba(99,102,241,0.3);
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
    box-shadow: 0 6px 20px rgba(99,102,241,0.5);
    transform: translateY(-2px);
}
.stButton > button:not([kind="primary"]) {
    background: rgba(15,19,35,0.9) !important;
    color: #94a3b8 !important;
    border: 1px solid rgba(99,102,241,0.25) !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.2s;
}
.stButton > button:not([kind="primary"]):hover {
    border-color: #a78bfa !important;
    color: #a78bfa !important;
    background: rgba(167,139,250,0.08) !important;
    transform: translateY(-1px);
}
.stLinkButton a {
    background: linear-gradient(135deg, #059669, #10b981) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    padding: 10px 22px !important;
    box-shadow: 0 2px 10px rgba(16,185,129,0.3);
}

/* ══════════════════════════════════════
   INPUTS
   ══════════════════════════════════════ */
.stTextInput input, .stTextArea textarea, .stNumberInput input {
    background: rgba(15,19,35,0.9) !important;
    border: 1px solid rgba(99,102,241,0.25) !important;
    color: #e2e8f0 !important;
    border-radius: 10px !important;
    transition: all 0.2s;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #8b5cf6 !important;
    box-shadow: 0 0 0 3px rgba(139,92,246,0.2) !important;
}
.stSelectbox > div > div {
    background: rgba(15,19,35,0.9) !important;
    border: 1px solid rgba(99,102,241,0.25) !important;
    color: #e2e8f0 !important;
    border-radius: 10px !important;
}

/* ══════════════════════════════════════
   METRICS — colourful gradient cards
   ══════════════════════════════════════ */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, rgba(99,102,241,0.12), rgba(139,92,246,0.06)) !important;
    border: 1px solid rgba(99,102,241,0.3) !important;
    border-radius: 14px !important;
    padding: 18px 20px !important;
    position: relative;
    overflow: hidden;
}
[data-testid="metric-container"]::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #6366f1, #8b5cf6, #a78bfa);
    border-radius: 14px 14px 0 0;
}
[data-testid="metric-container"] label { color: #64748b !important; font-size: 11px !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.6px; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #e2e8f0 !important; font-size: 24px !important; font-weight: 800 !important; }

/* ══════════════════════════════════════
   PROGRESS BAR — rainbow gradient
   ══════════════════════════════════════ */
.stProgress > div > div { background: rgba(15,19,35,0.8); border-radius: 8px; height: 8px !important; }
.stProgress > div > div > div {
    background: linear-gradient(90deg, #6366f1, #8b5cf6, #ec4899, #f97316, #eab308, #22c55e);
    border-radius: 8px;
    transition: width 0.5s ease;
}

/* ══════════════════════════════════════
   CONTAINERS
   ══════════════════════════════════════ */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(15,19,35,0.7) !important;
    border: 1px solid rgba(99,102,241,0.2) !important;
    border-radius: 14px !important;
    backdrop-filter: blur(6px);
}
.streamlit-expanderHeader {
    background: rgba(15,19,35,0.8) !important;
    border: 1px solid rgba(99,102,241,0.2) !important;
    border-radius: 10px !important;
    color: #94a3b8 !important;
    font-weight: 600 !important;
}
.streamlit-expanderContent {
    background: rgba(10,14,26,0.9) !important;
    border: 1px solid rgba(99,102,241,0.15) !important;
    border-top: none !important;
}

/* ══════════════════════════════════════
   ALERTS
   ══════════════════════════════════════ */
.stSuccess {
    background: linear-gradient(135deg, rgba(16,185,129,0.12), rgba(5,150,105,0.06)) !important;
    border: 1px solid rgba(16,185,129,0.4) !important;
    border-left: 4px solid #10b981 !important;
    color: #6ee7b7 !important;
    border-radius: 10px !important;
}
.stWarning {
    background: linear-gradient(135deg, rgba(245,158,11,0.12), rgba(217,119,6,0.06)) !important;
    border: 1px solid rgba(245,158,11,0.4) !important;
    border-left: 4px solid #f59e0b !important;
    color: #fcd34d !important;
    border-radius: 10px !important;
}
.stError {
    background: linear-gradient(135deg, rgba(239,68,68,0.12), rgba(220,38,38,0.06)) !important;
    border: 1px solid rgba(239,68,68,0.4) !important;
    border-left: 4px solid #ef4444 !important;
    color: #fca5a5 !important;
    border-radius: 10px !important;
}
.stInfo {
    background: linear-gradient(135deg, rgba(99,102,241,0.12), rgba(59,130,246,0.06)) !important;
    border: 1px solid rgba(99,102,241,0.4) !important;
    border-left: 4px solid #6366f1 !important;
    color: #a5b4fc !important;
    border-radius: 10px !important;
}

/* ══════════════════════════════════════
   FILE UPLOADER
   ══════════════════════════════════════ */
[data-testid="stFileUploader"] {
    background: rgba(99,102,241,0.04) !important;
    border: 2px dashed rgba(99,102,241,0.35) !important;
    border-radius: 14px !important;
    transition: all 0.2s;
}
[data-testid="stFileUploader"]:hover {
    border-color: rgba(139,92,246,0.6) !important;
    background: rgba(99,102,241,0.08) !important;
}

/* ══════════════════════════════════════
   SLIDER
   ══════════════════════════════════════ */
.stSlider [data-baseweb="slider"] div[role="slider"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    border: 2px solid #a78bfa !important;
    box-shadow: 0 0 10px rgba(99,102,241,0.5) !important;
}

/* ══════════════════════════════════════════════════
   JOB CARDS — the star of the show
   ══════════════════════════════════════════════════ */
.jm-card {
    background: linear-gradient(145deg, #0f1729 0%, #131d2e 60%, #0f1322 100%);
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 18px;
    padding: 24px 26px;
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
}
/* Subtle top accent stripe — changes colour per card via nth-child */
.jm-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #6366f1, #8b5cf6, #ec4899);
    border-radius: 18px 18px 0 0;
}
.jm-card:hover {
    transform: translateY(-3px);
    border-color: rgba(139,92,246,0.5);
    box-shadow: 0 8px 32px rgba(99,102,241,0.2), 0 2px 8px rgba(0,0,0,0.4);
}

/* ── Score ring ── */
.score-ring {
    width: 84px; height: 84px;
    border-radius: 50%;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    border: 4px solid;
    font-weight: 800; font-size: 21px;
    flex-shrink: 0;
    position: relative;
}
.score-ring::after {
    content: '';
    position: absolute; inset: -6px;
    border-radius: 50%;
    border: 2px solid transparent;
    background: inherit;
    background-clip: border-box;
    opacity: 0.2;
    filter: blur(4px);
}

/* ── Skill chips ── */
.chip-green {
    display: inline-block;
    background: linear-gradient(135deg, rgba(16,185,129,0.18), rgba(5,150,105,0.1));
    color: #6ee7b7;
    border: 1px solid rgba(16,185,129,0.4);
    font-size: 0.72rem; font-weight: 700;
    padding: 3px 10px; border-radius: 20px;
    letter-spacing: 0.2px;
}
.chip-red {
    display: inline-block;
    background: linear-gradient(135deg, rgba(239,68,68,0.18), rgba(220,38,38,0.1));
    color: #fca5a5;
    border: 1px solid rgba(239,68,68,0.4);
    font-size: 0.72rem; font-weight: 700;
    padding: 3px 10px; border-radius: 20px;
    letter-spacing: 0.2px;
}

/* ── Hard filter banners ── */
.hf-pass {
    display: inline-flex; align-items: center; gap: 6px;
    background: linear-gradient(135deg, rgba(16,185,129,0.15), rgba(5,150,105,0.08));
    border: 1px solid rgba(16,185,129,0.4);
    border-radius: 8px; padding: 6px 14px;
    font-size: 0.8rem; font-weight: 700; color: #6ee7b7;
    margin: 8px 0;
}
.hf-fail {
    display: inline-flex; align-items: center; gap: 6px;
    background: linear-gradient(135deg, rgba(245,158,11,0.15), rgba(217,119,6,0.08));
    border: 1px solid rgba(245,158,11,0.4);
    border-radius: 8px; padding: 6px 14px;
    font-size: 0.8rem; font-weight: 700; color: #fcd34d;
    margin: 8px 0;
}

/* ── Apply button ── */
.apply-btn {
    display: inline-block;
    background: linear-gradient(135deg, #059669, #10b981);
    color: #ffffff !important;
    text-decoration: none !important;
    font-weight: 700;
    font-size: 0.88rem;
    padding: 10px 26px;
    border-radius: 10px;
    transition: all 0.2s;
    letter-spacing: 0.3px;
    box-shadow: 0 2px 12px rgba(16,185,129,0.35);
}
.apply-btn:hover {
    background: linear-gradient(135deg, #047857, #059669) !important;
    box-shadow: 0 6px 20px rgba(16,185,129,0.5);
    transform: translateY(-2px);
    color: #ffffff !important;
}

/* ── Divider inside cards ── */
.card-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(99,102,241,0.25), transparent);
    margin: 14px 0;
}

/* ── Checkbox ── */
.stCheckbox > label { color: #94a3b8 !important; }

/* ══════════════════════════════════════
   MOBILE RESPONSIVE
   ══════════════════════════════════════ */
@media (max-width: 768px) {
    /* Main content padding */
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-top: 1rem !important;
        max-width: 100% !important;
    }

    /* Smaller title */
    h1 { font-size: 1.4rem !important; }
    h2 { font-size: 1.1rem !important; }
    h3 { font-size: 1rem !important; }

    /* Tabs — smaller text, wrap */
    .stTabs [data-baseweb="tab-list"] {
        flex-wrap: wrap !important;
        gap: 4px !important;
        padding: 4px !important;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 0.75rem !important;
        padding: 6px 12px !important;
    }

    /* Job cards — tighter padding */
    .jm-card {
        padding: 16px 14px !important;
        border-radius: 14px !important;
    }

    /* Score ring — smaller */
    .score-ring {
        width: 64px !important;
        height: 64px !important;
        font-size: 16px !important;
    }

    /* Skill chips — smaller */
    .chip-green, .chip-red {
        font-size: 0.65rem !important;
        padding: 2px 8px !important;
    }

    /* Apply button — full width */
    .apply-btn {
        display: block !important;
        text-align: center !important;
        width: 100% !important;
        padding: 12px !important;
        margin-top: 10px !important;
    }

    /* Buttons — full width */
    .stButton > button {
        width: 100% !important;
    }

    /* Sidebar — auto open on mobile */
    [data-testid="stSidebar"] {
        min-width: 100% !important;
        max-width: 100% !important;
    }

    /* Metrics — single column */
    [data-testid="metric-container"] {
        padding: 12px 14px !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 18px !important;
    }

    /* Hide hover effects on touch */
    .jm-card:hover { transform: none !important; }
    .stButton > button:hover { transform: none !important; }
    .apply-btn:hover { transform: none !important; }
}
</style>
""", unsafe_allow_html=True)

def get_headers() -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}

    if st.session_state.get("token"):
        headers["Authorization"] = f"Bearer {st.session_state.token}"

    return headers


def api_get(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = f"{st.session_state.api_url.rstrip('/')}/{endpoint.lstrip('/')}"
    response = requests.get(url, headers=get_headers(), params=params, timeout=60)
    response.raise_for_status()
    return response.json()


def api_post(endpoint: str, payload: Dict[str, Any], method: str = "POST") -> Dict[str, Any]:
    url = f"{st.session_state.api_url.rstrip('/')}/{endpoint.lstrip('/')}"
    fn = requests.put if method == "PUT" else requests.post
    response = fn(url, headers=get_headers(), json=payload, timeout=90)
    response.raise_for_status()
    return response.json()


def show_api_error(error: Exception) -> None:
    if isinstance(error, requests.exceptions.HTTPError):
        try:
            detail = error.response.json().get("detail", str(error))
            st.error(detail)
        except Exception:
            st.error(str(error))
    else:
        st.error(str(error))


def logout() -> None:
    st.session_state.token = ""
    st.session_state.user_email = ""
    st.session_state.full_name = ""
    st.session_state.is_logged_in = False
    st.session_state.profiles_loaded = False
    st.session_state.preferences_loaded = False
    st.session_state.all_profiles = []
    st.session_state.active_profile_id = None
    st.session_state.saved_profile = {}
    st.session_state.saved_preferences = {}
    st.session_state.last_match_result = None
    st.session_state.last_recommendations = None
    st.session_state.last_live_recommendations = None
    st.rerun()


def load_profiles_silently() -> None:
    """Load all profiles for the current user on first login."""
    if not st.session_state.is_logged_in or st.session_state.profiles_loaded:
        return

    try:
        result = api_get("/profiles")
        st.session_state.all_profiles = result.get("profiles", [])
        # Auto-select first profile if available
        if st.session_state.all_profiles and not st.session_state.active_profile_id:
            first_id = st.session_state.all_profiles[0]["candidate_id"]
            st.session_state.active_profile_id = first_id
            try:
                profile = api_get(f"/profiles/{first_id}")
                st.session_state.saved_profile = profile
            except Exception:
                st.session_state.saved_profile = {}
    except Exception:
        st.session_state.all_profiles = []

    st.session_state.profiles_loaded = True


def load_preferences_silently() -> None:
    if not st.session_state.is_logged_in or st.session_state.preferences_loaded:
        return

    try:
        preferences = api_get("/preferences")
        st.session_state.saved_preferences = preferences
    except Exception:
        st.session_state.saved_preferences = {}

    st.session_state.preferences_loaded = True


def profile_value(key: str, default: Any = "") -> Any:
    return st.session_state.saved_profile.get(key, default)


def preference_value(key: str, default: Any = "") -> Any:
    return st.session_state.saved_preferences.get(key, default)


def build_candidate_payload() -> Dict[str, Any]:
    return {
        "candidate_id": st.session_state.get("active_profile_id") or "candidate_001",
        "full_name": st.session_state.get("candidate_full_name", ""),
        "current_title": st.session_state.get("candidate_current_title", ""),
        "location": st.session_state.get("candidate_location", ""),
        "education": st.session_state.get("candidate_education") or None,
        "years_experience": int(st.session_state.get("candidate_years_experience", 0)),
        "skills": split_csv(st.session_state.get("candidate_skills", "")),
        "tools": split_csv(st.session_state.get("candidate_tools", "")),
        "domains": split_csv(st.session_state.get("candidate_domains", "")),
        "certifications": split_csv(st.session_state.get("candidate_certifications", "")),
        "projects": split_csv(st.session_state.get("candidate_projects", "")),
        "seniority": st.session_state.get("candidate_seniority") or None,
        "summary": st.session_state.get("candidate_summary") or None,
    }


def build_job_payload() -> Dict[str, Any]:
    years_required = st.session_state.get("job_years_required")

    return {
        "job_id": st.session_state.get("job_id", "job_001"),
        "title": st.session_state.get("job_title", ""),
        "company": st.session_state.get("job_company", ""),
        "location": st.session_state.get("job_location", ""),
        "workplace_type": st.session_state.get("job_workplace_type", ""),
        "domains": split_csv(st.session_state.get("job_domains", "")),
        "required_skills": split_csv(st.session_state.get("job_required_skills", "")),
        "preferred_skills": split_csv(st.session_state.get("job_preferred_skills", "")),
        "other_skills": split_csv(st.session_state.get("job_other_skills", "")),
        "years_experience_required": int(years_required) if years_required is not None else None,
        "education_required": st.session_state.get("job_education_required") or None,
        "seniority": st.session_state.get("job_seniority") or None,
    }


def build_preferences_payload() -> Dict[str, Any]:
    return {
        "preferred_titles": split_csv(st.session_state.get("preferred_titles", "")),
        "preferred_locations": split_csv(st.session_state.get("preferred_locations", "")),
        "preferred_workplace_types": split_csv(st.session_state.get("preferred_workplace_types", "")),
        "preferred_domains": split_csv(st.session_state.get("preferred_domains", "")),
        "preferred_seniority": st.session_state.get("preferred_seniority") or None,
        "min_score": int(st.session_state.get("min_score", 50)),
    }


def display_match_result(result: Dict[str, Any]) -> None:
    match_score = result.get("match_score", {})
    hard_filters = result.get("hard_filters", {})
    explanation = result.get("explanation", {})

    score = match_score.get("score", 0)
    fit_label = match_score.get("fit_label", "Unknown")

    col1, col2, col3 = st.columns(3)
    col1.metric("Match Score", f"{score}%")
    col2.metric("Fit Label", fit_label)
    col3.metric("Hard Filters", "Passed" if hard_filters.get("passed") else "Not Passed")

    st.subheader("Skill Match")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Matched Required Skills**")
        matched = explanation.get("matched_required_skills", [])
        if matched:
            st.success(", ".join(matched))
        else:
            st.info("No matched required skills found.")

    with c2:
        st.markdown("**Missing Required Skills**")
        missing = explanation.get("missing_required_skills", [])
        if missing:
            st.warning(", ".join(missing))
        else:
            st.success("No missing required skills.")

    st.subheader("Recommendations")
    recommendations = explanation.get("recommendations", [])
    if recommendations:
        for item in recommendations:
            st.write(f"- {item}")
    else:
        st.info("No recommendations returned by the backend.")

    st.subheader("Component Scores")
    st.json(match_score.get("component_scores", {}))

    with st.expander("Full API Response"):
        st.json(result)


def display_recommendations(result: Dict[str, Any]) -> None:
    recommendations = result.get("recommendations", [])

    if not recommendations:
        st.warning("No recommendations found.")
        return

    st.success(f"Found {len(recommendations)} recommended jobs.")

    for index, item in enumerate(recommendations, start=1):
        score = item.get("score", 0)
        fit = item.get("fit_label", "Unknown")
        passed = item.get("hard_filters_passed", False)
        matched = item.get("matched_required_skills", [])
        missing = item.get("missing_required_skills", [])
        source_url = item.get("source_url", "")
        if score >= 75:
            ring_color = "#10b981"; ring_glow = "rgba(16,185,129,0.3)"
        elif score >= 50:
            ring_color = "#f59e0b"; ring_glow = "rgba(245,158,11,0.3)"
        else:
            ring_color = "#ef4444"; ring_glow = "rgba(239,68,68,0.3)"
        hf_html = '<span class="hf-pass">✅ Meets requirements</span>' if passed else '<span class="hf-fail">⚠️ Partial match</span>'
        matched_chips = " ".join(f'<span class="chip-green">{s}</span>' for s in matched) if matched else "<em style='color:#475569'>None</em>"
        missing_chips = " ".join(f'<span class="chip-red">{s}</span>' for s in missing) if missing else '<span style="color:#10b981;font-size:0.85rem;font-weight:600;">🎉 None — perfect fit!</span>'
        apply_btn = f'<a href="{source_url}" target="_blank" class="apply-btn">🚀 Apply Now</a>' if source_url else ""
        meta_str = "  ·  ".join(p for p in [item.get("company",""), item.get("location",""), item.get("workplace_type","")] if p)
        card_html = (
            '<div class="jm-card">'
            '<div style="display:flex;align-items:flex-start;justify-content:space-between;gap:16px;">'
            '<div style="flex:1;min-width:0;">'
            f'<div style="font-size:1.1rem;font-weight:800;color:#e2e8f0;margin-bottom:5px;line-height:1.3;">'
            f'<span style="color:#6366f1;font-size:0.85rem;font-weight:700;margin-right:8px;">#{index}</span>'
            f'{item.get("title","Untitled Job")}</div>'
            f'<div style="font-size:0.83rem;color:#64748b;margin-bottom:10px;">{meta_str}</div>'
            f'{hf_html}'
            '</div>'
            f'<div class="score-ring" style="border-color:{ring_color};color:{ring_color};background:rgba(0,0,0,0.3);box-shadow:0 0 18px {ring_glow};flex-shrink:0;">'
            f'{score}%<br><span style="font-size:0.58rem;font-weight:600;color:#64748b;text-transform:uppercase;">{fit}</span>'
            '</div></div>'
            '<div class="card-divider"></div>'
            '<div style="display:flex;gap:20px;flex-wrap:wrap;">'
            '<div style="flex:1;min-width:180px;">'
            '<div style="font-size:0.72rem;font-weight:700;color:#10b981;text-transform:uppercase;letter-spacing:.07em;margin-bottom:7px;">✔ Matched Skills</div>'
            f'<div style="line-height:2;">{matched_chips}</div></div>'
            '<div style="flex:1;min-width:180px;">'
            '<div style="font-size:0.72rem;font-weight:700;color:#ef4444;text-transform:uppercase;letter-spacing:.07em;margin-bottom:7px;">✘ Missing Skills</div>'
            f'<div style="line-height:2;">{missing_chips}</div></div>'
            '</div>'
            + ('<div class="card-divider"></div><div>' + apply_btn + '</div>' if apply_btn else "")
            + '</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)

        recs = item.get("recommendations", [])
        if recs:
            with st.expander("💡 How to improve your match"):
                for rec in recs:
                    st.write(f"• {rec}")


# ============================================================
# App start
# ============================================================
init_state()
inject_css()
inject_analytics()

st.title("💼 Job Match Intelligence System")
st.caption("Candidate profile, job matching, and dataset-based recommendations.")


# ============================================================
# Sidebar
# ============================================================
with st.sidebar:
    st.header("Settings")

    st.divider()

    if not st.session_state.is_logged_in:
        auth_tab = st.radio(
            "Account",
            ["Login", "Register", "Forgot Password"],
            key="auth_tab_selection",
        )

        # ── Login ──────────────────────────────────────────
        if auth_tab == "Login":
            with st.form("login_form"):
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_password")
                submitted = st.form_submit_button("Login", use_container_width=True)

            if submitted:
                try:
                    result = api_post(
                        "/auth/login",
                        {"email": email, "password": password},
                    )
                    st.session_state.token = result["access_token"]
                    st.session_state.user_email = result["user_email"]
                    st.session_state.full_name = result.get("full_name", "")
                    st.session_state.is_logged_in = True
                    st.session_state.profile_loaded = False
                    st.session_state.preferences_loaded = False
                    st.success("Logged in successfully.")
                    st.rerun()
                except Exception as e:
                    show_api_error(e)

        # ── Register ────────────────────────────────────────
        elif auth_tab == "Register":
            with st.form("register_form"):
                full_name = st.text_input("Full Name", key="register_full_name")
                email = st.text_input("Email", key="register_email")
                password = st.text_input("Password", type="password", key="register_password")
                submitted = st.form_submit_button("Register", use_container_width=True)

            if submitted:
                try:
                    result = api_post(
                        "/auth/register",
                        {
                            "full_name": full_name,
                            "email": email,
                            "password": password,
                        },
                    )
                    st.session_state.token = result["access_token"]
                    st.session_state.user_email = result["user_email"]
                    st.session_state.full_name = result.get("full_name", "")
                    st.session_state.is_logged_in = True
                    st.session_state.profile_loaded = False
                    st.session_state.preferences_loaded = False
                    st.success("Account created successfully.")
                    st.rerun()
                except Exception as e:
                    show_api_error(e)

        # ── Forgot Password ─────────────────────────────────
        else:
            st.subheader("Reset Your Password")
            st.write("Enter your email to receive a reset link, or paste a reset token you already received.")

            # Step 1 — request reset email
            with st.form("forgot_password_form"):
                forgot_email = st.text_input("Registered Email", key="forgot_email")
                send_submitted = st.form_submit_button("Send Reset Link", use_container_width=True)

            if send_submitted:
                if not forgot_email.strip():
                    st.warning("Please enter your email address.")
                else:
                    try:
                        result = api_post(
                            "/auth/forgot-password",
                            {"email": forgot_email.strip()},
                        )
                        dev_token = result.get("dev_token", "")
                        if dev_token:
                            # Email not configured — show the token directly
                            st.warning(result.get("message", ""))
                            st.info(
                                "**Your reset token (copy this):**\n\n"
                                f"`{dev_token}`\n\n"
                                "Paste it into the form below to set your new password."
                            )
                            # Pre-fill the token field
                            st.session_state["prefill_reset_token"] = dev_token
                        else:
                            st.success(result.get("message", "Reset link sent — check your inbox."))
                    except Exception as e:
                        show_api_error(e)

            st.divider()

            # Step 2 — enter token + new password
            st.write("**Already have a reset token?** Paste it below and choose a new password.")

            # Pre-fill from URL query param (?reset_token=...) or from the
            # dev_token returned when email isn't configured
            url_token = (
                st.query_params.get("reset_token", "")
                or st.session_state.get("prefill_reset_token", "")
            )

            with st.form("reset_password_form"):
                reset_token = st.text_input(
                    "Reset Token (from your email)",
                    value=url_token,
                    key="reset_token_input",
                )
                new_pass = st.text_input("New Password", type="password", key="reset_new_password")
                confirm_pass = st.text_input("Confirm New Password", type="password", key="reset_confirm_password")
                reset_submitted = st.form_submit_button("Reset Password", use_container_width=True)

            if reset_submitted:
                if not reset_token.strip():
                    st.warning("Please paste your reset token.")
                elif len(new_pass) < 8:
                    st.warning("Password must be at least 8 characters.")
                elif new_pass != confirm_pass:
                    st.warning("Passwords do not match.")
                else:
                    try:
                        result = api_post(
                            "/auth/reset-password",
                            {"token": reset_token.strip(), "new_password": new_pass},
                        )
                        st.success(result.get("message", "Password reset successfully. You can now log in."))
                        # Clear the token from URL
                        st.query_params.clear()
                    except Exception as e:
                        show_api_error(e)

    else:
        st.success("Logged in")
        st.write(st.session_state.full_name)
        st.caption(st.session_state.user_email)

        if st.button("Logout", use_container_width=True):
            logout()


if st.session_state.is_logged_in:
    load_profiles_silently()
    load_preferences_silently()


# ============================================================
# Main app
# ============================================================
if not st.session_state.is_logged_in:
    # Auto-open sidebar on mobile via JS
    st.markdown("""
<script>
(function() {
    function openSidebar() {
        if (window.innerWidth <= 768) {
            var btn = document.querySelector('[data-testid="stSidebarCollapsedControl"] button');
            if (btn) { btn.click(); }
            else { setTimeout(openSidebar, 500); }
        }
    }
    setTimeout(openSidebar, 800);
})();
</script>
""", unsafe_allow_html=True)
    st.markdown("""
<div style="text-align:center; padding: 40px 20px;">
    <div style="font-size: 3rem; margin-bottom: 16px;">💼</div>
    <h2 style="color: #a78bfa; margin-bottom: 12px;">Welcome to Job Match Intelligence System</h2>
    <p style="color: #94a3b8; font-size: 1rem; margin-bottom: 24px;">Find jobs that match your skills — powered by AI</p>
    <div style="background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.3); border-radius: 14px; padding: 20px; display: inline-block;">
        <p style="color: #cbd5e1; margin: 0; font-size: 1rem;">
            📱 <strong>On mobile:</strong> Tap the <strong>☰ menu</strong> at the top left to login or register<br><br>
            🖥️ <strong>On desktop:</strong> Use the sidebar on the left
        </p>
    </div>
</div>
""", unsafe_allow_html=True)
    st.stop()


page = st.tabs(
    [
        "👤 My Profile",
        "🎯 My Job Matches",
        "⚙️ Preferences",
    ]
)


# ============================================================
# Candidate Profile
# ============================================================
with page[0]:
    st.header("Candidate Profile")

    # ── Profile selector bar ──────────────────────────────
    profiles = st.session_state.all_profiles
    active_id = st.session_state.active_profile_id

    sel_col, new_col, del_col = st.columns([4, 1, 1])

    with sel_col:
        if profiles:
            profile_labels = [
                f"{p['profile_name']}  ({p['current_title'] or 'No title'})"
                for p in profiles
            ]
            current_index = next(
                (i for i, p in enumerate(profiles) if p["candidate_id"] == active_id),
                0,
            )
            selected_index = st.selectbox(
                "Active Profile",
                range(len(profile_labels)),
                format_func=lambda i: profile_labels[i],
                index=current_index,
                key="profile_selector",
            )
            selected_id = profiles[selected_index]["candidate_id"]

            # Switch profile if user picks a different one
            if selected_id != active_id:
                try:
                    profile = api_get(f"/profiles/{selected_id}")
                    st.session_state.saved_profile = profile
                    st.session_state.active_profile_id = selected_id
                    st.rerun()
                except Exception as e:
                    show_api_error(e)
        else:
            st.info("No profiles yet. Click **New Profile** to create one.")

    with new_col:
        st.write("")  # vertical alignment
        st.write("")
        if st.button("＋ New", use_container_width=True):
            try:
                new_profile = api_post("/profiles", {
                    "profile_name": f"Profile {len(profiles) + 1}",
                    "full_name": st.session_state.full_name,
                    "current_title": "",
                    "location": "",
                    "years_experience": 0,
                    "skills": [], "tools": [], "domains": [],
                    "certifications": [], "projects": [],
                })
                st.session_state.active_profile_id = new_profile["candidate_id"]
                st.session_state.saved_profile = new_profile
                st.session_state.profiles_loaded = False   # force refresh
                st.success("New profile created.")
                st.rerun()
            except Exception as e:
                show_api_error(e)

    with del_col:
        st.write("")
        st.write("")
        if active_id and len(profiles) > 0:
            if st.button("🗑 Delete", use_container_width=True):
                try:
                    api_get(f"/profiles/{active_id}")  # confirm exists
                    requests.delete(
                        f"{st.session_state.api_url}/profiles/{active_id}",
                        headers=get_headers(),
                        timeout=30,
                    )
                    st.session_state.active_profile_id = None
                    st.session_state.saved_profile = {}
                    st.session_state.profiles_loaded = False
                    st.success("Profile deleted.")
                    st.rerun()
                except Exception as e:
                    show_api_error(e)

    # ── Show system-assigned Candidate ID (read-only) ─────
    if active_id:
        st.caption(f"🔑 Candidate ID (system-assigned): `{active_id}`")

    st.divider()

    # ── Profile Completeness Bar ──────────────────────────
    def compute_completeness_local(profile: dict) -> dict:
        """Compute completeness locally without an API call."""
        weights = {
            "skills": 25, "years_experience": 15, "current_title": 15,
            "education": 10, "seniority": 10, "domains": 10,
            "summary": 10, "location": 5,
        }
        labels = {
            "skills": "Skills (at least 3)",
            "years_experience": "Years of experience",
            "current_title": "Current job title",
            "education": "Education level",
            "seniority": "Seniority level",
            "domains": "Domain / industry",
            "summary": "Professional summary",
            "location": "Location",
        }
        score = 0
        missing = []
        for field, weight in weights.items():
            val = profile.get(field)
            ok = False
            if isinstance(val, list):
                ok = len(val) >= (3 if field == "skills" else 1)
            elif isinstance(val, int):
                ok = val > 0
            elif val:
                ok = True
            if ok:
                score += weight
            else:
                missing.append({"label": labels[field], "weight": weight})
        missing.sort(key=lambda x: x["weight"], reverse=True)
        return {"score": score, "missing": missing}

    current_profile_for_score = {
        "skills":           split_csv(st.session_state.get("candidate_skills", "")) or profile_value("skills", []),
        "years_experience": st.session_state.get("candidate_years_experience") or profile_value("years_experience", 0),
        "current_title":    st.session_state.get("candidate_current_title") or profile_value("current_title", ""),
        "education":        st.session_state.get("candidate_education") or profile_value("education", ""),
        "seniority":        st.session_state.get("candidate_seniority") or profile_value("seniority", ""),
        "domains":          split_csv(st.session_state.get("candidate_domains", "")) or profile_value("domains", []),
        "summary":          st.session_state.get("candidate_summary") or profile_value("summary", ""),
        "location":         st.session_state.get("candidate_location") or profile_value("location", ""),
    }
    completeness = compute_completeness_local(current_profile_for_score)
    score = completeness["score"]
    missing_fields = completeness["missing"]

    # Color the bar based on score
    if score >= 80:
        bar_color = "green"
        score_label = "Great"
    elif score >= 50:
        bar_color = "orange"
        score_label = "Good — a few things missing"
    else:
        bar_color = "red"
        score_label = "Incomplete — please fill in more details"

    st.markdown(f"**Profile Completeness: {score}% — {score_label}**")
    st.progress(score / 100)

    if missing_fields:
        with st.expander(f"📋 {len(missing_fields)} field(s) missing — click to see what to add"):
            for item in missing_fields:
                st.write(f"• **{item['label']}** — adds {item['weight']}%")

    st.divider()

    # ── Resume Upload Section ─────────────────────────────
    st.subheader("📄 Upload Resume to Auto-fill")
    st.write("Upload your resume and we'll extract your information automatically.")

    upload_col, info_col = st.columns([2, 3])
    with upload_col:
        uploaded_file = st.file_uploader(
            "Choose your resume",
            type=["pdf", "docx", "txt"],
            key="resume_upload",
            label_visibility="collapsed",
        )

    with info_col:
        st.caption("Supported formats: PDF, DOCX, TXT · Max size: 10 MB")
        st.caption("Your file is only used to fill the form below — it is not stored.")

    if uploaded_file is not None:
        if st.button("Extract & Auto-fill Profile", type="primary", key="extract_resume_btn"):
            with st.spinner("Reading your resume..."):
                try:
                    response = requests.post(
                        f"{st.session_state.api_url}/resume/parse",
                        headers={"Authorization": f"Bearer {st.session_state.token}"},
                        files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)},
                        timeout=60,
                    )
                    response.raise_for_status()
                    parsed = response.json()

                    extracted = parsed.get("extracted_profile", {})
                    comp = parsed.get("completeness", {})

                    # Store extracted data to pre-fill the form
                    st.session_state["resume_extracted"] = extracted

                    score_after = comp.get("score", 0)
                    missing_after = comp.get("missing", [])

                    st.success(f"Resume parsed! Profile completeness from your resume: **{score_after}%**")

                    if missing_after:
                        st.warning(
                            "We couldn't detect the following — please fill them in manually: "
                            + ", ".join(f['label'] for f in missing_after)
                        )
                    else:
                        st.success("All profile fields were detected!")

                except requests.exceptions.HTTPError as e:
                    try:
                        detail = e.response.json().get("detail", str(e))
                    except Exception:
                        detail = str(e)
                    st.error(f"Could not parse resume: {detail}")
                except Exception as e:
                    st.error(f"Error: {e}")

    # If resume was just extracted, pre-fill session state values
    if st.session_state.get("resume_extracted"):
        ex = st.session_state["resume_extracted"]
        if ex.get("full_name"):
            st.session_state["candidate_full_name"] = ex["full_name"]
        if ex.get("current_title"):
            st.session_state["candidate_current_title"] = ex["current_title"]
        if ex.get("location"):
            st.session_state["candidate_location"] = ex["location"]
        if ex.get("years_experience"):
            st.session_state["candidate_years_experience"] = ex["years_experience"]
        if ex.get("education"):
            st.session_state["candidate_education"] = ex["education"]
        if ex.get("seniority"):
            st.session_state["candidate_seniority"] = ex["seniority"]
        if ex.get("skills"):
            st.session_state["candidate_skills"] = ", ".join(ex["skills"])
        if ex.get("tools"):
            st.session_state["candidate_tools"] = ", ".join(ex["tools"])
        if ex.get("domains"):
            st.session_state["candidate_domains"] = ", ".join(ex["domains"])
        if ex.get("summary"):
            st.session_state["candidate_summary"] = ex["summary"]
        if ex.get("certifications"):
            st.session_state["candidate_certifications"] = ", ".join(ex["certifications"])
        if ex.get("projects"):
            st.session_state["candidate_projects"] = ", ".join(ex["projects"])
        # Clear so it doesn't re-apply on every rerun
        st.session_state["resume_extracted"] = None

    st.divider()

    # ── Profile form ──────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.text_input(
            "Profile Name",
            value=profile_value("profile_name", "My Profile"),
            key="candidate_profile_name",
            help="A label for this profile, e.g. 'Data Scientist Profile'",
        )
        st.text_input(
            "Full Name",
            value=profile_value("full_name", st.session_state.full_name),
            key="candidate_full_name",
        )
        st.text_input(
            "Current Title",
            value=profile_value("current_title", ""),
            key="candidate_current_title",
        )
        st.text_input(
            "Location",
            value=profile_value("location", ""),
            key="candidate_location",
        )
        st.selectbox(
            "Education",
            ["", "high_school", "associate", "bachelor", "master", "phd"],
            index=["", "high_school", "associate", "bachelor", "master", "phd"].index(
                profile_value("education", "") or ""
            )
            if (profile_value("education", "") or "") in ["", "high_school", "associate", "bachelor", "master", "phd"]
            else 0,
            key="candidate_education",
        )
        st.number_input(
            "Years of Experience",
            min_value=0,
            max_value=60,
            value=int(profile_value("years_experience", 0) or 0),
            key="candidate_years_experience",
        )

    with col2:
        st.selectbox(
            "Seniority",
            ["", "intern", "entry", "junior", "mid", "senior", "manager"],
            index=["", "intern", "entry", "junior", "mid", "senior", "manager"].index(
                profile_value("seniority", "") or ""
            )
            if (profile_value("seniority", "") or "") in ["", "intern", "entry", "junior", "mid", "senior", "manager"]
            else 0,
            key="candidate_seniority",
        )
        st.text_area(
            "Skills",
            value=join_list(profile_value("skills", [])),
            key="candidate_skills",
            help="Comma-separated values",
        )
        st.text_area(
            "Tools",
            value=join_list(profile_value("tools", [])),
            key="candidate_tools",
            help="Comma-separated values",
        )
        st.text_area(
            "Domains",
            value=join_list(profile_value("domains", [])),
            key="candidate_domains",
            help="Comma-separated values",
        )

    st.text_area(
        "Certifications",
        value=join_list(profile_value("certifications", [])),
        key="candidate_certifications",
        help="Comma-separated values",
    )
    st.text_area(
        "Projects",
        value=join_list(profile_value("projects", [])),
        key="candidate_projects",
        help="Comma-separated values",
    )
    st.text_area(
        "Summary",
        value=profile_value("summary", "") or "",
        key="candidate_summary",
    )

    if st.button("Save Profile", type="primary"):
        if not active_id:
            st.warning("Please create a profile first using the '＋ New' button.")
        else:
            try:
                payload = {
                    "profile_name": st.session_state.get("candidate_profile_name", "My Profile"),
                    "full_name": st.session_state.get("candidate_full_name", ""),
                    "current_title": st.session_state.get("candidate_current_title", ""),
                    "location": st.session_state.get("candidate_location", ""),
                    "education": st.session_state.get("candidate_education") or None,
                    "years_experience": int(st.session_state.get("candidate_years_experience", 0)),
                    "skills": split_csv(st.session_state.get("candidate_skills", "")),
                    "tools": split_csv(st.session_state.get("candidate_tools", "")),
                    "domains": split_csv(st.session_state.get("candidate_domains", "")),
                    "certifications": split_csv(st.session_state.get("candidate_certifications", "")),
                    "projects": split_csv(st.session_state.get("candidate_projects", "")),
                    "seniority": st.session_state.get("candidate_seniority") or None,
                    "summary": st.session_state.get("candidate_summary") or None,
                }
                result = api_post(f"/profiles/{active_id}", payload, method="PUT")
                st.session_state.saved_profile = result
                st.session_state.profiles_loaded = False  # refresh selector
                st.success("Profile saved successfully.")
                st.rerun()
            except Exception as e:
                show_api_error(e)


# ============================================================
# My Job Matches  (unified live search + ranking by fit)
# ============================================================
with page[1]:
    st.header("🎯 My Job Matches")
    st.write(
        "Live jobs from LinkedIn, Indeed, Glassdoor and more — ranked by how well they fit **your** profile."
    )

    # ── Guard: profile must be loaded ──────────────────────────
    # Use saved_profile (full profile from GET /profiles/{id}) which contains
    # skills, tools, domains etc. The all_profiles list only has lightweight
    # summary fields and must NOT be used for matching.
    active_profile = st.session_state.get("saved_profile") or None
    if active_profile and active_profile.get("candidate_id") != st.session_state.get("active_profile_id"):
        # Profile ID mismatch — re-fetch the correct full profile
        try:
            active_profile = api_get(f"/profiles/{st.session_state['active_profile_id']}")
            st.session_state["saved_profile"] = active_profile
        except Exception:
            active_profile = None

    if not active_profile:
        st.info("👈 Please complete your profile in **My Profile** first, then come back here.")
    else:
        # ── Search controls ────────────────────────────────────
        st.divider()

        # Pre-fill search query from profile title
        default_query = active_profile.get("current_title", "")

        col1, col2 = st.columns(2)
        with col1:
            matches_query = st.text_input(
                "Job Title / Keywords",
                value=st.session_state.get("matches_query", default_query),
                placeholder="e.g. data scientist, machine learning engineer",
                key="matches_query",
            )
            matches_location = st.text_input(
                "Location (optional)",
                value=st.session_state.get("matches_location", active_profile.get("location", "")),
                placeholder="e.g. Toronto, remote, New York",
                key="matches_location",
            )

        with col2:
            matches_top_k = st.number_input(
                "Number of results",
                min_value=1,
                max_value=10,
                value=st.session_state.get("matches_top_k", 5),
                key="matches_top_k",
            )
            matches_date_posted = st.selectbox(
                "Date Posted",
                options=["all", "today", "3days", "week", "month"],
                index=["all", "today", "3days", "week", "month"].index(
                    st.session_state.get("matches_date_posted", "week")
                ),
                key="matches_date_posted",
            )

        matches_use_prefs = st.checkbox(
            "Apply my saved preferences (location filter, min score, seniority…)",
            value=False,
            key="matches_use_prefs",
        )

        search_clicked = st.button(
            "🔍 Find My Best Matches",
            type="primary",
            key="matches_search_btn",
        )

        if search_clicked:
            if not matches_query.strip():
                st.warning("Please enter a job title or keywords.")
            else:
                try:
                    with st.spinner(f"Searching live jobs for '{matches_query}'…"):
                        live_payload = {
                            "candidate": {
                                "candidate_id": active_profile.get("candidate_id", ""),
                                "full_name": active_profile.get("full_name", ""),
                                "current_title": active_profile.get("current_title", ""),
                                "location": active_profile.get("location", ""),
                                "education": active_profile.get("education"),
                                "years_experience": active_profile.get("years_experience", 0),
                                "skills": active_profile.get("skills", []),
                                "tools": active_profile.get("tools", []),
                                "domains": active_profile.get("domains", []),
                                "seniority": active_profile.get("seniority"),
                                "summary": active_profile.get("summary"),
                                "certifications": active_profile.get("certifications", []),
                                "projects": active_profile.get("projects", []),
                            },
                            "search_query": matches_query.strip(),
                            "location": matches_location.strip(),
                            "top_k": int(matches_top_k),
                            "date_posted": matches_date_posted,
                            "preferences": build_preferences_payload() if matches_use_prefs else None,
                        }
                        live_result = api_post("/recommendations/live", live_payload)
                        st.session_state["last_live_recommendations"] = live_result

                    count = live_result.get("count", 0)
                    st.success(f"Found and scored {count} live jobs — ranked best fit first.")

                except Exception as e:
                    show_api_error(e)

        # ── Results ────────────────────────────────────────────
        if st.session_state.get("last_live_recommendations"):
            result = st.session_state["last_live_recommendations"]
            recommendations = result.get("recommendations", [])

            if not recommendations:
                st.warning("No matching jobs found. Try broader keywords or a different location.")
            else:
                st.divider()
                st.subheader(f"Top {len(recommendations)} Jobs Ranked by Fit")

                for index, item in enumerate(recommendations, start=1):
                    score = item.get("score", 0)
                    fit   = item.get("fit_label", "Unknown")
                    passed = item.get("hard_filters_passed", False)
                    matched = item.get("matched_required_skills", [])
                    missing = item.get("missing_required_skills", [])
                    source_url  = item.get("source_url", "")
                    date_posted = item.get("date_posted", "")
                    snippet     = item.get("description_snippet", "")

                    # Site name from URL
                    site_name = ""
                    if source_url:
                        try:
                            from urllib.parse import urlparse
                            _domain = urlparse(source_url).netloc.lower().replace("www.", "")
                            _site_map = {
                                "linkedin.com": "LinkedIn", "indeed.com": "Indeed",
                                "glassdoor.com": "Glassdoor", "ziprecruiter.com": "ZipRecruiter",
                                "monster.com": "Monster", "dice.com": "Dice",
                                "simplyhired.com": "SimplyHired", "careerbuilder.com": "CareerBuilder",
                            }
                            for _k, _v in _site_map.items():
                                if _k in _domain:
                                    site_name = _v
                                    break
                            if not site_name:
                                site_name = _domain.split(".")[0].capitalize()
                        except Exception:
                            pass

                    if score >= 75:
                        ring_color = "#2ea043"
                    elif score >= 50:
                        ring_color = "#d29922"
                    else:
                        ring_color = "#da3633"

                    hf_html = '<span class="hf-pass">✅ Meets all requirements</span>' if passed else '<span class="hf-fail">⚠️ Partial match</span>'
                    matched_chips = " ".join(f'<span class="chip-green">{s}</span>' for s in matched) if matched else "<em style='color:#8b949e'>None</em>"
                    missing_chips = " ".join(f'<span class="chip-red">{s}</span>' for s in missing) if missing else '<span style="color:#2ea043;font-size:0.85rem">None — great fit! 🎉</span>'
                    meta_parts = [p for p in [item.get("company",""), item.get("location",""), item.get("workplace_type","")] if p]
                    meta_str = "  ·  ".join(meta_parts)
                    badge_str = ""
                    if site_name:
                        badge_str += f'<span style="background:#21262d;color:#58a6ff;padding:2px 8px;border-radius:4px;font-size:0.75rem;margin-right:6px;">🌐 {site_name}</span>'
                    if date_posted:
                        badge_str += f'<span style="color:#8b949e;font-size:0.8rem;">📅 {date_posted}</span>'
                    snippet_html = f'<div style="color:#8b949e;font-size:0.85rem;margin-top:8px;line-height:1.5;">{snippet[:280]}{"…" if len(snippet)>280 else ""}</div>' if snippet else ""
                    apply_btn = f'<a href="{source_url}" target="_blank" class="apply-btn">🚀 Apply Now</a>' if source_url else ""

                    if score >= 75:
                        ring_color = "#10b981"; ring_glow = "rgba(16,185,129,0.3)"
                    elif score >= 50:
                        ring_color = "#f59e0b"; ring_glow = "rgba(245,158,11,0.3)"
                    else:
                        ring_color = "#ef4444"; ring_glow = "rgba(239,68,68,0.3)"

                    hf_html = '<span class="hf-pass">✅ Meets all requirements</span>' if passed else '<span class="hf-fail">⚠️ Partial match</span>'
                    matched_chips = " ".join(f'<span class="chip-green">{s}</span>' for s in matched) if matched else "<em style='color:#475569'>None</em>"
                    missing_chips = " ".join(f'<span class="chip-red">{s}</span>' for s in missing) if missing else '<span style="color:#10b981;font-size:0.85rem;font-weight:600;">🎉 None — perfect fit!</span>'
                    meta_parts = [p for p in [item.get("company",""), item.get("location",""), item.get("workplace_type","")] if p]
                    meta_str = "  ·  ".join(meta_parts)
                    badge_str = ""
                    if site_name:
                        badge_str += f'<span style="background:rgba(99,102,241,0.15);color:#a5b4fc;padding:2px 9px;border-radius:20px;font-size:0.72rem;font-weight:700;border:1px solid rgba(99,102,241,0.3);margin-right:6px;">🌐 {site_name}</span>'
                    if date_posted:
                        badge_str += f'<span style="color:#64748b;font-size:0.78rem;">📅 {date_posted}</span>'
                    snippet_html = f'<div style="color:#64748b;font-size:0.83rem;margin-top:8px;line-height:1.55;">{snippet[:280]}{"…" if len(snippet)>280 else ""}</div>' if snippet else ""
                    apply_btn = f'<a href="{source_url}" target="_blank" class="apply-btn">🚀 Apply Now</a>' if source_url else ""

                    card_html = (
                        '<div class="jm-card">'
                        '<div style="display:flex;align-items:flex-start;justify-content:space-between;gap:16px;">' 
                        '<div style="flex:1;min-width:0;">' 
                        f'<div style="font-size:1.15rem;font-weight:800;color:#e2e8f0;margin-bottom:5px;line-height:1.3;">' 
                        f'<span style="color:#6366f1;font-size:0.85rem;font-weight:700;margin-right:8px;">#{index}</span>' 
                        f'{item.get("title","Untitled")}</div>' 
                        f'<div style="font-size:0.83rem;color:#64748b;margin-bottom:6px;">{meta_str}</div>' 
                        f'<div style="margin-bottom:4px;">{badge_str}</div>' 
                        f'{snippet_html}' 
                        f'<div style="margin-top:10px;">{hf_html}</div>' 
                        '</div>' 
                        f'<div class="score-ring" style="border-color:{ring_color};color:{ring_color};background:rgba(0,0,0,0.3);box-shadow:0 0 18px {ring_glow};flex-shrink:0;">' 
                        f'{score}%<br><span style="font-size:0.58rem;font-weight:600;color:#64748b;text-transform:uppercase;">{fit}</span>' 
                        '</div></div>' 
                        '<div class="card-divider"></div>' 
                        '<div style="display:flex;gap:20px;flex-wrap:wrap;">' 
                        '<div style="flex:1;min-width:180px;">' 
                        '<div style="font-size:0.72rem;font-weight:700;color:#10b981;text-transform:uppercase;letter-spacing:.07em;margin-bottom:7px;">✔ Matched Skills</div>' 
                        f'<div style="line-height:2;">{matched_chips}</div></div>' 
                        '<div style="flex:1;min-width:180px;">' 
                        '<div style="font-size:0.72rem;font-weight:700;color:#ef4444;text-transform:uppercase;letter-spacing:.07em;margin-bottom:7px;">✘ Missing Skills</div>' 
                        f'<div style="line-height:2;">{missing_chips}</div></div>' 
                        '</div>' 
                        + ('<div class="card-divider"></div><div>' + apply_btn + '</div>' if apply_btn else "") 
                        + '</div>'
                    )
                    st.markdown(card_html, unsafe_allow_html=True)

                    recs = item.get("recommendations", [])
                    if recs:
                        with st.expander("💡 How to improve your match"):
                            for rec in recs:
                                st.write(f"• {rec}")


# ============================================================
# Preferences
# ============================================================
with page[2]:
    st.header("Job Preferences")

    st.text_area(
        "Preferred Titles",
        value=join_list(preference_value("preferred_titles", [])),
        key="preferred_titles",
        help="Example: data scientist, machine learning engineer",
    )

    st.text_area(
        "Preferred Locations",
        value=join_list(preference_value("preferred_locations", [])),
        key="preferred_locations",
        help="Example: ottawa, toronto, remote",
    )

    st.text_area(
        "Preferred Workplace Types",
        value=join_list(preference_value("preferred_workplace_types", [])),
        key="preferred_workplace_types",
        help="Example: remote, hybrid, on-site",
    )

    st.number_input(
        "Minimum Match Score (%)",
        min_value=0,
        max_value=100,
        value=int(preference_value("min_score", 50) or 50),
        key="min_score",
    )

    if st.button("Save Preferences", type="primary"):
        try:
            payload = build_preferences_payload()
            result = api_post("/preferences", payload)
            st.session_state.saved_preferences = result
            st.success("Preferences saved successfully.")
        except Exception as e:
            show_api_error(e)

    with st.expander("Preferences JSON Preview"):
        st.json(build_preferences_payload())

    # ── Change Password ────────────────────────────────────
    st.divider()
    st.subheader("Change Password")

    if not st.session_state.is_logged_in:
        st.info("Log in to change your password.")
    else:
        with st.form("change_password_form"):
            current_pw  = st.text_input("Current Password", type="password", key="cp_current")
            new_pw      = st.text_input("New Password",     type="password", key="cp_new")
            confirm_pw  = st.text_input("Confirm New Password", type="password", key="cp_confirm")
            submitted   = st.form_submit_button("Change Password", use_container_width=True)

        if submitted:
            if new_pw != confirm_pw:
                st.error("New passwords do not match.")
            elif not current_pw or not new_pw:
                st.error("Please fill in all fields.")
            else:
                try:
                    api_post(
                        "/auth/change-password",
                        {"current_password": current_pw, "new_password": new_pw},
                    )
                    st.success("Password changed successfully.")
                except Exception as e:
                    show_api_error(e)
