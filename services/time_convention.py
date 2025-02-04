
import datetime
from abc import ABC, abstractmethod
import numpy as np
from utils.numpy_date_utils import NumpyDateUtils

from classes.cashflows import Cashflows
from services.service import Service
from calculators.bond_position import BondPositionCalculator

class AbstractTimeConventionService(Service, ABC):
    @abstractmethod
    def year_count(self, bond_position : BondPositionCalculator, from_dates: np.ndarray, to_dates: np.ndarray):
        ...

class TimeConventionActActService:
    """
    An optimized version of your Act/Act day count.
    """

    def year_count(self, bond_position : BondPositionCalculator, from_dates: np.ndarray, to_dates: np.ndarray):
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
        year_count_start = day_count_start.astype(float) / np.where((1970 + from_years_up.astype(int)-1) % 4 == 0, 366.0, 365.0)

        # b. Middle :  1-1-2008 to 1-1-2019
        year_count_middle = (to_years_down - from_years_up).astype(float)

        # c. End :  1-1-2019 to 28-09-2019
        day_count_end = to_dates.astype('datetime64[D]') - to_years_down.astype('datetime64[D]')  
        year_count_end = day_count_end.astype(float) / np.where((1970 + to_years_down.astype(int)) % 4 == 0, 366.0, 365.0)

        return year_count_start + year_count_middle + year_count_end

class TimeConventionActActISDAService(AbstractTimeConventionService):
    def __init__(self):
        self.time_convention_service_helper = TimeConventionExact365Service()
        self._frequencies_allowed = [0.5, 1, 2, 4, 12] # nb coupons per year
        self._tolerance = 1E-6
    
    def round_to_nearest(self, value, options):
        # Rounds the given value to the nearest number from the options list.
        return min(options, key=lambda x: abs(x - value))
    
    def _compute_frequency(self, cashflows : Cashflows):
        time_delta = cashflows.dates[-1] - cashflows.dates[0]
        nb_cashflows = len(cashflows.dates)
        frequency =  nb_cashflows / time_delta.astype('timedelta64[Y]').astype(int)
        return self.round_to_nearest(frequency, self._frequencies_allowed)  
    
    def year_count(self, bond_position : BondPositionCalculator, from_dates : np.ndarray, to_dates  : np.ndarray):
        # 1. Identify negative intervals (swap them).
        frequency = self._compute_frequency(bond_position.bond.coupons)

        # 2. Precompute years for both:
  
        from_coupon_index = bond_position.bond.coupons.dates.searchsorted(from_dates, side = "right") 
        to_coupon_index = bond_position.bond.coupons.dates.searchsorted(to_dates, side = "right")

        # Compute the coupon start date = previous coupon date when available else the emission date.
        n = len(bond_position.bond.coupons)
        from_coupon_start_date = np.where(from_coupon_index > 0, bond_position.bond.coupons.dates[np.maximum(from_coupon_index - 1, 0)], np.datetime64(bond_position.bond.emission_date))
        from_coupon_end_date = np.where(from_coupon_index < n, bond_position.bond.coupons.dates[np.minimum(from_coupon_index, n-1)], np.datetime64(bond_position.bond.maturity_date))
        
        to_coupon_start_date = np.where(to_coupon_index > 0, bond_position.bond.coupons.dates[np.maximum(to_coupon_index - 1, 0)], np.datetime64(bond_position.bond.emission_date))
        to_coupon_end_date = np.where(to_coupon_index < n, bond_position.bond.coupons.dates[np.minimum(to_coupon_index, n-1)], np.datetime64(bond_position.bond.maturity_date))

        year_count = 0
        # 3. Compute years counts (eg. 12-06-2007 -> 28-09-2019)
        # a. Start :  12-06-2007 to 1-1-2008
        day_count = (from_dates - from_coupon_start_date).astype(float)
        day_count_coupon_period = (from_coupon_end_date - from_coupon_start_date).astype(float)
        year_count -= np.where(day_count_coupon_period >= self._tolerance, day_count / np.maximum(day_count_coupon_period, self._tolerance) / frequency, 0)

        # b. Middle :  1-1-2008 to 1-1-2019
        year_count += (to_coupon_index - from_coupon_index).astype(float) / frequency

        # c. End :  1-1-2019 to 28-09-2019
        day_count = (to_dates - to_coupon_start_date).astype(float)
        day_count_coupon_period = (to_coupon_end_date - to_coupon_start_date).astype(float)
        year_count += np.where(day_count_coupon_period >= self._tolerance, day_count / np.maximum(day_count_coupon_period, self._tolerance)  / frequency, 0)


        return year_count
        # # 3. Compute years counts (eg. 12-06-2007 -> 28-09-2019)
        # # a. Start :  12-06-2007 to 1-1-2008
        # day_count_start = from_years_up.astype('datetime64[D]') - from_dates.astype('datetime64[D]')
        # year_count_start = day_count_start.astype(float) / np.where((1970 + from_years_up.astype(int)-1) % 4 == 0, 366.0, 365.0)

        # # b. Middle :  1-1-2008 to 1-1-2019
        # year_count_middle = (to_years_down - from_years_up).astype(float)
        # # print(year_count_middle)

        # # c. End :  1-1-2019 to 28-09-2019
        # day_count_end = to_dates.astype('datetime64[D]') - to_years_down.astype('datetime64[D]')  
        # year_count_end = day_count_end.astype(float) / np.where((1970 + to_years_down.astype(int)) % 4 == 0, 366.0, 365.0)

        # # print("End", day_count_end, year_count_end)
        # return year_count_start + year_count_middle + year_count_end

