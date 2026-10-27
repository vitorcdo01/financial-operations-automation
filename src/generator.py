"""
Deterministic synthetic data generator for Financial Operations Automation.
Creates realistic, entirely fictitious internal transaction ledgers (Dataset A)
and external settlement reports (Dataset B) with controlled operational anomalies.
"""

from datetime import date, timedelta
from pathlib import Path
import random
from typing import Tuple

import pandas as pd

from src.config import SYNTHETIC_DATA_DIR

# Fee schedule by payment method (fictitious standard rates)
FEE_RATES: dict[str, float] = {
    "PIX": 0.0099,         # 0.99%
    "DEBIT_CARD": 0.0149,  # 1.49%
    "BOLETO": 0.0199,      # 1.99%
    "CREDIT_CARD": 0.0349, # 3.49%
}

SETTLEMENT_LAG_DAYS: dict[str, int] = {
    "PIX": 0,
    "DEBIT_CARD": 1,
    "BOLETO": 2,
    "CREDIT_CARD": 3,
}


def generate_synthetic_datasets(
    num_base_records: int = 120,
    seed: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generates deterministic synthetic datasets for internal transactions (Dataset A)
    and external settlement records (Dataset B), injecting controlled anomalies
    for data processing, validation, and reconciliation testing.
    """
    rng = random.Random(seed)
    start_date = date(2026, 9, 1)
    merchants = [f"MCH-{i:03d}" for i in range(1, 16)]
    payment_methods = list(FEE_RATES.keys())

    internal_rows: list[dict] = []
    settlement_rows: list[dict] = []

    for idx in range(1, num_base_records + 1):
        tx_id = f"TXN-2026-{idx:05d}"
        tx_date = start_date + timedelta(days=rng.randint(0, 25))
        method = rng.choice(payment_methods)
        merchant = rng.choice(merchants)

        gross = round(rng.uniform(25.0, 2500.0), 2)
        fee = round(gross * FEE_RATES[method], 2)
        net = round(gross - fee, 2)

        expected_lag = SETTLEMENT_LAG_DAYS[method]
        expected_settlement = tx_date + timedelta(days=expected_lag)

        # Base Internal Record (Dataset A)
        internal_record = {
            "transaction_id": tx_id,
            "transaction_date": tx_date.isoformat(),
            "expected_settlement_date": expected_settlement.isoformat(),
            "merchant_id": merchant,
            "payment_method": method,
            "gross_amount": gross,
            "fee_amount": fee,
            "net_amount": net,
            "currency": "BRL",
            "status": "CAPTURED",
        }

        # Base Settlement Record (Dataset B)
        stl_id = f"STL-2026-{idx:05d}"
        bank_ref = f"BNK-{rng.randint(100000, 999999)}"
        settlement_record = {
            "settlement_id": stl_id,
            "transaction_id": tx_id,
            "settlement_date": expected_settlement.isoformat(),
            "settled_gross_amount": gross,
            "settled_fee_amount": fee,
            "settled_net_amount": net,
            "bank_reference": bank_ref,
            "payout_status": "PAID",
        }

        # Controlled Anomaly Injection based on record index ranges
        # 1. Records 1 to 80: Standard clean matches (with a few 1-cent rounding cases)
        if 1 <= idx <= 80:
            if idx in (10, 20, 30):
                # Sub-cent rounding difference (+0.01) within tolerance
                settlement_record["settled_net_amount"] = round(net + 0.01, 2)
            internal_rows.append(internal_record)
            settlement_rows.append(settlement_record)

        # 2. Records 81 to 90: Amount Mismatch (Higher fee / divergent net settled)
        elif 81 <= idx <= 90:
            extra_fee = round(rng.uniform(2.50, 18.00), 2)
            settlement_record["settled_fee_amount"] = round(fee + extra_fee, 2)
            settlement_record["settled_net_amount"] = round(gross - settlement_record["settled_fee_amount"], 2)
            internal_rows.append(internal_record)
            settlement_rows.append(settlement_record)

        # 3. Records 91 to 96: Settlement Date Mismatch (Delayed beyond MAX_SETTLEMENT_DAYS_LAG=5)
        elif 91 <= idx <= 96:
            delayed_date = tx_date + timedelta(days=rng.randint(7, 14))
            settlement_record["settlement_date"] = delayed_date.isoformat()
            internal_rows.append(internal_record)
            settlement_rows.append(settlement_record)

        # 4. Records 97 to 104: Missing in Settlement (Captured internally, never settled)
        elif 97 <= idx <= 104:
            internal_rows.append(internal_record)
            # Intentionally omitted from settlement_rows

        # 5. Records 105 to 108: Duplicate Records in Internal or Settlement
        elif 105 <= idx <= 108:
            internal_rows.append(internal_record)
            settlement_rows.append(settlement_record)
            if idx in (105, 106):
                # Duplicate transaction_id in Internal Ledger (Dataset A)
                internal_rows.append(internal_record.copy())
            else:
                # Duplicate transaction_id in Settlement Report (Dataset B)
                dup_stl = settlement_record.copy()
                dup_stl["settlement_id"] = f"STL-DUP-{idx:05d}"
                settlement_rows.append(dup_stl)

        # 6. Records 109 to 114: Data Formatting Noise (whitespace, lowercase, slash dates)
        elif 109 <= idx <= 114:
            internal_record["transaction_id"] = f"  {tx_id.lower()} "
            internal_record["payment_method"] = f" {method.lower()} "
            internal_record["transaction_date"] = tx_date.strftime("%d/%m/%Y")
            internal_rows.append(internal_record)
            settlement_rows.append(settlement_record)

        # 7. Records 115 to 120: Data Validation Failures (Invalid business rules)
        elif 115 <= idx <= 120:
            if idx == 115:
                internal_record["merchant_id"] = None  # Missing required field
            elif idx == 116:
                internal_record["gross_amount"] = -150.00  # Negative transaction amount
            elif idx == 117:
                internal_record["net_amount"] = round(gross - fee + 50.00, 2)  # Math inconsistency
            elif idx == 118:
                internal_record["currency"] = "EUR"  # Unsupported currency
            elif idx == 119:
                internal_record["payment_method"] = "CRYPTO_TOKEN"  # Invalid payment method
            elif idx == 120:
                internal_record["transaction_date"] = "2026-13-45"  # Invalid date
            internal_rows.append(internal_record)

    # 8. Add Unexpected Settlement Records (Orphan settlements in Dataset B with no internal match)
    for orphan_idx in range(1, 5):
        orphan_date = start_date + timedelta(days=10 + orphan_idx)
        orphan_gross = round(rng.uniform(100.0, 900.0), 2)
        orphan_fee = round(orphan_gross * 0.02, 2)
        settlement_rows.append(
            {
                "settlement_id": f"STL-ORPHAN-{orphan_idx:03d}",
                "transaction_id": f"TXN-UNKNOWN-{orphan_idx:04d}",
                "settlement_date": orphan_date.isoformat(),
                "settled_gross_amount": orphan_gross,
                "settled_fee_amount": orphan_fee,
                "settled_net_amount": round(orphan_gross - orphan_fee, 2),
                "bank_reference": f"BNK-99900{orphan_idx}",
                "payout_status": "PAID",
            }
        )

    df_internal = pd.DataFrame(internal_rows)
    df_settlement = pd.DataFrame(settlement_rows)

    return df_internal, df_settlement


def save_synthetic_datasets(
    output_dir: Path = SYNTHETIC_DATA_DIR,
    num_base_records: int = 120,
    seed: int = 42,
) -> dict[str, Path]:
    """
    Generates and saves synthetic datasets in both CSV and Excel (.xlsx) formats
    to demonstrate multi-format ingestion capabilities.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    df_internal, df_settlement = generate_synthetic_datasets(
        num_base_records=num_base_records,
        seed=seed,
    )

    paths = {
        "internal_csv": output_dir / "internal_transactions.csv",
        "settlement_csv": output_dir / "settlement_records.csv",
        "internal_xlsx": output_dir / "internal_transactions.xlsx",
        "settlement_xlsx": output_dir / "settlement_records.xlsx",
    }

    df_internal.to_csv(paths["internal_csv"], index=False, encoding="utf-8")
    df_settlement.to_csv(paths["settlement_csv"], index=False, encoding="utf-8")
    df_internal.to_excel(paths["internal_xlsx"], index=False)
    df_settlement.to_excel(paths["settlement_xlsx"], index=False)

    return paths


if __name__ == "__main__":
    generated_paths = save_synthetic_datasets()
    print("Synthetic datasets successfully generated:")
    for label, file_path in generated_paths.items():
        print(f"  - {label}: {file_path}")