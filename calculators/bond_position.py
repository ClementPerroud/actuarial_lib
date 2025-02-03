import datetime
from classes.bond_position import BondPosition

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from services.yield_rate import YieldRateService
    from services.accrued_coupon import AbstractAccruedCouponService
    from services.amortization import AbstractAmortizationService
    from calculators.bond import BondCalculator


class BondPositionCalculator(BondPosition):
    def __init__(self, bond_position : BondPosition, bond : "BondCalculator"):
        super().__init__(**bond_position.__dict__)
        self.bond = bond
        self._yield_rate = None

    # SERVICE : YieldRateService
    @property
    def yield_rate_service(self):
        try: return self._yield_rate_service
        except: raise Exception("Please provide a YiedRateService")
    
    @yield_rate_service.setter
    def yield_rate_service(self, _yield_rate_service : "YieldRateService"): self._yield_rate_service = _yield_rate_service    

    def compute_yield_rate(self):
        if self._yield_rate is None: self._yield_rate = self.yield_rate_service.compute_yield_rate(bond_position=self)
        return self._yield_rate


    # SERVICE : YieldRateService
    @property
    def amortization_service(self):
        try: return self._amortization_service
        except: raise Exception("Please provide a AmortizationService")
   
    @amortization_service.setter
    def amortization_service(self, _amortization_service : "AbstractAmortizationService"): self._amortization_service = _amortization_service   

    def compute_amortization(self, date : datetime.datetime): return self.amortization_service.compute_amortization(bond_position=self, date= date)
    def compute_amortized_price(self, date : datetime.datetime): return self.amortization_service.compute_amortized_price(bond_position=self, date= date)
    def compute_amortization_profile(self, interval = datetime.timedelta(days = 1)): return self.amortization_service.compute_amortization_profile(bond_position=self, interval = interval)
    