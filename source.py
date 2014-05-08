__author__ = 'Matt'
__projectName__ = 'TPE-Price-Changing-Tool'
__organization__ = 'Tractor Parts Express'
__author__ = 'Matt Presley'
__contact__ = 'mpresley2653@gmail.com'
__version__ = '1.03'
__date__ = '5-8-2014'

"""
Program Summary:
The purpose of this application is to facilitate the process of changing prices for Tractor Parts Express ("TPE").
The user is expected to prepare input files with data from TPE's database and data sent to TPE by Tisco.
The system reads in this data and outputs files with updated product info, which can then be uploaded to TPE's database.


Planned changes in version 1.03:
- Make the program more modular, allowing the user to customize how they want prices changed and for which products
- Make the program (slightly) more object-oriented, using a base class (Product) and an inherited class (TpeProduct)
- Possibly add GUI elements to make customization more user-friendly

"""


import math

# input file streams
finTiscoProdNums = open('IN - Tisco Product Numbers.txt', 'r')
finTiscoPrices = open('IN - Tisco Prices.txt', 'r')
finDiscountProdNums = open('IN - Discount Product Numbers.txt', 'r')
finDiscountPrices = open('IN - Discount Prices.txt', 'r')
finTpeNames = open('IN - TPE Names.txt', 'r')
finTpeSKUs = open('IN - TPE SKUs.txt', 'r')
finTpePrices = open('IN - TPE Prices.txt', 'r')
finTpeWeights = open('IN - TPE Weights.txt', 'r')

# output file streams
foutSKUs = open('OUT - SKUs.txt', 'w')
foutNames = open('OUT - Names.txt', 'w')
foutPrices = open('OUT - Prices.txt', 'w')
foutMissingProds = open('OUT - Missing Products.txt', 'w')
foutExcludedProds = open('OUT - Excluded Products.txt', 'w')
foutOriginalProducts = open('OUT - Original Product List.txt', 'w')
foutUpdatedProducts = open('OUT - Updated Product List.txt', 'w')
foutTiscoProducts = open('OUT - Tisco Product List.txt', 'w')

# lists to hold various types of Products
TiscoProducts = [] # holds ALL Tisco products
DiscountProducts = [] # holds only discounted Tisco products
TpeProducts = [] # holds all products from TPE's current inventory
MissingProducts = [] # TPE products for which a match is not found
ExcludedProducts = [] # TPE products which are not to be changed due to type exclusion
UpdatedProducts = [] # TPE products which have their prices updated

# user input variables
updateSinglePack = False # boolean, True if user wants to update items sold individually
updateMultiPack = False # boolean, True if user wants to update items sold in multi-packs

# price modification variables
tiscoMarkup = 1.45 # single-pack items have their wholesale price increased by this amount
multiPackIncrease = 1.10 # multi-pack items have the TPE price increased by this amount instead of using TiscoMarkup



###############################################
# OBJECT AND FUNCTION SUMMARIES #
###############################################
# Product.................. object that holds information about a single product
# getTiscoProducts()....... reads in data from Tisco's files and creates a list of objects
# getTpeProducts()......... reads in data from TPE's files and creates a list of objects
# applyDiscounts()......... finds items in main Tisco list that need discounts and applies those discounts
# findMatchingProducts()... finds products in TPE's list that match products in Tisco's list
# findSpecialCases()....... finds products that need to be excluded or modified
# changePrices()........... updates the prices of all items TPE's inventory that we want to change
# printList().............. writes data to output files to be uploaded to ShopSite
# printAllInfo()........... writes a formatted set of data about all products in a list
# getUserInputs().......... asks user which types of products they want updates (single and/or multi-pack)



class Product:
    """Common base class for all products"""

    def __init__(self, SKU, name, prodNum, price, weight, isMultiPack):
        self.SKU = SKU # string
        self.name = name # string
        self.prodNum = prodNum # string
        self.price = price # float
        self.weight = weight # float
        self.isMultiPack = isMultiPack # boolean



def getUserInputs():
    """
This function asks the user which types of products they want to change.
Currently affects only 'single-pack' and 'multi-pack' product categories
"""
    print('called getUserInputs()')

    global updateSinglePack
    global updateMultiPack

    # get valid single-pack choice
    updateSinglePack = input('Do you want to update single-pack items? (yes/no) ')
    updateSinglePack = updateSinglePack.lower()
    while updateSinglePack != 'yes' and updateSinglePack != 'y' and updateSinglePack != 'no' and updateSinglePack != 'n':
        print('ERROR: Only \'yes\' and \'no\' are accepted answers.')
        updateSinglePack = input('Do you wish to update single-pack items? (yes/no) ')
        updateSinglePack = updateSinglePack.lower()
    if updateSinglePack == 'yes' or updateSinglePack == 'y':
        updateSinglePack = True
    else:
        updateSinglePack = False
    print("Updating single-pack items: " + str(updateSinglePack))#

    # get valid multi-pack choice
    updateMultiPack = input('Do you want to update multi-pack items? (yes/no) ')
    updateMultiPack = updateMultiPack.lower()
    while updateMultiPack != 'yes' and updateMultiPack != 'y' and updateMultiPack != 'no' and updateMultiPack != 'n':
        print('ERROR: Only \'yes\' and \'no\' are accepted answers.')
        updateMultiPack = input('Do you wish to update single-pack items? (yes/no) ')
        updateMultiPack = updateMultiPack.lower()
    if updateMultiPack == 'yes' or updateMultiPack == 'y':
        updateMultiPack = True
    else:
        updateMultiPack = False
    print("Updating multi-pack items: " + str(updateMultiPack))



