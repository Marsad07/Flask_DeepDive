from flask import render_template, session, redirect, url_for, request
from flask_intro.app.database import db3

def atlas_hub():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    cursor = db3.cursor(dictionary=True)
    cursor.execute("SELECT id, name FROM subjects WHERE user_id=%s", (user_id,))
    subjects = cursor.fetchall()

    return render_template("atlas_hub.html", subjects=subjects)

def atlas_subject(subject_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    cursor = db3.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, name, notes FROM subjects WHERE id=%s AND user_id=%s",
        (subject_id, user_id)
    )
    subject = cursor.fetchone()

    if not subject:
        return "Subject not found", 404

    return render_template("atlas_page.html", subject=subject)

def atlas_generate(subject_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    cursor = db3.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, name, notes FROM subjects WHERE id=%s AND user_id=%s",
        (subject_id, user_id)
    )
    subject = cursor.fetchone()

    if not subject:
        return "Subject not found", 404

    user_prompt = (request.form.get("user_prompt") or "").strip()
    use_notes = request.form.get("use_notes") == "1"

    notes = (subject.get("notes") or "").strip()

    if user_prompt == "":
        result = "Please type a prompt or click a suggested prompt."
        return render_template("atlas_page.html",
                               subject=subject, result=result, user_prompt=user_prompt)

    context_preview = ""
    if use_notes:
        if notes == "":
            context_preview = "\n\n[No notes found for this subject]"
        else:
            context_preview = "\n\n[NOTES CONTEXT PREVIEW]\n" + notes[:500]

    result = (
        "MOCK ATLAS RESPONSE\n"
        "-------------------\n"
        f"Prompt: {user_prompt}"
        f"{context_preview}\n\n"
        "(Next step: replace this mock response with a real AI API call.)"
    )

    return render_template("atlas_page.html",
                           subject=subject, result=result, user_prompt=user_prompt)
