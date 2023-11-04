"""
Implementation of the Terraform variant of the RPCPlugin spec.
"""
import datetime
from base64 import b64encode
from concurrent import futures
from sys import stderr

import grpc
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from . import tfplugin64_pb2_grpc
from .health_servicer import _configure_health_server
from .provider_servicer import ProviderServicer


class RPCPluginServer:
    def __init__(self):
        self.cert, self.key = generate_server_cert()

    def run(self):
        port = "1234"
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        tfplugin64_pb2_grpc.add_ProviderServicer_to_server(
            ProviderServicer(), server
        )
        key_cert_pair_for_grpc = (
            self.key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            ),
            self.cert.public_bytes(serialization.Encoding.PEM),
        )
        creds = grpc.ssl_server_credentials([key_cert_pair_for_grpc])
        server.add_secure_port(f"127.0.0.1:{port}", creds)
        _configure_health_server(server)
        cert_base64 = encode_cert_base64(self.cert)
        server.start()
        print(f"server listening on port {port}", file=stderr)
        print(f"1|6|tcp|127.0.0.1:{port}|grpc|{cert_base64}", flush=True)
        server.wait_for_termination()


def generate_server_cert() -> tuple[x509.Certificate, rsa.RSAPrivateKey]:
    # key
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    # cert
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "My Company"),
            x509.NameAttribute(NameOID.COMMON_NAME, "mysite.com"),
        ]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(
            datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(days=3)  # valid for 3 days
        )
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("localhost")]),
            critical=False,
        )
        .sign(key, hashes.SHA256())  # sign w/ private key
    )
    return cert, key


def encode_cert_base64(cert: x509.Certificate) -> str:
    return b64encode(cert.public_bytes(serialization.Encoding.DER)).decode(
        "ascii"
    )
