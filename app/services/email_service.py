"""
Email service for sending OTP codes
"""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


async def send_otp_email(to_email: str, otp_code: str) -> bool:
    """
    Send OTP code to user's email
    
    Args:
        to_email: Recipient email address
        otp_code: OTP code to send
    
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = "Your OTP Code - RAG Backend"
        message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        message["To"] = to_email
        
        # HTML email content
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h2 style="color: #333; margin-bottom: 20px;">Your One-Time Password</h2>
                    <p style="color: #666; font-size: 16px; line-height: 1.5;">
                        Use the following OTP code to complete your login:
                    </p>
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; text-align: center; margin: 20px 0;">
                        <h1 style="color: #007bff; font-size: 36px; letter-spacing: 5px; margin: 0;">
                            {otp_code}
                        </h1>
                    </div>
                    <p style="color: #666; font-size: 14px; line-height: 1.5;">
                        This code will expire in {settings.otp_expire_minutes} minutes.
                    </p>
                    <p style="color: #999; font-size: 12px; margin-top: 30px;">
                        If you didn't request this code, please ignore this email.
                    </p>
                </div>
            </body>
        </html>
        """
        
        # Plain text fallback
        text_content = f"""
        Your OTP Code: {otp_code}
        
        This code will expire in {settings.otp_expire_minutes} minutes.
        
        If you didn't request this code, please ignore this email.
        """
        
        # Attach both versions
        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        message.attach(part1)
        message.attach(part2)
        
        # Send email
        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            start_tls=True,
        )
        
        logger.info(f"OTP email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send OTP email to {to_email}: {str(e)}")
        return False
