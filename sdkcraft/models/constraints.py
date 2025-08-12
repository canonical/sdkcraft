#  This file is part of sdkcraft.
#
# Copyright 2024 Canonical Ltd.
#
#  This program is free software: you can redistribute it and/or modify it
#  under the terms of the GNU General Public License version 3, as
#  published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranties of MERCHANTABILITY,
#  SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR PURPOSE.
#  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Constrained pydantic types for SDKcraft."""

import re
from ipaddress import ip_address
from typing import Annotated
from urllib.parse import urlsplit, urlunsplit

from craft_application.models import constraints
from pydantic import AfterValidator, BeforeValidator, Field
from pydantic.fields import FieldInfo

RESERVED_NAME_REGEX = r"(?!^(system|try-.*|project-.*|sketch)$)"
RESERVED_NAME_COMPILED_REGEX = re.compile(RESERVED_NAME_REGEX)
MESSAGE_RESERVED_NAME = (
    "invalid name: Names cannot be 'system', 'sketch' or start with 'project-'."
)

PROJECT_NAME_REGEX = RESERVED_NAME_REGEX + constraints.PROJECT_NAME_REGEX
PROJECT_NAME_COMPILED_REGEX = re.compile(PROJECT_NAME_REGEX)


ProjectName = Annotated[
    str,
    Field(pattern=PROJECT_NAME_COMPILED_REGEX),
    FieldInfo.from_annotation(constraints.ProjectName),  # type: ignore[reportArgumentType]
    BeforeValidator(
        constraints.get_validator_by_regex(
            RESERVED_NAME_COMPILED_REGEX, MESSAGE_RESERVED_NAME
        )
    ),
]


def _parse_netloc(netloc: str) -> tuple[str | None, int | None]:
    split = urlsplit(urlunsplit(("", netloc, "", "", "")))

    if (
        (split.scheme, split.path, split.query, split.fragment) != ("", "", "", "")
        or split.username is not None
        or split.password is not None
    ):
        raise ValueError("expected hostname:port")

    return split.hostname, split.port


def _parse_address(address: str) -> tuple[str, int | None]:
    if not address:
        return "localhost", None

    if address.isdigit():
        hostname, port = _parse_netloc(f"localhost:{address}")
        if hostname != "localhost":
            raise AssertionError("expected digits to parse as port")
        return hostname, port

    try:
        hostname, port = _parse_netloc(address)
    except ValueError:
        pass
    else:
        if hostname is not None and port is not None:
            return hostname, port

    # Remove square brackets from standalone address.
    try:
        hostname, port = _parse_netloc(f"{address}:")
    except ValueError:
        pass
    else:
        if hostname is not None and port is None:
            return hostname, port

    return address, None


def _validate_endpoint(endpoint: str) -> str:
    if endpoint.startswith(("/", "@")):
        return endpoint
    if endpoint.startswith("$"):
        if endpoint.startswith(("$HOME/", "$XDG_RUNTIME_DIR/")):
            return endpoint
        variable, _, _ = endpoint.partition("/")
        raise ValueError(f"unexpected variable {variable!r}")

    if endpoint in ("tcp", "udp"):
        address = ""
    elif endpoint.endswith("/tcp"):
        address = endpoint.removesuffix("/tcp")
    elif endpoint.endswith("/udp"):
        address = endpoint.removesuffix("/udp")
    else:
        address = endpoint

    # Port is unused but still needs to be computed.
    # It is validated when querying the SplitResult.port property.
    hostname, _ = _parse_address(address)

    if hostname not in ("localhost", "ip6-localhost", "ip6-loopback"):
        ip_address(hostname)

    return endpoint


Endpoint = Annotated[str, AfterValidator(_validate_endpoint)]