def getTiscoProducts(productList, prodNums, prices):
    """
This function takes in an empty list of Product objects and populates it with information from input text files.
"""
    print('called getTiscoProducts()')

    # fill productList with ALL products
    for item in prodNums:
        item = item.replace('\n', '')
        newProduct = Product("", "", item, 0, 0, False)
        productList.append(newProduct)

    i = 0
    for item in prices:
        item = item.replace(',', '')
        item = item.lstrip()
        item = float(item)
        productList[i].price = item
        i += 1



def getTpeProducts():
    """
This function reads in TPE product names and extracts the part numbers, populating a list of Product objects with
both names and numbers. It then adds the SKU, price, and weight for each item.
"""
    print('called getTpeProducts()')

    # get names
    for name in finTpeNames:
        name = name.replace('\n', '')
        words = name.split()
        prodNumIndex = len(words)
        newProduct = Product("", name, words[prodNumIndex - 1], 0, 0, False)
        TpeProducts.append(newProduct)

    # get SKUs
    i = 0
    for sku in finTpeSKUs:
        sku = sku.replace('\n', '')
        TpeProducts[i].SKU = sku
        i += 1

    # get prices
    i = 0
    for price in finTpePrices:
        price = price.replace(',', '')
        price = price.lstrip()
        price = float(price)
        TpeProducts[i].price = price
        i += 1

    # get weights
    i = 0
    for weight in finTpeWeights:
        weight = weight.replace(',', '')
        weight = weight.lstrip()
        weight = float(weight)
        TpeProducts[i].weight = weight
        i += 1

    # sort the TpeProducts list by product name alphabetically
    TpeProducts.sort(key=lambda product: product.name)



def applyDiscounts():
    """
This function applies discounts to any matching products in the "full" Tisco list.
"""
    print('called applyDiscounts()')

    for discountProduct in DiscountProducts:
        for product in TiscoProducts:
            if product.prodNum == discountProduct.prodNum:
                product.price = discountProduct.price



def findSpecialCases(productList):
    """
This function compares each item in the given list against a set of criteria.
If a product fals under certain categories it will be copied into ExcludedProducts and will not be changed.
If a product is a multi-pack item, it is flagged as such and its price change will be handled differently.
"""
    print('called findSpecialCases()')

    removalSKU = [] # holds SKUs (keys) of any items that are to be excluded

    for product in productList:
        exclude = False

        # split each product name into words and search for keywords
        prodName = product.name.split(' ')
        for word in prodName:
            word = word.lower()

            # identify multi-pack items, and exclude if the user does not wish to update them
            if word == 'pack.':
                product.isMultiPack = True
                if updateMultiPack == False:
                    exclude = True

            # exclude if the product is a carburetor
            elif word == 'carburetor.':
                exclude = True

            # exclude if the product is a starter
            elif word == 'starter.':
                exclude = True

            # exclude if the product is a rim
            elif word == 'rim.':
                exclude = True

            # exclude if the product is a radiator
            elif word == 'radiator.':
                exclude = True

            if exclude:
                break

        # if the item is a single-pack item and the user does not wish to update them, exlude the item
        if product.isMultiPack == False and updateSinglePack == False:
            exclude = True

        # sort items to be excluded into lists, either for exlusion by type or quantity
        if exclude:
            removalSKU.append(product.SKU)
            ExcludedProducts.append(product)

    # remove any products from the list that are to be excluded
    for sku in removalSKU:
        for product in productList:
            if product.SKU == sku:
                productList.remove(product)



def findMatchingProducts():
    """
This function finds products (based on part number) that are found in both the TPE and Tisco lists.
Any matching products are added to a list: UpdatedProducts
Any products without matches are added to a different list: MissingProducts
"""
    print('called findMatchingProducts()')
    j = 1
    numTpeProds = 1
    tpeProdsLength = len(TpeProducts)
    for tpeItem in TpeProducts:
        tpeNum = tpeItem.prodNum
        matchFound = False

        for tiscoItem in TiscoProducts:
            # if a match is found, update the TPE price to the new Tisco price and copy the product to UpdatedProducts
            if tiscoItem.prodNum == tpeNum:
                if tpeItem.isMultiPack == False:
                    tpeItem.price = tiscoItem.price
                UpdatedProducts.append(tpeItem)
                matchFound = True
                break
        # if a match is not found, copy the TPE product to MissingProducts
        if matchFound == False:
            MissingProducts.append(tpeItem)
        numTpeProds += 1
        if numTpeProds % 1000 == 0:
            print(str(numTpeProds) + ' of ' + str(tpeProdsLength) + ' products compared.')



