import pandas as pd
import numpy as np
import datetime
from utils.lru_cache import lru_cache

from abc import ABC, abstractmethod

from classes.cashflows import Cashflows
from classes.bond_position import BondPosition
from calculators.bond_position import BondPositionCalculator
from services.service import Service
from services.accrued_coupon import AbstractAccruedCouponService, LinearAccruedCouponService, NoAccruedCouponService
from settings import medium_lru_cache_size

from utils.speed_analyser import step_timer

class AbstractCashflowService(Service, ABC):
    @abstractmethod
    def compute_future_coupons(self, bond_position : BondPositionCalculator, date : datetime.datetime, _apply_inflation = True) -> Cashflows:
        ...
    
    @abstractmethod
    def compute_future_redemptions(self, bond_position : BondPositionCalculator, date : datetime.datetime, _apply_inflation = True) -> Cashflows:
        ...
    
    @abstractmethod
    def compute_future_cashflows(self, bond_position : BondPositionCalculator, date : datetime.datetime) -> Cashflows:
        ...


class BaseCashflowService(AbstractCashflowService):
    def __init__(self, accrued_coupon_service : AbstractAccruedCouponService = None):
        self.accrued_coupon_service = accrued_coupon_service if accrued_coupon_service is not None else LinearAccruedCouponService()

    @lru_cache(maxsize = medium_lru_cache_size)
    def compute_future_coupons(self, bond_position : BondPositionCalculator, date : datetime.datetime, _apply_inflation = True):
        future_coupons = self._transform_cashflows(bond_position = bond_position, cashflows = bond_position.bond.coupons, date = date)
        if _apply_inflation: future_coupons = bond_position.bond.inflation_service.compute_adjusted_cashflows(bond_position= bond_position, cashflows=future_coupons, computation_date=date)
        return future_coupons
    
    @lru_cache(maxsize = medium_lru_cache_size)
    def compute_future_redemptions(self, bond_position : BondPositionCalculator, date : datetime.datetime, _apply_inflation = True):
        future_redemptions = self._transform_cashflows(bond_position = bond_position, cashflows = bond_position.bond.redemptions, date = date)
        if _apply_inflation: future_redemptions = bond_position.bond.inflation_service.compute_adjusted_cashflows(bond_position= bond_position, cashflows=future_redemptions, computation_date=date)
        return future_redemptions
    
    def compute_future_cashflows(self, bond_position : BondPositionCalculator, date : datetime.datetime):
        coupons = self.compute_future_coupons(bond_position= bond_position, date = date, _apply_inflation = False)
        redemptions = self.compute_future_redemptions(bond_position= bond_position, date = date, _apply_inflation = False)
        cashflows = coupons + redemptions
        # Adding Accrued coupon
        accrued_coupon_amount = self.accrued_coupon_service.compute_accrued_coupon(bond_position= bond_position, date= date) 
        if accrued_coupon_amount >= 1E-6: cashflows = cashflows.add_cashflow(date = date, amount = - accrued_coupon_amount)

        cashflows = bond_position.bond.inflation_service.compute_adjusted_cashflows(bond_position= bond_position, cashflows=cashflows, computation_date=date)
        return cashflows
    
    def _transform_cashflows(self, bond_position : BondPositionCalculator, cashflows : Cashflows, date : datetime.datetime, _apply_inflation = True):
        future_cashflows = cashflows.loc[
            date + datetime.timedelta(seconds=1) : 
            bond_position.bond.maturity_date + datetime.timedelta(seconds=1)
        ]  / bond_position.bond.base * bond_position.nominal
        return future_cashflows
    


class DailyCouponCashflowService(BaseCashflowService):
    def __init__(self):
        super().__init__(accrued_coupon_service = NoAccruedCouponService())

    @lru_cache(maxsize = medium_lru_cache_size)
    def compute_day_coupons(self, bond_position : BondPositionCalculator) -> Cashflows:
        coupon_dates = bond_position.bond.coupons.dates
        coupon_amounts = bond_position.bond.coupons.amounts

        # TODO : Modify with time conventions
        diff_dates = np.diff(coupon_dates, prepend= [np.datetime64()])
        diff_dates[0] = coupon_dates[0] - np.datetime64(bond_position.bond.emission_date)

        diff_dates = np.maximum(diff_dates, np.timedelta64(1, 'D'))

        nb_days_diff = diff_dates / np.timedelta64(1, 'D')

        coupon_daily_amounts = coupon_amounts / nb_days_diff
        
        daily_coupon_dates = np.arange(
                start = bond_position.bond.emission_date + datetime.timedelta(days = 1),
                stop = coupon_dates[-1] + np.timedelta64(1, 'D'),
                step = np.timedelta64(1, 'D'),
                dtype= "datetime64[s]"
            )
        daily_coupon_amounts = np.zeros(shape=daily_coupon_dates.shape, dtype= float)

        index = 0
        for i, nb_days in enumerate(nb_days_diff):
            daily_coupon_amounts[int(index): int(index + nb_days)] = coupon_daily_amounts[i]
            index += nb_days


        return Cashflows(dates=daily_coupon_dates, amounts = daily_coupon_amounts)
    
    def compute_future_coupons(self, bond_position : BondPositionCalculator, date : datetime.datetime, _apply_inflation = True):
        daily_coupons = self.compute_day_coupons(bond_position = bond_position)
        future_daily_coupons = self._transform_cashflows(bond_position = bond_position, cashflows = daily_coupons, date = date)
        if _apply_inflation: future_daily_coupons = bond_position.bond.inflation_service.compute_adjusted_cashflows(bond_position= bond_position, cashflows=future_daily_coupons, computation_date=date)
        return future_daily_coupons