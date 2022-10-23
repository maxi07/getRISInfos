# A python tool for extracting all RIS documents and adding missing info from Crossref
# Author: Maximilian Krause
# Date: 26.09.2022
# RIS info can be found here: https://pypi.org/project/rispy/

# Todo: proccess cant read write lobal var (filepath + count)

# Set var
verboseoutput = False
askConfirm = False
getPDF = False
noreverse = False
totalCount = 0
processes_count = 1
CIPHERS = "ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-SHA256:AES256-SHA"

# Define Error Logging
def printerror(ex, id = "undefined"):
	prefix = "[" + str(id) + "] "
	print(prefix + '\033[31m'  + str(ex) + '\033[0m', flush=True)

def printverbose(msg, id = "undefined"):
	if verboseoutput == True:
		prefix = "[" + str(id) + "] "
		print(prefix + str(msg), flush=True)

def printverboseerror(msg, id = "undefined"):
	if verboseoutput == True:
		prefix = "[" + str(id) + "] "
		print(prefix + '\033[31m' + str(msg) + '\033[0m', flush=True)

def printverbosewarning(msg, id="undefined"):
	if verboseoutput == True:
		prefix = "[" + str(id) + "] "
		print(prefix + '\033[33m' + str(msg) + '\033[0m', flush=True)

def printwarning(warn, id="undefined"):
	print('\033[33m' + str(warn) + '\033[0m', flush=True)

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
	import pathlib
	import urllib.request, json
	from argparse import ArgumentParser
	from datetime import datetime, date
	from colorama import init
	import traceback
	import random
	from difflib import SequenceMatcher
	from urllib.parse import quote  
	import re
	from mpire import WorkerPool
	from requests import Response
	import requests
	import time
	import re
	init()
except ModuleNotFoundError as ex:
	printerror("The app could not be started, a module is missing.")
	printerror("Please run command pip install -r requirements.txt")
	printerror(ex)
	exit(2)
except Exception as ex:
	printerror("An unknown error occured while loading modules." + str(ex))
	exit(2)


# Create class for counting and result returning
class resultInfo():
	foundItems = 0
	foundAbstract = 0
	foundReferenceType = 0
	foundJournal = 0
	foundUrl = 0
	foundAuthors = 0
	foundYear = 0
	foundLanguage = 0
	foundPublisher = 0
	successfullReverseChecks = 0
	downloadedPdfs = 0
	notFound = 0
	noDOI = 0
	filepathResult: pathlib.Path
	ris: dict
	id= 0
	total= 0
	args = None

# Calls crossref with given DOI number and downloads input
def getCrossref(doi: str, id: int) -> json:
	try:
		with urllib.request.urlopen("http://api.crossref.org/works/" + str(doi)) as url:			
			data = json.load(url)
			if data['status'] == 'ok':
				printverbose("Successfully retrieved JSON from Crossref for DOI " + printblue(str(doi)), id)
			return data
	except urllib.error.HTTPError as e:
		if e.code == 404:
			printverbosewarning("Crossref couldn't match " + doi, id)
		else:
			printverboseerror("Crossref returned " + str(e.code), id)
		return None
	except Exception as ex:
		printverboseerror("Failed downloading data from Crossref.", id)
		printverboseerror(traceback.format_exc(), id)
		return None

