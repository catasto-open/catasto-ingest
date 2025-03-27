# Catasto Ingest

## Analysis

- file types:
  - census
    - .FAB (FABBRICATI)
    - .TER (TERRENI)
    - .SOG (SOGGETTI)
    - .TIT (TITOLARITA')
    - SC.DAT (PLANIMETRIE)
    - DM.DAT (PLANIMETRIE)
  - geographic
    - .CXF
      - BORDI
      - TESTI
      - SIMBOLI
      - FIDUCIALI
      - LINEE
    - .SUP
- files structure
  - file_cxf ➡️ *.zip con i file CXF e SUP
  - immobili ➡️ *.zip con i file FAB, TER, SOG, TIT e PRM
  - planimetrie ➡️ *.zip con i file *_DM.DAT, *_SC.DAT e i TIF delle planimetrie da convertire in PDF (anche come file compresso nidificato all'interno del file ZIP principale)
  - processati
    - file_cxf
    - immobili
    - planimetrie

## Now to have a NATS server locally for testing

If you have docker installed, run:

```
docker run -p 4222:4222 nats -js
```