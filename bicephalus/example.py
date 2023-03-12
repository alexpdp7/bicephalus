import bicephalus
from bicephalus import main as bicephalus_main


def handler(request: bicephalus.Request) -> bicephalus.Response:
    if request.proto == bicephalus.Proto.GEMINI:
        content = f"# Hello at {request.path}"
        content_type = "text/gemini"
    elif request.proto == bicephalus.Proto.HTTP:
        content = f"<html><body><h1>Hello at {request.path}</h1></body></html>"
        content_type = "text/html"
    else:
        assert False, f"unknown protocol {request.proto}"

    return bicephalus.Response(
        content=content.encode("utf8"),
        content_type=content_type,
        status=bicephalus.Status.OK,
    )


def main():
    """
    Usage:

    $ openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem \
              -days 365 -nodes
    # specify localhost as the common name
    $ poetry run python -m bicephalus.example
    """
    bicephalus_main.main(handler)


if __name__ == "__main__":
    main()
