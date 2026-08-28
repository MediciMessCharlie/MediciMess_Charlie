def infer_account_type(account_name):
    name_lower = str(account_name).lower()

    if any(keyword in name_lower for keyword in [
        "cash", "receivable", "inventory", "land",
        "building", "equipment", "asset"
    ]):
        return "ASSET"

    if any(keyword in name_lower for keyword in [
        "payable", "loan", "debt", "liability", "deposits payable"
    ]):
        return "LIABILITY"

    if any(keyword in name_lower for keyword in [
        "capital", "equity", "retained earnings", "owner"
    ]):
        return "EQUITY"

    if any(keyword in name_lower for keyword in [
        "revenue", "income", "sales", "interest income", "fee"
    ]):
        return "REVENUE"

    if any(keyword in name_lower for keyword in [
        "expense", "wages", "rent", "supplies",
        "maintenance", "courier", "cost"
    ]):
        return "EXPENSE"

    return "ASSET"