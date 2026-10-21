# Védjegykép-ellenőrző

_Felhasználói kézikönyv (Trademark Image Checker, 1.2.0 verzió)_

A kézikönyv két részből áll. Az I. rész a program mindennapi használatát írja le. A II. rész a haladó lehetőségeket mutatja be: a parancssori paramétereket, a nyelv beállítását és a nyelvi fájlt, valamint a feltételfájl felépítését.

## I. Alapvető használat

### 1. Mire való a program?

A Védjegykép-ellenőrző egy képfájlról megállapítja, hogy megfelel-e a beállított feltételeknek (fájlméret, képméret pixelben, felbontás, képtípus), például egy védjegybejelentéshez feltöltendő kép követelményeinek. Ha a kép nem felel meg, a program segít beállítani a megfelelő értékeket, majd elkészíti és elmenti az átalakított képet.

### 2. A program indítása

- Kattintson duplán a TrademarkImage.exe fájlra. Python telepítésére nincs szükség.
- Az első indítás néhány másodpercig tarthat, mert a program kicsomagolja magát.
- Ha a Windows SmartScreen figyelmeztet, válassza a „További információ”, majd a „Futtatás mindenképp” lehetőséget (a program nincs digitálisan aláírva).
- Egy képfájlt az exe ikonjára húzva a program azonnal azzal a képpel indul.

A program magyarul indul. A nyelv a főablak jobb felső sarkában, a Nyelv listában bármikor átváltható (Magyar / English); a betöltött kép és a beállított értékek ilyenkor megmaradnak. A nyelv tartós beállítását a 11. fejezet írja le.

### 3. A főablak részei

| Terület | Leírás |
|---|---|
| Nyelv (jobb felső sarok) | A felület nyelvének kiválasztása (Magyar / English). |
| Feltételek (bal oldal) | A feltételek beállítása, valamint az Alkalmaz, a Feltételek betöltése... és a Feltételek mentése másként... gomb. Alul látható, melyik fájlból származnak a feltételek. |
| Képterület (jobb felül) | Ide kell behúzni a képet; betöltés után a kép előnézete látszik. |
| Képadatok | Fájl, formátum, mód, méret pixelben, felbontás (DPI), fájlméret. |
| Eredmény (jobb alul) | Zöld OK gomb, vagy a nem teljesülő feltételek piros gombjai és az Átalakítás és mentés... gomb. |

### 4. Kép betöltése

1. Húzza a képfájlt a Windows Intézőből a „Húzzon ide egy képet” feliratú területre, vagy
2. kattintson a területre, és válassza ki a képet a megnyíló ablakban.

Olvasható formátumok: JPEG, PNG, TIFF, BMP, GIF, WebP és a Pillow könyvtár által ismert egyéb formátumok. Ha a fájl nem kép, hibaüzenet jelenik meg.

### 5. Az ellenőrzés eredménye

#### 5.1 A kép megfelel

Ha minden feltétel teljesül, egy zöld gomb jelenik meg: „OK - a kép minden feltételnek megfelel (kattintson a kilépéshez)”. Erre kattintva a program bezárul, a képen nem változtat semmit.

#### 5.2 A kép nem felel meg

Minden nem teljesülő feltételhez egy piros gomb tartozik, amelyen a feltétel neve, a kép jelenlegi értéke és zárójelben a követelmény olvasható, például: „Szélesség: 4000 px (945-2835 px)”. A lehetséges gombok: Fájlméret, Szélesség, Magasság, Felbontás, Képtípus és JPEG kódolás. A felbontásnál „nincs megadva” látható, ha a fájl nem tárol DPI értéket.

### 6. A hibás értékek javítása

1. Kattintson egy piros gombra. Megnyílik egy ablak, amely mutatja a jelenlegi értéket és a követelményt, az Új érték mező pedig egy megfelelő javaslattal van kitöltve.
2. Írja be (vagy fogadja el) a kívánt értéket, és nyomja meg az OK gombot.
3. Ha az érték megfelel a feltételnek, a gomb fehér lesz, és az új értéket mutatja (pl. „Szélesség: 4000 px -> 2800 px”). Ha nem felel meg, hibaüzenet jelenik meg, és az ablak nyitva marad. A Mégse gombbal a változtatás elvethető, a gomb piros marad.

