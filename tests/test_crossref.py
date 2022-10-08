import pytest
from pathlib import Path
from src import getRISinfos

DATA_DIR = Path(__file__).parent.resolve() / "data"

def testCrossrefDownload():
    result = getRISinfos.getCrossref("10.3390/joitmc6040104", 0)
    assert result['status'] == 'ok'
    result = getRISinfos.getCrossref("10.339104", 0)
    assert result == None

def testCrossrefReverseTitleOnly():
    result = getRISinfos.getCrossrefReverse("Identifying Digital Transformation Paths in the Business Model of SMEs during the COVID-19 Pandemic", None, 0)
    assert result == "10.3390/joitmc6040104"
    assert result != "blabla"

def testCrossrefReverseTitleAndAuthor():
    result = getRISinfos.getCrossrefReverse("Identifying Digital Transformation Paths in the Business Model of SMEs during the COVID-19 Pandemic", "Anjar Priyono", 0)
    assert result == "10.3390/joitmc6040104"
    assert result != "blabla"

def testCrossrefNoMatch():
    result = getRISinfos.getCrossrefReverse("This is a useless title", "Anjar Priyono", 0)
    assert result == None

def testisPDF():
    source = DATA_DIR / "importSingle.ris"
    entry = getRISinfos.importRis(source)[0]
    assert getRISinfos.isPDF(entry["url"][0]) == False
    assert getRISinfos.isPDF(entry["url"][1]) == True

def testCleanYearStr():
    source = DATA_DIR / "importSingle.ris"
    entry = getRISinfos.importRis(source)[0]
    resInfo = getRISinfos.resultInfo
    resInfo.ris = entry
    newresInfo = getRISinfos.cleanRISYear(resInfo)
    assert newresInfo.ris['year'] == "2020"

def testCleanPY():
    y1 = "2017"
    y2 = "2018//"
    y3 = "2019///"
    y4 = "blabla"
    assert getRISinfos.cleanDateStr(y1) == "2017"
    assert getRISinfos.cleanDateStr(y2) == "2018"
    assert getRISinfos.cleanDateStr(y3) == "2019"
    assert getRISinfos.cleanDateStr(y4) == "blabla"