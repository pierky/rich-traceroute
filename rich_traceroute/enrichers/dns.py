from threading import Lock

import dns.resolver
import dns.reversename

from cachetools import cached, TTLCache

from ..config import DNS_QUERY_TIMEOUT, DNS_CACHE_TTL


name_to_ip_cache: TTLCache = TTLCache(maxsize=1024, ttl=DNS_CACHE_TTL)
name_to_ip_cache_lock = Lock()
ip_to_name_cache: TTLCache = TTLCache(maxsize=1024, ttl=DNS_CACHE_TTL)
ip_to_name_cache_lock = Lock()


@cached(cache=name_to_ip_cache, lock=name_to_ip_cache_lock)
def name_to_ip(name: str) -> str:
    try:
        answer = dns.resolver.query(
            name,
            tcp=False,
            lifetime=DNS_QUERY_TIMEOUT
        )

        for rr in answer:
            return str(rr)
    except:  # noqa: E722
        pass

    return ""


@cached(cache=ip_to_name_cache, lock=ip_to_name_cache_lock)
def ip_to_name(ip: str) -> str:
    try:
        qname = dns.reversename.from_address(ip)
        answer = dns.resolver.query(
            qname, "PTR",
            tcp=False,
            lifetime=DNS_QUERY_TIMEOUT
        )

        for rr in answer:
            res = str(rr)

            if res.endswith("."):
                res = res[:-1]

            return res
    except:  # noqa: E722
        return ""

    return ""
