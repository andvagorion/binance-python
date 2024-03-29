import sys
import os
from pathlib import Path
import requests
import json
import time
from datetime import datetime
import re
import pyperclip

### constants

root_dir = '.\\klines-5m'

root_url = 'https://api.binance.com/api/v1/klines'
interval = '5m'

INVERTED = ['EURBUSD', 'EURUSDT']

### parsing raw input

def parse_symbol(raw):
    if raw == 'BNB': return 'BNBEUR'
    elif raw == 'BUSD': return 'EURBUSD'
    elif raw == 'USDT': return 'EURUSDT'
    elif raw == 'ETH': return 'ETHEUR'
    elif raw in ['EURBUSD', 'EURUSDT', 'BNBEUR', 'ETHEUR']: return raw
    else:
        print('{} is not supported. Supported tokens: BUSD, USDT, BNB, ETH.'.format(raw))
        sys.exit(1)

def parse_date(raw):
    if not (re.search('\d+-\d+-\d+ \d+:\d+', raw)):
        print('{} can not be parsed as date. Format is \'yyyy-mm-dd hh:mm\'.'.format(raw))
        sys.exit(1)
    return raw

### reading and writing data

def read_data(path):
    with open(path, 'r') as f:
        data = json.load(f)
    return data


def write_data(symbol, year, month, data):
    p = get_path(symbol, year, month)
    print(f"Writing {len(data)} values for {symbol} to {p}.")
    with open(p, 'w') as f:
        json.dump(data, f)


def no_symbol_data(symbol):
    symbol_path = get_path(symbol)
    return not os.path.exists(symbol_path)


def strf_timestamp(ts):
    return datetime.fromtimestamp(ts / 1000.0).strftime("%Y-%m-%d %H:%M")

### loading price data

def get_path(symbol, year, month):
    return f"{root_dir}\\{symbol}\\{year}-{month}.json"


def load_data(symbol, last):
    url = '%s?symbol=%s&interval=%s&startTime=%s' % (root_url, symbol, interval, str(last + 1))
    data = requests.get(url).text
    return json.loads(data)


def beginning_of_current_year():
    current_year = datetime.today().year
    return datetime(current_year, 1, 1, 0, 0).timestamp()


def load_new(symbol):
    end_of_last_year = int(beginning_of_current_year() - 1) * 1000
    return load(symbol, end_of_last_year)


def get_last_entry_date(data):
    last = 0
    for entry in data:
        if entry[0] > last: last = entry[0]
    return last


def find_newest_file(symbol):
    dir = get_symbol_dir(symbol)
    p = Path(dir)
    if not p.is_dir(): return None
    
    files = list(p.glob('**/*.json'))
    if files:
        return sorted(files)[-1]
    else:
        return None

def create_dir(dir_path):
    print(f"Creating {dir_path}")
    try:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print("Could not create directory.")
        raise e


def get_symbol_dir(symbol):
    return f"{root_dir}\\{symbol}"


def update(symbol):
    symbol_dir = get_symbol_dir(symbol)
    
    if not Path(symbol_dir).is_dir():
        create_dir(symbol_dir)
    
    update_existing(symbol)


def update_existing(symbol):
    newest_file = find_newest_file(symbol)
    
    if not newest_file:
        print("Found no existing klines data.")
        load(symbol, None)
    else:
        newest_entry = get_last_entry_date(read_data(newest_file))
        print(f"Latest entry: {newest_entry}")
        load(symbol, newest_entry)


def start_of_month():
    dt = datetime.today().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return int(datetime.timestamp(dt) * 1000.0)


def year_from(ts):
    return datetime.fromtimestamp(ts / 1000.0).strftime("%Y")


def month_from(ts):
    return datetime.fromtimestamp(ts / 1000.0).strftime("%m")


def load(symbol, last):
    start = last
    if not start: start = start_of_month()
    
    print(f"Loading klines for {symbol} since {start} ({strf_timestamp(start)})")
    
    ts = start
    should_load_more = True
    current_year = year_from(start)
    current_month = month_from(start)
    
    klines_for_month = []
    
    path = get_path(symbol, current_year, current_month)
    if Path(path).exists(): klines_for_month = read_data(path)
    
    try:
        while(should_load_more):
            print(f"Loading data for {symbol} after {strf_timestamp(ts)}")
            data = load_data(symbol, ts)
            print(f'Loaded {len(data)} klines for {symbol}.')
            
            for entry in data:
                ts = entry[0]
                month = month_from(ts)
                year = year_from(ts)
                
                if (year != current_year or month != current_month):
                    write_data(symbol, current_year, current_month, klines_for_month)
                    klines_for_month = []
                    current_year = year
                    current_month = month
                
                klines_for_month.append(entry[:5])

            # only run again if a full batch of klines was loaded
            if len(data) == 500: time.sleep(1)
            else: should_load_more = False
    except KeyboardInterrupt:
        print('Interrupted. Saving...')
        try:
            write_data(symbol, current_year, current_month, klines_for_month)
            sys.exit(130)
        except SystemExit:
            os._exit(130)
    
    # write remaining entries
    if klines_for_month:
        write_data(symbol, current_year, current_month, klines_for_month)

### reading price data

columns = ['TIMESTAMP', 'OPEN', 'HIGH', 'LOW', 'CLOSE']

def get_price(symbol, date):
    if no_symbol_data(symbol): return None
    
    symbol_path = get_path(symbol)
    with open(symbol_path, 'r') as f:
        data = json.load(f)
    
    price = price_at(data, date)
    
    if price == None: return None
    
    if symbol in INVERTED:
        return round(1 / float(price), 10)
    else:
        return round(float(price), 4)


def price_at(data, date):
    for entry in data:
        ts = entry[columns.index('TIMESTAMP')]
        e_date = datetime.fromtimestamp(ts / 1000.0).strftime("%Y-%m-%d %H:%M")
        if e_date == date:
            return entry[columns.index('OPEN')]
    return None


### entry point

if len(sys.argv) != 3:
    print('Usage: klines-5m SYMBOL TIME, e.g. klines-5m \'BUSD\' \'2020-01-01 10:25\'')
    print('Or: klines-5m SYMBOL \'update\' to update price information for token.')
    sys.exit(1)

raw_symbol = sys.argv[1]
raw_date = sys.argv[2]

symbol = parse_symbol(raw_symbol)

if (raw_date == 'update'):
    print(f'Loading klines for {symbol}.')
    
    update(symbol)
    sys.exit(0)

date = parse_date(raw_date)

price = get_price(symbol, date)
if (price != None):
    formatted = "{0:.4f}".format(price)
    pyperclip.copy(formatted)
    print(formatted)
else:
    print('No price data available.')