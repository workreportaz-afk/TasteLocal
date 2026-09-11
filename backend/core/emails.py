"""
Transactional emails for the booking flow (issue: no email was ever sent to
tourist or vendor at any point in the booking lifecycle).

In dev (DEBUG=True and no EMAIL_HOST configured), Django's console backend
is used -- emails are printed to the `docker compose logs backend` output
instead of actually being sent, so you can see and test this without
setting up a real mailbox. Set EMAIL_HOST/EMAIL_HOST_USER/EMAIL_HOST_PASSWORD
in your .env (see .env.example) to send real emails, e.g. with a free
Gmail "app password" or a free Mailtrap sandbox inbox.

All sends are wrapped in try/except and logged rather than raised, so a
misconfigured or briefly-down mail server never breaks a booking request
or a vendor's confirm/cancel action.
"""
import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def _send(subject, message, to_email):
    if not to_email:
        return
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=False,
        )
    except Exception:
        # Don't let a broken mail server 500 a booking request.
        logger.exception("Failed to send email %r to %s", subject, to_email)


def send_booking_created_emails(booking):
    """Fires once, right after a tourist submits a booking request."""
    experience = booking.experience
    vendor_user = experience.vendor.user

    _send(
        subject=f"Booking request received - {experience.title}",
        message=(
            f"Hi {booking.tourist.username},\n\n"
            f"We've received your booking request for \"{experience.title}\" "
            f"on {booking.booking_date:%d %b %Y, %I:%M %p} "
            f"for {booking.number_of_participants} participant(s).\n"
            f"Total: ${booking.total_price}\n\n"
            f"Status: Pending -- the vendor still needs to confirm this booking. "
            f"You'll get another email as soon as they do.\n\n"
            f"- TasteLocal"
        ),
        to_email=booking.tourist.email,
    )

    _send(
        subject=f"New booking request - {experience.title}",
        message=(
            f"Hi {vendor_user.username},\n\n"
            f"{booking.tourist.username} has requested to book \"{experience.title}\" "
            f"on {booking.booking_date:%d %b %Y, %I:%M %p} "
            f"for {booking.number_of_participants} participant(s).\n\n"
            f"Please log in to your Vendor Dashboard to confirm or decline this booking.\n\n"
            f"- TasteLocal"
        ),
        to_email=vendor_user.email,
    )


def send_booking_status_email(booking):
    """Fires when a vendor confirms, cancels, or completes a booking."""
    experience = booking.experience
    status_text = {
        "confirmed": "confirmed",
        "cancelled": "cancelled",
        "completed": "marked as completed",
    }.get(booking.status)
    if not status_text:
        return

    _send(
        subject=f"Booking {status_text} - {experience.title}",
        message=(
            f"Hi {booking.tourist.username},\n\n"
            f"Your booking for \"{experience.title}\" on "
            f"{booking.booking_date:%d %b %Y, %I:%M %p} has been {status_text} "
            f"by {experience.vendor.business_name}.\n\n"
            f"- TasteLocal"
        ),
        to_email=booking.tourist.email,
    )
