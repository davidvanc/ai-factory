from rich.console import Console
from rich.table import Table


def display_report(report: dict):
    console = Console()
    table = Table(title="Air Quality Health Report")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_row("City", report.get("city", "N/A"))
    table.add_row("PM2.5 (µg/m³)", str(report.get("pm25", "N/A")))
    table.add_row("PM10 (µg/m³)", str(report.get("pm10", "N/A")))
    table.add_row("Health Score (0-100)", str(report.get("score", "N/A")))
    table.add_row("Risk Level", report.get("risk_level", "N/A"))
    console.print(table)
