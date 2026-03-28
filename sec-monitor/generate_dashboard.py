import json
import os

LOG_PATH = "sec-monitor/filings_log.json"
OUTPUT_PATH = "index.html"

def generate():
    if not os.path.exists(LOG_PATH): return
    with open(LOG_PATH, 'r') as f: data = json.load(f)
    
    # Sort by date (newest first)
    data.reverse()

    html = """
    <html>
    <head>
        <title>SEC Insider Monitor</title>
        <style>
            body { font-family: sans-serif; margin: 20px; background: #f4f4f9; }
            table { width: 100%; border-collapse: collapse; background: white; }
            th, td { padding: 12px; border: 1px solid #ddd; text-align: left; }
            th { background: #333; color: white; }
            tr:nth-child(even) { background: #f9f9f9; }
            .buy { color: green; font-weight: bold; }
            .sell { color: red; font-weight: bold; }
            .header { margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 MJG SEC Insider Dashboard</h1>
            <p>Automatically updated every hour.</p>
        </div>
        <table>
            <tr>
                <th>Company</th>
                <th>Ticker</th>
                <th>Form</th>
                <th>Date</th>
                <th>Insider Activity</th>
            </tr>
    """

    for item in data:
        details_str = ""
        if item.get("details"):
            for d in item["details"]:
                cls = "buy" if d['type'] == "BUY" else "sell"
                details_str += f"<div class='{cls}'>{d['type']}: {int(d['shares']):,} shares @ ${d['price']:.2f}</div>"
        else:
            details_str = item['description']

        html += f"""
            <tr>
                <td>{item['company']}</td>
                <td>{item['ticker']}</td>
                <td>{item['form']}</td>
                <td>{item['filingDate']}</td>
                <td>{details_str}</td>
            </tr>
        """

    html += "</table></body></html>"
    
    with open(OUTPUT_PATH, 'w') as f:
        f.write(html)

if __name__ == "__main__":
    generate()
