from abc import ABC, abstractmethod
from enum import Enum

from classes.bond_position import BondPosition
from calculators.bond_position import BondPositionCalculator
from services.yield_rate import YieldRateService
from services.amortization import ActuarialAmortizationService
from services.bond_cashflow import BaseCashflowService, DailyCouponCashflowService
from services.accrued_coupon import AbstractAccruedCouponService, LinearAccruedCouponService
from services.inflation import AbstractInflationService, NoInflationService
from factories.amortization.amortization import AbstractAmortizationFactory


class ClassicActuarialAmortizationFactory(AbstractAmortizationFactory):
    def __init__(self,
            accrued_coupon_service : AbstractAccruedCouponService = LinearAccruedCouponService(),
            inflation_service : AbstractInflationService = NoInflationService()
        ):
        super().__init__(inflation_service= inflation_service)
        self.accrued_coupon_service = accrued_coupon_service
        self.bond_cashflow_service = BaseCashflowService(accrued_coupon_service=self.accrued_coupon_service)
        self.amortization_service = ActuarialAmortizationService(bond_cashflow_service = self.bond_cashflow_service)
        self.yield_rate_service = YieldRateService(amortization_service= self.amortization_service)

    def create_bond_position_calculator(self, bond_position : BondPosition):
        bond = self.create_bond_calculator(bond = bond_position.bond)
        bond_position = BondPositionCalculator(bond_position=bond_position, bond = bond)
        bond_position.yield_rate_service = self.yield_rate_service
        bond_position.amortization_service = self.amortization_service
        return bond_position


class DailyCouponActuarialAmortizationFactory(AbstractAmortizationFactory):
    def __init__(self, inflation_service : AbstractInflationService = NoInflationService()):
        super().__init__(inflation_service= inflation_service)
        self.bond_cashflow_service = DailyCouponCashflowService()
        self.amortization_service = ActuarialAmortizationService(bond_cashflow_service = self.bond_cashflow_service)
        self.yield_rate_service = YieldRateService(amortization_service= self.amortization_service)

    def create_bond_position_calculator(self, bond_position : BondPosition):
        bond = self.create_bond_calculator(bond = bond_position.bond)
        bond_position = BondPositionCalculator(bond_position=bond_position, bond = bond)
        bond_position.yield_rate_service = self.yield_rate_service
        bond_position.amortization_service = self.amortization_service
        return bond_position
