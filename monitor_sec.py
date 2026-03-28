import json
import os
import requests
import time
import xml.etree.ElementTree as ET
from datetime import datetime

# --- CONFIGURATION ---
BASE_DIR = "sec-monitor"
WATCHLIST_PATH = os.path.join(BASE_DIR, "watchlist.json")
LOG_PATH = os.path.join(BASE_DIR, "filings_log.json")
USER_AGENT = "Mozilla/5.0 (compatible; MaxSECMonitor/1.0; mgsoccer17@gmail.com)"
START_DATE = "2026-01-01" # Only 2026 data

def get_form4_details(cik, accession, doc_name):
    """Deep-dive into Form 4 to extract Name, Title, and P/S/A trades > 1,000 shares"""
    acc_clean = accession.replace('-', '')
    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_clean}/{doc_name}"
    
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT})
        if resp.status_code != 200: return None
        
        root = ET.fromstring(resp.content)
        name = root.find(".//rptOwnerName").text if root.find(".//rptOwnerName") is not None else "Unknown"
        title = root.find(".//officerTitle").text if root.find(".//officerTitle") is not None else "Director/Owner"
        
        transactions = []
        # Check both Table I (Common Stock) and Table II (Derivatives/Options)
        for tx in root.findall(".//nonDerivativeTransaction") + root.findall(".//derivativeTransaction"):
            code = tx.find(".//transactionCode").text if tx.find(".//transactionCode") is not None else ""
            shares_node = tx.find(".//transactionShares/value") or tx.find(".//underlyingSecurityShares/value")
            shares = float(shares_node.text) if shares_node is not None else 0
            
            # --- STRATEGIC FILTERS ---
            if code not in ["P", "S", "A"]: continue # Only P, S, or A
            if code in ["S", "A"] and shares <= 1000: continue # S and A must be > 1000
            
            price_node = tx.find(".//transactionPricePerShare/value")
            price = float(price_node.text) if price_node is not None else 0
            date = tx.find(".//transactionDate/value").text if tx.find(".//transactionDate/value") is not None else ""
            
            transactions.append({
                "insider_name": name,
                "insider_title": title,
                "date": date,
                "type": "BUY (P)" if code == "P" else "SELL (S)" if code == "S" else "AWARD (A)",
                "shares": shares,
                "price": price,
                "value": shares * price
            })
        return transactions if transactions else None
    except:
        return None

def run_monitor():
    if not os.path.exists(WATCHLIST_PATH): return
    with open(WATCHLIST_PATH, 'r') as f: watchlist = json.load(f)
    
    # Load and filter existing log to ensure only 2026 data exists
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, 'r') as f: 
            raw_log = json.load(f)
            filings_log = [f for f in raw_log if f['filingDate'] >= START_DATE]
    else:
        filings_log = []
    
    existing_accs = {f['accessionNumber'] for f in filings_log}
    new_count = 0

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
                f_date = recent['filingDate'][i]
                
                if f_date < START_DATE: break # Stop checking this company
                if acc in existing_accs: continue
                
                form = recent['form'][i]
                entry = {
                    "company": co['company'],
                    "ticker": co['ticker'],
                    "accessionNumber": acc,
                    "form": form,
                    "filingDate": f_date,
                    "description": recent['primaryDocDescription'][i],
                    "details": None
                }

                if form in ["4", "4/A"]:
                    doc = recent['primaryDocument'][i]
                    entry["details"] = get_form4_details(cik, acc, doc)
                
                filings_log.append(entry)
                new_count += 1
            time.sleep(0.1)
        except: continue

    with open(LOG_PATH, 'w') as f:
        json.dump(filings_log, f, indent=2)

if __name__ == "__main__":
    run_monitor()
