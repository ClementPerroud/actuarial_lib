import numpy as np

class NumpyDateUtils:
    # Year methods
    @classmethod
    def years_floored(cls, dates : np.ndarray):
        return dates.astype('datetime64[Y]').astype("datetime64[s]")
    @classmethod
    def years_ceiled(cls, dates : np.ndarray):
        ceil_years = dates.astype('datetime64[Y]').astype(float) + 1
        return ceil_years.astype("datetime64[Y]").astype("datetime64[s]")
    @classmethod
    def get_years(cls, dates : np.ndarray):
        return dates.astype('datetime64[Y]').astype(float) + 1970
    
    # Month methods
    @classmethod
    def months_floored(cls, dates : np.ndarray):
        return dates.astype('datetime64[M]').astype("datetime64[s]")
    @classmethod
    def get_months(cls, dates : np.ndarray):
        return dates.astype('datetime64[M]').astype(int) % 12 + 1
    
    # Day methods
    @classmethod
    def get_days(cls, dates : np.ndarray):
        return (dates - dates.astype('datetime64[M]')).astype(int) + 1