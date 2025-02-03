import pandas as pd
import numpy as np
import datetime

from abc import ABC, abstractmethod
from classes.bond_position import BondPosition
from services.service import Service
from calculators.bond_position import BondPositionCalculator
from settings import medium_lru_cache_size

class AbstractAccruedCouponService(Service, ABC):
    @abstractmethod
    def compute_accrued_coupon(self, bond_position_calculator : BondPositionCalculator,  date : datetime.datetime):
        ...

    
    # @lru_cache(maxsize= medium_lru_cache_size)
    def _compute_parameters(self, bond_position : BondPositionCalculator, date : datetime.datetime):
        next_coupon_index = bond_position.bond.coupons.dates.searchsorted(np.datetime64(date), side = "right")
        amount = bond_position.bond.coupons.amounts[next_coupon_index] / bond_position.bond.base * bond_position.nominal 
        end_date = bond_position.bond.coupons.dates[next_coupon_index]
        if next_coupon_index == 0:
            start_date = bond_position.bond.emission_date
        else: 
            start_date = bond_position.bond.coupons.dates[next_coupon_index-1]

        return bond_position, amount, start_date, end_date

    

class LinearAccruedCouponService(AbstractAccruedCouponService):
    def compute_accrued_coupon(self, bond_position : BondPositionCalculator, date : datetime.datetime):
        bond_position, amount, start_date, end_date  = self._compute_parameters(bond_position=bond_position, date= date)
        if start_date == date: return 0

        start_date = np.array([start_date], dtype= 'datetime64[s]')
        end_date = np.array([end_date], dtype = "datetime64[s]") 
        date =  np.array([date], dtype= 'datetime64[s]')
        return amount * (
            bond_position.bond.time_convention_service.year_count(from_dates=start_date, to_dates=date)
            / bond_position.bond.time_convention_service.year_count(from_dates=start_date, to_dates=end_date)
        )[0]

class ActuarialAccruedCouponService(AbstractAccruedCouponService):
    def compute_accrued_coupon(self, bond_position : BondPositionCalculator, date : datetime.datetime):
        bond_position, amount, start_date, end_date  = self._compute_parameters(bond_position=bond_position, date= date)
        if start_date == date: return 0

        start_date = np.array([start_date], dtype= 'datetime64[s]')
        end_date = np.array([end_date], dtype = "datetime64[s]") 
        date =  np.array([date], dtype= 'datetime64[s]')
        delta_before_t = bond_position.bond.time_convention_service.year_count(from_dates=start_date, to_dates=date)
        delta_total =  bond_position.bond.time_convention_service.year_count(from_dates=start_date, to_dates=end_date)


        return amount *(
            ((1 + bond_position.compute_yield_rate()) ** delta_before_t - 1) 
            / ((1 + bond_position.compute_yield_rate()) ** delta_total - 1)
        )[0]


class NoAccruedCouponService(AbstractAccruedCouponService):
    def compute_accrued_coupon(self, bond_position : BondPositionCalculator, date : datetime.datetime): return 0