import os

QUERY_IDENTIFIER = b"nif_local_salta_8223"
RESPONSE_IDENTIFIER = b"NOT_EZ_GIMEL_SHTAIM"
DOMAIN = "arazim.local"
CACHE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "last_server_ip.txt"
)