- **Szélesség, magasság:** a „Méretarány megtartása” jelölőnégyzet bekapcsolva (alapértelmezés) a másik méretet is arányosan módosítja, így a kép nem torzul. Ha emiatt a másik méret kerül a megengedett tartományon kívülre, arra is megjelenik egy piros gomb. A felajánlott értékek - ha lehetséges - megtartják a képarányt.
- **Felbontás:** egész szám DPI-ben, a legkisebb és a legnagyobb felbontás között (alapesetben 96-600 DPI). A felbontás csak a fájlban tárolt adat, a pixelméretet nem változtatja.
- **Fájlméret:** a megengedett legnagyobb méret MB-ban (tizedesvessző és -pont is használható). A program a mentéskor szükség esetén csökkenti a JPEG minőséget, illetve a képméretet, hogy a fájl beleférjen.
- **Képtípus:** a listából választható ki a megengedett típusok egyike.
- **JPEG kódolás:** progresszív JPEG esetén válassza az „alap (baseline)” értéket; a program a képet alap JPEG-ként menti újra.

### 7. Átalakítás és mentés

Amikor az utolsó piros gomb is fehér lesz, a program automatikusan megnyitja a mentési ablakot. Ha ezt megszakítja, később az „Átalakítás és mentés...” gombbal indíthatja újra.

- Az alapértelmezett formátum az eredeti fájl formátuma (ha az a választott képtípust tárolni tudja), az alapértelmezett fájlnév „\<eredeti név>_atalakitott”.
- A formátumot a fájltípus-listából vagy a kiterjesztéssel (.jpg, .png, .tif, .bmp) lehet megadni.
- Ha a formátum nem tudja tárolni a képtípust (pl. CMYK képet PNG-be), a program jelzi, mely formátumok megfelelőek, és újra megnyitja a mentési ablakot.
- Mentés után a program újra ellenőrzi az elkészült fájlt, kiírja az eredményt (méret, fájlméret, JPEG minőség), és betölti az új képet - ha minden rendben, megjelenik a zöld OK gomb.

| Formátum | Tárolható képtípusok | Megjegyzés |
|---|---|---|
| JPEG (.jpg) | RGB, szürkeárnyalatos, CMYK | Veszteséges, kis fájlméret - általában ez ajánlott |
| PNG (.png) | RGB, RGBA, szürkeárnyalatos, fekete-fehér, palettás | Veszteségmentes |
| TIFF (.tif) | mind | Veszteségmentes tömörítés |
| BMP (.bmp) | RGB, szürkeárnyalatos, fekete-fehér, palettás | Tömörítetlen, nagy fájlok |

Átalakításkor a JPEG fájlok mindig alap (nem progresszív) kódolással készülnek, az átlátszó részek fehér hátteret kapnak (kivéve RGBA típus esetén), a fekete-fehér átalakítás 50%-os küszöbbel történik, a kép pedig a fényképezőgép által tárolt tájolás szerint elforgatásra kerül.

### 8. A feltételek beállítása

| Mező | Alapérték |
|---|---|
| Legnagyobb fájlméret (MB) | 2 (1 MB = 1 048 576 bájt) |
| Legkisebb szélesség (px) | 945 |
| Legkisebb magasság (px) | 945 |
| Legnagyobb szélesség (px) | 2835 |
| Legnagyobb magasság (px) | 2010 |
| Legkisebb felbontás (DPI) | 96 |
| Legnagyobb felbontás (DPI) | 600 |
| Megengedett képtípusok | RGB, szürkeárnyalatos, fekete-fehér, CMYK |
| Progresszív JPEG megengedett | nem (kikapcsolva) |

| Képtípus | Jelentése |
|---|---|
| RGB (színes) | Színes kép |
| RGBA (színes, átlátszó) | Színes kép átlátszósággal |
| szürkeárnyalatos | Szürkeárnyalatos kép |
| fekete-fehér | Kétszínű (fekete-fehér) kép |
| CMYK | Nyomdai színmodellű kép |
| palettás | Legfeljebb 256 színű kép, pl. GIF |

1. Módosítsa a mezőket, majd nyomja meg az Alkalmaz gombot.
2. Ha a feltételek változtak, a program megkérdezi, el akarja-e menteni őket fájlba. Igen válasz esetén a mentési ablak a jelenlegi feltételfájlt (alapesetben criterias.json) ajánlja fel.
3. A betöltött kép ellenőrzése az új feltételekkel automatikusan megismétlődik.

