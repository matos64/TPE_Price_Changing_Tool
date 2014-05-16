__projectName__ = 'TPE-Price-Changing-Tool'
__organization__ = 'Tractor Parts Express'
__author__ = 'Matt Presley'
__contact__ = 'mpresley2653@gmail.com'
__version__ = '1.03'
__date__ = '5-14-2014'

"""
Program Summary:
The purpose of this application is to facilitate the process of changing prices for Tractor Parts Express ("TPE").
The user is expected to prepare input files with data from TPE's database and data sent to TPE by Tisco.
The system reads in this data and outputs files with updated product info, which can then be uploaded to TPE's database.


Planned changes in version 1.03:
- Make the program more modular, allowing the user to customize how they want prices changed and for which products
- Possibly add GUI elements to make customization more user-friendly

"""

import math

# input file streams
finTiscoProdNums = open('IN - Tisco Product Numbers.txt', 'r')
finTiscoPrices = open('IN - Tisco Prices.txt', 'r')
finDiscountProdNums = open('IN - Discount Product Numbers.txt', 'r')
finDiscountPrices = open('IN - Discount Prices.txt', 'r')
finTpeNames = open('IN - TPE Names.txt', 'r')
finTpeSkus = open('IN - TPE SKUs.txt', 'r')
finTpePrices = open('IN - TPE Prices.txt', 'r')
finTpeWeights = open('IN - TPE Weights.txt', 'r')

# output file streams
foutSkus = open('OUT - Skus.txt', 'w')
foutNames = open('OUT - Names.txt', 'w')
foutPrices = open('OUT - Prices.txt', 'w')
foutMissingProds = open('OUT - Missing Products.txt', 'w')
foutExcludedProds = open('OUT - Excluded Products.txt', 'w')
foutOriginalProducts = open('OUT - Original Product List.txt', 'w')
foutUpdatedProducts = open('OUT - Updated Product List.txt', 'w')
foutTiscoProducts = open('OUT - Tisco Product List.txt', 'w')

# lists to hold various types of Products
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

# user input variables
updateSinglePack = False 		# boolean, True if user wants to update items sold individually
updateMultiPack = False 		# boolean, True if user wants to update items sold in multi-packs
singlePackBasePrice = 'current'	# string, determines whether the price increase is based on wholesale or current price
multiPackBasePrice = 'current'	# string, determines whether the price increase is based on wholesale or current price
singlePackMultiplier = 1.00 	# float, to be multiplied by the wholesale or current prices of single-pack products
multiPackMultiplier = 1.00 		# float, to be multiplied by the wholesale or current prices of multi-pack products



###############################################
# OBJECT AND FUNCTION SUMMARIES #
###############################################
# Product.................. object that holds information about a single product
# getTiscoProducts()....... reads in data from Tisco's files and creates a list of objects
# getTpeProducts()......... reads in data from TPE's files and creates a list of objects
# applyTiscoDiscounts()......... finds items in main Tisco list that need discounts and applies those discounts
# findMatchingProducts()... finds products in TPE's list that match products in Tisco's list
# categorizeAndExcludeProducts()....... finds products that need to be excluded or modified
# updatePrices()........... updates the prices of all items TPE's inventory that we want to change
# generateUploadFiles().............. writes data to output files to be uploaded to ShopSite
# printAllInfo()........... writes a formatted set of data about all products in a list
# getUserInputs().......... asks user which types of products they want updates (single and/or multi-pack)



class Product:
	"""Common base class for all products"""
	def __init__(self: object, sku, name, prodNum, price, weight, isMultiPack, isExcluded, isSinglePack):
		self.sku = sku 						# string
		self.name = name 					# string
		self.prodNum = prodNum 				# string
		self.price = price 					# float
		self.weight = weight 				# float
		self.isSinglePack = isSinglePack	# boolean
		self.isMultiPack = isMultiPack 		# boolean
		self.isExcluded = isExcluded		# boolean




def getUserInputs():
	"""
	This function asks the user which types of products they want to change and how.
	For both single- and multi-pack products, the user has the option to change prices based on the wholesale price,
	based on the current TPE price, or to exclude the category from modification.
	The user is also asked by what factor they wish for the prices to change.
	At the end of the function, a summary of the user's choices is displayed to the console.
	Called by "Main".
	"""
	print('called getUserInputs()')

	global updateSinglePack
	global singlePackBasePrice
	global singlePackMultiplier
	global updateMultiPack
	global multiPackBasePrice
	global multiPackMultiplier

	# get single-pack and multi-pack preferences
	getPreferences('single-pack')
	getPreferences('multi-pack')

	print("\nSINGLE-PACK PREFERENCES")
	print("Update desired: " + str(updateMultiPack))
	print("Base price: " + str(singlePackBasePrice))
	print("Prices will be multiplied by " + str(singlePackMultiplier))

	print("\nMULTI-PACK PREFERENCES")
	print("Update desired: " + str(updateSinglePack))
	print("Base price: " + str(multiPackBasePrice))
	print("Prices will be multiplied by " + str(multiPackMultiplier) + '\n')



