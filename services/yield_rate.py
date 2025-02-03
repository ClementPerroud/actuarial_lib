from abc import ABC, abstractmethod
import logging

from classes.bond import Bond
from classes.bond_position import BondPosition
from calculators.bond_position import BondPositionCalculator

from services.service import Service
from services.solver import SolverNewtonRaphsonStandard
from services.amortization import ActuarialAmortizationService

from utils.lru_cache import lru_cache
from utils.speed_analyser import step_timer
import settings

class YieldRateService(Service):
    
    def __init__(self, solver = None, amortization_service = None) -> None:
        self.solver = solver if solver is not None else SolverNewtonRaphsonStandard()

        if amortization_service is None:
            amortization_service = ActuarialAmortizationService()
            logging.warn(f"Initializing {self.__class__.__name__} with {amortization_service.__class__.__name__}")
        self.amortization_service = amortization_service

    # @lru_cache(maxsize= settings.big_lru_cache_size)
    def compute_yield_rate(self, bond_position : BondPositionCalculator):
        at_date = bond_position.acquisition_date

        if bond_position.acquisition_date < bond_position.bond.emission_date:
            at_date = bond_position.bond.emission_date
        
        if at_date >= bond_position.bond.maturity_date:
            return 0
        

        def equation_to_solve(yield_rate):
            bond_position._yield_rate = yield_rate
            return (
                self.amortization_service.compute_amortized_price(
                    bond_position=bond_position,
                    date=at_date,
                )
                - bond_position.acquisition_clean_price 
            )

        yield_rate =  self.solver.solve(equation_function=equation_to_solve)


        return yield_rate