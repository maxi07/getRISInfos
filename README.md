# GetRISInfos
This python program grabs an _.ris_ file (multiple entries possible), scans every entry and adds missing info to the entry. As source the [Crossref API](https://api.crossref.org) is being used.
If a **DOI** is present, we will use this for direct lookup. If no DOI is present, we will try to do an reverse lookup using the **title and author**.

<img src="https://github.com/maxi07/getRISInfos/blob/master/doc/app_screenshot1.png?raw=true" align="center" width="800"/>

## Added data
Currently supported data to be added are:
- Abstract
- Type of reference (book, journal)
- Journal name
- Document URL
- Language
- Download full-text PDF if available
- Authors

## How to use
1. Provide filepath of _.ris_ rile (eg. C:\Users\Max\test.ris)
2. Provide output path (eg. C:\Users\Max\)
3. Wait until finished

## Options
- ```--verbose``` parameter to print verbose logging.
- ```--confirm``` parameter to confirm before replacing data.
- ```--getpdf``` parameter to search for available PDFs and download them.
- ```--noreverse``` parameter to skip reverse lookup.
- ```--processes``` parameter to set number of processes (default is count of your cpu).


## Todo
- [ ] Add return header check (current limit of API is 50r/s)