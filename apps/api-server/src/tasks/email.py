"""
Email Tasks

Background tasks for sending emails via SMTP.
Falls back to logging when SMTP is not configured.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from src.celery_app import celery_app
from src.config import config

logger = logging.getLogger(__name__)


def _is_smtp_configured() -> bool:
    """Check whether SMTP credentials are present in config."""
    return config.smtp.is_configured()


def _send_smtp_email(
    to_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None,
) -> bool:
    """
    Low-level SMTP send helper.

    Args:
        to_email: Recipient email address.
        subject: Email subject line.
        body: Plain-text body.
        html_body: Optional HTML body. When provided the email is sent as
            multipart/alternative with both text and HTML parts.

    Returns:
        True if the message was accepted by the SMTP server, False otherwise.
    """
    smtp_cfg = config.smtp

    if not _is_smtp_configured():
        logger.warning(
            "SMTP not configured – logging email instead of sending. "
            "Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_EMAIL."
        )
        logger.info(f"[EMAIL-FALLBACK] To: {to_email} | Subject: {subject}")
        logger.info(f"[EMAIL-FALLBACK] Body: {body[:200]}...")
        if html_body:
            logger.info(f"[EMAIL-FALLBACK] HTML Body: {html_body[:200]}...")
        return True  # Pretend success so callers don't retry endlessly

    msg = MIMEMultipart("alternative") if html_body else MIMEMultipart()
    msg["From"] = smtp_cfg.from_email
    msg["To"] = to_email
    msg["Subject"] = subject

    # Always attach a plain-text part
    msg.attach(MIMEText(body, "plain", "utf-8"))

    # Optionally attach an HTML part
    if html_body:
        msg.attach(MIMEText(html_body, "html", "utf-8"))

    smtp_conn = None
    try:
        if smtp_cfg.use_tls:
            smtp_conn = smtplib.SMTP(smtp_cfg.host, smtp_cfg.port, timeout=30)
            smtp_conn.ehlo()
            smtp_conn.starttls()
            smtp_conn.ehlo()
        else:
            smtp_conn = smtplib.SMTP(smtp_cfg.host, smtp_cfg.port, timeout=30)
            smtp_conn.ehlo()

        smtp_conn.login(smtp_cfg.user, smtp_cfg.password)
        smtp_conn.sendmail(smtp_cfg.from_email, [to_email], msg.as_string())
        logger.info(f"Email sent successfully to {to_email}: {subject}")
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP authentication failed: {e}")
        return False
    except smtplib.SMTPConnectError as e:
        logger.error(f"SMTP connection failed: {e}")
        return False
    except smtplib.SMTPRecipientsRefused as e:
        logger.error(f"SMTP recipient refused: {to_email} – {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error while sending to {to_email}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending email to {to_email}: {e}")
        return False
    finally:
        if smtp_conn is not None:
            try:
                smtp_conn.quit()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Celery tasks
# ---------------------------------------------------------------------------

@celery_app.task(
    name="src.tasks.email.send_email",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_email(
    self,
    to_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None,
):
    """
    Send an email in the background via SMTP.

    If SMTP is not configured the email is simply logged.

    Args:
        to_email: Recipient email address.
        subject: Email subject.
        body: Plain-text email body.
        html_body: Optional HTML email body.

    Returns:
        True if successful, False otherwise.
    """
    try:
        success = _send_smtp_email(to_email, subject, body, html_body=html_body)
        if not success:
            # Retry with exponential backoff
            raise self.retry(exc=Exception("SMTP send failed"), countdown=2 ** self.request.retries)
        return True

    except self.MaxRetriesExceededError:
        logger.error(f"Max retries exceeded for email to {to_email}: {subject}")
        return False
    except Exception as e:
        if "retry" in str(type(e)).lower():
            raise  # re-raise retry signal
        logger.error(f"Failed to send email to {to_email}: {e}")
        try:
            raise self.retry(exc=e, countdown=2 ** self.request.retries)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for email to {to_email}: {subject}")
            return False


@celery_app.task(
    name="src.tasks.email.send_welcome_email",
    bind=True,
    max_retries=3,
)
def send_welcome_email(self, user_email: str, user_name: str):
    """
    Send welcome email to a new user.

    Args:
        user_email: User's email address.
        user_name: User's display name.

    Returns:
        True if successful.
    """
    subject = "Chào mừng đến với VietStore!"

    text_body = (
        f"Chào {user_name},\n\n"
        f"Cảm ơn bạn đã đăng ký tài khoản tại VietStore.\n\n"
        f"Chúng tôi rất vui được chào đón bạn!\n\n"
        f"Trân trọng,\n"
        f"Đội ngũ VietStore"
    )

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #f8f9fa; padding: 30px; border-radius: 8px;">
            <h2 style="color: #2d5016;">Chào mừng đến với VietStore!</h2>
            <p>Chào <strong>{user_name}</strong>,</p>
            <p>Cảm ơn bạn đã đăng ký tài khoản tại VietStore.</p>
            <p>Chúng tôi rất vui được chào đón bạn!</p>
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            <p style="color: #888; font-size: 12px;">Trân trọng,<br>Đội ngũ VietStore</p>
        </div>
    </body>
    </html>
    """

    try:
        success = _send_smtp_email(user_email, subject, text_body, html_body=html_body)
        if not success:
            raise self.retry(exc=Exception("SMTP send failed"), countdown=2 ** self.request.retries)
        return True
    except self.MaxRetriesExceededError:
        logger.error(f"Max retries exceeded for welcome email to {user_email}")
        return False
    except Exception as e:
        if "retry" in str(type(e)).lower():
            raise
        logger.error(f"Failed to send welcome email to {user_email}: {e}")
        try:
            raise self.retry(exc=e, countdown=2 ** self.request.retries)
        except self.MaxRetriesExceededError:
            return False


