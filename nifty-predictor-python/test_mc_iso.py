from moneycontrol_scraper import moneycontrol_scraper

print("Testing MoneyControl Scraper...")
try:
    oc = moneycontrol_scraper.get_option_chain('nifty')
    if oc:
        print(f"Success! Source: {oc.get('source')}")
        chain = oc.get('chain')
        if chain:
             print(f"Chain length: {len(chain)}")
             print(f"First strike: {chain[0]}")
             
             # Check premiums
             valid = 0
             for row in chain:
                 if row.get('ce_ltp', 0) > 0: valid += 1
             print(f"Strikes with valid premiums: {valid}/{len(chain)}")
        else:
             print("Chain is empty")
    else:
        print("Failed to get option chain (None returned)")

except Exception as e:
    print(f"Exception: {e}")
    import traceback
    traceback.print_exc()
