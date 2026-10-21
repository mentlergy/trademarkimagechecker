# Védjegykép-ellenőrző

_Felhasználói kézikönyv (Trademark Image Checker, 1.1.0 verzió)_

## 1. Mire való a program?

A Védjegykép-ellenőrző egy képfájlról megállapítja, hogy megfelel-e a beállított feltételeknek (fájlméret, képméret pixelben, felbontás, képtípus), például egy védjegybejelentéshez feltöltendő kép követelményeinek. Ha a kép nem felel meg, a program segít beállítani a megfelelő értékeket, majd elkészíti és elmenti az átalakított képet.

## 2. A program indítása

- Kattintson duplán a TrademarkImage.exe fájlra. Python telepítésére nincs szükség.
- Az első indítás néhány másodpercig tarthat, mert a program kicsomagolja magát.
- Ha a Windows SmartScreen figyelmeztet, válassza a „További információ”, majd a „Futtatás mindenképp” lehetőséget (a program nincs digitálisan aláírva).
- Egy képfájlt az exe ikonjára húzva a program azonnal azzal a képpel indul.

Parancssorból további lehetőségek is vannak:

```powershell
TrademarkImage.exe
TrademarkImage.exe kep.jpg
TrademarkImage.exe --config sajat_feltetelek.json kep.jpg
TrademarkImage.exe --lang en
TrademarkImage.exe --locals sajat_szovegek.json
```

| Paraméter | Jelentése |
|---|---|
| --config FÁJL | A feltételeket tartalmazó JSON fájl (alapértelmezés: criterias.json az indítási könyvtárban). |
| --lang KÓD | A felület nyelve: hu (magyar) vagy en (angol), illetve bármely további, a locals.json-ba felvett nyelv kódja. |
| --locals FÁJL | Saját szövegfájl (alapértelmezés: locals.json az indítási könyvtárban, ha van). |
| KÉP | Induláskor megnyitandó képfájl. |

Ha az indítási könyvtárban van criterias.json nevű fájl, a program induláskor abból tölti be a feltételeket. Ha nincs ilyen fájl, az alapértelmezett feltételekkel dolgozik.

## 3. A főablak részei

| Terület | Leírás |
|---|---|
| Nyelv (jobb felső sarok) | A felület nyelvének kiválasztása (Magyar / English). |
| Feltételek (bal oldal) | A feltételek beállítása, valamint az Alkalmaz, a Feltételek betöltése... és a Feltételek mentése másként... gomb. Alul látható, melyik fájlból származnak a feltételek. |
| Képterület (jobb felül) | Ide kell behúzni a képet; betöltés után a kép előnézete látszik. |
| Képadatok | Fájl, formátum, mód, méret pixelben, felbontás (DPI), fájlméret. |
| Eredmény (jobb alul) | Zöld OK gomb, vagy a nem teljesülő feltételek piros gombjai és az Átalakítás és mentés... gomb. |

## 4. A felület nyelve

A program alapértelmezés szerint magyarul indul. A nyelv a főablak jobb felső sarkában, a Nyelv listában bármikor átváltható; ilyenkor a betöltött kép és a már beállított értékek megmaradnak. A választás csak az adott futásra érvényes. Ha a program mindig más nyelven induljon, használja a --lang paramétert, vagy írja át a locals.json fájlban a "default_language" értékét (pl. "en").

### 4.1 Szövegek módosítása, új nyelv felvétele

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
- Új nyelv felvétele: másolja le az "en" blokkot, adjon neki új kódot (pl. "de"), írja át a "language_name" értékét (pl. "Deutsch"), majd fordítsa le a szövegeket. A program következő indításakor az új nyelv megjelenik a Nyelv listában.
- Ha egy szöveg hiányzik egy nyelvből, a program az angol szöveget mutatja. Hibás fájl esetén figyelmeztetést ad, és a beépített szövegekkel dolgozik.
- Elég csak a megváltoztatott szövegeket tartalmazó fájlt az exe mellé tenni: a program a beépített szövegekhez hozzáadja, illetve azokat felülírja vele.

## 5. Kép betöltése

1. Húzza a képfájlt a Windows Intézőből a „Húzzon ide egy képet” feliratú területre, vagy
2. kattintson a területre, és válassza ki a képet a megnyíló ablakban.

Olvasható formátumok: JPEG, PNG, TIFF, BMP, GIF, WebP és a Pillow könyvtár által ismert egyéb formátumok. Ha a fájl nem kép, hibaüzenet jelenik meg.

## 6. Az ellenőrzés eredménye

### 6.1 A kép megfelel

Ha minden feltétel teljesül, egy zöld gomb jelenik meg: „OK - a kép minden feltételnek megfelel (kattintson a kilépéshez)”. Erre kattintva a program bezárul, a képen nem változtat semmit.

### 6.2 A kép nem felel meg

Minden nem teljesülő feltételhez egy piros gomb tartozik, amelyen a feltétel neve, a kép jelenlegi értéke és zárójelben a követelmény olvasható, például: „Szélesség: 4000 px (945-2835 px)”. A lehetséges gombok: Fájlméret, Szélesség, Magasság, Felbontás és Képtípus. A felbontásnál „nincs megadva” látható, ha a fájl nem tárol DPI értéket.

## 7. A hibás értékek javítása