class TimeConvention30360Service(AbstractTimeConventionService):
    def year_count(self, bond_position : BondPositionCalculator, from_dates: np.ndarray, to_dates: np.ndarray):
        return Numerator30.day_count(
            from_dates=from_dates, to_dates=to_dates
        ) / Denominator360.day_count(from_dates=from_dates, to_dates=to_dates)


class TimeConvention30E360Service(AbstractTimeConventionService):
    def year_count(self, bond_position : BondPositionCalculator, from_dates: np.ndarray, to_dates: np.ndarray):
        return Numerator30E.day_count(
            from_dates=from_dates, to_dates=to_dates
        ) / Denominator360.day_count(from_dates=from_dates, to_dates=to_dates)


class TimeConventionExact360Service(AbstractTimeConventionService):
    def year_count(self, bond_position : BondPositionCalculator, from_dates: np.ndarray, to_dates: np.ndarray):
        return NumeratorExact.day_count(
            from_dates=from_dates, to_dates=to_dates
        ) / Denominator360.day_count(from_dates=from_dates, to_dates=to_dates)


class TimeConventionExact365Service(AbstractTimeConventionService):
    def year_count(self, bond_position : BondPositionCalculator, from_dates: np.ndarray, to_dates: np.ndarray):
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
    def day_count(self, bond_position : BondPositionCalculator, from_dates: np.ndarray, to_dates: np.ndarray):
        return (
            360 * (NumpyDateUtils.get_years(to_dates) - NumpyDateUtils.get_years(from_dates))
            + 30 * (NumpyDateUtils.get_months(to_dates) - NumpyDateUtils.get_months(from_dates))
            + (NumpyDateUtils.get_days(to_dates) - NumpyDateUtils.get_days(from_dates))
        )


class Denominator360:
    @classmethod
    def day_count(self, bond_position : BondPositionCalculator, from_dates: np.ndarray, to_dates: np.ndarray):
        return np.timedelta64(datetime.timedelta(days=360))


class Numerator30E(Numerator30):
    @classmethod
    def day_count(self, bond_position : BondPositionCalculator, from_dates: np.ndarray, to_dates: np.ndarray):
        from_dates = np.where(NumpyDateUtils.get_days(from_dates) == 31, from_dates - np.timedelta64(1, "D"), from_dates)
        to_dates = np.where(NumpyDateUtils.get_days(to_dates) == 31, to_dates - np.timedelta64(1, "D"), to_dates)
        return super().day_count(from_dates, to_dates)
