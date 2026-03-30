# Stabilizace mechaniky načítání a ovládání v IQR23

## Problém
Senzory v Home Assistantu občas padaly do stavu `unavailable` během normálného provozu, především když dělal restart nebo došlo k časovému výpadku připojení.

## Root cause
Mechanika načítání dat měla několik problémů:

1. **Mazání cache na dílčí selhání**: Pro obsah příkazu `load()` se `self.state` mazal úplně na začátku (`self.state = dict()`). Pokud pak selhal jeden ze čtyř XML endpointů (např. `data_i_all.xml`), zbylé tři se sice nahrály, ale pak se slučovaly do částečného stavu. Senzory bez dat pak padaly do `unavailable`.

2. **Amplifikace transientních chyb**: Při síťové chybě se `loadIfRequired()` vyhazoval RuntimeError, která prostupovala až k entitám. Ty pak označovaly `available=False` i když měly v cache poslední známou hodnotu.

3. **Špatný handling ovládání**: Při ovládání switche (`setDigitalOutputMode`) se chyba v `logout()` nebo `load()` nezpracovávala elegantně – pokud se odhlášení nezdařilo, zůstalo zařízení v neznámém stavu.

4. **Nadměrný obsah `available` logiky**: V `switch.py` se pro určení dostupnosti prováděla dodatková `getDigitalOutputMode()` volání, což zvyšovalo počet dotazů a riziko chyby.

## Řešení

### 1. Odolné načítání s paralelisací (`iqr23.py`, `load()`)
```python
# Nově:
results = await asyncio.gather(*(self.loadFile(file) for file in files), 
                               return_exceptions=True)
```
- Všechny čtyři XML soubory se stahují paralelně.
- Výjimky se zachytávají bez zastavení ostatních stahů.
- Sloučují se pouze úspěšně načtené soubory.
- Starý `self.state` zůstává, jenom se update-uje novými hodnotami.
- Pokud všechny čtyři selžou, teprve pak se vyhozuje `RuntimeError`.

### 2. Cache fallback na transientní chyby (`iqr23.py`, `loadIfRequired()`)
```python
try:
    await self.load()
    self.loadtime = now
except Exception as err:
    if self.state:
        _LOGGER.warning("Refresh failed..., using cached state")
    else:
        raise
```
- Pokud refresh selže a máme cache → beze změny pokračujeme.
- Pokud refresh selže a `self.state` je prázdný → teprve pak vyhazujeme chybu.
- `loadtime` se neaktualizuje, takže se příště zase pokusíme (exponential backoff v HA).

### 3. Jednoduchá `available` logika v entitách
- **sensor.py**, **binary_sensor.py**, **switch.py**: `available=True` jen když se podařilo získat hodnotu.
- `KeyError` → `available=False` (data nejsou v cache).
- `TimeoutError` / `ClientError` → logujeme, ale nezměníme `available` (použijeme poslední známou hodnotu).
- Odebrán zbytečný `getDigitalOutputMode()` call v switch update.

### 4. Robustnější ovládání (`iqr23.py`, `setDigitalOutputMode()`)
```python
asyncio.login(AccessLevel.MASTER)
await self._pressBtn(btn)
await self.logout(save=True)  # Now handles failures gracefully
try:
    await self.load()
except Exception as e:
    _LOGGER.warning("Failed to reload state, but command was sent")
```
- Logout s `save=True` vždy pokusíme; chyba se loguje, ne vyhazuje.
- Pokud refresh stavu selže, nezastavuje se ovládání – příkaz už byl odeslán.

### 5. Lepší error handling v `_pressBtn()` a `logout()`
- Kontrolují status kódu (`response.status != 200`).
- Chyby se logují, ne tiše ignorují.
- Logout se pokusí i když save selže.

## Testování
Manuální testy prokázaly:
- ✓ `load()` zvládá částičné selhání (3 z 4 souborů OK)
- ✓ `loadIfRequired()` zachovává cache na chybu
- ✓ Entity zůstávají `available` pokud mají data
- ✓ Fresh cache (< 5 sec) se nenatahuje zbytečně

## Dopad na uživatele
- Senzory teď padají do `unavailable` pouze pokud:
  - Všechny 4 XML zdroje selžou dlouhodobě (ne transientně)
  - Nebo data pro daný senzor chybí v zařízení
- Přechodné výpadky připojení (<5 sec refresh interval) se skrývají za cache
- Ovládání je odolnější vůči chybám během logout/save

## Soubory změněné
- `custom_components/iqr23/iqr23.py` – Load logika + control + session
- `custom_components/iqr23/sensor.py` – Zjednodušená `available` logika
- `custom_components/iqr23/binary_sensor.py` – Zjednodušená `available` logika
- `custom_components/iqr23/switch.py` – Odlančená `getDigitalOutputMode()` call + error handling
- `tests/test_iqr23.py` – Přidány testy pro cache fallback + partial source failure
