from typing import Any
import numpy as np
import pandas as pd
import datetime
from classes.time_convention import TimeConvention
from classes.cashflows import Cashflows
from classes.security import Security


class Bond(Security):
    def __init__(
        self,
        emission_date: datetime.date,
        maturity_date: datetime.date,
        redemptions : Cashflows,
        coupons : Cashflows,
        base = 100,
        time_convention= TimeConvention,
        inflation_index=None,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.emission_date = emission_date
        self.maturity_date = maturity_date
        self.time_convention = time_convention

        self.inflation_index = inflation_index

        self.redemptions = redemptions
        self.coupons = coupons
        self.base = base


    def __eq__(self, other : Security): return hash(self.security_id) == hash(other.security_id)
    def __hash__(self): return super().__hash__()

    

    