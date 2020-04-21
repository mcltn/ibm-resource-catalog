import os, requests, simplejson, sys, string, csv
from urllib.parse import urlparse


offset = 0
count = 0
total_count = 0

loop = True

header = {}
#token = 'Bearer ey'
#os.environ['BEARER_TOKEN'] # 'Bearer AABB1122...'
#header = {'Authorization': token}

## OPEN LOG FILE FOR OUTPUT
log = open("resource-catalog.log","w")

## OPEN CSV FILE FOR OUTPUT
outputname = 'resource-catalog-03272020.csv'
outfile = open(outputname, 'w')
csvwriter = csv.writer(outfile, delimiter='\t', quotechar='"', quoting=csv.QUOTE_ALL)

fieldnames = ['ParentId', 'ParentName', 'ParentProvider', 'ParentDescription', 'ChildId', 'ChildName','ChildKind', 'PlanDescription', 'Provider', 'ResourceId',
              'Location', 'PriceType', 'ChargeUnit', 'ChargeUnitDisplayName', 'ChargeUnitName', 'ChargeUnitQuantity', 'DisplayCap', 'UsageCapQuantity', 'MetricId', 'TierModel', 
              'Price', 'QuantityTier']
csvwriter = csv.DictWriter(outfile, delimiter=',', fieldnames=fieldnames)
csvwriter.writerow(dict((fn, fn) for fn in fieldnames))

currentRow = {}


def getChildResource(id, parent_name, parent_provider, parent_description, url):
	url += '?include=metadata.pricing'
	r = requests.get(url, headers=header)
	children = r.json()
	#print(simplejson.dumps(children, sort_keys=True, indent=4 * ' '))

	for child in children['resources']:
		child_id = child['id']
		child_kind = child['kind']
		child_name = child['name']

		location = ''
		if 'deployment' in child['metadata']:
			location = child['metadata']['deployment']['location']

		if 'provider' in child and 'name' in child['provider']:
			provider = child['provider']['name']
		else:
			provider = 'n/a'

		description = ''
		if 'long_description' in child['overview_ui']['en']:
			description = child['overview_ui']['en']['long_description']
		elif "description" in child['overview_ui']['en']:
			description = child['overview_ui']['en']['description']

		currentRow['ParentId'] = id 
		currentRow['ParentName'] =  parent_name
		currentRow['ParentProvider'] =  parent_provider
		currentRow['ParentDescription'] =  parent_description
		currentRow['ChildId'] = child_id
		currentRow['ChildKind'] = child_kind
		currentRow['ChildName'] = child_name
		currentRow['PlanDescription'] = description
		currentRow['Provider'] = provider
		currentRow['ResourceId'] = id # repeat?
		currentRow['Location'] = location

#		for resource in resources['resources']:
		if 'pricing' in child['metadata'] and 'url' in child['metadata']['pricing']:
			price_url = child['metadata']['pricing']['url']
			print('\n\n\n')
			print('###### ' + price_url + ' ######')
			r = requests.get(price_url, headers=header)
			result = r.json()
			#print(simplejson.dumps(result, sort_keys=True, indent=4 * ' '))

			#if 'deployment' not in child['metadata']:
			#	break
			#elif child['metadata']['deployment']['location'] == 'us-south' or child['metadata']['deployment']['location'] == 'global':
			getPricing(result)
		else:
			if 'children_url' in child:
				getChildResource(id, parent_name, parent_provider, parent_description, child['children_url'])




def getPricing(result):
	if 'type' in result:
		currentRow['PriceType'] = result['type']
		if (len(result['metrics']) > 0):
			for metric in result['metrics']:

				currentRow['ChargeUnit'] = metric['charge_unit']
				currentRow['ChargeUnitDisplayName'] = metric['charge_unit_display_name']
				currentRow['ChargeUnitName'] = metric['charge_unit_name']
				currentRow['ChargeUnitQuantity'] = metric['charge_unit_quantity']
				currentRow['DisplayCap'] = metric['display_cap']
				currentRow['MetricId'] = metric['metric_id']
				currentRow['TierModel'] = metric['tier_model']
				currentRow['UsageCapQuantity'] = metric['usage_cap_qty']

				price = 0
				quantity_tier = 0

				if 'amounts' in metric and metric['amounts'] != None:
					for amount in metric['amounts']:
						#if amount['country'] == 'USA':
							#### Should loop here for more tiers??
						for tier in amount['prices']:
							currentRow['Price'] = tier['price']
							currentRow['QuantityTier'] = tier['quantity_tier']

							csvwriter.writerow(currentRow)
		else:
			print('No Pricing...')
			currentRow['ChargeUnit'] = ""
			currentRow['ChargeUnitDisplayName'] = ""
			currentRow['ChargeUnitName'] = ""
			currentRow['ChargeUnitQuantity'] = 0
			currentRow['DisplayCap'] = 0
			currentRow['MetricId'] = ""
			currentRow['TierModel'] = ""
			currentRow['UsageCapQuantity'] = 0
			currentRow['Price'] = 0
			currentRow['QuantityTier'] = 0
			csvwriter.writerow(currentRow)



while loop:
	print('\n##### CATALOG #####')
	print('## OFFSET ' + str(offset) + ' ###')
	url = 'https://resource-catalog.bluemix.net/api/v1?include=metadata.pricing'
	url += '&_offset=' + str(offset)

	r = requests.get(url, headers=header)
	print(r.status_code)
	response = r.json()

	log.write(simplejson.dumps(response, sort_keys=True, indent=4 * ' '))

	print('\n')
	print(response['count'])
	print(response['resource_count'])
	print(response['limit'])
	print(response['offset'])
	print(offset)

	count = response['count']
	offset += response['resource_count']

	for resource in response['resources']:
		print('\n### RESOURCE ###')
		#print(simplejson.dumps(resource, sort_keys=True, indent=4 * ' '))

		print('Id:\t' + resource['id'])
		print('Kind:\t' + resource['kind'])
		print('Name:\t' + resource['name'])
		print('Provider:\t' + resource['provider']['name'])
		print('Description:\t' + resource['overview_ui']['en']['long_description'])
		print('Url:\t' + resource['children_url'])

		getChildResource(resource['id'], resource['name'], resource['provider']['name'], resource['overview_ui']['en']['long_description'], resource['children_url'])

		total_count += 1

	if offset >= count:
		loop = False

outfile.close()

print('completed')
print(total_count)