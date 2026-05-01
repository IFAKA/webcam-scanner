import socket
from urllib.parse import urlparse

from .contracts import LocalNetworkConfig

DEFAULT_API_PORT = 8000


def local_network_config(
    *,
    public_api_url: str | None = None,
    api_port: int = DEFAULT_API_PORT,
) -> LocalNetworkConfig:
    override = normalized_public_url(public_api_url)
    if override is not None:
        parsed = urlparse(override)
        return LocalNetworkConfig(
            api_base_url=override,
            websocket_base_url=websocket_base_url(parsed.scheme, parsed.netloc),
            host=parsed.hostname or "localhost",
            port=parsed.port or default_port(parsed.scheme),
            detected_interface="configured",
            is_loopback=is_loopback_host(parsed.hostname),
        )

    host = detect_lan_ipv4()
    return LocalNetworkConfig(
        api_base_url=f"http://{host}:{api_port}",
        websocket_base_url=f"ws://{host}:{api_port}",
        host=host,
        port=api_port,
        detected_interface="auto",
        is_loopback=is_loopback_host(host),
    )


def normalized_public_url(value: str | None) -> str | None:
    if value is None or value.strip() == "":
        return None

    parsed = urlparse(value.strip().rstrip("/"))
    if parsed.scheme not in {"http", "https"} or parsed.netloc == "":
        raise ValueError("ROOM_SCANNER_PUBLIC_API_URL must be an http(s) URL with a host.")
    return parsed.geturl()


def websocket_base_url(http_scheme: str, netloc: str) -> str:
    scheme = "wss" if http_scheme == "https" else "ws"
    return f"{scheme}://{netloc}"


def default_port(scheme: str) -> int:
    return 443 if scheme == "https" else 80


def is_loopback_host(host: str | None) -> bool:
    if host is None:
        return False
    return host.startswith("127.") or host in {"localhost", "::1"}


def detect_lan_ipv4() -> str:
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        udp_socket.connect(("8.8.8.8", 80))
        host = udp_socket.getsockname()[0]
        if not is_loopback_host(host):
            return host
    except OSError:
        pass
    finally:
        udp_socket.close()

    try:
        for address in socket.gethostbyname_ex(socket.gethostname())[2]:
            if "." in address and not is_loopback_host(address):
                return address
    except OSError:
        pass

    return "127.0.0.1"