1. Kattintson egy piros gombra. Megnyílik egy ablak, amely mutatja a jelenlegi értéket és a követelményt, az Új érték mező pedig egy megfelelő javaslattal van kitöltve.
2. Írja be (vagy fogadja el) a kívánt értéket, és nyomja meg az OK gombot.
3. Ha az érték megfelel a feltételnek, a gomb fehér lesz, és az új értéket mutatja (pl. „Szélesség: 4000 px -> 2800 px”). Ha nem felel meg, hibaüzenet jelenik meg, és az ablak nyitva marad. A Mégse gombbal a változtatás elvethető, a gomb piros marad.

- **Szélesség, magasság:** a „Méretarány megtartása” jelölőnégyzet bekapcsolva (alapértelmezés) a másik méretet is arányosan módosítja, így a kép nem torzul. Ha emiatt a másik méret kerül a megengedett tartományon kívülre, arra is megjelenik egy piros gomb. A felajánlott értékek - ha lehetséges - megtartják a képarányt.
- **Felbontás:** egész szám DPI-ben. A felbontás csak a fájlban tárolt adat, a pixelméretet nem változtatja.
- **Fájlméret:** a megengedett legnagyobb méret MB-ban (tizedesvessző és -pont is használható). A program a mentéskor szükség esetén csökkenti a JPEG minőséget, illetve a képméretet, hogy a fájl beleférjen.
- **Képtípus:** a listából választható ki a megengedett típusok egyike.

## 8. Átalakítás és mentés

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

Átalakításkor az átlátszó részek fehér hátteret kapnak (kivéve RGBA típus esetén), a fekete-fehér átalakítás 50%-os küszöbbel történik, a kép pedig a fényképezőgép által tárolt tájolás szerint elforgatásra kerül.

## 9. A feltételek beállítása

| Mező | Kulcs a JSON fájlban | Alapérték |
|---|---|---|
| Legnagyobb fájlméret (MB) | max_file_size_mb | 2 (1 MB = 1 048 576 bájt) |
| Legkisebb szélesség (px) | min_width | 945 |
| Legkisebb magasság (px) | min_height | 945 |
| Legnagyobb szélesség (px) | max_width | 2835 |
| Legnagyobb magasság (px) | max_height | 2010 |
| Legkisebb felbontás (DPI) | min_dpi | 96 |
| Megengedett képtípusok | allowed_types | RGB, szürkeárnyalatos, fekete-fehér, CMYK |

| Képtípus a felületen | Azonosító a JSON fájlban | Jelentése |
|---|---|---|
| RGB (színes) | RGB | Színes kép |
| RGBA (színes, átlátszó) | RGBA | Színes kép átlátszósággal |
| szürkeárnyalatos | greyscale | Szürkeárnyalatos kép |
| fekete-fehér | B&W | Kétszínű (fekete-fehér) kép |
| CMYK | CMYK | Nyomdai színmodellű kép |
| palettás | palette | Legfeljebb 256 színű kép, pl. GIF |

1. Módosítsa a mezőket, majd nyomja meg az Alkalmaz gombot.
2. Ha a feltételek változtak, a program megkérdezi, el akarja-e menteni őket fájlba. Igen válasz esetén a mentési ablak a jelenlegi feltételfájlt (alapesetben criterias.json) ajánlja fel.
3. A betöltött kép ellenőrzése az új feltételekkel automatikusan megismétlődik.

Más feltételkészlet betöltése: Feltételek betöltése... gomb, majd a JSON fájl kiválasztása. Mentés tetszőleges néven: Feltételek mentése másként... gomb.

Ha azt szeretné, hogy a program mindig a saját feltételeivel induljon, mentse őket criterias.json néven az exe mellé. A fájl egyszerű JSON szöveg, Jegyzettömbbel is szerkeszthető (a képtípusokat az azonosítójukkal kell megadni):

```json
{
  "max_file_size_mb": 2.0,
  "min_width": 945,
  "min_height": 945,
  "max_width": 2835,
  "max_height": 2010,
  "min_dpi": 96.0,
  "allowed_types": ["RGB", "greyscale", "B&W", "CMYK"]
}
```

## 10. Gyakori kérdések és hibaüzenetek

| Üzenet / helyzet | Teendő |
|---|---|
| A kép nem nyitható meg / Nem felismerhető képfájl | A fájl nem kép vagy sérült - válasszon másik fájlt. |
| Érvénytelen érték | A beírt érték nem szám, vagy kívül esik a megengedett tartományon. |
| Érvénytelen feltételek | A Feltételek panel valamelyik mezője hibás (pl. a minimum nagyobb a maximumnál, vagy nincs megengedett képtípus). |
| Nem megfelelő formátum | A választott fájlformátum nem tudja tárolni a képtípust - válasszon a felsorolt formátumok közül. |
| Sikertelen átalakítás ... legkisebb megengedett méret | A kép a megadott fájlméretbe a minimális képméret mellett sem fér bele. Válasszon JPEG formátumot vagy más képtípust. |
| A felbontás „nincs megadva” | A fájl nem tárol DPI értéket; állítson be egyet a Felbontás gombbal. |
| Figyelmeztetés indításkor | A feltételfájl vagy a locals.json hibás / nem található, vagy ismeretlen a --lang nyelvkód. A program az alapértelmezett beállításokkal fut. |
| Angol szöveg jelenik meg magyar felületen | A szöveg hiányzik a locals.json magyar részéből - pótolja a hiányzó kulcsot. |
