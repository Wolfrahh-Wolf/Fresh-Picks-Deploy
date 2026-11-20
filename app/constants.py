"""
constants.py - Fresh Picks: Application Constants
"""

# Pricing & Business Rules
MINIMUM_ORDER_AMOUNT = 100.0
FREEBIE_THRESHOLD = 500.0
FREEBIE_MULTIPLIER_50G = 50
PRICE_DIVISOR_G = 1000.0
RAZORPAY_PAISE_MULTIPLIER = 100

# Stock Thresholds
LOW_STOCK_THRESHOLD_G = 5000

# Slot Priority for Sorting
SLOT_PRIORITY = {"Morning": 1, "Afternoon": 2, "Evening": 3}

# Order Statuses
VALID_ORDER_STATUSES = {"Order Placed", "Out for Delivery", "Delivered", "Cancelled"}

# ID Base Counters
USER_ID_BASE = 1001
ADMIN_ID_BASE = 1001
PRODUCT_ID_BASE = 1001
FREE_ITEM_ID_BASE = 1001
DELIVERY_BOY_ID_BASE = 1001
ORDER_ID_BASE = 1001

# Delivery
DELIVERY_SLOTS = {"Morning", "Afternoon", "Evening"}

# OTP Defaults
DEFAULT_OTP_TTL_MINUTES = 10
