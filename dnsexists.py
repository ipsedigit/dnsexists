import socket
import sys


def resolve(hostname: str) -> bool:
    """Return True if hostname resolves in DNS, False otherwise."""
    try:
        socket.getaddrinfo(hostname, None)
        return True
    except socket.gaierror:
        return False


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python dnsexists.py <hostname>")
        sys.exit(2)
    hostname = sys.argv[1]
    if resolve(hostname):
        print(f"{hostname}: EXISTS")
        sys.exit(0)
    else:
        print(f"{hostname}: NOT FOUND")
        sys.exit(1)


if __name__ == "__main__":
    main()
