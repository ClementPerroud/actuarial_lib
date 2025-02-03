import numpy as np
import pandas as pd
import datetime
import matplotlib.pyplot as plt
from dateutil.relativedelta import relativedelta
from tqdm.auto import tqdm

import matplotlib.pyplot as plt

from classes.bond_position import BondPosition
from calculators.bond_position import BondPositionCalculator
from classes.bond import Bond
from classes.time_convention import TimeConvention
from classes.cashflows import Cashflows
from services.accrued_coupon import LinearAccruedCouponService, ActuarialAccruedCouponService
from factories.amortization.actuarial import ClassicActuarialAmortizationFactory, DailyCouponActuarialAmortizationFactory
from factories.amortization.linear import LinearAmortizationFactory
from factories.amortization.full import FullAmortizationFactory
from factories.bond.coupon import CouponFactory

# Bond Parameters
emission_date = datetime.datetime(2020, 1, 1)
maturity_date = datetime.datetime(2030, 1, 1)
time_convention = TimeConvention.ACT_ACT

coupons = CouponFactory().create_coupons(coupon_rate= 5, emission_date= emission_date, maturity_date=maturity_date, frequency=CouponFactory.Frequency.YEARLY)
redemptions = Cashflows(dates = [maturity_date], amounts= [100])

bond = Bond(
    emission_date= emission_date,
    maturity_date= maturity_date,
    redemptions= redemptions,
    coupons= coupons,
    time_convention= time_convention
)

# Position Parameters
acquisition_date = datetime.datetime(2022,6,1)
nominal = 100_000
acquisition_price_clean_100 = 98

bond_position = BondPosition(
    bond = bond,
    nominal=nominal,
    acquisition_date= acquisition_date,
    acquisition_clean_price= nominal*acquisition_price_clean_100/100
)


# Case 1 : Coupon Couru
factory = ClassicActuarialAmortizationFactory()
bond_position_calculator = factory.create_bond_position_calculator(bond_position=bond_position)

amortization = bond_position_calculator.compute_amortization(date = datetime.datetime(2026,1,5))
amortization_profile = bond_position_calculator.compute_amortization_profile()
amortization_profile.plot(color = "r")


# Case 2 : Coupon Couru Actuarial
factory = ClassicActuarialAmortizationFactory(accrued_coupon_service = ActuarialAccruedCouponService())
bond_position_calculator = factory.create_bond_position_calculator(bond_position=bond_position)

amortization_profile = bond_position_calculator.compute_amortization_profile()
amortization_profile.plot(color = "g")


# # Case 3 : Daily Coupon
factory = DailyCouponActuarialAmortizationFactory()
bond_position_calculator = factory.create_bond_position_calculator(bond_position=bond_position)

amortization_profile = bond_position_calculator.compute_amortization_profile(interval= relativedelta(months = 1))
amortization_profile.plot(color = "b")


# Case 4 : Linear
factory = LinearAmortizationFactory()
bond_position_calculator = factory.create_bond_position_calculator(bond_position=bond_position)

amortization_profile = bond_position_calculator.compute_amortization_profile(interval= relativedelta(months = 1))
amortization_profile.plot(color = "orange")


# Case 5 : Full
factory = FullAmortizationFactory()
bond_position_calculator = factory.create_bond_position_calculator(bond_position=bond_position)

amortization_profile = bond_position_calculator.compute_amortization_profile(interval= relativedelta(months = 1))
amortization_profile.plot(color = "yellow")

plt.show()