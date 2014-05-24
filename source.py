__projectName__ = 'TPE-Price-Changing-Tool'
__organization__ = 'Tractor Parts Express'
__author__ = 'Matt Presley'
__contact__ = 'mpresley2653@gmail.com'
__version__ = '1.03'
__date__ = '5-23-2014'


"""
Program Summary:
The purpose of this application is to facilitate the process of changing prices for Tractor Parts Express ("TPE").
The user is expected to prepare input files with data from TPE's database and with data sent to TPE by Tisco.
The system reads in this data and outputs files with updated product info, which can then be uploaded to TPE's database.


What's new in version 1.03:
- The system has been made more modular, allowing the user to customize how they want prices changed and for
	which products instead of having everything hard-coded.
- Any functions more than 50 lines long have been broken up into multiple smaller functions for readability.
- New class added to hold all user choices: UserInputs.
- Many variable and function names have been changed for clarity.
- Totals: The system now uses 2 classes, 23 functions, and 625 lines of code (including comments and whitespace).
"""


import math


# lists to hold various types of items
fileStreams = []		# holds all input and output file streams
TiscoProducts = [] 		# holds ALL Tisco products
DiscountProducts = [] 	# holds only discounted Tisco products
TpeProducts = [] 		# holds all products from TPE's current inventory
MissingProducts = [] 	# TPE products for which a match is not found
ExcludedProducts = [] 	# TPE products which are not to be modified due to type exclusion
UpdatedProducts = [] 	# TPE products which are have their prices updated
SinglePackProducts = []	# single-pack products ready to have prices updated
MultiPackProducts = []	# multi-pack products ready to have prices updated
ExcludedCategories = ['carburetor.', 'starter.', 'rim.', 'radiator.'] # hard-coding these for now
prodNumList = []		# product numbers only
skuList = []			# skus only
priceList = []			# prices only
weightList = []			# weights only


#################################
# OBJECT AND FUNCTION SUMMARIES #
#################################
# Product.................. object that holds info about a single product
# UserInputs............... object that holds user input for a given category of products
# openFileStreams()........ opens file streams and consolidates them into a list
# openStream()............. opens an input or output file stream and adds it to a list.
# closeFileStreams()....... closes all open file streams in the given list.
# getUserInputs().......... asks the user which types of products they want to change and how.
# getPreferences()......... gets user input for either single-pack or multi-pack preferences.
# getModify().............. asks the user whether they want a product category to be modified or ignored.
# getBase()................ asks the user on what they want the prices based (TPE or TISCO).
# getPriceMultiplier()..... asks the user by what factor they would like the base price modified.
# getWeightMultiplier().... asks the user by how much to increase the price per pound.
# printUserChoices()....... prints out the user's choices for confirmation and testing.
# getTpeProducts()......... reads in TPE product info from files and populates a list of Products.
# getComponent()........... reads in a list containing a single member type and appends each to its Product object.
# getTiscoProducts()....... populates an empty list of Products with information from input text files.
# applyTiscoDiscounts().... applies discounts to any matching products in the "full" Tisco list.
# categorizeAndExcludeProducts() sorts TPE products into a set of pre-defined categories and removes select products.
# updatePrices()........... updates the prices of all TPE products in the given list.
# findMatchingProducts()... finds products (based on part number) that are found in both the TPE and Tisco lists.
# polishUpPrices()......... adds the final touches to prices after the primary modifications have been made.
# printAllInfo()........... prints out a formatted list containing all members of a product list.
# findMaxLength().......... reads in a list and finds the maximum number of characters of any element in the list.
# writeLabel()............. writes a column header and blank spaces after it based on the longest item in the column.
# writeProductInfo()....... writes all information about a single product to an output file.
# generateUploadFiles().... writes product names, prices, and skus to three text files for copy/pasting into Excel.


