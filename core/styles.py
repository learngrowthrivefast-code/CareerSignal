import streamlit as st

def apply_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    :root {
        --primary:       #6366f1;
        --primary-light: #818cf8;
        --primary-dark:  #4f46e5;
        --cyan:          #22d3ee;
        --bg-card:       rgba(255,255,255,0.04);
        --border:        rgba(255,255,255,0.08);
        --border-hover:  rgba(99,102,241,0.4);
        --muted:         #94a3b8;
        --success:       #10b981;
        --warning:       #f59e0b;
    }

    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

    /* ── Hide Streamlit chrome ── */
    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }

    /* ── Metrics ── */
    [data-testid="metric-container"] {
        background    : rgba(99,102,241,0.07) !important;
        border        : 1px solid rgba(99,102,241,0.2) !important;
        border-radius : 10px !important;
        padding       : 16px 20px !important;
    }
    [data-testid="stMetricLabel"] {
        font-size      : 11px !important;
        text-transform : uppercase !important;
        letter-spacing : 1px !important;
        color          : var(--muted) !important;
    }
    [data-testid="stMetricValue"] {
        font-size   : 22px !important;
        font-weight : 700 !important;
        color       : var(--primary-light) !important;
    }

    /* ── Buttons ── */
    .stButton > button[kind="primary"] {
        background    : linear-gradient(135deg, var(--primary), #8b5cf6) !important;
        border        : none !important;
        border-radius : 8px !important;
        font-weight   : 600 !important;
        letter-spacing: 0.3px !important;
        box-shadow    : 0 4px 15px rgba(99,102,241,0.25) !important;
        transition    : all 0.2s ease !important;
    }
    .stButton > button[kind="primary"]:hover {
        transform  : translateY(-1px) !important;
        box-shadow : 0 6px 20px rgba(99,102,241,0.4) !important;
    }
    .stButton > button[kind="secondary"] {
        border        : 1px solid var(--border) !important;
        border-radius : 8px !important;
        background    : var(--bg-card) !important;
        transition    : all 0.2s ease !important;
    }
    .stButton > button[kind="secondary"]:hover {
        border-color : var(--primary-light) !important;
        background   : rgba(99,102,241,0.1) !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        background    : var(--bg-card) !important;
        border        : 1px solid var(--border) !important;
        border-radius : 10px !important;
        padding       : 4px !important;
        gap           : 4px !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius : 8px !important;
        font-weight   : 500 !important;
        font-size     : 14px !important;
    }
    .stTabs [aria-selected="true"] {
        background : var(--primary) !important;
        color      : white !important;
    }

    /* ── Expanders ── */
    .streamlit-expanderHeader {
        border-radius : 10px !important;
        background    : var(--bg-card) !important;
        border        : 1px solid var(--border) !important;
        font-weight   : 500 !important;
        transition    : border-color 0.2s ease !important;
    }
    .streamlit-expanderHeader:hover {
        border-color : var(--border-hover) !important;
    }
    .streamlit-expanderContent {
        border        : 1px solid var(--border) !important;
        border-top    : none !important;
        border-radius : 0 0 10px 10px !important;
        padding       : 16px !important;
    }

    /* ── Progress bar ── */
    .stProgress > div > div > div {
        background    : linear-gradient(90deg, var(--primary), var(--cyan)) !important;
        border-radius : 10px !important;
    }

    /* ── Inputs ── */
    .stTextInput > div > div > input,
    .stTextArea  > div > div > textarea {
        border-radius : 8px !important;
        border        : 1px solid var(--border) !important;
        background    : var(--bg-card) !important;
        transition    : border-color 0.2s ease !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea  > div > div > textarea:focus {
        border-color : var(--primary-light) !important;
        box-shadow   : 0 0 0 2px rgba(99,102,241,0.2) !important;
    }
    .stSelectbox > div > div {
        border-radius : 8px !important;
        border        : 1px solid var(--border) !important;
        background    : var(--bg-card) !important;
    }

    /* ── Divider ── */
    hr {
        border-color : var(--border) !important;
        margin       : 20px 0 !important;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background   : #0d0d1a !important;
        border-right : 1px solid var(--border) !important;
    }

    /* ── Alerts ── */
    [data-testid="stAlert"] {
        border-radius : 10px !important;
    }

    /* ── Chat ── */
    [data-testid="stChatMessage"] {
        border-radius : 12px !important;
    }

    /* ── Reusable HTML components ── */
    .cs-page-header { padding-bottom: 20px; }
    .cs-page-title {
        font-size  : 26px;
        font-weight: 700;
        background : linear-gradient(135deg, #f1f5f9, #a5b4fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin     : 0;
        line-height: 1.3;
    }
    .cs-page-subtitle {
        color      : var(--muted);
        font-size  : 14px;
        margin-top : 6px;
    }
    .cs-card {
        background    : var(--bg-card);
        border        : 1px solid var(--border);
        border-radius : 12px;
        padding       : 20px 24px;
        margin-bottom : 16px;
    }
    .cs-badge {
        display        : inline-block;
        padding        : 3px 10px;
        border-radius  : 20px;
        font-size      : 11px;
        font-weight    : 600;
        letter-spacing : 0.5px;
        text-transform : uppercase;
    }
    .cs-badge-indigo {
        background : rgba(99,102,241,0.15);
        color      : #a5b4fc;
        border     : 1px solid rgba(99,102,241,0.3);
    }
    .cs-badge-green {
        background : rgba(16,185,129,0.15);
        color      : #6ee7b7;
        border     : 1px solid rgba(16,185,129,0.3);
    }
    .cs-badge-amber {
        background : rgba(245,158,11,0.15);
        color      : #fcd34d;
        border     : 1px solid rgba(245,158,11,0.3);
    }
    </style>
    """, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = ""):
    st.markdown(f"""
    <div class="cs-page-header">
        <p class="cs-page-title">{title}</p>
        {"" if not subtitle else f'<p class="cs-page-subtitle">{subtitle}</p>'}
    </div>
    """, unsafe_allow_html=True)
