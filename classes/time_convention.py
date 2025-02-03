from enum import Enum
class TimeConvention(Enum):
    ACT_ACT = "act/act"
    ACT_365 = "act/365"
    ACT_360 = "act/360"
    EXACT_EXACT = "exact/exact"
    _30_360 = "30/360"
    _30E_360 = "30E/360"