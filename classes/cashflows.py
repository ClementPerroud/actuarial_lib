from typing import Any
import numpy as np
import pandas as pd
import datetime


class Cashflows:
    def __init__(self, dates : np.ndarray, amounts : np.ndarray):
        self.data = pd.Series(index = dates, data = amounts, dtype= float)
        if not self.data.index.is_monotonic_increasing: self.data.sort_index(inplace= True)
        if not self.data.index.is_unique: self.data = self.data.groupby(level=0).sum()
        self.root = self

    @classmethod
    def _create(cls, parent: "Cashflows", data):
        """Creates a filtered view of the original Cashflows object."""
        instance = cls.__new__(cls)  # Creates an uninitialized instance
        instance.data = data  # Ensure a copy to avoid side effects
        instance.root = parent.root
        return instance

    # --- Encapsulating `.loc` and `.iloc` ---
    @property
    def loc(self):return _LocIndexer(self)
    @property
    def iloc(self):return _IlocIndexer(self)
    @property
    def dates(self): return self.data.index.values
    @property
    def amounts(self): return self.data.values
    
    def __repr__(self): return repr(self.data)

    def to_series(self): return self.data

    def __mul__(self, other): return Cashflows._create(parent = self, data = self.data.__mul__(other))
    def __rmul__(self, other): return Cashflows._create(parent = self, data = self.data.__rmul__(other))
    def __sub__(self, other): return Cashflows._create(parent = self, data = self.data.__neg__(other))
    def __sub__(self, other): return Cashflows._create(parent = self, data = self.data.__sub__(other))
    def __truediv__(self, other): return Cashflows._create(parent = self, data = self.data.__truediv__(other))
    def __len__(self): return self.data.__len__()

    def __add__(self, other):
        """Combine two Cashflows instances and return a new instance with sorted and grouped data."""
        if not isinstance(other, Cashflows):
            return Cashflows._create(parent = self, data = self.data.__add__(other))

        combined_data = self.data.add(other.data, fill_value=0)  # Ensures missing dates are handled
        return Cashflows._create(self, combined_data)
    
    def add_cashflow(self, date, amount):
        new_cashflow = pd.Series(data=[amount], index=[date], dtype= float)
        new_data = self.data.add(new_cashflow, fill_value= 0)
        return Cashflows._create(parent = self, data=new_data)


class _LocIndexer:
    """
    Encapsulates cashflows.data.loc[...] access. 
    Returns either a Cashflows object (slice) or a scalar (single value).
    """
    def __init__(self, parent: "Cashflows"):
        self.parent = parent

    def __getitem__(self, key):
        result = self.parent.data.loc[key]
        if isinstance(result, pd.Series):
            # Return a new Cashflows instance
            return Cashflows._create(self.parent, result)
        else:
            # It's a single value
            return result

    def __setitem__(self, key, value):
        # Allow writing to the underlying data
        self.parent.data.loc[key] = value


class _IlocIndexer:
    """
    Encapsulates cashflows.data.iloc[...] access.
    """
    def __init__(self, parent: "Cashflows"):
        self.parent = parent

    def __getitem__(self, key):
        result = self.parent.data.iloc[key]
        if isinstance(result, pd.Series):
            return Cashflows._create(self.parent, result)
        else:
            return result

    def __setitem__(self, key, value):
        self.parent.data.iloc[key] = value

if __name__ == "__main__":
    dates = np.arange(
        datetime.datetime(2020, 1, 1),
        datetime.datetime(2021, 1, 1),
        datetime.timedelta(days = 1)
    )
    cashflows = Cashflows(dates = dates, amounts = [1 for _ in dates])

    filtered_cashflows = cashflows.loc[datetime.datetime(2020, 1, 10):]

    filtered_cashflows.add_cashflow(date = datetime.datetime(2020, 1, 1), amount = 2)
    print(filtered_cashflows)

