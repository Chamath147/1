from __future__ import annotations
import json
from dataclasses import asdict, dataclass
from typing import Optional

import itsdangerous
from itsdangerous import TimestampSigner
from app import config
from app.models import User


signer = TimestampSigner(config.CUSTOM_ALIAS_SECRET)


@dataclass
class AliasSuffix:
    # whether this is a custom domain
    is_custom: bool
    # Suffix
    suffix: str
    # Suffix signature
    signed_suffix: str
    # whether this is a premium SL domain. Not apply to custom domain
    is_premium: bool
    # can be either Custom or SL domain
    domain: str
    # if custom domain, whether the custom domain has MX verified, i.e. can receive emails
    mx_verified: bool = True

    def serialize(self):
        return json.dumps(asdict(self))

    @classmethod
    def deserialize(cls, data: str) -> AliasSuffix:
        return AliasSuffix(**json.loads(data))


def check_suffix_signature(signed_suffix: str) -> Optional[str]:
    try:
        return signer.unsign(signed_suffix, max_age=600).decode()
    except itsdangerous.BadSignature:
        return None


def get_alias_suffixes(user: User) -> [AliasSuffix]:
    """
    Similar to as get_available_suffixes() but also return custom domain that doesn't have MX set up.
    """
    user_custom_domains = user.verified_custom_domains()

    alias_suffixes: [AliasSuffix] = []

    # put custom domain first
    # for each user domain, generate both the domain and a random suffix version
    for custom_domain in user_custom_domains:
        if custom_domain.random_prefix_generation:
            suffix = "." + user.get_random_alias_suffix() + "@" + custom_domain.domain
            alias_suffix = AliasSuffix(
                is_custom=True,
                suffix=suffix,
                signed_suffix=signer.sign(suffix).decode(),
                is_premium=False,
                domain=custom_domain.domain,
                mx_verified=custom_domain.verified,
            )
            if user.default_alias_custom_domain_id == custom_domain.id:
                alias_suffixes.insert(0, alias_suffix)
            else:
                alias_suffixes.append(alias_suffix)

        suffix = "@" + custom_domain.domain
        alias_suffix = AliasSuffix(
            is_custom=True,
            suffix=suffix,
            signed_suffix=signer.sign(suffix).decode(),
            is_premium=False,
            domain=custom_domain.domain,
            mx_verified=custom_domain.verified,
        )

        # put the default domain to top
        # only if random_prefix_generation isn't enabled
        if (
            user.default_alias_custom_domain_id == custom_domain.id
            and not custom_domain.random_prefix_generation
        ):
            alias_suffixes.insert(0, alias_suffix)
        else:
            alias_suffixes.append(alias_suffix)

    # then SimpleLogin domain
    for sl_domain in user.get_sl_domains():
        suffix = (
            (
                ""
                if config.DISABLE_ALIAS_SUFFIX
                else "." + user.get_random_alias_suffix()
            )
            + "@"
            + sl_domain.domain
        )
        alias_suffix = AliasSuffix(
            is_custom=False,
            suffix=suffix,
            signed_suffix=signer.sign(suffix).decode(),
            is_premium=sl_domain.premium_only,
            domain=sl_domain.domain,
            mx_verified=True,
        )

        # put the default domain to top
        if user.default_alias_public_domain_id == sl_domain.id:
            alias_suffixes.insert(0, alias_suffix)
        else:
            alias_suffixes.append(alias_suffix)

    return alias_suffixes
