from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
import os
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd

class ReportGenerator:
    """Generate PDF reports for forecasts and inventory"""
    
    def __init__(self, outlet_name="Restaurant Outlet"):
        self.outlet_name = outlet_name
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1976d2'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
    
    def generate_forecast_report(self, forecast_data, item_forecasts, output_path):
        """
        Generate comprehensive forecast report PDF
        
        Args:
            forecast_data: Dict with forecast information
            item_forecasts: Dict with item-level forecasts
            output_path: Where to save the PDF
        
        Returns:
            str: Path to generated PDF
        """
        print(f"\n📄 Generating forecast report...")
        
        # Create PDF document
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        story = []
        
        # Title
        title = Paragraph(f"Forecast Report<br/>{self.outlet_name}", self.title_style)
        story.append(title)
        story.append(Spacer(1, 0.2*inch))
        
        # Report metadata
        meta_data = [
            ['Report Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Forecast Date:', forecast_data.get('forecast_dates', ['N/A'])[0]],
            ['Model Used:', forecast_data.get('model_used', 'N/A').upper()],
            ['Confidence Level:', f"{int(forecast_data.get('confidence_level', 0) * 100)}%"]
        ]
        
        meta_table = Table(meta_data, colWidths=[2*inch, 4*inch])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(meta_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Summary section
        summary_title = Paragraph("Forecast Summary", self.styles['Heading2'])
        story.append(summary_title)
        story.append(Spacer(1, 0.1*inch))
        
        summary_data = [
            ['Metric', 'Value'],
            ['Tomorrow\'s Predicted Customers', str(forecast_data.get('next_day_prediction', 'N/A'))],
            ['Average for Next Week', str(int(sum(forecast_data.get('next_week_predictions', [0])) / 
                                                len(forecast_data.get('next_week_predictions', [1]))))],
            ['Forecast ID', f"#{forecast_data.get('forecast_id', 'N/A')}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Weekly forecast table
        weekly_title = Paragraph("Next 7 Days Forecast", self.styles['Heading2'])
        story.append(weekly_title)
        story.append(Spacer(1, 0.1*inch))
        
        weekly_data = [['Date', 'Predicted Customers']]
        for date, customers in zip(
            forecast_data.get('forecast_dates', []),
            forecast_data.get('next_week_predictions', [])
        ):
            weekly_data.append([date, str(customers)])
        
        weekly_table = Table(weekly_data, colWidths=[3*inch, 3*inch])
        weekly_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        story.append(weekly_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Item-level forecasts
        if item_forecasts:
            items_title = Paragraph("Item-Level Demand Forecast", self.styles['Heading2'])
            story.append(items_title)
            story.append(Spacer(1, 0.1*inch))
            
            items_data = [['Food Item', 'Tomorrow\'s Quantity', 'Weekly Total']]
            
            for item_name, forecast in item_forecasts.items():
                next_day = forecast.get('next_day', forecast) if isinstance(forecast, dict) else forecast
                weekly = forecast.get('next_week', [next_day] * 7) if isinstance(forecast, dict) else [next_day] * 7
                weekly_total = sum(weekly) if isinstance(weekly, list) else next_day * 7
                
                items_data.append([
                    item_name,
                    str(next_day),
                    str(int(weekly_total))
                ])
            
            items_table = Table(items_data, colWidths=[2.5*inch, 1.75*inch, 1.75*inch])
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4caf50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            
            story.append(items_table)
        
        # Add chart
        story.append(PageBreak())
        chart_title = Paragraph("Visual Forecast", self.styles['Heading2'])
        story.append(chart_title)
        story.append(Spacer(1, 0.2*inch))
        
        # Generate chart
        chart_path = self._create_forecast_chart(forecast_data)
        if chart_path:
            img = Image(chart_path, width=6*inch, height=4*inch)
            story.append(img)
            os.remove(chart_path)  # Clean up temp file
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer = Paragraph(
            "<i>Generated by Food Forecasting System</i>",
            ParagraphStyle('Footer', fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
        )
        story.append(footer)
        
        # Build PDF
        doc.build(story)
        print(f"✅ Report saved to: {output_path}")
        
        return output_path
    
    def generate_inventory_report(self, inventory_data, output_path):
        """
        Generate inventory recommendations report
        
        Args:
            inventory_data: Dict with inventory information
            output_path: Where to save PDF
        
        Returns:
            str: Path to generated PDF
        """
        print(f"\n📄 Generating inventory report...")
        
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        story = []
        
        # Title
        title = Paragraph(f"Inventory Report<br/>{self.outlet_name}", self.title_style)
        story.append(title)
        story.append(Spacer(1, 0.2*inch))
        
        # Metadata
        meta = Paragraph(
            f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            self.styles['Normal']
        )
        story.append(meta)
        story.append(Spacer(1, 0.3*inch))
        
        # Summary
        shopping_list = inventory_data.get('shopping_list', {})
        summary_title = Paragraph("Shopping List Summary", self.styles['Heading2'])
        story.append(summary_title)
        story.append(Spacer(1, 0.1*inch))
        
        summary_data = [
            ['Total Items to Order:', str(shopping_list.get('total_items', 0))],
            ['Estimated Total Cost:', f"${shopping_list.get('total_cost', 0):.2f}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Shopping list
        items_title = Paragraph("Items to Order", self.styles['Heading2'])
        story.append(items_title)
        story.append(Spacer(1, 0.1*inch))
        
        items_data = [['Ingredient', 'Quantity', 'Unit', 'Cost']]
        
        for item in shopping_list.get('items', []):
            items_data.append([
                item['ingredient'],
                str(item['quantity']),
                item['unit'],
                f"${item['cost']:.2f}"
            ])
        
        items_table = Table(items_data, colWidths=[2.5*inch, 1*inch, 1*inch, 1.5*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        story.append(items_table)
        
        # Purchase orders by supplier
        purchase_orders = inventory_data.get('purchase_orders', {})
        if purchase_orders:
            story.append(PageBreak())
            po_title = Paragraph("Purchase Orders by Supplier", self.styles['Heading2'])
            story.append(po_title)
            story.append(Spacer(1, 0.2*inch))
            
            for supplier, order in purchase_orders.items():
                supplier_para = Paragraph(f"<b>{supplier}</b>", self.styles['Heading3'])
                story.append(supplier_para)
                story.append(Spacer(1, 0.1*inch))
                
                po_data = [['Ingredient', 'Quantity', 'Unit', 'Unit Price', 'Total']]
                
                for item in order.get('items', []):
                    po_data.append([
                        item.get('ingredient', ''),
                        str(item.get('quantity', 0)),
                        item.get('unit', ''),
                        f"${item.get('unit_price', 0):.2f}",
                        f"${item.get('line_total', 0):.2f}"
                    ])
                
                # Add total row
                po_data.append([
                    '', '', '', 'TOTAL:',
                    f"${order.get('total_cost', 0):.2f}"
                ])
                
                po_table = Table(po_data, colWidths=[1.8*inch, 0.8*inch, 0.6*inch, 1*inch, 1*inch])
                po_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4caf50')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -2), 1, colors.black),
                    ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.lightgrey])
                ]))
                
                story.append(po_table)
                story.append(Spacer(1, 0.3*inch))
        
        # Build PDF
        doc.build(story)
        print(f"✅ Report saved to: {output_path}")
        
        return output_path
    
    def generate_excel_report(self, forecast_data, item_forecasts, output_path):
        """
        Generate multi-sheet Excel report
        
        Args:
            forecast_data: Dict with forecast information
            item_forecasts: Dict with item-level forecasts
            output_path: Where to save the Excel file
        """
        print(f"\n📊 Generating Excel report...")
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 1. Summary Sheet
            summary_df = pd.DataFrame([
                ['Outlet Name', self.outlet_name],
                ['Report Date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                ['Forecast ID', forecast_data.get('forecast_id', 'N/A')],
                ['Model Used', forecast_data.get('model_used', 'N/A')],
                ['Confidence Level', f"{int(forecast_data.get('confidence_level', 0) * 100)}%"],
                ['Tomorrow\'s Customers', forecast_data.get('next_day_prediction', 0)]
            ], columns=['Metric', 'Value'])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # 2. Weekly Forecast Sheet
            weekly_df = pd.DataFrame({
                'Date': forecast_data.get('forecast_dates', []),
                'Predicted Customers': forecast_data.get('next_week_predictions', [])
            })
            weekly_df.to_excel(writer, sheet_name='Weekly Outlook', index=False)
            
            # 3. Item Predictions Sheet
            items_list = []
            for item_name, forecast in item_forecasts.items():
                next_day = forecast.get('next_day', forecast) if isinstance(forecast, dict) else forecast
                category = forecast.get('category', 'General') if isinstance(forecast, dict) else 'General'
                items_list.append({
                    'Item Name': item_name,
                    'Category': category,
                    'Tomorrow\'s Prediction': next_day,
                    'Weekly Estimated': next_day * 7
                })
            
            items_df = pd.DataFrame(items_list)
            items_df.to_excel(writer, sheet_name='Item Predictions', index=False)
            
            # 4. Inventory Sheet (if available)
            # This could be expanded if inventory_data is passed
            
        print(f"✅ Excel report saved to: {output_path}")
        return output_path
    
    def _create_forecast_chart(self, forecast_data):
        """Create a chart visualization for forecast"""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            dates = forecast_data.get('forecast_dates', [])
            predictions = forecast_data.get('next_week_predictions', [])
            
            ax.plot(dates, predictions, marker='o', linewidth=2, markersize=8, color='#1976d2')
            ax.set_xlabel('Date', fontsize=12)
            ax.set_ylabel('Predicted Customers', fontsize=12)
            ax.set_title('Next 7 Days Customer Forecast', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Save to temporary file
            temp_path = 'temp_chart.png'
            plt.savefig(temp_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return temp_path
        
        except Exception as e:
            print(f"⚠️  Chart generation failed: {str(e)}")
            return None


# Test
if __name__ == '__main__':
    generator = ReportGenerator("Main Branch Restaurant")
    
    # Test forecast report
    test_forecast = {
        'forecast_id': 123,
        'next_day_prediction': 95,
        'confidence_level': 0.88,
        'model_used': 'xgboost',
        'forecast_dates': ['2024-01-08', '2024-01-09', '2024-01-10', '2024-01-11', '2024-01-12', '2024-01-13', '2024-01-14'],
        'next_week_predictions': [95, 102, 88, 110, 105, 98, 92]
    }
    
    test_items = {
        'Burger': {'next_day': 45},
        'Pizza': {'next_day': 30},
        'Coffee': {'next_day': 70},
        'Salad': {'next_day': 25}
    }
    
    generator.generate_forecast_report(
        test_forecast,
        test_items,
        'test_forecast_report.pdf'
    )
    print("✅ Test report generated!")
