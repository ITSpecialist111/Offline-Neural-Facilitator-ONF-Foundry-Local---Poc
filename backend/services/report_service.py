import os
from datetime import datetime
import json
import csv

class ReportService:
    def __init__(self, export_dir=None):
        # Default to user's Documents folder if on Windows, else local reports dir
        if not export_dir:
            user_profile = os.environ.get('USERPROFILE')
            if user_profile:
                self.export_dir = os.path.join(user_profile, 'Documents', 'FacilitatorReports')
            else:
                self.export_dir = "reports"
        else:
            self.export_dir = export_dir
            
        os.makedirs(self.export_dir, exist_ok=True)

    def generate_report(self, transcript, insights, summary, agenda_topic):
        """
        Generates a Markdown report and saves it to the export directory.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"Meeting_Report_{timestamp}.md"
        filepath = os.path.join(self.export_dir, filename)
        
        content = f"""# Meeting Report
**Date**: {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Topic**: {agenda_topic}

## Executive Summary
{summary if summary else "No summary generated."}

## Key Insights & Action Items
"""
        
        # Group insights by type
        for insight in insights:
            content += f"- **{insight.get('type', 'Info')}**: {insight.get('text', '')}\n"

        content += "\n## Transcript\n"
        for msg in transcript:
            role = msg.get('role', 'Unknown').capitalize()
            text = msg.get('text', '')
            content += f"**{role}**: {text}\n\n"
            
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return filepath
        except Exception as e:
            print(f"Error saving report: {e}")
            return None

    def export_json(self, data):
        """
        Exports data to JSON.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"Export_{timestamp}.json"
        filepath = os.path.join(self.export_dir, filename)
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return filepath
        except Exception as e:
            print(f"Error exporting JSON: {e}")
            return None

    def export_csv(self, data):
        """
        Exports conversation history to CSV.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"Export_{timestamp}.csv"
        filepath = os.path.join(self.export_dir, filename)
        
        try:
            with open(filepath, "w", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Role", "Content", "Timestamp", "Type"])
                
                # Assume data is a list of events or a dict with 'history'
                history = data.get('history', []) if isinstance(data, dict) else data
                
                for item in history:
                    writer.writerow([
                        item.get('role', 'Unknown'),
                        item.get('content', '') or item.get('text', ''),
                        item.get('timestamp', ''),
                        item.get('type', 'message')
                    ])
            return filepath
        except Exception as e:
            print(f"Error exporting CSV: {e}")
            return None
    def export_pdf(self, transcript, insights, summary, topic):
        """
        Generates a PDF report using reportlab.
        """
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"Meeting_Report_{timestamp}.pdf"
        filepath = os.path.join(self.export_dir, filename)
        
        try:
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            styles = getSampleStyleSheet()
            
            # Custom Styles
            title_style = styles['Title']
            heading_style = styles['Heading2']
            normal_style = styles['Normal']
            
            elements = []
            
            # Title
            elements.append(Paragraph("Meeting Report", title_style))
            elements.append(Spacer(1, 12))
            
            # Meta
            elements.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", normal_style))
            elements.append(Paragraph(f"<b>Topic:</b> {topic}", normal_style))
            elements.append(Spacer(1, 12))
            
            # Summary
            elements.append(Paragraph("Executive Summary", heading_style))
            elements.append(Paragraph(summary if summary else "No summary generated.", normal_style))
            elements.append(Spacer(1, 12))
            
            # Insights
            elements.append(Paragraph("Key Insights & Action Items", heading_style))
            for insight in insights:
                text = f"• <b>{insight.get('type', 'Info')}</b>: {insight.get('text', '')}"
                elements.append(Paragraph(text, normal_style))
            elements.append(Spacer(1, 12))
            
            # Transcript
            elements.append(Paragraph("Transcript", heading_style))
            for msg in transcript:
                role = msg.get('role', 'Unknown').capitalize()
                text = msg.get('text', '') or msg.get('content', '')
                elements.append(Paragraph(f"<b>{role}:</b> {text}", normal_style))
                elements.append(Spacer(1, 6))
                
            doc.build(elements)
            return filepath
        except Exception as e:
            print(f"Error saving PDF report: {e}")
            return None