def getCrossrefReverse(title: str, author: str, id: int) -> str:
	"""
	Calls crossref with given title and downloads input.
	Returns DOI as str."""
	try:
		# Encode title
		originalTitle = title
		title = title.replace(" ", "+")
		title = re.sub('[^A-Za-z0-9+ ]+', '', title)
		searchResults = 5
		confidenceLevel = 0.85
		searchURL = r"https://api.crossref.org/works?rows=" + str(searchResults) + r"&query.title=" + title
		if author:
			author = author.replace(",", "")
			author = author.replace(" ", "+")
			author = author.replace(".", "")
			searchURL += r"&query.author=" + quote(author)
		with urllib.request.urlopen(searchURL) as url:	# Test with author		
			data = json.load(url)
			if data['status'] == 'ok':
				# test if title is the same
				for i in range(len(data['message']['items'])):
					if 'title' and 'DOI' in data['message']['items'][i]:					
						confidence = similar(originalTitle[:100], data['message']['items'][i]['title'][0][:100])
						if confidence >= confidenceLevel:
							printverbose(printgreen("Successfully retrieved JSON from Crossref by reverse check, confidence: " + str(round(confidence * 100, 1)) + "%."), id)
							printverbose("Original title:\t\t" + originalTitle, id)
							printverbose("Detected online title:\t" + str(data['message']['items'][i]['title'][0]), id)
							return str(data['message']['items'][i]['DOI'])
						else:
							printverbosewarning("Skipping entry due low confidence level: " + str(round(confidence * 100, 1)) + "%.", id)
							printverbose("Original title:\t\t" + originalTitle, id)
							printverbose("Detected online title:\t" + str(data['message']['items'][i]['title'][0]), id)
							continue
					else:
						printverbosewarning("Skipping entry in reverse check due to missing title and doi.", id)
						continue

		searchURL = r"https://api.crossref.org/works?rows=" + str(searchResults) + r"&query.title=" + title
		with urllib.request.urlopen(searchURL) as url:	# Test without author		
			data = json.load(url)
			if data['status'] == 'ok':
				# test if title is the same
				for i in range(len(data['message']['items'])):
					if 'title' and 'DOI' in data['message']['items'][i]:
						confidence = similar(originalTitle, str(data['message']['items'][i]['title'][0]))
						if confidence >= confidenceLevel:
							printverbose(printgreen("Successfully retrieved JSON from Crossref by reverse check, confidence: " + str(round(confidence * 100, 1)) + "%."), id)
							printverbose("Original title:\t\t" + originalTitle, id)
							printverbose("Detected online title:\t" + str(data['message']['items'][i]['title'][0]), id)
							return str(data['message']['items'][i]['DOI'])
						else:
							printverbosewarning("Skipping entry due low confidence level: " + str(round(confidence * 100, 1)) + "%.", id)
							printverbose("Original title:\t\t" + originalTitle, id)
							printverbose("Detected online title:\t" + str(data['message']['items'][i]['title'][0]), id)
							continue
					else:
						printverbosewarning("Skipping entry in reverse check due to missing title and doi.", id)
						continue
		return None
	except urllib.error.HTTPError as e:
		if e.code == 404:
			printverbosewarning("Crossref couldn't match " + title, id)
			return None
		else:
			printverboseerror("Crossref returned " + str(e.code), id)
			return None
	except Exception as ex:
		printverboseerror("Failed downloading data from Crossref.", id)
		printverboseerror(traceback.format_exc(), id)
		return None

def similar(a, b) -> float:
	"""Test if inputs are similar"""
	a = str(a).lower()
	b = str(b).lower()
	return SequenceMatcher(None, a, b).ratio()

# Try to find a pdf to download
def downloadPDF(urllist: list, filename: str, resultInfo: resultInfo) -> int:
	"""
	Downloads the file if the mimetype pdf is detected.
	"""
	id = resultInfo.id
	filename = filename[:75] if len(filename) > 75 else filename
	filename = re.sub('[^A-Za-z0-9 ]+', '', filename) # Remove unwanted chars
	filename = filename.strip() # Remove trailing and ending spaces
	for url in urllist:
		success = downloadFile(url, filename, resultInfo)
		if success == True:
			resultInfo.downloadedPdfs+=1
			return resultInfo.downloadedPdfs	
	printverbosewarning("No PDF could be found.", id)
	return 0

def isPDF(url: str, id=0) -> bool:
	"""
	Does the url contain a downloadable resource
	"""
	retries = 3
	for i in range(retries):
		try:
			h = requests.head(url, allow_redirects=True)
			header = h.headers
			content_type = header.get('content-type')
			if content_type:
				if 'application/pdf' in content_type.lower():
					return True
				else:
					return False
			else:
				return False
		except requests.exceptions.SSLError:
			printverboseerror("Failed request to check PDF due to too many requests (SSL Error).", id)
		except Exception:
			printverboseerror("Failed PDF check.", id)
		printverbose("[" + str(i+1) + "/" + str(retries) + "] Will retry in 10 seconds", id)
		time.sleep(10)


