# Airfoil Tools

[![Release EXE](https://img.shields.io/github/v/release/giuliodori/airfoil-tools)](dist/airfoil-tools.exe)
[![License](https://img.shields.io/github/license/giuliodori/airfoil-tools)](LICENSE)

Airfoil Tools e' una GUI desktop per generare profili NACA a 4 cifre, esportarli in `.pts` e `.dxf`, e stimare `lift` e `drag`.

![gui](images/gui.png)
![Manta](images/manta.jpg)

## Installazione semplice (exe consigliato)

Per la maggior parte degli utenti e' sufficiente l'eseguibile.

### 1) Download

Scarica la cartella con l'eseguibile da GitHub:

```text
https://github.com/giuliodori/airfoil-tools/releases/latest
```

Se hai clonato o scaricato lo ZIP del repository, il file principale su Windows e':
- `airfoil-tools\dist\airfoil-tools.exe`

### 2) Avvio

- Fai doppio click su `airfoil-tools\dist\airfoil-tools.exe`.
- La GUI si apre e puoi subito generare ed esportare i profili.

Avvio rapido alternativo dalla cartella del repository:
- Doppio click su `airfoil-tools.bat`

## Codice sorgente Python (opzionale)

Usa questa sezione solo se vuoi eseguire da sorgente.

### Requisiti (solo sorgente)

- Python 3.10+
- `numpy`
- `matplotlib`
- `ezdxf` (necessario per l'export `.dxf`)

Installa le dipendenze:

```bash
python -m pip install numpy matplotlib ezdxf
```

Esegui:

```bash
python airfoil_tools.py
```

Su Windows puoi anche usare:
- `airfoil-tools.bat`

## Esempi di CAD per `.pts` e `.dxf`

### CAD/3D con supporto DXF

- AutoCAD
- CREO Parametric
- Fusion 360
- Inventor
- SolidWorks
- FreeCAD
- Rhino
- BricsCAD
- DraftSight
- QCAD
- LibreCAD
- Onshape (workflow DXF)

### Software per file di punti (`.pts`/XYZ)

- CloudCompare
- MeshLab
- MATLAB
- GNU Octave
- Python (NumPy / Pandas)
- CATIA (import punti)
- Siemens NX (import punti)
- Autodesk Alias (point set)

## Note sui profili NACA 4 cifre

I profili NACA 4 cifre sono una famiglia storica di profili alari definita da quattro numeri che descrivono in modo semplice la geometria. Sono ancora molto usati per studio preliminare, didattica e comparazioni rapide.

### Significato delle cifre

Le quattro cifre sono `M P TT`:

- `M` (prima cifra) e' il massimo camber in percentuale della corda.
- `P` (seconda cifra) e' la posizione del massimo camber in decimi di corda.
- `TT` (ultime due cifre) e' lo spessore massimo in percentuale della corda.

Esempio:

`NACA 2412` significa camber massimo 2% a 40% di corda, spessore 12%.

### Quali profili sono piu' usati e per dove

Profili simmetrici (camber zero) per applicazioni dove serve comportamento simmetrico:

- `NACA 0012` e `NACA 0015` per superfici di coda, timoni e profili generici.

Profili con camber moderato per ali e piccoli velivoli:

- `NACA 2412` e `NACA 4412` per ali leggere e applicazioni generiche dove serve buona portanza.

Profili piu' spessi per robustezza strutturale o basse velocita':

- `NACA 0018` e `NACA 4418` per strutture con vincoli di spessore o Reynolds piu' bassi.

## Licenza

Questo progetto e' rilasciato con doppia licenza:

- GNU General Public License v3.0 (GPL-3.0-only) per uso open-source
- Licenza commerciale per uso proprietario o closed-source

Per licenze commerciali:
- info@duilio.cc
