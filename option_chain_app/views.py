from django.shortcuts import render
import requests
import pandas as pd
from datetime import datetime

# Option Chain Class to Fetch Data
class OptionChain:
    def __init__(self, symbol, indices_equities, is_index=True, timeout=5):
        self.symbol = symbol
        self.timeout = timeout
        base_url = "https://www.nseindia.com/api/option-chain-{}?symbol={}"
        self.url = base_url.format(indices_equities if is_index else 'indices', symbol)
        self.session = requests.Session()
        self.session.headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "*/*", "Accept-Language": "en-us,en;q=0.5"
        }
        self.session.get("https://www.nseindia.com/option-chain", timeout=self.timeout)
    
    def fetch_data(self):
        try:
            response = self.session.get(self.url, timeout=self.timeout)
            return response.json()
        except Exception as ex:
            print(f"Error fetching data: {ex}")
            return None

# Function to Process Data and Return Results
def fetch_data(company_name, indices_equities):
    try:
        option_chain = OptionChain(company_name.upper(), indices_equities)
        data = option_chain.fetch_data()
        if not data:
            return None
        
        expiry = data['records']['expiryDates'][0]
        df = oi_chain_builder(data, expiry)
        price = data['records']['underlyingValue']
        pcr = data['filtered']['PE']['totOI'] / data['filtered']['CE']['totOI']
        change_in_oi = df["PUTS_Chng_in_OI"].sum() / df["CALLS_Chng_in_OI"].sum()
        top_ce_oi = df.loc[df['CALLS_Chng_in_OI'].idxmax(), "StrikePrice"]
        top_pe_oi = df.loc[df['PUTS_Chng_in_OI'].idxmax(), "StrikePrice"]
        return price, change_in_oi, pcr, top_ce_oi, top_pe_oi
    except Exception as e:
        print(f"Error: {e}")
        return None

# Define View for Stock Data
def stock_data_view(request):
    context = {}
    
    if request.method == "POST":
        company_name = request.POST.get("company_name")
        indices_equities = request.POST.get("indices_equities")
        data = fetch_data(company_name, indices_equities)
        
        if data:
            price, change_in_oi, pcr, top_ce_oi, top_pe_oi = data
            context['company_name'] = company_name
            context['price'] = price
            context['change_in_oi'] = change_in_oi
            context['pcr'] = pcr
            context['top_ce_oi'] = top_ce_oi
            context['top_pe_oi'] = top_pe_oi
        else:
            context['error'] = "Data not found or expired!"
    
    return render(request, "stock_data.html", context)