def cleanDateStr(input: str, id=0) -> str:
	if input[0:4].isdigit():
		if input.endswith("/"):
			newpy = input[0:4]
			printverbose("Cleaned PY string from '" + input + "' to '" + newpy + "'.", id)
			return newpy
		else:
			return input
	else:
		printverbose("Input string to clean PY is not a valid year!", id)
		return input

def cleanRISYear(input: resultInfo, id=0) -> resultInfo:
	if 'year' in input.ris:
		input.ris['year'] = cleanDateStr(input.ris['year'], id)
		return input
	else:
		return input

def downloadFile(url: str, name: str, resultInfo: resultInfo) -> bool:
	"""
	Downloads PDF and returns True is successfull
	"""
	try:
		id = resultInfo.id
		printverbose("Reading filetype for " + printblue(url), id)
		user_agents_list = [
		'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
		'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.83 Safari/537.36',
		'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36']
		hdr = {
			"User-Agent": random.choice(user_agents_list),
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
			"Accept-Language": "en-US,en;q=0.5",
			"Accept-Encoding": "gzip, deflate",
			"Connection": "keep-alive",
			"Upgrade-Insecure-Requests": "1",
			"Sec-Fetch-Dest": "document",
			"Sec-Fetch-Mode": "navigate",
			"Sec-Fetch-Site": "none",
			"Sec-Fetch-User": "?1",
			"Cache-Control": "max-age=0",
		}
		
		if isPDF(url, id):
			printverbose("Detected " + url + " as PDF file.", id)
			filename = name + ".pdf"
			p = Path(resultInfo.filepathResult, filename)
			response = requests.get(url, headers=hdr, allow_redirects=True)
			open(p, 'wb').write(response.content)
			printverbose("Saved PDF at " + printgreen(str(p.absolute())), id)
			return True
		else:
			printverbosewarning("Requested filetype for url " + str(url) + " is not PDF, skipping download.", id)
			return False
	except urllib.error.HTTPError as e:
		if e.code == 403:
			printverboseerror("Access denied for " + url, id)
		elif e.code == 404:
			printverboseerror("URL " + url + " does not exist.", id)
		elif e.code == 503:
			printverboseerror("The server for " + url + " is unavailable at the moment", id)
		elif e.code == 400:
			printverboseerror("The request is invalid.", id)
		else:
			printverboseerror("Failed opening url, Error " + str(e.code), id)
	except ConnectionRefusedError:
		printverboseerror("The connection got refused, please check PC connection.", id)
	except urllib.error.URLError:
		printverboseerror("The connection got refused, please check PC connection.", id)
	except Exception:
		printverboseerror("Failed downloading pdf. ", id)
		printverboseerror(traceback.format_exc())
		return False

def readYear(data:json, id: int) -> str:
	try:
		if 'published' in data['message']:
			detectedDate = str(data['message']['published']['date-parts'][0][0])
			if detectedDate[0:4].isdigit():
				detectedDate = detectedDate[0:4]
				printverbose("Found year: " + printgreen(detectedDate), id)
				return detectedDate
			else:
				return None
		elif 'issued' in data['message']:
			detectedDate = str(data['message']['published']['date-parts'][0][0])
			if detectedDate[0:4].isdigit():
				detectedDate = detectedDate[0:4]
				printverbose("Found year: " + printgreen(detectedDate), id)
				return detectedDate
			else:
				return None
		else:
			printverbosewarning("No year was detected.", id)
			return None
	except Exception:
		printverboseerror("Failed reading year. ", id)
		printverboseerror(traceback.format_exc(), id)


def readAbstract(data: json, id: int) -> str:
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
			printverbose("Found abstract: " + printgreen(abstract_raw[0:80] + "..."), id)
			return abstract_raw
		else:
			printverbosewarning("No abstract was found online.", id)
			return None
	except Exception:
		printverboseerror("Failed reading abstract. ", id)
		printverboseerror(traceback.format_exc(), id)


def readReferenceType(data: json, id: int) -> str:
	try:
		if 'DOI' in data['message']:
			id = data['message']['DOI']
		else:
			id = data['message']['title'][:20]
		if 'type' in data['message']:
			type = str(data['message']['type'])
			printverbose("Found type " + printgreen(type), id)
			return type
		else:
			printverbosewarning("No type was found online", id)
			return None
	except Exception as e:
		printverboseerror("Failed reading type. " + str(e))

