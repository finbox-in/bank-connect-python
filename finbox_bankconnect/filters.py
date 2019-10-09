import datetime

def make_account_id_filter(account_id):
    def account_id_filter(row):
        return row['account_id'] == account_id
    return account_id_filter

def make_daterange_filter(from_date, to_date):
    def daterange_filter(row):
        try:
            curr_date = datetime.datetime.strptime(row["date"], "%Y-%m-%d %H:%M:%S").date()
        except ValueError:
            # invalid date format
            return False
        check_from = True
        check_to = True
        if from_date is not None:
            check_from = from_date <= curr_date
        if to_date is not None:
            check_to = curr_date <= to_date
        return check_from and check_to
    return daterange_filter
