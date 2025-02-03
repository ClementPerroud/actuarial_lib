from abc import ABC, abstractmethod
import numpy as np
import copy
import datetime
import pandas as pd
from dateutil import tz
from dateutil.relativedelta import relativedelta

from services.service import Service

class AbstractSolver(Service, ABC):
    @abstractmethod
    def solve(self, equation_function):
        ...

class SolverNewtonRaphsonStandard(AbstractSolver):
    def __init__(
        self,
        default_start_at=0.01,
        epsilon_derivation=1e-7,
        precision=1e-6,
        max_iteration=100,
        verbose=False,
    ):
        self.epsilon_derivation = epsilon_derivation
        self.default_start_at = default_start_at
        self.precision = precision
        self.max_iteration = max_iteration
        self.verbose = verbose

    def derivation(self, x, equation_function, f_x):
        upper_evaluation = equation_function(x + self.epsilon_derivation)
        lower_evaluation = f_x
        derivation = (upper_evaluation - lower_evaluation) / self.epsilon_derivation
        return derivation

    def solve(self, equation_function, start_at=None):
        x = self.default_start_at if start_at is None else start_at
        f_x = equation_function(x)
        for i in range(self.max_iteration):
            derivation = self.derivation(x, equation_function=equation_function, f_x=f_x)
            assert abs(derivation) >= 1E-7, "Cannot perform derivation."
            new_x = (
                -f_x / self.derivation(x, equation_function=equation_function, f_x=f_x)
                + x
            )

            f_new_x = equation_function(new_x)
            deviation = np.abs(f_new_x)

            x = new_x
            f_x = f_new_x

            if deviation < self.precision:
                break
        if self.verbose:
            if i == self.max_iteration - 1:
                print(f"Max iterations reached : {i+1} with precision {deviation:1.2e}")
            else:
                print(f"Nb iteration : {i+1} ; precision : {deviation:1.2e}")
        return x


class SolverDichotomy(AbstractSolver):
    def __init__(
        self, upper_limit=1.0, lower_limit=-1 + 1e-3, precision=1e-7, max_iteration=100
    ):
        self.precision = precision
        self.upper_limit = upper_limit
        self.lower_limit = lower_limit
        self.max_iteration = max_iteration

    def solve(self, equation_function):
        upper = self.upper_limit
        lower = self.lower_limit

        # We make sur the function is increasing
        if equation_function(upper) < equation_function(lower):
            original_equation = copy.copy(equation_function)
            equation_function = lambda x: -original_equation(x)

        for i in range(self.max_iteration):
            x = (upper + lower) / 2
            if equation_function(x) > 0:
                upper = x
            else:
                lower = x

            if (upper - lower) / 2 < self.precision:
                break
        return (upper + lower) / 2


class Interpolation2DEngine:
    def __init__(self, X : list, Y : list):
        self.X = np.array(list(map(self.convert, X)))
        self.Y = np.array(Y)
        self.index_sorted = np.argsort(X)

        self.X = self.X[self.index_sorted]
        self.Y = self.Y[self.index_sorted]

        self.saved_values = {}

    def convert(self, x):
        if isinstance(x, datetime.date):
            return datetime.datetime.timestamp(
                datetime.datetime.combine(
                    x,
                    datetime.datetime.min.time(),
                    tzinfo= tz.UTC
                )
            )
        if isinstance(x, datetime.datetime):
            x.tzinfo = tz.UTC
            return datetime.datetime.timestamp(x)
        if isinstance(x, np.datetime64):
            x : np.datetime64
            return pd.Timestamp(x).timestamp()
        return x

    def interpolate(self, x):
        x = self.convert(x)
        right_index = np.searchsorted(self.X, x)
        # from -inf to x[0]
        if right_index <= 0:
            right_index = 1
        # from x[-1] to +inf
        elif right_index >= len(self.X):
            right_index = len(self.X) - 1
        left_index = right_index - 1

        alpha = (self.Y[right_index] - self.Y[left_index])/(self.X[right_index] - self.X[left_index])
        beta = (self.X[right_index] * self.Y[left_index] - self.X[left_index] * self.Y[right_index])/(self.X[right_index] - self.X[left_index])
        return alpha * x + beta

def RQI_Interpolation(date : datetime.date, indice_df : pd.Series):
    indice_df = indice_df.copy()
    date_m3 = datetime.date(year=date.year, month=date.month, day = 1) - relativedelta(months=2) - datetime.timedelta(days = 1)
    date_m2 = datetime.date(year=date.year, month=date.month, day = 1) - relativedelta(months=1) - datetime.timedelta(days = 1)
    nb_days = (datetime.date(year=date.year, month=date.month, day = 1) + relativedelta(months=1) - datetime.date(year=date.year, month=date.month, day = 1)).days

    to_string = lambda date : f"{date.year}&{date.month}"
    # print(indice_df.index)
    indice_df.index = indice_df.index.to_series().apply(to_string)
    indice_m3 = indice_df.loc[to_string(date_m3)]
    indice_m2 = indice_df.loc[to_string(date_m2)]

    return round(indice_m3 + (indice_m2 - indice_m3) * (date.day - 1)/ nb_days, 5)

def main():
    equation_to_solve = lambda x: np.cos(x) - x**3
    solver = SolverNewtonRaphsonStandard(verbose=True)
    solver.solve(equation_function=equation_to_solve)

if __name__ == "__main__":
    main()
