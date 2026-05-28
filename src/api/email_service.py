from __future__ import annotations

"""
email_service.py
~~~~~~~~~~~~~~~~
Sends transactional emails (password reset) via SMTP.

Configuration is read from configs/sources.yaml under the `email` key:

    email:
      smtp_host: "smtp.gmail.com"
      smtp_port: 587
      sender_email: "you@gmail.com"
      sender_password: "your-app-password"
      app_base_url: "http://localhost:8501"

For Gmail you must create an App Password:
  Google Account → Security → 2-Step Verification → App passwords
  (your normal Gmail password will NOT work here)
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict

import yaml


# ─────────────────────────────────────────────
# Config loader
# ─────────────────────────────────────────────

def _load_email_config() -> Dict[str, Any]:
    config_path = Path(__file__).resolve().parents[2] / "configs" / "sources.yaml"
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)
    return cfg.get("email", {})


# ─────────────────────────────────────────────
# Core send helper
# ─────────────────────────────────────────────

def send_email(*, to_email: str, subject: str, html_body: str) -> None:
    """
    Send an HTML email via SMTP (TLS).

    Raises:
        RuntimeError  — if SMTP credentials are not configured.
        Exception     — re-raises any SMTP / network error.
    """
    cfg = _load_email_config()

    smtp_host = cfg.get("smtp_host", "smtp.gmail.com")
    smtp_port = int(cfg.get("smtp_port", 587))
    sender    = cfg.get("sender_email", "")
    password  = cfg.get("sender_password", "")

    if not sender or not password or "your-" in password:
        raise RuntimeError(
            "Email is not configured. "
            "Please fill in configs/sources.yaml → email section "
            "(smtp_host, smtp_port, sender_email, sender_password)."
        )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = sender
    msg["To"]      = to_email
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, to_email, msg.as_string())


# ─────────────────────────────────────────────
# Password reset email
# ─────────────────────────────────────────────

def send_password_reset_email(*, to_email: str, token: str) -> None:
    """
    Send a password-reset email containing:
      • A clickable link (uses app_base_url from config)
      • The raw token for manual copy-paste as fallback
    """
    cfg = _load_email_config()
    base_url = cfg.get("app_base_url", "http://localhost:8501").rstrip("/")
    reset_url = f"{base_url}/?reset_token={token}"

    subject = "Job Match — Password Reset Request"

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; max-width: 560px; margin: auto;">
      <h2 style="color: #1a73e8;">Reset Your Password</h2>
      <p>We received a request to reset the password for your Job Match account
         (<strong>{to_email}</strong>).</p>

      <p>Click the button below to set a new password. This link is valid for
         <strong>1 hour</strong> and can only be used once.</p>

      <p style="text-align:center; margin: 32px 0;">
        <a href="{reset_url}"
           style="background:#1a73e8; color:#fff; padding:14px 28px;
                  text-decoration:none; border-radius:6px; font-size:16px;">
          Reset My Password
        </a>
      </p>

      <p style="font-size:13px; color:#666;">
        If the button doesn't work, copy and paste this link into your browser:<br>
        <a href="{reset_url}">{reset_url}</a>
      </p>

      <hr style="border:none; border-top:1px solid #eee; margin:24px 0;">

      <p style="font-size:13px; color:#888;">
        If you did not request a password reset, you can safely ignore this email.
        Your password will not change.
      </p>
    </body>
    </html>
    """

    send_email(to_email=to_email, subject=subject, html_body=html_body)
