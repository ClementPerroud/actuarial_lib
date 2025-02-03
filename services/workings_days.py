import datetime


class DayOfWeek:
    Monday = 0
    Tuesday = 1
    Wednesday = 2
    Thursday = 3
    Friday = 4
    Saturday = 5
    Sunday = 6


class Month:
    January = 1
    February = 2
    March = 3
    April = 4
    May = 5
    June = 6
    July = 7
    August = 8
    September = 9
    October = 10
    November = 11
    December = 12


class DayOfYear:
    def __init__(self, month, day) -> None:
        self.month = month
        self.day = day

    def __str__(self) -> str:
        return f"DayOfYear(month={self.month}, day={self.day})"

    def __eq__(self, other) -> bool:
        return self.month == other.month and self.day == other.day

    def __gt__(self, other):
        if self.month > other.month:
            return True
        if self.month == other.month & self.day > other.day:
            return True
        return False

    def __lt__(self, other):
        if self.month < other.month:
            return True
        if self.month == other.month & self.day < other.day:
            return True
        return False

    def __ge__(self, other):
        return self.__gt__(other) or self.__eq__(other)

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)


class WorkingDaysConvention:
    def __init__(
        self,
        weekly_non_working_days=[DayOfWeek.Saturday, DayOfWeek.Sunday],
        yearly_non_working_days=[],  # List of DayOfDay
        other_non_working_days=[],  # List of datetime.date
    ):
        self.weekly_non_working_days = weekly_non_working_days
        self.yearly_non_working_days = yearly_non_working_days
        self.other_non_working_days = other_non_working_days

    def __call__(self, date: datetime.date, working_days=0):
        # We begin to check the current date (and not tomorrow !)
        working_days_to_add = working_days + 1
        date_to_check = date - datetime.timedelta(days=1)
        while working_days_to_add > 0:
            date_to_check += datetime.timedelta(days=1)
            if self.is_working_day(date_to_check):
                working_days_to_add -= 1

        return date_to_check

    def is_working_day(self, date: datetime.date):
        if date.weekday() in self.weekly_non_working_days:
            return False
        if date in self.yearly_non_working_days:
            return False
        if date in self.other_non_working_days:
            return False
        return True


if __name__ == "__main__":
    from dateutil.relativedelta import relativedelta
    import numpy as np
    import pandas as pd

    working_days_convention = WorkingDaysConvention()
    maturity_date = datetime.date(year=2044, month=8, day=26)
    interval = relativedelta(months=3)
    coupons_dates = [maturity_date]
    for i in range(1, 100):
        coupons_dates.append(working_days_convention(maturity_date - i * interval))
    print(pd.Series(coupons_dates).head(30))
