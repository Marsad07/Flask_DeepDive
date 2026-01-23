from flask import render_template, request, redirect, url_for, session
from app.services.atlas_ai_service import get_atlas_reply
import uuid

WELCOME = "Hi, I’m Atlas AI \nHow can I help you study today?"

def _init_chat_store():
    if "atlas_chats" not in session or not isinstance(session["atlas_chats"], dict):
        session["atlas_chats"] = {}
    if "atlas_current_chat" not in session or session["atlas_current_chat"] not in session["atlas_chats"]:
        chat_id = uuid.uuid4().hex[:8]
        session["atlas_chats"][chat_id] = {
            "title": "New chat",
            "messages": [{"role": "Atlas", "content": WELCOME}]
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
        messages=chat["messages"]
    )

def chat_new():
    _init_chat_store()
    chat_id = uuid.uuid4().hex[:8]
    session["atlas_chats"][chat_id] = {
        "title": "New chat",
        "messages": [{"role": "Atlas", "content": WELCOME}]
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
            chat["title"] = user_text[:24] + ("..." if len(user_text) > 24 else "")

    if uploaded and uploaded.filename:
        filename = uploaded.filename
        chat["messages"].append({"role": "Atlas", "content": f"📎 File selected: {filename}"})

        if filename.lower().endswith(".txt"):
            file_text = uploaded.read().decode("utf-8", errors="ignore").strip()
            if file_text:
                chat["messages"].append({"role": "You", "content": "[Uploaded notes]\n" + file_text})
        else:
            chat["messages"].append({"role": "Atlas", "content": "I can only read .txt files right now."})
            session.modified = True
            return redirect(url_for("atlas.chat_page"))

    try:
        history = chat["messages"][-12:]
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