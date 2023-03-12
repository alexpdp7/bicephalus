import contextlib
import pathlib
import ssl
import subprocess
import tempfile


@contextlib.contextmanager
def ssl_context_from_files(cert_path, key_path):
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(cert_path, key_path)
    yield context


@contextlib.contextmanager
def temporary_ssl_context(common_name):
    with tempfile.TemporaryDirectory() as cert_dir:
        cert_dir = pathlib.Path(cert_dir)
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:4096", "-keyout", "key.pem", "-out", "cert.pem", "-days", "365", "-nodes", "-subj", f"/CN={common_name}"], check=True, cwd=cert_dir)
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(cert_dir / "cert.pem", cert_dir / "key.pem")
        yield context