def printAllInfo(productList, outfile):
    """
This function prints out a formatted list containing all members of a product list
"""
    print('called printAllInfo()')
    if not productList:
        outfile.write('List is empty!\n\n\n')

    # find maximum SKU length
    skuLength = 0
    for product in productList:
        if len(product.SKU) > skuLength:
            skuLength = len(product.SKU)

    # write labels
    outfile.write('PRODUCT NUMBER SKU')
    for i in range(0, skuLength-3):
        outfile.write(' ')
    outfile.write('PRICE WEIGHT NAME\n')

    # write each product's information
    for product in productList:
        # product number
        outfile.write(product.prodNum)

        # sku
        numSpaces = 20 - len(product.prodNum)
        for i in range(0, numSpaces):
            outfile.write(" ")
        outfile.write(str(product.SKU))

        # price
        numSpaces = skuLength - len(str(product.SKU))
        for i in range(0, numSpaces):
            outfile.write(" ")
        outfile.write(str(product.price))

        # weight
        numSpaces = 20 - len(str(product.price))
        for i in range(0, numSpaces):
            outfile.write(" ")
        outfile.write(str(product.weight))

        # name
        numSpaces = 20 - len(str(product.weight))
        for i in range(0, numSpaces):
            outfile.write(" ")
        outfile.write(product.name + '\n')



def changePrices(productList):
    """
This function changes the prices of all products in productList.
If the product is a multi-pack item, its TPE price is increased by multiPackIncrease (ex 10%).
If the product is not a multi-pack item, its Tisco wholesale price is increased by tiscoMarkup (ex. 45%)
For all products, the price is increased based on weight (weightIncrease), then is "rounded up" to the next 99 cents.
This function also updates the name of the item to reflect the new price.
"""
    print('called changePrices()')

    for product in productList:

        #increase price of single-pack items
        if updateSinglePack == True and product.isMultiPack == False:
            product.price *= tiscoMarkup

        # increase price of multi-pack items
        elif updateMultiPack == True and product.isMultiPack == True:
            product.price *= multiPackIncrease

        # remove the extra cents
        product.price = math.floor(product.price)

        # for prices ending in multiples of 10, add $1 to avoid "10.99" issue
        testPrice = str(product.price)
        if testPrice[len(testPrice) - 1] == '0':
            product.price += 1

        # for prices specifically just above $100, drop them to $99.99
        if product.price > 99 and product.price < 104:
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



def printList(productList):
    """
This function takes in a product list and writes product names, prices, and SKUs
to three separate text files for copy/pasting into Excel
"""
    for product in productList:
        foutNames.write(product.name + '\n')
        foutSKUs.write(product.SKU + '\n')
        foutPrices.write(str(product.price).lstrip() + '\n')



##############################################
# "MAIN" #
##############################################

# ask user which types of products they want to update
getUserInputs()



# read in info from text files
getTiscoProducts(TiscoProducts, finTiscoProdNums, finTiscoPrices)
getTiscoProducts(DiscountProducts, finDiscountProdNums, finDiscountPrices)
getTpeProducts()

# generate full product list for comparison
printAllInfo(TpeProducts, foutOriginalProducts)
printAllInfo(TiscoProducts, foutTiscoProducts)


# apply discounts to items in TiscoProducts
applyDiscounts()

# find TPE products that are to be excluded or flagged as special cases
findSpecialCases(TpeProducts)

# compare Tisco products and TPE products to find products that need price changes
findMatchingProducts()

# update prices
changePrices(UpdatedProducts)

# print final output into files for uploading to ShopSite
printList(UpdatedProducts)



# print formatted lists of products
#printAllInfo(TpeProducts, )

printAllInfo(UpdatedProducts, foutUpdatedProducts)
printAllInfo(MissingProducts, foutMissingProds)
printAllInfo(ExcludedProducts, foutExcludedProds)



# close input streams
finTiscoPrices.close()
finTiscoProdNums.close()
finDiscountPrices.close()
finDiscountProdNums.close()
finTpeNames.close()
finTpeSKUs.close()
finTpePrices.close()
finTpeWeights.close()



# close output streams
foutSKUs.close()
foutNames.close()
foutPrices.close()
foutMissingProds.close()
foutExcludedProds.close()
foutOriginalProducts.close()
foutTiscoProducts.close()
foutUpdatedProducts.close()


print('\n'+'Done, son!')