class Product:
	""" This class holds all information about a single product in the TPE or Tisco inventory. """
	def __init__(self: object, sku, name, prodNum, price, weight, isMultiPack, isExcluded, isSinglePack):
		self.sku = sku 						# string
		self.name = name 					# string
		self.prodNum = prodNum 				# string
		self.price = price 					# float
		self.weight = weight 				# float
		self.isSinglePack = isSinglePack	# boolean
		self.isMultiPack = isMultiPack 		# boolean
		self.isExcluded = isExcluded		# boolean


class UserInputs:
	""" This class holds all user preferences for one product multiplicity (single-packs or multi-packs). """
	def __init__(self, willModify, priceBasedOn, baseMultiplier, weightMultiplier):
		self.willModify = willModify
		self.priceBasedOn = priceBasedOn
		self.baseMultiplier = baseMultiplier
		self.weightMultiplier = weightMultiplier


def openFileStreams():
	"""	This function opens file streams and consolidates them into a list. Called by "Main". """
	print('called openFileStreams()')

	# input file streams
	global finTiscoProdNums, finTiscoPrices, finDiscountProdNums, finDiscountPrices, finTpeNames, finTpeSkus, finTpePrices, finTpeWeights
	finTiscoProdNums = openStream('IN - Tisco Product Numbers.txt', 'r')
	finTiscoPrices = openStream('IN - Tisco Prices.txt', 'r')
	finDiscountProdNums = openStream('IN - Discount Product Numbers.txt', 'r')
	finDiscountPrices = openStream('IN - Discount Prices.txt', 'r')
	finTpeNames = openStream('IN - TPE Names.txt', 'r')
	finTpeSkus = openStream('IN - TPE SKUs.txt', 'r')
	finTpePrices = openStream('IN - TPE Prices.txt', 'r')
	finTpeWeights = openStream('IN - TPE Weights.txt', 'r')

	# output file streams
	global foutSkus, foutNames, foutPrices, foutMissingProds, foutExcludedProds, foutOriginalProducts, foutUpdatedProducts, foutTiscoProducts
	foutSkus = openStream('OUT - Skus.txt', 'w')
	foutNames = openStream('OUT - Names.txt', 'w')
	foutPrices = openStream('OUT - Prices.txt', 'w')
	foutMissingProds = openStream('OUT - Missing Products.txt', 'w')
	foutExcludedProds = openStream('OUT - Excluded Products.txt', 'w')
	foutOriginalProducts = openStream('OUT - Original Product List.txt', 'w')
	foutUpdatedProducts = openStream('OUT - Updated Product List.txt', 'w')
	foutTiscoProducts = openStream('OUT - Tisco Product List.txt', 'w')


def openStream(file, readOrWrite):
	"""	This function opens an input or output file stream and adds it to a list. Called by openFileStreams(). """
	stream = open(file, readOrWrite)
	fileStreams.append(stream)
	return stream


def closeFileStreams():
	""" This function closes all open file streams in the given list. Called by "Main".	"""
	for stream in fileStreams:
		stream.close()
	print('called closeFileStreams()')


def getUserInputs():
	"""
	This function asks the user which types of products they want to change and how.
	For both single- and multi-pack products, the user has the option to change prices based on the wholesale price,
			or based on the current TPE price. The user may alternatively exclude the category from modification.
	The user is asked by what factor prices should be changed, how much to add based on weight, and how to
			"round up" the final price.
	Finally, a summary of the user's choices is displayed to the console.
	Called by "Main".
	"""
	print('called getUserInputs()')

	global singlePacks, multiPacks, roundUpAmount
	singlePacks = UserInputs(False, 'nothing', 0.0, 0.0)
	multiPacks = UserInputs(False, 'nothing', 0.0, 0.0)

	# get single-pack and multi-pack preferences
	getPreferences('single-pack', singlePacks)
	getPreferences('multi-pack', multiPacks)

	# ask user for "round up" amount (88 cents, 99 cents, etc)
	roundUpAmount = input('To how many cents would you like prices "rounded up"? (ex. \'88\' rounds prices up to the next 88 cents) ')
	roundUpAmount = int(roundUpAmount)
	while not (0 <= roundUpAmount <= 99):
		print('ERROR: The "round up" amount must be between 0 and 99, (inclusive).')
		roundUpAmount = input('To how many cents do you wanted prices "rounded up"? (ex. \'88\' rounds prices up to the next 88 cents) ')
		roundUpAmount = int(roundUpAmount)

	# print out inputs to the user for confirmation
	printUserChoices()


