"""Administrator authentication and booking management."""

from datetime import timedelta
from functools import wraps

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.blueprints.forms import BookingForm, LoginForm
from app.catalog import get_place_type, get_unit
from app.catalog.types import Granularity
from app.models import Booking, BookingStatus
from app.services.booking_validation import save_booking

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def login_required(view):
    """Redirect anonymous users to the login form."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate the single administrator account from configuration."""
    form = LoginForm()
    if form.validate_on_submit():
        expected_user = current_app.config["ADMIN_USERNAME"]
        expected_pass = current_app.config["ADMIN_PASSWORD"]
        if (
            form.username.data == expected_user
            and form.password.data == expected_pass
        ):
            session["admin_logged_in"] = True
            next_url = request.args.get("next") or url_for("admin.bookings_list")
            return redirect(next_url)
        flash("Неверный логин или пароль.", "danger")
    return render_template("admin/login.html", form=form)


@admin_bp.post("/logout")
@login_required
def logout():
    """Clear the administrator session."""
    session.pop("admin_logged_in", None)
    return redirect(url_for("public.index"))


@admin_bp.get("/bookings")
@login_required
def bookings_list():
    """List bookings newest first."""
    bookings = Booking.query.order_by(Booking.starts_at.desc()).all()
    return render_template("admin/bookings_list.html", bookings=bookings)


def _prefill_form(form: BookingForm, booking: Booking | None = None) -> None:
    """Populate dynamic fields when editing an existing booking."""
    if booking is None:
        return
    form.unit_id.data = booking.unit_id
    form.status.data = booking.status.value
    form.note.data = booking.note
    unit = get_unit(booking.unit_id)
    place_type = get_place_type(unit.type_id)
    if place_type.granularity == Granularity.HOURLY:
        form.hourly_date.data = booking.starts_at.date()
        form.start_hour.data = booking.starts_at.hour
        hours = int((booking.ends_at - booking.starts_at).total_seconds() // 3600)
        form.duration_hours.data = hours
    elif place_type.granularity == Granularity.DAILY:
        form.daily_start.data = booking.starts_at.date()
        form.daily_end.data = booking.ends_at.date() - timedelta(days=1)
    else:
        form.monthly_year.data = booking.starts_at.year
        form.monthly_month.data = booking.starts_at.month


@admin_bp.route("/bookings/new", methods=["GET", "POST"])
@login_required
def booking_new():
    """Create a booking after phone confirmation."""
    form = BookingForm()
    if form.validate_on_submit():
        starts_at, ends_at, parse_error = form.resolve_interval()
        if parse_error:
            flash(parse_error, "danger")
        else:
            status = BookingStatus(form.status.data)
            booking, result = save_booking(
                form.unit_id.data,
                starts_at,
                ends_at,
                status,
                form.note.data,
            )
            if booking is None:
                for message in result.errors:
                    flash(message, "danger")
            else:
                flash("Бронь сохранена.", "success")
                return redirect(url_for("admin.bookings_list"))
    return render_template(
        "admin/booking_form.html",
        form=form,
        title="Новая бронь",
        granularity_hint=None,
    )


@admin_bp.route("/bookings/<int:booking_id>/edit", methods=["GET", "POST"])
@login_required
def booking_edit(booking_id: int):
    """Update status, note, or interval of an existing booking."""
    booking = Booking.query.get_or_404(booking_id)
    form = BookingForm(obj=booking)
    _prefill_form(form, booking)
    if form.validate_on_submit():
        starts_at, ends_at, parse_error = form.resolve_interval()
        if parse_error:
            flash(parse_error, "danger")
        else:
            status = BookingStatus(form.status.data)
            updated, result = save_booking(
                form.unit_id.data,
                starts_at,
                ends_at,
                status,
                form.note.data,
                booking_id=booking.id,
            )
            if updated is None:
                for message in result.errors:
                    flash(message, "danger")
            else:
                flash("Бронь обновлена.", "success")
                return redirect(url_for("admin.bookings_list"))
    return render_template(
        "admin/booking_form.html",
        form=form,
        title=f"Бронь #{booking.id}",
        granularity_hint=None,
    )
