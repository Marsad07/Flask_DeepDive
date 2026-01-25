from flask import render_template, request, redirect, url_for, session
from app.services.atlas_ai_service import get_atlas_reply
from PIL import Image
import pytesseract
from docx import Document
import uuid

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

WELCOME = "Hi, I’m Atlas AI \nHow can I help you study today?"
ALLOWED_EXTS = {"txt", "pdf", "docx", "png", "jpg", "jpeg"}

def _ext(filename: str) -> str:
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[1].lower()

def _read_txt(uploaded) -> str:
    data = uploaded.read()
    return data.decode("utf-8", errors="replace").strip()

def _read_docx(uploaded) -> str:
    doc = Document(uploaded)
    lines = [p.text for p in doc.paragraphs if p.text]
    return "\n".join(lines).strip()

def _read_pdf(uploaded) -> str:
    if PdfReader is None:
        return ""
    reader = PdfReader(uploaded)
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts).strip()

def _read_image(uploaded) -> str:
    img = Image.open(uploaded)
    text = pytesseract.image_to_string(img)
    return text.strip()

def _init_chat_store():
    if "atlas_chats" not in session or not isinstance(session["atlas_chats"], dict):
        session["atlas_chats"] = {}

    if (
        "atlas_current_chat" not in session
        or session["atlas_current_chat"] not in session["atlas_chats"]
    ):
        chat_id = uuid.uuid4().hex[:8]
        session["atlas_chats"][chat_id] = {
            "title": "New chat",
            "messages": [{"role": "Atlas", "content": WELCOME}],
            "notes_text": "",
        }
        session["atlas_current_chat"] = chat_id

    session.modified = True

def _get_current():
    _init_chat_store()
    chat_id = session["atlas_current_chat"]
    return chat_id, session["atlas_chats"][chat_id]

def chat_page():
    chat_id, chat = _get_current()
    chats = session["atlas_chats"]
    return render_template(
        "atlas_chat.html",
        chats=chats,
        current_chat_id=chat_id,
        messages=chat["messages"],
    )

def chat_new():
    _init_chat_store()
    chat_id = uuid.uuid4().hex[:8]
    session["atlas_chats"][chat_id] = {
        "title": "New chat",
        "messages": [{"role": "Atlas", "content": WELCOME}],
        "notes_text": "",
    }
    session["atlas_current_chat"] = chat_id
    session.modified = True
    return redirect(url_for("atlas.chat_page"))

def chat_switch(chat_id):
    _init_chat_store()
    if chat_id in session["atlas_chats"]:
        session["atlas_current_chat"] = chat_id
        session.modified = True
    return redirect(url_for("atlas.chat_page"))

def chat_delete(chat_id):
    _init_chat_store()
    if chat_id in session["atlas_chats"]:
        session["atlas_chats"].pop(chat_id, None)
        if session.get("atlas_current_chat") == chat_id:
            remaining = list(session["atlas_chats"].keys())
            if remaining:
                session["atlas_current_chat"] = remaining[0]
            else:
                session.pop("atlas_current_chat", None)
        session.modified = True
    return redirect(url_for("atlas.chat_page"))

def chat_send():
    chat_id, chat = _get_current()

    user_text = (request.form.get("message") or "").strip()
    uploaded = request.files.get("attachment")

    if not user_text and not (uploaded and uploaded.filename):
        return redirect(url_for("atlas.chat_page"))

    if user_text:
        chat["messages"].append({"role": "You", "content": user_text})
        if chat.get("title") == "New chat":
            short = user_text[:24]
            chat["title"] = short + ("..." if len(user_text) > 24 else "")

    if uploaded and uploaded.filename:
        filename = uploaded.filename
        chat["messages"].append(
            {"role": "Atlas", "content": f"📎 File selected: {filename}"}
        )
        ext = _ext(filename)

        if ext not in ALLOWED_EXTS:
            chat["messages"].append(
                {
                    "role": "Atlas",
                    "content": (
                        "I can read .txt, .pdf, .docx, and images "
                        "(.png, .jpg, .jpeg)."
                    ),
                }
            )
            session["atlas_chats"][chat_id] = chat
            session.modified = True
            return redirect(url_for("atlas.chat_page"))

        if ext == "txt":
            file_text = _read_txt(uploaded)
        elif ext == "docx":
            file_text = _read_docx(uploaded)
        elif ext in {"png", "jpg", "jpeg"}:
            file_text = _read_image(uploaded)
        else:
            file_text = _read_pdf(uploaded)
            if not file_text:
                chat["messages"].append(
                    {
                        "role": "Atlas",
                        "content": (
                            "PDF support requires pypdf. "
                            "Run: pip install pypdf"
                        ),
                    }
                )
                session["atlas_chats"][chat_id] = chat
                session.modified = True
                return redirect(url_for("atlas.chat_page"))

        if file_text:
            chat["notes_text"] = file_text

            chat["messages"].append(
                {
                    "role": "Atlas",
                    "content": (
                        "📄 I’ve loaded your notes.\n"
                        "What would you like to do?\n\n"
                        "• Summarise them\n"
                        "• Explain a topic simply\n"
                        "• Create quiz questions\n"
                        "• Ask a specific question"
                    ),
                }
            )

            if not user_text:
                session["atlas_chats"][chat_id] = chat
                session.modified = True
                return redirect(url_for("atlas.chat_page"))
        else:
            chat["messages"].append(
                {
                    "role": "Atlas",
                    "content": (
                        "I couldn’t extract any readable text "
                        "from that file."
                    ),
                }
            )

            if not user_text:
                session["atlas_chats"][chat_id] = chat
                session.modified = True
                return redirect(url_for("atlas.chat_page"))

    try:
        history = chat["messages"][-12:]
        notes = (chat.get("notes_text") or "").strip()
        if notes:
            history = (
                [{"role": "system",
                  "content": "User's uploaded notes:\n" + notes}]
                + history
            )
        reply = get_atlas_reply(history)
    except Exception:
        reply = "Atlas is temporarily unavailable. Please try again."

    chat["messages"].append({"role": "Atlas", "content": reply})
    session["atlas_chats"][chat_id] = chat
    session.modified = True
    return redirect(url_for("atlas.chat_page"))

def chat_rename(chat_id):
    _init_chat_store()
    new_title = (request.form.get("title") or "").strip()

    if chat_id in session["atlas_chats"] and new_title:
        session["atlas_chats"][chat_id]["title"] = new_title[:40]
        session.modified = True

    return redirect(url_for("atlas.chat_page"))

