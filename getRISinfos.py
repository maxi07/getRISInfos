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
	from datetime import datetime, date
	from tqdm import tqdm
	from colorama import init
	import traceback
	import unicodedata
	import re
	init()
except ModuleNotFoundError as ex:
    printerror("The app could not be started, a module is missing.")
    printerror(ex)
    exit(2)
except Exception as ex:
	printerror("An unknown error occured while loading modules." + str(ex))
	exit(2)

# Set var
filepathResult = ""
verboseoutput = False
askConfirm = False
getPDF = False
foundItems = 0
foundAbstract = 0
foundReferenceType = 0
foundJournal = 0
foundUrl = 0
foundAuthors = 0
foundLanguage = 0
foundPublisher = 0
successfullReverseChecks = 0
downloadedPdfs = 0
notFound = 0
noDOI = 0
finalentries = [{}]

# Parse Arguments
parser = ArgumentParser()
parser.add_argument("--verbose", "-v", help="Print detailed output.", action="store_true")
parser.add_argument("--confirm", "-c", help="Ask confirmation before replacing details.", action="store_true")
parser.add_argument("--getpdf", "-p", help="Try to download pdf if available.", action="store_true")

args = parser.parse_args()
if args.verbose:
	verboseoutput = True
if args.confirm:
	askConfirm = True
if args.getpdf:
	getPDF = True

# Calls crossref with given DOI number and downloads input
def getCrossref(doi: str) -> json:
	try:
		with urllib.request.urlopen("http://api.crossref.org/works/" + str(doi)) as url:			
			data = json.load(url)
			if data['status'] == 'ok':
				printverbose("Successfully retrieved JSON from Crossref")
			return data
	except Exception as ex:
		printverboseerror("Failed downloading data from Crossref.")
		printverboseerror(traceback.format_exc())
		return None

# Calls crossref with given title and downloads input
def getCrossrefReverse(title: str, author: str) -> json:
	try:
		# Encode title
		title = title.replace(" ", "+")
		searchURL = r"https://api.crossref.org/works?rows=1&query.title=" + title
		if author:
			author = author.replace(",", "")
			author = author.replace(" ", "+")
			author = author.replace(".", "")
			searchURL += "&query.author=" + author
		with urllib.request.urlopen(searchURL) as url:			
			data = json.load(url)
			if data['status'] == 'ok':
				printverbose("Successfully retrieved JSON from Crossref by reverse check.")
			return data
	except Exception as ex:
		printverboseerror("Failed downloading data from Crossref.")
		printverboseerror(traceback.format_exc())
		return None

# Try to find a pdf to download
def downloadPDF(urllist: list):
	"""
	Downloads the file if the mimetype pdf is detected.
	"""
	global downloadedPdfs
	filename = entry['title']
	filename = filename[:75] if len(filename) > 75 else filename
	filename = re.sub('[^A-Za-z0-9 ]+', '', filename) # Remove unwanted chars
	for url in urllist:
		success = downloadFile(url, filename)
		if success == True:
			downloadedPdfs+=1
			return
	printverbosewarning("No PDF could be found.")


def downloadFile(url: str, name: str) -> bool:
	"""
	Checks mimetype, if PDF and download successfull returns True
	"""
	try:
		response =  urllib.request.urlopen(url)
		info = response.info()
		if info.get_content_type() == "application/pdf":
			printverbose("Detected " + url + " as PDF file.")
			filename = name + ".pdf"
			p = Path(filepathResult / filename)
			with open(p, 'wb') as output:
				data = response.read()
				output.write(data)
				printverbose("Saved PDF at " + printgreen(str(p.absolute())))
				return True
		else:
			printverbosewarning("Requested filetype for url " + str(url) + " is not PDF, skipping download.")
			return False
	except urllib.error.HTTPError as e:
		printverboseerror("Failed opening url.")
		printverboseerror(str(e.code) + " " + str(e.read()))	
	except Exception:
		printverboseerror("Failed downloading pdf. ")
		printverboseerror(traceback.format_exc())
		return False


def readAbstract(data) -> str:
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
	except Exception:
		printverboseerror("Failed reading abstract. ")
		printverboseerror(traceback.format_exc())


def readReferenceType(data) -> str:
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

def readJournal(data) -> str:
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

def readLanguage(data) -> str:
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

