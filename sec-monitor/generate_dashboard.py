import json
import os

LOG_PATH = "sec-monitor/filings_log.json"
OUTPUT_PATH = "index.html"

def generate():
    if not os.path.exists(LOG_PATH): return
    with open(LOG_PATH, 'r') as f: data = json.load(f)
    
    # Sort by date (newest first)
    data.sort(key=lambda x: x['filingDate'], reverse=True)

    html = """
    <html>
    <head>
        <title>2026 Strategic SEC Monitor</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; background: #f7fafc; color: #2d3748; }
            .header { background: #1a202c; color: white; padding: 25px 40px; }
            .container { padding: 40px; max-width: 1400px; margin: auto; }
            table { width: 100%; border-collapse: collapse; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }
            th { background: #4a5568; color: white; padding: 18px; text-align: left; text-transform: uppercase; font-size: 11px; letter-spacing: 0.05em; }
            td { padding: 18px; border-bottom: 1px solid #edf2f7; font-size: 14px; vertical-align: top; }
            tr:hover { background-color: #f8fafc; }
            .buy { color: #276749; background: #c6f6d5; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 12px; }
            .sell { color: #9b2c2c; background: #fed7d7; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 12px; }
            .award { color: #2c5282; background: #bee3f8; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 12px; }
            .ticker-badge { background: #edf2f7; color: #4a5568; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
            .insider-name { font-weight: bold; color: #1a202c; display: block; }
            .insider-title { font-size: 11px; color: #718096; }
            .val-sub { color: #a0aec0; font-size: 11px; margin-top: 4px; display: block; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1 style="margin:0;">🚀 Strategic SEC Monitor</h1>
            <p style="margin:5px 0 0 0; opacity: 0.8; font-size: 14px;">Filings from Jan 1, 2026 | Strategic Filters: Buy (P) All, Sell/Award (S/A) > 1,000 shares</p>
        </div>
        <div class="container">
            <table>
                <tr>
                    <th style="width: 200px;">Company</th>
                    <th style="width: 80px;">Form</th>
                    <th style="width: 120px;">Filing Date</th>
                    <th style="width: 250px;">Insider / Reporter</th>
                    <th>Significant Activity / Description</th>
                </tr>
    """

    for item in data:
        insider_info = "—"
        trade_details = f"<span style='color: #4a5568;'>{item['description']}</span>"
        
        if item.get("details"):
            insider_info = f"<span class='insider-name'>{item['details'][0]['insider_name']}</span>"
            insider_info += f"<span class='insider-title'>{item['details'][0]['insider_title']}</span>"
            
            trade_details = ""
            for d in item["details"]:
                cls = "buy" if "BUY" in d['type'] else "sell" if "SELL" in d['type'] else "award"
                
                if "AWARD" in d['type']:
                    # Awards usually $0, hide price for cleaner look
                    trade_details += f"<div style='margin-bottom:12px;'><span class='{cls}'>{d['type']}</span> {int(d['shares']):,} shares</div>"
                else:
                    trade_details += f"""
                        <div style='margin-bottom:12px;'>
                            <span class='{cls}'>{d['type']}</span> {int(d['shares']):,} shares @ ${d['price']:.2f}
                            <span class='val-sub'>Total Market Value: ${d['value']:,.0f}</span>
                        </div>
                    """
        elif item['form'] in ["4", "4/A"]:
            continue # Form 4 exists but didn't meet our filters

        html += f"""
            <tr>
                <td><strong>{item['company']}</strong><br><span class='ticker-badge'>{item['ticker']}</span></td>
                <td><strong>{item['form']}</strong></td>
                <td>{item['filingDate']}</td>
                <td>{insider_info}</td>
                <td>{trade_details}</td>
            </tr>
        """

    html += "</table></div></body></html>"
    
    with open(OUTPUT_PATH, 'w') as f:
        f.write(html)

if __name__ == "__main__":
    generate()
