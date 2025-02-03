import datetime
from classes.bond import Bond

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from services.inflation import AbstractInflationService
    from services.time_convention import AbstractTimeConventionService


class BondCalculator(Bond):
    def __init__(self, bond : Bond):
        super().__init__(**bond.__dict__)

    # SERVICE : TimeConventionService
    @property
    def time_convention_service(self):
        try: return self._time_convention_service
        except: raise Exception("Please provide a TimeConventionService this Bond")
    
    @time_convention_service.setter
    def time_convention_service(self, time_convention_service : "AbstractTimeConventionService"):
        self._time_convention_service = time_convention_service
        return self


    # SERVICE : InflationService
    @property
    def inflation_service(self):
        try: return self._inflation_service
        except: raise Exception("Please provide a InflationService this Bond")
    
    @inflation_service.setter
    def inflation_service(self, inflation_service : "AbstractInflationService"):
        self._inflation_service = inflation_service
        return self