def readPublisher(data) -> str:
	try:
		if 'publisher' in data['message']:
			publisher = str(data['message']['publisher'])
			printverbose("Found publisher: " + printgreen(publisher))
			return publisher
		else:
			printverbosewarning("No publisher was found online")
			return None

	except Exception as e:
		printverboseerror("Failed reading language. " + str(e))

def readAuthors(data) -> list[dict]:
	try:
		if 'author' in data['message']:
			authorlist = [{}]
			for author in data['message']['author']:
				if author['sequence'] == "first":
					authorlist.append({'name': author['family'] + ", " + author['given'], 'sequence': "first"})
					printverbose("Found first author: " + printgreen(author['family'] + ", " + author['given']))
				elif author['sequence'] == "additional":
					authorlist.append({'name': author['family'] + ", " + author['given'], 'sequence': "additional"})
					printverbose("Found additional author: " + printgreen(author['family'] + ", " + author['given']))
				else:
					authorlist.append({'name:': author['family'] + ", " + author['given'], 'sequence': "none"})
					printverbose("Found author: " + printgreen(author['family'] + ", " + author['given']))
			return authorlist
		else:
			printverbosewarning("No author was found online")
			return None

	except Exception as e:
		printverboseerror("Failed reading author. " + str(e))

def query_yes_no(question, default="yes"):
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        print(question + prompt)
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")

def checkEntry(entry: dict):
	global successfullReverseChecks
	global notFound
	# Check if DOI
	if 'doi' in entry:		
		doAnalysis(entry)
	elif 'title' and 'authors' in entry: # Do reverse search with title and author
		try:
			# Encode title
			title = str(entry['title'])
			logMessage = "No DOI detected, starting reverse search with title " + printblue(title[:50] + "...")

			# Get first author
			firstAuthor = str(entry["authors"][0])		
			if firstAuthor:
				logMessage += " and author " + printblue(firstAuthor + ".")
			printverbose(logMessage)
			data = getCrossrefReverse(title, firstAuthor)
			if data:
				successfullReverseChecks +=1
				entry['doi'] = data['message']['items'][0]['DOI']
				doAnalysis(entry)
			else:
				notFound +=1
		except:
			printverboseerror("Failed reverse engineering the entry.")
			printverboseerror(traceback.format_exc())
	else: #Nothing could be matched
		printverbosewarning("Document could not be matched.")