def getPreferences(multiplicity, userInputs):
	"""
	This function gets user input for either single-pack or multi-pack preferences, and will be called twice.
	Called by getUserInputs()
	"""
	print('Called getPreferences()')

	# ask the user whether they want a product category modified
	userInputs.willModify = getModify(multiplicity)

	# if yes, ask the user for info on how they want prices to be modified
	if userInputs.willModify:
		userInputs.priceBasedOn = getBase()
		userInputs.baseMultiplier = getPriceMultiplier()
		userInputs.weightMultiplier = getWeightMultiplier()


def getModify(multiplicity):
	"""
	This function asks the user whether they want a product category (single-pack or multi-pack) to be modified or ignored.
	Called by getPreferences().
	"""
	print("Called getModify()")

	updateOrNot = input('Do you want to modify ' + multiplicity + ' items? (yes/no) ')
	updateOrNot = updateOrNot.lower()
	while updateOrNot != 'yes' and updateOrNot != 'y' and updateOrNot != 'no' and updateOrNot != 'n':
		print('ERROR: Only \'yes\' and \'no\' are accepted answers.')
		updateOrNot = input('Do you want to modify ' + multiplicity + ' items? (yes/no) ')
		updateOrNot = updateOrNot .lower()
	if updateOrNot == 'yes' or updateOrNot == 'y':
		updateOrNot = True
	else:
		updateOrNot = False
	return updateOrNot


def getBase():
	"""
	This function asks the user on what they want the prices based (TPE or TISCO).
	Called by getPreferences().
	"""
	print("Called getBase()")

	priceBasedOn = input('Which prices do you want the new prices based on? (TPE/Tisco)')
	priceBasedOn = priceBasedOn.upper()
	while priceBasedOn != 'TPE' and priceBasedOn != 'TISCO':
		print('ERROR: Only \'TPE\' and \'Tisco\' are accepted answers.')
		priceBasedOn = input('Which prices do you want the new prices based on? (TPE/Tisco)')
		priceBasedOn = priceBasedOn.upper()
	return priceBasedOn


def getPriceMultiplier():
	"""
	This function asks the user by what factor they would like the base price modified.
	Called by getPreferences().
	"""
	print("Called getPriceMultiplier()")

	multiplier = input('By what factor would you like to multiply the base price? (ex. \'1.45\' adds a 45% increase) ')
	multiplier = float(multiplier)
	while not (0.49 < multiplier < 2.01):
		print('ERROR: The price multiplier must be between 0.5 (cutting prices in half) and 2.0 (doubling prices).')
		multiplier = input('By what factor would you like to multiply the base price? (ex. \'1.45\' adds a 45% increase)')
		multiplier = float(multiplier)
	return multiplier


def getWeightMultiplier():
	"""
	This function asks the user by how much to increase the price per pound.
	Called by getPreferences().
	"""
	print("Called getBasePreference()")

	dollarsPerPound = input('How much should the price increase per pound? (ex. \'0.30\' adds a 30 cents per pound) ')
	dollarsPerPound = float(dollarsPerPound)
	while not (dollarsPerPound >= 0.0):
		print('ERROR: The price increase per pound must be a non-negative number.')
		dollarsPerPound = input('How much should the price increase per pound? (ex. \'0.30\' adds a 30 cents per pound) ')
		dollarsPerPound = float(dollarsPerPound)
	return dollarsPerPound


