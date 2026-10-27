"""
Central configuration module for Financial Operations Automation.
Defines directory paths, database settings, and business tolerance rules.
"""

from pathlib import Path

# Base project paths (OS-independent)
BASE_DIR: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = BASE_DIR / "data"
SYNTHETIC_DATA_DIR: Path = DATA_DIR / "synthetic"
OUTPUT_DATA_DIR: Path = DATA_DIR / "outputs"
DB_PATH: Path = OUTPUT_DATA_DIR / "financial_ops.db"
LOG_FILE_PATH: Path = OUTPUT_DATA_DIR / "execution.log"

# Ensure required data directories exist at runtime
SYNTHETIC_DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Financial Reconciliation Business Parameters
AMOUNT_TOLERANCE: float = 0.01  # Acceptable rounding difference in currency units (e.g., R$ 0.01)
MAX_SETTLEMENT_DAYS_LAG: int = 5  # Maximum expected calendar days between capture and settlement
SUPPORTED_CURRENCIES: tuple[str, ...] = ("BRL", "USD")
VALID_PAYMENT_METHODS: tuple[str, ...] = ("CREDIT_CARD", "DEBIT_CARD", "PIX", "BOLETO")

# Required Schema Definitions
REQUIRED_INTERNAL_COLUMNS: tuple[str, ...] = (
    "transaction_id",
    "transaction_date",
    "expected_settlement_date",
    "merchant_id",
    "payment_method",
    "gross_amount",
    "fee_amount",
    "net_amount",
    "currency",
    "status",
)

REQUIRED_SETTLEMENT_COLUMNS: tuple[str, ...] = (
    "settlement_id",
    "transaction_id",
    "settlement_date",
    "settled_gross_amount",
    "settled_fee_amount",
    "settled_net_amount",
    "bank_reference",
    "payout_status",
)