@celery_app.task(
    name="src.tasks.email.send_order_confirmation",
    bind=True,
    max_retries=3,
)
def send_order_confirmation(self, user_email: str, order_id: str, total: float):
    """
    Send order confirmation email.

    Args:
        user_email: User's email address.
        order_id: Order ID.
        total: Order total amount.

    Returns:
        True if successful.
    """
    subject = f"Xác nhận đơn hàng #{order_id}"

    text_body = (
        f"Đơn hàng của bạn đã được xác nhận thành công.\n\n"
        f"Mã đơn hàng: {order_id}\n"
        f"Tổng tiền: {total:,.0f} VNĐ\n\n"
        f"Chúng tôi sẽ xử lý đơn hàng của bạn sớm nhất có thể.\n\n"
        f"Trân trọng,\n"
        f"Đội ngũ VietStore"
    )

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #f8f9fa; padding: 30px; border-radius: 8px;">
            <h2 style="color: #2d5016;">Xác nhận đơn hàng</h2>
            <p>Đơn hàng của bạn đã được xác nhận thành công.</p>
            <table style="border-collapse: collapse; width: 100%; margin: 15px 0;">
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Mã đơn hàng</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">#{order_id}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Tổng tiền</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{total:,.0f} VNĐ</td>
                </tr>
            </table>
            <p>Chúng tôi sẽ xử lý đơn hàng của bạn sớm nhất có thể.</p>
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            <p style="color: #888; font-size: 12px;">Trân trọng,<br>Đội ngũ VietStore</p>
        </div>
    </body>
    </html>
    """

    try:
        success = _send_smtp_email(user_email, subject, text_body, html_body=html_body)
        if not success:
            raise self.retry(exc=Exception("SMTP send failed"), countdown=2 ** self.request.retries)
        return True
    except self.MaxRetriesExceededError:
        logger.error(f"Max retries exceeded for order confirmation email to {user_email}")
        return False
    except Exception as e:
        if "retry" in str(type(e)).lower():
            raise
        logger.error(f"Failed to send order confirmation to {user_email}: {e}")
        try:
            raise self.retry(exc=e, countdown=2 ** self.request.retries)
        except self.MaxRetriesExceededError:
            return False


@celery_app.task(
    name="src.tasks.email.send_password_reset",
    bind=True,
    max_retries=3,
)
def send_password_reset(self, user_email: str, reset_token: str, reset_url: Optional[str] = None):
    """
    Send password reset email.

    Args:
        user_email: User's email address.
        reset_token: Password reset token.
        reset_url: Optional full URL for the reset page including the token.

    Returns:
        True if successful.
    """
    subject = "Đặt lại mật khẩu – VietStore"

    link_line = ""
    if reset_url:
        link_line = f"\nNhấn vào liên kết sau để đặt lại mật khẩu: {reset_url}\n"

    text_body = (
        f"Bạn đã yêu cầu đặt lại mật khẩu.\n\n"
        f"Mã đặt lại: {reset_token}\n"
        f"{link_line}"
        f"\nNếu bạn không yêu cầu điều này, vui lòng bỏ qua email này.\n\n"
        f"Trân trọng,\n"
        f"Đội ngũ VietStore"
    )

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #f8f9fa; padding: 30px; border-radius: 8px;">
            <h2 style="color: #2d5016;">Đặt lại mật khẩu</h2>
            <p>Bạn đã yêu cầu đặt lại mật khẩu.</p>
            <div style="background-color: #fff; border: 1px dashed #ccc; padding: 15px; text-align: center; margin: 15px 0;">
                <span style="font-size: 24px; font-weight: bold; letter-spacing: 4px; color: #2d5016;">{reset_token}</span>
            </div>
            {"<p><a href='" + reset_url + "' style='background-color: #2d5016; color: #fff; padding: 10px 20px; text-decoration: none; border-radius: 4px;'>Đặt lại mật khẩu</a></p>" if reset_url else ""}
            <p style="color: #888; font-size: 13px;">Nếu bạn không yêu cầu điều này, vui lòng bỏ qua email này.</p>
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            <p style="color: #888; font-size: 12px;">Trân trọng,<br>Đội ngũ VietStore</p>
        </div>
    </body>
    </html>
    """

    try:
        success = _send_smtp_email(user_email, subject, text_body, html_body=html_body)
        if not success:
            raise self.retry(exc=Exception("SMTP send failed"), countdown=2 ** self.request.retries)
        return True
    except self.MaxRetriesExceededError:
        logger.error(f"Max retries exceeded for password reset email to {user_email}")
        return False
    except Exception as e:
        if "retry" in str(type(e)).lower():
            raise
        logger.error(f"Failed to send password reset email to {user_email}: {e}")
        try:
            raise self.retry(exc=e, countdown=2 ** self.request.retries)
        except self.MaxRetriesExceededError:
            return False
