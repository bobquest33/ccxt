# coding=utf-8

markets = [
    '_1broker',
    '_1btcxe',
    'anxpro',
    'bit2c',
    'bitbay',
    'bitbays',
    'bitcoincoid',
    'bitfinex',
    'bitlish',
    'bitmarket',
    'bitmex',
    'bitso',
    'bitstamp',
    'bittrex',
    'blinktrade',
    'btcchina',
    'btce',
    'btcexchange',
    'btctrader',
    'btctradeua',
    'btcturk',
    'btcx',
    'bter',
    'bxinth',
    'ccex',
    'cex',
    'chilebit',
    'coincheck',
    'coinmate',
    'coinsecure',
    'cryptocapital',
    'dsx',
    'exmo',
    'foxbit',
    'fybse',
    'fybsg',
    'gdax',
    'gemini',
    'hitbtc',
    'huobi',
    'itbit',
    'jubi',
    'kraken',
    'livecoin',
    'liqui',
    'luno',
    'mercado',
    'okcoincny',
    'okcoinusd',
    'paymium',
    'poloniex',
    'quadrigacx',
    'quoine',
    'southxchange',
    'surbitcoin',
    'therock',
    'urdubit',
    'vaultoro',
    'vbtc',
    'virwox',
    'yobit',
    'zaif',
]

__all__ = markets + [ 'markets', 'Market' ]

# Python 2 & 3
import base64
import calendar
import collections
import datetime
import functools
import hashlib
import hmac
import json
import math
import re
import sys
import time

try: 
    import urllib.parse   as _urlencode  # Python 3
    import urllib.request as _urllib
except ImportError: 
    import urllib  as _urlencode         # Python 2
    import urllib2 as _urllib

try:
  basestring # Python 3
except NameError:
  basestring = str # Python 2

