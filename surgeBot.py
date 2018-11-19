from apiCalls import apiCalls
import datetime
import time
import requests
import json
'''
This program capitalizes on cryptocurrentcy surges and pumps by trading
coins that have quickly risen in price. Uses Bittrex and CoinMarketCap api
for data and trade execution.
'''
class surgeBot: 
	TIME_PERIOD = 3600 # 1 hour
	ACTION_THRESHOLD = 5 # percent
	BAD_COINS = ['BTC'] # coins that are delisted, dne, or are generally untradeable
	MIN_MARKET_CAP = 10000000
	MIN_USD_VOLUME = 5000000
	MIN_BTC_VOLUME = 300
	
	'''
	* Searches through list of all cryptocurrencies on Bittrex and selects the one with the largest
	* percent gain in a specified time period.
	* @return  name of chosen cryptocurrency 
	'''
	def surgeSearch(self):
		chosenCoin = ''
		chosenCoinIncrease = -100
		api = apiCalls()
		# get list of all cryptos from Bittrex
		cryptoList = api.getJSONFromURL('https://bittrex.com/api/v1.1/public/getcurrencies', {})
		if (not cryptoList):
			print("BITTREX ISSUE")
			self.main()
		for coin in cryptoList['result']:
			if (coin['IsActive'] and coin['Currency'] not in self.BAD_COINS):
				coinName = coin['CurrencyLong']
				coinSymbol = coin['Currency']
				ticker = 'BTC-' + coinSymbol
				coinInfo = self.coinMarketCapCall(coinName)
				if (coinInfo[2] < self.MIN_MARKET_CAP):
					self.BAD_COINS.append(coinSymbol)
				elif (coinInfo[0] > chosenCoinIncrease):
					chosenCoin = ticker
					chosenCoinIncrease = coinInfo[0]
			time.sleep(7) # prevent rate limiting
		return chosenCoin

	'''
	* Gets information about an individual cryptocurrency from coinmarketcap
	* @param coin  cryptocurrency name
	* @return      array of information for individual cryptocurrency
	*			   if no info available, return array of zeros
	'''
	def coinMarketCapCall(self, coin):
		try:
			url = "https://api.coinmarketcap.com/v1/ticker/" + coin
			response = requests.get(url, {})
			result = response.json()
			change = float(result[0]['percent_change_1h'])
			price = float(result[0]['price_usd'])
			marketCap = float(result[0]['market_cap_usd'])
			return [change, price, marketCap]
		except:
			return [0,0,0]
	
	'''
	* Purchases cryptocurrency from Bittrex and logs purchase info
	* @param coin  chosen cryptocurrency
	* @return      array of information from purchase [coin ticker, purchased price, purchase time]
	'''
	def buy(self, ticker):
		if (ticker == ""):
			print("...invalid ticker...")
			self.main()
		print("initiating buy (" + ticker + ")")
		buyInfo = [0, 0, 0, 0, 0]
		api = apiCalls()
		coinInfo = api.getJSONFromURL('https://bittrex.com/api/v1.1/public/getmarketsummary', {"market" : ticker})
		if (not coinInfo):
			return buyInfo
		volume = coinInfo['result'][0]['Volume']
		if (volume > self.MIN_BTC_VOLUME):
			buyInfo = api.buy()
			self.log("buy", buyInfo['orderTime'], buyInfo['executedPrice'], buyInfo['amount'])
			print("buy succeeded")
		elif (volume < 50):
			print("buy failed")
			self.BAD_COINS.append(ticker)
			self.main()
		return buyInfo

	'''
	* Analyzes coin data and decides when to sell
	* @param buyInfo  purchase information used to make selling decision
	*
	'''
	def analyzePrice(self, buyInfo):
		api = apiCalls()
		ticker = buyInfo[0]
		buyPrice = float(buyInfo[2])
		highPrice = buyPrice
		while (True):
			print("...analyzing " + ticker + " markets...")
			response = api.getPrice(ticker)
			currentPrice = response['Last']
			if (currentPrice > highPrice):
				highPrice = currentPrice
				print("PRICE INCREASE")
			elif (self.percentChange(currentPrice, highPrice) < -5 or 
					self.percentChange(currentPrice, buyPrice) > 5):
				# sell if current price falls 5% below high price or 
				# current price is certain percentage above buy price
				print("initiating sell (" + ticker + ")")
				self.sell(ticker)
				break
			time.sleep(20) 

	'''
	* @param price1  current price
	* @param price2  variable price
	* @return        percent difference between two prices
	'''
	def percentChange(self, price1, price2):
		return ((price1 - price2) / price1) * 100

	'''
	* Sells specified coin on Bittrex for optimal price and logs transaction info
	* @param ticker  cryptocurrency to be sold
	'''
	def sell(self, ticker):
		api = apiCalls()
		sellInfo = api.sell(ticker)
		if not (sellInfo):
			print("ERROR: Sell Failed")
		else:
			print("sold")
			self.log("sell", sellInfo['orderTime'], sellInfo['executedPrice'], sellInfo['amount'])
			self.main()
		
	'''
	* Logs all transactions in format that enables easy profit/loss calculations 
	* and visualizations
	* @param buyOrSell  whether transaction was buying or selling
	* @param time       time of transaction
	* @param price      price of transaction
	* @param amount     total amount bought or sold
	'''
	def log(self, buyOrSell, time, price, amount):
		file = open("testLog.txt", "a")
		write(buyOrSell + " " + time + " " + price + " " + amount)
		file.close()

	def main(self):
		chosenCoin = self.surgeSearch()
		buyInfo = self.buy(chosenCoin)
		self.analyzePrice(buyInfo)

if __name__ == '__main__':
	bot = surgeBot()
	bot.main()