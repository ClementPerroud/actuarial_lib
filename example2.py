import numpy as np
import pandas as pd
import datetime
import matplotlib.pyplot as plt
from tqdm.auto import tqdm

import matplotlib.pyplot as plt

from classes.bond_position import BondPosition
from calculators.bond_position import BondPositionCalculator
from classes.bond import Bond, TimeConvention
from classes.cashflows import Cashflows
from services.accrued_coupon import LinearAccruedCouponService, ActuarialAccruedCouponService, NoAccruedCouponService
from services.inflation import NoInflationService, ForcedFixedInflationService, RecomputeWithPastInflationService
from factories.amortization.actuarial import ClassicActuarialAmortizationFactory, DailyCouponActuarialAmortizationFactory
from factories.amortization.linear import LinearAmortizationFactory
from factories.amortization.full import FullAmortizationFactory
from factories.bond.coupon import CouponFactory



computation_date = datetime.datetime(2000,5, 17)
# Bond Parameters
emission_date = datetime.datetime(1999, 7, 25)
maturity_date = datetime.datetime(2029, 7, 25)
time_convention = TimeConvention.ACT_365
coupon_frequency = CouponFactory.Frequency.YEARLY
inflation_index = "ICP"


# dates = pd.date_range("2000-01-01", "2050-01-01", freq= "1MS")
# powers = np.arange(len(dates)) / 12

factory = ClassicActuarialAmortizationFactory(
    inflation_service= ForcedFixedInflationService(),
    accrued_coupon_service= LinearAccruedCouponService(),
    # inflation_service = RecomputeWithPastInflationService(
    #     {
    #         "index1" : pd.Series(index = dates, data = 1.02 ** powers),
    #         "index2" : pd.Series(index = dates, data = 1.03 ** powers)
    #     }
    # )
)

coupons = CouponFactory().create_coupons(
    coupon_rate= 3.4,
    emission_date= emission_date,
    maturity_date=maturity_date,
    frequency=coupon_frequency,
    adjust_coupons=True,
    time_convention= time_convention
)

redemptions = Cashflows(dates = [maturity_date], amounts= [100])

bond = Bond(
    emission_date= emission_date,
    maturity_date= maturity_date,
    redemptions= redemptions,
    coupons= coupons,
    time_convention= time_convention,
    inflation_index= inflation_index
)

# Position Parameters
acquisition_date = datetime.datetime(2000,5, 17)
nominal = 100
acquisition_price_clean_100 = 93.0652726

bond_position = BondPosition(
    bond = bond,
    nominal=nominal,
    acquisition_date= acquisition_date,
    acquisition_clean_price= nominal*acquisition_price_clean_100/100
)

bond_position_calculator = factory.create_bond_position_calculator(bond_position=bond_position)
bond_position_calculator.bond.inflation_coefficients = {
    acquisition_date : 1.008665031
}

amortization = bond_position_calculator.compute_amortization(date = computation_date)
yield_rate = bond_position_calculator.compute_yield_rate()

amortization_profile = bond_position_calculator.compute_amortization_profile()


print(f"Amortization : {amortization:0.2f}")
print(f"Yield Rate : {100*yield_rate:0.2f}%")


amortization_profile.plot(color = "b")
plt.show()

