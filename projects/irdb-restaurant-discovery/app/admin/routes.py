"""Admin moderation routes for review and flag workflows."""

from datetime import datetime
import json
from flask import Blueprint, request, session, jsonify
from ..extensions import db
from ..models import Flag, Review, Restaurant, User, AdminAuditLog

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required():
    return session.get("role") == "admin" and bool(session.get("user_id"))


@admin_bp.get("/flags")
def queue():
    if not admin_required():
        return jsonify({"error": "admin required"}), 403

    rows = (
        db.session.query(Flag, Review, Restaurant, User)
        .join(Review, Flag.review_id == Review.review_id)
        .join(Restaurant, Review.restaurant_id == Restaurant.restaurant_id)
        .join(User, Flag.reporter_id == User.user_id)
        .filter(Flag.status == "open")
        .order_by(Flag.created_at.asc())
        .limit(200)
        .all()
    )

    out = []
    for fl, rv, rest, reporter in rows:
        out.append({
            "flag_id": fl.flag_id,
            "reason": fl.reason,
            "details": fl.details,
            "flag_created_at": fl.created_at.isoformat() if fl.created_at else None,
            "review": {
                "review_id": rv.review_id,
                "status": rv.status,
                "stars": rv.stars,
                "review_text": rv.review_text,
                "created_at": rv.created_at.isoformat() if rv.created_at else None,
            },
            "restaurant": {"restaurant_id": rest.restaurant_id, "name": rest.name},
            "reporter": {"user_id": reporter.user_id, "email": reporter.email},
        })
    return jsonify({"items": out})


@admin_bp.post("/flags/<int:flag_id>/resolve")
def resolve(flag_id):
    if not admin_required():
        return jsonify({"error": "admin required"}), 403

    data = request.get_json(force=True)
    decision = data.get("decision")
    admin_note = data.get("admin_note")
    resolve_flag = bool(data.get("resolve_flag", True))

    fl = Flag.query.get_or_404(flag_id)
    rv = Review.query.get_or_404(fl.review_id)

    before = {
        "flag": {"flag_id": fl.flag_id, "status": fl.status},
        "review": {"review_id": rv.review_id, "status": rv.status, "admin_note": rv.admin_note},
    }

    if decision not in ("publish", "reject", "needs_edit"):
        return jsonify({"error": "decision must be publish|reject|needs_edit"}), 400

    if decision == "publish":
        rv.status = "published"
        action = "REVIEW_PUBLISHED"
    elif decision == "reject":
        rv.status = "rejected"
        action = "REVIEW_REJECTED"
    else:
        rv.status = "needs_edit"
        action = "REVIEW_NEEDS_EDIT"

    rv.admin_note = admin_note
    rv.moderated_by = session["user_id"]
    rv.moderated_at = datetime.utcnow()

    if resolve_flag:
        fl.status = "resolved"
        fl.resolved_by = session["user_id"]
        fl.resolved_at = datetime.utcnow()

    after = {
        "flag": {"flag_id": fl.flag_id, "status": fl.status, "resolved_by": fl.resolved_by},
        "review": {"review_id": rv.review_id, "status": rv.status, "admin_note": rv.admin_note},
    }

    log = AdminAuditLog(
        admin_user_id=session["user_id"],
        action=action,
        target_type="review",
        target_id=rv.review_id,
        details=json.dumps({"before": before, "after": after})
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({"ok": True, "review_id": rv.review_id, "new_status": rv.status, "flag_status": fl.status})


@admin_bp.get("/pending-reviews")
def pending_reviews():
    if not admin_required():
        return jsonify({"error": "admin required"}), 403

    rows = (
        db.session.query(Review, Restaurant, User)
        .join(Restaurant, Restaurant.restaurant_id == Review.restaurant_id)
        .join(User, User.user_id == Review.user_id)
        .filter(Review.status == "pending")
        .order_by(Review.created_at.asc())
        .limit(300)
        .all()
    )

    items = []
    for rv, rest, user in rows:
        items.append({
            "review_id": rv.review_id,
            "restaurant_id": rest.restaurant_id,
            "restaurant_name": rest.name,
            "user_id": user.user_id,
            "user_email": user.email,
            "stars": rv.stars,
            "review_text": rv.review_text,
            "status": rv.status,
            "created_at": rv.created_at.isoformat() if rv.created_at else None,
        })

    return jsonify({"items": items})


@admin_bp.post("/reviews/<int:review_id>/moderate")
def moderate_review(review_id):
    if not admin_required():
        return jsonify({"error": "admin required"}), 403

    data = request.get_json(force=True)
    decision = (data.get("decision") or "").strip()
    admin_note = (data.get("admin_note") or "").strip()

    if decision not in ("publish", "reject", "needs_edit"):
        return jsonify({"error": "decision must be publish|reject|needs_edit"}), 400

    rv = Review.query.get_or_404(review_id)

    before = {"review_id": rv.review_id, "status": rv.status, "admin_note": rv.admin_note}

    if decision == "publish":
        rv.status = "published"
        action = "REVIEW_PUBLISHED"
    elif decision == "reject":
        rv.status = "rejected"
        action = "REVIEW_REJECTED"
    else:
        rv.status = "needs_edit"
        action = "REVIEW_NEEDS_EDIT"

    rv.admin_note = admin_note or None
    rv.moderated_by = session["user_id"]
    rv.moderated_at = datetime.utcnow()

    after = {"review_id": rv.review_id, "status": rv.status, "admin_note": rv.admin_note}

    db.session.add(AdminAuditLog(
        admin_user_id=session["user_id"],
        action=action,
        target_type="review",
        target_id=rv.review_id,
        details=json.dumps({"before": before, "after": after})
    ))

    db.session.commit()

    return jsonify({"ok": True, "review_id": rv.review_id, "new_status": rv.status})

