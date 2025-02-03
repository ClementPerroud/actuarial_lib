from enum import Enum
import datetime
import numpy as np
from dateutil.relativedelta import relativedelta

from classes.cashflows import Cashflows
from classes.time_convention import TimeConvention
from services.time_convention import AbstractTimeConventionService
from factories.time_convention import TimeConventionFactory

class CouponFactory:
    class Frequency(Enum):
        YEARLY = relativedelta(months = 12)
        HALF_YEARLY = relativedelta(months = 6)
        QUARTERLY = relativedelta(months= 3)
        MONTHLY = relativedelta(months = 1)

    def __init__(self):
        self.time_convention_factory = TimeConventionFactory()

    def _adjust_coupons(self, date : datetime.datetime, frequency : Frequency, emission_date : datetime.datetime, time_convention : AbstractTimeConventionService):
        coupon_start_date = max(date - frequency.value, emission_date)
        theorical_year_count = (frequency.value.months + frequency.value.years * 12) / 12
        real_year_count = time_convention.year_count(np.datetime64(coupon_start_date), np.datetime64(date)) 
        return real_year_count / theorical_year_count
    def create_coupons(self,
            emission_date : datetime.datetime,
            maturity_date: datetime,
            frequency : Frequency,
            coupon_rate : float,

            adjust_coupons = False,
            adjust_first_coupon = False,
            time_convention : TimeConvention = None
        ):
        if (adjust_coupons or adjust_first_coupon) and time_convention is None:
            raise ValueError("Please provite a time_convention when using adjust_coupons = True or adjust_first_coupon = True")
        if isinstance(time_convention, TimeConvention):
            time_convention = self.time_convention_factory.create_time_convention_service(time_convention=time_convention)
        coupon_dates = []
        coupon_amounts = []
        date = maturity_date
        while date > emission_date:
            
            # Add date
            coupon_dates.append(date)

            # Compute amount
            amount = coupon_rate
            if adjust_coupons: amount *= self._adjust_coupons(date= date, frequency= frequency, emission_date= emission_date, time_convention= time_convention)
            
            coupon_amounts.append(amount)
            date -= frequency.value
        
        if adjust_first_coupon and not adjust_coupons:
            coupon_amounts[-1] = amount * self._adjust_coupons(date= date, frequency= frequency, emission_date= emission_date, time_convention= time_convention) 

        return Cashflows(dates = coupon_dates, amounts= coupon_amounts)