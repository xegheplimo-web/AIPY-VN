"""
Email Tasks

Background tasks for sending emails.
"""

import logging

from src.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="src.tasks.email.send_email",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_email(self, to_email: str, subject: str, body: str, html: bool = False):
    """
    Send an email in the background.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body content
        html: Whether the body is HTML (default: False)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # TODO: Integrate with actual email service (SendGrid, SES, etc.)
        logger.info(f"Sending email to {to_email}: {subject}")
        
        # Mock implementation
        logger.info(f"Email content: {body[:100]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


@celery_app.task(
    name="src.tasks.email.send_welcome_email",
    bind=True,
    max_retries=3
)
def send_welcome_email(self, user_email: str, user_name: str):
    """
    Send welcome email to new user.
    
    Args:
        user_email: User's email address
        user_name: User's name
    
    Returns:
        True if successful
    """
    subject = "Chào mừng đến với VietStore!"
    body = f"""
    Chào {user_name},
    
    Cảm ơn bạn đã đăng ký tài khoản tại VietStore.
    
    Chúng tôi rất vui được chào đón bạn!
    
    Trân trọng,
    Đội ngũ VietStore
    """
    
    return send_email(user_email, subject, body)


@celery_app.task(
    name="src.tasks.email.send_order_confirmation",
    bind=True,
    max_retries=3
)
def send_order_confirmation(self, user_email: str, order_id: str, total: float):
    """
    Send order confirmation email.
    
    Args:
        user_email: User's email address
        order_id: Order ID
        total: Order total amount
    
    Returns:
        True if successful
    """
    subject = f"Xác nhận đơn hàng #{order_id}"
    body = f"""
    Đơn hàng của bạn đã được xác nhận thành công.
    
    Mã đơn hàng: {order_id}
    Tổng tiền: {total:,.0f} VNĐ
    
    Chúng tôi sẽ xử lý đơn hàng của bạn sớm nhất có thể.
    
    Trân trọng,
    Đội ngũ VietStore
    """
    
    return send_email(user_email, subject, body)


@celery_app.task(
    name="src.tasks.email.send_password_reset",
    bind=True,
    max_retries=3
)
def send_password_reset(self, user_email: str, reset_token: str):
    """
    Send password reset email.
    
    Args:
        user_email: User's email address
        reset_token: Password reset token
    
    Returns:
        True if successful
    """
    subject = "Đặt lại mật khẩu"
    body = f"""
    Bạn đã yêu cầu đặt lại mật khẩu.
    
    Token đặt lại: {reset_token}
    
    Nếu bạn không yêu cầu điều này, vui lòng bỏ qua email này.
    
    Trân trọng,
    Đội ngũ VietStore
    """
    
    return send_email(user_email, subject, body)
