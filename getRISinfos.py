# A python tool for extracting all RIS documents and adding missing info from Crossref
# Author: Maximilian Krause
# Date: 26.09.2022
# RIS info can be found here: https://pypi.org/project/rispy/

# Define Error Logging
def printerror(ex):
	print('\033[31m' + str(ex) + '\033[0m')

def printverbose(msg):
	if verboseoutput == True:
		print(str(msg))

def printverboseerror(msg):
	if verboseoutput == True:
		print('\033[31m' + str(msg) + '\033[0m')

def printverbosewarning(msg):
	if verboseoutput == True:
		print('\033[33m' + str(msg) + '\033[0m')

def printwarning(warn):
	print('\033[33m' + str(warn) + '\033[0m')

def printyellow(warn) -> str:
	return('\033[33m' + str(warn) + '\033[0m')

def printgreen(msg) -> str:
	return('\033[32m' + str(msg) + '\033[0m')

def printblue(msg) -> str:
	return('\033[34m' + str(msg) + '\033[0m')

# Imports
import os
try:
	from pathlib import Path
	import rispy
	import urllib.request, json
	from argparse import ArgumentParser
	from datetime import datetime
	from tqdm import tqdm
	from colorama import init
	init()
except ModuleNotFoundError as ex:
    printerror("The app could not be started, a module is missing.")
    printerror(ex)
    exit(2)
except Exception as ex:
	printerror("An unknown error occured while loading modules." + str(ex))
	exit(2)

# Set var
verboseoutput = False
foundItems = 0
foundAbstract = 0
foundReferenceType = 0
foundJournal = 0
foundUrl = 0
foundLanguage = 0
notFound = 0
noDOI = 0
finalentries = [{}]


# Parse Arguments
parser = ArgumentParser()
parser.add_argument("--verbose", "-v", help="Print detailed output.", action="store_true")
args = parser.parse_args()
if args.verbose:
	verboseoutput = True

# Calls crossref with given DOI number and downloads input
def getCrossref(doi):
	try:
		with urllib.request.urlopen("http://api.crossref.org/works/" + str(doi)) as url:			
			data = json.load(url)
			if data['status'] == 'ok':
				printverbose("Successfully retrieved JSON from Crossref")
			return data
	except Exception as ex:
		printverboseerror("Failed downloading data.")
		printverboseerror(str(ex))
		return None

def readAbstract(data):
	try:
		if 'abstract' in data['message']:
			abstract_raw = str(data['message']['abstract'])
			# Test if abstract starts with <jats:p> and remove
			if abstract_raw.startswith("<jats:p>"):
				abstract_raw = abstract_raw[8:]
			# Test if abstract ends with <jats:p>
			if abstract_raw.endswith("</jats:p>"):
				abstract_raw = abstract_raw[:-9]
			#Test if abstract starts with <jats:sec>
			if abstract_raw.startswith("<jats:sec>"):
				index = abstract_raw.find("<jats:p>")
				abstract_raw = abstract_raw[index+8:]
				index = abstract_raw.find("</jats:p>")
				abstract_raw = abstract_raw[:index]
			#Test if abstract starts with <jats:title>
			if abstract_raw.startswith("<jats:title>"):
				index = abstract_raw.find("<jats:p>")
				abstract_raw = abstract_raw[index+8:]
				index = abstract_raw.find("</jats:p>")
				abstract_raw = abstract_raw[:index]
			printverbose("Found abstract: " + printgreen(abstract_raw[0:80] + "..."))
			return abstract_raw
		else:
			printverbosewarning("No abstract was found online.")
			return None
	except Exception as e:
		printverboseerror("Failed reading abstract. " + str(e))

def readReferenceType(data):
	try:
		if 'type' in data['message']:
			type = str(data['message']['type'])
			printverbose("Found type " + printgreen(type))
			return type
		else:
			printverbosewarning("No type was found online")
			return None
	except Exception as e:
		printverboseerror("Failed reading type. " + str(e))

def readJournal(data):
	try:
		if 'container-title' in data['message']:
			journal = str(data['message']['container-title'])
			journal = journal[2:]
			journal = journal[:-2]
			printverbose("Found journal: " + printgreen(journal))
			return journal
		else:
			printverbosewarning("No journal was found online")
			return None
	except Exception as e:
		printverboseerror("Failed reading journal. " + str(e))

def readURL(data):
	try:
		if 'link' in data['message']:
			link = str(data['message']['link'][0]["URL"])
			printverbose("Found document url: " + printgreen(link))
			return link
		else:
			printverbosewarning("No document url was found online")
			return None
	except Exception as e:
		printverboseerror("Failed reading document url. " + str(e))

def readLanguage(data):
	try:
		if 'language' in data['message']:
			language = str(data['message']['language'])
			printverbose("Found language: " + printgreen(language))
			return language
		else:
			printverbosewarning("No language was found online")
			return None

	except Exception as e:
		printverboseerror("Failed reading language. " + str(e))

