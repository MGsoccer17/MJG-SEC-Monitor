import json
import os
import requests
import time
import xml.etree.ElementTree as ET
from datetime import datetime

# --- SETTINGS ---
BASE_DIR = "sec-monitor"
WATCHLIST_PATH = os.path.join(BASE_DIR, "watchlist.json")
LOG_PATH = os.path.join(BASE_DIR, "filings_log.json")
USER_AGENT = "Mozilla/5.0 (compatible; MaxSECMonitor/1.0; mgsoccer17@gmail.com)"

def get_form4_details(cik, accession, doc_name):
    """Deep-dive into Form 4 XML to get Shares and Price"""
    acc_clean = accession.replace('-', '')
    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_clean}/{doc_name}"
    
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT})
        if resp.status_code != 200: return None
        
        # Parse the XML content
        root = ET.fromstring(resp.content)
        transactions = []
        
        # Look for non-derivative transactions (Common Stock)
        for tx in root.findall(".//nonDerivativeTransaction"):
            date = tx.find(".//transactionDate/value").text if tx.find(".//transactionDate/value") is not None else ""
            code = tx.find(".//transactionCode").text if tx.find(".//transactionCode") is not None else ""
            shares = tx.find(".//transactionShares/value").text if tx.find(".//transactionShares/value") is not None else "0"
            price = tx.find(".//transactionPricePerShare/value").text if tx.find(".//transactionPricePerShare/value") is not None else "0"
            
            # P = Purchase (Buy), S = Sale (Sell)
            tx_type = "BUY" if code == "P" else "SELL" if code == "S" else code
            
            transactions.append({
                "date": date,
                "type": tx_type,
                "shares": float(shares),
                "price": float(price),
                "total_value": float(shares) * float(price)
            })
        return transactions
    except:
        return None

def run_monitor():
    # 1. Load Files
    with open(WATCHLIST_PATH, 'r') as f: watchlist = json.load(f)
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, 'r') as f: filings_log = json.load(f)
    else: filings_log = []
    
    existing_accs = {f['accessionNumber'] for f in filings_log}
    new_count = 0

    # 2. Poll SEC
    for co in watchlist['companies']:
        if co['status'] != 'ACTIVE': continue
        cik = co['cik'].zfill(10)
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        
        try:
            resp = requests.get(url, headers={"User-Agent": USER_AGENT})
            if resp.status_code != 200: continue
            
            recent = resp.json().get('filings', {}).get('recent', {})
            for i in range(len(recent.get('accessionNumber', []))):
                acc = recent['accessionNumber'][i]
                if acc in existing_accs: continue
                
                form = recent['form'][i]
                entry = {
                    "company": co['company'],
                    "ticker": co['ticker'],
                    "accessionNumber": acc,
                    "form": form,
                    "filingDate": recent['filingDate'][i],
                    "description": recent['primaryDocDescription'][i],
                    "details": None
                }

                # 3. IF FORM 4, DO THE DEEP DIVE
                if form in ["4", "4/A"]:
                    doc = recent['primaryDocument'][i]
                    entry["details"] = get_form4_details(cik, acc, doc)
                
                filings_log.append(entry)
                new_count += 1
            time.sleep(0.1)
        except: continue

    with open(LOG_PATH, 'w') as f:
        json.dump(filings_log, f, indent=2)
    print(f"Finished! Found {new_count} new filings.")

if __name__ == "__main__":
    run_monitor()
