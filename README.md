# GetRISInfos
This python program grabs an _.ris_ file (multiple entries possible), scans every entry and adds missing info to the entry. As source the [Crossref API](https://api.crossref.org) is being used. To work, each RIS entry must have a valid DOI number.

## Added data
Currently supported data to be added are:
- Abstract
- Type of reference (book, journal)
- Journal name
- Document URL
- Language

## How to use
1. Provide filepath of _.ris_ rile (eg. C:\Users\Max\test.ris)
2. Provide output path (eg. C:\Users\Max\)
3. Wait until finished

## Options
Use ```-v``` parameter to print verbose logging.

## Todo
- [ ] Add multithreading
- [ ] Add module installer file
- [ ] Add return header check (current limit of API is 50r/s)