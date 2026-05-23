"""Restaurant-owner routes for brand dashboards, replies, and branch editing."""

from datetime import datetime
from flask import Blueprint, jsonify, request, session
from sqlalchemy import func

from app.branding import canonical_brand_display_name, canonical_brand_expr, canonical_brand_key
from app.extensions import db
from app.models import (
    User,
    Restaurant,
    Review,
    ReviewReply,
    RestaurantBrandAccount,
)

restaurant_bp = Blueprint("restaurant", __name__, url_prefix="/restaurant")


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


def require_restaurant_user():
    user = current_user()
    if not user:
        return None, (jsonify({"error": "Authentication required"}), 401)
    if user.role != "restaurant":
        return None, (jsonify({"error": "Restaurant access only"}), 403)
    return user, None


def get_managed_brand(user_id):
    return RestaurantBrandAccount.query.filter_by(user_id=user_id).first()


def _restaurant_brand_expr():
    brand_expr = func.coalesce(func.nullif(Restaurant.brand_name, ""), Restaurant.name)
    return canonical_brand_expr(brand_expr)


def user_owns_restaurant_brand(user_id, restaurant_id):
    managed_brand_expr = canonical_brand_expr(RestaurantBrandAccount.brand_name)
    row = (
        db.session.query(RestaurantBrandAccount.id)
        .join(Restaurant, managed_brand_expr == _restaurant_brand_expr())
        .filter(
            RestaurantBrandAccount.user_id == user_id,
            Restaurant.restaurant_id == restaurant_id,
        )
        .first()
    )
    return row is not None


def _managed_restaurant(user_id, restaurant_id):
    managed_brand_expr = canonical_brand_expr(RestaurantBrandAccount.brand_name)
    row = (
        db.session.query(Restaurant)
        .join(RestaurantBrandAccount, managed_brand_expr == _restaurant_brand_expr())
        .filter(
            RestaurantBrandAccount.user_id == user_id,
            Restaurant.restaurant_id == restaurant_id,
        )
        .first()
    )
    return row


@restaurant_bp.get("/dashboard")
def restaurant_dashboard():
    user, error = require_restaurant_user()
    if error:
        return error

    managed_brand = get_managed_brand(user.user_id)
    if not managed_brand:
        return jsonify({"error": "No brand linked to this account"}), 404

    managed_brand_key = canonical_brand_key(managed_brand.brand_name)
    branches = (
        Restaurant.query
        .filter(_restaurant_brand_expr() == managed_brand_key)
        .order_by(Restaurant.name.asc(), Restaurant.postcode.asc())
        .all()
    )

    branch_ids = [b.restaurant_id for b in branches]

    published_reviews_count = 0
    avg_rating = None

    if branch_ids:
        published_reviews_count = (
            db.session.query(func.count(Review.review_id))
            .filter(
                Review.restaurant_id.in_(branch_ids),
                Review.status == "published"
            )
            .scalar()
        ) or 0

        avg_rating = (
            db.session.query(func.avg(Review.stars))
            .filter(
                Review.restaurant_id.in_(branch_ids),
                Review.status == "published"
            )
            .scalar()
        )

    return jsonify({
        "brand_name": canonical_brand_display_name(managed_brand.brand_name),
        "branch_count": len(branches),
        "published_reviews_count": int(published_reviews_count),
        "average_rating": round(float(avg_rating), 2) if avg_rating is not None else None,
        "branches": [
            {
                "restaurant_id": b.restaurant_id,
                "name": b.name,
                "address": getattr(b, "address", None),
                "description": getattr(b, "description", None),
                "city": getattr(b, "city", None),
                "postcode": getattr(b, "postcode", None),
                "price_level": getattr(b, "price_level", None),
                "fhrs_rating": getattr(b, "fhrs_rating", None),
                "menu_url": getattr(b, "menu_url", None),
                "menu_verified": getattr(b, "menu_verified", None),
                "website_url": getattr(b, "website_url", None),
                "ordering_url": getattr(b, "ordering_url", None),
                "phone": getattr(b, "phone", None),
                "email": getattr(b, "email", None),
            }
            for b in branches
        ]
    }), 200


@restaurant_bp.get("/reviews")
def restaurant_reviews():
    user, error = require_restaurant_user()
    if error:
        return error

    managed_brand = get_managed_brand(user.user_id)
    if not managed_brand:
        return jsonify({"error": "No brand linked to this account"}), 404

    managed_brand_key = canonical_brand_key(managed_brand.brand_name)
    rows = (
        db.session.query(Review, Restaurant, ReviewReply)
        .join(Restaurant, Restaurant.restaurant_id == Review.restaurant_id)
        .outerjoin(ReviewReply, ReviewReply.review_id == Review.review_id)
        .filter(
            _restaurant_brand_expr() == managed_brand_key,
            Review.status == "published"
        )
        .order_by(Review.created_at.desc())
        .all()
    )

    results = []
    for review, restaurant, reply in rows:
        results.append({
            "review_id": review.review_id,
            "restaurant_id": restaurant.restaurant_id,
            "branch_name": restaurant.name,
            "brand_name": restaurant.brand_name,
            "postcode": getattr(restaurant, "postcode", None),
            "stars": review.stars,
            "review_text": review.review_text,
            "status": review.status,
            "created_at": review.created_at.isoformat() if review.created_at else None,
            "reply": None if not reply else {
                "reply_id": reply.reply_id,
                "reply_text": reply.reply_text,
                "is_edited": reply.is_edited,
                "created_at": reply.created_at.isoformat() if reply.created_at else None,
                "updated_at": reply.updated_at.isoformat() if reply.updated_at else None,
            }
        })

    return jsonify({
        "brand_name": canonical_brand_display_name(managed_brand.brand_name),
        "count": len(results),
        "reviews": results
    }), 200


