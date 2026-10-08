
from pathlib import Path
from typing import Any

import pandas as pd


def save_trade_report(
    trades: list[dict[str, Any]],
    output_path: str = "reports/trade_report.xlsx",
) -> str:
    """Save trade records to an Excel report."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    dataframe = pd.DataFrame(trades)
    dataframe.to_excel(path, index=False)

    return str(path)