from enum import Enum
class TimeConvention(Enum):
    ACT_ACT_ICMA = "ACT/ACT (ICMA)"
    ACT_ACT_ISDA = "ACT/ACT (ISDA)"
    ACT_365 = "ACT/365"
    ACT_360 = "ACT/360"
    _30_360 = "30/360"
    _30E_360 = "30E/360"