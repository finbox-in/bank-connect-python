def make_account_id_filter(account_id):
    def account_id_filter(row):
        return row['account_id'] == account_id
    return account_id_filter
