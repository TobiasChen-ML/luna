import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from ..core.config import get_config_value

logger = logging.getLogger(__name__)


class EmailService:
    async def _get_smtp_config(self) -> dict:
        return {
            "host": await get_config_value("SMTP_ADDRESS"),
            "port": int(await get_config_value("SMTP_PORT") or "587"),
            "user": await get_config_value("SMTP_USERNAME"),
            "password": await get_config_value("SMTP_PASSWORD"),
            "from_email": await get_config_value("SMTP_FROM_EMAIL"),
        }
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html: bool = False
    ) -> bool:
        config = await self._get_smtp_config()
        if not config["host"]:
            logger.warning("SMTP not configured, skipping email")
            return False
        
        try:
            msg = MIMEMultipart()
            msg["From"] = config["from_email"]
            msg["To"] = to_email
            msg["Subject"] = subject
            
            if html:
                msg.attach(MIMEText(body, "html"))
            else:
                msg.attach(MIMEText(body, "plain"))
            
            with smtplib.SMTP(
                config["host"],
                config["port"]
            ) as server:
                if config["user"]:
                    server.starttls()
                    server.login(
                        config["user"],
                        config["password"]
                    )
                server.send_message(msg)
            
            logger.info(f"Email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    async def send_verification_email(
        self,
        to_email: str,
        verification_token: str,
        verification_url: str
    ) -> bool:
        verify_link = f"{verification_url}?token={verification_token}"
        
        subject = "Verify Your Email"
        html_body = f"""
        <html>
        <body>
            <h2>Welcome to Roxy!</h2>
            <p>Please click the link below to verify your email address:</p>
            <p><a href="{verify_link}">{verify_link}</a></p>
            <p>This link will expire in 24 hours.</p>
        </body>
        </html>
        """
        return await self.send_email(to_email, subject, html_body, html=True)
    
    async def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
        reset_url: str
    ) -> bool:
        reset_link = f"{reset_url}?token={reset_token}"
        
        subject = "Reset Your Password"
        html_body = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>Click the link below to reset your password:</p>
            <p><a href="{reset_link}">{reset_link}</a></p>
            <p>This link will expire in 1 hour.</p>
        </body>
        </html>
        """
        return await self.send_email(to_email, subject, html_body, html=True)
    
    async def send_notification_email(
        self,
        to_email: str,
        subject: str,
        message: str
    ) -> bool:
        html_body = f"""
        <html>
        <body>
            <p>{message}</p>
        </body>
        </html>
        """
        return await self.send_email(to_email, subject, html_body, html=True)