def readJournal(data, id: int) -> str:
	try:
		if 'container-title' in data['message']:
			journal = str(data['message']['container-title'])
			journal = journal[2:]
			journal = journal[:-2]
			printverbose("Found journal: " + printgreen(journal), id)
			return journal
		else:
			printverbosewarning("No journal was found online", id)
			return None
	except Exception as e:
		printverboseerror("Failed reading journal. " + str(e), id)

def readLanguage(data, id: int) -> str:
	try:
		if 'language' in data['message']:
			language = str(data['message']['language'])
			printverbose("Found language: " + printgreen(language), id)
			return language
		else:
			printverbosewarning("No language was found online", id)
			return None

	except Exception as e:
		printverboseerror("Failed reading language. " + str(e), id)

def readPublisher(data, id: int) -> str:
	try:
		if 'publisher' in data['message']:
			publisher = str(data['message']['publisher'])
			printverbose("Found publisher: " + printgreen(publisher), id)
			return publisher
		else:
			printverbosewarning("No publisher was found online", id)
			return None
	except Exception as e:
		printverboseerror("Failed reading language. " + str(e))

def readAuthors(data, id: int) -> list[dict]:
	try:
		if 'author' in data['message']:
			authorlist = []
			for author in data['message']['author']:
				if author['sequence'] == "first":
					if 'family' and 'given' in author:
						authorlist.append({'name': author['family'] + ", " + author['given'], 'sequence': "first"})
						printverbose("Found first author: " + printgreen(author['family'] + ", " + author['given']), id)
					elif 'family' in author:
						authorlist.append({'name': author['family'], 'sequence': "first"})
						printverbose("Found first author: " + printgreen(author['family']), id)
					elif 'name' in author:
						authorlist.append({'name': author['name'], 'sequence': "first"})
						printverbose("Found first author: " + printgreen(author['name']), id)						
				elif author['sequence'] == "additional":
					if 'family' and 'given' in author:
						authorlist.append({'name': author['family'] + ", " + author['given'], 'sequence': "additional"})
						printverbose("Found additional author: " + printgreen(author['family'] + ", " + author['given']), id)
					elif 'family' in author:
						authorlist.append({'name': author['family'], 'sequence': "additional"})
						printverbose("Found additional author: " + printgreen(author['family']), id)
					elif 'name' in author:
						authorlist.append({'name': author['name'], 'sequence': "additional"})
						printverbose("Found additional author: " + printgreen(author['name']), id)
				else:
					if 'family' and 'given' in author:
						authorlist.append({'name': author['family'] + ", " + author['given']})
						printverbose("Found author: " + printgreen(author['family'] + ", " + author['given']), id)
					elif 'family' in author:
						authorlist.append({'name': author['family']})
						printverbose("Found author: " + printgreen(author['family']), id)
					elif 'name' in author:
						authorlist.append({'name': author['name']})
						printverbose("Found author: " + printgreen(author['name']), id)
			return authorlist
		else:
			printverbosewarning("No author was found online", id)
			return None

	except Exception as e:
		printverboseerror("Failed reading author. " + str(e), id)

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

def checkEntry(resultInfo: resultInfo) -> resultInfo:
	global verboseoutput
	global getPDF
	global askConfirm
	global noreverse
	if resultInfo.args.verbose:
		verboseoutput = True
	if resultInfo.args.confirm:
		askConfirm = True
	if resultInfo.args.getpdf:
		getPDF = True
	if resultInfo.args.noreverse:
		noreverse = True

	# Check if DOI
	id = resultInfo.id
	if 'doi' in resultInfo.ris:
		printverbose("Reading info for DOI " + printblue(resultInfo.ris['doi'])), id
		return doAnalysis(resultInfo)
	elif noreverse == True:
		printverbosewarning("No DOI found, reverse lookup is disabled.")
		return resultInfo
	elif 'title' and 'authors' in resultInfo.ris: # Do reverse search with title and author
		try:
			# Encode title
			title = str(resultInfo.ris['title'])
			logMessage = "No DOI detected, starting reverse search with title " + printblue(title[:50] + "...")

			# Get first author
			firstAuthor = str(resultInfo.ris["authors"][0])		
			if firstAuthor:
				logMessage += " and author " + printblue(firstAuthor + ".")
			printverbose(logMessage, id)
			doi = getCrossrefReverse(title, firstAuthor, id)
			if doi:
				resultInfo.successfullReverseChecks +=1
				resultInfo.ris['doi'] = doi
				return doAnalysis(resultInfo)
			else:
				resultInfo.notFound +=1
				printverbosewarning("Document could not be matched.", id)
				return resultInfo
		except:
			printverboseerror("Failed reverse engineering the entry.", id)
			printverboseerror(traceback.format_exc()), id
			return resultInfo

	else: #Nothing could be matched
		printverbosewarning("Document could not be matched.")
		resultInfo.notFound +=1
		return resultInfo