def printUserChoices():
	""" This function prints out the user's choices for confirmation and testing. Called by getUserInputs(). """

	print("\nSINGLE-PACK PREFERENCES")
	print("Update desired: " + str(singlePacks.willModify))
	print("Prices based on: " + str(singlePacks.priceBasedOn))
	print("Prices will be multiplied by " + str(singlePacks.baseMultiplier))
	print("Dollars added per pound: " + str(singlePacks.weightMultiplier))

	print("\nMULTI-PACK PREFERENCES")
	print("Update desired: " + str(multiPacks.willModify))
	print("Prices based on: " + str(multiPacks.priceBasedOn))
	print("Prices will be multiplied by " + str(multiPacks.baseMultiplier))
	print("Dollars added per pound: " + str(multiPacks.weightMultiplier))

	print("\n\"Round-up\" amount: " + str(roundUpAmount) + " cents.\n")


def getTpeProducts():
	"""
	This function reads in TPE product names and extracts the part numbers, populating a list of Product objects with
	both names and numbers. It then adds the sku, price, and weight for each item.
	Called by "Main".
	"""
	print('called getTpeProducts()')

	# get names, product numbers, skus, prices, and weights for each product
	getComponent(TpeProducts, finTpeNames, 'name', '\n')
	getComponent(TpeProducts, finTpeSkus, 'sku', '\n')
	getComponent(TpeProducts, finTpePrices, 'price', ',')
	getComponent(TpeProducts, finTpeWeights, 'weight', ',')

	# sort the TpeProducts list by product name alphabetically
	TpeProducts.sort(key=lambda product: product.name)


def getComponent(productList, finList, memberType, charToRemove):
	"""
	This function reads in a list containing a single member type and appends each to its Product object.
	Called by getTpeProducts().
	"""

	i = 0
	for item in finList:
		item = item.replace(charToRemove, '')
		item = item.lstrip()

		# get names and product numbers
		if memberType == 'name':
			words = item.split()
			prodNumIndex = len(words)
			newProduct = Product("", item, words[prodNumIndex - 1], 0, 0, False, False, False)
			productList.append(newProduct)

		# get skus
		elif memberType == 'sku':
			productList[i].sku = item

		# get prices
		elif memberType == 'price':
			item = float(item)
			productList[i].price = item

		# get weights
		elif memberType == 'weight':
			item = float(item)
			productList[i].weight = item
		i += 1


def getTiscoProducts(productList, prodNums, prices):
    """
	This function takes in an empty list of Products and populates it with information from input files.
	Called by "Main".
	"""
    print('called getTiscoProducts()')

    # fill productList with ALL products
    for item in prodNums:
        item = item.replace('\n', '')
        newProduct = Product("", "", item, 0, 0, False, False, False)
        productList.append(newProduct)

    i = 0
    for item in prices:
        item = item.replace(',', '')
        item = item.lstrip()
        item = float(item)
        productList[i].price = item
        i += 1


def applyTiscoDiscounts(productList):
    """
	This function applies discounts to any matching products in the "full" Tisco list.
	Called by "Main".
	"""
    print('called applyTiscoDiscounts()')

    for discountProduct in DiscountProducts:
        for product in productList:
            if product.prodNum == discountProduct.prodNum:
                product.price = discountProduct.price


