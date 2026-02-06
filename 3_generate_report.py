import database
import pandas as pd
import time
import os

def generate_report():
    print("Step 3: Generating Professional Excel Report")
    
    Session = database.init_db()
    session = Session()
    
    articles = session.query(database.Article).all()
    print(f"Fetching {len(articles)} records...")
    
    data = []
    for art in articles:
        cat = session.query(database.Category).get(art.category_id)
        
        # Format ID as KB-XXX
        kb_id = f"KB-{art.article_custom_id}" if art.article_custom_id and art.article_custom_id != "N/A" else "KB-N/A"
        
        data.append({
            'Article ID': kb_id,
            'Article Title': art.title,
            'Category': cat.name if cat else 'Unknown',
            'URL': art.url,
            'Last Updated': art.last_updated.strftime('%Y-%m-%d') if art.last_updated else "",
            'Topics Covered': art.topics_covered,
            'Content Type': art.content_type,
            'Word Count': art.word_count,
            'Has Screenshots': 'Yes' if art.has_screenshots else 'No',
            'Gaps Identified': art.gap_analysis
        })
        
    if not data:
        print("No data to export.")
        return
        
    df = pd.DataFrame(data)
    
    # Filename with timestamp
    filename = f"AI_Audit_Report_{int(time.time())}.xlsx"
    
    # Use XlsxWriter for "Beautiful" formatting
    writer = pd.ExcelWriter(filename, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Audit Report')
    
    workbook = writer.book
    worksheet = writer.sheets['Audit Report']
    
    # Formats
    header_fmt = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'valign': 'top',
        'fg_color': '#D7E4BC', # Light Green
        'border': 1
    })
    
    cell_fmt = workbook.add_format({
        'text_wrap': True,
        'valign': 'top',
        'border': 1
    })
    
    # Set Column Widths and Apply Formats
    # Columns: ID(0), Title(1), Cat(2), URL(3), Updated(4), Topics(5), Type(6), Count(7), Screens(8), Gaps(9)
    
    worksheet.set_column('A:A', 15, cell_fmt) # ID
    worksheet.set_column('B:B', 40, cell_fmt) # Title
    worksheet.set_column('C:C', 20, cell_fmt) # Category
    worksheet.set_column('D:D', 30, cell_fmt) # URL
    worksheet.set_column('E:E', 15, cell_fmt) # Updated
    worksheet.set_column('F:F', 30, cell_fmt) # Topics
    worksheet.set_column('G:G', 20, cell_fmt) # Content Type
    worksheet.set_column('H:H', 12, cell_fmt) # Count
    worksheet.set_column('I:I', 15, cell_fmt) # Screenshots
    worksheet.set_column('J:J', 50, cell_fmt) # Gaps
    
    # Apply header format
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(0, col_num, value, header_fmt)
        
    writer.close()
    
    print(f"Success! Report saved to: {filename}")
    print(f"Total Rows: {len(df)}")

if __name__ == "__main__":
    generate_report()
