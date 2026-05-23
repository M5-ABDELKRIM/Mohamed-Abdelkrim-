"""Public routes for page delivery, discovery, reviews, favourites, and map data."""

import os
from flask import Blueprint, request, session, jsonify, current_app, send_from_directory
from sqlalchemy import func, case
from flask import render_template

from ..branding import (
    canonical_brand_display_name as shared_canonical_brand_display_name,
    canonical_brand_expr as shared_canonical_brand_expr,
    canonical_brand_key as shared_canonical_brand_key,
    slugify_brand_name as shared_slugify_brand_name,
)
from ..extensions import db
from ..models import Restaurant, Review, ReviewReply, Flag, Favorite, User, Cuisine

public_bp = Blueprint("public", __name__)


def require_login():
    if not session.get("user_id"):
        return jsonify({"error": "login required"}), 401
    return None


def _frontend_dir():
    return os.path.join(current_app.root_path, "..", "frontend")


def _brand_logo_path(brand_name: str | None) -> str | None:
    slug = _slugify_brand_name(brand_name)
    if not slug:
        return None

    frontend_dir = _frontend_dir()
    for extension in ("svg", "png", "webp", "jpg", "jpeg", "ico"):
        filename = f"{slug}.{extension}"
        full_path = os.path.join(frontend_dir, "logos", filename)
        if os.path.exists(full_path):
            return f"/frontend/logos/{filename}"

    return None

def _slugify_brand_name(value: str | None) -> str:
    return shared_slugify_brand_name(value)


def _canonical_brand_key(value: str | None) -> str:
    return shared_canonical_brand_key(value)


def _canonical_brand_display_name(value: str | None) -> str:
    return shared_canonical_brand_display_name(value)


def _canonical_brand_expr():
    brand_expr = func.coalesce(func.nullif(Restaurant.brand_name, ""), Restaurant.name)
    return shared_canonical_brand_expr(brand_expr)


@public_bp.get("/")
def root():
    return send_from_directory(_frontend_dir(), "login.html")


@public_bp.get("/login")
def login_page():
    return send_from_directory(_frontend_dir(), "login.html")


@public_bp.get("/discovery")
def discovery_page():
    return send_from_directory(_frontend_dir(), "discovery.html")


@public_bp.get("/profile")
def profile_page():
    return send_from_directory(_frontend_dir(), "profile.html")


@public_bp.get("/map")
def map_page():
    return send_from_directory(_frontend_dir(), "map.html")


@public_bp.get("/admin-queue")
def admin_queue_page():
    return send_from_directory(_frontend_dir(), "admin_queue.html")


@public_bp.get("/admin/admin-queue")
def admin_queue_page_alias():
    return send_from_directory(_frontend_dir(), "admin_queue.html")


@public_bp.get("/frontend/<path:filename>")
def frontend_static(filename):
    return send_from_directory(_frontend_dir(), filename)


@public_bp.get("/cuisines")
def cuisines():
    rows = (
        db.session.query(Cuisine.cuisine_id, Cuisine.name)
        .join(Restaurant, Restaurant.cuisine_id == Cuisine.cuisine_id)
        .filter(Restaurant.cuisine_id.isnot(None))
        .group_by(Cuisine.cuisine_id, Cuisine.name)
        .order_by(Cuisine.name.asc())
        .all()
    )

    return jsonify({
        "items": [
            {"cuisine_id": cuisine_id, "name": name}
            for cuisine_id, name in rows
        ]
    })