def categorizeAndExcludeProducts(productList):
	"""
	This function sorts all TPE products into a set of pre-defined categories.
	Each product is flagged as either a single-pack or multi-pack item.
	Products that need to be excluded are flagged as such as well.
	After flagging is complete, flagged products are moved to one of three different lists for further processing.
	Called by "Main".
	"""
	print('called categorizeAndExcludeProducts()')

	for product in productList:
		product.isExcluded = False

		# split each product name into words and search for keywords
		prodName = product.name.split(' ')
		for word in prodName:
			word = word.lower()

			# flag multi-pack items
			if word == 'pack.':
				product.isMultiPack = True

			# flag items to be excluded
			for category in ExcludedCategories:
				if word == category:
					product.isExcluded = True

		# flag single-pack items
		if not product.isMultiPack:
			product.isSinglePack = True

		# move all remaining items into one of three lists: SinglePackProducts, MultiPackProducts, or ExcludedProducts
		if product.isExcluded:
			ExcludedProducts.append(product)			# products excluded by category
		elif product.isSinglePack and singlePacks.willModify:
			SinglePackProducts.append(product)
		elif product.isMultiPack and multiPacks.willModify:
			MultiPackProducts.append(product)
		else:
			ExcludedProducts.append(product)			# products excluded by quantity


def updatePrices(singlePackProducts, multiPackProducts):
	"""
	This function updates the prices of all non-excluded TPE products.
	Single-pack items are addressed first and then multi-pack items second, if neither category has been excluded.
	Then all updated products are merged back into a single list and final touches are made.
	Called by "Main".
	"""
	print('called updatePrices()')

	# update single-pack products and append to UpdatedProducts list
	if singlePacks.willModify:
		if singlePacks.priceBasedOn == 'TISCO':
			findMatchingProducts(singlePackProducts)
		for product in singlePackProducts:
			product.price *= singlePacks.baseMultiplier
			product.price += product.weight * singlePacks.weightMultiplier
			UpdatedProducts.append(product)

	# update multi-pack products and append to UpdatedProducts list
	if multiPacks.willModify:
		if multiPacks.priceBasedOn == 'TISCO':
			findMatchingProducts(multiPackProducts)
		for product in multiPackProducts:
			product.price *= multiPacks.baseMultiplier
			product.price += product.weight * multiPacks.weightMultiplier
			UpdatedProducts.append(product)

	# "polish up" final prices and modify product names to reflect the updated prices
	polishUpPrices(UpdatedProducts)


def findMatchingProducts(tpeProducts):
	"""
	This function finds products (based on part number) that are found in both the TPE and Tisco lists.
	Any matching products have the TPE price change to match Tisco's price
	Any products without matches are added to a different list: MissingProducts
	Called by updatePrices().
	"""
	print('called findMatchingProducts()')

	for tpeItem in tpeProducts:
		tpeNum = tpeItem.prodNum
		matchFound = False

		# if a match is found, update the TPE price to the Tisco price
		for tiscoItem in TiscoProducts:
			if tiscoItem.prodNum == tpeNum:
				tpeItem.price = tiscoItem.price
				matchFound = True
				break

		# if a match is not found, copy the TPE product to MissingProducts
		if not matchFound:
			MissingProducts.append(tpeItem)
			tpeProducts.remove(tpeItem)


def polishUpPrices(productList):
	"""
	This function adds the final touches to prices after the primary modifications have been made.
	Prices ending in "0" (10, 20, 200, etc) will cost $1 less.
	Everything is "rounded up" a number of cents set by the user.
	Product names are changed to reflect new prices.
	Called by updatePrices().
	"""
	print('called polishUpPrices()')

	for product in productList:

		# remove the extra cents
		product.price = math.floor(product.price)

		# for prices ending in multiples of 10, add $1 to avoid "10.99" issue
		testPrice = str(product.price)
		if testPrice[len(testPrice) - 1] == '0':
			product.price += 1

		# "round up" to 99 cents
		product.price = int(product.price)
		product.price = str(product.price) + "." + str(roundUpAmount)

		# for prices specifically just near $100, set them to exactly $100.00
		if 98 < float(product.price) < 104:
			product.price = '100.00'

		# modify product name to include new price
		i = 0
		words = product.name.split()
		newPrice = str(product.price)
		for word in words:
			if word[0] == '$':
				words[i] = '$' + newPrice + '.'
			i+=1
		product.name = " ".join(words)


