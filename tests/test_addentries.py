import pytest
from pathlib import Path
from src import getRISinfos
import json

data_DIR = Path(__file__).parent.resolve() / "data"
f = open(data_DIR / "crossrefresult.json")
data1 = json.load(f) 

g = open(data_DIR / "crossrefresult2.json")
data2 = json.load(g) 

def testYear():
    assert getRISinfos.readYear(data1, id=0) == "2002"
    assert getRISinfos.readYear(data2, id=0) == "2017"

def testAbstract():
    abstract = getRISinfos.readAbstract(data1, id=0)
    assert abstract.startswith("Automatic processing of seismic data is") == True
    abstract2 = getRISinfos.readAbstract(data2, id=0)
    assert abstract2.startswith("Die Digitalisierung ist im produzierenden Gewerbe") == True

def testreadReferenceType():
    assert getRISinfos.readReferenceType(data1, id=0) == "journal-article"
    assert getRISinfos.readReferenceType(data2, id=0) == "journal-article"

def testreadJournal():
    assert getRISinfos.readJournal(data1, id=0) == "Discrete Dynamics in Nature and Society"
    assert getRISinfos.readJournal(data2, id=0) == "Zeitschrift für wirtschaftlichen Fabrikbetrieb"

def testLanguage():
    assert getRISinfos.readLanguage(data1, id=0) == "en"
    assert getRISinfos.readLanguage(data2, id=0) == "en"

def testpublisher():
    assert getRISinfos.readPublisher(data1, id=0) == "Hindawi Limited"
    assert getRISinfos.readPublisher(data2, id=0) == "Walter de Gruyter GmbH"

def testAuthors():
    authorList = [{"name": "Antoniou, I.", "sequence": "first"}, {"name": "Ivanov, V. V.", "sequence": "additional"}, {"name": "Kisel, I. V.", "sequence": "additional"}]
    detectedAuthors = getRISinfos.readAuthors(data1, id=0)
    assert detectedAuthors == authorList

    authorList2 = [{"name": "Hönig, Hannes", "sequence": "first"}, {"name": "Lorenz, Björn", "sequence": "additional"}]
    detectedAuthors2 = getRISinfos.readAuthors(data2, id=0)
    assert detectedAuthors2 == authorList2