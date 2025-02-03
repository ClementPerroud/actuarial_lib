import datetime
import pandas as pd
from classes.bond import Bond

class BondPosition:
    def __init__(self, bond : Bond, nominal : float, acquisition_date : datetime.datetime, acquisition_clean_price : float):
        self.bond = bond
        self.nominal = nominal
        self.acquisition_date = acquisition_date
        self.acquisition_clean_price = acquisition_clean_price
    
    def __hash__(self):
        return hash((self.bond,self.nominal, self.acquisition_date, self.acquisition_clean_price))
    

