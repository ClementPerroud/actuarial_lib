from classes.bond_position import BondPosition
from calculators.bond_position import BondPositionCalculator
from services.amortization import LinearAmortizationService
from services.bond_cashflow import BaseCashflowService
from services.accrued_coupon import  NoAccruedCouponService
from services.inflation import AbstractInflationService, NoInflationService
from factories.amortization.amortization import AbstractAmortizationFactory

class LinearAmortizationFactory(AbstractAmortizationFactory):
    def __init__(self, inflation_service : AbstractInflationService= NoInflationService()):
        super().__init__(inflation_service=inflation_service)
        self.accrued_coupon_service = NoAccruedCouponService() #No used because we don't compute future coupons => no accrued coupon needed
        self.bond_cashflow_service = BaseCashflowService(accrued_coupon_service = self.accrued_coupon_service)
        self.amortization_service = LinearAmortizationService(bond_cashflow_service = self.bond_cashflow_service)

    def create_bond_position_calculator(self, bond_position : BondPosition):
        bond = self.create_bond_calculator(bond = bond_position.bond)
        bond_position = BondPositionCalculator(bond_position=bond_position, bond = bond)
        bond_position.amortization_service = self.amortization_service
        return bond_position
