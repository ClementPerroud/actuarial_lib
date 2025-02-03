from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
import datetime
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
import logging

from classes.cashflows import Cashflows
from services.service import Service
from calculators.bond_position import BondPositionCalculator



class AbstractInflationService(Service, ABC):
    @abstractmethod
    def compute_adjusted_cashflows(self,
            bond_position : BondPositionCalculator,
            cashflows : Cashflows,
            computation_date: datetime.datetime,
        ) -> Cashflows:
        ...

class NoInflationService(AbstractInflationService):
    def compute_adjusted_cashflows(self, bond_position : BondPositionCalculator, cashflows : Cashflows, computation_date: datetime.datetime):
        return cashflows

class ForcedFixedInflationService(AbstractInflationService):
    _warning_logged = False
    _error_message = lambda computation_date : f"""
Please provide an inflation coefficient at date {computation_date} or before.
You can set it this way : 
bond_position_calculator.inflation_coefficients = {{}} # Set up
bond_position_calculator.inflation_coefficients[date] = ... # Add inflation coefficient"""
    def compute_adjusted_cashflows(self, bond_position : BondPositionCalculator, cashflows : Cashflows, computation_date: datetime.datetime):
        assert cashflows.dates[0] >= np.datetime64(computation_date), "One or several cashflow are before the computation_date. We can not apply fixed inflation ratio."
        # return bond_position.bond.inflation_coefficients[computation_date] * cashflows
        try: return bond_position.bond.inflation_coefficients[computation_date] * cashflows
        except AttributeError: 
            raise AttributeError(self.error_message(computation_date))
        except KeyError:
            # Retrieve the latest available
            dates = np.array(list(bond_position.bond.inflation_coefficients.keys()))
            last_date_index = np.searchsorted(dates, computation_date, side = "right") - 1
            if last_date_index < 0:
                raise ValueError(self._error_message(computation_date))
            last_date = dates[last_date_index]
            if not self._warning_logged:
                self._warning_logged = True
                logging.warn(f"One or some inflation coefficients are missing. The latest available coefficient has been used instead (ex : coefficient for date {computation_date} has been taken from {last_date})")
            return bond_position.bond.inflation_coefficients[last_date] * cashflows


class RecomputeWithAvailableInflationService(AbstractInflationService):
    """Inflation Service will freeze the inflation index in the futures"""
    def __init__(self, inflation_series : dict[str, pd.Series]):
        self.inflation_series = inflation_series
        for index, inflation_serie in inflation_series.items():
            self.inflation_series[index] = inflation_serie.asfreq("1ME", method ="ffill") # Make it monthly (end of the month)

    def _compute_RQIs(self, dates : pd.DatetimeIndex, inflation_serie : pd.Series):
        dates_month = dates + pd.offsets.DateOffset(days = 1) - pd.offsets.MonthBegin()

        date_m3 = dates_month - pd.offsets.DateOffset(months=2, days= 1)
        date_m2 = dates_month - pd.offsets.DateOffset(months=1, days= 1)
        
        days_in_month = dates.days_in_month

        indice_m3 = inflation_serie.asof(date_m3) # Pick last available for month -3
        indice_m2 = inflation_serie.asof(date_m2) # Pick last available for month -2

        days = dates.day
        if isinstance(dates, pd.Timestamp):
            return indice_m3 +  (indice_m2 - indice_m3) * days / days_in_month
        return indice_m3.values +  (indice_m2.values - indice_m3.values) * days.values / days_in_month.values
    
    def compute_adjusted_cashflows(self, bond_position : BondPositionCalculator, cashflows : Cashflows, computation_date: datetime.datetime):
        index = bond_position.bond.inflation_index
        if index is None: return cashflows

        RQI_cashflows = self._compute_RQIs(dates = cashflows.data.index, inflation_serie = self.inflation_series[index])
        RQI_emission_date = self._compute_RQIs(dates = pd.Timestamp(bond_position.bond.emission_date), inflation_serie = self.inflation_series[index])
        
        return cashflows * (RQI_cashflows / RQI_emission_date)

class RecomputeWithPastInflationService(RecomputeWithAvailableInflationService):
    def compute_adjusted_cashflows(self, bond_position, cashflows, computation_date):
        index = bond_position.bond.inflation_index
        if index is None: return cashflows

        past_inflation_series = self.inflation_series[index].loc[:computation_date - relativedelta(months = 2)]
        if cashflows.dates[0] >= np.datetime64(computation_date - relativedelta(months = 2)):
            RQI_cashflows = self._compute_RQIs(dates = cashflows.data.index[0], inflation_serie = past_inflation_series)
        else: RQI_cashflows = self._compute_RQIs(dates = cashflows.data.index, inflation_serie = past_inflation_series)
        RQI_emission_date = self._compute_RQIs(dates = pd.Timestamp(bond_position.bond.emission_date), inflation_serie = past_inflation_series)

        return cashflows * (RQI_cashflows / RQI_emission_date)
    