def doAnalysis(entry: dict):
	"""
	Perform the actual analysis.
	:param dict: The dictionary entry from RIS
	"""
	global foundItems
	global foundAbstract
	global foundReferenceType
	global foundJournal
	global foundUrl
	global foundLanguage
	global foundPublisher
	global foundAuthors
	global notFound
	global noDOI
	global finalentries
	try:
		doi = str(entry['doi'])
		printverbose("")
		printverbose("(" + str(currentcount) + "/" + str(len(entries)) + ") Reading info for DOI " + printblue(doi))
		jsoninfo = getCrossref(doi)
		if not jsoninfo: #Crossref returned 404
			printverbosewarning("Crossref couldn't match " + doi)
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
		if not 'language' in entry:
			printverbose("No document language was detected, searching online.")
			language = readLanguage(jsoninfo)
			if language:
				# Add language to dictionary
				entry['language'] = language
				foundItems +=1
				foundLanguage +=1
		if not 'access_date' in entry:
			printverbose("No access date was detected, adding todays date.")
			entry['access_date'] = str(date.today())
		if not 'publisher' in entry:
			printverbose("No publisher was detected, searching online.")
			publisher = readPublisher(jsoninfo)
			if publisher:
				# Add publisher to dictionary
				entry['publisher'] = publisher
				foundItems +=1
				foundPublisher +=1
		if not 'authors' and not 'first_authors' and not 'secondary_authors' and not 'subsidiary_authors' in entry:
			printverbose("No author was detected, searching online.")
			authors = readAuthors(jsoninfo)
			if authors:
				# Add authors to dictionary
				firstAuthors = []
				additionalAuthors = []
				otherAuthors = []
				for author in authors:
					if author['sequence'] == "First":
						firstAuthors.append(author['name'])
					elif author['sequence'] == "Additional":
						additionalAuthors.append(author['name'])
					else:
						otherAuthors.append(author['name'])
				entry['authors'] = otherAuthors
				entry['first_authors'] = firstAuthors
				entry['second_authors'] = additionalAuthors
				foundItems +=1
				foundAuthors +=1
		if 'authors' or 'first_authors' or 'secondary_authors' or 'subsidiary_authors' in entry:
			printverbose("Authors were detected, searching online for additions.")
			authors = readAuthors(jsoninfo)
			if authors:
				# Add authors to dictionary
				firstAuthors = []
				additionalAuthors = []
				otherAuthors = []
				for author in authors:
					if not author:
						continue
					if author['sequence'] == "first":
						firstAuthors.append(author['name'])
					elif author['sequence'] == "additional":
						additionalAuthors.append(author['name'])
					else:
						otherAuthors.append(author['name'])
					foundAuthors +=1			
				if askConfirm == True:
					currentAuthors = []
					# Add all current author to one string
					if entry.get('authors'):
						currentAuthors.append(entry.get('authors'))
					if entry.get('first_authors'):
						currentAuthors.append(entry.get('first_authors'))
					if entry.get('secondary_authors'):
						currentAuthors.append(entry.get('secondary_authors'))
					if entry.get('subsidiary_authors'):
						currentAuthors.append(entry.get('subsidiary_authors'))

					# Add all new authors to string
					newAuthors = firstAuthors + additionalAuthors + otherAuthors
					currentAuthorsString = ""
					newAuthorsString = ""
					for cA in currentAuthors:
						currentAuthorsString += str(cA)
					for nA in newAuthors:
						newAuthorsString += str(nA)
					print("Current authors: " + currentAuthorsString)
					print("New authors: " + newAuthorsString)
					choice = query_yes_no("Replace authors?")
					if choice == True:
						entry['authors'] = otherAuthors
						entry['first_authors'] = firstAuthors
						entry['secondary_authors'] = additionalAuthors
				else:
						entry['authors'] = otherAuthors
						entry['first_authors'] = firstAuthors
						entry['secondary_authors'] = additionalAuthors
				foundItems +=1
		
		# Add URLs
		urllist = []
		urllist.append(entry['url'])
		for url in getUrls(jsoninfo):
			urllist.append(url)
			printverbose("Found document URL: " + printgreen(url))
			foundUrl +=1
			foundItems +=1
		
		# Set url in entry
		if len(urllist) > 0:
			entry['file_attachments1'] = urllist
			if not 'url' in entry:
				entry['url'] = urllist[0]

		if getPDF == True:
			if 'url' or 'file_attachments1' or 'file_attachments2' in entry:
				downloadPDF(urllist)			

		# Add dict entry to new list
		finalentries.append(entry)
	except Exception as ex:
		printerror("An error occured for analysis.")
		printverboseerror(traceback.format_exc())
			
def getUrls(jsoninfo: json) -> list:
	try:
		urls = []
		if 'link' in jsoninfo['message']:
			for url in jsoninfo['message']['link']:
				if url['content-type'] == "application/pdf":
					urls.append(url['URL'])
				elif url['content-type'] == "unspecified":
					urls.append(url['URL'])
				else:
					printverbosewarning("No PDF was found.")
			return urls
		else:
			printverbosewarning("No PDF was found.")
			return None
	except Exception:
		printverboseerror("Failed retrieving URL.")
		printverboseerror(traceback.format_exc())
		return None

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
	while not filepathResult:
		filepathResult = input(r"Enter filepath for saving result (e.g. C:\Users\Max): ")
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
		filepathResult = Path(filepathResult)


	try:
		p = Path('tests', 'data', filepathOriginal)
		entries = rispy.load(p, encoding='utf-8')
		# Create new dictionary for later final output writing
		print("Detected " + printblue(str(len(entries))) + " items in ris file.")
		currentcount = 0
		if verboseoutput == True:
			for entry in entries:
				currentcount +=1
				checkEntry(entry)
		else:
			for entry in tqdm(entries, desc ="Analyzing RIS", ascii=' ='):
				currentcount +=1
				checkEntry(entry)
		
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
		print("Added authors:\t\t" + printgreen(str(foundAuthors)))
		if getPDF == True:
			print("Downloaded PDFs:\t" + printgreen(str(downloadedPdfs)))
		print("Reverse checks:\t" + printgreen(str(successfullReverseChecks)))
		print("Documents not found:\t" + printyellow(str(notFound)))
		input("Press enter to exit.")
	except Exception as ex:
		printerror("Error opening file")
		printerror(str(ex))
		input("Press enter to exit.")