class Market (object):

    id        = None
    rateLimit = 2000
    timeout   = 10
    verbose   = False
    products  = None
    tickers   = None

    def __init__ (self, config = {}):

        for key in config:
            setattr (self, key, config[key])

        if self.api:
            for apiType, methods in self.api.items ():
                for method, urls in methods.items ():
                    for url in urls:
                        url = url.strip ()
                        splitPath = re.compile ('[^a-zA-Z0-9]').split (url)

                        uppercaseMethod  = method.upper ()
                        lowercaseMethod  = method.lower ()
                        camelcaseMethod  = lowercaseMethod.capitalize ()
                        camelcaseSuffix  = ''.join ([ Market.capitalize (x) for x in splitPath ])
                        lowercasePath    = [ x.strip ().lower () for x in splitPath ]
                        underscoreSuffix = '_'.join ([ k for k in lowercasePath if len (k) ])

                        if camelcaseSuffix.find (camelcaseMethod) == 0:
                            camelcaseSuffix = camelcaseSuffix[len (camelcaseMethod):]

                        if underscoreSuffix.find (lowercaseMethod) == 0:
                            underscoreSuffix = underscoreSuffix[len (lowercaseMethod):]

                        camelcase  = apiType + camelcaseMethod + Market.capitalize (camelcaseSuffix)
                        underscore = apiType + '_' + lowercaseMethod + '_' + underscoreSuffix.lower ()

                        f = functools.partial (self.request, url, apiType, uppercaseMethod)
                        setattr (self, camelcase,  f)
                        setattr (self, underscore, f)


    # return (fetch ((self.cors ? self.cors : '') + url, options)
    #     .then (response => (typeof response === 'string') ? response : response.text ())
    #     .then (response => {
    #         try {
    #             return JSON.parse (response)
    #         } catch (e) {
    #             cloudflareProtection = response.match (/cloudflare/i) ? 'DDoS protection by Cloudflare' : ''
    #             if (self.verbose)
    #                 console.log (self.id, response, cloudflareProtection, e)
    #             throw e
    #         }
    #     }))

    
    def fetch (self, url, method = 'GET', headers = None, data = None):
        """Perform a HTTP request and return decoded JSON data"""
        version = '.'.join (map (str, sys.version_info[:3]))
        userAgent = 'ccxt/0.1.0 (+https://github.com/kroitor/ccxt) Python/' + version
        headers = headers or {}
        headers.update ({ 'User-Agent': userAgent })
        if self.verbose:
            print (url, method, headers, data)
        request = _urllib.Request (url, data, headers)
        request.get_method = lambda: method
        response = None
        try:
            handler = _urllib.HTTPHandler if url.startswith ('http://') else _urllib.HTTPSHandler
            opener = _urllib.build_opener (handler)
            response = opener.open (request, timeout = self.timeout).read ().decode('utf-8')
            return json.loads (response)
        except _urllib.HTTPError as e:
            try: 
                text = e.fp.read ()
                if re.search ('(cloudflare)', text, flags = re.IGNORECASE):
                    error = 'DDoS protection by Cloudflare'
                    print (self.id, method, url, e.code, e.msg, error)
                else:
                    print (self.id, method, url, e.code, e.msg, json.loads (text))
            except Exception as unused:
                print (self.id, method, url, e.code, e.msg, text)
            raise

    # import httplib
    # connection =  httplib.HTTPConnection('1.2.3.4:1234')
    # body_content = 'BODY CONTENT GOES HERE'
    # connection.request('PUT', '/url/path/to/put/to', body_content)
    # result = connection.getresponse()
    # # Now result.status and result.reason contains interesting stuff

    @staticmethod
    def capitalize (string): # first character only, rest characters unchanged
        if len (string) > 1:
            return "%s%s" % (string[0].upper (), string[1:])
        return string.upper ()

    @staticmethod 
    def keysort (dictionary):
        return collections.OrderedDict (sorted (dictionary.items (), key = lambda t: t[0]))

    @staticmethod
    def extend (*args):
        result = {}
        if args is not None:
            for arg in args:
                result.update (arg)
        return result

    @staticmethod
    def index_by (l, key):
        result = {}
        for x in l:
            result[x[key]] = x
        return result

    @staticmethod
    def indexBy (l, key):
        return Market.index_by (l, key)

    @staticmethod
    def sort_by (l, key, descending = False):
        return sorted (l, key = lambda k: k[key], reverse = descending)

    @staticmethod
    def sortBy (l, key, descending = False):
        return Market.sort_by (l, key, descending)

    @staticmethod
    def commonCurrencyCode (currency):
        return 'BTC' if currency == 'XBT' else currency

    @staticmethod
    def extract_params (string):
        return re.findall (r'{([a-zA-Z0-9_]+?)}', string)

    @staticmethod
    def implode_params (string, params):
        for key in params:
            string = string.replace ('{' + key + '}', str (params[key]))
        return string

    @staticmethod
    def extractParams (string):
        return Market.extract_params (string)

    @staticmethod
    def implodeParams (string, params):
        return Market.implode_params (string, params)

    @staticmethod
    def omit (d, *args):
        result = d.copy ()
        for arg in args:
            if type (arg) is list:
                for key in arg:
                    if key in result: del result[key]
            else:
                if arg in result: del result[arg]
        return result

    @staticmethod
    def s ():
        return Market.seconds ()
    
    @staticmethod
    def sec ():
        return Market.seconds ()
    
    @staticmethod
    def ms ():
        return Market.milliseconds ()
    
    @staticmethod
    def msec ():
        return Market.milliseconds ()
    
    @staticmethod
    def us ():
        return Market.microseconds ()
    
    @staticmethod
    def usec ():
        return Market.microseconds ()
    
    @staticmethod
    def seconds ():
        return int (time.time ())
    
    @staticmethod
    def milliseconds ():
        return int (time.time () * 1000)
    
    @staticmethod
    def microseconds ():
        return int (time.time () * 1000000)

    @staticmethod
    def iso8601 (timestamp):
        return (datetime
            .datetime
            .utcfromtimestamp (int (round (timestamp / 1000)))
            .strftime ('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z')

    @staticmethod
    def parse8601 (timestamp):
        yyyy = '([0-9]{4})-?'
        mm   = '([0-9]{2})-?'
        dd   = '([0-9]{2})(?:T|[\s])?'
        h    = '([0-9]{2}):?'
        m    = '([0-9]{2}):?'
        s    = '([0-9]{2})'
        ms   = '(\.[0-9]{3})?'
        tz = '(?:(\+|\-)([0-9]{2})\:?([0-9]{2})|Z)?'
        regex = r'' + yyyy + mm + dd + h + m + s + ms + tz
        match = re.search (regex, timestamp, re.IGNORECASE)
        yyyy, mm, dd, h, m, s, ms, sign, hours, minutes = match.groups ()
        ms = ms or '.000'
        sign = sign or ''
        sign = int (sign + '1')
        hours = int (hours or 0) * sign
        minutes = int (minutes or 0) * sign
        offset = datetime.timedelta (hours = hours, minutes = minutes)
        string = yyyy + mm + dd + h + m + s + ms + 'Z'
        dt = datetime.datetime.strptime (string, "%Y%m%d%H%M%S.%fZ")
        dt = dt + offset
        return calendar.timegm (dt.utctimetuple ()) * 1000

    @staticmethod
    def hash (request, hash = 'md5', digest = 'hex'):
        h = hashlib.new (hash, request)
        if digest == 'hex':
            return h.hexdigest ()
        elif digest == 'base64':
            return base64.b64encode (h.digest ())
        return h.digest ()

    @staticmethod
    def hmac (request, secret, hash = hashlib.sha256, digest = 'hex'):
        h = hmac.new (secret, request, hash)
        if digest == 'hex':
            return h.hexdigest ()
        elif digest == 'base64':
            return base64.b64encode (h.digest ())
        return h.digest ()

    @staticmethod
    def base64urlencode (s):
        return base64.urlsafe_b64encode (s).replace ('=', '')

    @staticmethod
    def jwt (request, secret, hash = hashlib.sha256, alg = 'HS256'):
        encodedHeader = Market.base64urlencode (json.dumps ({ 'alg': alg, 'typ': 'JWT' }, separators = (',', ':')))
        encodedData = Market.base64urlencode (json.dumps (request, separators = (',', ':')))
        token = encodedHeader + '.' + encodedData
        signature = Market.base64urlencode (Market.hmac (token, secret, hash, 'binary'))
        return token + '.' + signature

    def nonce (self):
        return Market.seconds ()

    def load_products (self, reload = False):
        if not reload:
            if self.products:
                return self.products
        self.products = Market.indexBy (self.fetchProducts (), 'symbol')
        return self.products

    def loadProducts  (self, reload = False):
        return self.load_products  ()
    
    def fetchProducts (self):
        return self.fetch_products ()

    def product (self, product):
        isString = isinstance (product, basestring)
        if isString and self.products and (product in self.products):
            return self.products [product]
        return product

    def product_id (self, product):
        p = self.product (product)
        return p['id'] if type (p) is dict else product

    def productId  (self, product):
        return self.product_id (product)

    def symbol (self, product):
        p = self.product (product)
        return p['symbol'] if type (p) is dict else product

    def fetchBalance (self):
        return self.fetch_balance ()
    
    def fetchOrderBook (self, product): 
        return self.fetch_order_book (product)
    
    def fetchTicker (self, product):
        return self.fetch_ticker (product)
    
    def fetchTrades (self, product): 
        return self.fetch_trades (product)

    def create_limit_buy_order (self, product, amount, price, params = {}):
        return self.create_order (product, 'limit', 'buy', amount, price, params)

    def create_limit_sell_order (self, product, amount, price, params = {}):
        return self.create_order (product, 'limit', 'sell', amount, price, params)

    def create_market_buy_order (self, product, amount, params = {}):
        return self.create_order (product, 'market', 'buy', amount, params)

    def create_market_sell_order (self, product, amount, params = {}):
        return self.create_order (product, 'market', 'sell', amount, params)

    def createLimitBuyOrder (self, product, amount, price, params = {}):
        return self.create_limit_buy_order (product, amount, price, params)

    def createLimitSellOrder (self, product, amount, price, params = {}):
        return self.create_limit_sell_order (product, amount, price, params)

    def createMarketBuyOrder (self, product, amount, params = {}): 
        return self.create_market_buy_order (product, amount, params)

    def createMarketSellOrder (self, product, amount, params = {}):
        return self.create_market_sell_order (product, amount, params)

#==============================================================================

class _1broker (Market):

    def __init__ (self, config = {}):
        params = {
            'id': '_1broker',
            'name': '1Broker',
            'countries': 'US',
            'rateLimit': 2000,
            'version': 'v2',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766021-420bd9fc-5ecb-11e7-8ed6-56d0081efed2.jpg',
                'api': 'https://1broker.com/api',        
                'www': 'https://1broker.com',
                'doc': 'https://1broker.com/?c=en/content/api-documentation',
            },
            'api': {
                'private': {
                    'get': [
                        'market/bars',
                        'market/categories',
                        'market/details',
                        'market/list',
                        'market/quotes',
                        'market/ticks',
                        'order/cancel',
                        'order/create',
                        'order/open',
                        'position/close',
                        'position/close_cancel',
                        'position/edit',
                        'position/history',
                        'position/open',
                        'position/shared/get',
                        'social/profile_statistics',
                        'social/profile_trades',
                        'user/bitcoin_deposit_address',
                        'user/details',
                        'user/overview',
                        'user/quota_status',
                        'user/transaction_log',
                    ],
                },
            },
        }
        params.update (config)
        super (_1broker, self).__init__ (params)

    def fetchCategories (self):
        categories = self.privateGetMarketCategories ()
        return categories['response']

    def fetch_products (self):
        categories = self.fetchCategories ()
        result = []
        for c in range (0, len (categories)):
            category = categories[c]
            products = self.privateGetMarketList ({ 
                'category': category.lower (),
            })
            for p in range (0, len (products['response'])):
                product = products['response'][p]
                if (category == 'FOREX') or (category == 'CRYPTO'):
                    id = product['symbol']
                    symbol = product['name']
                    base, quote = symbol.split ('/')
                    result.append ({
                        'id': id,
                        'symbol': symbol,
                        'base': base,
                        'quote': quote,
                        'info': product,
                    })
                else:
                    id = product['symbol']
                    symbol = product['symbol']
                    name = product['name']
                    type = product['type'].lower ()
                    result.append ({
                        'id': id,
                        'symbol': symbol,
                        'name': name,
                        'type': type,
                        'info': product,
                    })
        return result

    def fetch_balance (self):
        return self.privateGetUserOverview ()

    def fetch_order_book (self, product):
        response = self.privateGetMarketQuotes ({
            'symbols': self.product_id (product),
        })
        orderbook = response['response'][0]
        timestamp = self.parse8601 (orderbook['updated'])
        bidPrice = float (orderbook['bid'])
        askPrice = float (orderbook['ask'])
        bid = [ bidPrice, None ]
        ask = [ askPrice, None ]
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'bids': [ bid ],
            'asks': [ ask ],
        }

    def fetch_ticker (self, product):
        result = self.privateGetMarketBars ({
            'symbol': self.product_id (product),
            'resolution': 60,
            'limit': 1,
        })
        orderbook = self.fetchOrderBook (product)
        ticker = result['response'][0]
        timestamp = self.parse8601 (ticker['date'])
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['h']),
            'low': float (ticker['l']),
            'bid': orderbook['bids'][0]['price'],
            'ask': orderbook['asks'][0]['price'],
            'vwap': None,
            'open': float (ticker['o']),
            'close': float (ticker['c']),
            'first': None,
            'last': None,
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': None,
        } 

    def create_order (self, product, type, side, amount, price = None, params = {}):
        order = {
            'symbol': self.product_id (product),
            'margin': amount,
            'direction': 'short' if (side == 'sell') else 'long',
            'leverage': 1,
            'type': side,
        }
        if type == 'limit':
            order['price'] = price
        else:
            order['type'] += '_market'
        return self.privateGetOrderCreate (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        if not (self.apiKey) or len ((self.apyKey) < 1):
            raise Exception (self.id + ' requires apiKey for all requests') 
        url = self.urls['api'] + '/' + self.version + '/' + path + '.php'
        query = self.extend ({ 'token': self.apiKey }, params)
        url += '?' + _urlencode.urlencode (query)
        return self.fetch (url, method)

#------------------------------------------------------------------------------

class cryptocapital (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'cryptocapital',
            'name': 'Crypto Capital',
            'comment': 'Crypto Capital API',
            'countries': 'PA', # Panama
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27993158-7a13f140-64ac-11e7-89cc-a3b441f0b0f8.jpg',
                'www': 'https://cryptocapital.co',
                'doc': 'https://github.com/cryptocap',
            },
            'api': {
                'public': {
                    'get': [
                        'stats',
                        'historical-prices',
                        'order-book',
                        'transactions',
                    ],
                },
                'private': {            
                    'post': [
                        'balances-and-info',
                        'open-orders',
                        'user-transactions',
                        'btc-deposit-address/get',
                        'btc-deposit-address/new',
                        'deposits/get',
                        'withdrawals/get',
                        'orders/new',
                        'orders/edit',
                        'orders/cancel',
                        'orders/status',
                        'withdrawals/new',
                    ],
                },
            },
        }
        params.update (config)
        super (cryptocapital, self).__init__ (params)

    def fetch_balance (self):
        return self.privatePostBalancesAndInfo ()

    def fetch_order_book (self, product):
        response = self.publicGetOrderBook ({
            'currency': self.product_id (product),
        })
        orderbook = response['order-book']
        timestamp = self.milliseconds ()
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = { 'bids': 'bid', 'asks': 'ask' }
        keys = list (sides.keys ())
        for k in range (0, len (keys)):
            key = keys[k]
            side = sides[key]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                timestamp = int (order['timestamp']) * 1000
                price = float (order['price'])
                amount = float (order['order_amount'])
                result[key].append ([ price, amount, timestamp ])
        return result

    def fetch_ticker (self, product):
        response = self.publicGetStats ({
            'currency': self.product_id (product),
        })
        ticker = response['stats']
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['max']),
            'low': float (ticker['min']),
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': None,
            'open': float (ticker['open']),
            'close': None,
            'first': None,
            'last': float (ticker['last_price']),
            'change': float (ticker['daily_change']),
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['total_btc_traded']),
        }

    def fetch_trades (self, product):
        return self.publicGetTransactions ({
            'currency': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        order = {
            'side': side,
            'type': type,
            'currency': self.product_id (product),
            'amount': amount,
        }
        if type == 'limit':
            order['limit_price'] = price
        return self.privatePostOrdersNew (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + path
        if type == 'public':
            if params:
                url += '?' + _urlencode.urlencode (params)
        else:
            query = self.extend ({
                'api_key': self.apiKey,
                'nonce': self.nonce (),
            }, params)
            query['signature'] = self.hmac (json.dumps (query), self.secret)
            body = json.dumps (query)
            headers = { 'Content-Type': 'application/json' }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class _1btcxe (cryptocapital):

    def __init__ (self, config = {}):
        params = {
            'id': '_1btcxe',
            'name': '1BTCXE',
            'countries': 'PA', # Panama
            'comment': 'Crypto Capital API',
            'urls': { 
                'logo': 'https://user-images.githubusercontent.com/1294454/27766049-2b294408-5ecc-11e7-85cc-adaff013dc1a.jpg',
                'api': 'https://1btcxe.com/api',
                'www': 'https://1btcxe.com',
                'doc': 'https://1btcxe.com/api-docs.php',
            },    
            'products': {
                'BTC/USD': { 'id': 'USD', 'symbol': 'BTC/USD', 'base': 'BTC', 'quote': 'USD', },
                'BTC/EUR': { 'id': 'EUR', 'symbol': 'BTC/EUR', 'base': 'BTC', 'quote': 'EUR', },
                'BTC/CNY': { 'id': 'CNY', 'symbol': 'BTC/CNY', 'base': 'BTC', 'quote': 'CNY', },
                'BTC/RUB': { 'id': 'RUB', 'symbol': 'BTC/RUB', 'base': 'BTC', 'quote': 'RUB', },
                'BTC/CHF': { 'id': 'CHF', 'symbol': 'BTC/CHF', 'base': 'BTC', 'quote': 'CHF', },
                'BTC/JPY': { 'id': 'JPY', 'symbol': 'BTC/JPY', 'base': 'BTC', 'quote': 'JPY', },
                'BTC/GBP': { 'id': 'GBP', 'symbol': 'BTC/GBP', 'base': 'BTC', 'quote': 'GBP', },
                'BTC/CAD': { 'id': 'CAD', 'symbol': 'BTC/CAD', 'base': 'BTC', 'quote': 'CAD', },
                'BTC/AUD': { 'id': 'AUD', 'symbol': 'BTC/AUD', 'base': 'BTC', 'quote': 'AUD', },
                'BTC/AED': { 'id': 'AED', 'symbol': 'BTC/AED', 'base': 'BTC', 'quote': 'AED', },
                'BTC/BGN': { 'id': 'BGN', 'symbol': 'BTC/BGN', 'base': 'BTC', 'quote': 'BGN', },
                'BTC/CZK': { 'id': 'CZK', 'symbol': 'BTC/CZK', 'base': 'BTC', 'quote': 'CZK', },
                'BTC/DKK': { 'id': 'DKK', 'symbol': 'BTC/DKK', 'base': 'BTC', 'quote': 'DKK', },
                'BTC/HKD': { 'id': 'HKD', 'symbol': 'BTC/HKD', 'base': 'BTC', 'quote': 'HKD', },
                'BTC/HRK': { 'id': 'HRK', 'symbol': 'BTC/HRK', 'base': 'BTC', 'quote': 'HRK', },
                'BTC/HUF': { 'id': 'HUF', 'symbol': 'BTC/HUF', 'base': 'BTC', 'quote': 'HUF', },
                'BTC/ILS': { 'id': 'ILS', 'symbol': 'BTC/ILS', 'base': 'BTC', 'quote': 'ILS', },
                'BTC/INR': { 'id': 'INR', 'symbol': 'BTC/INR', 'base': 'BTC', 'quote': 'INR', },
                'BTC/MUR': { 'id': 'MUR', 'symbol': 'BTC/MUR', 'base': 'BTC', 'quote': 'MUR', },
                'BTC/MXN': { 'id': 'MXN', 'symbol': 'BTC/MXN', 'base': 'BTC', 'quote': 'MXN', },
                'BTC/NOK': { 'id': 'NOK', 'symbol': 'BTC/NOK', 'base': 'BTC', 'quote': 'NOK', },
                'BTC/NZD': { 'id': 'NZD', 'symbol': 'BTC/NZD', 'base': 'BTC', 'quote': 'NZD', },
                'BTC/PLN': { 'id': 'PLN', 'symbol': 'BTC/PLN', 'base': 'BTC', 'quote': 'PLN', },
                'BTC/RON': { 'id': 'RON', 'symbol': 'BTC/RON', 'base': 'BTC', 'quote': 'RON', },
                'BTC/SEK': { 'id': 'SEK', 'symbol': 'BTC/SEK', 'base': 'BTC', 'quote': 'SEK', },
                'BTC/SGD': { 'id': 'SGD', 'symbol': 'BTC/SGD', 'base': 'BTC', 'quote': 'SGD', },
                'BTC/THB': { 'id': 'THB', 'symbol': 'BTC/THB', 'base': 'BTC', 'quote': 'THB', },
                'BTC/TRY': { 'id': 'TRY', 'symbol': 'BTC/TRY', 'base': 'BTC', 'quote': 'TRY', },
                'BTC/ZAR': { 'id': 'ZAR', 'symbol': 'BTC/ZAR', 'base': 'BTC', 'quote': 'ZAR', },
            },
        }
        params.update (config)
        super (_1btcxe, self).__init__ (params)

#------------------------------------------------------------------------------

class anxpro (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'anxpro',
            'name': 'ANXPro',
            'countries': [ 'JP', 'SG', 'HK', 'NZ', ],
            'version': '2',
            'rateLimit': 2000,
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27765983-fd8595da-5ec9-11e7-82e3-adb3ab8c2612.jpg',
                'api': 'https://anxpro.com/api',
                'www': 'https://anxpro.com',
                'doc': 'https://anxpro.com/pages/api',
            },
            'api': {
                'public': {
                    'get': [
                        '{currency_pair}/money/ticker',
                        '{currency_pair}/money/depth/full',
                        '{currency_pair}/money/trade/fetch', # disabled by ANXPro
                    ],    
                },
                'private': {
                    'post': [
                        '{currency_pair}/money/order/add',
                        '{currency_pair}/money/order/cancel',
                        '{currency_pair}/money/order/quote',
                        '{currency_pair}/money/order/result',
                        '{currency_pair}/money/orders',
                        'money/{currency}/address',
                        'money/{currency}/send_simple',
                        'money/info',
                        'money/trade/list',
                        'money/wallet/history',
                    ],    
                },
            },
            'products': {
                'BTC/USD': { 'id': 'BTCUSD', 'symbol': 'BTC/USD', 'base': 'BTC', 'quote': 'USD' },
                'BTC/HKD': { 'id': 'BTCHKD', 'symbol': 'BTC/HKD', 'base': 'BTC', 'quote': 'HKD' },
                'BTC/EUR': { 'id': 'BTCEUR', 'symbol': 'BTC/EUR', 'base': 'BTC', 'quote': 'EUR' },
                'BTC/CAD': { 'id': 'BTCCAD', 'symbol': 'BTC/CAD', 'base': 'BTC', 'quote': 'CAD' },
                'BTC/AUD': { 'id': 'BTCAUD', 'symbol': 'BTC/AUD', 'base': 'BTC', 'quote': 'AUD' },
                'BTC/SGD': { 'id': 'BTCSGD', 'symbol': 'BTC/SGD', 'base': 'BTC', 'quote': 'SGD' },
                'BTC/JPY': { 'id': 'BTCJPY', 'symbol': 'BTC/JPY', 'base': 'BTC', 'quote': 'JPY' },
                'BTC/GBP': { 'id': 'BTCGBP', 'symbol': 'BTC/GBP', 'base': 'BTC', 'quote': 'GBP' },
                'BTC/NZD': { 'id': 'BTCNZD', 'symbol': 'BTC/NZD', 'base': 'BTC', 'quote': 'NZD' },
                'LTC/BTC': { 'id': 'LTCBTC', 'symbol': 'LTC/BTC', 'base': 'LTC', 'quote': 'BTC' },
                'DOGE/BTC': { 'id': 'DOGEBTC', 'symbol': 'DOGE/BTC', 'base': 'DOGE', 'quote': 'BTC' },
                'STR/BTC': { 'id': 'STRBTC', 'symbol': 'STR/BTC', 'base': 'STR', 'quote': 'BTC' },
                'XRP/BTC': { 'id': 'XRPBTC', 'symbol': 'XRP/BTC', 'base': 'XRP', 'quote': 'BTC' },
            },
        }
        params.update (config)
        super (anxpro, self).__init__ (params)

    def fetch_balance (self):
        return self.privatePostMoneyInfo ()

    def fetch_order_book (self, product):
        response = self.publicGetCurrencyPairMoneyDepthFull ({
            'currency_pair': self.product_id (product),
        })
        orderbook = response['data']
        timestamp = int (orderbook['dataUpdateTime'] / 1000)
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = [ 'bids', 'asks' ]
        for s in range (0, len (sides)):
            side = sides[s]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = float (order['price'])
                amount = float (order['amount'])
                result[side].append ([ price, amount ])
        return result

    def fetch_ticker (self, product):
        response = self.publicGetCurrencyPairMoneyTicker ({
            'currency_pair': self.product_id (product),
        })
        ticker = response['data']
        timestamp = int (ticker['dataUpdateTime'] / 1000)
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']['value']),
            'low': float (ticker['low']['value']),
            'bid': float (ticker['buy']['value']),
            'ask': float (ticker['sell']['value']),
            'vwap': float (ticker['vwap']['value']),
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']['value']),
            'change': None,
            'percentage': None,
            'average': float (ticker['avg']['value']),
            'baseVolume': None,
            'quoteVolume': float (ticker['vol']['value']),
        }

    def fetch_trades (self, product):
        return self.publicGetCurrencyPairMoneyTradeFetch ({
            'currency_pair': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        order = {
            'currency_pair': self.product_id (product),
            'amount_int': amount,
            'type': side,
        }
        if type == 'limit':
            order['price_int'] = price
        return self.privatePostCurrencyPairOrderAdd (self.extend (order, params))

    def nonce (self):
        return self.milliseconds ()

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        request = self.implode_params (path, params)
        query = self.omit (params, self.extract_params (path))
        url = self.urls['api'] + '/' + self.version + '/' + request
        if type == 'public':
            if query:
                url += '?' + _urlencode.urlencode (query)
        else:
            nonce = self.nonce ()
            body = _urlencode.urlencode (self.extend ({ 'nonce': nonce }, query))
            secret = base64.b64decode (self.secret)
            auth = request + "\0" + body
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Rest-Key': self.apiKey,
                'Rest-Sign': self.hmac (auth, secret, hashlib.sha512, 'base64'),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class bit2c (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'bit2c',
            'name': 'Bit2C',
            'countries': 'IL', # Israel
            'rateLimit': 3000,
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766119-3593220e-5ece-11e7-8b3a-5a041f6bcc3f.jpg',
                'api': 'https://www.bit2c.co.il',
                'www': 'https://www.bit2c.co.il',
                'doc': [
                    'https://www.bit2c.co.il/home/api',
                    'https://github.com/OferE/bit2c',
                ],
            },
            'api': {
                'public': {
                    'get': [
                        'Exchanges/{pair}/Ticker',
                        'Exchanges/{pair}/orderbook',
                        'Exchanges/{pair}/trades',
                    ],
                },
                'private': {
                    'post': [
                        'Account/Balance',
                        'Account/Balance/v2',
                        'Merchant/CreateCheckout',
                        'Order/AccountHistory',
                        'Order/AddCoinFundsRequest',
                        'Order/AddFund',
                        'Order/AddOrder',
                        'Order/AddOrderMarketPriceBuy',
                        'Order/AddOrderMarketPriceSell',
                        'Order/CancelOrder',
                        'Order/MyOrders',
                        'Payment/GetMyId',
                        'Payment/Send',
                    ],
                },
            },
            'products': {
                'BTC/NIS': { 'id': 'BtcNis', 'symbol': 'BTC/NIS', 'base': 'BTC', 'quote': 'NIS' },
                'LTC/BTC': { 'id': 'LtcBtc', 'symbol': 'LTC/BTC', 'base': 'LTC', 'quote': 'BTC' },
                'LTC/NIS': { 'id': 'LtcNis', 'symbol': 'LTC/NIS', 'base': 'LTC', 'quote': 'NIS' },
            },
        }
        params.update (config)
        super (bit2c, self).__init__ (params)

    def fetch_balance (self):
        return self.privatePostAccountBalanceV2 ()

    def fetch_order_book (self, product):
        orderbook = self.publicGetExchangesPairOrderbook ({
            'pair': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = [ 'bids', 'asks' ]
        for s in range (0, len (sides)):
            side = sides[s]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = order[0]
                amount = order[1]
                timestamp = order[2] * 1000
                result[side].append ([ price, amount, timestamp ])
        return result

    def fetch_ticker (self, product):
        ticker = self.publicGetExchangesPairTicker ({
            'pair': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['h']),
            'low': float (ticker['l']),
            'bid': None,
            'ask': None,
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['ll']),
            'change': None,
            'percentage': None,
            'average': float (ticker['av']),
            'baseVolume': None,
            'quoteVolume': float (ticker['a']),
        }

    def fetch_trades (self, product):
        return self.publicGetExchangesPairTrades ({
            'pair': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        method = 'privatePostOrderAddOrder'
        order = {
            'Amount': amount,
            'Pair': self.product_id (product),
        }
        if type == 'market':
            method += 'MarketPrice' + self.capitalize (side)
        else:
            order['Price'] = price
            order['Total'] = amount * price
            order['IsBid'] = (side == 'buy')
        return getattr (self, method) (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.implode_params (path, params)
        if type == 'public':
            url += '.json'
        else:
            nonce = self.nonce ()
            query = self.extend ({ 'nonce': nonce }, params)
            body = _urlencode.urlencode (query)
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': len (body),
                'key': self.apiKey,
                'sign': self.hmac (body, self.secret, hashlib.sha512, 'base64'),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class bitbay (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'bitbay',
            'name': 'BitBay',
            'countries': [ 'PL', 'EU', ], # Poland
            'rateLimit': 1000,
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766132-978a7bd8-5ece-11e7-9540-bc96d1e9bbb8.jpg',
                'www': 'https://bitbay.net',
                'api': {
                    'public': 'https://bitbay.net/API/Public',
                    'private': 'https://bitbay.net/API/Trading/tradingApi.php',
                },
                'doc': [
                    'https://bitbay.net/public-api',
                    'https://bitbay.net/account/tab-api',
                    'https://github.com/BitBayNet/API',
                ], 
            },
            'api': {
                'public': {
                    'get': [
                        '{id}/all',
                        '{id}/market',
                        '{id}/orderbook',
                        '{id}/ticker',
                        '{id}/trades',
                    ],
                },
                'private': {
                    'post': [
                        'info',
                        'trade',
                        'cancel',
                        'orderbook',
                        'orders',
                        'transfer',
                        'withdraw',
                        'history',
                        'transactions',
                    ],
                },
            },
            'products': {  
                'BTC/USD': { 'id': 'BTCUSD', 'symbol': 'BTC/USD', 'base': 'BTC', 'quote': 'USD' },
                'BTC/EUR': { 'id': 'BTCEUR', 'symbol': 'BTC/EUR', 'base': 'BTC', 'quote': 'EUR' },
                'BTC/PLN': { 'id': 'BTCPLN', 'symbol': 'BTC/PLN', 'base': 'BTC', 'quote': 'PLN' },
                'LTC/USD': { 'id': 'LTCUSD', 'symbol': 'LTC/USD', 'base': 'LTC', 'quote': 'USD' },
                'LTC/EUR': { 'id': 'LTCEUR', 'symbol': 'LTC/EUR', 'base': 'LTC', 'quote': 'EUR' },
                'LTC/PLN': { 'id': 'LTCPLN', 'symbol': 'LTC/PLN', 'base': 'LTC', 'quote': 'PLN' },
                'LTC/BTC': { 'id': 'LTCBTC', 'symbol': 'LTC/BTC', 'base': 'LTC', 'quote': 'BTC' },
                'ETH/USD': { 'id': 'ETHUSD', 'symbol': 'ETH/USD', 'base': 'ETH', 'quote': 'USD' },
                'ETH/EUR': { 'id': 'ETHEUR', 'symbol': 'ETH/EUR', 'base': 'ETH', 'quote': 'EUR' },
                'ETH/PLN': { 'id': 'ETHPLN', 'symbol': 'ETH/PLN', 'base': 'ETH', 'quote': 'PLN' },
                'ETH/BTC': { 'id': 'ETHBTC', 'symbol': 'ETH/BTC', 'base': 'ETH', 'quote': 'BTC' },
                'LSK/USD': { 'id': 'LSKUSD', 'symbol': 'LSK/USD', 'base': 'LSK', 'quote': 'USD' },
                'LSK/EUR': { 'id': 'LSKEUR', 'symbol': 'LSK/EUR', 'base': 'LSK', 'quote': 'EUR' },
                'LSK/PLN': { 'id': 'LSKPLN', 'symbol': 'LSK/PLN', 'base': 'LSK', 'quote': 'PLN' },
                'LSK/BTC': { 'id': 'LSKBTC', 'symbol': 'LSK/BTC', 'base': 'LSK', 'quote': 'BTC' },
            },
        }
        params.update (config)
        super (bitbay, self).__init__ (params)

    def fetch_balance (self):
        return self.privatePostInfo ()

    def fetch_order_book (self, product):
        orderbook = self.publicGetIdOrderbook ({
            'id': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        result = {
            'bids': orderbook['bids'],
            'asks': orderbook['asks'],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        return result

    def fetch_ticker (self, product):
        ticker = self.publicGetIdTicker ({
            'id': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['max']),
            'low': float (ticker['min']),
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': float (ticker['vwap']),
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': float (ticker['average']),
            'baseVolume': None,
            'quoteVolume': float (ticker['volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetIdTrades ({
            'id': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        p = self.product (product)
        return self.privatePostTrade (self.extend ({
            'type': side,
            'currency': p['base'],
            'amount': amount,
            'payment_currency': p['quote'],
            'rate': price,
        }, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'][type]
        if type == 'public':
            url += '/' + self.implode_params (path, params) + '.json'
        else:
            body = _urlencode.urlencode (self.extend ({
                'method': path,
                'moment': self.nonce (),
            }, params))
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': len (body),
                'API-Key': self.apiKey,
                'API-Hash': self.hmac (body, self.secret, hashlib.sha512),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class bitbays (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'bitbays',
            'name': 'BitBays',
            'countries': [ 'CN', 'GB', 'HK', 'AU', 'CA' ],
            'rateLimit': 2000,
            'version': 'v1',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27808599-983687d2-6051-11e7-8d95-80dfcbe5cbb4.jpg',
                'api': 'https://bitbays.com/api',
                'www': 'https://bitbays.com',
                'doc': 'https://bitbays.com/help/api/',
            },
            'api': {
                'public': {
                    'get': [
                        'ticker',
                        'trades',
                        'depth',
                    ],
                },
                'private': {
                    'post': [
                        'cancel',
                        'info',
                        'orders',
                        'order',
                        'transactions',
                        'trade',
                    ],
                },
            },
            'products': {
                'BTC/USD': { 'id': 'btc_usd', 'symbol': 'BTC/USD', 'base': 'BTC', 'quote': 'USD' },
                'BTC/CNY': { 'id': 'btc_cny', 'symbol': 'BTC/CNY', 'base': 'BTC', 'quote': 'CNY' },
                'ODS/BTC': { 'id': 'ods_btc', 'symbol': 'ODS/BTC', 'base': 'ODS', 'quote': 'BTC' },
                'LSK/BTC': { 'id': 'lsk_btc', 'symbol': 'LSK/BTC', 'base': 'LSK', 'quote': 'BTC' },
                'LSK/CNY': { 'id': 'lsk_cny', 'symbol': 'LSK/CNY', 'base': 'LSK', 'quote': 'CNY' },
            },
        }
        params.update (config)
        super (bitbays, self).__init__ (params)

    def fetch_order_book (self, product):
        response = self.publicGetDepth ({
            'market': self.product_id (product),
        })
        orderbook = response['result']
        timestamp = self.milliseconds ()
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = [ 'bids', 'asks' ]
        for s in range (0, len (sides)):
            side = sides[s]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = float (order[0])
                amount = float (order[1])
                result[side].append ([ price, amount ])
        return result

    def fetch_ticker (self, product):
        response = self.publicGetTicker ({
            'market': self.product_id (product),
        })
        ticker = response['result']
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['buy']),
            'ask': float (ticker['sell']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['vol']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTrades ({
            'market': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        order = {
            'market': self.product_id (product),
            'op': side,
            'amount': amount,
        }
        if type == 'market':
            order['order_type'] = 1
            order['price'] = price
        else:
            order['order_type'] = 0
        return self.privatePostTrade (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.version + '/' + path
        if type == 'public':
            if params:
                url += '?' + _urlencode.urlencode (params)
        else:
            nonce = self.nonce ()
            body = _urlencode.urlencode (self.extend ({
                'nonce': nonce,
            }, params))
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': len (body),
                'Key': self.apiKey,
                'Sign': self.hmac (body, self.secret, hashlib.sha512),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class bitcoincoid (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'bitcoincoid',
            'name': 'Bitcoin.co.id',
            'countries': 'ID', # Indonesia
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766138-043c7786-5ecf-11e7-882b-809c14f38b53.jpg',
                'api': {
                    'public': 'https://vip.bitcoin.co.id/api',
                    'private': 'https://vip.bitcoin.co.id/tapi',
                },
                'www': 'https://www.bitcoin.co.id',
                'doc': [
                    'https://vip.bitcoin.co.id/trade_api',
                    'https://vip.bitcoin.co.id/downloads/BITCOINCOID-API-DOCUMENTATION.pdf',
                ],
            },
            'api': {
                'public': {
                    'get': [
                        '{pair}/ticker',
                        '{pair}/trades',
                        '{pair}/depth',
                    ],
                },
                'private': {
                    'post': [
                        'getInfo',
                        'transHistory',
                        'trade',
                        'tradeHistory',
                        'openOrders',
                        'cancelOrder',
                    ],
                },
            },
            'products': {
                'BTC/IDR':  { 'id': 'btc_idr', 'symbol': 'BTC/IDR', 'base': 'BTC', 'quote': 'IDR', 'baseId': 'btc', 'quoteId': 'idr' },
                'BTS/BTC':  { 'id': 'bts_btc', 'symbol': 'BTS/BTC', 'base': 'BTS', 'quote': 'BTC', 'baseId': 'bts', 'quoteId': 'btc' },
                'DASH/BTC': { 'id': 'drk_btc', 'symbol': 'DASH/BTC', 'base': 'DASH', 'quote': 'BTC', 'baseId': 'drk', 'quoteId': 'btc' },
                'DOGE/BTC': { 'id': 'doge_btc', 'symbol': 'DOGE/BTC', 'base': 'DOGE', 'quote': 'BTC', 'baseId': 'doge', 'quoteId': 'btc' },
                'ETH/BTC':  { 'id': 'eth_btc', 'symbol': 'ETH/BTC', 'base': 'ETH', 'quote': 'BTC', 'baseId': 'eth', 'quoteId': 'btc' },
                'LTC/BTC':  { 'id': 'ltc_btc', 'symbol': 'LTC/BTC', 'base': 'LTC', 'quote': 'BTC', 'baseId': 'ltc', 'quoteId': 'btc' },
                'NXT/BTC':  { 'id': 'nxt_btc', 'symbol': 'NXT/BTC', 'base': 'NXT', 'quote': 'BTC', 'baseId': 'nxt', 'quoteId': 'btc' },
                'STR/BTC':  { 'id': 'str_btc', 'symbol': 'STR/BTC', 'base': 'STR', 'quote': 'BTC', 'baseId': 'str', 'quoteId': 'btc' },
                'NEM/BTC':  { 'id': 'nem_btc', 'symbol': 'NEM/BTC', 'base': 'NEM', 'quote': 'BTC', 'baseId': 'nem', 'quoteId': 'btc' },
                'XRP/BTC':  { 'id': 'xrp_btc', 'symbol': 'XRP/BTC', 'base': 'XRP', 'quote': 'BTC', 'baseId': 'xrp', 'quoteId': 'btc' },
            },
        }
        params.update (config)
        super (bitcoincoid, self).__init__ (params)

    def fetch_balance (self):
        return self.privatePostGetInfo ()

    def fetch_order_book (self, product):
        orderbook = self.publicGetPairDepth ({
            'pair': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = { 'bids': 'buy', 'asks': 'sell' }
        keys = list (sides.keys ())
        for k in range (0, len (keys)):
            key = keys[k]
            side = sides[key]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = float (order[0])
                amount = float (order[1])
                result[key].append ([ price, amount ])
        return result

    def fetch_ticker (self, product):
        pair = self.product (product)
        response = self.publicGetPairTicker ({
            'pair': pair['id'],
        })
        ticker = response['ticker']
        timestamp = float (ticker['server_time']) * 1000
        baseVolume = 'vol_' + pair['baseId'].lower ()
        quoteVolume = 'vol_' + pair['quoteId'].lower ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['buy']),
            'ask': float (ticker['sell']),
            'vwap': float (ticker['vwap']),
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': float (ticker['average']),
            'baseVolume': float (ticker[baseVolume]),
            'quoteVolume': float (ticker[quoteVolume]),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetPairTrades ({
            'pair': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        p = self.product (product)
        order = {
            'pair': p['id'],
            'type': side,
            'price': price,
        }
        base = p['base'].lower ()
        order[base] = amount
        return self.privatePostTrade (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'][type]
        if type == 'public':
            url += '/' + self.implode_params (path, params)
        else:
            body = _urlencode.urlencode (self.extend ({
                'method': path,
                'nonce': self.nonce (),
            }, params))
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': len (body),
                'Key': self.apiKey,
                'Sign': self.hmac (body, self.secret, hashlib.sha512),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class bitfinex (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'bitfinex',
            'name': 'Bitfinex',
            'countries': 'US',
            'version': 'v1',
            'rateLimit': 2000,
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766244-e328a50c-5ed2-11e7-947b-041416579bb3.jpg',
                'api': 'https://api.bitfinex.com',
                'www': 'https://www.bitfinex.com',
                'doc': [
                    'https://bitfinex.readme.io/v1/docs',
                    'https://bitfinex.readme.io/v2/docs',
                    'https://github.com/bitfinexcom/bitfinex-api-node',
                ],
            },
            'api': {
                'public': {
                    'get': [
                        'book/{symbol}',
                        'candles/{symbol}',
                        'lendbook/{currency}',
                        'lends/{currency}',
                        'pubticker/{symbol}',
                        'stats/{symbol}',
                        'symbols',
                        'symbols_details',
                        'today',
                        'trades/{symbol}',                
                    ],
                },
                'private': {
                    'post': [
                        'account_infos',
                        'balances',
                        'basket_manage',
                        'credits',
                        'deposit/new',
                        'funding/close',
                        'history',
                        'history/movements',
                        'key_info',
                        'margin_infos',
                        'mytrades',
                        'offer/cancel',
                        'offer/new',
                        'offer/status',
                        'offers',
                        'order/cancel',
                        'order/cancel/all',
                        'order/cancel/multi',
                        'order/cancel/replace',
                        'order/new',
                        'order/new/multi',
                        'order/status',
                        'orders',
                        'position/claim',
                        'positions',
                        'summary',
                        'taken_funds',
                        'total_taken_funds',
                        'transfer',
                        'unused_taken_funds',
                        'withdraw',
                    ],
                },
            },
        }
        params.update (config)
        super (bitfinex, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetSymbolsDetails ()
        result = []
        for p in range (0, len (products)):
            product = products[p]
            id = product['pair'].upper ()
            base = id[0:3]
            quote = id[3:6]
            # issue #4 Bitfinex names Dash as DSH, instead of DASH
            if base == 'DSH':
                base = 'DASH'
            symbol = base + '/' + quote
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.privatePostBalances ()

    def fetch_order_book (self, product):
        orderbook = self.publicGetBookSymbol ({ 
            'symbol': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = [ 'bids', 'asks' ]
        for s in range (0, len (sides)):
            side = sides[s]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = float (order['price'])
                amount = float (order['amount'])
                timestamp = int (float (order['timestamp']))
                result[side].append ([ price, amount, timestamp ])
        return result

    def fetch_ticker (self, product):
        ticker = self.publicGetPubtickerSymbol ({
            'symbol': self.product_id (product),
        })
        timestamp = float (ticker['timestamp']) * 1000
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last_price']),
            'change': None,
            'percentage': None,
            'average': float (ticker['mid']),
            'baseVolume': None,
            'quoteVolume': float (ticker['volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTradesSymbol ({
            'symbol': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        return self.privatePostOrderNew (self.extend ({
            'symbol': self.product_id (product),
            'amount': str (amount),
            'price': str (price),
            'side': side,
            'type': 'exchange ' + type,
            'ocoorder': false,
            'buy_price_oco': 0,
            'sell_price_oco': 0,
        }, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        request = '/' + self.version + '/' + self.implode_params (path, params)
        query = self.omit (params, self.extract_params (path))
        url = self.urls['api'] + request
        if type == 'public':            
            if query:
                url += '?' + _urlencode.urlencode (query)
        else:
            nonce = self.nonce ()
            query = self.extend ({
                'nonce': str (nonce),
                'request': request,
            }, query)
            payload = base64.b64encode (json.dumps (query))
            headers = {
                'X-BFX-APIKEY': self.apiKey,
                'X-BFX-PAYLOAD': payload,
                'X-BFX-SIGNATURE': self.hmac (payload, self.secret, hashlib.sha384),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class bitlish (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'bitlish',
            'name': 'bitlish',
            'countries': [ 'GB', 'EU', 'RU', ],
            'rateLimit': 2000,    
            'version': 'v1',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766275-dcfc6c30-5ed3-11e7-839d-00a846385d0b.jpg',
                'api': 'https://bitlish.com/api',
                'www': 'https://bitlish.com',
                'doc': 'https://bitlish.com/api',
            },
            'api': {
                'public': {
                    'get': [
                        'instruments',
                        'ohlcv',
                        'pairs',
                        'tickers',
                        'trades_depth',
                        'trades_history',
                    ],
                },
                'private': {
                    'post': [
                        'accounts_operations',
                        'balance',
                        'cancel_trade',
                        'cancel_trades_by_ids',
                        'cancel_all_trades',
                        'create_bcode',
                        'create_template_wallet',
                        'create_trade',
                        'deposit',
                        'list_accounts_operations_from_ts',
                        'list_active_trades',
                        'list_bcodes',
                        'list_my_matches_from_ts',
                        'list_my_trades',
                        'list_my_trads_from_ts',
                        'list_payment_methods',
                        'list_payments',
                        'redeem_code',
                        'resign',
                        'signin',
                        'signout',
                        'trade_details',
                        'trade_options',
                        'withdraw',
                        'withdraw_by_id',
                    ],
                },
            },
        }
        params.update (config)
        super (bitlish, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetPairs ()
        result = []
        keys = list (products.keys ())
        for p in range (0, len (keys)):
            product = products[keys[p]]
            id = product['id']
            symbol = product['name']
            base, quote = symbol.split ('/')
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_ticker (self, product):
        p = self.product (product)
        tickers = self.publicGetTickers ()
        ticker = tickers[p['id']]
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['max']),
            'low': float (ticker['min']),
            'bid': None,
            'ask': None,
            'vwap': None,
            'open': None,
            'close': None,
            'first': float (ticker['first']),
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': None,
            'info': ticker,
        }

    def fetch_order_book (self, product):
        orderbook = self.publicGetTradesDepth ({
            'pair_id': self.product_id (product),
        })
        timestamp = int (int (orderbook['last']) / 1000)
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = { 'bids': 'bid', 'asks': 'ask' }
        keys = list (sides.keys ())
        for k in range (0, len (keys)):
            key = keys[k]
            side = sides[key]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = float (order['price'])
                amount = float (order['volume'])
                result[key].append ([ price, amount ])
        return result

    def fetch_trades (self, product):
        return self.publicGetTradesHistory ({
            'pair_id': self.product_id (product),
        })

    def fetch_balance (self):
        return self.privatePostBalance ()

    def sign_in (self):
        return self.privatePostSignin ({
            'login': self.login,
            'passwd': self.password,
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        order = {
            'pair_id': self.product_id (product),
            'dir': 'bid' if (side == 'buy') else 'ask',
            'amount': amount,
        }
        if type == 'limit':
            order['price'] = price
        return self.privatePostCreateTrade (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.version + '/' + path
        if type == 'public':
            if params:
                url += '?' + _urlencode.urlencode (params)
        else:
            body = json.dumps (self.extend ({ 'token': self.apiKey }, params))
            headers = { 'Content-Type': 'application/json' }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class bitmarket (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'bitmarket',
            'name': 'BitMarket',
            'countries': [ 'PL', 'EU', ],
            'rateLimit': 3000,
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27767256-a8555200-5ef9-11e7-96fd-469a65e2b0bd.jpg',
                'api': {
                    'public': 'https://www.bitmarket.net',
                    'private': 'https://www.bitmarket.pl/api2/', # last slash is critical
                },
                'www': [
                    'https://www.bitmarket.pl',
                    'https://www.bitmarket.net',
                ],
                'doc': [
                    'https://www.bitmarket.net/docs.php?file=api_public.html',
                    'https://www.bitmarket.net/docs.php?file=api_private.html',
                    'https://github.com/bitmarket-net/api',
                ],
            },
            'api': {
                'public': {
                    'get': [
                        'json/{market}/ticker',
                        'json/{market}/orderbook',
                        'json/{market}/trades',
                        'json/ctransfer',
                        'graphs/{market}/90m',
                        'graphs/{market}/6h',
                        'graphs/{market}/1d',
                        'graphs/{market}/7d',
                        'graphs/{market}/1m',
                        'graphs/{market}/3m',
                        'graphs/{market}/6m',
                        'graphs/{market}/1y',
                    ],
                },
                'private': {
                    'post': [
                        'info',
                        'trade',
                        'cancel',
                        'orders',
                        'trades',
                        'history',
                        'withdrawals',
                        'tradingdesk',
                        'tradingdeskStatus',
                        'tradingdeskConfirm',
                        'cryptotradingdesk',
                        'cryptotradingdeskStatus',
                        'cryptotradingdeskConfirm',
                        'withdraw',
                        'withdrawFiat',
                        'withdrawPLNPP',
                        'withdrawFiatFast',
                        'deposit',
                        'transfer',
                        'transfers',
                        'marginList',
                        'marginOpen',
                        'marginClose',
                        'marginCancel',
                        'marginModify',
                        'marginBalanceAdd',
                        'marginBalanceRemove',
                        'swapList',
                        'swapOpen',
                        'swapClose',
                    ],
                },
            },
            'products': {
                'BTC/PLN': { 'id': 'BTCPLN', 'symbol': 'BTC/PLN', 'base': 'BTC', 'quote': 'PLN' },
                'BTC/EUR': { 'id': 'BTCEUR', 'symbol': 'BTC/EUR', 'base': 'BTC', 'quote': 'EUR' },
                'LTC/PLN': { 'id': 'LTCPLN', 'symbol': 'LTC/PLN', 'base': 'LTC', 'quote': 'PLN' },
                'LTC/BTC': { 'id': 'LTCBTC', 'symbol': 'LTC/BTC', 'base': 'LTC', 'quote': 'BTC' },
                'LMX/BTC': { 'id': 'LiteMineXBTC', 'symbol': 'LMX/BTC', 'base': 'LMX', 'quote': 'BTC' },
            },
        }
        params.update (config)
        super (bitmarket, self).__init__ (params)

    def fetch_balance (self):
        return self.privatePostInfo ()

    def fetch_order_book (self, product):
        orderbook = self.publicGetJsonMarketOrderbook ({
            'market': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        result = {
            'bids': orderbook['bids'],
            'asks': orderbook['asks'],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        return result


    def fetch_ticker (self, product):
        ticker = self.publicGetJsonMarketTicker ({
            'market': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': float (ticker['vwap']),
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetJsonMarketTrades ({
            'market': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        return self.privatePostTrade (self.extend ({
            'market': self.product_id (product),
            'type': side,
            'amount': amount,
            'rate': price,
        }, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'][type]
        if type == 'public':
            url += '/' + self.implode_params (path + '.json', params)
        else:
            nonce = self.nonce ()
            query = self.extend ({
                'tonce': nonce,
                'method': path,
            }, params)
            body = _urlencode.urlencode (query)
            headers = {
                'API-Key': self.apiKey,
                'API-Hash': self.hmac (body, self.secret, hashlib.sha512),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class bitmex (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'bitmex',
            'name': 'BitMEX',
            'countries': 'SC', # Seychelles
            'version': 'v1',
            'rateLimit': 2000,
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766319-f653c6e6-5ed4-11e7-933d-f0bc3699ae8f.jpg',
                'api': 'https://www.bitmex.com',
                'www': 'https://www.bitmex.com',
                'doc': [
                    'https://www.bitmex.com/app/apiOverview',
                    'https://github.com/BitMEX/api-connectors/tree/master/official-http',
                ],
            },
            'api': {
                'public': {
                    'get': [
                        'announcement',
                        'announcement/urgent',
                        'funding',
                        'instrument',
                        'instrument/active',
                        'instrument/activeAndIndices',
                        'instrument/activeIntervals',
                        'instrument/compositeIndex',
                        'instrument/indices',
                        'insurance',
                        'leaderboard',
                        'liquidation',
                        'orderBook',
                        'orderBook/L2',
                        'quote',
                        'quote/bucketed',
                        'schema',
                        'schema/websocketHelp',
                        'settlement',
                        'stats',
                        'stats/history',
                        'trade',
                        'trade/bucketed',
                    ],
                },
                'private': {
                    'get': [
                        'apiKey',
                        'chat',
                        'chat/channels',
                        'chat/connected',
                        'execution',
                        'execution/tradeHistory',
                        'notification',
                        'order',
                        'position',
                        'user',
                        'user/affiliateStatus',
                        'user/checkReferralCode',
                        'user/commission',
                        'user/depositAddress',
                        'user/margin',
                        'user/minWithdrawalFee',
                        'user/wallet',
                        'user/walletHistory',
                        'user/walletSummary',
                    ],
                    'post': [
                        'apiKey',
                        'apiKey/disable',
                        'apiKey/enable',
                        'chat',
                        'order',
                        'order/bulk',
                        'order/cancelAllAfter',
                        'order/closePosition',
                        'position/isolate',
                        'position/leverage',
                        'position/riskLimit',
                        'position/transferMargin',
                        'user/cancelWithdrawal',
                        'user/confirmEmail',
                        'user/confirmEnableTFA',
                        'user/confirmWithdrawal',
                        'user/disableTFA',
                        'user/logout',
                        'user/logoutAll',
                        'user/preferences',
                        'user/requestEnableTFA',
                        'user/requestWithdrawal',
                    ],
                    'put': [
                        'order',
                        'order/bulk',
                        'user',
                    ],
                    'delete': [
                        'apiKey',
                        'order',
                        'order/all',
                    ],
                }
            },
        }
        params.update (config)
        super (bitmex, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetInstrumentActive ()
        result = []
        for p in range (0, len (products)):
            product = products[p]
            id = product['symbol']
            base = product['underlying']
            quote = product['quoteCurrency']
            isFuturesContract = id != (base + quote)
            base = self.commonCurrencyCode (base)
            quote = self.commonCurrencyCode (quote)
            symbol = id if isFuturesContract else (base + '/' + quote)
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.privateGetUserMargin ({ 'currency': 'all' })

    def fetch_order_book (self, product):
        orderbook = self.publicGetOrderBookL2 ({
            'symbol': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        for o in range (0, len (orderbook)):
            order = orderbook[o]
            side = 'asks' if (order['side'] == 'Sell') else 'bids'
            amount = order['size']
            price = order['price']
            result[side].append ([ price, amount ])
        result['bids'] = self.sort_by (result['bids'], 0, True)
        result['asks'] = self.sort_by (result['asks'], 0)
        return result

    def fetch_ticker (self, product):
        request = {
            'symbol': self.product_id (product),
            'binSize': '1d',
            'partial': True,
            'count': 1,
            'reverse': True,            
        }
        quotes = self.publicGetQuoteBucketed (request)
        quotesLength = len (quotes)
        quote = quotes[quotesLength - 1]
        tickers = self.publicGetTradeBucketed (request)
        ticker = tickers[0]
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (quote['bidPrice']),
            'ask': float (quote['askPrice']),
            'vwap': float (ticker['vwap']),
            'open': None,
            'close': float (ticker['close']),
            'first': None,
            'last': None,
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': float (ticker['homeNotional']),
            'quoteVolume': float (ticker['foreignNotional']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTrade ({
            'symbol': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        order = {
            'symbol': self.product_id (product),
            'side': self.capitalize (side),
            'orderQty': amount,
            'ordType': self.capitalize (type),
        }
        if type == 'limit':
            order['rate'] = price
        return self.privatePostOrder (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        query = '/api/' + self.version + '/' + path
        if params:
            query += '?' + _urlencode.urlencode (params)
        url = self.urls['api'] + query
        if type == 'private':
            nonce = str (self.nonce ())
            if method == 'POST':
                if params:
                    body = json.dumps (params)
            request = ''.join ([ method, query, nonce, body or ''])
            headers = {
                'Content-Type': 'application/json',
                'api-nonce': nonce,
                'api-key': self.apiKey,
                'api-signature': self.hmac (request, self.secret),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class bitso (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'bitso',
            'name': 'Bitso',
            'countries': 'MX', # Mexico
            'rateLimit': 2000, # 30 requests per minute
            'version': 'v3',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766335-715ce7aa-5ed5-11e7-88a8-173a27bb30fe.jpg',
                'api': 'https://api.bitso.com',
                'www': 'https://bitso.com',
                'doc': 'https://bitso.com/api_info',
            },
            'api': {
                'public': {
                    'get': [
                        'available_books',
                        'ticker',
                        'order_book',
                        'trades',
                    ],
                },
                'private': {
                    'get': [
                        'account_status',
                        'balance',
                        'fees',
                        'fundings',
                        'fundings/{fid}',
                        'funding_destination',
                        'kyc_documents',
                        'ledger',
                        'ledger/trades',
                        'ledger/fees',
                        'ledger/fundings',
                        'ledger/withdrawals',
                        'mx_bank_codes',
                        'open_orders',
                        'order_trades/{oid}',
                        'orders/{oid}',
                        'user_trades',
                        'user_trades/{tid}',
                        'withdrawals/',
                        'withdrawals/{wid}',
                    ],
                    'post': [
                        'bitcoin_withdrawal',
                        'debit_card_withdrawal',
                        'ether_withdrawal',
                        'orders',
                        'phone_number',
                        'phone_verification',
                        'phone_withdrawal',
                        'spei_withdrawal',
                    ],
                    'delete': [
                        'orders/{oid}',
                        'orders/all',
                    ],
                }
            },
        }
        params.update (config)
        super (bitso, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetAvailableBooks ()
        result = []
        for p in range (0, len (products['payload'])):
            product = products['payload'][p]
            id = product['book']
            symbol = id.upper ().replace ('_', '/')
            base, quote = symbol.split ('/')
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.privateGetBalance ()

    def fetch_order_book (self, product):
        response = self.publicGetOrderBook ({
            'book': self.product_id (product),
        })
        orderbook = response['payload']
        timestamp = self.parse8601 (orderbook['updated_at'])
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = [ 'bids', 'asks' ]
        for s in range (0, len (sides)):
            side = sides[s]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = float (order['price'])
                amount = float (order['amount'])
                result[side].append ([ price, amount ])
        return result

    def fetch_ticker (self, product):
        response = self.publicGetTicker ({
            'book': self.product_id (product),
        })
        ticker = response['payload']
        timestamp = self.parse8601 (ticker['created_at'])
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': float (ticker['vwap']),
            'open': None,
            'close': None,
            'first': None,
            'last': None,
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTrades ({
            'book': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        order = {
            'book': self.product_id (product),
            'side': side,
            'type': type,
            'major': amount,
        }
        if type == 'limit':
            order['price'] = price
        return self.privatePostOrders (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        query = '/' + self.version + '/' + self.implode_params (path, params)
        url = self.urls['api'] + query
        if type == 'public':
            if params:
                url += '?' + _urlencode.urlencode (params)
        else:
            if params:
                body = json.dumps (params)
            nonce = str (self.nonce ())
            request = ''.join ([ nonce, method, query, body or '' ])
            signature = self.hmac (request, self.secret)
            auth = self.apiKey + ':' + nonce + ':' + signature
            headers = { 'Authorization': "Bitso " + auth }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class bitstamp (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'bitstamp',
            'name': 'Bitstamp',
            'countries': 'GB',
            'rateLimit': 1000,
            'version': 'v2',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27786377-8c8ab57e-5fe9-11e7-8ea4-2b05b6bcceec.jpg',
                'api': 'https://www.bitstamp.net/api',
                'www': 'https://www.bitstamp.net',
                'doc': 'https://www.bitstamp.net/api',
            },
            'api': {
                'public': {
                    'get': [
                        'order_book/{id}/',
                        'ticker_hour/{id}/',
                        'ticker/{id}/',
                        'transactions/{id}/',
                    ],
                },
                'private': {
                    'post': [
                        'balance/',
                        'balance/{id}/',
                        'buy/{id}/',
                        'buy/market/{id}/',
                        'cancel_order/',
                        'liquidation_address/info/',
                        'liquidation_address/new/',
                        'open_orders/all/',
                        'open_orders/{id}/',
                        'sell/{id}/',
                        'sell/market/{id}/',
                        'transfer-from-main/',
                        'transfer-to-main/',
                        'user_transactions/',
                        'user_transactions/{id}/',
                        'withdrawal/cancel/',
                        'withdrawal/open/',
                        'withdrawal/status/',
                        'xrp_address/',
                        'xrp_withdrawal/',
                    ],
                },
            },
            'products': {
                'BTC/USD': { 'id': 'btcusd', 'symbol': 'BTC/USD', 'base': 'BTC', 'quote': 'USD' },
                'BTC/EUR': { 'id': 'btceur', 'symbol': 'BTC/EUR', 'base': 'BTC', 'quote': 'EUR' },
                'EUR/USD': { 'id': 'eurusd', 'symbol': 'EUR/USD', 'base': 'EUR', 'quote': 'USD' },
                'XRP/USD': { 'id': 'xrpusd', 'symbol': 'XRP/USD', 'base': 'XRP', 'quote': 'USD' },
                'XRP/EUR': { 'id': 'xrpeur', 'symbol': 'XRP/EUR', 'base': 'XRP', 'quote': 'EUR' },
                'XRP/BTC': { 'id': 'xrpbtc', 'symbol': 'XRP/BTC', 'base': 'XRP', 'quote': 'BTC' },
            },
        }
        params.update (config)
        super (bitstamp, self).__init__ (params)

    def fetch_order_book (self, product):
        orderbook = self.publicGetOrderBookId ({
            'id': self.product_id (product),
        })
        timestamp = int (orderbook['timestamp']) * 1000
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = [ 'bids', 'asks' ]
        for s in range (0, len (sides)):
            side = sides[s]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = float (order[0])
                amount = float (order[1])
                result[side].append ([ price, amount ])
        return result

    def fetch_ticker (self, product):
        ticker = self.publicGetTickerId ({
            'id': self.product_id (product),
        })
        timestamp = int (ticker['timestamp']) * 1000
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': float (ticker['vwap']),
            'open': float (ticker['open']),
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTransactionsId ({ 
            'id': self.product_id (product),
        })

    def fetch_balance (self):
        return self.privatePostBalance ()

    def create_order (self, product, type, side, amount, price = None, params = {}):
        method = 'privatePost' + self.capitalize (side)
        order = {
            'id': self.product_id (product),
            'amount': amount,
        }
        if type == 'market':
            method += 'Market'
        else:
            order['price'] = price
        method += 'Id'
        return getattr (self, method) (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.version + '/' + self.implode_params (path, params)
        query = self.omit (params, self.extract_params (path))
        if type == 'public':
            if query:
                url += '?' + _urlencode.urlencode (query)
        else:
            nonce = str (self.nonce ())
            auth = nonce + self.uid + self.apiKey
            signature = self.hmac (auth, self.secret)
            query = self.extend ({
                'key': self.apiKey,
                'signature': signature.upper (),
                'nonce': nonce,
            }, query)
            body = _urlencode.urlencode (query)
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': len (body),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class bittrex (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'bittrex',
            'name': 'Bittrex',
            'countries': 'US',
            'version': 'v1.1',
            'rateLimit': 2000,
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766352-cf0b3c26-5ed5-11e7-82b7-f3826b7a97d8.jpg',
                'api': 'https://bittrex.com/api',
                'www': 'https://bittrex.com',
                'doc': [ 
                    'https://bittrex.com/Home/Api',
                    'https://www.npmjs.org/package/node.bittrex.api',
                ],
            },
            'api': {
                'public': {
                    'get': [
                        'currencies',
                        'markethistory',
                        'markets',
                        'marketsummaries',
                        'marketsummary',
                        'orderbook',
                        'ticker',            
                    ],
                },
                'account': {
                    'get': [
                        'balance',
                        'balances',
                        'depositaddress',
                        'deposithistory',
                        'order',
                        'orderhistory',
                        'withdrawalhistory',
                        'withdraw',
                    ],
                },
                'market': {
                    'get': [
                        'buylimit',
                        'buymarket',
                        'cancel',
                        'openorders',
                        'selllimit',
                        'sellmarket',
                    ],
                },
            },
        }
        params.update (config)
        super (bittrex, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetMarkets ()
        result = []
        for p in range (0, len (products['result'])):
            product = products['result'][p]
            id = product['MarketName']
            base = product['MarketCurrency']
            quote = product['BaseCurrency']
            symbol = base + '/' + quote
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.accountGetBalances ()

    def fetch_order_book (self, product):
        response = self.publicGetOrderbook ({
            'market': self.product_id (product),
            'type': 'both',
            'depth': 50,
        })
        orderbook = response['result']
        timestamp = self.milliseconds ()
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = { 'bids': 'buy', 'asks': 'sell' }
        keys = list (sides.keys ())
        for k in range (0, len (keys)):
            key = keys[k]
            side = sides[key]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = float (order['Rate'])
                amount = float (order['Quantity'])
                result[key].append ([ price, amount ])
        return result

    def fetch_ticker (self, product):
        response = self.publicGetMarketsummary ({
            'market': self.product_id (product),
        })
        ticker = response['result'][0]
        timestamp = self.parse8601 (ticker['TimeStamp'])
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['High']),
            'low': float (ticker['Low']),
            'bid': float (ticker['Bid']),
            'ask': float (ticker['Ask']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['Last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['Volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetMarkethistory ({ 
            'market': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        method = 'marketGet' + self.capitalize (side) + type
        order = {
            'market': self.product_id (product),
            'quantity': amount,
        }
        if type == 'limit':
            order['rate'] = price
        return getattr (self, method) (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.version + '/'
        if type == 'public':
            url += type + '/' + method.lower () + path
            if params:
                url += '?' + _urlencode.urlencode (params)
        else:
            nonce = self.nonce ()
            url += type + '/'
            if ((type == 'account') and (path != 'withdraw')) or (path == 'openorders'):
                url += method.lower ()
            url += path + '?' + _urlencode.urlencode (self.extend ({
                'nonce': nonce,
                'apikey': self.apiKey,
            }, params))
            headers = { 'apisign': self.hmac (url, self.secret, hashlib.sha512) }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class blinktrade (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'blinktrade',
            'name': 'BlinkTrade',
            'countries': [ 'US', 'VE', 'VN', 'BR', 'PK', 'CL' ],
            'rateLimit': 1000, 
            'version': 'v1',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27990968-75d9c884-6470-11e7-9073-46756c8e7e8c.jpg',
                'api': {
                    'public': 'https://api.blinktrade.com/api',
                    'private': 'https://api.blinktrade.com/tapi',
                },
                'www': 'https://blinktrade.com',
                'doc': 'https://blinktrade.com/docs',
            },
            'api': {
                'public': {
                    'get': [
                        '{currency}/ticker',    # ?crypto_currency=BTC
                        '{currency}/orderbook', # ?crypto_currency=BTC
                        '{currency}/trades',    # ?crypto_currency=BTC&since=<TIMESTAMP>&limit=<NUMBER>
                    ],
                },
                'private': {
                    'post': [
                        'D',   # order
                        'F',   # cancel order
                        'U2',  # balance
                        'U4',  # my orders
                        'U6',  # withdraw
                        'U18', # deposit
                        'U24', # confirm withdrawal
                        'U26', # list withdrawals
                        'U30', # list deposits
                        'U34', # ledger
                        'U70', # cancel withdrawal
                    ],
                },
            },
            'products': {
                'BTC/VEF': { 'id': 'BTCVEF', 'symbol': 'BTC/VEF', 'base': 'BTC', 'quote': 'VEF', 'brokerId': 1, 'broker': 'SurBitcoin', },
                'BTC/VND': { 'id': 'BTCVND', 'symbol': 'BTC/VND', 'base': 'BTC', 'quote': 'VND', 'brokerId': 3, 'broker': 'VBTC', },
                'BTC/BRL': { 'id': 'BTCBRL', 'symbol': 'BTC/BRL', 'base': 'BTC', 'quote': 'BRL', 'brokerId': 4, 'broker': 'FoxBit', },
                'BTC/PKR': { 'id': 'BTCPKR', 'symbol': 'BTC/PKR', 'base': 'BTC', 'quote': 'PKR', 'brokerId': 8, 'broker': 'UrduBit', },
                'BTC/CLP': { 'id': 'BTCCLP', 'symbol': 'BTC/CLP', 'base': 'BTC', 'quote': 'CLP', 'brokerId': 9, 'broker': 'ChileBit', },
            },
        }
        params.update (config)
        super (blinktrade, self).__init__ (params)

    def fetch_balance (self):
        return self.privatePostU2 ({
            'BalanceReqID': self.nonce (),
        })

    def fetch_order_book (self, product):
        p = self.product (product)
        orderbook = self.publicGetCurrencyOrderbook ({
            'currency': p['quote'],
            'crypto_currency': p['base'],
        })
        timestamp = self.milliseconds ()
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = [ 'bids', 'asks' ]
        for s in range (0, len (sides)):
            side = sides[s]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = float (order[0])
                amount = float (order[1])
                result[side].append ([ price, amount ])
        return result

    def fetch_ticker (self, product):
        p = self.product (product)
        ticker = self.publicGetCurrencyTicker ({
            'currency': p['quote'],
            'crypto_currency': p['base'],
        })
        timestamp = self.milliseconds ()
        lowercaseQuote = p['quote'].lower ()
        quoteVolume = 'vol_' + lowercaseQuote
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['buy']),
            'ask': float (ticker['sell']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': float (ticker['vol']),
            'quoteVolume': float (ticker[quoteVolume]),
            'info': ticker,
        }

    def fetch_trades (self, product):
        p = self.product (product)
        return self.publicGetCurrencyTrades ({
            'currency': p['quote'],
            'crypto_currency': p['base'],
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        if type == 'market':
            raise Exception (self.id + ' allows limit orders only')
        p = self.product (product)
        order = {
            'ClOrdID': self.nonce (),
            'Symbol': p['id'],
            'Side': self.capitalize (side),
            'OrdType': 2,
            'Price': price,
            'OrderQty': amount,
            'BrokerID': p['brokerId'],
        }
        return self.privatePostD (self.extend (order, params))

    def cancel_order (self, id, params = {}):
        return self.privatePostF (self.extend ({
            'ClOrdID': id,
        }, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'][type] + '/' + self.version + '/' + self.implode_params (path, params)
        query = self.omit (params, self.extract_params (path))
        if type == 'public':
            if query:
                url += '?' + _urlencode.urlencode (query)
        else:
            nonce = str (self.nonce ())
            request = self.extend ({ 'MsgType': path }, query)
            body = json.dumps (request)
            headers = {
                'APIKey': self.apiKey,
                'Nonce': nonce,
                'Signature': self.hmac (nonce, self.secret),
                'Content-Type': 'application/json',
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class btcchina (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'btcchina',
            'name': 'BTCChina',
            'countries': 'CN',
            'rateLimit': 3000,
            'version': 'v1',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766368-465b3286-5ed6-11e7-9a11-0f6467e1d82b.jpg',
                'api': {
                    'public': 'https://data.btcchina.com/data',
                    'private': 'https://api.btcchina.com/api_trade_v1.php',
                },
                'www': 'https://www.btcchina.com',
                'doc': 'https://www.btcchina.com/apidocs'
            },
            'api': {
                'public': {
                    'get': [
                        'historydata',
                        'orderbook',
                        'ticker',
                        'trades',
                    ],
                },
                'private': {
                    'post': [
                        'BuyIcebergOrder',
                        'BuyOrder',
                        'BuyOrder2',
                        'BuyStopOrder',
                        'CancelIcebergOrder',
                        'CancelOrder',
                        'CancelStopOrder',
                        'GetAccountInfo',
                        'getArchivedOrder',
                        'getArchivedOrders',
                        'GetDeposits',
                        'GetIcebergOrder',
                        'GetIcebergOrders',
                        'GetMarketDepth',
                        'GetMarketDepth2',
                        'GetOrder',
                        'GetOrders',
                        'GetStopOrder',
                        'GetStopOrders',
                        'GetTransactions',
                        'GetWithdrawal',
                        'GetWithdrawals',
                        'RequestWithdrawal',
                        'SellIcebergOrder',
                        'SellOrder',
                        'SellOrder2',
                        'SellStopOrder',
                    ],
                },
            },
        }
        params.update (config)
        super (btcchina, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetTicker ({
            'market': 'all',
        })
        result = []
        keys = list (products.keys ())
        for p in range (0, len (keys)):
            key = keys[p]
            product = products[key]
            parts = key.split ('_')
            id = parts[1]
            base = id[0:3]
            quote = id[3:6]
            base = base.upper ()
            quote = quote.upper ()
            symbol = base + '/' + quote
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.privatePostGetAccountInfo ()

    def fetch_order_book (self, product):
        orderbook = self.publicGetOrderbook ({
            'market': self.product_id (product),
        })
        timestamp = orderbook['date'] * 1000
        result = {
            'bids': orderbook['bids'],
            'asks': orderbook['asks'],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        result['asks'] = self.sort_by (result['asks'], 0)
        return result

    def fetch_ticker (self, product):
        p = self.product (product)
        tickers = self.publicGetTicker ({
            'market': p['id'],
        })
        ticker = tickers['ticker']
        timestamp = ticker['date'] * 1000
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['buy']),
            'ask': float (ticker['sell']),
            'vwap': float (ticker['vwap']),
            'open': float (ticker['open']),
            'close': float (ticker['prev_close']),
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['vol']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTrades ({
            'market': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        p = self.product (product)
        method = 'privatePost' + self.capitalize (side) + 'Order2'
        order = {}
        id = p['id'].upper ()
        if type == 'market':
            order['params'] = [ None, amount, id ]
        else:
            order['params'] = [ price, amount, id ]
        return getattr (self, method) (self.extend (order, params))

    def nonce (self):
        return self.microseconds ()

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'][type] + '/' + path
        if type == 'public':
            if params:
                url += '?' + _urlencode.urlencode (params)
        else:
            p = []
            if 'params' in params:
                p = params['params']
            nonce = self.nonce ()
            request = {
                'method': path,
                'id': nonce,
                'params': p,
            }
            p = ','.join (p)
            body = json.dumps (request)
            query = (
                'tonce=' + nonce +
                '&accesskey=' + self.apiKey +
                '&requestmethod=' + method.lower () +
                '&id=' + nonce +
                '&method=' + path +
                '&params=' + p
            )
            signature = self.hmac (query, self.secret, hashlib.sha1)
            auth = self.apiKey + ':' + signature 
            headers = {
                'Content-Length': len (body),
                'Authorization': 'Basic ' + base64.b64encode (query),
                'Json-Rpc-Tonce': nonce,
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class btce (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'btce',
            'name': 'BTC-e',
            'countries': [ 'BG', 'RU' ], # Bulgaria, Russia
            'version': '3',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27843225-1b571514-611a-11e7-9208-2641a560b561.jpg',
                'api': {
                    'public': 'https://btc-e.com/api',
                    'private': 'https://btc-e.com/tapi',
                },
                'www': 'https://btc-e.com',
                'doc': [
                    'https://btc-e.com/api/3/docs',
                    'https://btc-e.com/tapi/docs',
                ],
            },
            'api': {
                'public': {
                    'get': [
                        'info',
                        'ticker/{pair}',
                        'depth/{pair}',
                        'trades/{pair}',
                    ],
                },
                'private': {
                    'post': [
                        'getInfo',
                        'Trade',
                        'ActiveOrders',
                        'OrderInfo',
                        'CancelOrder',
                        'TradeHistory',
                        'TransHistory',
                        'CoinDepositAddress',
                        'WithdrawCoin',
                        'CreateCoupon',
                        'RedeemCoupon',
                    ],
                }
            },
        }
        params.update (config)
        super (btce, self).__init__ (params)

    def fetch_products (self):
        response = self.publicGetInfo ()
        products = response['pairs']
        keys = list (products.keys ())
        result = []
        for p in range (0, len (keys)):
            id = keys[p]
            product = products[id]
            base, quote = id.split ('_')
            base = base.upper ()
            quote = quote.upper ()
            symbol = base + '/' + quote
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.privatePostGetInfo ()

    def fetch_order_book (self, product):
        p = self.product (product)
        response = self.publicGetDepthPair ({
            'pair': p['id'],
        })
        orderbook = response[p['id']] 
        timestamp = self.milliseconds ()
        result = {
            'bids': orderbook['bids'],
            'asks': orderbook['asks'],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        result['bids'] = self.sort_by (result['bids'], 0, True)
        result['asks'] = self.sort_by (result['asks'], 0)
        return result

    def fetch_ticker (self, product):
        p = self.product (product)
        tickers = self.publicGetTickerPair ({
            'pair': p['id'],
        })
        ticker = tickers[p['id']]
        timestamp = ticker['updated'] * 1000
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': ticker['high'] if ticker['high'] else None,
            'low': ticker['low'] if ticker['low'] else None,
            'bid': ticker['buy'] if ticker['buy'] else None,
            'ask': ticker['sell'] if ticker['sell'] else None,
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': ticker['last'] if ticker['last'] else None,
            'change': None,
            'percentage': None,
            'average': ticker['avg'] if ticker['avg'] else None,
            'baseVolume': ticker['vol_cur'] if ticker['vol_cur'] else None,
            'quoteVolume': ticker['vol'] if ticker['vol'] else None,
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTradesPair ({
            'pair': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        order = {
            'pair': self.product_id (product),
            'type': side,
            'amount': amount,
            'rate': price,
        }
        return self.privatePostTrade (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'][type] + '/' + self.version + '/' + self.implode_params (path, params)
        query = self.omit (params, self.extract_params (path))
        if type == 'public':
            if query:
                url += '?' + _urlencode.urlencode (query)
        else:
            nonce = self.nonce ()
            body = _urlencode.urlencode (self.extend ({
                'nonce': nonce,
            }, params))
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': len (body),
                'Key': self.apiKey,
                'Sign': self.hmac (body, self.secret, hashlib.sha512),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class btctrader (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'btctrader',
            'name': 'BTCTrader',
            'countries': [ 'TR', 'GR', 'PH' ], # Turkey, Greece, Philippines
            'rateLimit': 1000,
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27992404-cda1e386-649c-11e7-8dc1-40bbd2897768.jpg',
                'api': 'https://www.btctrader.com/api',
                'www': 'https://www.btctrader.com',
                'doc': 'https://github.com/BTCTrader/broker-api-docs',
            },
            'api': {
                'public': {
                    'get': [
                        'ohlcdata', # ?last=COUNT
                        'orderbook',
                        'ticker',                
                        'trades',   # ?last=COUNT (max 50)
                        
                    ],
                },
                'private': {
                    'get': [
                        'balance',
                        'openOrders',
                        'userTransactions', # ?offset=0&limit=25&sort=asc
                        
                    ],
                    'post': [
                        'buy',
                        'cancelOrder',                
                        'sell',
                    ],
                },
            },
        }
        params.update (config)
        super (btctrader, self).__init__ (params)

    def fetch_balance (self):
        return self.privateGetBalance ()

    def fetch_order_book (self, product):
        orderbook = self.publicGetOrderbook ()
        timestamp = int (orderbook['timestamp'] * 1000)
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = [ 'bids', 'asks' ]
        for s in range (0, len (sides)):
            side = sides[s]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = float (order[0])
                amount = float (order[1])
                result[side].append ([ price, amount ])
        return result

    def fetch_ticker (self, product):
        ticker = self.publicGetTicker ()
        timestamp = int (ticker['timestamp'] * 1000)
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': None,
            'open': float (ticker['open']),
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': float (ticker['average']),
            'baseVolume': None,
            'quoteVolume': float (ticker['volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        maxCount = 50
        return self.publicGetTrades ({
            # 'last': maxCount,
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        method = 'privatePost' + self.capitalize (side)
        order = {
            'Type': 'BuyBtc' if (side == 'buy') else 'SelBtc',
            'IsMarketOrder': 1 if (type == 'market') else 0,
        }
        if type == 'market':
            if side == 'buy':
                order['Total'] = amount
            else:
                order['Amount'] = amount
        else:
            order['Price'] = price
            order['Amount'] = amount
        return getattr (self, method) (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + path
        if type == 'public':
            if params:
                url += '?' + _urlencode.urlencode (params)
        else:
            nonce = self.nonce ().toString
            body = _urlencode.urlencode (params)
            secret = self.base64ToString (self.secret)
            auth = self.apiKey + nonce
            headers = {
                'X-PCK': self.apiKey,
                'X-Stamp': str (nonce),
                'X-Signature': self.hmac (auth, secret, hashlib.sha256, 'base64'),
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': len (body),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class btcexchange (btctrader):

    def __init__ (self, config = {}):
        params = {
            'id': 'btcexchange',
            'name': 'BTCExchange',
            'countries': 'PH', # Philippines
            'rateLimit': 1000,
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27993052-4c92911a-64aa-11e7-96d8-ec6ac3435757.jpg',
                'api': 'https://www.btcexchange.ph/api',
                'www': 'https://www.btcexchange.ph',
                'doc': 'https://github.com/BTCTrader/broker-api-docs',
            },
            'products': {
                'BTC/PHP': { 'id': 'BTC/PHP', 'symbol': 'BTC/PHP', 'base': 'BTC', 'quote': 'PHP' },
            },
        }
        params.update (config)
        super (btcexchange, self).__init__ (params)

#------------------------------------------------------------------------------

class btctradeua (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'btctradeua',
            'name': 'BTC Trade UA',
            'countries': 'UA', # Ukraine,
            'rateLimit': 2000,
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27941483-79fc7350-62d9-11e7-9f61-ac47f28fcd96.jpg',
                'api': 'https://btc-trade.com.ua/api',
                'www': 'https://btc-trade.com.ua',
                'doc': 'https://docs.google.com/document/d/1ocYA0yMy_RXd561sfG3qEPZ80kyll36HUxvCRe5GbhE/edit',
            },
            'api': {
                'public': {
                    'get': [
                        'deals/{symbol}',
                        'trades/sell/{symbol}',
                        'trades/buy/{symbol}',
                        'japan_stat/high/{symbol}',
                    ],
                },
                'private': {
                    'post': [
                        'auth',
                        'ask/{symbol}',
                        'balance',
                        'bid/{symbol}',
                        'buy/{symbol}',
                        'my_orders/{symbol}',
                        'order/status/{orderId}',            
                        'remove/order/{orderId}',
                        'sell/{symbol}',
                    ],
                },
            },
            'products': {
                'BTC/UAH': { 'id': 'btc_uah', 'symbol': 'BTC/UAH', 'base': 'BTC', 'quote': 'UAH' },
                'ETH/UAH': { 'id': 'eth_uah', 'symbol': 'ETH/UAH', 'base': 'ETH', 'quote': 'UAH' },
                'LTC/UAH': { 'id': 'ltc_uah', 'symbol': 'LTC/UAH', 'base': 'LTC', 'quote': 'UAH' },
                'DOGE/UAH': { 'id': 'doge_uah', 'symbol': 'DOGE/UAH', 'base': 'DOGE', 'quote': 'UAH' },
                'DASH/UAH': { 'id': 'dash_uah', 'symbol': 'DASH/UAH', 'base': 'DASH', 'quote': 'UAH' },
                'SIB/UAH': { 'id': 'sib_uah', 'symbol': 'SIB/UAH', 'base': 'SIB', 'quote': 'UAH' },
                'KRB/UAH': { 'id': 'krb_uah', 'symbol': 'KRB/UAH', 'base': 'KRB', 'quote': 'UAH' },
                'NVC/UAH': { 'id': 'nvc_uah', 'symbol': 'NVC/UAH', 'base': 'NVC', 'quote': 'UAH' },
                'LTC/BTC': { 'id': 'ltc_btc', 'symbol': 'LTC/BTC', 'base': 'LTC', 'quote': 'BTC' },
                'NVC/BTC': { 'id': 'nvc_btc', 'symbol': 'NVC/BTC', 'base': 'NVC', 'quote': 'BTC' },
                'ITI/UAH': { 'id': 'iti_uah', 'symbol': 'ITI/UAH', 'base': 'ITI', 'quote': 'UAH' },
                'DOGE/BTC': { 'id': 'doge_btc', 'symbol': 'DOGE/BTC', 'base': 'DOGE', 'quote': 'BTC' },
                'DASH/BTC': { 'id': 'dash_btc', 'symbol': 'DASH/BTC', 'base': 'DASH', 'quote': 'BTC' },
            },
        }
        params.update (config)
        super (btctradeua, self).__init__ (params)

    def sign_in (self):
        return self.privatePostAuth ()

    def fetch_balance (self):
        return self.privatePostBalance ()

    def fetch_order_book (self, product):
        p = self.product (product)
        bids = self.publicGetTradesBuySymbol ({
            'symbol': p['id'],
        })
        asks = self.publicGetTradesSellSymbol ({
            'symbol': p['id'],
        })
        orderbook = {
            'bids': [],
            'asks': [],
        }
        if bids:
            if 'list' in bids:
                orderbook['bids'] = bids['list']
        if asks:
            if 'list' in asks:
                orderbook['asks'] = asks['list']
        timestamp = self.milliseconds ()
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = [ 'bids', 'asks' ]
        for s in range (0, len (sides)):
            side = sides[s]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = float (order['price'])
                amount = float (order['currency_trade'])
                result[side].append ([ price, amount ])
        return result

    def fetch_ticker (self, product):
        response = self.publicGetJapanStatHighSymbol ({
            'symbol': self.product_id (product),
        })
        ticker = response['trades']
        timestamp = self.milliseconds ()
        result = {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': None,
            'low': None,
            'bid': None,
            'ask': None,
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': None,
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': None,
            'info': ticker,
        }
        tickerLength = len (ticker)
        if tickerLength > 0:
            start = max (tickerLength - 48, 0)
            for t in range (start, len (ticker)):
                candle = ticker[t]
                if result['open'] is None:
                    result['open'] = candle[1]
                if (result['high'] is None) or (result['high'] < candle[2]):
                    result['high'] = candle[2]
                if (result['low'] is None) or (result['low'] > candle[3]):
                    result['low'] = candle[3]
                if result['quoteVolume'] is None:
                    result['quoteVolume'] = -candle[5]
                else:
                    result['quoteVolume'] -= candle[5]
            last = tickerLength - 1
            result['close'] = ticker[last][4]
            result['quoteVolume'] = -1 * result['quoteVolume']
        return result

    def fetch_trades (self, product):
        return self.publicGetDealsSymbol ({
            'symbol': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        if type == 'market':
            raise Exception (self.id + ' allows limit orders only')
        p = self.product (product)
        method = 'privatePost' + self.capitalize (side) + 'Id'
        order = {
            'count': amount,
            'currency1': p['quote'],
            'currency': p['base'],
            'price': price,
        }
        return getattr (self, method) (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.implode_params (path, params)
        query = self.omit (params, self.extract_params (path))
        if type == 'public':
            if query:
                url += self.implode_params (path, query)
        else:
            nonce = self.nonce ()
            body = _urlencode.urlencode (self.extend ({
                'out_order_id': nonce,
                'nonce': nonce,
            }, query))
            headers = {
                'public-key': self.apiKey,
                'api-sign': self.hash (body + self.secret, hashlib.sha256),
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': len (body),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class btcturk (btctrader):

    def __init__ (self, config = {}):
        params = {
            'id': 'btcturk',
            'name': 'BTCTurk',
            'countries': 'TR', # Turkey
            'rateLimit': 1000,
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27992709-18e15646-64a3-11e7-9fa2-b0950ec7712f.jpg',
                'api': 'https://www.btcturk.com/api',
                'www': 'https://www.btcturk.com',
                'doc': 'https://github.com/BTCTrader/broker-api-docs',
            },
            'products': {
                'BTC/TRY': { 'id': 'BTC/TRY', 'symbol': 'BTC/TRY', 'base': 'BTC', 'quote': 'TRY' },
            },
        }
        params.update (config)
        super (btcturk, self).__init__ (params)

#------------------------------------------------------------------------------

class btcx (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'btcx',
            'name': 'BTCX',
            'countries': [ 'IS', 'US', 'EU', ],
            'rateLimit': 3000, # support in english is very poor, unable to tell rate limits
            'version': 'v1',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766385-9fdcc98c-5ed6-11e7-8f14-66d5e5cd47e6.jpg',
                'api': 'https://btc-x.is/api',
                'www': 'https://btc-x.is',
                'doc': 'https://btc-x.is/custom/api-document.html',
            },
            'api': {
                'public': {
                    'get': [
                        'depth/{id}/{limit}',
                        'ticker/{id}',         
                        'trade/{id}/{limit}',
                    ],
                },
                'private': {
                    'post': [
                        'balance',
                        'cancel',
                        'history',
                        'order',
                        'redeem',
                        'trade',
                        'withdraw',
                    ],
                },
            },
            'products': {
                'BTC/USD': { 'id': 'btc/usd', 'symbol': 'BTC/USD', 'base': 'BTC', 'quote': 'USD' },
                'BTC/EUR': { 'id': 'btc/eur', 'symbol': 'BTC/EUR', 'base': 'BTC', 'quote': 'EUR' },
            },
        }
        params.update (config)
        super (btcx, self).__init__ (params)

    def fetch_balance (self):
        return self.privatePostBalance ()

    def fetch_order_book (self, product):
        orderbook = self.publicGetDepthIdLimit ({ 
            'id': self.product_id (product),
            'limit': 1000,
        })
        timestamp = self.milliseconds ()
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = [ 'bids', 'asks' ]
        for s in range (0, len (sides)):
            side = sides[s]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = order['price']
                amount = order['amount']
                result[side].append ([ price, amount ])
        return result

    def fetch_ticker (self, product):
        ticker = self.publicGetTickerId ({
            'id': self.product_id (product),
        })
        timestamp = ticker['time'] * 1000
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['buy']),
            'ask': float (ticker['sell']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTradeIdLimit ({
            'id': self.product_id (product),
            'limit': 100,
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        return self.privatePostTrade (self.extend ({
            'type': side.upper (),
            'market': self.product_id (product),
            'amount': amount,
            'price': price,
        }, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.version + '/'
        if type == 'public':
            url += self.implode_params (path, params)
        else:
            nonce = self.nonce ()
            url += type
            body = _urlencode.urlencode (self.extend ({
                'Method': path.upper (),
                'Nonce': nonce,
            }, params))
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Key': self.apiKey,
                'Signature': self.hmac (body, self.secret, hashlib.sha512),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class bter (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'bter',
            'name': 'Bter',
            'countries': [ 'VG', 'CN' ], # British Virgin Islands, China
            'version': '2',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27980479-cfa3188c-6387-11e7-8191-93fc4184ba5c.jpg',
                'api': {
                    'public': 'https://data.bter.com/api',
                    'private': 'https://api.bter.com/api',
                },
                'www': 'https://bter.com',
                'doc': 'https://bter.com/api2',
            },
            'api': {
                'public': {
                    'get': [
                        'pairs',
                        'marketinfo',
                        'marketlist',
                        'tickers',
                        'ticker/{id}',
                        'orderBook/{id}',
                        'trade/{id}',
                        'tradeHistory/{id}/{tid}',
                    ],
                },
                'private': {
                    'post': [
                        'balances',
                        'depositAddress',
                        'newAddress',
                        'depositsWithdrawals',
                        'buy',
                        'sell',
                        'cancelOrder',
                        'cancelAllOrders',
                        'getOrder',
                        'openOrders',
                        'tradeHistory',
                        'withdraw',
                    ],
                },
            },
        }
        params.update (config)
        super (bter, self).__init__ (params)

    def fetch_products (self):
        response = self.publicGetMarketlist ()
        products = response['data']
        result = []
        for p in range (0, len (products)):
            product = products[p]
            id = product['pair']
            base = product['curr_a']
            quote = product['curr_b']
            symbol = base + '/' + quote
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.privatePostBalances ()

    def fetch_order_book (self, product):
        orderbook = self.publicGetOrderBookId ({
            'id': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = [ 'bids', 'asks' ]
        for s in range (0, len (sides)):
            side = sides[s]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = order[0]
                amount = order[1]
                result[side].append ([ price, amount ])
        result['asks'] = self.sort_by (result['asks'], 0)
        return result

    def fetch_ticker (self, product):
        ticker = self.publicGetTickerId ({
            'id': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high24hr']),
            'low': float (ticker['low24hr']),
            'bid': float (ticker['highestBid']),
            'ask': float (ticker['lowestAsk']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': float (ticker['percentChange']),
            'percentage': None,
            'average': None,
            'baseVolume': float (ticker['baseVolume']),
            'quoteVolume': float (ticker['quoteVolume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTradeId ({
            'id': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        method = 'privatePost' + self.capitalize (side)
        order = {
            'currencyPair': self.symbol (product),
            'rate': price,
            'amount': amount,
        }
        return getattr (self, method) (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        prefix = (type + '/') if (type == 'private') else ''
        url = self.urls['api'][type] + self.version + '/1/' + prefix + self.implode_params (path, params)
        query = self.omit (params, self.extract_params (path))
        if type == 'public':
            if query:
                url += '?' + _urlencode.urlencode (query)
        else:
            nonce = self.nonce ()
            request = { 'nonce': nonce }
            body = _urlencode.urlencode (self.extend (request, query))
            headers = {
                'Key': self.apiKey,
                'Sign': self.hmac (body, self.secret, hashlib.sha512),
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': len (body),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class bxinth (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'bxinth',
            'name': 'BX.in.th',
            'countries': 'TH', # Thailand
            'rateLimit': 2000,
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766412-567b1eb4-5ed7-11e7-94a8-ff6a3884f6c5.jpg',
                'api': 'https://bx.in.th/api',
                'www': 'https://bx.in.th',
                'doc': 'https://bx.in.th/info/api',
            },
            'api': {
                'public': {
                    'get': [
                        '', # ticker
                        'options',
                        'optionbook',
                        'orderbook',
                        'pairing',
                        'trade',
                        'tradehistory',
                    ],
                },
                'private': {
                    'post': [
                        'balance',
                        'biller',
                        'billgroup',
                        'billpay',
                        'cancel',
                        'deposit',
                        'getorders',
                        'history',
                        'option-issue',
                        'option-bid',
                        'option-sell',
                        'option-myissue',
                        'option-mybid',
                        'option-myoptions',
                        'option-exercise',
                        'option-cancel',
                        'option-history',
                        'order',
                        'withdrawal',
                        'withdrawal-history',
                    ],
                },
            },
        }
        params.update (config)
        super (bxinth, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetPairing ()
        keys = list (products.keys ())
        result = []
        for p in range (0, len (keys)):
            product = products[keys[p]]
            id = product['pairing_id']
            base = product['primary_currency']
            quote = product['secondary_currency']
            symbol = base + '/' + quote
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.privatePostBalance ()

    def fetch_order_book (self, product):
        orderbook = self.publicGetOrderbook ({
            'pairing': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = [ 'bids', 'asks' ]
        for s in range (0, len (sides)):
            side = sides[s]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = float (order[0])
                amount = float (order[1])
                result[side].append ([ price, amount ])
        return result

    def fetch_ticker (self, product):
        p = self.product (product)
        tickers = self.publicGet ({ 'pairing': p['id'] })
        ticker = tickers[p['id']]
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': None,
            'low': None,
            'bid': float (ticker['orderbook']['bids']['highbid']),
            'ask': float (ticker['orderbook']['asks']['highbid']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last_price']),
            'change': float (ticker['change']),
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['volume_24hours']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTrade ({
            'pairing': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        return self.privatePostOrder (self.extend ({
            'pairing': self.product_id (product),
            'type': side,
            'amount': amount,
            'rate': price,
        }, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + path + '/'
        if params:
            url += '?' + _urlencode.urlencode (params)
        if type == 'private':
            nonce = self.nonce ()
            signature = self.hash (self.apiKey + nonce + self.secret, hashlib.sha256)
            body = _urlencode.urlencode (self.extend ({
                'key': self.apiKey,
                'nonce': nonce,
                'signature': signature,
                # twofa: self.twofa,
            }, params))
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': len (body),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class ccex (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'ccex',
            'name': 'C-CEX',
            'countries': [ 'DE', 'EU', ],
            'rateLimit': 2000,
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766433-16881f90-5ed8-11e7-92f8-3d92cc747a6c.jpg',
                'api': {
                    'tickers': 'https://c-cex.com/t',
                    'public': 'https://c-cex.com/t/api_pub.html',
                    'private': 'https://c-cex.com/t/api.html',
                },
                'www': 'https://c-cex.com',
                'doc': 'https://c-cex.com/?id=api',
            },
            'api': {
                'tickers': {
                    'get': [
                        'coinnames',
                        '{market}',
                        'pairs',
                        'prices',
                        'volume_{coin}',
                    ],
                },
                'public': {
                    'get': [                
                        'balancedistribution',
                        'markethistory',
                        'markets',
                        'marketsummaries',
                        'orderbook',
                    ],
                },
                'private': {            
                    'get': [
                        'buylimit',
                        'cancel',
                        'getbalance',
                        'getbalances',                
                        'getopenorders',
                        'getorder',
                        'getorderhistory',
                        'mytrades',
                        'selllimit',
                    ],
                },
            },
        }
        params.update (config)
        super (ccex, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetMarkets ()
        result = []
        for p in range (0, len (products['result'])):
            product = products['result'][p]
            id = product['MarketName']
            base = product['MarketCurrency']
            quote = product['BaseCurrency']
            symbol = base + '/' + quote
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.privateGetBalances ()

    def fetch_order_book (self, product):
        response = self.publicGetOrderbook ({
            'market': self.product_id (product),
            'type': 'both',
            'depth': 100,
        })
        orderbook = response['result']
        timestamp = self.milliseconds ()
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = { 'bids': 'buy', 'asks': 'sell' }
        keys = list (sides.keys ())
        for k in range (0, len (keys)):
            key = keys[k]
            side = sides[key]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = float (order['Rate'])
                amount = float (order['Quantity'])
                result[key].append ([ price, amount ])
        return result

    def fetch_ticker (self, product):
        response = self.tickersGetMarket ({
            'market': self.product_id (product).lower (),
        })
        ticker = response['ticker']
        timestamp = ticker['updated'] * 1000
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['buy']),
            'ask': float (ticker['sell']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['lastprice']),
            'change': None,
            'percentage': None,
            'average': float (ticker['avg']),
            'baseVolume': None,
            'quoteVolume': float (ticker['buysupport']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetMarkethistory ({
            'market': self.product_id (product),
            'type': 'both',
            'depth': 100,
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        method = 'privateGet' + self.capitalize (side) + type
        return getattr (self, method) (self.extend ({
            'market': self.product_id (product),
            'quantity': amount,
            'rate': price,
        }, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'][type]
        if type == 'private':
            nonce = str (self.nonce ())
            query = self.keysort (self.extend ({
                'a': path,
                'apikey': self.apiKey,
                'nonce': nonce,
            }, params))
            url += '?' + _urlencode.urlencode (query)
            headers = { 'apisign': self.hmac (url, self.secret, hashlib.sha512) }
        elif type == 'public':
            url += '?' + _urlencode.urlencode (self.extend ({
                'a': 'get' + path,
            }, params))
        else:
            url += '/' + self.implode_params (path, params) + '.json'
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class cex (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'cex',
            'name': 'CEX.IO',
            'countries': [ 'GB', 'EU', 'CY', 'RU', ],
            'rateLimit': 2000,
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766442-8ddc33b0-5ed8-11e7-8b98-f786aef0f3c9.jpg',
                'api': 'https://cex.io/api',
                'www': 'https://cex.io',
                'doc': 'https://cex.io/cex-api',
            },
            'api': {
                'public': {
                    'get': [
                        'currency_limits',
                        'last_price/{pair}',
                        'last_prices/{currencies}',
                        'ohlcv/hd/{yyyymmdd}/{pair}',
                        'order_book/{pair}',
                        'ticker/{pair}',
                        'tickers/{currencies}',
                        'trade_history/{pair}',
                    ],
                    'post': [
                        'convert/{pair}',
                        'price_stats/{pair}',
                    ],
                },
                'private': {
                    'post': [
                        'active_orders_status/',
                        'archived_orders/{pair}',
                        'balance/',
                        'cancel_order/',
                        'cancel_orders/{pair}',
                        'cancel_replace_order/{pair}',
                        'close_position/{pair}',
                        'get_address/',
                        'get_myfee/',
                        'get_order/',
                        'get_order_tx/',
                        'open_orders/{pair}',
                        'open_orders/',
                        'open_position/{pair}',
                        'open_positions/{pair}',
                        'place_order/{pair}',
                        'place_order/{pair}',
                    ],
                }
            },
        }
        params.update (config)
        super (cex, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetCurrencyLimits ()
        result = []
        for p in range (0, len (products['data']['pairs'])):
            product = products['data']['pairs'][p]
            id = product['symbol1'] + '/' + product['symbol2']
            symbol = id
            base, quote = symbol.split ('/')
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.privatePostBalance ()

    def fetch_order_book (self, product):
        orderbook =  self.publicGetOrderBookPair ({
            'pair': self.product_id (product),
        })
        timestamp = orderbook['timestamp'] * 1000
        result = {
            'bids': orderbook['bids'],
            'asks': orderbook['asks'],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        return result

    def fetch_ticker (self, product):
        ticker = self.publicGetTickerPair ({
            'pair': self.product_id (product),
        })
        timestamp = int (ticker['timestamp']) * 1000
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': float (ticker['change']),
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTradeHistoryPair ({
            'pair': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        order = {
            'pair': self.product_id (product),
            'type': side,
            'amount': amount,            
        }
        if type == 'limit':
            order['price'] = price
        else:
            order['order_type'] = type
        return self.privatePostPlaceOrderPair (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.implode_params (path, params)
        query = self.omit (params, self.extract_params (path))
        if type == 'public':   
            if query:
                url += '?' + _urlencode.urlencode (query)
        else:
            nonce = str (self.nonce ())
            body = _urlencode.urlencode (self.extend ({
                'key': self.apiKey,
                'signature': self.hmac (nonce + self.uid + self.apiKey, self.secret).upper (),
                'nonce': nonce,
            }, query))
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': len (body),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class chilebit (blinktrade):

    def __init__ (self, config = {}):
        params = {
            'id': 'chilebit',
            'name': 'ChileBit',
            'countries': 'CL',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27991414-1298f0d8-647f-11e7-9c40-d56409266336.jpg',
                'api': {
                    'public': 'https://api.blinktrade.com/api',
                    'private': 'https://api.blinktrade.com/tapi',
                },
                'www': 'https://chilebit.net',
                'doc': 'https://blinktrade.com/docs',
            },
            'comment': 'Blinktrade API',
            'products': {
                'BTC/CLP': { 'id': 'BTCCLP', 'symbol': 'BTC/CLP', 'base': 'BTC', 'quote': 'CLP', 'brokerId': 9, 'broker': 'ChileBit', },
            },
        }
        params.update (config)
        super (chilebit, self).__init__ (params)

#------------------------------------------------------------------------------

class coincheck (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'coincheck',
            'name': 'coincheck',
            'countries': [ 'JP', 'ID', ],
            'rateLimit': 2000,
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766464-3b5c3c74-5ed9-11e7-840e-31b32968e1da.jpg',
                'api': 'https://coincheck.com/api',
                'www': 'https://coincheck.com',
                'doc': 'https://coincheck.com/documents/exchange/api',
            },
            'api': {
                'public': {
                    'get': [
                        'exchange/orders/rate',
                        'order_books',
                        'rate/{pair}',
                        'ticker',
                        'trades',
                    ],
                },
                'private': {
                    'get': [
                        'accounts',
                        'accounts/balance',
                        'accounts/leverage_balance',
                        'bank_accounts',
                        'deposit_money',
                        'exchange/orders/opens',
                        'exchange/orders/transactions',
                        'exchange/orders/transactions_pagination',
                        'exchange/leverage/positions',
                        'lending/borrows/matches',
                        'send_money',
                        'withdraws',
                    ],            
                    'post': [
                        'bank_accounts',
                        'deposit_money/{id}/fast',
                        'exchange/orders',
                        'exchange/transfers/to_leverage',
                        'exchange/transfers/from_leverage',
                        'lending/borrows',
                        'lending/borrows/{id}/repay',
                        'send_money',
                        'withdraws',
                    ],
                    'delete': [
                        'bank_accounts/{id}',
                        'exchange/orders/{id}',
                        'withdraws/{id}',
                    ],
                },
            },
            'products': {
                'BTC/JPY':  { 'id': 'btc_jpy',  'symbol': 'BTC/JPY',  'base': 'BTC',  'quote': 'JPY' }, # the only real pair
                'ETH/JPY':  { 'id': 'eth_jpy',  'symbol': 'ETH/JPY',  'base': 'ETH',  'quote': 'JPY' },
                'ETC/JPY':  { 'id': 'etc_jpy',  'symbol': 'ETC/JPY',  'base': 'ETC',  'quote': 'JPY' },
                'DAO/JPY':  { 'id': 'dao_jpy',  'symbol': 'DAO/JPY',  'base': 'DAO',  'quote': 'JPY' },
                'LSK/JPY':  { 'id': 'lsk_jpy',  'symbol': 'LSK/JPY',  'base': 'LSK',  'quote': 'JPY' },
                'FCT/JPY':  { 'id': 'fct_jpy',  'symbol': 'FCT/JPY',  'base': 'FCT',  'quote': 'JPY' },
                'XMR/JPY':  { 'id': 'xmr_jpy',  'symbol': 'XMR/JPY',  'base': 'XMR',  'quote': 'JPY' },
                'REP/JPY':  { 'id': 'rep_jpy',  'symbol': 'REP/JPY',  'base': 'REP',  'quote': 'JPY' },
                'XRP/JPY':  { 'id': 'xrp_jpy',  'symbol': 'XRP/JPY',  'base': 'XRP',  'quote': 'JPY' },
                'ZEC/JPY':  { 'id': 'zec_jpy',  'symbol': 'ZEC/JPY',  'base': 'ZEC',  'quote': 'JPY' },
                'XEM/JPY':  { 'id': 'xem_jpy',  'symbol': 'XEM/JPY',  'base': 'XEM',  'quote': 'JPY' },
                'LTC/JPY':  { 'id': 'ltc_jpy',  'symbol': 'LTC/JPY',  'base': 'LTC',  'quote': 'JPY' },
                'DASH/JPY': { 'id': 'dash_jpy', 'symbol': 'DASH/JPY', 'base': 'DASH', 'quote': 'JPY' },
                'ETH/BTC':  { 'id': 'eth_btc',  'symbol': 'ETH/BTC',  'base': 'ETH',  'quote': 'BTC' },
                'ETC/BTC':  { 'id': 'etc_btc',  'symbol': 'ETC/BTC',  'base': 'ETC',  'quote': 'BTC' },
                'LSK/BTC':  { 'id': 'lsk_btc',  'symbol': 'LSK/BTC',  'base': 'LSK',  'quote': 'BTC' },
                'FCT/BTC':  { 'id': 'fct_btc',  'symbol': 'FCT/BTC',  'base': 'FCT',  'quote': 'BTC' },
                'XMR/BTC':  { 'id': 'xmr_btc',  'symbol': 'XMR/BTC',  'base': 'XMR',  'quote': 'BTC' },
                'REP/BTC':  { 'id': 'rep_btc',  'symbol': 'REP/BTC',  'base': 'REP',  'quote': 'BTC' },
                'XRP/BTC':  { 'id': 'xrp_btc',  'symbol': 'XRP/BTC',  'base': 'XRP',  'quote': 'BTC' },
                'ZEC/BTC':  { 'id': 'zec_btc',  'symbol': 'ZEC/BTC',  'base': 'ZEC',  'quote': 'BTC' },
                'XEM/BTC':  { 'id': 'xem_btc',  'symbol': 'XEM/BTC',  'base': 'XEM',  'quote': 'BTC' },
                'LTC/BTC':  { 'id': 'ltc_btc',  'symbol': 'LTC/BTC',  'base': 'LTC',  'quote': 'BTC' },
                'DASH/BTC': { 'id': 'dash_btc', 'symbol': 'DASH/BTC', 'base': 'DASH', 'quote': 'BTC' },
            },
        }
        params.update (config)
        super (coincheck, self).__init__ (params)

    def fetch_balance (self):
        return self.privateGetAccountsBalance ()

    def fetch_order_book (self, product):
        orderbook =  self.publicGetOrderBooks ()
        timestamp = self.milliseconds ()
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = [ 'bids', 'asks' ]
        for s in range (0, len (sides)):
            side = sides[s]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = float (order[0])
                amount = float (order[1])
                result[side].append ([ price, amount ])
        return result

    def fetch_ticker (self, product):
        ticker = self.publicGetTicker ()
        timestamp = ticker['timestamp'] * 1000
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTrades ()

    def create_order (self, product, type, side, amount, price = None, params = {}):
        prefix = ''
        order = {
            'pair': self.product_id (product),
        }
        if type == 'market':
            order_type = type + '_' + side
            order['order_type'] = order_type
            prefix = (order_type + '_') if (side == buy) else ''
            order[prefix + 'amount'] = amount
        else:
            order['order_type'] = side
            order['rate'] = price
            order['amount'] = amount
        return self.privatePostExchangeOrders (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.implode_params (path, params)
        query = self.omit (params, self.extract_params (path))
        if type == 'public':
            if query:
                url += '?' + _urlencode.urlencode (query)
        else:
            nonce = str (self.nonce ())
            if query:
                body = _urlencode.urlencode (self.keysort (query))
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': len (body),
                'ACCESS-KEY': self.apiKey,
                'ACCESS-NONCE': nonce,
                'ACCESS-SIGNATURE': self.hmac (nonce + url + (body or ''), self.secret)
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class coinmate (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'coinmate',
            'name': 'CoinMate',
            'countries': [ 'GB', 'CZ' ], # UK, Czech Republic
            'rateLimit': 1000,
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27811229-c1efb510-606c-11e7-9a36-84ba2ce412d8.jpg',
                'api': 'https://coinmate.io/api',
                'www': 'https://coinmate.io',
                'doc': [
                    'https://coinmate.io/developers',
                    'http://docs.coinmate.apiary.io/#reference',
                ],
            },
            'api': {
                'public': {
                    'get': [
                        'orderBook',
                        'ticker',
                        'transactions',
                    ],
                },
                'private': {
                    'post': [
                        'balances',
                        'bitcoinWithdrawal',
                        'bitcoinDepositAddresses',
                        'buyInstant',
                        'buyLimit',
                        'cancelOrder',
                        'cancelOrderWithInfo',
                        'createVoucher',
                        'openOrders',
                        'redeemVoucher',
                        'sellInstant',
                        'sellLimit',
                        'transactionHistory',
                        'unconfirmedBitcoinDeposits',
                    ],
                },
            },
            'products': {
                'BTC/EUR': { 'id': 'BTC_EUR', 'symbol': 'BTC/EUR', 'base': 'BTC', 'quote': 'EUR'  },
                'BTC/CZK': { 'id': 'BTC_CZK', 'symbol': 'BTC/CZK', 'base': 'BTC', 'quote': 'CZK'  },
            },
        }
        params.update (config)
        super (coinmate, self).__init__ (params)

    def fetch_balance (self):
        return self.privatePostBalances ()

    def fetch_order_book (self, product):
        response = self.publicGetOrderBook ({
            'currencyPair': self.product_id (product),
            'groupByPriceLimit': 'False',
        })
        orderbook = response['data']
        timestamp = orderbook['timestamp'] * 1000
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = [ 'bids', 'asks' ]
        for s in range (0, len (sides)):
            side = sides[s]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = order['price']
                amount = order['amount']
                result[side].append ([ price, amount ])
        return result

    def fetch_ticker (self, product):
        response = self.publicGetTicker ({
            'currencyPair': self.product_id (product),
        })
        ticker = response['data']
        timestamp = ticker['timestamp'] * 1000
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['amount']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTransactions ({
            'currencyPair': self.product_id (product),
            'minutesIntoHistory': 10,
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        method = 'privatePost' + self.capitalize (side)
        order = {
            'currencyPair': self.product_id (product),
        }
        if type == 'market':
            if side == 'buy':
                order['total'] = amount # amount in fiat
            else:
                order['amount'] = amount # amount in fiat
            method += 'Instant'
        else:
            order['amount'] = amount # amount in crypto
            order['price'] = price
            method += self.capitalize (type)
        return getattr (self, method) (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + path
        if type == 'public':
            if params:
                url += '?' + _urlencode.urlencode (params)
        else:
            nonce = str (self.nonce ())
            auth = ' '.join ([ nonce, self.uid, self.apiKey ])
            signature = self.hmac (auth, self.secret)
            body = _urlencode.urlencode (self.extend ({
                'clientId': self.uid,
                'nonce': nonce,
                'publicKey': self.apiKey,
                'signature': signature.upper (),
            }, params))
            headers = {
                'Content-Type':  'application/x-www-form-urlencoded',
                'Content-Length': len (body),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class coinsecure (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'coinsecure',
            'name': 'Coinsecure',
            'countries': 'IN', # India
            'rateLimit': 1000,
            'version': 'v1',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766472-9cbd200a-5ed9-11e7-9551-2267ad7bac08.jpg',
                'api': 'https://api.coinsecure.in',
                'www': 'https://coinsecure.in',
                'doc': [
                    'https://api.coinsecure.in',
                    'https://github.com/coinsecure/plugins',
                ],
            },
            'api': {
                'public': {
                    'get': [
                        'bitcoin/search/confirmation/{txid}',
                        'exchange/ask/low',
                        'exchange/ask/orders',
                        'exchange/bid/high',
                        'exchange/bid/orders',
                        'exchange/lastTrade',
                        'exchange/max24Hr',
                        'exchange/min24Hr',
                        'exchange/ticker',
                        'exchange/trades',
                    ],
                },
                'private': {
                    'get': [
                        'mfa/authy/call',
                        'mfa/authy/sms',            
                        'netki/search/{netkiName}',
                        'user/bank/otp/{number}',
                        'user/kyc/otp/{number}',
                        'user/profile/phone/otp/{number}',
                        'user/wallet/coin/address/{id}',
                        'user/wallet/coin/deposit/confirmed/all',
                        'user/wallet/coin/deposit/confirmed/{id}',
                        'user/wallet/coin/deposit/unconfirmed/all',
                        'user/wallet/coin/deposit/unconfirmed/{id}',
                        'user/wallet/coin/wallets',
                        'user/exchange/bank/fiat/accounts',
                        'user/exchange/bank/fiat/balance/available',
                        'user/exchange/bank/fiat/balance/pending',
                        'user/exchange/bank/fiat/balance/total',
                        'user/exchange/bank/fiat/deposit/cancelled',
                        'user/exchange/bank/fiat/deposit/unverified',
                        'user/exchange/bank/fiat/deposit/verified',
                        'user/exchange/bank/fiat/withdraw/cancelled',
                        'user/exchange/bank/fiat/withdraw/completed',
                        'user/exchange/bank/fiat/withdraw/unverified',
                        'user/exchange/bank/fiat/withdraw/verified',
                        'user/exchange/ask/cancelled',
                        'user/exchange/ask/completed',
                        'user/exchange/ask/pending',
                        'user/exchange/bid/cancelled',
                        'user/exchange/bid/completed',
                        'user/exchange/bid/pending',
                        'user/exchange/bank/coin/addresses',
                        'user/exchange/bank/coin/balance/available',
                        'user/exchange/bank/coin/balance/pending',
                        'user/exchange/bank/coin/balance/total',
                        'user/exchange/bank/coin/deposit/cancelled',
                        'user/exchange/bank/coin/deposit/unverified',
                        'user/exchange/bank/coin/deposit/verified',
                        'user/exchange/bank/coin/withdraw/cancelled',
                        'user/exchange/bank/coin/withdraw/completed',
                        'user/exchange/bank/coin/withdraw/unverified',
                        'user/exchange/bank/coin/withdraw/verified',
                        'user/exchange/bank/summary',
                        'user/exchange/coin/fee',
                        'user/exchange/fiat/fee',
                        'user/exchange/kycs',
                        'user/exchange/referral/coin/paid',
                        'user/exchange/referral/coin/successful',
                        'user/exchange/referral/fiat/paid',
                        'user/exchange/referrals',
                        'user/exchange/trade/summary',
                        'user/login/token/{token}',
                        'user/summary',
                        'user/wallet/summary',
                        'wallet/coin/withdraw/cancelled',
                        'wallet/coin/withdraw/completed',
                        'wallet/coin/withdraw/unverified',
                        'wallet/coin/withdraw/verified',
                    ],
                    'post': [
                        'login',
                        'login/initiate',
                        'login/password/forgot',
                        'mfa/authy/initiate',
                        'mfa/ga/initiate',
                        'signup',
                        'user/netki/update',
                        'user/profile/image/update',
                        'user/exchange/bank/coin/withdraw/initiate',
                        'user/exchange/bank/coin/withdraw/newVerifycode',
                        'user/exchange/bank/fiat/withdraw/initiate',
                        'user/exchange/bank/fiat/withdraw/newVerifycode',
                        'user/password/change',
                        'user/password/reset',
                        'user/wallet/coin/withdraw/initiate',
                        'wallet/coin/withdraw/newVerifycode',
                    ],
                    'put': [
                        'signup/verify/{token}',
                        'user/exchange/kyc',
                        'user/exchange/bank/fiat/deposit/new',
                        'user/exchange/ask/new',
                        'user/exchange/bid/new',
                        'user/exchange/instant/buy',
                        'user/exchange/instant/sell',
                        'user/exchange/bank/coin/withdraw/verify',
                        'user/exchange/bank/fiat/account/new',
                        'user/exchange/bank/fiat/withdraw/verify',
                        'user/mfa/authy/initiate/enable',
                        'user/mfa/ga/initiate/enable',
                        'user/netki/create',
                        'user/profile/phone/new',
                        'user/wallet/coin/address/new',
                        'user/wallet/coin/new',
                        'user/wallet/coin/withdraw/sendToExchange',
                        'user/wallet/coin/withdraw/verify',
                    ],
                    'delete': [
                        'user/gcm/{code}',
                        'user/logout',
                        'user/exchange/bank/coin/withdraw/unverified/cancel/{withdrawID}',
                        'user/exchange/bank/fiat/deposit/cancel/{depositID}',
                        'user/exchange/ask/cancel/{orderID}',
                        'user/exchange/bid/cancel/{orderID}',
                        'user/exchange/bank/fiat/withdraw/unverified/cancel/{withdrawID}',
                        'user/mfa/authy/disable/{code}',
                        'user/mfa/ga/disable/{code}',
                        'user/profile/phone/delete',
                        'user/profile/image/delete/{netkiName}',
                        'user/wallet/coin/withdraw/unverified/cancel/{withdrawID}',
                    ],
                },
            },
            'products': {
                'BTC/INR': { 'id': 'BTC/INR', 'symbol': 'BTC/INR', 'base': 'BTC', 'quote': 'INR' },
            },
        }
        params.update (config)
        super (coinsecure, self).__init__ (params)

    def fetch_balance (self):
        return self.privateGetUserExchangeBankSummary ()

    def fetch_order_book (self, product):
        bids = self.publicGetExchangeBidOrders ()
        asks = self.publicGetExchangeAskOrders ()
        orderbook = {
            'bids': bids['message'],
            'asks': asks['message'],
        }
        timestamp = self.milliseconds ()
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = [ 'bids', 'asks' ]
        for s in range (0, len (sides)):
            side = sides[s]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = order['rate']
                amount = order['vol']
                result[side].append ([ price, amount ])
        return result

    def fetch_ticker (self, product):
        response = self.publicGetExchangeTicker ()
        ticker = response['message']
        timestamp = ticker['timestamp']
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': None,
            'open': float (ticker['open']),
            'close': None,
            'first': None,
            'last': float (ticker['lastPrice']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': float (ticker['coinvolume']),
            'quoteVolume': float (ticker['fiatvolume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetExchangeTrades ()

    def create_order (self, product, type, side, amount, price = None, params = {}):
        method = 'privatePutUserExchange'
        order = {}
        if type == 'market':       
            method += 'Instant' + self.capitalize (side)
            if side == 'buy':
                order['maxFiat'] = amount
            else:
                order['maxVol'] = amount
        else:
            direction = 'Bid' if (side == 'buy') else 'Ask'
            method += direction + 'New'
            order['rate'] = price
            order['vol'] = amount
        return getattr (self, method) (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.version + '/' + self.implode_params (path, params)
        query = self.omit (params, self.extract_params (path))
        if type == 'private':
            headers = { 'Authorization': self.apiKey }
            if query:
                body = json.dumps (query)
                headers['Content-Type'] = 'application/json'
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class dsx (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'dsx',
            'name': 'DSX',
            'countries': 'UK',
            'rateLimit': 2000,
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27990275-1413158a-645a-11e7-931c-94717f7510e3.jpg',
                'api': {
                    'mapi': 'https://dsx.uk/mapi',  # market data
                    'tapi': 'https://dsx.uk/tapi',  # trading
                    'dwapi': 'https://dsx.uk/dwapi', # deposit/withdraw
                },
                'www': 'https://dsx.uk',
                'doc': [
                    'https://api.dsx.uk',
                    'https://dsx.uk/api_docs/public',
                    'https://dsx.uk/api_docs/private',
                    '',
                ],
            },
            'api': {
                'mapi': { # market data (public)
                    'get': [
                        'barsFromMoment/{id}/{period}/{start}', # empty reply :\
                        'depth/{id}',
                        'info',
                        'lastBars/{id}/{period}/{amount}', # period is (m, h or d)
                        'periodBars/{id}/{period}/{start}/{end}',
                        'ticker/{id}',
                        'trades/{id}',
                    ],
                },
                'tapi': { # trading (private)
                    'post': [
                        'getInfo',
                        'TransHistory',
                        'TradeHistory',
                        'OrderHistory',
                        'ActiveOrders',
                        'Trade',
                        'CancelOrder',
                    ],
                },
                'dwapi': { # deposit / withdraw (private)
                    'post': [
                        'getCryptoDepositAddress',
                        'cryptoWithdraw',
                        'fiatWithdraw',
                        'getTransactionStatus',
                        'getTransactions',
                    ],
                },
            },
        }
        params.update (config)
        super (dsx, self).__init__ (params)

    def fetch_products (self):
        response = self.mapiGetInfo ()
        keys = list (response['pairs'].keys ())
        result = []
        for p in range (0, len (keys)):
            id = keys[p]
            product = response['pairs'][id]
            base = id[0:3]
            quote = id[3:6]
            base = base.upper ()
            quote = quote.upper ()
            symbol = base + '/' + quote
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.tapiPostGetInfo ()

    def fetch_order_book (self, product):
        p = self.product (product)
        response = self.mapiGetDepthId ({
            'id': p['id'],
        })
        orderbook = response[p['id']]
        timestamp = self.milliseconds ()
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = [ 'bids', 'asks' ]
        for s in range (0, len (sides)):
            side = sides[s]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = order[0]
                amount = order[1]
                result[side].append ([ price, amount ])
        return result

    def fetch_ticker (self, product):
        p = self.product (product)
        response = self.mapiGetTickerId ({
            'id': p['id'],
        })
        ticker = response[p['id']]
        timestamp = ticker['updated'] * 1000
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['buy']),
            'ask': float (ticker['sell']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': float (ticker['avg']),
            'baseVolume': float (ticker['vol']),
            'quoteVolume': float (ticker['vol_cur']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.mapiGetTradesId ({
            'id': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        if type == 'market':
            raise Exception (self.id + ' allows limit orders only')
        order = {
            'pair': self.product_id (product),
            'type': side,
            'rate': price,
            'amount': amount,            
        }
        return self.tapiPostTrade (self.extend (order, params))

    def request (self, path, type = 'mapi', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'][type]
        if (type == 'mapi') or (type == 'dwapi'):
            url += '/' + self.implode_params (path, params)
        query = self.omit (params, self.extract_params (path))
        if type == 'mapi':
            if query:
                url += '?' + _urlencode.urlencode (query)
        else:
            nonce = self.nonce ()
            method = path
            body = _urlencode.urlencode (self.extend ({
                'method': path,
            }, query))
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': len (body),
                'Key': self.apiKey,
                'Sign': self.hmac (body, self.secret, hashlib.sha512, 'base64'),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class exmo (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'exmo',
            'name': 'EXMO',
            'countries': [ 'ES', 'RU', ], # Spain, Russia
            'rateLimit': 1000, # once every 350 ms ≈ 180 requests per minute ≈ 3 requests per second
            'version': 'v1',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766491-1b0ea956-5eda-11e7-9225-40d67b481b8d.jpg',
                'api': 'https://api.exmo.com',
                'www': 'https://exmo.me',
                'doc': [
                    'https://exmo.me/ru/api_doc',
                    'https://github.com/exmo-dev/exmo_api_lib/tree/master/nodejs',
                ],
            },
            'api': {
                'public': {
                    'get': [
                        'currency',
                        'order_book',
                        'pair_settings',
                        'ticker',
                        'trades',
                    ],
                },
                'private': {
                    'post': [
                        'user_info',
                        'order_create',
                        'order_cancel',
                        'user_open_orders',
                        'user_trades',
                        'user_cancelled_orders',
                        'order_trades',
                        'required_amount',
                        'deposit_address',
                        'withdraw_crypt',
                        'withdraw_get_txid',
                        'excode_create',
                        'excode_load',
                        'wallet_history',
                    ],
                },
            },
        }
        params.update (config)
        super (exmo, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetPairSettings ()
        keys = list (products.keys ())
        result = []
        for p in range (0, len (keys)):
            id = keys[p]
            product = products[id]
            symbol = id.replace ('_', '/')
            base, quote = symbol.split ('/')
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.privatePostUserInfo ()

    def fetch_order_book (self, product):
        p = self.product (product)
        response = self.publicGetOrderBook ({
            'pair': p['id'],
        })
        orderbook = response[p['id']]
        timestamp = self.milliseconds ()
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = { 'bids': 'bid', 'asks': 'ask' }
        keys = list (sides.keys ())
        for k in range (0, len (keys)):
            key = keys[k]
            side = sides[key]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = float (order[0])
                amount = float (order[1])
                result[key].append ([ price, amount ])
        return result

    def fetch_ticker (self, product):
        response = self.publicGetTicker ()
        p = self.product (product)
        ticker = response[p['id']]
        timestamp = ticker['updated'] * 1000
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['buy_price']),
            'ask': float (ticker['sell_price']),
            'vwap': None,
            'open': float (ticker['open']),
            'close': None,
            'first': None,
            'last': float (ticker['last_trade']),
            'change': None,
            'percentage': None,
            'average': float (ticker['avg']),
            'baseVolume': float (ticker['vol']),
            'quoteVolume': float (ticker['vol_curr']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTrades ({
            'pair': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        prefix = ''
        if type =='market':
            prefix = 'market_'
        order = {
            'pair': self.product_id (product),
            'quantity': amount,
            'price': price or 0,
            'type': prefix + side,
        }
        return self.privatePostOrderCreate (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.version + '/' + path
        if type == 'public':
            if params:
                url += '?' + _urlencode.urlencode (params)
        else:
            nonce = self.nonce ()
            body = _urlencode.urlencode (self.extend ({ 'nonce': nonce }, params))
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': len (body),
                'Key': self.apiKey,
                'Sign': self.hmac (body, self.secret, hashlib.sha512),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class foxbit (blinktrade):

    def __init__ (self, config = {}):
        params = {
            'id': 'foxbit',
            'name': 'FoxBit',
            'countries': 'BR',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27991413-11b40d42-647f-11e7-91ee-78ced874dd09.jpg',
                'api': {
                    'public': 'https://api.blinktrade.com/api',
                    'private': 'https://api.blinktrade.com/tapi',
                },
                'www': 'https://foxbit.exchange',
                'doc': 'https://blinktrade.com/docs',
            },
            'comment': 'Blinktrade API',
            'products': {
                'BTC/BRL': { 'id': 'BTCBRL', 'symbol': 'BTC/BRL', 'base': 'BTC', 'quote': 'BRL', 'brokerId': 4, 'broker': 'FoxBit', },
            },
        }
        params.update (config)
        super (foxbit, self).__init__ (params)

#------------------------------------------------------------------------------

class fyb (Market):

    def __init__ (self, config = {}):
        params = {
            'rateLimit': 2000,
            'api': {
                'public': {
                    'get': [
                        'ticker',
                        'tickerdetailed',
                        'orderbook',
                        'trades',
                    ],
                },
                'private': {
                    'post': [
                        'test',
                        'getaccinfo',
                        'getpendingorders',
                        'getorderhistory',
                        'cancelpendingorder',
                        'placeorder',
                        'withdraw',
                    ],
                },
            },
        }
        params.update (config)
        super (fyb, self).__init__ (params)

    def fetch_balance (self):
        return self.privatePostGetaccinfo ()

    def fetch_order_book (self, product):
        orderbook = self.publicGetOrderbook ()
        timestamp = self.milliseconds ()
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = [ 'bids', 'asks' ]
        for s in range (0, len (sides)):
            side = sides[s]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = float (order[0])
                amount = float (order[1])
                result[side].append ([ price, amount ])
        return result

    def fetch_ticker (self, product):
        ticker = self.publicGetTickerdetailed ()
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': None,
            'low': None,
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['vol']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTrades ()

    def create_order (self, product, type, side, amount, price = None, params = {}):
        return self.privatePostPlaceorder (self.extend ({
            'qty': amount,
            'price': price,
            'type': side[0].upper ()
        }, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + path
        if type == 'public':           
            url += '.json'
        else:
            nonce = self.nonce ()
            body = _urlencode.urlencode (self.extend ({ 'timestamp': nonce }, params))
            headers = {
                'Content-type': 'application/x-www-form-urlencoded',
                'key': self.apiKey,
                'sig': self.hmac (body, self.secret, hashlib.sha1)
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class fybse (fyb):

    def __init__ (self, config = {}):
        params = {
            'id': 'fybse',
            'name': 'FYB-SE',
            'countries': 'SE', # Sweden
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766512-31019772-5edb-11e7-8241-2e675e6797f1.jpg',
                'api': 'https://www.fybse.se/api/SEK',
                'www': 'https://www.fybse.se',
                'doc': 'http://docs.fyb.apiary.io',
            },
            'products': {
                'BTC/SEK': { 'id': 'SEK', 'symbol': 'BTC/SEK', 'base': 'BTC', 'quote': 'SEK' },
            },
        }
        params.update (config)
        super (fybse, self).__init__ (params)

#------------------------------------------------------------------------------

class fybsg (fyb):

    def __init__ (self, config = {}):
        params = {
            'id': 'fybsg',
            'name': 'FYB-SG',
            'countries': 'SG', # Singapore
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766513-3364d56a-5edb-11e7-9e6b-d5898bb89c81.jpg',
                'api': 'https://www.fybsg.com/api/SGD',
                'www': 'https://www.fybsg.com',
                'doc': 'http://docs.fyb.apiary.io',
            },
            'products': {
                'BTC/SGD': { 'id': 'SGD', 'symbol': 'BTC/SGD', 'base': 'BTC', 'quote': 'SGD' },
            },
        }
        params.update (config)
        super (fybsg, self).__init__ (params)

#------------------------------------------------------------------------------

class gdax (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'gdax',
            'name': 'GDAX',
            'countries': 'US',
            'rateLimit': 1000,
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766527-b1be41c6-5edb-11e7-95f6-5b496c469e2c.jpg',
                'api': 'https://api.gdax.com',
                'www': 'https://www.gdax.com',
                'doc': 'https://docs.gdax.com',
            },
            'api': {
                'public': {
                    'get': [
                        'currencies',
                        'products',
                        'products/{id}/book',
                        'products/{id}/candles',
                        'products/{id}/stats',
                        'products/{id}/ticker',
                        'products/{id}/trades',
                        'time',
                    ],
                },
                'private': {
                    'get': [
                        'accounts',
                        'accounts/{id}',
                        'accounts/{id}/holds',
                        'accounts/{id}/ledger',
                        'coinbase-accounts',
                        'fills',
                        'funding',
                        'orders',
                        'orders/{id}',
                        'payment-methods',
                        'position',
                        'reports/{id}',
                        'users/self/trailing-volume',
                    ],
                    'post': [
                        'deposits/coinbase-account',
                        'deposits/payment-method',
                        'funding/repay',
                        'orders',
                        'position/close',
                        'profiles/margin-transfer',
                        'reports',
                        'withdrawals/coinbase',
                        'withdrawals/crypto',
                        'withdrawals/payment-method',
                    ],
                    'delete': [
                        'orders',
                        'orders/{id}',
                    ],
                },
            },
        }
        params.update (config)
        super (gdax, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetProducts ()
        result = []
        for p in range (0, len (products)):
            product = products[p]
            id = product['id']
            base = product['base_currency']
            quote = product['quote_currency']
            symbol = base + '/' + quote            
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.privateGetAccounts ()

    def fetch_order_book (self, product):
        orderbook = self.publicGetProductsIdBook ({
            'id': self.product_id (product),
            'level': 2, # 1 best bidask, 2 aggregated, 3 full
        })
        timestamp = self.milliseconds ()
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = [ 'bids', 'asks' ]
        for s in range (0, len (sides)):
            side = sides[s]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = float (order[0])
                amount = float (order[1])
                result[side].append ([ price, amount ])
        return result

    def fetch_ticker (self, product):
        p = self.product (product)
        ticker = self.publicGetProductsIdTicker ({
            'id': p['id'],
        })
        quote = self.publicGetProductsIdStats ({
            'id': p['id'],
        })
        timestamp = self.parse8601 (ticker['time'])
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (quote['high']),
            'low': float (quote['low']),
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': None,
            'open': float (quote['open']),
            'close': None,
            'first': None,
            'last': float (quote['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetProductsIdTrades ({
            'id': self.product_id (product), # fixes issue #2
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        order = {
            'client_oid': self.nonce (),
            'product_id': self.product_id (product),
            'side': side,
            'size': amount,
            'type': type,            
        }
        if type == 'limit':
            order['price'] = price
        return self.privatePostOrder (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        request = '/' + self.implode_params (path, params)
        url = self.urls['api'] + request
        query = self.omit (params, self.extract_params (path))
        if type == 'public':
            if query:
                url += '?' + _urlencode.urlencode (query)
        else:
            nonce = str (self.nonce ())
            if query:
                body = json.dumps (query)
            what = nonce + method + request + (body or '')
            secret = base64.b64decode (self.secret)
            signature = self.hash (what, secret, hashlib.sha256, 'binary')
            headers = {
                'CB-ACCESS-KEY': self.apiKey,
                'CB-ACCESS-SIGN': base64.b64encode (signature),
                'CB-ACCESS-TIMESTAMP': nonce,
                'CB-ACCESS-PASSPHRASE': self.password,
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class gemini (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'gemini',
            'name': 'Gemini',
            'countries': 'US',
            'rateLimit': 2000, # 200 for private API
            'version': 'v1',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27816857-ce7be644-6096-11e7-82d6-3c257263229c.jpg',
                'api': 'https://api.gemini.com',
                'www': 'https://gemini.com',
                'doc': 'https://docs.gemini.com/rest-api',
            },
            'api': {
                'public': {
                    'get': [
                        'symbols',
                        'pubticker/{symbol}',
                        'book/{symbol}',
                        'trades/{symbol}',
                        'auction/{symbol}',
                        'auction/{symbol}/history',
                    ],
                },
                'private': {
                    'post': [
                        'order/new',
                        'order/cancel',
                        'order/cancel/session',
                        'order/cancel/all',
                        'order/status',
                        'orders',
                        'mytrades',
                        'tradevolume',
                        'balances',
                        'deposit/{currency}/newAddress',
                        'withdraw/{currency}',
                        'heartbeat',
                    ],
                },
            },
        }
        params.update (config)
        super (gemini, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetSymbols ()
        result = []
        for p in range (0, len (products)):
            product = products[p]
            id = product
            uppercaseProduct = product.upper ()
            base = uppercaseProduct[0:3]
            quote = uppercaseProduct[3:6]
            symbol = base + '/' + quote
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_order_book (self, product):
        orderbook = self.publicGetBookSymbol ({
            'symbol': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = [ 'bids', 'asks' ]
        for s in range (0, len (sides)):
            side = sides[s]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = float (order['price'])
                amount = float (order['amount'])
                timestamp = int (order['timestamp']) * 1000
                result[side].append ([ price, amount, timestamp ])
        return result

    def fetch_ticker (self, product):
        p = self.product (product)
        ticker = self.publicGetPubtickerSymbol ({
            'symbol': p['id'],
        })
        timestamp = ticker['volume']['timestamp']
        baseVolume = p['base']
        quoteVolume = p['quote']
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': None,
            'low': None,
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': float (ticker['volume'][baseVolume]),
            'quoteVolume': float (ticker['volume'][quoteVolume]),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTradesSymbol ({
            'symbol': self.product_id (product),
        })

    def fetch_balance (self):
        return self.privatePostBalances ()

    def create_order (self, product, type, side, amount, price = None, params = {}):
        if type == 'market':
            raise Exception (self.id + ' allows limit orders only')
        order = {
            'client_order_id': self.nonce (),
            'symbol': self.product_id (product),
            'amount': str (amount),
            'price': str (price),
            'side': side,
            'type': 'exchange limit', # gemini allows limit orders only
        }
        return self.privatePostOrderNew (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = '/' + self.version + '/' + self.implode_params (path, params)
        query = self.omit (params, self.extract_params (path))
        if type == 'public':
            if query:
                url += '?' + _urlencode.urlencode (query)
        else:
            nonce = self.nonce ()
            request = self.extend ({
                'request': url,
                'nonce': nonce,
            }, query)
            payload = base64.b64encode (json.dumps (request))
            signature = self.hmac (payload, self.secret, hashlib.sha384)
            headers = {
                'Content-Type': 'text/plain',
                'Content-Length': 0,
                'X-GEMINI-APIKEY': self.apiKey,
                'X-GEMINI-PAYLOAD': payload,
                'X-GEMINI-SIGNATURE': signature,
            }
        url = self.urls['api'] + url
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class hitbtc (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'hitbtc',
            'name': 'HitBTC',
            'countries': 'HK', # Hong Kong
            'rateLimit': 2000,
            'version': '1',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766555-8eaec20e-5edc-11e7-9c5b-6dc69fc42f5e.jpg',
                'api': 'http://api.hitbtc.com',
                'www': 'https://hitbtc.com',
                'doc': [
                    'https://hitbtc.com/api',
                    'http://hitbtc-com.github.io/hitbtc-api',
                    'http://jsfiddle.net/bmknight/RqbYB',
                ],
            },
            'api': {
                'public': {
                    'get': [
                        '{symbol}/orderbook',
                        '{symbol}/ticker',
                        '{symbol}/trades',
                        '{symbol}/trades/recent',
                        'symbols',
                        'ticker',
                        'time,'
                    ],
                },
                'trading': {
                    'get': [
                        'balance',
                        'orders/active',
                        'orders/recent',
                        'order',
                        'trades/by/order',
                        'trades',
                    ],
                    'post': [
                        'new_order',
                        'cancel_order',
                        'cancel_orders',
                    ],
                },
                'payment': {
                    'get': [
                        'balance',
                        'address/{currency}',
                        'transactions',
                        'transactions/{transaction}',
                    ],
                    'post': [
                        'transfer_to_trading',
                        'transfer_to_main',
                        'address/{currency}',
                        'payout',
                    ],
                }
            },
        }
        params.update (config)
        super (hitbtc, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetSymbols ()
        result = []
        for p in range (0, len (products['symbols'])):
            product = products['symbols'][p]
            id = product['symbol']
            base = product['commodity']
            quote = product['currency']
            symbol = base + '/' + quote
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.tradingGetBalance ()

    def fetch_order_book (self, product):
        orderbook = self.publicGetSymbolOrderbook ({
            'symbol': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = [ 'bids', 'asks' ]
        for s in range (0, len (sides)):
            side = sides[s]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = float (order[0])
                amount = float (order[1])
                result[side].append ([ price, amount ])
        return result

    def fetch_ticker (self, product):
        ticker = self.publicGetSymbolTicker ({
            'symbol': self.product_id (product),
        })
        timestamp = ticker['timestamp']
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': None,
            'open': float (ticker['open']),
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': float (ticker['volume']),
            'quoteVolume': float (ticker['volume_quote']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetSymbolTrades ({
            'symbol': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        order = {
            'clientOrderId': self.nonce (),
            'symbol': self.product_id (product),
            'side': side,
            'quantity': amount,
            'type': type,            
        }
        if type == 'limit':
            order['price'] = price
        return self.tradingPostNewOrder (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = '/api/' + self.version + '/' + type + '/' + self.implode_params (path, params)
        query = self.omit (params, self.extract_params (path))
        if type == 'public':
            if query:
                url += '?' + _urlencode.urlencode (query)
        else:
            nonce = self.nonce ()
            query = self.extend ({ 'nonce': nonce, 'apikey': self.apiKey }, query)
            if method == 'POST':
                if query:
                    body = _urlencode.urlencode (query)
            if query:
                url += '?' + _urlencode.urlencode (query)
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Signature': self.hmac (url + (body or ''), self.secret, hashlib.sha512).lower (),
            }
        url = self.urls['api'] + url
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class huobi (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'huobi',
            'name': 'Huobi',
            'countries': 'CN',
            'rateLimit': 5000,
            'version': 'v3',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766569-15aa7b9a-5edd-11e7-9e7f-44791f4ee49c.jpg',
                'api': 'http://api.huobi.com',
                'www': 'https://www.huobi.com',
                'doc': 'https://github.com/huobiapi/API_Docs_en/wiki',
            },
            'api': {
                'staticmarket': {
                    'get': [
                        '{id}_kline_{period}',
                        'ticker_{id}',
                        'depth_{id}',
                        'depth_{id}_{length}',
                        'detail_{id}',
                    ],
                },
                'usdmarket': {
                    'get': [
                        '{id}_kline_{period}',
                        'ticker_{id}',
                        'depth_{id}',
                        'depth_{id}_{length}',
                        'detail_{id}',
                    ],
                },
                'trade': {
                    'post': [
                        'get_account_info',
                        'get_orders',
                        'order_info',
                        'buy',
                        'sell',
                        'buy_market',
                        'sell_market',
                        'cancel_order',
                        'get_new_deal_orders',
                        'get_order_id_by_trade_id',
                        'withdraw_coin',
                        'cancel_withdraw_coin',
                        'get_withdraw_coin_result',
                        'transfer',
                        'loan',
                        'repayment',
                        'get_loan_available',
                        'get_loans',
                    ],            
                },
            },
            'products': {
                'BTC/CNY': { 'id': 'btc', 'symbol': 'BTC/CNY', 'base': 'BTC', 'quote': 'CNY', 'type': 'staticmarket', 'coinType': 1, },
                'LTC/CNY': { 'id': 'ltc', 'symbol': 'LTC/CNY', 'base': 'LTC', 'quote': 'CNY', 'type': 'staticmarket', 'coinType': 2, },
                'BTC/USD': { 'id': 'btc', 'symbol': 'BTC/USD', 'base': 'BTC', 'quote': 'USD', 'type': 'usdmarket',    'coinType': 1, },
            },
        }
        params.update (config)
        super (huobi, self).__init__ (params)

    def fetch_balance (self):
        return self.tradePostGetAccountInfo ()

    def fetch_order_book (self, product):
        p = self.product (product)
        method = p['type'] + 'GetDepthId'
        orderbook = getattr (self, method) ({ 'id': p['id'] })
        timestamp = self.milliseconds ()
        result = {
            'bids': orderbook['bids'],
            'asks': orderbook['asks'],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        return result

    def fetch_ticker (self, product):
        p = self.product (product)
        method = p['type'] + 'GetTickerId'
        response = getattr (self, method) ({ 'id': p['id'] })
        ticker = response['ticker']
        timestamp = int (response['time']) * 1000
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['buy']),
            'ask': float (ticker['sell']),
            'vwap': None,
            'open': float (ticker['open']),
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['vol']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        p = self.product (product)
        method = p['type'] + 'GetDetailId'
        return getattr (self, method) ({ 'id': p['id'] })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        p = self.product (product)
        method = 'tradePost' + self.capitalize (side)
        order = {
            'coin_type': p['coinType'],
            'amount': amount,
            'market': p['quote'].lower (),
        }
        if type == 'limit':
            order['price'] = price
        else:
            method += self.capitalize (type)
        return getattr (self, method) (self.extend (order, params))

    def request (self, path, type = 'trade', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api']
        if type == 'trade':
            url += '/api' + self.version
            query = self.keysort (self.extend ({
                'method': path,
                'access_key': self.apiKey,
                'created': self.nonce (),
            }, params))
            queryString = _urlencode.urlencode (self.omit (query, 'market'))
            # secret key must be at the end of query to be signed
            queryString += '&secret_key=' + self.secret
            query['sign'] = self.hash (queryString)
            body = _urlencode.urlencode (query)
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': len (body),
            }
        else:
            url += '/' + type + '/' + self.implode_params (path, params) + '_json.js'
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class itbit (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'itbit',    
            'name': 'itBit',
            'countries': 'US',
            'rateLimit': 3000,
            'version': 'v1',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27822159-66153620-60ad-11e7-89e7-005f6d7f3de0.jpg',
                'api': 'https://api.itbit.com',
                'www': 'https://www.itbit.com',
                'doc': [
                    'https://www.itbit.com/api',
                    'https://api.itbit.com/docs',
                ],
            },
            'api': {
                'public': {
                    'get': [
                        'markets/{symbol}/ticker',
                        'markets/{symbol}/order_book',
                        'markets/{symbol}/trades',
                    ],
                },
                'private': {
                    'get': [
                        'wallets',
                        'wallets/{walletId}',
                        'wallets/{walletId}/balances/{currencyCode}',
                        'wallets/{walletId}/funding_history',
                        'wallets/{walletId}/trades',
                        'wallets/{walletId}/orders/{orderId}',
                    ],
                    'post': [
                        'wallet_transfers',
                        'wallets',
                        'wallets/{walletId}/cryptocurrency_deposits',
                        'wallets/{walletId}/cryptocurrency_withdrawals',
                        'wallets/{walletId}/orders',
                        'wire_withdrawal',
                    ],
                    'delete': [
                        'wallets/{walletId}/orders/{orderId}',
                    ],
                },
            },
            'products': {
                'BTC/USD': { 'id': 'XBTUSD', 'symbol': 'BTC/USD', 'base': 'BTC', 'quote': 'USD' },
                'BTC/SGD': { 'id': 'XBTSGD', 'symbol': 'BTC/SGD', 'base': 'BTC', 'quote': 'SGD' },
                'BTC/EUR': { 'id': 'XBTEUR', 'symbol': 'BTC/EUR', 'base': 'BTC', 'quote': 'EUR' },
            },
        }
        params.update (config)
        super (itbit, self).__init__ (params)

    def fetch_order_book (self, product):
        orderbook = self.publicGetMarketsSymbolOrderBook ({ 
            'symbol': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = [ 'bids', 'asks' ]
        for s in range (0, len (sides)):
            side = sides[s]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = float (order[0])
                amount = float (order[1])
                result[side].append ([ price, amount ])
        return result

    def fetch_ticker (self, product):
        ticker = self.publicGetMarketsSymbolTicker ({
            'symbol': self.product_id (product),
        })
        timestamp = self.parse8601 (ticker['serverTimeUTC'])
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high24h']),
            'low': float (ticker['low24h']),
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': float (ticker['vwap24h']),
            'open': float (ticker['openToday']),
            'close': None,
            'first': None,
            'last': float (ticker['lastPrice']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['volume24h']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetMarketsSymbolTrades ({
            'symbol': self.product_id (product),
        })

    def fetch_balance (self):
        return self.privateGetWallets ()

    def nonce (self):
        return self.milliseconds ()

    def create_order (self, product, type, side, amount, price = None, params = {}):
        if type == 'market':
            raise Exception (self.id + ' allows limit orders only')
        amount = str (amount)
        price = str (price)
        p = self.product (product)
        order = {
            'side': side,
            'type': type,
            'currency': p['base'],
            'amount': amount,
            'display': amount,
            'price': price,
            'instrument': p['id'],
        }
        return self.privatePostTradeAdd (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.version + '/' + self.implode_params (path, params)
        query = self.omit (params, self.extract_params (path))
        if type == 'public':
            if query:
                url += '?' + _urlencode.urlencode (query)
        else:
            if query:
                body = json.dumps (query)
            else:
                body = ''
            nonce = str (self.nonce ())
            timestamp = nonce
            auth = [ method, url, body, nonce, timestamp ]
            message = nonce + json.dumps (auth)
            hashedMessage = self.hash (message, hashlib.sha256, 'binary')
            signature = self.hmac (url + hashedMessage, self.secret, hashlib.sha512, 'base64')
            headers = {
                'Authorization': self.apiKey + ':' + signature,
                'Content-Type': 'application/json',
                'X-Auth-Timestamp': timestamp,
                'X-Auth-Nonce': nonce,
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class jubi (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'jubi',
            'name': 'jubi.com',
            'countries': 'CN',
            'rateLimit': 2000,
            'version': 'v1',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766581-9d397d9a-5edd-11e7-8fb9-5d8236c0e692.jpg',
                'api': 'https://www.jubi.com/api',
                'www': 'https://www.jubi.com',
                'doc': 'https://www.jubi.com/help/api.html',
            },
            'api': {
                'public': {
                    'get': [
                        'depth',
                        'orders',
                        'ticker',
                    ],
                },
                'private': {
                    'post': [
                        'balance',
                        'trade_add',
                        'trade_cancel',
                        'trade_list',
                        'trade_view',
                        'wallet',
                    ],
                },
            },
            'products': {
                'BTC/CNY':  { 'id': 'btc',  'symbol': 'BTC/CNY',  'base': 'BTC',  'quote': 'CNY' },
                'ETH/CNY':  { 'id': 'eth',  'symbol': 'ETH/CNY',  'base': 'ETH',  'quote': 'CNY' },
                'ANS/CNY':  { 'id': 'ans',  'symbol': 'ANS/CNY',  'base': 'ANS',  'quote': 'CNY' },
                'BLK/CNY':  { 'id': 'blk',  'symbol': 'BLK/CNY',  'base': 'BLK',  'quote': 'CNY' },
                'DNC/CNY':  { 'id': 'dnc',  'symbol': 'DNC/CNY',  'base': 'DNC',  'quote': 'CNY' },
                'DOGE/CNY': { 'id': 'doge', 'symbol': 'DOGE/CNY', 'base': 'DOGE', 'quote': 'CNY' },
                'EAC/CNY':  { 'id': 'eac',  'symbol': 'EAC/CNY',  'base': 'EAC',  'quote': 'CNY' },
                'ETC/CNY':  { 'id': 'etc',  'symbol': 'ETC/CNY',  'base': 'ETC',  'quote': 'CNY' },
                'FZ/CNY':   { 'id': 'fz',   'symbol': 'FZ/CNY',   'base': 'FZ',   'quote': 'CNY' },
                'GOOC/CNY': { 'id': 'gooc', 'symbol': 'GOOC/CNY', 'base': 'GOOC', 'quote': 'CNY' },
                'GAME/CNY': { 'id': 'game', 'symbol': 'GAME/CNY', 'base': 'GAME', 'quote': 'CNY' },
                'HLB/CNY':  { 'id': 'hlb',  'symbol': 'HLB/CNY',  'base': 'HLB',  'quote': 'CNY' },
                'IFC/CNY':  { 'id': 'ifc',  'symbol': 'IFC/CNY',  'base': 'IFC',  'quote': 'CNY' },
                'JBC/CNY':  { 'id': 'jbc',  'symbol': 'JBC/CNY',  'base': 'JBC',  'quote': 'CNY' },
                'KTC/CNY':  { 'id': 'ktc',  'symbol': 'KTC/CNY',  'base': 'KTC',  'quote': 'CNY' },
                'LKC/CNY':  { 'id': 'lkc',  'symbol': 'LKC/CNY',  'base': 'LKC',  'quote': 'CNY' },
                'LSK/CNY':  { 'id': 'lsk',  'symbol': 'LSK/CNY',  'base': 'LSK',  'quote': 'CNY' },
                'LTC/CNY':  { 'id': 'ltc',  'symbol': 'LTC/CNY',  'base': 'LTC',  'quote': 'CNY' },
                'MAX/CNY':  { 'id': 'max',  'symbol': 'MAX/CNY',  'base': 'MAX',  'quote': 'CNY' },
                'MET/CNY':  { 'id': 'met',  'symbol': 'MET/CNY',  'base': 'MET',  'quote': 'CNY' },
                'MRYC/CNY': { 'id': 'mryc', 'symbol': 'MRYC/CNY', 'base': 'MRYC', 'quote': 'CNY' },        
                'MTC/CNY':  { 'id': 'mtc',  'symbol': 'MTC/CNY',  'base': 'MTC',  'quote': 'CNY' },
                'NXT/CNY':  { 'id': 'nxt',  'symbol': 'NXT/CNY',  'base': 'NXT',  'quote': 'CNY' },
                'PEB/CNY':  { 'id': 'peb',  'symbol': 'PEB/CNY',  'base': 'PEB',  'quote': 'CNY' },
                'PGC/CNY':  { 'id': 'pgc',  'symbol': 'PGC/CNY',  'base': 'PGC',  'quote': 'CNY' },
                'PLC/CNY':  { 'id': 'plc',  'symbol': 'PLC/CNY',  'base': 'PLC',  'quote': 'CNY' },
                'PPC/CNY':  { 'id': 'ppc',  'symbol': 'PPC/CNY',  'base': 'PPC',  'quote': 'CNY' },
                'QEC/CNY':  { 'id': 'qec',  'symbol': 'QEC/CNY',  'base': 'QEC',  'quote': 'CNY' },
                'RIO/CNY':  { 'id': 'rio',  'symbol': 'RIO/CNY',  'base': 'RIO',  'quote': 'CNY' },
                'RSS/CNY':  { 'id': 'rss',  'symbol': 'RSS/CNY',  'base': 'RSS',  'quote': 'CNY' },
                'SKT/CNY':  { 'id': 'skt',  'symbol': 'SKT/CNY',  'base': 'SKT',  'quote': 'CNY' },
                'TFC/CNY':  { 'id': 'tfc',  'symbol': 'TFC/CNY',  'base': 'TFC',  'quote': 'CNY' },
                'VRC/CNY':  { 'id': 'vrc',  'symbol': 'VRC/CNY',  'base': 'VRC',  'quote': 'CNY' },
                'VTC/CNY':  { 'id': 'vtc',  'symbol': 'VTC/CNY',  'base': 'VTC',  'quote': 'CNY' },
                'WDC/CNY':  { 'id': 'wdc',  'symbol': 'WDC/CNY',  'base': 'WDC',  'quote': 'CNY' },
                'XAS/CNY':  { 'id': 'xas',  'symbol': 'XAS/CNY',  'base': 'XAS',  'quote': 'CNY' },
                'XPM/CNY':  { 'id': 'xpm',  'symbol': 'XPM/CNY',  'base': 'XPM',  'quote': 'CNY' },
                'XRP/CNY':  { 'id': 'xrp',  'symbol': 'XRP/CNY',  'base': 'XRP',  'quote': 'CNY' },
                'XSGS/CNY': { 'id': 'xsgs', 'symbol': 'XSGS/CNY', 'base': 'XSGS', 'quote': 'CNY' },
                'YTC/CNY':  { 'id': 'ytc',  'symbol': 'YTC/CNY',  'base': 'YTC',  'quote': 'CNY' },
                'ZET/CNY':  { 'id': 'zet',  'symbol': 'ZET/CNY',  'base': 'ZET',  'quote': 'CNY' },
                'ZCC/CNY':  { 'id': 'zcc',  'symbol': 'ZCC/CNY',  'base': 'ZCC',  'quote': 'CNY' },        
            },
        }
        params.update (config)
        super (jubi, self).__init__ (params)

    def fetch_balance (self):
        return self.privatePostBalance ()

    def fetch_order_book (self, product):
        orderbook = self.publicGetDepth ({
            'coin': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        result = {
            'bids': orderbook['bids'],
            'asks': orderbook['asks'],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        result['asks'] = self.sort_by (result['asks'], 0)
        return result

    def fetch_ticker (self, product):
        ticker = self.publicGetTicker ({ 
            'coin': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['buy']),
            'ask': float (ticker['sell']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': float (ticker['vol']),
            'quoteVolume': float (ticker['volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetOrders ({
            'coin': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        return self.privatePostTradeAdd (self.extend ({
            'amount': amount,
            'price': price,
            'type': side,
            'coin': self.product_id (product),
        }, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.version + '/' + path
        if type == 'public':  
            if params:
                url += '?' + _urlencode.urlencode (params)
        else:
            nonce = str (self.nonce ())
            query = self.extend ({
                'key': self.apiKey,
                'nonce': nonce,
            }, params)
            query['signature'] = self.hmac (_urlencode.urlencode (query), self.hash (self.secret))
            body = _urlencode.urlencode (query)
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': len (body),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class kraken (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'kraken',
            'name': 'Kraken',
            'countries': 'US',
            'version': '0',
            'rateLimit': 3000,
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766599-22709304-5ede-11e7-9de1-9f33732e1509.jpg',
                'api': 'https://api.kraken.com',
                'www': 'https://www.kraken.com',
                'doc': [
                    'https://www.kraken.com/en-us/help/api',
                    'https://github.com/nothingisdead/npm-kraken-api',
                ],
            },
            'api': {
                'public': {
                    'get': [
                        'Assets',
                        'AssetPairs',
                        'Depth',
                        'OHLC',
                        'Spread',
                        'Ticker',
                        'Time',
                        'Trades',
                    ],
                },
                'private': {
                    'post': [
                        'AddOrder',
                        'Balance',
                        'CancelOrder',
                        'ClosedOrders',
                        'DepositAddresses',
                        'DepositMethods',
                        'DepositStatus',
                        'Ledgers',
                        'OpenOrders',
                        'OpenPositions', 
                        'QueryLedgers', 
                        'QueryOrders', 
                        'QueryTrades',
                        'TradeBalance',
                        'TradesHistory',
                        'TradeVolume',
                        'Withdraw',
                        'WithdrawCancel', 
                        'WithdrawInfo',                 
                        'WithdrawStatus',
                    ],
                },
            },
        }
        params.update (config)
        super (kraken, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetAssetPairs ()
        keys = list (products['result'].keys ())
        result = []
        for p in range (0, len (keys)):
            id = keys[p]
            product = products['result'][id]
            base = product['base']
            quote = product['quote']
            if (base[0] == 'X') or (base[0] == 'Z'):
                base = base[1:]
            if (quote[0] == 'X') or (quote[0] == 'Z'):
                quote = quote[1:]
            base = self.commonCurrencyCode (base)
            quote = self.commonCurrencyCode (quote)
            darkpool = id.find ('.d') >= 0
            symbol = product['altname'] if darkpool else (base + '/' + quote)
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_order_book (self, product):
        p = self.product (product)
        response = self.publicGetDepth  ({
            'pair': p['id'],
        })
        orderbook = response['result'][p['id']]
        timestamp = self.milliseconds ()
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = [ 'bids', 'asks' ]
        for s in range (0, len (sides)):
            side = sides[s]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = float (order[0])
                amount = float (order[1])
                timestamp = order[2] * 1000
                result[side].append ([ price, amount, timestamp ])
        return result

    def fetch_ticker (self, product):
        p = self.product (product)
        response = self.publicGetTicker ({
            'pair': p['id'],
        })
        ticker = response['result'][p['id']]
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['h'][1]),
            'low': float (ticker['l'][1]),
            'bid': float (ticker['b'][0]),
            'ask': float (ticker['a'][0]),
            'vwap': float (ticker['p'][1]),
            'open': float (ticker['o']),
            'close': None,
            'first': None,
            'last': float (ticker['c'][0]),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['v'][1]),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTrades ({
            'pair': self.product_id (product),
        })

    def fetch_balance (self):
        return self.privatePostBalance ()

    def create_order (self, product, type, side, amount, price = None, params = {}):
        order = {
            'pair': self.product_id (product),
            'type': side,
            'ordertype': type,
            'volume': amount,
        }
        if type == 'limit':
            order['price'] = price
        return self.privatePostAddOrder (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = '/' + self.version + '/' + type + '/' + path
        if type == 'public':
            if params:
                url += '?' + _urlencode.urlencode (params)
        else:
            nonce = str (self.nonce ())
            query = self.extend ({ 'nonce': nonce }, params)
            body = _urlencode.urlencode (query)
            query = url + self.hash (nonce + body, hashlib.sha256, 'binary')
            secret = base64.b64decode (self.secret)
            headers = {
                'API-Key': self.apiKey,
                'API-Sign': self.hmac (query, secret, hashlib.sha512, 'base64'),
                'Content-type': 'application/x-www-form-urlencoded',
            }
        url = self.urls['api'] + url
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class livecoin (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'livecoin',
            'name': 'LiveCoin',
            'countries': [ 'US', 'UK', 'RU' ],
            'rateLimit': 1000,
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27980768-f22fc424-638a-11e7-89c9-6010a54ff9be.jpg',
                'api': 'https://api.livecoin.net',
                'www': 'https://www.livecoin.net',
                'doc': 'https://www.livecoin.net/api?lang=en',
            },
            'api': {
                'public': {
                    'get': [
                        'exchange/all/order_book',
                        'exchange/last_trades',
                        'exchange/maxbid_minask',
                        'exchange/order_book',
                        'exchange/restrictions',
                        'exchange/ticker', # omit params to get all tickers at once
                        'info/coinInfo',
                    ],
                },
                'private': {
                    'get': [
                        'exchange/client_orders',
                        'exchange/order',
                        'exchange/trades',
                        'exchange/commission',
                        'exchange/commissionCommonInfo',
                        'payment/balances',
                        'payment/balance',
                        'payment/get/address',
                        'payment/history/size',
                        'payment/history/transactions',
                    ],
                    'post': [
                        'exchange/buylimit',
                        'exchange/buymarket',
                        'exchange/cancellimit',
                        'exchange/selllimit',
                        'exchange/sellmarket',
                        'payment/out/capitalist',
                        'payment/out/card',
                        'payment/out/coin',
                        'payment/out/okpay',
                        'payment/out/payeer',
                        'payment/out/perfectmoney',
                        'payment/voucher/amount',
                        'payment/voucher/make',
                        'payment/voucher/redeem',
                    ],
                },
            },
        }
        params.update (config)
        super (livecoin, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetExchangeTicker ()
        result = []
        for p in range (0, len (products)):
            product = products[p]
            id = product['symbol']
            symbol = id
            base, quote = symbol.split ('/')
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.privateGetPaymentBalances ()

    def fetch_order_book (self, product):
        orderbook = self.publicGetExchangeOrderBook ({
            'currencyPair': self.product_id (product),
            'groupByPrice': 'false',
            'depth': 100,
        })
        timestamp = orderbook['timestamp']
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = [ 'bids', 'asks' ]
        for s in range (0, len (sides)):
            side = sides[s]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = float (order[0])
                amount = float (order[1])
                result[side].append ([ price, amount ])
        return result

    def fetch_ticker (self, product):
        ticker = self.publicGetExchangeTicker ({
            'currencyPair': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['best_bid']),
            'ask': float (ticker['best_ask']),
            'vwap': float (ticker['vwap']),
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetExchangeLastTrades ({
            'currencyPair': self.product_id (product)
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        method = 'privatePost' + self.capitalize (side) + type
        order = {
            'currencyPair': self.product_id (product),
            'quantity': amount,
        }
        if type == 'limit':
            order['price'] = price
        return getattr (self, method) (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + path
        if type == 'public':
            if params:
                url += '?' + _urlencode.urlencode (params)
        else:
            query = self.keysort (params)
            body = _urlencode.urlencode (query)
            signature = self.hmac (body, self.secret, hashlib.sha256)
            headers = {
                'Api-Key': self.apiKey,
                'Sign': signature.upper (),
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': len (body),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class liqui (btce):

    def __init__ (self, config = {}):
        params = {
            'id': 'liqui',
            'name': 'Liqui',
            'countries': [ 'UA', ],
            'rateLimit': 1000,
            'version': '3',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27982022-75aea828-63a0-11e7-9511-ca584a8edd74.jpg',
                'api': {
                    'public': 'https://api.liqui.io/api',
                    'private': 'https://api.liqui.io/tapi',
                },
                'www': 'https://liqui.io',
                'doc': 'https://liqui.io/api',
            },
        }
        params.update (config)
        super (liqui, self).__init__ (params)

#------------------------------------------------------------------------------

class luno (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'luno',
            'name': 'luno',
            'countries': [ 'GB', 'SG', 'ZA', ],
            'rateLimit': 5000,
            'version': '1',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766607-8c1a69d8-5ede-11e7-930c-540b5eb9be24.jpg',
                'api': 'https://api.mybitx.com/api',
                'www': 'https://www.luno.com',
                'doc': [
                    'https://npmjs.org/package/bitx',
                    'https://github.com/bausmeier/node-bitx',
                ],
            },
            'api': {
                'public': {
                    'get': [
                        'orderbook',
                        'ticker',
                        'tickers',
                        'trades',
                    ],
                },
                'private': {
                    'get': [
                        'accounts/{id}/pending',
                        'accounts/{id}/transactions',
                        'balance',
                        'fee_info',
                        'funding_address',
                        'listorders',
                        'listtrades',
                        'orders/{id}',
                        'quotes/{id}',
                        'withdrawals',
                        'withdrawals/{id}',
                    ],
                    'post': [
                        'accounts',
                        'postorder',
                        'marketorder',
                        'stoporder',
                        'funding_address',
                        'withdrawals',
                        'send',
                        'quotes',
                        'oauth2/grant',
                    ],
                    'put': [
                        'quotes/{id}',
                    ],
                    'delete': [
                        'quotes/{id}',
                        'withdrawals/{id}',
                    ],
                },
            },
        }
        params.update (config)
        super (luno, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetTickers ()
        result = []
        for p in range (0, len (products['tickers'])):
            product = products['tickers'][p]
            id = product['pair']
            base = id[0:3]
            quote = id[3:6]
            base = self.commonCurrencyCode (base)
            quote = self.commonCurrencyCode (quote)
            symbol = base + '/' + quote
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.privateGetBalance ()

    def fetch_order_book (self, product):
        orderbook = self.publicGetOrderbook ({
            'pair': self.product_id (product),
        })
        timestamp = orderbook['timestamp']
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = [ 'bids', 'asks' ]
        for s in range (0, len (sides)):
            side = sides[s]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = float (order['price'])
                amount = float (order['volume'])
                # timestamp = order[2] * 1000
                result[side].append ([ price, amount ])
        return result

    def fetch_ticker (self, product):
        ticker = self.publicGetTicker ({
            'pair': self.product_id (product),
        })
        timestamp = ticker['timestamp']
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': None,
            'low': None,
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last_trade']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['rolling_24_hour_volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTrades ({
            'pair': self.product_id (product)
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        method = 'privatePost'
        order = { 'pair': self.product_id (product) }
        if type == 'market':
            method += 'Marketorder'
            order['type'] = side.upper ()
            if side == 'buy':
                order['counter_volume'] = amount
            else:
                order['base_volume'] = amount            
        else:
            method += 'Order'
            order['volume'] = amount
            order['price'] = price
            if side == 'buy':
                order['type'] = 'BID'
            else:
                order['type'] = 'ASK'
        return getattr (self, method) (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.version + '/' + self.implode_params (path, params)
        query = self.omit (params, self.extract_params (path))
        if query:
            url += '?' + _urlencode.urlencode (query)
        if type == 'private':
            auth = base64.b64encode (self.apiKey + ':' + self.secret)
            headers = { 'Authorization': 'Basic ' + auth }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class mercado (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'mercado',
            'name': 'Mercado Bitcoin',
            'countries': 'BR', # Brazil
            'rateLimit': 1000,
            'version': 'v3',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27837060-e7c58714-60ea-11e7-9192-f05e86adb83f.jpg',
                'api': {
                    'public': 'https://www.mercadobitcoin.net/api',
                    'private': 'https://www.mercadobitcoin.net/tapi',
                },
                'www': 'https://www.mercadobitcoin.com.br',
                'doc': [
                    'https://www.mercadobitcoin.com.br/api-doc',
                    'https://www.mercadobitcoin.com.br/trade-api',
                ],
            },
            'api': {
                'public': {
                    'get': [ # last slash critical
                        'orderbook/',
                        'orderbook_litecoin/',
                        'ticker/',
                        'ticker_litecoin/',
                        'trades/',
                        'trades_litecoin/',
                        'v2/ticker/',
                        'v2/ticker_litecoin/',
                    ],
                },
                'private': {
                    'post': [
                        'cancel_order',
                        'get_account_info',
                        'get_order',
                        'get_withdrawal',
                        'list_system_messages',
                        'list_orders',
                        'list_orderbook',
                        'place_buy_order',
                        'place_sell_order',
                        'withdraw_coin',
                    ],
                },
            },
            'products': {
                'BTC/BRL': { 'id': 'BRLBTC', 'symbol': 'BTC/BRL', 'base': 'BTC', 'quote': 'BRL', 'suffix': '' },
                'LTC/BRL': { 'id': 'BRLLTC', 'symbol': 'LTC/BRL', 'base': 'LTC', 'quote': 'BRL', 'suffix': 'Litecoin' },
            },
        }
        params.update (config)
        super (mercado, self).__init__ (params)

    def fetch_order_book (self, product):
        p = self.product (product)
        method = 'publicGetOrderbook' + self.capitalize (p['suffix'])
        orderbook = getattr (self, method) ()
        timestamp = self.milliseconds ()
        result = {
            'bids': orderbook['bids'],
            'asks': orderbook['asks'],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        return result

    def fetch_ticker (self, product):
        p = self.product (product)
        method = 'publicGetV2Ticker' + self.capitalize (p['suffix'])
        response = getattr (self, method) ()
        ticker = response['ticker']
        timestamp = int (ticker['date']) * 1000
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['buy']),
            'ask': float (ticker['sell']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['vol']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        p = self.product (product)
        method = 'publicGetTrades' + self.capitalize (p['suffix'])
        return getattr (self, method) ()

    def fetch_balance (self):
        return self.privatePostGetAccountInfo ()

    def create_order (self, product, type, side, amount, price = None, params = {}):
        if type == 'market':
            raise Exception (self.id + ' allows limit orders only')
        method = 'privatePostPlace' + self.capitalize (side) + 'Order'
        order = {
            'coin_pair': self.product_id (product),
            'quantity': amount,
            'limit_price': price,
        }
        return getattr (self, method) (self.extend (order, params))        

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'][type] + '/'
        if type == 'public':
            url += path
        else:
            url += self.version + '/'
            nonce = self.nonce ()
            body = _urlencode.urlencode (self.extend ({
                'tapi_method': path,
                'tapi_nonce': nonce,
            }, params))
            auth = '/tapi/' + self.version  + '/' + '?' + body
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'TAPI-ID': self.apiKey,
                'TAPI-MAC': self.hmac (auth, self.secret, hashlib.sha512),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class okcoin (Market):

    def __init__ (self, config = {}):
        params = {
            'version': 'v1',
            'rateLimit': 2000, # up to 3000 requests per 5 minutes ≈ 600 requests per minute ≈ 10 requests per second ≈ 100 ms
            'api': {
                'public': {
                    'get': [
                        'depth',
                        'exchange_rate',
                        'future_depth',
                        'future_estimated_price',
                        'future_hold_amount',
                        'future_index',
                        'future_kline',
                        'future_price_limit',
                        'future_ticker',
                        'future_trades',
                        'kline',
                        'otcs',
                        'ticker',
                        'trades',    
                    ],
                },
                'private': {
                    'post': [
                        'account_records',
                        'batch_trade',
                        'borrow_money',
                        'borrow_order_info',
                        'borrows_info',
                        'cancel_borrow',
                        'cancel_order',
                        'cancel_otc_order',
                        'cancel_withdraw',
                        'future_batch_trade',
                        'future_cancel',
                        'future_devolve',
                        'future_explosive',
                        'future_order_info',
                        'future_orders_info',
                        'future_position',
                        'future_position_4fix',
                        'future_trade',
                        'future_trades_history',
                        'future_userinfo',
                        'future_userinfo_4fix',
                        'lend_depth',
                        'order_fee',
                        'order_history',
                        'order_info',
                        'orders_info',
                        'otc_order_history',
                        'otc_order_info',
                        'repayment',
                        'submit_otc_order',
                        'trade',
                        'trade_history',
                        'trade_otc_order',
                        'withdraw',
                        'withdraw_info',
                        'unrepayments_info',
                        'userinfo',
                    ],
                },
            },
        }
        params.update (config)
        super (okcoin, self).__init__ (params)

    def fetch_order_book (self, product):
        orderbook = self.publicGetDepth ({
            'symbol': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        result = {
            'bids': orderbook['bids'],
            'asks': self.sort_by (orderbook['asks'], 0),
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        return result

    def fetch_ticker (self, product):
        response = self.publicGetTicker ({
            'symbol': self.product_id (product),
        })
        ticker = response['ticker']
        timestamp = int (response['date']) * 1000
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['buy']),
            'ask': float (ticker['sell']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['vol']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTrades ({
            'symbol': self.product_id (product),
        })

    def fetch_balance (self):
        return self.privatePostUserinfo ()

    def create_order (self, product, type, side, amount, price = None, params = {}):
        order = {
            'symbol': self.product_id (product),
            'type': side,
            'amount': amount,
        }
        if type == 'limit':
            order['price'] = price
        else:
            order['type'] += '_market'
        return self.privatePostTrade (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = '/api/' + self.version + '/' + path + '.do'   
        if type == 'public':
            if params:
                url += '?' + _urlencode.urlencode (params)
        else:
            query = self.keysort (self.extend ({
                'api_key': self.apiKey,
            }, params))
            # secret key must be at the end of query
            queryString = _urlencode.urlencode (query) + '&secret_key=' + self.secret
            query['sign'] = self.hash (queryString).upper ()
            body = _urlencode.urlencode (query)
            headers = { 'Content-type': 'application/x-www-form-urlencoded' }
        url = self.urls['api'] + url
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class okcoincny (okcoin):

    def __init__ (self, config = {}):
        params = {
            'id': 'okcoincny',
            'name': 'OKCoin CNY',
            'countries': 'CN',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766792-8be9157a-5ee5-11e7-926c-6d69b8d3378d.jpg',
                'api': 'https://www.okcoin.cn',
                'www': 'https://www.okcoin.cn',
                'doc': 'https://www.okcoin.cn/rest_getStarted.html',
            },
            'products': {
                'BTC/CNY': { 'id': 'btc_cny', 'symbol': 'BTC/CNY', 'base': 'BTC', 'quote': 'CNY' },
                'LTC/CNY': { 'id': 'ltc_cny', 'symbol': 'LTC/CNY', 'base': 'LTC', 'quote': 'CNY' },
            },
        }
        params.update (config)
        super (okcoincny, self).__init__ (params)

#------------------------------------------------------------------------------

class okcoinusd (okcoin):

    def __init__ (self, config = {}):
        params = {
            'id': 'okcoinusd',
            'name': 'OKCoin USD',
            'countries': [ 'CN', 'US' ],
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766791-89ffb502-5ee5-11e7-8a5b-c5950b68ac65.jpg',        
                'api': 'https://www.okcoin.com',
                'www': 'https://www.okcoin.com',
                'doc': [
                    'https://www.okcoin.com/rest_getStarted.html',
                    'https://www.npmjs.com/package/okcoin.com',
                ],
            },
            'products': {
                'BTC/USD': { 'id': 'btc_usd', 'symbol': 'BTC/USD', 'base': 'BTC', 'quote': 'USD' },
                'LTC/USD': { 'id': 'ltc_usd', 'symbol': 'LTC/USD', 'base': 'LTC', 'quote': 'USD' },
            },
        }
        params.update (config)
        super (okcoinusd, self).__init__ (params)

#------------------------------------------------------------------------------

class paymium (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'paymium',
            'name': 'Paymium',
            'countries': [ 'FR', 'EU', ],
            'rateLimit': 3000,
            'version': 'v1',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27790564-a945a9d4-5ff9-11e7-9d2d-b635763f2f24.jpg',
                'api': 'https://paymium.com/api',
                'www': 'https://www.paymium.com',
                'doc': [
                    'https://www.paymium.com/page/developers',
                    'https://github.com/Paymium/api-documentation',
                ],
            },
            'api': {
                'public': {
                    'get': [
                        'countries',
                        'data/{id}/ticker',
                        'data/{id}/trades',
                        'data/{id}/depth',
                        'bitcoin_charts/{id}/trades',
                        'bitcoin_charts/{id}/depth',
                    ],
                },
                'private': {
                    'get': [
                        'merchant/get_payment/{UUID}',
                        'user',
                        'user/addresses',
                        'user/addresses/{btc_address}',
                        'user/orders',
                        'user/orders/{UUID}',
                        'user/price_alerts',
                    ],
                    'post': [
                        'user/orders',
                        'user/addresses',
                        'user/payment_requests',
                        'user/price_alerts',
                        'merchant/create_payment',
                    ],
                    'delete': [
                        'user/orders/{UUID}/cancel',
                        'user/price_alerts/{id}',
                    ],
                },
            },
            'products': {
                'BTC/EUR': { 'id': 'eur', 'symbol': 'BTC/EUR', 'base': 'BTC', 'quote': 'EUR' },
            },
        }
        params.update (config)
        super (paymium, self).__init__ (params)

    def fetch_balance (self):
        return self.privateGetUser ()

    def fetch_order_book (self, product):
        orderbook = self.publicGetDataIdDepth  ({
            'id': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = [ 'bids', 'asks' ]
        for s in range (0, len (sides)):
            side = sides[s]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = order['price']
                amount = order['amount']
                timestamp = order['timestamp'] * 1000
                result[side].append ([ price, amount, timestamp ])
        result['bids'] = self.sort_by (result['bids'], 0, True)
        return result

    def fetch_ticker (self, product):
        ticker = self.publicGetDataIdTicker ({
            'id': self.product_id (product),
        })
        timestamp = ticker['at'] * 1000
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': float (ticker['vwap']),
            'open': float (ticker['open']),
            'close': None,
            'first': None,
            'last': float (ticker['price']),
            'change': None,
            'percentage': float (ticker['variation']),
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetDataIdTrades ({
            'id': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        order = {
            'type': self.capitalize (type) + 'Order',
            'currency': self.product_id (product),
            'direction': side,
            'amount': amount,
        }
        if type == 'market':
            order['price'] = price
        return self.privatePostUserOrders (self.extend (order, params))

    def cancel_order (self, id, params = {}):
        return self.privatePostCancelOrder (self.extend ({
            'orderNumber': id,
        }, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.version + '/' + self.implode_params (path, params)
        query = self.omit (params, self.extract_params (path))
        if type == 'public':
            if query:
                url += '?' + _urlencode.urlencode (query)
        else:
            body = json.dumps (params)
            nonce = str (self.nonce ())            
            auth = nonce + url + body
            headers = {
                'Api-Key': self.apiKey,
                'Api-Signature': self.hmac (auth, self.secret),
                'Api-Nonce': nonce,                
                'Content-Type': 'application/json',
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class poloniex (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'poloniex',
            'name': 'Poloniex',
            'countries': 'US',
            'rateLimit': 1000, # 6 calls per second
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766817-e9456312-5ee6-11e7-9b3c-b628ca5626a5.jpg',
                'api': {
                    'public': 'https://poloniex.com/public',
                    'private': 'https://poloniex.com/tradingApi',
                },
                'www': 'https://poloniex.com',
                'doc': [
                    'https://poloniex.com/support/api/',
                    'http://pastebin.com/dMX7mZE0',
                ],
            },
            'api': {
                'public': {
                    'get': [
                        'return24hVolume',
                        'returnChartData',
                        'returnCurrencies',
                        'returnLoanOrders',
                        'returnOrderBook',
                        'returnTicker',
                        'returnTradeHistory',
                    ],
                },
                'private': {
                    'post': [
                        'buy',
                        'cancelLoanOffer',
                        'cancelOrder',
                        'closeMarginPosition',
                        'createLoanOffer',
                        'generateNewAddress',
                        'getMarginPosition',
                        'marginBuy',
                        'marginSell',
                        'moveOrder',
                        'returnActiveLoans',
                        'returnAvailableAccountBalances',
                        'returnBalances',
                        'returnCompleteBalances',
                        'returnDepositAddresses',
                        'returnDepositsWithdrawals',
                        'returnFeeInfo',
                        'returnLendingHistory',
                        'returnMarginAccountSummary',
                        'returnOpenLoanOffers',
                        'returnOpenOrders',
                        'returnOrderTrades',
                        'returnTradableBalances',
                        'returnTradeHistory',
                        'sell',
                        'toggleAutoRenew',
                        'transferBalance',
                        'withdraw',
                    ],
                },
            },
        }
        params.update (config)
        super (poloniex, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetReturnTicker ()
        keys = list (products.keys ())
        result = []
        for p in range (0, len (keys)):
            id = keys[p]
            product = products[id]
            symbol = id.replace ('_', '/')
            quote, base = symbol.split ('/')
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.privatePostReturnCompleteBalances ({
            'account': 'all',
        })

    def fetch_order_book (self, product):
        orderbook = self.publicGetReturnOrderBook ({
            'currencyPair': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = [ 'bids', 'asks' ]
        for s in range (0, len (sides)):
            side = sides[s]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = float (order[0])
                amount = float (order[1])
                result[side].append ([ price, amount ])
        return result

    def fetch_ticker (self, product):
        p = self.product (product)
        tickers = self.publicGetReturnTicker ()
        ticker = tickers[p['id']]
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high24hr']),
            'low': float (ticker['low24hr']),
            'bid': float (ticker['highestBid']),
            'ask': float (ticker['lowestAsk']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': None,
            'change': float (ticker['percentChange']),
            'percentage': None,
            'average': None,
            'baseVolume': float (ticker['baseVolume']),
            'quoteVolume': float (ticker['quoteVolume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetReturnTradeHistory ({
            'currencyPair': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        method = 'privatePost' + self.capitalize (side)
        return getattr (self, method) (self.extend ({
            'currencyPair': self.product_id (product),
            'rate': price,
            'amount': amount,
        }, params))

    def cancel_order (self, id, params = {}):
        return self.privatePostCancelOrder (self.extend ({
            'orderNumber': id,
        }, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'][type]
        query = self.extend ({ 'command': path }, params)
        if type == 'public':
            url += '?' + _urlencode.urlencode (query)
        else:
            query['nonce'] = self.nonce ()
            body = _urlencode.urlencode (query)
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Key': self.apiKey,
                'Sign': self.hmac (body, self.secret, hashlib.sha512),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class quadrigacx (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'quadrigacx',
            'name': 'QuadrigaCX',
            'countries': 'CA',
            'rateLimit': 2000,
            'version': 'v2',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766825-98a6d0de-5ee7-11e7-9fa4-38e11a2c6f52.jpg',
                'api': 'https://api.quadrigacx.com',
                'www': 'https://www.quadrigacx.com',
                'doc': 'https://www.quadrigacx.com/api_info',
            },
            'api': {
                'public': {
                    'get': [
                        'order_book',
                        'ticker',                
                        'transactions',
                    ],
                },
                'private': {
                    'post': [
                        'balance',
                        'bitcoin_deposit_address',
                        'bitcoin_withdrawal',
                        'buy',
                        'cancel_order',
                        'ether_deposit_address',
                        'ether_withdrawal',
                        'lookup_order',
                        'open_orders',
                        'sell',
                        'user_transactions',
                    ],
                },
            },
            'products': {
                'BTC/CAD': { 'id': 'btc_cad', 'symbol': 'BTC/CAD', 'base': 'BTC', 'quote': 'CAD' },
                'BTC/USD': { 'id': 'btc_usd', 'symbol': 'BTC/USD', 'base': 'BTC', 'quote': 'USD' },
                'ETH/BTC': { 'id': 'eth_btc', 'symbol': 'ETH/BTC', 'base': 'ETH', 'quote': 'BTC' },
                'ETH/CAD': { 'id': 'eth_cad', 'symbol': 'ETH/CAD', 'base': 'ETH', 'quote': 'CAD' },
            },
        }
        params.update (config)
        super (quadrigacx, self).__init__ (params)

    def fetch_balance (self):
        return self.privatePostBalance ()

    def fetch_order_book (self, product):
        orderbook = self.publicGetOrderBook ({
            'book': self.product_id (product),
        })
        timestamp = int (orderbook['timestamp']) * 1000
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = [ 'bids', 'asks' ]
        for s in range (0, len (sides)):
            side = sides[s]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = float (order[0])
                amount = float (order[1])
                result[side].append ([ price, amount ])
        return result

    def fetch_ticker (self, product):
        ticker = self.publicGetTicker ({
            'book': self.product_id (product),
        })
        timestamp = int (ticker['timestamp']) * 1000
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': float (ticker['vwap']),
            'open': None,
            'close': None,
            'first': None,
            'last': None,
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTransactions ({
            'book': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        method = 'privatePost' + self.capitalize (side) 
        order = {
            'amount': amount,
            'book': self.product_id (product),
        }
        if type == 'limit':
            order['price'] = price
        return getattr (self, method) (self.extend (order, params))

    def cancel_order (self, id, params = {}):
        return self.privatePostCancelOrder (self.extend ({ id }, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.version + '/' + path
        if type == 'public':
            url += '?' + _urlencode.urlencode (params)
        else:
            nonce = self.nonce ()
            request = ''.join ([ nonce, self.uid, self.apiKey ])
            signature = self.hmac (request, self.secret)
            query = self.extend ({ 
                'key': self.apiKey,
                'nonce': nonce,
                'signature': signature,
            }, params)
            body = json.dumps (query)
            headers = {
                'Content-Type': 'application/json',
                'Content-Length': len (body),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class quoine (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'quoine',
            'name': 'QUOINE',
            'countries': [ 'JP', 'SG', 'VN' ],
            'version': '2',
            'rateLimit': 2000,
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766844-9615a4e8-5ee8-11e7-8814-fcd004db8cdd.jpg',
                'api': 'https://api.quoine.com',
                'www': 'https://www.quoine.com',
                'doc': 'https://developers.quoine.com',
            },
            'api': {
                'public': {
                    'get': [
                        'products',
                        'products/{id}',
                        'products/{id}/price_levels',
                        'executions',
                        'ir_ladders/{currency}',
                    ],
                },
                'private': {
                    'get': [
                        'accounts/balance',
                        'crypto_accounts',
                        'executions/me',
                        'fiat_accounts',
                        'loan_bids',
                        'loans',
                        'orders',
                        'orders/{id}',
                        'orders/{id}/trades',
                        'trades',
                        'trades/{id}/loans',
                        'trading_accounts',
                        'trading_accounts/{id}',
                    ],
                    'post': [
                        'fiat_accounts',
                        'loan_bids',
                        'orders',
                    ],
                    'put': [
                        'loan_bids/{id}/close',
                        'loans/{id}',
                        'orders/{id}',
                        'orders/{id}/cancel',
                        'trades/{id}',
                        'trades/{id}/close',
                        'trades/close_all',
                        'trading_accounts/{id}',
                    ],
                },
            },
        }
        params.update (config)
        super (quoine, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetProducts ()
        result = []
        for p in range (0, len (products)):
            product = products[p]
            id = product['id']
            base = product['base_currency']
            quote = product['quoted_currency']
            symbol = base + '/' + quote
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.privateGetAccountsBalance ()

    def fetch_order_book (self, product):
        orderbook = self.publicGetProductsIdPriceLevels ({
            'id': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = { 'bids': 'buy_price_levels', 'asks': 'sell_price_levels' }
        keys = list (sides.keys ())
        for k in range (0, len (keys)):
            key = keys[k]
            side = sides[key]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = float (order[0])
                amount = float (order[1])
                result[key].append ([ price, amount ])
        return result

    def fetch_ticker (self, product):
        ticker = self.publicGetProductsId ({
            'id': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high_market_ask']),
            'low': float (ticker['low_market_bid']),
            'bid': float (ticker['market_bid']),
            'ask': float (ticker['market_ask']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last_traded_price']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': float (ticker['volume_24h']),
            'quoteVolume': None,
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetExecutions ({
            'product_id': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        order = {
            'order_type': type,
            'product_id': self.product_id (product),
            'side': side,
            'quantity': amount,
        }
        if type == 'limit':
            order['price'] = price
        return self.privatePostOrders (self.extend ({
            'order': order,
        }, params))

    def cancel_order (self, id, params = {}):
        return self.privatePutOrdersIdCancel (self.extend ({
            'id': id,
        }, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = '/' + self.implode_params (path, params)
        query = self.omit (params, self.extract_params (path))
        headers = {
            'X-Quoine-API-Version': self.version,
            'Content-type': 'application/json',
        }
        if type == 'public':
            if query:
                url += '?' + _urlencode.urlencode (query)
        else:
            nonce = self.nonce ()
            request = {
                'path': url, 
                'nonce': nonce, 
                'token_id': self.apiKey,
                'iat': int (math.floor (nonce / 1000)), # issued at
            }
            if query:
                body = json.dumps (query)
            headers['X-Quoine-Auth'] = self.jwt (request, self.secret)
        return self.fetch (self.urls['api'] + url, method, headers, body)

#------------------------------------------------------------------------------

class southxchange (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'southxchange',
            'name': 'SouthXchange',
            'countries': 'AR', # Argentina
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27838912-4f94ec8a-60f6-11e7-9e5d-bbf9bd50a559.jpg',
                'api': 'https://www.southxchange.com/api',
                'www': 'https://www.southxchange.com',
                'doc': 'https://www.southxchange.com/Home/Api',
            },
            'api': {
                'public': {
                    'get': [
                        'markets',
                        'price/{symbol}',
                        'prices',
                        'book/{symbol}',
                        'trades/{symbol}',
                    ],
                },
                'private': {
                    'post': [
                        'cancelMarketOrders',
                        'cancelOrder',
                        'generatenewaddress',
                        'listOrders',
                        'listBalances',
                        'placeOrder',
                        'withdraw',
                    ],
                },
            },
        }
        params.update (config)
        super (southxchange, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetMarkets ()
        result = []
        for p in range (0, len (products)):
            product = products[p]
            base = product[0]
            quote = product[1]
            symbol = base + '/' + quote
            id = symbol
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.privatePostListBalances ()

    def fetch_order_book (self, product):
        orderbook = self.publicGetBookSymbol ({
            'symbol': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = { 'bids': 'BuyOrders', 'asks': 'SellOrders' }
        keys = list (sides.keys ())
        for k in range (0, len (keys)):
            key = keys[k]
            side = sides[key]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = float (order['Price'])
                amount = float (order['Amount'])
                result[key].append ([ price, amount ])
        return result

    def fetch_ticker (self, product):
        ticker = self.publicGetPriceSymbol ({
            'symbol': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': None,
            'low': None,
            'bid': float (ticker['Bid']),
            'ask': float (ticker['Ask']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['Last']),
            'change': float (ticker['Variation24Hr']),
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['Volume24Hr']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTradesSymbol ({
            'symbol': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        p = self.product (product)
        order = {
            'listingCurrency': p['base'],
            'referenceCurrency': p['quote'],
            'type': side,
            'amount': amount,
        }
        if type == 'limit':
            order['limitPrice'] = price
        return self.privatePostPlaceOrder (self.extend (order, params))

    def cancel_order (self, id, params = {}):
        return self.privatePostCancelOrder (self.extend ({
            'orderCode': id,
        }, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.implode_params (path, params)
        query = self.omit (params, self.extract_params (path))
        if type == 'private':
            nonce = self.nonce ()
            query = self.extend ({
                'key': self.apiKey,
                'nonce': nonce,
            }, query)
            body = json.dumps (query)
            headers = {
                'Content-Type': 'application/json',
                'Hash': self.hmac (body, self.secret, hashlib.sha512),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class surbitcoin (blinktrade):

    def __init__ (self, config = {}):
        params = {
            'id': 'surbitcoin',
            'name': 'SurBitcoin',
            'countries': 'VE',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27991511-f0a50194-6481-11e7-99b5-8f02932424cc.jpg',
                'api': {
                    'public': 'https://api.blinktrade.com/api',
                    'private': 'https://api.blinktrade.com/tapi',
                },
                'www': 'https://surbitcoin.com',
                'doc': 'https://blinktrade.com/docs',
            },
            'comment': 'Blinktrade API',
            'products': {
                'BTC/VEF': { 'id': 'BTCVEF', 'symbol': 'BTC/VEF', 'base': 'BTC', 'quote': 'VEF', 'brokerId': 1, 'broker': 'SurBitcoin', },
            },
        }
        params.update (config)
        super (surbitcoin, self).__init__ (params)

#------------------------------------------------------------------------------

class therock (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'therock',
            'name': 'TheRockTrading',
            'countries': 'MT',
            'rateLimit': 1000,
            'version': 'v1',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766869-75057fa2-5ee9-11e7-9a6f-13e641fa4707.jpg',
                'api': 'https://api.therocktrading.com',
                'www': 'https://therocktrading.com',
                'doc': 'https://api.therocktrading.com/doc/',
            },
            'api': {
                'public': {
                    'get': [
                        'funds/{id}/orderbook',
                        'funds/{id}/ticker',
                        'funds/{id}/trades',
                        'funds/tickers',
                    ],
                },
                'private': {
                    'get': [
                        'balances',
                        'balances/{id}',
                        'discounts',
                        'discounts/{id}',
                        'funds',
                        'funds/{id}',
                        'funds/{id}/trades',
                        'funds/{fund_id}/orders',
                        'funds/{fund_id}/orders/{id}',                
                        'funds/{fund_id}/position_balances',
                        'funds/{fund_id}/positions',
                        'funds/{fund_id}/positions/{id}',
                        'transactions',
                        'transactions/{id}',
                        'withdraw_limits/{id}',
                        'withdraw_limits',
                    ],
                    'post': [
                        'atms/withdraw',
                        'funds/{fund_id}/orders',
                    ],
                    'delete': [
                        'funds/{fund_id}/orders/{id}',
                        'funds/{fund_id}/orders/remove_all',
                    ],
                },
            },
        }
        params.update (config)
        super (therock, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetFundsTickers ()
        result = []
        for p in range (0, len (products['tickers'])):
            product = products['tickers'][p]
            id = product['fund_id']
            base = id[0:3]
            quote = id[3:6]
            symbol = base + '/' + quote
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.privateGetBalances ()

    def fetch_order_book (self, product):
        orderbook = self.publicGetFundsIdOrderbook ({
            'id': self.product_id (product),
        })
        timestamp = self.parse8601 (orderbook['date'])
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = [ 'bids', 'asks' ]
        for s in range (0, len (sides)):
            side = sides[s]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = float (order['price'])
                amount = float (order['amount'])
                result[side].append ([ price, amount ])
        return result

    def fetch_ticker (self, product):
        ticker = self.publicGetFundsIdTicker ({
            'id': self.product_id (product),
        })
        timestamp = self.parse8601 (ticker['date'])
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': None,
            'open': float (ticker['open']),
            'close': float (ticker['close']),
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': float (ticker['volume_traded']),
            'quoteVolume': float (ticker['volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetFundsIdTrades ({
            'id': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        if type == 'market':
            raise Exception (self.id + ' allows limit orders only')
        return self.privatePostFundsFundIdOrders (self.extend ({
            'fund_id': self.product_id (product),
            'side': side,
            'amount': amount,
            'price': price,
        }, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.version + '/' + self.implode_params (path, params)
        query = self.omit (params, self.extract_params (path))
        if type == 'private':
            nonce = str (self.nonce ())
            headers = {
                'X-TRT-KEY': self.apiKey,
                'X-TRT-NONCE': nonce,
                'X-TRT-SIGN': self.hmac (nonce + url, self.secret, hashlib.sha512),
            }
            if query:
                body = json.dumps (query)
                headers['Content-Type'] = 'application/json'
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class urdubit (blinktrade):

    def __init__ (self, config = {}):
        params = {
            'id': 'urdubit',
            'name': 'UrduBit',
            'countries': 'PK',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27991453-156bf3ae-6480-11e7-82eb-7295fe1b5bb4.jpg',
                'api': {
                    'public': 'https://api.blinktrade.com/api',
                    'private': 'https://api.blinktrade.com/tapi',
                },
                'www': 'https://urdubit.com',
                'doc': 'https://blinktrade.com/docs',
            },
            'comment': 'Blinktrade API',
            'products': {
                'BTC/PKR': { 'id': 'BTCPKR', 'symbol': 'BTC/PKR', 'base': 'BTC', 'quote': 'PKR', 'brokerId': 8, 'broker': 'UrduBit', },
            },
        }
        params.update (config)
        super (urdubit, self).__init__ (params)

#------------------------------------------------------------------------------

class vaultoro (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'vaultoro',
            'name': 'Vaultoro',
            'countries': 'CH',
            'rateLimit': 1000,
            'version': '1',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766880-f205e870-5ee9-11e7-8fe2-0d5b15880752.jpg',
                'api': 'https://api.vaultoro.com',
                'www': 'https://www.vaultoro.com',
                'doc': 'https://api.vaultoro.com',
            },
            'api': {
                'public': {
                    'get': [
                        'bidandask',
                        'buyorders',
                        'latest',
                        'latesttrades',
                        'markets',
                        'orderbook',
                        'sellorders',
                        'transactions/day',
                        'transactions/hour',
                        'transactions/month',
                    ],
                },
                'private': {
                    'get': [
                        'balance',
                        'mytrades',
                        'orders',
                    ],
                    'post': [
                        'buy/{symbol}/{type}',
                        'cancel/{orderid',
                        'sell/{symbol}/{type}',
                        'withdraw',
                    ],
                },
            },
        }
        params.update (config)
        super (vaultoro, self).__init__ (params)

    def fetch_products (self):
        result = []
        products = self.publicGetMarkets ()
        product = products['data']
        base = product['BaseCurrency']
        quote = product['MarketCurrency']
        symbol = base + '/' + quote
        baseId = base
        quoteId = quote
        id = product['MarketName']
        result.append ({
            'id': id,
            'symbol': symbol,
            'base': base,
            'quote': quote,
            'baseId': baseId,
            'quoteId': quoteId,
            'info': product,
        })
        return result

    def fetch_balance (self):
        return self.privateGetBalance ()

    def fetch_order_book (self, product):
        response = self.publicGetOrderbook ()
        orderbook = {
            'bids': response['data'][0]['b'],
            'asks': response['data'][1]['s'],
        }
        timestamp = self.milliseconds ()
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = [ 'bids', 'asks' ]
        for s in range (0, len (sides)):
            side = sides[s]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = order['Gold_Price']
                amount = order['Gold_Amount']
                result[side].append ([ price, amount ])
        result['bids'] = self.sort_by (result['bids'], 0, True)
        return result

    def fetch_ticker (self, product):
        quote = self.publicGetBidandask ()
        bidsLength = len (quote['bids'])
        bid = quote['bids'][bidsLength - 1]
        ask = quote['asks'][0]
        response = self.publicGetMarkets ()
        ticker = response['data']
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['24hHigh']),
            'low': float (ticker['24hLow']),
            'bid': bid[0],
            'ask': ask[0],
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['LastPrice']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['24hVolume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTransactionsDay ()

    def create_order (self, product, type, side, amount, price = None, params = {}):
        p = self.product (product)
        method = 'privatePost' + self.capitalize (side) + 'SymbolType'
        return getattr (self, method) (self.extend ({
            'symbol': p['quoteId'].lower (),
            'type': type,
            'gld': amount,
            'price': price or 1,
        }, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/'
        if type == 'public':
            url += path
        else:
            nonce = self.nonce ()
            url += self.version + '/' + self.implode_params (path, params)
            query = self.extend ({
                'nonce': nonce,
                'apikey': self.apiKey,
            }, self.omit (params, self.extract_params (path)))
            url += '?' + _urlencode.urlencode (query)
            headers = {
                'Content-Type': 'application/json',
                'X-Signature': self.hmac (url, self.secret)
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class vbtc (blinktrade):

    def __init__ (self, config = {}):
        params = {
            'id': 'vbtc',
            'name': 'VBTC',
            'countries': 'VN',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27991481-1f53d1d8-6481-11e7-884e-21d17e7939db.jpg',
                'api': {
                    'public': 'https://api.blinktrade.com/api',
                    'private': 'https://api.blinktrade.com/tapi',
                },
                'www': 'https://vbtc.exchange',
                'doc': 'https://blinktrade.com/docs',
            },
            'comment': 'Blinktrade API',
            'products': {
                'BTC/VND': { 'id': 'BTCVND', 'symbol': 'BTC/VND', 'base': 'BTC', 'quote': 'VND', 'brokerId': 3, 'broker': 'VBTC', },
            },
        }
        params.update (config)
        super (vbtc, self).__init__ (params)

#------------------------------------------------------------------------------

class virwox (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'virwox',
            'name': 'VirWoX',
            'countries': 'AT',
            'rateLimit': 1000,
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766894-6da9d360-5eea-11e7-90aa-41f2711b7405.jpg',
                'api': {
                    'public': 'http://api.virwox.com/api/json.php',
                    'private': 'https://www.virwox.com/api/trading.php',
                },
                'www': 'https://www.virwox.com',
                'doc': 'https://www.virwox.com/developers.php',
            },
            'api': {
                'public': {
                    'get': [
                        'getInstruments',
                        'getBestPrices',
                        'getMarketDepth',
                        'estimateMarketOrder',
                        'getTradedPriceVolume',
                        'getRawTradeData',
                        'getStatistics',
                        'getTerminalList',
                        'getGridList',
                        'getGridStatistics',
                    ],
                    'post': [
                        'getInstruments',
                        'getBestPrices',
                        'getMarketDepth',
                        'estimateMarketOrder',
                        'getTradedPriceVolume',
                        'getRawTradeData',
                        'getStatistics',
                        'getTerminalList',
                        'getGridList',
                        'getGridStatistics',
                    ],
                },
                'private': {
                    'get': [
                        'cancelOrder',
                        'getBalances',
                        'getCommissionDiscount',
                        'getOrders',
                        'getTransactions',
                        'placeOrder',
                    ],
                    'post': [
                        'cancelOrder',
                        'getBalances',
                        'getCommissionDiscount',
                        'getOrders',
                        'getTransactions',
                        'placeOrder',
                    ],
                },
            },
        }
        params.update (config)
        super (virwox, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetInstruments ()
        keys = list (products['result'].keys ())
        result = []
        for p in range (0, len (keys)):
            product = products['result'][keys[p]]
            id = product['instrumentID']
            symbol = product['symbol']
            base = product['longCurrency']
            quote = product['shortCurrency']
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.privatePostGetBalances ()

    def fetchBestPrices (self, product):
        return self.publicPostGetBestPrices ({
            'symbols': [ self.symbol (product) ],
        })

    def fetch_order_book (self, product):
        response = self.publicPostGetMarketDepth ({
            'symbols': [ self.symbol (product) ],
            'buyDepth': 100,
            'sellDepth': 100,
        })
        orderbook = response['result'][0]
        timestamp = self.milliseconds ()
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        sides = { 'bids': 'buy', 'asks': 'sell' }
        keys = list (sides.keys ())
        for k in range (0, len (keys)):
            key = keys[k]
            side = sides[key]
            orders = orderbook[side]
            for i in range (0, len (orders)):
                order = orders[i]
                price = float (order['price'])
                amount = float (order['volume'])
                result[key].append ([ price, amount ])
        return result

    def fetch_ticker (self, product):
        end = self.milliseconds ()
        start = end - 86400000
        response = self.publicGetTradedPriceVolume ({
            'instrument': self.symbol (product),
            'endDate': self.yyyymmddhhmmss (end),
            'startDate': self.yyyymmddhhmmss (start),
            'HLOC': 1,
        })
        tickers = response['result']['priceVolumeList']
        keys = list (tickers.keys ())
        length = len (keys)
        lastKey = keys[length - 1]
        ticker = tickers[lastKey]
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': None,
            'ask': None,
            'vwap': None,
            'open': float (ticker['open']),
            'close': float (ticker['close']),
            'first': None,
            'last': None,
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': float (ticker['longVolume']),
            'quoteVolume': float (ticker['shortVolume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetRawTradeData ({
            'instrument': self.symbol (product),
            'timespan': 3600,
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        order = {
            'instrument': self.symbol (product),
            'orderType': side.upper (),
            'amount': amount,
        }
        if type == 'limit':
            order['price'] = price
        return self.privatePostPlaceOrder (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'][type]
        auth = {}
        if type == 'public':
            auth['key'] = self.apiKey
            auth['user'] = self.login
            auth['pass'] = self.password
        nonce = self.nonce ()
        if method == 'GET':
            url += '?' + _urlencode.urlencode (self.extend ({ 
                'method': path, 
                'id': nonce,
            }, auth, params))
        else:
            headers = { 'Content-type': 'application/json' }
            body = json.dumps ({ 
                'method': path, 
                'params': self.extend (auth, params),
                'id': nonce,
            })
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class yobit (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'yobit',
            'name': 'YoBit',
            'countries': 'RU',
            'rateLimit': 2000, # responses are cached every 2 seconds
            'version': '3',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766910-cdcbfdae-5eea-11e7-9859-03fea873272d.jpg',
                'api': 'https://yobit.net',
                'www': 'https://www.yobit.net',
                'doc': 'https://www.yobit.net/en/api/',
            },
            'api': {
                'api': {
                    'get': [
                        'depth/{pairs}',
                        'info',
                        'ticker/{pairs}',
                        'trades/{pairs}',
                    ],
                },
                'tapi': {
                    'post': [
                        'ActiveOrders',
                        'CancelOrder',
                        'GetDepositAddress',
                        'getInfo',
                        'OrderInfo',
                        'Trade',                
                        'TradeHistory',
                        'WithdrawCoinsToAddress',
                    ],
                },
            },
        }
        params.update (config)
        super (yobit, self).__init__ (params)

    def fetch_products (self):
        products = self.apiGetInfo ()
        keys = list (products['pairs'].keys ())
        result = []
        for p in range (0, len (keys)):
            id = keys[p]
            product = products['pairs'][id]
            symbol = id.upper ().replace ('_', '/')
            base, quote = symbol.split ('/')
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.tapiPostGetInfo ()

    def fetch_order_book (self, product):
        p = self.product (product)
        response = self.apiGetDepthPairs ({
            'pairs': p['id'],
        })
        orderbook = response[p['id']]
        timestamp = self.milliseconds ()
        result = {
            'bids': orderbook['bids'],
            'asks': orderbook['asks'],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        return result

    def fetch_ticker (self, product):
        p = self.product (product)
        tickers = self.apiGetTickerPairs ({
            'pairs': p['id'],
        })
        ticker = tickers[p['id']]
        timestamp = ticker['updated'] * 1000
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['buy']),
            'ask': float (ticker['sell']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': float (ticker['avg']),
            'baseVolume': float (ticker['vol_cur']),
            'quoteVolume': float (ticker['vol']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.apiGetTradesPairs ({
            'pairs': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        if type == 'market':
            raise Exception (self.id + ' allows limit orders only')
        return self.tapiPostTrade (self.extend ({
            'pair': self.product_id (product),
            'type': side,
            'amount': amount,
            'rate': price,
        }, params))

    def cancel_order (self, id, params = {}):
        return self.tapiPostCancelOrder (self.extend ({
            'order_id': id,
        }, params))

    def request (self, path, type = 'api', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + type
        if type == 'api':
            url += '/' + self.version + '/' + self.implode_params (path, params)
            query = self.omit (params, self.extract_params (path))
            if query:
                url += '?' + _urlencode.urlencode (query)
        else:
            nonce = self.nonce ()
            query = self.extend ({ 'method': path, 'nonce': nonce }, params)
            body = _urlencode.urlencode (query)
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'key': self.apiKey,
                'sign': self.hmac (body, self.secret, hashlib.sha512),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class zaif (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'zaif',
            'name': 'Zaif',
            'countries': 'JP',
            'rateLimit': 3000,
            'version': '1',
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766927-39ca2ada-5eeb-11e7-972f-1b4199518ca6.jpg',
                'api': 'https://api.zaif.jp',
                'www': 'https://zaif.jp',
                'doc': [
                    'https://corp.zaif.jp/api-docs',
                    'https://corp.zaif.jp/api-docs/api_links',
                    'https://www.npmjs.com/package/zaif.jp',
                    'https://github.com/you21979/node-zaif',
                ],
            },
            'api': {
                'api': {
                    'get': [
                        'depth/{pair}',
                        'currencies/{pair}',
                        'currencies/all',
                        'currency_pairs/{pair}',
                        'currency_pairs/all',
                        'last_price/{pair}',
                        'ticker/{pair}',
                        'trades/{pair}',
                    ],
                },
                'tapi': {
                    'post': [
                        'active_orders',
                        'cancel_order',
                        'deposit_history',
                        'get_id_info',
                        'get_info',
                        'get_info2',
                        'get_personal_info',
                        'trade',
                        'trade_history',
                        'withdraw',
                        'withdraw_history',
                    ],
                },
                'ecapi': {
                    'post': [
                        'createInvoice',
                        'getInvoice',
                        'getInvoiceIdsByOrderNumber',
                        'cancelInvoice',
                    ],
                },
            },
        }
        params.update (config)
        super (zaif, self).__init__ (params)

    def fetch_products (self):
        products = self.apiGetCurrencyPairsAll ()
        result = []
        for p in range (0, len (products)):
            product = products[p]
            id = product['currency_pair']
            symbol = product['name']
            base, quote = symbol.split ('/')
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.tapiPostGetInfo ()

    def fetch_order_book (self, product):
        orderbook = self.apiGetDepth  ({
            'pair': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        result = {
            'bids': orderbook['bids'],
            'asks': orderbook['asks'],
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
        }
        return result

    def fetch_ticker (self, product):
        ticker = self.apiGetTickerPair ({
            'pair': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': float (ticker['vwap']),
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.apiGetTradesPair ({
            'pair': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        if type == 'market':
            raise Exception (self.id + ' allows limit orders only')
        return self.tapiPostTrade (self.extend ({
            'currency_pair': self.product_id (product),
            'action': 'bid' if (side == 'buy') else 'ask',
            'amount': amount,
            'price': price,
        }, params))

    def cancel_order (self, id, params = {}):
        return self.tapiPostCancelOrder (self.extend ({
            'order_id': id,
        }, params))

    def request (self, path, type = 'api', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + type
        if type == 'api':
            url += '/' + self.version + '/' + self.implode_params (path, params)
        else:
            nonce = self.nonce ()
            body = _urlencode.urlencode (self.extend ({
                'method': path,
                'nonce': nonce,
            }, params))
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': len (body),
                'Key': self.apiKey,
                'Sign': self.hmac (body, self.secret, hashlib.sha512),
            }
        return self.fetch (url, method, headers, body)
