"""
Common types shared across different modules.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ThordataBaseConfig:
    """Base class for all config objects with payload conversion."""

    def to_payload(self) -> dict[str, Any]:
        raise NotImplementedError


class Device(str, Enum):
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"


class OutputFormat(str, Enum):
    HTML = "html"
    PNG = "png"


@dataclass
class CommonSettings:
    """
    Common settings for video/audio downloads.
    Keys strictly aligned with Thordata Video Builder API.
    """

    resolution: str | None = None
    video_codec: str | None = None  # vp9, avc
    audio_format: str | None = None  # opus, mp3
    bitrate: str | None = None
    selected_only: str | bool | None = None
    is_subtitles: str | bool | None = None
    subtitles_language: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {}
        for k, v in self.__dict__.items():
            if v is not None:
                # API expects explicit string "true"/"false" for booleans
                if isinstance(v, bool):
                    result[k] = "true" if v else "false"
                else:
                    result[k] = str(v)
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


def normalize_enum_value(value: object, enum_class: type) -> str:
    """
    Safely convert an enum or string to its string value.
    """
    if isinstance(value, enum_class):
        return str(getattr(value, "value", value)).lower()
    if isinstance(value, str):
        return value.lower()
    raise TypeError(
        f"Expected {enum_class.__name__} or str, got {type(value).__name__}"
    )


# --- Geography Enums ---


class Continent(str, Enum):
    AFRICA = "af"
    ANTARCTICA = "an"
    ASIA = "as"
    EUROPE = "eu"
    NORTH_AMERICA = "na"
    OCEANIA = "oc"
    SOUTH_AMERICA = "sa"


class Country(str, Enum):
    US = "us"
    CA = "ca"
    MX = "mx"
    GB = "gb"
    DE = "de"
    FR = "fr"
    ES = "es"
    IT = "it"
    NL = "nl"
    PL = "pl"
    RU = "ru"
    UA = "ua"
    SE = "se"
    NO = "no"
    DK = "dk"
    FI = "fi"
    CH = "ch"
    AT = "at"
    BE = "be"
    PT = "pt"
    IE = "ie"
    CZ = "cz"
    GR = "gr"
    CN = "cn"
    JP = "jp"
    KR = "kr"
    IN = "in"
    AU = "au"
    NZ = "nz"
    SG = "sg"
    HK = "hk"
    TW = "tw"
    TH = "th"
    VN = "vn"
    ID = "id"
    MY = "my"
    PH = "ph"
    PK = "pk"
    BD = "bd"
    BR = "br"
    AR = "ar"
    CL = "cl"
    CO = "co"
    PE = "pe"
    VE = "ve"
    AE = "ae"
    SA = "sa"
    IL = "il"
    TR = "tr"
    ZA = "za"
    EG = "eg"
    NG = "ng"
    KE = "ke"
    MA = "ma"
