# Modularno Vizualizacijsko okolje

Omogoča dodajanje funkcionalnosti v okolje na modularen način. Vsak modul je lahko namenjen prikazu objektov ali drugim 
funkcijam in vsaka implementirana funkcionalnost je lahko sestavljena iz enega ali večih modulov. 
Posamezen modul lahko hkrati uporablja več funkcionalnosti.

Ogrodje trenutno obsega:
* [DisplayManager.ts](src/DisplayManager.ts), ki vsebuje nadzor nad kamero, zaznavanje klikov objektov in metode za dodajanje modulov in funkcionalnosti.
* [BaseClasses.ts](src/BaseClasses.ts), ki vsebuje osnovni abstraktni razred za module
* [Environment.ts](src/Environment.ts), ki vsebuje abstraktno implementacijo modula za nalaganje OBJ/MTL datotek, z možnostjo vezanja dogodkov na objekte.
* [Feature.ts](src/Feature.ts), ki vsebuje razrede za implementacijo funkcionalnosti.

Primere uporabe najdete v [index.html](index.html), [TurnLever.ts](src/turn_lever/TurnLever.ts) in [CarLoad.ts](src/CarLoad.ts).