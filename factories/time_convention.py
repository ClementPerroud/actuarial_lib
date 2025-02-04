from classes.time_convention import TimeConvention
from services.time_convention import TimeConventionActActICMAService, TimeConventionActActISDAService, TimeConventionExact365Service, TimeConventionExact360Service, TimeConvention30360Service, TimeConvention30E360Service

class TimeConventionFactory:
    _time_convention_mapping = {
        TimeConvention.ACT_ACT_ICMA : TimeConventionActActICMAService(),
        TimeConvention.ACT_ACT_ISDA : TimeConventionActActISDAService(),
        TimeConvention.ACT_365 : TimeConventionExact365Service(),
        TimeConvention.ACT_360 : TimeConventionExact360Service(),
        TimeConvention._30_360 : TimeConvention30360Service(),
        TimeConvention._30E_360 : TimeConvention30E360Service(),
    }
    def create_time_convention_service(self, time_convention : TimeConvention):
        if time_convention not in self._time_convention_mapping: raise ValueError(f"{time_convention} not found in mapping of time convention in {self.__class__.__name__}")
        return self._time_convention_mapping[time_convention]