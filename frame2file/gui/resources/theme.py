PALETTE = {
    "bg": "#080d14",
    "panel": "#111924",
    "panel_alt": "#15202c",
    "panel_soft": "#1a2532",
    "border": "#263445",
    "border_focus": "#3d6eaa",
    "accent": "#5ea8ff",
    "accent_hover": "#77b7ff",
    "accent_soft": "#183b63",
    "text": "#eef5ff",
    "text_secondary": "#a9b8c9",
    "text_muted": "#738397",
    "success": "#31c968",
    "success_hover": "#48dd7b",
    "success_active": "#24a956",
    "danger": "#e65b66",
    "danger_hover": "#f0717c",
}


def app_stylesheet() -> str:
    colors = PALETTE
    return f"""
    QMainWindow, QWidget {{
        background: {colors["bg"]};
        color: {colors["text"]};
        font-family: "Segoe UI";
        font-size: 10pt;
    }}

    QLabel#AppTitle {{
        color: {colors["text"]};
        font-size: 30px;
        font-weight: 800;
    }}

    QLabel#Subtitle, QLabel#Muted {{
        color: {colors["text_secondary"]};
    }}

    QLabel#SectionTitle {{
        color: {colors["text"]};
        font-size: 13px;
        font-weight: 700;
    }}

    QFrame#Panel {{
        background: {colors["panel"]};
        border: 1px solid {colors["border"]};
        border-radius: 16px;
    }}

    QFrame#HeaderLogo {{
        background: {colors["panel_alt"]};
        border: 1px solid {colors["border"]};
        border-radius: 18px;
    }}

    QLineEdit {{
        background: {colors["panel_soft"]};
        border: 1px solid {colors["border"]};
        border-radius: 10px;
        color: {colors["text"]};
        padding: 10px 12px;
        selection-background-color: {colors["accent_soft"]};
    }}

    QLineEdit:focus {{
        border-color: {colors["border_focus"]};
    }}

    QPushButton {{
        background: {colors["panel_soft"]};
        border: 1px solid {colors["border"]};
        border-radius: 10px;
        color: {colors["text"]};
        font-weight: 700;
        padding: 10px 14px;
    }}

    QPushButton:hover {{
        background: #213246;
        border-color: {colors["accent"]};
    }}

    QPushButton:pressed {{
        background: #172434;
    }}

    QPushButton:disabled {{
        color: {colors["text_muted"]};
        background: #121b26;
        border-color: #1d2a38;
    }}

    QPushButton#PrimaryButton {{
        background: {colors["accent"]};
        color: #06111f;
        border: 0;
    }}

    QPushButton#DangerButton:hover {{
        border-color: {colors["danger"]};
        color: #ffd9dd;
    }}

    QPushButton#ExportButton {{
        background: {colors["success"]};
        color: #04170d;
        border: 0;
        border-radius: 14px;
        font-size: 16px;
        font-weight: 900;
        padding: 15px 18px;
    }}

    QPushButton#ExportButton:hover {{
        background: {colors["success_hover"]};
    }}

    QPushButton#ExportButton:pressed {{
        background: {colors["success_active"]};
    }}

    QProgressBar {{
        background: {colors["panel_soft"]};
        border: 1px solid {colors["border"]};
        border-radius: 8px;
        color: transparent;
        min-height: 14px;
        max-height: 14px;
    }}

    QProgressBar::chunk {{
        background: {colors["success"]};
        border-radius: 7px;
    }}

    QListWidget#ThumbnailList {{
        background: {colors["panel"]};
        border: 1px solid {colors["border"]};
        border-radius: 14px;
        padding: 14px;
        outline: 0;
    }}

    QListWidget#ThumbnailList::item {{
        background: {colors["panel_alt"]};
        border: 1px solid {colors["border"]};
        border-radius: 14px;
        color: {colors["text_secondary"]};
        padding: 10px;
        margin: 4px;
    }}

    QListWidget#ThumbnailList::item:hover {{
        background: #192638;
        border-color: #38516e;
        color: {colors["text"]};
    }}

    QListWidget#ThumbnailList::item:selected {{
        background: #183456;
        border: 2px solid {colors["accent"]};
        color: {colors["text"]};
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 12px;
        margin: 6px 2px 6px 2px;
    }}

    QScrollBar::handle:vertical {{
        background: #2b3c50;
        border-radius: 5px;
        min-height: 42px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: #3d5874;
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    QMessageBox {{
        background: {colors["panel"]};
    }}
    """
