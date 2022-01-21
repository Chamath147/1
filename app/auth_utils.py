import requests
import hashlib
from app.config import DISABLE_PWNEDPASSWORDS


def check_pwnedpasswords(password, bypass=False):
    """
    Checks a password against Pwned Passwords using the k-anonymity range endpoint

    Returns true if the password is in Pwned Passwords, false otherwise.
    """
    if bypass is False and DISABLE_PWNEDPASSWORDS:
        return False
    else:
        sha1_hash = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
        lookup_hash = sha1_hash[0:5]
        pwnedpasswords_res = requests.get(
            "https://api.pwnedpasswords.com/range/" + lookup_hash
        ).content.decode("utf-8")
        hash_matches = list(
            map(lambda x: x.split(":")[0], pwnedpasswords_res.splitlines())
        )
        return sha1_hash[5:] in hash_matches