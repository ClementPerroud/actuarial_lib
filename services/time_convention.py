
import datetime
from abc import ABC, abstractmethod
import numpy as np
from utils.numpy_date_utils import NumpyDateUtils

from services.service import Service

class AbstractTimeConventionService(Service, ABC):
    @abstractmethod
    def year_count(self, from_dates: np.ndarray, to_dates: np.ndarray):
        ...

class OptimizedActActService:
    """
    An optimized version of your Act/Act day count.
    """

    def year_count(self, from_dates: np.ndarray, to_dates: np.ndarray):
        """
        Vectorized year count that avoids recursion for negative intervals
        and uses minimal repeated calls.
        """
        # 1. Identify negative intervals (swap them).

        # 2. Precompute years for both:
        from_years_up = from_dates.astype('datetime64[Y]') + 1
        to_years_down = to_dates.astype('datetime64[Y]')


        # 3. Compute years counts (eg. 12-06-2007 -> 28-09-2019)
        # a. Start :  12-06-2007 to 1-1-2008
        day_count_start = from_years_up.astype('datetime64[D]') - from_dates.astype('datetime64[D]')
        year_count_start = day_count_start.astype(float) / np.where(from_years_up.astype(int) % 4 == 0, 366.0, 365.0)

        # b. Middle :  1-1-2008 to 1-1-2019
        year_count_middle = (to_years_down - from_years_up).astype(float)

        # c. End :  1-1-2019 to 28-09-2019
        day_count_end = to_dates.astype('datetime64[D]') - to_years_down.astype('datetime64[D]')  
        year_count_end = day_count_end.astype(float) / np.where(from_years_up.astype(int) % 4 == 0, 366.0, 365.0)

        return year_count_start + year_count_middle + year_count_end
    
class TimeConventionActActService(AbstractTimeConventionService):
    def _inner_to_ceil_year_count(self, dates: np.datetime64):
        timedeltas = (NumpyDateUtils.years_ceiled(dates) - dates)
        filter_leap_year = NumpyDateUtils.get_years(dates) %4 == 0
        return timedeltas / np.where(filter_leap_year, np.timedelta64(366, 'D'), np.timedelta64(365,'D'))

    def _inner_to_floor_year_count(self, dates: np.datetime64):
        return 1 - self._inner_to_ceil_year_count(dates= dates)
    
    def year_count(self, from_dates : np.ndarray, to_dates  : np.ndarray):
      
        diff_array = (to_dates - from_dates)
        result = np.zeros(shape=diff_array.shape)
        
        if_neg = to_dates < from_dates
        if if_neg.sum() > 0:
            result[if_neg] = -self.year_count(
                from_dates = to_dates if np.isscalar(to_dates) else to_dates[if_neg],
                to_dates = from_dates if np.isscalar(from_dates) else from_dates[if_neg]
            )
        
        elif_same_year = np.logical_not(if_neg) & (NumpyDateUtils.get_years(to_dates) == NumpyDateUtils.get_years(from_dates))
        if elif_same_year.sum() > 0:
            filter_leap_year = NumpyDateUtils.get_years(
                dates = from_dates if np.isscalar(from_dates) else from_dates[elif_same_year]
                ) %4 == 0
            result[elif_same_year] = diff_array[elif_same_year] / np.where(filter_leap_year, np.timedelta64(366, 'D'), np.timedelta64(365, 'D'))

        else_filter = np.logical_not(if_neg) & np.logical_not(elif_same_year)

        if else_filter.sum() > 0: #from_dates.year < to_dates.year
            from_dates_else = from_dates if np.isscalar(from_dates) else from_dates[else_filter]
            to_dates_else = to_dates if np.isscalar(to_dates) else to_dates[else_filter]
            result[else_filter]= (
                self._inner_to_ceil_year_count(dates = from_dates_else)
                + NumpyDateUtils.get_years(to_dates_else) - NumpyDateUtils.get_years(from_dates_else) - 1
                + self._inner_to_floor_year_count(dates = to_dates_else)
            )
        return result


class TimeConvention30360Service(AbstractTimeConventionService):
    def year_count(self, from_dates: np.ndarray, to_dates: np.ndarray):
        return Numerator30.day_count(
            from_dates=from_dates, to_dates=to_dates
        ) / Denominator360.day_count(from_dates=from_dates, to_dates=to_dates)


class TimeConvention30E360Service(AbstractTimeConventionService):
    def year_count(self, from_dates: np.ndarray, to_dates: np.ndarray):
        return Numerator30E.day_count(
            from_dates=from_dates, to_dates=to_dates
        ) / Denominator360.day_count(from_dates=from_dates, to_dates=to_dates)


class TimeConventionExact360Service(AbstractTimeConventionService):
    def year_count(self, from_dates: np.ndarray, to_dates: np.ndarray):
        return NumeratorExact.day_count(
            from_dates=from_dates, to_dates=to_dates
        ) / Denominator360.day_count(from_dates=from_dates, to_dates=to_dates)


class TimeConventionExact365Service(AbstractTimeConventionService):
    def year_count(self, from_dates: np.ndarray, to_dates: np.ndarray):
        return NumeratorExact.day_count(
            from_dates=from_dates, to_dates=to_dates
        ) / Denominator365.day_count(from_dates=from_dates, to_dates=to_dates)


# Utils numerators and denominators

class NumeratorExact:
    @classmethod
    def day_count(self, from_dates : np.ndarray, to_dates : np.ndarray):
        return to_dates - from_dates


class Denominator365:
    @classmethod
    def day_count(self, from_dates : np.ndarray, to_dates : np.ndarray):
        return np.timedelta64(datetime.timedelta(days=365))


class Numerator30:
    @classmethod
    def day_count(self, from_dates: np.ndarray, to_dates: np.ndarray):
        return (
            360 * (NumpyDateUtils.get_years(to_dates) - NumpyDateUtils.get_years(from_dates))
            + 30 * (NumpyDateUtils.get_months(to_dates) - NumpyDateUtils.get_months(from_dates))
            + (NumpyDateUtils.get_days(to_dates) - NumpyDateUtils.get_days(from_dates))
        )


class Denominator360:
    @classmethod
    def day_count(self, from_dates: np.ndarray, to_dates: np.ndarray):
        return np.timedelta64(datetime.timedelta(days=360))


class Numerator30E(Numerator30):
    @classmethod
    def day_count(self, from_dates: np.ndarray, to_dates: np.ndarray):
        from_dates = np.where(NumpyDateUtils.get_days(from_dates) == 31, from_dates - np.timedelta64(1, "D"), from_dates)
        to_dates = np.where(NumpyDateUtils.get_days(to_dates) == 31, to_dates - np.timedelta64(1, "D"), to_dates)
        return super().day_count(from_dates, to_dates)
