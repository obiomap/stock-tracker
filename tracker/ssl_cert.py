"""
Generates a self-signed TLS certificate valid for localhost and the machine's
local IP addresses. The cert is stored in certs/ and reused across restarts.
Regenerated automatically if it expires within 30 days.
"""
import ipaddress
import socket
from datetime import datetime, timezone, timedelta
from pathlib import Path

CERT_DIR = Path(__file__).parent.parent / "certs"
CERT_FILE = CERT_DIR / "server.crt"
KEY_FILE = CERT_DIR / "server.key"
VALIDITY_DAYS = 825  # ~2.25 years (browser max for self-signed)
RENEW_BEFORE_DAYS = 30


def _local_ips() -> list[str]:
    ips = ["127.0.0.1"]
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None):
            addr = info[4][0]
            try:
                ipaddress.ip_address(addr)
                if addr not in ips:
                    ips.append(addr)
            except ValueError:
                pass
    except Exception:
        pass
    return ips


def _needs_regen() -> bool:
    if not CERT_FILE.exists() or not KEY_FILE.exists():
        return True
    try:
        from cryptography import x509
        from cryptography.hazmat.backends import default_backend
        cert = x509.load_pem_x509_certificate(CERT_FILE.read_bytes(), default_backend())
        expires = cert.not_valid_after_utc
        threshold = datetime.now(timezone.utc) + timedelta(days=RENEW_BEFORE_DAYS)
        return expires < threshold
    except Exception:
        return True


def ensure_cert() -> tuple[Path, Path]:
    """Return (cert_path, key_path), generating them first if needed."""
    if not _needs_regen():
        return CERT_FILE, KEY_FILE

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    CERT_DIR.mkdir(exist_ok=True)

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    local_ips = _local_ips()
    hostname = socket.gethostname()

    san_entries = [
        x509.DNSName("localhost"),
        x509.DNSName(hostname),
    ]
    for ip in local_ips:
        try:
            san_entries.append(x509.IPAddress(ipaddress.ip_address(ip)))
        except ValueError:
            pass

    now = datetime.now(timezone.utc)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "Stock Tracker"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Stock Tracker"),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=VALIDITY_DAYS))
        .add_extension(x509.SubjectAlternativeName(san_entries), critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )

    KEY_FILE.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )
    CERT_FILE.write_bytes(cert.public_bytes(serialization.Encoding.PEM))

    # restrict file permissions as much as Windows allows
    try:
        import os, stat
        os.chmod(KEY_FILE, stat.S_IRUSR | stat.S_IWUSR)
    except Exception:
        pass

    return CERT_FILE, KEY_FILE
