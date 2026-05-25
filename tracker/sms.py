"""
SMS alerts via Twilio (primary) or email-to-SMS carrier gateways (free fallback).

Twilio: sign up at twilio.com (free trial ~$15 credit). Run 'run.bat setup' to configure.
Gateway: works with any US carrier — no extra account needed, uses your existing email config.
"""
from __future__ import annotations

CARRIER_GATEWAYS: dict[str, str] = {
    "AT&T":             "@txt.att.net",
    "Verizon":          "@vtext.com",
    "T-Mobile":         "@tmomail.net",
    "Sprint":           "@messaging.sprintpcs.com",
    "Cricket":          "@mms.cricketwireless.net",
    "MetroPCS":         "@mymetropcs.com",
    "Boost Mobile":     "@sms.myboostmobile.com",
    "US Cellular":      "@email.uscc.net",
    "Google Fi":        "@msg.fi.google.com",
    "Republic Wireless":"@text.republicwireless.com",
    "Straight Talk":    "@vtext.com",
    "TracFone":         "@mmst5.tracfone.com",
}


def _twilio_ready(config: dict) -> bool:
    s = config.get("sms", {})
    return bool(s.get("twilio_sid") and s.get("twilio_token") and s.get("twilio_from"))


def _clean_phone(phone: str) -> str:
    """Strip non-digit chars and return 10-digit US number."""
    digits = "".join(c for c in phone if c.isdigit())
    return digits[-10:] if len(digits) >= 10 else digits


def send_sms(to_number: str, carrier: str, message: str, config: dict) -> bool:
    """Send one SMS. Uses Twilio if configured, otherwise email-to-SMS gateway."""
    if not to_number:
        return False
    if _twilio_ready(config):
        return _send_twilio(to_number, message, config)
    if carrier:
        return _send_gateway(to_number, carrier, message, config)
    return False


def _send_twilio(to_number: str, message: str, config: dict) -> bool:
    try:
        from twilio.rest import Client
        s = config["sms"]
        client = Client(s["twilio_sid"], s["twilio_token"])
        clean = _clean_phone(to_number)
        e164 = f"+1{clean}" if not to_number.strip().startswith("+") else to_number.strip()
        client.messages.create(body=message[:160], from_=s["twilio_from"], to=e164)
        return True
    except Exception as e:
        print(f"[SMS/Twilio] {e}")
        return False


def _send_gateway(phone: str, carrier: str, message: str, config: dict) -> bool:
    """Send via email-to-SMS gateway — requires Resend to be configured."""
    import os
    # Exact match first; fall back to case-insensitive search
    gateway = CARRIER_GATEWAYS.get(carrier, "")
    if not gateway:
        carrier_lower = carrier.lower().replace("-", "").replace(" ", "")
        for k, v in CARRIER_GATEWAYS.items():
            if k.lower().replace("-", "").replace(" ", "") == carrier_lower:
                gateway = v
                break
    if not gateway:
        print(f"[SMS/gateway] unknown carrier: {carrier!r}")
        return False
    clean = _clean_phone(phone)
    if len(clean) != 10:
        print(f"[SMS/gateway] bad phone digits: {clean!r}")
        return False
    sms_addr = f"{clean}{gateway}"
    print(f"[SMS/gateway] sending to {sms_addr}")
    # SMS gateways need plain text — send directly via Resend (not HTML wrapper)
    api_key = os.environ.get("RESEND_API_KEY") or config.get("resend_api_key", "")
    from_addr = (os.environ.get("RESEND_FROM")
                 or config.get("resend_from", "onboarding@resend.dev"))
    if not api_key:
        print("[SMS/gateway] no RESEND_API_KEY — cannot send")
        return False
    try:
        import resend
        resend.api_key = api_key
        resend.Emails.send({
            "from": from_addr,
            "to": [sms_addr],
            "subject": "",
            "text": message[:160],
        })
        print(f"[SMS/gateway] sent OK → {sms_addr}")
        return True
    except Exception as e:
        print(f"[SMS/gateway] error → {sms_addr}: {e}")
        return False


def send_sms_to_subscribers(message: str, relevant_symbols: set[str], config: dict) -> int:
    """Fan out SMS to all SMS-subscribed users who track at least one alerted symbol."""
    from . import database as db
    if not config.get("sms", {}).get("enabled") and not _twilio_ready(config):
        return 0
    subscribers = db.get_active_subscribers()
    sent = 0
    for sub in subscribers:
        phone = sub.get("phone_number", "").strip()
        if not phone:
            continue
        sub_stocks = set(sub["stocks"])
        if sub_stocks and not (sub_stocks & relevant_symbols):
            continue
        carrier = sub.get("carrier", "").strip()
        if send_sms(phone, carrier, message, config):
            sent += 1
    return sent
