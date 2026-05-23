"""SQLAlchemy models describing the main entities in the IRDb platform."""

from .extensions import db
from sqlalchemy.sql import func
from datetime import datetime


class User(db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("customer", "restaurant", "admin"), nullable=False, default="customer")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())


class Area(db.Model):
    __tablename__ = "areas"
    area_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)


class Cuisine(db.Model):
    __tablename__ = "cuisines"
    cuisine_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)


class Restaurant(db.Model):
    __tablename__ = "restaurants"
    restaurant_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)

    area_id = db.Column(db.Integer, db.ForeignKey("areas.area_id"), nullable=True)
    cuisine_id = db.Column(db.Integer, db.ForeignKey("cuisines.cuisine_id"), nullable=True)

    price_level = db.Column(db.Enum("Â£", "Â£Â£", "Â£Â£Â£"), nullable=True)
    address_line1 = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    postcode = db.Column(db.String(20), nullable=True)
    latitude = db.Column(db.Numeric(10, 7), nullable=True)
    longitude = db.Column(db.Numeric(10, 7), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    website_url = db.Column(db.String(255), nullable=True)
    ordering_url = db.Column(db.String(255), nullable=True)
    hygiene_rating = db.Column(db.SmallInteger, nullable=True)
    menu_url = db.Column(db.String(500), nullable=True)
    menu_source_type = db.Column(db.Enum("page", "pdf"), nullable=True)
    menu_verified = db.Column(db.Boolean, nullable=False, default=False)

    created_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    brand_name = db.Column(db.String(150), nullable=True)


class RestaurantHours(db.Model):
    __tablename__ = "restaurant_hours"
    hours_id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.restaurant_id"), nullable=False)
    day_of_week = db.Column(db.Enum("Mon","Tue","Wed","Thu","Fri","Sat","Sun"), nullable=False)
    open_time = db.Column(db.Time, nullable=True)
    close_time = db.Column(db.Time, nullable=True)
    is_closed = db.Column(db.Boolean, nullable=False, default=False)


class Review(db.Model):
    __tablename__ = "reviews"
    review_id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.restaurant_id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)

    stars = db.Column(db.SmallInteger, nullable=False)
    review_text = db.Column(db.Text, nullable=False)

    status = db.Column(db.Enum("pending","published","rejected","needs_edit"),
                       nullable=False, default="pending")
    admin_note = db.Column(db.String(255), nullable=True)
    moderated_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    moderated_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    updated_at = db.Column(db.DateTime, nullable=True)


class Flag(db.Model):
    __tablename__ = "flags"
    flag_id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey("reviews.review_id"), nullable=False)
    reporter_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)

    reason = db.Column(db.String(255), nullable=False)
    details = db.Column(db.Text, nullable=True)

    status = db.Column(db.Enum("open","resolved"), nullable=False, default="open")
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    resolved_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)


class Favorite(db.Model):
    __tablename__ = "favorites"
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.restaurant_id"), primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())


class Photo(db.Model):
    __tablename__ = "photos"
    photo_id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.restaurant_id"), nullable=False)
    photo_url = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.String(140), nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())


class AdminAuditLog(db.Model):
    __tablename__ = "admin_audit_log"
    audit_id = db.Column(db.Integer, primary_key=True)
    admin_user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    action = db.Column(db.String(60), nullable=False)
    target_type = db.Column(db.String(40), nullable=False)
    target_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())


class RestaurantBrandAccount(db.Model):
    __tablename__ = "restaurant_brand_accounts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    brand_name = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "brand_name", name="uq_brand_account"),
    )


class ReviewReply(db.Model):
    __tablename__ = "review_replies"

    reply_id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(
        db.Integer,
        db.ForeignKey("reviews.review_id", ondelete="CASCADE"),
        nullable=False
    )
    restaurant_id = db.Column(
        db.Integer,
        db.ForeignKey("restaurants.restaurant_id", ondelete="CASCADE"),
        nullable=False
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    reply_text = db.Column(db.Text, nullable=False)
    is_edited = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True)