@public_bp.get("/restaurants")
def restaurants():
    """
    /restaurants?q=...&page=1&per_page=30&sort=name_asc&has_menu=0
    returns grouped brands instead of raw branch rows
    """
    q = (request.args.get("q") or "").strip()
    page = int(request.args.get("page", 1))
    per_page = min(int(request.args.get("per_page", 30)), 100)

    sort = (request.args.get("sort") or "name_asc").strip()
    has_menu = (request.args.get("has_menu") or "").strip()
    cuisine_id = (request.args.get("cuisine_id") or "").strip()

    brand_expr = func.coalesce(func.nullif(Restaurant.brand_name, ""), Restaurant.name)
    normalized_brand_expr = _canonical_brand_expr()
    display_name_expr = func.coalesce(func.min(func.nullif(Restaurant.brand_name, "")), func.min(Restaurant.name))
    cuisine_id_expr = func.max(Restaurant.cuisine_id)
    cuisine_name_expr = func.max(Cuisine.name)

    branch_count_expr = func.count(func.distinct(Restaurant.restaurant_id))

    avg_rating_expr = func.avg(
        case(
            (Review.status == "published", Review.stars),
            else_=None
        )
    )

    review_count_expr = func.count(
        func.distinct(
            case(
                (Review.status == "published", Review.review_id),
                else_=None
            )
        )
    )

    has_menu_expr = func.max(
        case(
            (Restaurant.menu_url.isnot(None), 1),
            else_=0
        )
    )

    query = (
        db.session.query(
            func.min(Restaurant.restaurant_id).label("restaurant_id"),
            display_name_expr.label("display_name"),
            branch_count_expr.label("branch_count"),
            func.max(Restaurant.city).label("city"),
            func.max(Restaurant.postcode).label("postcode"),
            func.max(Restaurant.hygiene_rating).label("hygiene_rating"),
            func.max(Restaurant.menu_url).label("menu_url"),
            func.max(Restaurant.menu_source_type).label("menu_source_type"),
            cuisine_id_expr.label("cuisine_id"),
            cuisine_name_expr.label("cuisine_name"),
            has_menu_expr.label("has_menu"),
            avg_rating_expr.label("avg_rating"),
            review_count_expr.label("review_count"),
        )
        .outerjoin(Review, Review.restaurant_id == Restaurant.restaurant_id)
        .outerjoin(Cuisine, Cuisine.cuisine_id == Restaurant.cuisine_id)
    )

    if has_menu == "1":
        query = query.filter(
            Restaurant.menu_url.isnot(None),
            Restaurant.menu_verified == True
        )

    if q:
        like = f"%{q}%"
        query = query.filter(brand_expr.ilike(like))

    if cuisine_id.isdigit():
        query = query.filter(Restaurant.cuisine_id == int(cuisine_id))

    query = query.group_by(normalized_brand_expr)

    if sort == "rating_desc":
        query = query.order_by(avg_rating_expr.desc(), display_name_expr.asc())
    elif sort == "fhrs_desc":
        query = query.order_by(func.max(Restaurant.hygiene_rating).desc(), display_name_expr.asc())
    else:
        query = query.order_by(display_name_expr.asc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    items = []
    for row in pagination.items:
        display_name = _canonical_brand_display_name(row.display_name)
        items.append({
            "restaurant_id": row.restaurant_id,
            "name": display_name,
            "brand_name": display_name,
            "logo_url": _brand_logo_path(display_name),
            "branch_count": int(row.branch_count or 0),
            "address_line1": None,
            "city": row.city,
            "postcode": row.postcode,
            "hygiene_rating": row.hygiene_rating,
            "menu_url": row.menu_url,
            "menu_source_type": row.menu_source_type,
            "cuisine_id": row.cuisine_id,
            "cuisine_name": row.cuisine_name,
            "has_menu": bool(row.has_menu),
            "avg_rating": float(row.avg_rating) if row.avg_rating is not None else None,
            "review_count": int(row.review_count or 0),
        })

    return jsonify({
        "items": items,
        "page": pagination.page,
        "pages": pagination.pages,
        "total": pagination.total
    })

@public_bp.get("/restaurants/featured")
def featured_restaurants():
    normalized_brand_expr = _canonical_brand_expr()
    display_name_expr = func.coalesce(func.min(func.nullif(Restaurant.brand_name, "")), func.min(Restaurant.name))
    branch_count_expr = func.count(func.distinct(Restaurant.restaurant_id))
    avg_rating_expr = func.avg(
        case(
            (Review.status == "published", Review.stars),
            else_=None
        )
    )
    review_count_expr = func.count(
        func.distinct(
            case(
                (Review.status == "published", Review.review_id),
                else_=None
            )
        )
    )

    rows = (
        db.session.query(
            display_name_expr.label("display_name"),
            func.min(Restaurant.restaurant_id).label("restaurant_id"),
            branch_count_expr.label("branch_count"),
            func.max(Restaurant.city).label("city"),
            func.max(Restaurant.postcode).label("postcode"),
            func.max(Restaurant.hygiene_rating).label("hygiene_rating"),
            func.max(Cuisine.name).label("cuisine_name"),
            avg_rating_expr.label("avg_rating"),
            review_count_expr.label("review_count"),
        )
        .outerjoin(Review, Review.restaurant_id == Restaurant.restaurant_id)
        .outerjoin(Cuisine, Cuisine.cuisine_id == Restaurant.cuisine_id)
        .filter(
            Restaurant.menu_url.isnot(None),
            Restaurant.menu_verified == True,
        )
        .group_by(normalized_brand_expr)
        .having(avg_rating_expr.isnot(None))
        .order_by(avg_rating_expr.desc(), review_count_expr.desc(), display_name_expr.asc())
        .limit(6)
        .all()
    )

    items = []
    for row in rows:
        display_name = _canonical_brand_display_name(row.display_name)

        review_rows = (
            db.session.query(
                Review.review_id,
                Review.stars,
                Review.review_text,
                Review.created_at,
                User.full_name,
                ReviewReply.reply_id,
                ReviewReply.reply_text,
                ReviewReply.is_edited,
                ReviewReply.created_at,
                ReviewReply.updated_at,
            )
            .join(Restaurant, Restaurant.restaurant_id == Review.restaurant_id)
            .join(User, User.user_id == Review.user_id)
            .outerjoin(ReviewReply, ReviewReply.review_id == Review.review_id)
            .filter(
                _canonical_brand_expr() == _canonical_brand_key(display_name),
                Review.status == "published",
            )
            .order_by(Review.created_at.desc())
            .limit(2)
            .all()
        )

        reviews = []
        for review_id, stars, review_text, created_at, full_name, reply_id, reply_text, reply_is_edited, reply_created_at, reply_updated_at in review_rows:
            reviews.append({
                "review_id": review_id,
                "stars": stars,
                "review_text": review_text,
                "created_at": created_at.isoformat() if created_at else None,
                "user_full_name": full_name,
                "reply": None if not reply_id else {
                    "reply_id": reply_id,
                    "reply_text": reply_text,
                    "is_edited": reply_is_edited,
                    "created_at": reply_created_at.isoformat() if reply_created_at else None,
                    "updated_at": reply_updated_at.isoformat() if reply_updated_at else None,
                },
            })

        items.append({
            "restaurant_id": row.restaurant_id,
            "name": display_name,
            "brand_name": display_name,
            "logo_url": _brand_logo_path(display_name),
            "branch_count": int(row.branch_count or 0),
            "city": row.city,
            "postcode": row.postcode,
            "hygiene_rating": row.hygiene_rating,
            "cuisine_name": row.cuisine_name,
            "avg_rating": float(row.avg_rating) if row.avg_rating is not None else None,
            "review_count": int(row.review_count or 0),
            "reviews": reviews,
        })

    return jsonify({"items": items})

@public_bp.get("/restaurants/<int:restaurant_id>")
def restaurant_detail(restaurant_id: int):
    r = db.session.get(Restaurant, restaurant_id)
    if not r:
        return jsonify({"error": "Restaurant not found"}), 404

    review_count, avg_rating = (
        db.session.query(
            func.count(Review.review_id),
            func.avg(Review.stars)
        )
        .filter(
            Review.restaurant_id == restaurant_id,
            Review.status == "published"
        )
        .one()
    )

    review_count = int(review_count or 0)
    avg_rating = float(avg_rating) if avg_rating is not None else None

    rows = (
        db.session.query(
            Review.review_id,
            Review.stars,
            Review.review_text,
            Review.created_at,
            User.full_name,
            ReviewReply.reply_id,
            ReviewReply.reply_text,
            ReviewReply.is_edited,
            ReviewReply.created_at,
            ReviewReply.updated_at,
        )
        .join(User, User.user_id == Review.user_id)
        .outerjoin(ReviewReply, ReviewReply.review_id == Review.review_id)
        .filter(
            Review.restaurant_id == restaurant_id,
            Review.status == "published"
        )
        .order_by(Review.created_at.desc())
        .limit(100)
        .all()
    )

    reviews = []
    for review_id, stars, review_text, created_at, full_name, reply_id, reply_text, reply_is_edited, reply_created_at, reply_updated_at in rows:
        reviews.append({
            "review_id": review_id,
            "stars": stars,
            "review_text": review_text,
            "created_at": created_at.isoformat() if created_at else None,
            "user_full_name": full_name,
            "reply": None if not reply_id else {
                "reply_id": reply_id,
                "reply_text": reply_text,
                "is_edited": reply_is_edited,
                "created_at": reply_created_at.isoformat() if reply_created_at else None,
                "updated_at": reply_updated_at.isoformat() if reply_updated_at else None,
            },
        })

    is_favorited = False
    if session.get("user_id"):
        is_favorited = (
            Favorite.query.filter_by(
                user_id=session["user_id"],
                restaurant_id=restaurant_id
            ).first()
            is not None
        )

    return jsonify({
        "restaurant": {
            "restaurant_id": r.restaurant_id,
            "name": r.name,
            "description": r.description,
            "address_line1": r.address_line1,
            "city": r.city,
            "postcode": r.postcode,
            "phone": r.phone,
            "email": r.email,
            "website_url": r.website_url,
            "ordering_url": r.ordering_url,
            "price_level": r.price_level,
            "hygiene_rating": r.hygiene_rating,
            "menu_url": r.menu_url,
            "menu_source_type": r.menu_source_type,
            "menu_verified": r.menu_verified,
        },
        "rating": {
            "review_count": review_count,
            "avg": avg_rating,
        },
        "reviews": reviews,
        "is_favorited": is_favorited,
    })

@public_bp.get("/restaurant-groups/<path:brand_name>")
def restaurant_group_detail(brand_name):
    brand_name = (brand_name or "").strip()
    if not brand_name:
        return jsonify({"error": "Brand name required"}), 400

    requested_brand_key = _canonical_brand_key(brand_name)
    normalized_brand_expr = _canonical_brand_expr()

    rows = (
        Restaurant.query
        .filter(normalized_brand_expr == requested_brand_key)
        .order_by(Restaurant.name.asc(), Restaurant.city.asc(), Restaurant.postcode.asc())
        .all()
    )

    if not rows:
        return jsonify({"error": "Restaurant group not found"}), 404

    branches = []
    for r in rows:
        review_count, avg_rating = (
            db.session.query(
                func.count(Review.review_id),
                func.avg(Review.stars)
            )
            .filter(
                Review.restaurant_id == r.restaurant_id,
                Review.status == "published"
            )
            .one()
        )

        review_rows = (
            db.session.query(
                Review.review_id,
                Review.stars,
                Review.review_text,
                Review.created_at,
                User.full_name,
                ReviewReply.reply_id,
                ReviewReply.reply_text,
                ReviewReply.is_edited,
                ReviewReply.created_at,
                ReviewReply.updated_at,
            )
            .join(User, User.user_id == Review.user_id)
            .outerjoin(ReviewReply, ReviewReply.review_id == Review.review_id)
            .filter(
                Review.restaurant_id == r.restaurant_id,
                Review.status == "published",
            )
            .order_by(Review.created_at.desc())
            .limit(3)
            .all()
        )

        reviews = []
        for review_id, stars, review_text, created_at, full_name, reply_id, reply_text, reply_is_edited, reply_created_at, reply_updated_at in review_rows:
            reviews.append({
                "review_id": review_id,
                "stars": stars,
                "review_text": review_text,
                "created_at": created_at.isoformat() if created_at else None,
                "user_full_name": full_name,
                "reply": None if not reply_id else {
                    "reply_id": reply_id,
                    "reply_text": reply_text,
                    "is_edited": reply_is_edited,
                    "created_at": reply_created_at.isoformat() if reply_created_at else None,
                    "updated_at": reply_updated_at.isoformat() if reply_updated_at else None,
                },
            })

        branches.append({
            "restaurant_id": r.restaurant_id,
            "name": r.name,
            "brand_name": r.brand_name,
            "description": r.description,
            "address_line1": r.address_line1,
            "city": r.city,
            "postcode": r.postcode,
            "phone": r.phone,
            "email": r.email,
            "website_url": r.website_url,
            "ordering_url": r.ordering_url,
            "price_level": r.price_level,
            "hygiene_rating": r.hygiene_rating,
            "menu_url": r.menu_url,
            "menu_source_type": r.menu_source_type,
            "menu_verified": r.menu_verified,
            "rating": {
                "review_count": int(review_count or 0),
                "avg": float(avg_rating) if avg_rating is not None else None
            },
            "reviews": reviews,
        })

    display_brand_name = None
    for restaurant in rows:
        if restaurant.brand_name:
            display_brand_name = _canonical_brand_display_name(restaurant.brand_name)
            break
    if not display_brand_name:
        display_brand_name = _canonical_brand_display_name(rows[0].name)

    return jsonify({
        "brand_name": display_brand_name,
        "logo_url": _brand_logo_path(display_brand_name),
        "branch_count": len(branches),
        "branches": branches
    })

@public_bp.post("/restaurants/<int:restaurant_id>/reviews")
def create_review(restaurant_id):
    err = require_login()
    if err:
        return err

    r = db.session.get(Restaurant, restaurant_id)
    if not r:
        return jsonify({"error": "Restaurant not found"}), 404

    data = request.get_json(force=True)
    stars = int(data.get("stars", 0))
    review_text = (data.get("review_text") or "").strip()

    if stars < 1 or stars > 5:
        return jsonify({"error": "stars must be 1-5"}), 400

    if len(review_text) < 3:
        return jsonify({"error": "review_text too short"}), 400

    rv = Review(
        restaurant_id=restaurant_id,
        user_id=session["user_id"],
        stars=stars,
        review_text=review_text,
        status="pending",
    )
    db.session.add(rv)
    db.session.commit()

    return jsonify({"ok": True, "review_id": rv.review_id, "status": rv.status})

@public_bp.get("/me/reviews")
def my_reviews():
    err = require_login()
    if err:
        return err

    user_id = session["user_id"]

    rows = (
        db.session.query(Review, Restaurant)
        .join(Restaurant, Restaurant.restaurant_id == Review.restaurant_id)
        .filter(Review.user_id == user_id)
        .order_by(Review.created_at.desc())
        .limit(200)
        .all()
    )

    items = []
    for rv, r in rows:
        items.append({
            "review_id": rv.review_id,
            "restaurant_id": rv.restaurant_id,
            "restaurant_name": r.name,
            "stars": rv.stars,
            "review_text": rv.review_text,
            "status": rv.status,
            "created_at": rv.created_at.isoformat() if rv.created_at else None
        })

    return jsonify({"items": items})

@public_bp.post("/reviews/<int:review_id>/flags")
def flag_review(review_id):
    err = require_login()
    if err:
        return err

    if not db.session.get(Review, review_id):
        return jsonify({"error": "Review not found"}), 404

    data = request.get_json(force=True)
    reason = (data.get("reason") or "").strip()
    details = data.get("details")

    if not reason:
        return jsonify({"error": "reason required"}), 400

    fl = Flag(
        review_id=review_id,
        reporter_id=session["user_id"],
        reason=reason,
        details=details,
        status="open"
    )
    db.session.add(fl)
    db.session.commit()

    return jsonify({"ok": True, "flag_id": fl.flag_id})

@public_bp.get("/me/favorites")
def my_favorites():
    err = require_login()
    if err:
        return err

    user_id = session["user_id"]

    favs = (
        db.session.query(Favorite, Restaurant)
        .join(Restaurant, Restaurant.restaurant_id == Favorite.restaurant_id)
        .filter(Favorite.user_id == user_id)
        .order_by(Favorite.created_at.desc())
        .limit(500)
        .all()
    )

    items = []
    for fav, r in favs:
        items.append({
            "restaurant_id": r.restaurant_id,
            "name": r.name,
            "address_line1": r.address_line1,
            "city": r.city,
            "postcode": r.postcode,
            "hygiene_rating": r.hygiene_rating,
            "favorited_at": fav.created_at.isoformat() if fav.created_at else None
        })

    return jsonify({"items": items})

@public_bp.post("/restaurants/<int:restaurant_id>/favorite")
def toggle_favorite(restaurant_id):
    err = require_login()
    if err:
        return err

    r = db.session.get(Restaurant, restaurant_id)
    if not r:
        return jsonify({"error": "Restaurant not found"}), 404

    user_id = session["user_id"]

    existing = Favorite.query.filter_by(
        user_id=user_id,
        restaurant_id=restaurant_id
    ).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({"favorited": False})

    fav = Favorite(user_id=user_id, restaurant_id=restaurant_id)
    db.session.add(fav)
    db.session.commit()
    return jsonify({"favorited": True})

@public_bp.get("/map-restaurants")
def map_restaurants():
    avg_rating_expr = func.avg(
        case(
            (Review.status == "published", Review.stars),
            else_=None
        )
    )
    review_count_expr = func.count(
        func.distinct(
            case(
                (Review.status == "published", Review.review_id),
                else_=None
            )
        )
    )

    rows = (
        db.session.query(
            Restaurant.restaurant_id,
            Restaurant.name,
            Restaurant.brand_name,
            Restaurant.address_line1,
            Restaurant.city,
            Restaurant.postcode,
            Restaurant.hygiene_rating,
            Restaurant.menu_url,
            Restaurant.website_url,
            Restaurant.ordering_url,
            Restaurant.latitude,
            Restaurant.longitude,
            Cuisine.name.label("cuisine_name"),
            avg_rating_expr.label("avg_rating"),
            review_count_expr.label("review_count"),
        )
        .outerjoin(Review, Review.restaurant_id == Restaurant.restaurant_id)
        .outerjoin(Cuisine, Cuisine.cuisine_id == Restaurant.cuisine_id)
        .filter(
            Restaurant.menu_verified == True,
            Restaurant.menu_url.isnot(None),
            Restaurant.latitude.isnot(None),
            Restaurant.longitude.isnot(None),
        )
        .group_by(
            Restaurant.restaurant_id,
            Restaurant.name,
            Restaurant.brand_name,
            Restaurant.address_line1,
            Restaurant.city,
            Restaurant.postcode,
            Restaurant.hygiene_rating,
            Restaurant.menu_url,
            Restaurant.website_url,
            Restaurant.ordering_url,
            Restaurant.latitude,
            Restaurant.longitude,
            Cuisine.name,
        )
        .order_by(Restaurant.name.asc(), Restaurant.postcode.asc())
        .all()
    )

    items = []
    for row in rows:
        display_name = _canonical_brand_display_name(row.brand_name or row.name)
        items.append({
            "restaurant_id": row.restaurant_id,
            "name": row.name,
            "brand_name": display_name,
            "logo_url": _brand_logo_path(display_name),
            "address_line1": row.address_line1,
            "city": row.city,
            "postcode": row.postcode,
            "hygiene_rating": row.hygiene_rating,
            "menu_url": row.menu_url,
            "website_url": row.website_url,
            "ordering_url": row.ordering_url,
            "cuisine_name": row.cuisine_name,
            "latitude": float(row.latitude) if row.latitude is not None else None,
            "longitude": float(row.longitude) if row.longitude is not None else None,
            "avg_rating": float(row.avg_rating) if row.avg_rating is not None else None,
            "review_count": int(row.review_count or 0),
        })

    return jsonify({"items": items})

@public_bp.get("/restaurant-portal")
def restaurant_portal_page():
    return render_template("restaurant_dashboard.html")

