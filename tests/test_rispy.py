import pytest
from pathlib import Path
from src import getRISinfos

DATA_DIR = Path(__file__).parent.resolve() / "data"

def testImport():
    source = DATA_DIR / "importSingle.ris"
    entries = getRISinfos.importRis(source)
    assert len(entries) == 1
    assert entries[0]['doi'] == "10.3390/joitmc6040104"

def testImportMultiple():
    source = DATA_DIR / "importMultiple.ris"
    entries = getRISinfos.importRis(source)
    assert len(entries) == 3
    assert entries[0]['doi'] == "10.1108/JKM-08-2016-0357"
    assert entries[1]['title'] == "Blockchain, bank credit and SME financing"
    assert entries[2]['url'][0] == "https://www.tandfonline.com/doi/abs/10.1080/10919392.2018.1484598"
    assert entries[2]['url'][1] == "https://www.researchgate.net/profile/Salah-Kabanda-2/publication/326385562_Exploring_SME_cybersecurity_practices_in_developing_countries/links/5cd56c2ea6fdccc9dd9d5ae4/Exploring-SME-cybersecurity-practices-in-developing-countries.pdf"

    