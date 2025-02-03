from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
import datetime
import logging

from classes.bond_position import BondPosition
from calculators.bond_position import BondPositionCalculator

from services.service import Service
from services.bond_cashflow import BaseCashflowService

class AbstractAmortizationService(Service, ABC):
    @abstractmethod
    def compute_amortization(self,
            bond_position : BondPositionCalculator,
            date: pd.Timestamp,
        ):
        ...

    @abstractmethod
    def compute_amortized_price(self,
            bond_position : BondPositionCalculator,
            date: pd.Timestamp,
        ):
        ...

    def compute_amortization_profile(self, bond_position : BondPositionCalculator, interval : datetime.timedelta):
        amortizations = []
        dates=  []
        date = bond_position.acquisition_date
        while date < bond_position.bond.maturity_date:
            amortizations.append(
                bond_position.compute_amortization(date= date)
            )
            dates.append(date)
            date += interval

        return pd.Series(index= dates, data = amortizations)

class LinearAmortizationService(AbstractAmortizationService):
    def __init__(self,  bond_cashflow_service = None):
        super().__init__()
        self.bond_cashflow_service = bond_cashflow_service if bond_cashflow_service is not None else BaseCashflowService()

    def compute_amortization(
            self,
            bond_position : BondPositionCalculator,
            date: datetime.datetime,
        ):
        # Case where the amortization date is after the maturity date or before the acquisition data. The amortization is 0 as there is no asset to amortize.
        if bond_position.bond.maturity_date <= date or date <= bond_position.acquisition_date: return 0

        total_redemption_price = self.bond_cashflow_service.compute_future_redemptions(bond_position= bond_position, date= date).amounts.sum()

        return (
            ( total_redemption_price - bond_position.acquisition_clean_price )
            * bond_position.bond.time_convention_service.year_count(from_dates = np.datetime64(bond_position.acquisition_date, "ns"), to_dates = np.datetime64(date, "ns"))
            / bond_position.bond.time_convention_service.year_count(from_dates = np.datetime64(bond_position.acquisition_date, "ns"), to_dates = np.datetime64(bond_position.bond.maturity_date, "ns"))
        )
 
    def compute_amortized_price(self, bond_position, date):
        return bond_position.acquisition_clean_price + self.compute_amortization(bond_position = bond_position, date = date)


class FullAmortizationService(AbstractAmortizationService):
    def __init__(self,  bond_cashflow_service = None):
        super().__init__()
        if bond_cashflow_service is None:
            bond_cashflow_service = BaseCashflowService()
            logging.warn(f"Initializing {self.__class__.__name__} with {bond_cashflow_service.__class__.__name__}")
        self.bond_cashflow_service = bond_cashflow_service 

    def compute_amortization(
            self,
            bond_position : BondPositionCalculator,
            date: datetime.datetime,
        ):
        # Case where the amortization date is after the maturity date or before the acquisition data. The amortization is 0 as there is no asset to amortize.
        if bond_position.bond.maturity_date <= date or date <= bond_position.acquisition_date: return 0

        total_redemption_price = self.bond_cashflow_service.compute_future_redemptions(bond_position= bond_position, date= bond_position.acquisition_date).amounts.sum()
        return (total_redemption_price - bond_position.acquisition_clean_price)
    
    def compute_amortized_price(self, bond_position : BondPositionCalculator, date : datetime.datetime):
        return self.bond_cashflow_service.compute_future_redemptions(bond_position= bond_position, date= date).amounts.sum()



class ActuarialAmortizationService(AbstractAmortizationService):
    def __init__(self, bond_cashflow_service = None):
        super().__init__()
        

        if bond_cashflow_service is None:
            bond_cashflow_service = BaseCashflowService()
            logging.warn(f"Initializing {self.__class__.__name__} with {bond_cashflow_service.__class__.__name__}")
        self.bond_cashflow_service = bond_cashflow_service
        self.full_amortization_service = FullAmortizationService(bond_cashflow_service=bond_cashflow_service)

    def compute_amortization(
            self,
            bond_position : BondPositionCalculator,
            date: datetime.datetime,
        ):

        # Case where the amortization date is after the maturity date or before the acquisition data. The amortization is 0 as there is no asset to amortize.
        if bond_position.bond.maturity_date <= date or date < bond_position.acquisition_date: return 0

        total_redemptions =  self.bond_cashflow_service.compute_future_redemptions(bond_position= bond_position, date= date).amounts.sum()
        # Case where we have nothing the amortize
        if abs(total_redemptions - bond_position.acquisition_clean_price) < 1E-3 and bond_position.bond.inflation_index is None:
            return 0
        

        # Retrieve yield rate
        amortized_price = self.compute_amortized_price(
            bond_position=bond_position,
            date=date
        )
        
        
        
        amortization = amortized_price - bond_position.acquisition_clean_price

        return amortization

    def compute_amortized_price(
        self, bond_position: BondPositionCalculator, date
    ):
        cashflows = self.bond_cashflow_service.compute_future_cashflows(
            bond_position=bond_position,
            date= date
        )
        date_np64 = np.datetime64(date)
        cashflow_dates, cashflow_amounts = cashflows.dates, cashflows.amounts

        # Compute time powers
        time_powers = bond_position.bond.time_convention_service.year_count(from_dates= date_np64, to_dates=cashflow_dates)
        
        # Actualize cashflows
        actualized_cashflow = cashflow_amounts / ((1+ bond_position.compute_yield_rate()) ** time_powers)

        amortized_price = np.sum(actualized_cashflow)

        # print("-------------------------------")
        # print("computation date", date_np64)
        # print("amounts " ,cashflow_amounts)
        # print("dates " ,cashflow_dates)
        # print("time_powers ", time_powers)
        # print("yield_rate" , bond_position._yield_rate)
        # print("discounted", actualized_cashflow)
        # print("price", amortized_price)

        return amortized_price