from enum import Enum


#  Enum class to handle different versions of Razorpay API
class Version(Enum):
    V1 = 1
    V2 = 2

# A set of valid values for the 'expand' parameter for quick lokups 

# (order.py)
VALID_EXPAND_VALUES_ORDERS = {
    "payments",
    "payments.card",
    "transfers",
    "virtual_account",
}

# (payments.py)
VALID_EXPAND_VALUES_PAYMENTS = {
 'card', 'emi', 'transaction', 'transaction.settlement', 'refunds', 'offers', 'token', 'settlement'
}

