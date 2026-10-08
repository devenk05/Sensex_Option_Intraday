from pathlib import Path

path = Path("main.py")
text = path.read_text(encoding="utf-8-sig")

imports = [
    "from daily_report_archive import DailyReportArchive",
    "from daily_report_delivery import DailyReportDelivery",
    "from daily_report_dispatcher import DailyReportDispatcher",
    "from daily_report_engine import DailyReportEngine",
    "from daily_report_formatter import DailyReportFormatter",
    "from daily_report_google_sheets import DailyReportGoogleSheets",
    "from daily_report_job import DailyReportJob",
    "from daily_report_loop import DailyReportLoop",
    "from daily_report_pipeline import DailyReportPipeline",
    "from daily_report_runner import DailyReportRunner",
    "from daily_report_scheduler import DailyReportScheduler",
    "from daily_report_sender import DailyReportSender",
    "from daily_report_service import DailyReportService",
    "from daily_report_validator import DailyReportValidator",
    "from daily_summary import DailySummary",
    "from daily_summary_storage import DailySummaryStorage",
    "from daily_trade_filter import DailyTradeFilter",
    "from daily_trade_summary import DailyTradeSummary",
    "from dashboard import generate_dashboard",
    "from excel_report import save_trade_report",
    "from google_sheets_engine import append_google_sheet_row",
    "from telegram_engine import send_telegram_message",
    "from trade_pnl_calculator import TradePnLCalculator",
]

anchor = "from trade_engine import decide_trade"
if anchor not in text:
    raise SystemExit("ERROR: import anchor not found.")

for line in imports:
    if line not in text:
        text = text.replace(anchor, anchor + "\n" + line, 1)

marker = '    print("KITE_CONNECTION_OK")'
if marker not in text:
    raise SystemExit("ERROR: KITE_CONNECTION_OK anchor not found.")

block = '''

    # Daily report stack: compatible adapters for function-based engines.
    class _TelegramAdapter:
        def send_message(self, message):
            return send_telegram_message(message)

    class _GoogleSheetsAdapter:
        def send_row(self, row):
            return append_google_sheet_row(row)

    daily_scheduler = DailyReportScheduler()
    daily_summary = DailySummary()
    daily_summary_storage = DailySummaryStorage()
    daily_report_engine = DailyReportEngine(
        summary_engine=daily_summary,
        summary_storage=daily_summary_storage,
    )

    daily_pipeline = DailyReportPipeline(
        trade_filter=DailyTradeFilter(),
        report_engine=daily_report_engine,
        validator=DailyReportValidator(),
        archive=DailyReportArchive(),
    )

    daily_dispatcher = DailyReportDispatcher(
        telegram_sender=DailyReportSender(
            formatter=DailyReportFormatter(),
            telegram_engine=_TelegramAdapter(),
        ),
        google_sheets_sender=DailyReportGoogleSheets(
            sheets_engine=_GoogleSheetsAdapter(),
        ),
    )

    daily_service = DailyReportService(
        pipeline=daily_pipeline,
        dispatcher=daily_dispatcher,
    )

    daily_job = DailyReportJob(
        scheduler=daily_scheduler,
        report_service=daily_service,
    )

    daily_report_loop = DailyReportLoop(
        report_job=daily_job,
        trades_provider=TRADE_HISTORY.get_all_trades,
        interval_seconds=30,
    )

    daily_report_thread = Thread(
        target=daily_report_loop.run_forever,
        name="daily-report-loop",
        daemon=True,
    )
    daily_report_thread.start()
    print("DAILY_REPORT_LOOP_STARTED")
'''

if "DAILY_REPORT_LOOP_STARTED" not in text:
    text = text.replace(marker, marker + block, 1)

path.write_text(text, encoding="utf-8")
print("UPDATED main.py with daily report pipeline and scheduler.")