Más feltételkészlet betöltése: Feltételek betöltése... gomb, majd a JSON fájl kiválasztása. Mentés tetszőleges néven: Feltételek mentése másként... gomb. A feltételfájlokról bővebben a 12. fejezet szól.

### 9. Gyakori kérdések és hibaüzenetek

| Üzenet / helyzet | Teendő |
|---|---|
| A kép nem nyitható meg / Nem felismerhető képfájl | A fájl nem kép vagy sérült - válasszon másik fájlt. |
| Érvénytelen érték | A beírt érték nem szám, vagy kívül esik a megengedett tartományon. |
| Érvénytelen feltételek | A Feltételek panel valamelyik mezője hibás (pl. a minimum nagyobb a maximumnál, vagy nincs megengedett képtípus). |
| Nem megfelelő formátum | A választott fájlformátum nem tudja tárolni a képtípust - válasszon a felsorolt formátumok közül. |
| Sikertelen átalakítás ... legkisebb megengedett méret | A kép a megadott fájlméretbe a minimális képméret mellett sem fér bele. Válasszon JPEG formátumot vagy más képtípust. |
| A felbontás „nincs megadva” | A fájl nem tárol DPI értéket; állítson be egyet a Felbontás gombbal. |

---

## II. Haladó használat és testreszabás

### 10. Parancssori paraméterek

A program parancssorból (vagy parancsikonból) paraméterekkel is indítható:

```powershell
TrademarkImage.exe
TrademarkImage.exe kep.jpg
TrademarkImage.exe --config sajat_feltetelek.json kep.jpg
TrademarkImage.exe --lang en
TrademarkImage.exe --locals sajat_szovegek.json
```

| Paraméter | Jelentése |
|---|---|
| --config FÁJL | A feltételeket tartalmazó JSON fájl (alapértelmezés: criterias.json az indítási könyvtárban). Lásd a 12. fejezetet. |
| --lang KÓD | A felület nyelve: hu (magyar) vagy en (angol), illetve bármely további, a locals.json-ba felvett nyelv kódja. Lásd a 11. fejezetet. |
| --locals FÁJL | Saját szövegfájl (alapértelmezés: locals.json az indítási könyvtárban, ha van). |
| KÉP | Induláskor megnyitandó képfájl. |
| -h, --help | Megjeleníti a paraméterek leírását. Angolul: --lang en --help. |
| --version | Megjeleníti a program verziószámát. |

- Az érték egyenlőségjellel is megadható (pl. --lang=en). A szóközt tartalmazó fájlneveket tegye idézőjelek közé.
- Az indítási könyvtár dupla kattintásos indításnál az exe mappája. Parancsikon esetén a parancsikon „Indítás helye” mezője adja meg.
- A súgó egy külön ablakban, a verziószám egy üzenetablakban jelenik meg; ezután a program kilép.

#### 10.1 Hibás paraméterek

A program induláskor ellenőrzi a paramétereket. Ha valamelyik hibás, egy hibaüzenetben felsorolja az összes problémát, és nem indul el. Hibának számít például:

- a --config, a --locals vagy a --lang után hiányzik az érték;
- a megadott fájl nem létezik, mappa, vagy nem megfelelő (pl. kép vagy szövegfájl a --config után);
- ismeretlen nyelvkód a --lang után (az üzenet felsorolja az elérhető nyelveket);
- a megadott kép nem létezik vagy nem kép;
- ismeretlen vagy többször megadott paraméter, illetve egynél több képfájl.

A hibaüzenet a kiválasztott nyelven jelenik meg, és a végén megmutatja, hogyan kérhető súgó. Szkriptekből a kilépési kód is vizsgálható: 0 = rendben, 2 = parancssori hiba.

### 11. A nyelv beállítása és a nyelvi fájl

#### 11.1 A nyelv kiválasztása

- **Futás közben:** a főablak jobb felső sarkában lévő Nyelv listában. A választás csak az adott futásra érvényes.
- **Indításkor:** a --lang paraméterrel, pl. TrademarkImage.exe --lang en.
- **Tartósan:** a locals.json fájlban a "default_language" értékének átírásával (pl. "en").

#### 11.2 A locals.json felépítése

A program összes szövege a locals.json fájlban van, amely az exe mellett található, és Jegyzettömbbel szerkeszthető (UTF-8 kódolással mentse). Felépítése:

```json
{
  "default_language": "hu",
  "languages": {
    "hu": { "language_name": "Magyar",  "prop.width": "Szélesség", ... },
    "en": { "language_name": "English", "prop.width": "Width", ... }
  }
}
```

