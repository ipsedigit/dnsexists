import socket

TLD_WHOIS_SERVERS: dict[str, str] = {
    ".com": "whois.verisign-grs.com",
    ".net": "whois.verisign-grs.com",
    ".org": "whois.pir.org",
    ".io": "whois.nic.io",
    ".co": "whois.nic.co",
    ".ai": "whois.nic.ai",
    ".dev": "whois.nic.google",
    ".app": "whois.nic.google",
    ".it": "whois.nic.it",
    ".eu": "whois.eu",
    ".info": "whois.nic.info",
    ".biz": "whois.nic.biz",
    ".me": "whois.domain.me",
    ".online": "whois.radix.website",
    ".store": "whois.radix.website",
    ".shop": "whois.nic.shop",
    ".tech": "whois.radix.website",
    ".news": "whois.radix.website",
    ".club": "whois.nic.club",
    ".xyz": "whois.nic.xyz",
}

_NOT_FOUND_PATTERNS = [
    "no match for",
    "not found",
    "no entries found",
    "domain not found",
]


def query(server: str, domain: str, timeout: float = 5.0) -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    sock.connect((server, 43))
    sock.sendall(f"{domain}\r\n".encode())
    chunks = []
    while True:
        data = sock.recv(4096)
        if not data:
            break
        chunks.append(data)
    sock.close()
    return b"".join(chunks).decode("utf-8", errors="replace")


def is_registered(domain: str) -> bool:
    tld = "." + domain.rsplit(".", 1)[-1]
    if tld not in TLD_WHOIS_SERVERS:
        raise ValueError(f"Unsupported TLD: {tld}")
    server = TLD_WHOIS_SERVERS[tld]
    try:
        response = query(server, domain)
    except Exception:
        return True
    lower = response.lower()
    if any(p in lower for p in _NOT_FOUND_PATTERNS):
        return False
    return True
