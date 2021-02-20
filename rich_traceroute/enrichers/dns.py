from threading import Lock

import dns.resolver
from cachetools import cached, TTLCache

from ..config import DNS_QUERY_TIMEOUT, DNS_CACHE_TTL


name_to_ip_cache: TTLCache = TTLCache(maxsize=1024, ttl=DNS_CACHE_TTL)
name_to_ip_cache_lock = Lock()
ip_to_name_cache: TTLCache = TTLCache(maxsize=1024, ttl=DNS_CACHE_TTL)
ip_to_name_cache_lock = Lock()


@cached(cache=name_to_ip_cache, lock=name_to_ip_cache_lock)
def name_to_ip(name: str) -> str:
    response = dns.resolver.resolve(
        name,
        tcp=False,
        lifetime=DNS_QUERY_TIMEOUT,
        search=False
    ).response

    return response.answer[0][0].to_text()


@cached(cache=ip_to_name_cache, lock=ip_to_name_cache_lock)
def ip_to_name(ip: str) -> str:
    response = dns.resolver.resolve_address(
        ip,
        tcp=False,
        lifetime=DNS_QUERY_TIMEOUT,
        search=False
    ).response

    res = response.answer[0][0].to_text()

    if res.endswith("."):
        res = res[:-1]

    return res