- Egy szöveg módosításához írja át az idézőjelek közötti értéket a kettőspont után. A kulcsot (a kettőspont előtti részt) ne változtassa meg.
- A kapcsos zárójelben lévő részeket (pl. {value}, {path}) a program tölti ki - ezeket változatlanul hagyja meg. A \n új sort jelent.
- Ha egy szöveg hiányzik egy nyelvből, a program az angol szöveget mutatja. Hibás fájl esetén figyelmeztetést ad, és a beépített szövegekkel dolgozik.
- Elég csak a megváltoztatott szövegeket tartalmazó fájlt az exe mellé tenni: a program a beépített szövegekhez hozzáadja, illetve azokat felülírja vele.

#### 11.3 Új nyelv felvétele

1. Nyissa meg a locals.json fájlt, és másolja le az "en" blokkot.
2. Adjon neki új kódot (pl. "de"), és írja át a "language_name" értékét (pl. "Deutsch").
3. Fordítsa le a szövegeket, majd mentse a fájlt UTF-8 kódolással.
4. A program következő indításakor az új nyelv megjelenik a Nyelv listában.

### 12. A feltételfájl

Induláskor a program az indítási könyvtárban lévő criterias.json fájlból tölti be a feltételeket, vagy a --config paraméterrel megadott fájlból. Ha azt szeretné, hogy a program mindig a saját feltételeivel induljon, mentse őket criterias.json néven az exe mellé (Feltételek mentése másként... gomb). A feltételfájl egyszerű JSON szöveg, Jegyzettömbbel is szerkeszthető:

```json
{
  "max_file_size_mb": 2.0,
  "min_width": 945,
  "min_height": 945,
  "max_width": 2835,
  "max_height": 2010,
  "min_dpi": 96.0,
  "max_dpi": 600.0,
  "allowed_types": ["RGB", "greyscale", "B&W", "CMYK"],
  "allow_progressive_jpeg": false
}
```

| Kulcs | Mező a felületen | Alapérték |
|---|---|---|
| max_file_size_mb | Legnagyobb fájlméret (MB) | 2.0 |
| min_width | Legkisebb szélesség (px) | 945 |
| min_height | Legkisebb magasság (px) | 945 |
| max_width | Legnagyobb szélesség (px) | 2835 |
| max_height | Legnagyobb magasság (px) | 2010 |
| min_dpi | Legkisebb felbontás (DPI) | 96.0 |
| max_dpi | Legnagyobb felbontás (DPI) | 600.0 |
| allowed_types | Megengedett képtípusok | ["RGB", "greyscale", "B&W", "CMYK"] |
| allow_progressive_jpeg | Progresszív JPEG megengedett | false (true = megengedett) |

A képtípusokat a fájlban az azonosítójukkal kell megadni:

| Azonosító a fájlban | Képtípus a felületen |
|---|---|
| RGB | RGB (színes) |
| RGBA | RGBA (színes, átlátszó) |
| greyscale | szürkeárnyalatos |
| B&W | fekete-fehér |
| CMYK | CMYK |
| palette | palettás |

- A hiányzó kulcsok az alapértéket kapják, így elég csak az eltérő értékeket megadni.
- Tizedesponttal kell írni (2.5), a pixelértékek egész számok.
- Ismeretlen kulcs, hibás érték vagy ellentmondás (pl. a minimum nagyobb a maximumnál) esetén: ha a fájlt a --config adta meg, a program hibaüzenettel kilép; az indítási könyvtár criterias.json fájljánál figyelmeztet, és az alapértelmezett feltételekkel indul.

### 13. Hibaelhárítás a haladó beállításoknál

| Üzenet / helyzet | Teendő |
|---|---|
| Parancssori hiba, a program nem indul | Javítsa a hibaüzenetben felsorolt paramétereket (lásd 10.1). A paraméterek leírása: --help. |
| Figyelmeztetés indításkor | Az indítási könyvtárban lévő criterias.json vagy locals.json hibás. A program az alapértelmezett beállításokkal fut. |
| Angol szöveg jelenik meg magyar felületen | A szöveg hiányzik a locals.json magyar részéből - pótolja a hiányzó kulcsot. |
| Kulcs (pl. prop.width) látszik szöveg helyett | A szöveg az angol részből is hiányzik - pótolja. |
| Ékezetes betűk helyett furcsa jelek | Mentse a locals.json-t UTF-8 kódolással. |