def printAllInfo(productList, outfile):
	"""
	This function prints out a formatted list containing all members of a Product list.
	Called by "Main".
	"""
	print('called printAllInfo()')

	if not productList:
		outfile.write('List is empty!\n\n\n')

	# split products into their member components
	for product in productList:
		prodNumList.append(product.prodNum)
		skuList.append(product.sku)
		priceList.append(str(product.price).lstrip() + '\n')
		weightList.append(str(product.weight).lstrip() + '\n')

	# find maximum length for each member in the overall product list
	prodNumLength = findMaxLength(prodNumList)
	skuLength = findMaxLength(skuList)
	priceLength = findMaxLength(priceList)
	weightLength = findMaxLength(weightList)

	# write labels
	prodNumLength = writeLabel(outfile, 'PRODUCT NUMBER     ', prodNumLength)
	skuLength = writeLabel(outfile, 'SKU     ', skuLength)
	priceLength = writeLabel(outfile, 'PRICE     ', priceLength)
	weightLength = writeLabel(outfile, 'WEIGHT     ', weightLength)
	outfile.write('NAME\n')

	# write each product's information
	for product in productList:
		writeProductInfo(outfile, product.prodNum, prodNumLength)
		writeProductInfo(outfile, product.sku, skuLength)
		writeProductInfo(outfile, str(product.price), priceLength)
		writeProductInfo(outfile, str(product.weight), weightLength)
		outfile.write(product.name + '\n')


def findMaxLength(itemList):
	"""
	This function reads in a list and finds the maximum number of characters of any element in the list.
	Called by printAllInfo().
	"""
	maxLength = 0
	for item in itemList:
		if len(item) > maxLength:
			maxLength = len(item)
	return maxLength + 5


def writeLabel(outfile, label, maxLength):
	"""
	This function writes a column header and blank spaces after it based on the longest item in the column.
	Called by printAllInfo().
	"""
	outfile.write(label)
	if maxLength > len(label):
		for i in range(0, maxLength - len(label)):
			outfile.write(' ')
	else:
		maxLength = len(label)
	return maxLength


def writeProductInfo(outfile, member, maxLength):
	"""
	This function writes all information about a single product to an output file.
	Called by printAllInfo().
	"""
	outfile.write(str(member))
	for i in range(0, maxLength - len(member)):
		outfile.write(" ")


def generateUploadFiles(productList):
	"""
	This function writes product names, prices, and skus to three separate text files for copy/pasting into Excel.
	Called by "Main".
	"""
	print('called generateUploadFiles()')
	for product in productList:
		foutNames.write(product.name + '\n')
		foutSkus.write(product.sku + '\n')
		foutPrices.write(str(product.price).lstrip() + '\n')


##############################
#           "MAIN"           #
##############################

# ask user which types of products they want to modify and how
getUserInputs()

# open all file streams
openFileStreams()

# read in info from text files
getTiscoProducts(TiscoProducts, finTiscoProdNums, finTiscoPrices)
getTiscoProducts(DiscountProducts, finDiscountProdNums, finDiscountPrices)
getTpeProducts()

# apply discounts to items in TiscoProducts
applyTiscoDiscounts(TiscoProducts)

# generate full product lists before making modifications, for comparison
printAllInfo(TpeProducts, foutOriginalProducts)
printAllInfo(TiscoProducts, foutTiscoProducts)

# sort TPE products into categories and exlude products that are not to be modified
categorizeAndExcludeProducts(TpeProducts)

# update prices
updatePrices(SinglePackProducts, MultiPackProducts)

# print final output into files for uploading to ShopSite
generateUploadFiles(UpdatedProducts)

# print formatted lists of products
printAllInfo(UpdatedProducts, foutUpdatedProducts)
printAllInfo(MissingProducts, foutMissingProds)
printAllInfo(ExcludedProducts, foutExcludedProds)

# close all file streams
closeFileStreams()

print('\n'+'WORK COMPLETE!')