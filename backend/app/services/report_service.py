import os
import csv
from datetime import datetime, timedelta
from typing import Dict
from loguru import logger

from app.core.config import settings
from app.models.report import Report
from app.services.analytics_service import AnalyticsService


def generate_ai_insights(summary: Dict) -> str:
    total = summary.get("total_traffic", 0)
    peak_hour = summary.get("peak_hour")
    cameras = summary.get("cameras", [])

    insights = []
    insights.append(f"Weekly surveillance summary for {summary['period_start'][:10]} to {summary['period_end'][:10]}.")

    if total > 0:
        insights.append(f"Total foot traffic recorded: {total:,} people across {len(cameras)} camera(s).")

    if peak_hour is not None:
        period = "morning" if 6 <= peak_hour < 12 else "afternoon" if 12 <= peak_hour < 18 else "evening" if 18 <= peak_hour < 22 else "night"
        insights.append(f"Peak activity was observed at {peak_hour:02d}:00 ({period} hours).")

    busiest = max(cameras, key=lambda c: c["total_traffic"], default=None) if cameras else None
    if busiest:
        insights.append(f"The busiest location was '{busiest['camera_name']}' at {busiest['address']} with {busiest['total_traffic']:,} total counts.")

    quietest = min(cameras, key=lambda c: c["total_traffic"], default=None) if cameras and len(cameras) > 1 else None
    if quietest and quietest != busiest:
        insights.append(f"The least active location was '{quietest['camera_name']}' with {quietest['total_traffic']:,} total counts.")

    avg_total = sum(c["avg_count"] for c in cameras) / len(cameras) if cameras else 0
    if avg_total > 50:
        insights.append("High average occupancy detected — consider increasing patrol frequency during peak hours.")
    elif avg_total > 20:
        insights.append("Moderate traffic levels observed. Current monitoring coverage appears adequate.")
    else:
        insights.append("Low traffic levels recorded this week. System is operating in low-load mode.")

    return " ".join(insights)


async def generate_pdf_report(summary: Dict, file_path: str):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        doc = SimpleDocTemplate(file_path, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle("Title", parent=styles["Title"], fontSize=22, textColor=colors.HexColor("#1a1a2e"), alignment=TA_CENTER, spaceAfter=6)
        sub_style = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=11, textColor=colors.HexColor("#666666"), alignment=TA_CENTER, spaceAfter=20)
        h2_style = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=14, textColor=colors.HexColor("#16213e"), spaceBefore=14, spaceAfter=6)
        body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=14)

        story = []

        story.append(Paragraph("public.safeV3", title_style))
        story.append(Paragraph("Weekly Surveillance Intelligence Report", sub_style))
        story.append(Paragraph(f"Period: {summary['period_start'][:10]} → {summary['period_end'][:10]}", sub_style))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#0f3460")))
        story.append(Spacer(1, 0.4*cm))

        # Summary table
        story.append(Paragraph("Executive Summary", h2_style))
        summary_data = [
            ["Metric", "Value"],
            ["Total Cameras", str(summary["total_cameras"])],
            ["Total Traffic (week)", f"{summary['total_traffic']:,}"],
            ["Peak Hour", f"{summary['peak_hour']:02d}:00" if summary.get("peak_hour") is not None else "N/A"],
            ["Report Generated", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")],
        ]
        t = Table(summary_data, colWidths=[8*cm, 8*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f3460")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 11),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8f9fa"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.4*cm))

        # Per camera
        story.append(Paragraph("Per-Camera Analytics", h2_style))
        for cam in summary.get("cameras", []):
            story.append(Paragraph(f"📷 {cam['camera_name']} — {cam['address']}", body_style))
            cam_data = [
                ["Total Traffic", "Avg Count", "Max Count"],
                [str(cam["total_traffic"]), str(cam["avg_count"]), str(cam["max_count"])],
            ]
            ct = Table(cam_data, colWidths=[5.3*cm, 5.3*cm, 5.3*cm])
            ct.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f4fd")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(ct)
            story.append(Spacer(1, 0.2*cm))

        # AI insights
        story.append(Paragraph("AI-Generated Insights", h2_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#dee2e6")))
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph(summary.get("ai_insights", "No insights available."), body_style))

        doc.build(story)
        logger.info(f"PDF report generated: {file_path}")
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise


async def generate_csv_report(summary: Dict, file_path: str):
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Weekly Report", summary["period_start"][:10], "to", summary["period_end"][:10]])
        writer.writerow([])
        writer.writerow(["Camera ID", "Camera Name", "Address", "Total Traffic", "Avg Count", "Max Count"])
        for cam in summary.get("cameras", []):
            writer.writerow([
                cam["camera_id"], cam["camera_name"], cam["address"],
                cam["total_traffic"], cam["avg_count"], cam["max_count"],
            ])
        writer.writerow([])
        writer.writerow(["AI Insights"])
        writer.writerow([summary.get("ai_insights", "")])
    logger.info(f"CSV report generated: {file_path}")


async def create_weekly_report(db) -> Report:
    from app.models.report import Report

    now = datetime.utcnow()
    period_end = now
    period_start = now - timedelta(days=7)

    logger.info("Generating weekly report...")

    summary = await AnalyticsService.get_weekly_summary(db, period_start, period_end)
    ai_insights = generate_ai_insights(summary)
    summary["ai_insights"] = ai_insights

    os.makedirs(settings.REPORTS_DIR, exist_ok=True)
    ts = now.strftime("%Y%m%d_%H%M%S")
    pdf_path = os.path.join(settings.REPORTS_DIR, f"weekly_report_{ts}.pdf")
    csv_path = os.path.join(settings.REPORTS_DIR, f"weekly_report_{ts}.csv")

    await generate_pdf_report(summary, pdf_path)
    await generate_csv_report(summary, csv_path)

    report = Report(
        title=f"Weekly Report {period_start.strftime('%b %d')} – {period_end.strftime('%b %d, %Y')}",
        report_type="weekly",
        period_start=period_start,
        period_end=period_end,
        file_path=pdf_path,
        file_format="pdf",
        status="ready",
        ai_insights=ai_insights,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    await AnalyticsService.reset_weekly_stats(db, period_start)

    logger.info(f"Weekly report created: ID {report.id}")
    return report
