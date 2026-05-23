"""Authentication routes for registration, login, logout, and session checks."""

from flask import Blueprint, request, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db
from ..models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    data = request.get_json(force=True)
    email = data["email"].strip().lower()
    full_name = data.get("full_name", "").strip()
    password = data["password"]

    if not full_name:
        full_name = email.split("@")[0]

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "email exists"}), 400

    u = User(
        full_name=full_name,
        email=email,
        password_hash=generate_password_hash(password),
        role="customer",
        is_active=True
    )
    db.session.add(u)
    db.session.commit()

    return jsonify({"ok": True, "user_id": u.user_id})


@auth_bp.post("/login")
def login():
    data = request.get_json(force=True)
    email = data["email"].strip().lower()
    password = data["password"]

    u = User.query.filter_by(email=email, is_active=True).first()
    if not u or not check_password_hash(u.password_hash, password):
        return jsonify({"error": "invalid credentials"}), 401

    session["user_id"] = u.user_id
    session["role"] = u.role
    return jsonify({"ok": True, "user_id": u.user_id, "role": u.role})


@auth_bp.post("/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@auth_bp.get("/me")
def me():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "not_logged_in"}), 401

    u = User.query.get(user_id)
    if not u or not u.is_active:
        session.clear()
        return jsonify({"error": "not_logged_in"}), 401

    return jsonify({
        "user_id": u.user_id,
        "email": u.email,
        "full_name": u.full_name,
        "role": u.role
    })