@restaurant_bp.post("/reviews/<int:review_id>/reply")
def create_review_reply(review_id):
    user, error = require_restaurant_user()
    if error:
        return error

    managed_brand = get_managed_brand(user.user_id)
    if not managed_brand:
        return jsonify({"error": "No brand linked to this account"}), 404

    data = request.get_json(silent=True) or {}
    reply_text = (data.get("reply_text") or "").strip()

    if not reply_text:
        return jsonify({"error": "reply_text is required"}), 400

    review = (
        db.session.query(Review, Restaurant)
        .join(Restaurant, Restaurant.restaurant_id == Review.restaurant_id)
        .filter(Review.review_id == review_id)
        .first()
    )

    if not review:
        return jsonify({"error": "Review not found"}), 404

    review_obj, restaurant = review

    if review_obj.status != "published":
        return jsonify({"error": "Only published reviews can be replied to"}), 400

    if canonical_brand_key(restaurant.brand_name or restaurant.name) != canonical_brand_key(managed_brand.brand_name):
        return jsonify({"error": "You do not manage this brand"}), 403

    existing_reply = ReviewReply.query.filter_by(review_id=review_obj.review_id).first()
    if existing_reply:
        return jsonify({"error": "This review already has a reply"}), 400

    new_reply = ReviewReply(
        review_id=review_obj.review_id,
        restaurant_id=restaurant.restaurant_id,
        user_id=user.user_id,
        reply_text=reply_text,
        is_edited=False,
        created_at=datetime.utcnow()
    )

    db.session.add(new_reply)
    db.session.commit()

    return jsonify({
        "message": "Reply created successfully",
        "reply": {
            "reply_id": new_reply.reply_id,
            "review_id": new_reply.review_id,
            "restaurant_id": new_reply.restaurant_id,
            "reply_text": new_reply.reply_text,
            "is_edited": new_reply.is_edited,
            "created_at": new_reply.created_at.isoformat() if new_reply.created_at else None,
        }
    }), 201


@restaurant_bp.put("/replies/<int:reply_id>")
def update_review_reply(reply_id):
    user, error = require_restaurant_user()
    if error:
        return error

    data = request.get_json(silent=True) or {}
    reply_text = (data.get("reply_text") or "").strip()

    if not reply_text:
        return jsonify({"error": "reply_text is required"}), 400

    reply_row = (
        db.session.query(ReviewReply, Restaurant)
        .join(Restaurant, Restaurant.restaurant_id == ReviewReply.restaurant_id)
        .filter(ReviewReply.reply_id == reply_id)
        .first()
    )

    if not reply_row:
        return jsonify({"error": "Reply not found"}), 404

    reply, restaurant = reply_row

    if not user_owns_restaurant_brand(user.user_id, restaurant.restaurant_id):
        return jsonify({"error": "You do not manage this brand"}), 403

    reply.reply_text = reply_text
    reply.is_edited = True
    reply.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        "message": "Reply updated successfully",
        "reply": {
            "reply_id": reply.reply_id,
            "review_id": reply.review_id,
            "restaurant_id": reply.restaurant_id,
            "reply_text": reply.reply_text,
            "is_edited": reply.is_edited,
            "created_at": reply.created_at.isoformat() if reply.created_at else None,
            "updated_at": reply.updated_at.isoformat() if reply.updated_at else None,
        }
    }), 200


@restaurant_bp.put("/branches/<int:restaurant_id>")
def update_branch_details(restaurant_id):
    user, error = require_restaurant_user()
    if error:
        return error

    restaurant = _managed_restaurant(user.user_id, restaurant_id)
    if not restaurant:
        return jsonify({"error": "Branch not found or not managed by this account"}), 404

    data = request.get_json(silent=True) or {}
    allowed_fields = {
        "description",
        "phone",
        "email",
        "website_url",
        "ordering_url",
        "menu_url",
        "price_level",
    }

    updates_applied = False
    price_enum = set(getattr(Restaurant.__table__.c.price_level.type, "enums", []) or [])

    for field in allowed_fields:
        if field not in data:
            continue

        value = data.get(field)
        if isinstance(value, str):
            value = value.strip() or None

        if field == "price_level" and value is not None and price_enum and value not in price_enum:
            return jsonify({"error": "Invalid price_level"}), 400

        setattr(restaurant, field, value)
        updates_applied = True

    if not updates_applied:
        return jsonify({"error": "No valid fields supplied"}), 400

    db.session.commit()

    return jsonify({
        "message": "Branch updated successfully",
        "branch": {
            "restaurant_id": restaurant.restaurant_id,
            "name": restaurant.name,
            "description": restaurant.description,
            "phone": restaurant.phone,
            "email": restaurant.email,
            "website_url": restaurant.website_url,
            "ordering_url": restaurant.ordering_url,
            "menu_url": restaurant.menu_url,
            "price_level": restaurant.price_level,
        }
    }), 200


