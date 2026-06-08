"""
Email notification service
"""

import logging
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from jinja2 import Template
from src.config import config

logger = logging.getLogger(__name__)


class EmailTemplate(str, Enum):
    """Email template types"""
    WELCOME = "welcome"
    ORDER_CONFIRMATION = "order_confirmation"
    ORDER_SHIPPED = "order_shipped"
    ORDER_DELIVERED = "order_delivered"
    PAYMENT_RECEIVED = "payment_received"
    PASSWORD_RESET = "password_reset"
    STORE_VERIFIED = "store_verified"
    STORE_SUSPENDED = "store_suspended"
    PROMOTION = "promotion"
    SYSTEM_ALERT = "system_alert"


@dataclass
class EmailData:
    """Email data structure"""
    to_email: str
    to_name: str
    subject: str
    template: EmailTemplate
    context: dict
    html_content: Optional[str] = None
    text_content: Optional[str] = None


class EmailService:
    """Service for sending email notifications"""
    
    def __init__(self):
        self.smtp_host = config.smtp_host if hasattr(config, 'smtp_host') else 'smtp.gmail.com'
        self.smtp_port = config.smtp_port if hasattr(config, 'smtp_port') else 587
        self.smtp_username = config.smtp_username if hasattr(config, 'smtp_username') else None
        self.smtp_password = config.smtp_password if hasattr(config, 'smtp_password') else None
        self.from_email = config.from_email if hasattr(config, 'from_email') else 'noreply@vietstore.vn'
        self.from_name = config.from_name if hasattr(config, 'from_name') else 'VietStore'
        self.enabled = bool(self.smtp_username and self.smtp_password)
    
    def _get_template(self, template: EmailTemplate) -> str:
        """Get email template content"""
        templates = {
            EmailTemplate.WELCOME: """
                <h2>Chào mừng {{ name }}!</h2>
                <p>Cảm ơn bạn đã đăng ký tài khoản tại VietStore.</p>
                <p>Chúng tôi rất vui được chào đón bạn!</p>
                <p>Trân trọng,<br>VietStore Team</p>
            """,
            EmailTemplate.ORDER_CONFIRMATION: """
                <h2>Xác nhận đơn hàng #{{ order_id }}</h2>
                <p>Chào {{ name }},</p>
                <p>Đơn hàng của bạn đã được xác nhận thành công.</p>
                <p>Tổng tiền: {{ total_amount }} VNĐ</p>
                <p>Chúng tôi sẽ thông báo khi đơn hàng được gửi.</p>
                <p>Trân trọng,<br>VietStore Team</p>
            """,
            EmailTemplate.ORDER_SHIPPED: """
                <h2>Đơn hàng #{{ order_id }} đã được gửi</h2>
                <p>Chào {{ name }},</p>
                <p>Đơn hàng của bạn đang trên đường đến bạn.</p>
                <p>Mã vận đơn: {{ tracking_number }}</p>
                <p>Trân trọng,<br>VietStore Team</p>
            """,
            EmailTemplate.ORDER_DELIVERED: """
                <h2>Đơn hàng #{{ order_id }} đã được giao</h2>
                <p>Chào {{ name }},</p>
                <p>Đơn hàng của bạn đã được giao thành công.</p>
                <p>Cảm ơn bạn đã mua sắm tại VietStore!</p>
                <p>Trân trọng,<br>VietStore Team</p>
            """,
            EmailTemplate.PAYMENT_RECEIVED: """
                <h2>Thanh toán đã nhận</h2>
                <p>Chào {{ name }},</p>
                <p>Chúng tôi đã nhận được thanh toán cho đơn hàng #{{ order_id }}.</p>
                <p>Số tiền: {{ amount }} VNĐ</p>
                <p>Trân trọng,<br>VietStore Team</p>
            """,
            EmailTemplate.PASSWORD_RESET: """
                <h2>Đặt lại mật khẩu</h2>
                <p>Chào {{ name }},</p>
                <p>Bạn đã yêu cầu đặt lại mật khẩu.</p>
                <p>Nhấn vào link bên dưới để đặt lại mật khẩu:</p>
                <p><a href="{{ reset_link }}">Đặt lại mật khẩu</a></p>
                <p>Link này sẽ hết hạn sau 1 giờ.</p>
                <p>Trân trọng,<br>VietStore Team</p>
            """,
            EmailTemplate.STORE_VERIFIED: """
                <h2>Cửa hàng đã được xác minh</h2>
                <p>Chào {{ name }},</p>
                <p>Cửa hàng của bạn đã được xác minh thành công.</p>
                <p>Bạn có thể bắt đầu bán hàng ngay bây giờ!</p>
                <p>Trân trọng,<br>VietStore Team</p>
            """,
            EmailTemplate.STORE_SUSPENDED: """
                <h2>Cửa hàng đã bị tạm dừng</h2>
                <p>Chào {{ name }},</p>
                <p>Cửa hàng của bạn đã bị tạm dừng vì: {{ reason }}</p>
                <p>Vui lòng liên hệ hỗ trợ để biết thêm chi tiết.</p>
                <p>Trân trọng,<br>VietStore Team</p>
            """,
            EmailTemplate.PROMOTION: """
                <h2>Khuyến mãi đặc biệt!</h2>
                <p>Chào {{ name }},</p>
                <p>{{ message }}</p>
                <p>Mã khuyến mãi: {{ code }}</p>
                <p>Giảm giá: {{ discount }}%</p>
                <p>Hạn sử dụng: {{ expiry }}</p>
                <p>Trân trọng,<br>VietStore Team</p>
            """,
            EmailTemplate.SYSTEM_ALERT: """
                <h2>Cảnh báo hệ thống</h2>
                <p>{{ message }}</p>
                <p>Vui lòng kiểm tra hệ thống ngay.</p>
                <p>Trân trọng,<br>VietStore Team</p>
            """,
        }
        
        return templates.get(template, "")
    
    def _render_template(self, template: EmailTemplate, context: dict) -> str:
        """Render email template with context"""
        template_str = self._get_template(template)
        jinja_template = Template(template_str)
        return jinja_template.render(**context)
    
    async def send_email(self, email_data: EmailData) -> bool:
        """
        Send email
        
        Args:
            email_data: Email data
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.warning("Email service is disabled. No SMTP credentials configured.")
            return False
        
        try:
            # Render template if not provided
            if not email_data.html_content:
                email_data.html_content = self._render_template(email_data.template, email_data.context)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = email_data.subject
            msg['From'] = formataddr((self.from_name, self.from_email))
            msg['To'] = formataddr((email_data.to_name, email_data.to_email))
            
            # Add HTML content
            html_part = MIMEText(email_data.html_content, 'html')
            msg.attach(html_part)
            
            # Add text content if provided
            if email_data.text_content:
                text_part = MIMEText(email_data.text_content, 'plain')
                msg.attach(text_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent to {email_data.to_email}: {email_data.subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {email_data.to_email}: {e}")
            return False
    
    async def send_welcome_email(self, to_email: str, to_name: str) -> bool:
        """Send welcome email"""
        email_data = EmailData(
            to_email=to_email,
            to_name=to_name,
            subject="Chào mừng đến với VietStore!",
            template=EmailTemplate.WELCOME,
            context={"name": to_name},
        )
        return await self.send_email(email_data)
    
    async def send_order_confirmation(
        self,
        to_email: str,
        to_name: str,
        order_id: str,
        total_amount: float,
    ) -> bool:
        """Send order confirmation email"""
        email_data = EmailData(
            to_email=to_email,
            to_name=to_name,
            subject=f"Xác nhận đơn hàng #{order_id}",
            template=EmailTemplate.ORDER_CONFIRMATION,
            context={
                "name": to_name,
                "order_id": order_id,
                "total_amount": f"{total_amount:,.0f}",
            },
        )
        return await self.send_email(email_data)
    
    async def send_order_shipped(
        self,
        to_email: str,
        to_name: str,
        order_id: str,
        tracking_number: str,
    ) -> bool:
        """Send order shipped email"""
        email_data = EmailData(
            to_email=to_email,
            to_name=to_name,
            subject=f"Đơn hàng #{order_id} đã được gửi",
            template=EmailTemplate.ORDER_SHIPPED,
            context={
                "name": to_name,
                "order_id": order_id,
                "tracking_number": tracking_number,
            },
        )
        return await self.send_email(email_data)
    
    async def send_order_delivered(
        self,
        to_email: str,
        to_name: str,
        order_id: str,
    ) -> bool:
        """Send order delivered email"""
        email_data = EmailData(
            to_email=to_email,
            to_name=to_name,
            subject=f"Đơn hàng #{order_id} đã được giao",
            template=EmailTemplate.ORDER_DELIVERED,
            context={"name": to_name, "order_id": order_id},
        )
        return await self.send_email(email_data)
    
    async def send_payment_received(
        self,
        to_email: str,
        to_name: str,
        order_id: str,
        amount: float,
    ) -> bool:
        """Send payment received email"""
        email_data = EmailData(
            to_email=to_email,
            to_name=to_name,
            subject=f"Thanh toán đã nhận - Đơn hàng #{order_id}",
            template=EmailTemplate.PAYMENT_RECEIVED,
            context={
                "name": to_name,
                "order_id": order_id,
                "amount": f"{amount:,.0f}",
            },
        )
        return await self.send_email(email_data)
    
    async def send_password_reset(
        self,
        to_email: str,
        to_name: str,
        reset_link: str,
    ) -> bool:
        """Send password reset email"""
        email_data = EmailData(
            to_email=to_email,
            to_name=to_name,
            subject="Đặt lại mật khẩu",
            template=EmailTemplate.PASSWORD_RESET,
            context={"name": to_name, "reset_link": reset_link},
        )
        return await self.send_email(email_data)
    
    async def send_store_verified(
        self,
        to_email: str,
        to_name: str,
    ) -> bool:
        """Send store verified email"""
        email_data = EmailData(
            to_email=to_email,
            to_name=to_name,
            subject="Cửa hàng đã được xác minh",
            template=EmailTemplate.STORE_VERIFIED,
            context={"name": to_name},
        )
        return await self.send_email(email_data)
    
    async def send_store_suspended(
        self,
        to_email: str,
        to_name: str,
        reason: str,
    ) -> bool:
        """Send store suspended email"""
        email_data = EmailData(
            to_email=to_email,
            to_name=to_name,
            subject="Cửa hàng đã bị tạm dừng",
            template=EmailTemplate.STORE_SUSPENDED,
            context={"name": to_name, "reason": reason},
        )
        return await self.send_email(email_data)
    
    async def send_promotion(
        self,
        to_email: str,
        to_name: str,
        message: str,
        code: str,
        discount: int,
        expiry: str,
    ) -> bool:
        """Send promotion email"""
        email_data = EmailData(
            to_email=to_email,
            to_name=to_name,
            subject="Khuyến mãi đặc biệt!",
            template=EmailTemplate.PROMOTION,
            context={
                "name": to_name,
                "message": message,
                "code": code,
                "discount": discount,
                "expiry": expiry,
            },
        )
        return await self.send_email(email_data)
    
    async def send_system_alert(
        self,
        to_email: str,
        to_name: str,
        message: str,
    ) -> bool:
        """Send system alert email"""
        email_data = EmailData(
            to_email=to_email,
            to_name=to_name,
            subject="Cảnh báo hệ thống",
            template=EmailTemplate.SYSTEM_ALERT,
            context={"name": to_name, "message": message},
        )
        return await self.send_email(email_data)
    
    async def send_bulk_emails(self, email_data_list: List[EmailData]) -> int:
        """
        Send bulk emails
        
        Args:
            email_data_list: List of email data
        
        Returns:
            Number of emails sent successfully
        """
        success_count = 0
        for email_data in email_data_list:
            if await self.send_email(email_data):
                success_count += 1
        
        logger.info(f"Bulk email sent: {success_count}/{len(email_data_list)} successful")
        return success_count


# Global email service instance
email_service = EmailService()