def doAnalysis(resultInfo: resultInfo) -> dict:
	"""
	Perform the actual analysis.
	:param dict: The dictionary entry from RIS
	"""
	id = resultInfo.id
	try:
		doi = str(resultInfo.ris['doi'])
		jsoninfo = getCrossref(doi, id)
		if not jsoninfo: #Crossref returned 404
			resultInfo.notFound +=1
			return resultInfo
		if not 'abstract' in resultInfo.ris:
			printverbose("No abstract was detected, searching online.", id)
			abstract = readAbstract(jsoninfo, id)
			if abstract:
				# Add abstract to dictionary
				resultInfo.ris['abstract'] = abstract
				resultInfo.foundAbstract +=1
				resultInfo.foundAbstract +=1
		if not 'type_of_reference' in resultInfo.ris:
			printverbose("No reference type was detected, searching online.", id)
			type = readReferenceType(jsoninfo, id)
			if type:
				# Add type to dictionary
				resultInfo.ris['type_of_reference'] = type
				resultInfo.foundItems +=1
				resultInfo.foundReferenceType +=1
		if not 'journal_name' and not 'alternate_title3' and not 'alternate_title2' in resultInfo.ris:
			printverbose("No journal title was detected, searching online.", id)
			journal = readJournal(jsoninfo, id)
			if journal:
				# Add journal to dictionary
				resultInfo.ris['journal_name'] = journal
				resultInfo.foundItems +=1
				resultInfo.foundJournal +=1
		if not 'language' in resultInfo.ris:
			printverbose("No document language was detected, searching online.", id)
			language = readLanguage(jsoninfo, id)
			if language:
				# Add language to dictionary
				resultInfo.ris['language'] = language
				resultInfo.foundItems +=1
				resultInfo.foundLanguage +=1
		if not 'access_date' in resultInfo.ris:
			printverbose("No access date was detected, adding todays date.", id)
			resultInfo.ris['access_date'] = str(date.today())
		if not 'publisher' in resultInfo.ris:
			printverbose("No publisher was detected, searching online.", id)
			publisher = readPublisher(jsoninfo, id)
			if publisher:
				# Add publisher to dictionary
				resultInfo.ris['publisher'] = publisher
				resultInfo.foundItems +=1
				resultInfo.foundPublisher +=1
		if not 'year' in resultInfo.ris:
			printverbose("No publishing year was detected, searching online.", id)
			year = readYear(jsoninfo, id)
			if year:
				resultInfo.ris['year'] = year
				resultInfo.foundItems +=1
				resultInfo.foundYear +=1
		if not 'authors' and not 'first_authors' and not 'secondary_authors' and not 'subsidiary_authors' in resultInfo.ris:
			printverbose("No author was detected, searching online.", id)
			authors = readAuthors(jsoninfo, id)
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
				resultInfo.ris['authors'] = otherAuthors
				resultInfo.ris['first_authors'] = firstAuthors
				resultInfo.ris['second_authors'] = additionalAuthors
				resultInfo.foundItems +=1
				resultInfo.foundAuthors +=1
		if 'authors' or 'first_authors' or 'secondary_authors' or 'subsidiary_authors' in resultInfo.ris:
			printverbose("Authors were detected, searching online for additions.", id)
			authors = readAuthors(jsoninfo, id)
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
					resultInfo.foundAuthors +=1			
				if askConfirm == True:
					currentAuthors = []
					# Add all current author to one string
					if resultInfo.ris.get('authors'):
						currentAuthors.append(resultInfo.ris.get('authors'))
					if resultInfo.ris.get('first_authors'):
						currentAuthors.append(resultInfo.ris.get('first_authors'))
					if resultInfo.ris.get('secondary_authors'):
						currentAuthors.append(resultInfo.ris.get('secondary_authors'))
					if resultInfo.ris.get('subsidiary_authors'):
						currentAuthors.append(resultInfo.ris.get('subsidiary_authors'))

					# Add all new authors to string
					newAuthors = firstAuthors + additionalAuthors + otherAuthors
					currentAuthorsString = ""
					newAuthorsString = ""
					for cA in currentAuthors:
						currentAuthorsString += str(cA)
					for nA in newAuthors:
						newAuthorsString += str(nA)
					print("Current authors: " + currentAuthorsString, id)
					print("New authors: " + newAuthorsString, id)
					choice = query_yes_no("Replace authors?")
					if choice == True:
						resultInfo.ris['authors'] = otherAuthors
						resultInfo.ris['first_authors'] = firstAuthors
						resultInfo.ris['secondary_authors'] = additionalAuthors
				else:
						resultInfo.ris['authors'] = otherAuthors
						resultInfo.ris['first_authors'] = firstAuthors
						resultInfo.ris['secondary_authors'] = additionalAuthors
				resultInfo.foundItems +=1
		
		# Add URLs
		urllist = []
		if 'url' in resultInfo.ris:
			for url in resultInfo.ris['url']:
				urllist.append(url)
		additionalURLs = getUrls(jsoninfo, id)
		if additionalURLs:
			for url in additionalURLs:
				if url not in urllist:
					urllist.append(url)
					printverbose("Found document URL: " + printgreen(url), id)
					resultInfo.foundUrl +=1
					resultInfo.foundItems +=1
		
		# Set url in resultInfo.ris
		if len(urllist) > 0:
			resultInfo.ris['url'] = set(urllist) # Remove duplicate url

		if getPDF == True:
			if 'url' or 'file_attachments1' or 'file_attachments2' in resultInfo.ris:
				resultInfo.downloadedPdfs = downloadPDF(urllist,str(resultInfo.ris['title']), resultInfo)
			else:
				resultInfo.downloadedPdfs = 0
		else:
				resultInfo.downloadedPdfs = 0

		# Clean the year strings
		resultInfo = cleanRISYear(resultInfo, id)


		# Add dict resultInfo.ris to new list
		return resultInfo
	except Exception as ex:
		printerror("An error occured for analysis.")
		if 'doi' in resultInfo.ris:
			printerror("DOI: " + str(resultInfo.ris['doi']))
		printverboseerror(traceback.format_exc())
		return resultInfo
			