def doAnalysis(entry):
	global foundItems
	global foundAbstract
	global foundReferenceType
	global foundJournal
	global foundUrl
	global foundLanguage
	global notFound
	global noDOI
	global finalentries
	try:
	# Test if DOI is present in current entry
		if 'doi' in entry:
			doi = str(entry['doi'])
			printverbose("")
			printverbose("(" + str(currentcount) + "/" + str(len(entries)) + ") Reading info for DOI " + printblue(doi))
			jsoninfo = getCrossref(doi)
			if not jsoninfo: #Crossref returned 404
				notFound +=1
				return
			if not 'abstract' in entry:
				printverbose("No abstract was detected, searching online.")
				abstract = readAbstract(jsoninfo)
				if abstract:
					# Add abstract to dictionary
					entry['abstract'] = abstract
					foundItems +=1
					foundAbstract +=1
			if not 'type_of_reference' in entry:
				printverbose("No reference type was detected, searching online.")
				type = readReferenceType(jsoninfo)
				if type:
					# Add type to dictionary
					entry['type_of_reference'] = type
					foundItems +=1
					foundReferenceType +=1
			if not 'journal_name' or not 'alternate_title3' or not 'alternate_title2' in entry:
				printverbose("No journal title was detected, searching online.")
				journal = readJournal(jsoninfo)
				if journal:
					# Add journal to dictionary
					entry['journal_name'] = journal
					foundItems +=1
					foundJournal +=1
			if not 'url' or not 'file_attachments1' or not 'file_attachments2' in entry:
				printverbose("No document url was detected, searching online.")
				url = readURL(jsoninfo)
				if url:
					# Add url to dictionary
					entry['url'] = url
					foundItems +=1
					foundUrl +=1
			if not 'language' in entry:
				printverbose("No document language was detected, searching online.")
				language = readLanguage(jsoninfo)
				if language:
					# Add language to dictionary
					entry['language'] = language
					foundItems +=1
					foundLanguage +=1
		else:
			printverbosewarning("(" + str(currentcount) + "/" + str(len(entries)) + ") DOI was not found for " + str(entry['title']))
			noDOI +=1
		# Add dict entry to new list
		finalentries.append(entry)
	except Exception as ex:
		printerror(str(ex))
			

if __name__ == "__main__":
	# Get filepath to RIS file
	filepathOriginal = ""
	while not filepathOriginal:
		filepathOriginal = input("Enter full filepath to .ris file: ")
		# Test if input starts with " and remove
		if filepathOriginal.startswith('"'):
			filepathOriginal = filepathOriginal[1:]
		# Test if abstract ends with 
		if filepathOriginal.endswith('"'):
			filepathOriginal = filepathOriginal[:-1]
		# Test if file exist
		if not os.path.exists(filepathOriginal):
			printerror("File does not exist!")
			filepathOriginal = None
			continue
		# Check if it is a .ris file
		if not filepathOriginal.endswith('.ris'):
			printerror("Given file is not a .ris file!")
			filepathOriginal = None

	# Get filepath for saving output
	filepathResult = ""
	while not filepathResult:
		filepathResult = input(r"Enter filepath for saving result (e.g. C:\Users\Max\): ")
		if not os.path.exists(filepathResult):
			printerror("File does not exist!")
			filepathResult = None
			continue
		# Test if input starts with " and remove
		if filepathResult.startswith('"'):
			filepathResult = filepathResult[1:]
		# Test if abstract ends with 
		if filepathResult.endswith('"'):
			filepathResult = filepathResult[:-1]


	try:
		p = Path('tests', 'data', filepathOriginal)
		entries = rispy.load(p, encoding='utf-8')
		# Create new dictionary for later final output writing
		print("Detected " + printblue(str(len(entries))) + " items in ris file.")
		currentcount = 0
		if verboseoutput == True:
			for entry in entries:
				currentcount +=1
				doAnalysis(entry)
		else:
			for entry in tqdm(entries, desc ="Analyzing RIS", ascii=' ='):
				currentcount +=1
				doAnalysis(entry)
		
		# Now write entries into output file
		print()
		print(printgreen("Done with reading all entries,") + " now saving file to " + str(filepathResult))

		# Get Timestamp
		now = datetime.now() # current date and time
		timestamp = now.strftime("%Y%m%d%H%M%S")

		try:
			with open(os.path.join(str(filepathResult), 'output_' + timestamp + '.ris'), 'w', encoding="utf-8") as bibliography_file:
				rispy.dump(finalentries, bibliography_file)
		except Exception as ex:
			printerror("Failed saving file. " + str(ex))

		print(printgreen("Done! ") + "We have added " + printblue(str(foundItems)) + " items to the list.")
		print("Added abstracts:\t" + printgreen(str(foundAbstract)))
		print("Added reference types:\t" + printgreen(str(foundReferenceType)))
		print("Added journal names:\t" + printgreen(str(foundJournal)))
		print("Added document urls:\t" + printgreen(str(foundUrl)))
		print("Added languages:\t" + printgreen(str(foundLanguage)))
		print("Documents without DOI:\t" + printyellow(str(noDOI)))
		print("Documents not found:\t" + printyellow(str(notFound)))
		input("Press enter to exit.")
	except Exception as ex:
		printerror("Error opening file")
		printerror(str(ex))
		input("Press enter to exit.")