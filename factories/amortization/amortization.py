from abc import ABC, abstractmethod

from classes.bond_position import BondPosition
from classes.bond import Bond
from calculators.bond import BondCalculator
from services.inflation import AbstractInflationService, NoInflationService
from factories.time_convention import TimeConventionFactory

class AbstractAmortizationFactory(ABC):
    def __init__(self,
            inflation_service : AbstractInflationService = NoInflationService()
        ):
        self.time_convention_factory = TimeConventionFactory()
        self.inflation_service = inflation_service

    def create_bond_calculator(self, bond : Bond):
        bond_calculator = BondCalculator(bond = bond)
        bond_calculator.time_convention_service = self.time_convention_factory.create_time_convention_service(
            time_convention=bond.time_convention
        )
        bond_calculator.inflation_service = self.inflation_service
        return bond_calculator
    
    @abstractmethod
    def create_bond_position_calculator(self, bond_position : BondPosition):
        ...