def getUrls(jsoninfo: json, id="") -> list:
	try:
		urls = []
		if 'link' in jsoninfo['message']:
			for url in jsoninfo['message']['link']:
				if url['content-type'] == "application/pdf":
					urls.append(url['URL'])
				elif url['content-type'] == "unspecified":
					urls.append(url['URL'])
				else:
					printverbosewarning("Crossref did not return any PDF urls.", id)
			return urls
		else:
			printverbosewarning("Crossref couldn't find any urls.", id)
			return None
	except Exception:
		printverboseerror("Failed retrieving URL.", id)
		printverboseerror(traceback.format_exc(), id)
		return None

def importRis(filepath: str) -> list[dict]:
	p = Path(filepath)

	# Overwrite rispy default list, as rispy only works with one url per document
	
	try:
		rispy.LIST_TYPE_TAGS.extend(["UR", "M1", "L1", "L2"])
		entries = rispy.load(p, encoding='utf-8')
		print("Detected " + printblue(str(len(entries))) + " items in ris file.")
		return entries
	except OSError as e:
		printerror("RIS is not properly formatted, probably missing article type.")
		printerror(traceback.format_exc())
		return None
	except Exception as e:
		printerror(str(e))
		printerror(traceback.format_exc())
		return None



if __name__ == "__main__":
		# Parse Arguments
	parser = ArgumentParser()
	parser.add_argument("--verbose", help="Print detailed output.", action="store_true")
	parser.add_argument("--confirm", help="Ask confirmation before replacing details.", action="store_true")
	parser.add_argument("--getpdf", help="Try to download pdf if available.", action="store_true")
	parser.add_argument("--noreverse", help="Disable the reverse lookup if no DOI is present.", action="store_true")
	parser.add_argument("--processes", help="Set the number of processes (be careful).", action="store", type=int)
	parser.add_argument("--input", help='Define filepath for input RIS.', type=str)
	parser.add_argument("--output", help='Define filepath for output RIS.', type=str)
	args = parser.parse_args()

	# Get filepath to RIS file
	filepathOriginal = ""
	while not filepathOriginal:
		if args.input:
			filepathOriginal = args.input
		else:
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
		if args.output:
			filepathResult = args.output
		else:
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
		entries = importRis(filepathOriginal)
		if entries == None:
			exit(4)
		totalCount = len(entries)

		inputList = []
		for i in entries:
			entry = resultInfo()
			entry.ris = i
			entry.foundItems = 0
			entry.total = len(entries)
			entry.id = entries.index(i) + 1
			entry.filepathResult = filepathResult
			entry.args = args
			inputList.append(entry)

		results: list[resultInfo]

		if not args.processes:
			if totalCount > os.cpu_count() * 4:
				processes_count = os.cpu_count()* 4
			else:
				processes_count = totalCount
		else: 
			printwarning("Will overwrite default processes count with " + str(args.processes))
			processes_count = args.processes
		print("Launching " + str(processes_count) + " processes, please wait.")
		with WorkerPool(n_jobs=processes_count) as pool:
			results = pool.map(checkEntry, inputList, progress_bar=not args.verbose, progress_bar_options={'desc': 'Analyzing RIS', 'unit': 'entries', 'ascii': ' █'})

		
		# Now write entries into output file
		print()
		print("Done with reading all entries, processed " + printgreen(str(len(results))) + " entries.")
		print("Now saving file to " + printblue(str(filepathResult)))

		# Get Timestamp
		now = datetime.now() # current date and time
		timestamp = now.strftime("%Y%m%d%H%M%S")

		foundItems = 0
		foundAbstract = 0
		foundReferenceType = 0
		foundJournal = 0
		foundYear = 0
		foundUrl = 0
		foundAuthors = 0
		foundLanguage = 0
		foundPublisher = 0
		successfullReverseChecks = 0
		downloadedPdfs = 0
		notFound = 0
		noDOI = 0
		finalentries = []
		for i in results:
			try:
				foundItems += i.foundItems
				foundAbstract += i.foundAbstract
				foundReferenceType += i.foundReferenceType
				foundJournal += i.foundJournal
				foundUrl += i.foundUrl
				foundAuthors += i.foundAuthors
				foundYear += i.foundYear
				foundLanguage += i.foundLanguage
				foundPublisher += i.foundPublisher
				successfullReverseChecks += i.successfullReverseChecks
				if downloadedPdfs is not None:
					downloadedPdfs += i.downloadedPdfs
				notFound += i.notFound
				noDOI += i.noDOI
				finalentries.append(i.ris)
			except:
				printerror("Item " + str(i+1) + " is empty.")
				printerror(traceback.format_exc())
		
		try:
			with open(os.path.join(str(filepathResult), 'output_' + timestamp + '.ris'), 'w', encoding="utf-8") as bibliography_file:
				rispy.dump(finalentries, bibliography_file)
		except Exception as ex:
			printerror("Failed saving file. " + str(ex))
			
		print(printgreen("Done! ") + "We have added " + printblue(str(foundItems)) + " categories to the list.")
		print("Added abstracts:\t" + printgreen(str(foundAbstract)))
		print("Added reference types:\t" + printgreen(str(foundReferenceType)))
		print("Added journal names:\t" + printgreen(str(foundJournal)))
		print("Added document urls:\t" + printgreen(str(foundUrl)))
		print("Added languages:\t" + printgreen(str(foundLanguage)))
		print("Added authors:\t\t" + printgreen(str(foundAuthors)))
		print("Addes years:\t\t" + printgreen(str(foundYear)))
		if args.getpdf == True:
			print("Downloaded PDFs:\t" + printgreen(str(downloadedPdfs)))
		print("Reverse checks:\t\t" + printgreen(str(successfullReverseChecks)))
		print("Articles not found:\t" + printyellow(str(notFound)))
		input("Press enter to exit.")
	except Exception as ex:
		printerror("Error opening file")
		printerror(traceback.format_exc())
		input("Press enter to exit.")