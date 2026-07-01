"""
serve_https.py — 폰 LAN 테스트용 자체서명 HTTPS 서버
카메라(getUserMedia)는 보안컨텍스트(HTTPS 또는 localhost)에서만 동작하므로,
PC-폰이 같은 Wi-Fi일 때 https://<PC-IP>:8443 으로 접속해 테스트한다.

사용:
  pip install cryptography   # 최초 1회 (인증서 자동생성용)
  python serve_https.py
  → 폰 브라우저에서 https://<표시된 IP>:8443  (인증서 경고는 '고급 → 계속' 허용)
"""
import http.server, ssl, socket, os, datetime
from pathlib import Path

HERE = Path(__file__).parent
PORT = 8443
CERT = HERE / "_dev_cert.pem"


def ensure_cert():
    if CERT.exists():
        return
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "walkguardian-dev")])
    cert = (x509.CertificateBuilder()
            .subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
            .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]), False)
            .sign(key, hashes.SHA256()))
    with open(CERT, "wb") as f:
        f.write(key.private_bytes(serialization.Encoding.PEM,
                                  serialization.PrivateFormat.TraditionalOpenSSL,
                                  serialization.NoEncryption()))
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    print("자체서명 인증서 생성:", CERT.name)


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80)); return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def main():
    os.chdir(HERE)
    ensure_cert()
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile=str(CERT))
    httpd = http.server.HTTPServer(("0.0.0.0", PORT), http.server.SimpleHTTPRequestHandler)
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    ip = lan_ip()
    print(f"\n📱 폰에서 접속: https://{ip}:{PORT}")
    print(f"   (같은 Wi-Fi, 인증서 경고는 '고급→계속 진행' 허용)\n")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