def getPreferences(multiplicity):
	"""
	This function gets user input for either single-pack or multi-pack preferences, and will be called twice.
	Called by getUserInputs()
	"""
	print('Called getPreferences()')

	global updateSinglePack
	global singlePackBasePrice
	global singlePackMultiplier
	global updateMultiPack
	global multiPackBasePrice
	global multiPackMultiplier

	# ask the user whether they want an item type modified
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

	# ask the user on what they want the prices based
	if updateOrNot:
		basePrice = input('Which prices do you want the new prices based on? (TPE/Tisco)')
		basePrice = basePrice.upper()
		while basePrice != 'TPE' and basePrice != 'TISCO':
			print('ERROR: Only \'TPE\' and \'Tisco\' are accepted answers.')
			basePrice = input('Which prices do you want the new prices based on? (TPE/Tisco)')
			basePrice = basePrice.upper()

		# ask the user by what factor they would like the prices modified
		multiplier = input('By what factor would you like to multiply the base price? (ex. \'1.45\' adds a 45% increase) ')
		multiplier = float(multiplier)
		while not (0.49 < multiplier < 2.01):
			print('ERROR: The price multiplier must be between 0.5 (cutting prices in half) and 2.0 (doubling prices).')
			multiplier = input('By what factor would you like to multiply the base price? (ex. \'1.45\' adds a 45% increase)')
			multiplier = float(multiplier)

	if multiplicity == 'single-pack':
		updateSinglePack = updateOrNot
		singlePackBasePrice = basePrice
		singlePackMultiplier = multiplier
	elif multiplicity == 'multi-pack':
		updateMultiPack= updateOrNot
		multiPackBasePrice= basePrice
		multiPackMultiplier= multiplier



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
	print('called getComponent()')

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
	This function takes in an empty list of Product objects and populates it with information from input text files.
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
	After flagging is complete, flagged products are moved to a different list.
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
			# ExcludedCategories = ['carburetor.', 'starter.', 'rim.', 'radiator.']
			for category in ExcludedCategories:
				if word == category:
					product.isExcluded = True

		# flag single-pack items
		if not product.isMultiPack:
			product.isSinglePack = True

		# move all remaining items into one of three lists: SinglePackProducts, MultiPackProducts, or ExcludedProducts
		if product.isExcluded:
			ExcludedProducts.append(product)			# products excluded by category
		elif product.isSinglePack and updateSinglePack:
			SinglePackProducts.append(product)
		elif product.isMultiPack and updateMultiPack:
			MultiPackProducts.append(product)
		else:
			ExcludedProducts.append(product)			# products excluded by quantity

	# free up space in list
	for product in productList:
		productList.remove(product)



def updatePrices(singlePackProducts, multiPackProducts):
	"""
	This function updates the prices of all TPE products in the given list.
	Single-pack items are addressed first and then multi-pack items second, if neither category has been excluded.
	Then all updated products are merged back into a single list and final touches are made.
	Called by "Main".
	"""
	print('called updatePrices()')

	# update single-pack products and append to UpdatedProducts list
	if updateSinglePack:
		if singlePackBasePrice == 'TISCO':
			findMatchingProducts(singlePackProducts)
		for product in singlePackProducts:
			product.price *= singlePackMultiplier
			UpdatedProducts.append(product)

	# update multi-pack products and append to UpdatedProducts list
	if updateMultiPack:
		if multiPackBasePrice == 'TISCO':
			findMatchingProducts(multiPackProducts)
		for product in multiPackProducts:
			product.price *= multiPackMultiplier
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
	Prices ending in "0" (10, 20, 200, etc) will cost $1 cheaper.
	Everything is "rounded up" to x.99 cents.
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

		# for prices specifically just above $100, drop them to $99.99
		if 99 < product.price < 104:
			product.price = 99

		# "round up" to 99 cents
		product.price += 0.99

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
	This function prints out a formatted list containing all members of a product list.
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
	#print('called findMaxLength()')
	maxLength = 0
	for item in itemList:
		if len(item) > maxLength:
			maxLength = len(item)
		return maxLength + 5



def writeLabel(outfile, label, maxLength):
	"""
	This function writes a column header and blank spaces after it.
	Called by printAllInfo().
	"""
	print('called writeLabel()')
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
	#print('called writeProductInfo()')
	outfile.write(str(member))
	for i in range(0, maxLength - len(member)):
		outfile.write(" ")



def generateUploadFiles(productList):
	"""
	This function takes in a product list and writes product names, prices, and skus to three separate text files for
	copy/pasting into Excel.
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

# close input streams
finTiscoPrices.close()
finTiscoProdNums.close()
finDiscountPrices.close()
finDiscountProdNums.close()
finTpeNames.close()
finTpeSkus.close()
finTpePrices.close()
finTpeWeights.close()

# close output streams
foutSkus.close()
foutNames.close()
foutPrices.close()
foutMissingProds.close()
foutExcludedProds.close()
foutOriginalProducts.close()
foutTiscoProducts.close()
foutUpdatedProducts.close()

print('\n'+'Done, son!')