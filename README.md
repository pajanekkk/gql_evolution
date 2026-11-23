# Event boilerplate project

Demonstrační boilerplate pro doménu `Event / EventInvitation` podle funkčního vzoru ze `src.zip`.

## Zásady

- GQL vrstva nesmí importovat DB vrstvu ani typově odkazovat na DB modely.
- Pro decoupling mezi vrstvami se používají `Protocol` kontrakty v `src/common/protocols.py`.
- `LoaderMap`, services a GQL typy jsou explicitně definované.
- `EventInvitation` je vazba `Event - User` se stavem pozvánky/účasti.
- `UserGQLModel` je externí federovaná entita pro Apollo Federation.
- `StateGQLModel` je také externí federovaná entita, protože stav pozvánky typicky patří do UG / state-machine subgrafu.
- Page resolvery vždy používají `whereType` definovaný přes `@createInputs2`.
- Mutace používají `BaseService.ExecuteServiceMethod` a `CreateErrorCallback`, aby resolver neobsahoval lokální zpracování výjimek.
- `BaseGQLModel.from_dataclass()` zůstává kompatibilní název, ale interně volá `from_db()` a ukládá původní entitu do `_dbdata` bez `dataclasses.asdict()`.


## Závislost na `uoishelpers`

Projekt pracuje s balíkem `uoishelpers` z repozitáře:

```text
https://github.com/hrbolek/uoishelpers/archive/4e41615436d6effbe248d8503e4df373549bcec3.zip
```

Závislost je uvedená přímo v `pyproject.toml`:

```toml
'uoishelpers @ https://github.com/hrbolek/uoishelpers/archive/4e41615436d6effbe248d8503e4df373549bcec3.zip'
```

Boilerplate proto nepřidává lokální náhražky pro `uoishelpers`. Používá importy ve stejném stylu jako funkční vzor, například:

```python
from uoishelpers.dataloaders.LoaderMapBase import LoaderMapBase
from uoishelpers.dataloaders.IDLoader import IDLoader
from uoishelpers.gqlpermissions import OnlyForAuthentized
from uoishelpers.resolvers import PageResolver, createInputs2
```

Závislost je připnutá na konkrétní commit, aby instalace i CI používaly stejnou verzi.

## Vrstvy

```text
DBDefinitions/
  Domain_Events/
    EventModel.py
    EventInvitationModel.py

Dataloaders/
  __init__.py        # explicitní LoaderMap

ServiceDefinitions/
  Domain_Events/
    EventService.py
    EventInvitationService.py

GraphTypeDefinitions/
  BaseGQLModel.py    # _dbdata + LoaderName kontrakt
  Domain_Events/
    EventGQLModel.py
    EventInvitationGQLModel.py
  Domain_UG/
    UserGQLModel.py  # externí federovaná entita
    StateGQLModel.py # externí federovaná entita
```

## Studenti typicky doplní

1. DB model do `DBDefinitions/Domain_X`.
2. Explicitní položku v `LoaderMap`.
3. Service třídu do `ServiceDefinitions/Domain_X`.
4. GQL typ bez importu DB vrstvy.
5. `InputFilter` přes `@createInputs2`.
6. Query přes `PageResolver(... whereType=...)`.
7. Mutace přes `ExecuteServiceMethod`.

## Spuštění Coder

```bash
python .CoderDefinitions/main.py
```

## Spouštění ??

```bash
uvicorn main:app --port 9999 --env-file environment.txt
```
localhost:9999/gql

---

## Deníček – Contact a Employment část

### 2026-10-15 – DB vrstva Contact a Employment (commit 2e23156)

Podle zadání `gql_personalities/2` vznikly první modely. Entita `Address` je v zadání škrtnutá, proto se neimplementuje.

**Co bylo přidáno:**
- `ContactModel` (tabulka `contacts`) – osoba, typ kontaktu, hodnota, příznak preferovaného kontaktu
- `EmploymentModel` (tabulka `employments`) – osoba, zaměstnavatel, pozice, oddělení, začátek, konec, popis

---

### 2026-10-16 – Úprava tabulek (commit 360c017)

Zjednodušené modely, doplněný export z `src/DBDefinitions/__init__.py` a úprava DB CLI.

---

### 2026-10-22 – Úklid modelů a demo data (commit 282c3b2)

**Co bylo přidáno / opraveno:**
- `systemdata.json` – první demo kontakty a zaměstnání navázané na skutečné uživatele z UG
- z `ContactModel` odstraněny zbytky stromových atributů bez odpovídajících sloupců, z obou modelů nepoužité importy
- z `__all__` odstraněna neexistující položka `EventTypeModelContactModel`, kvůli které padal `from src.DBDefinitions import *`
- `requirements-dev.txt` – doplněn `prometheus_client`, který `uoishelpers` potřebuje při importu

**Problémy a řešení:**
- `readJsonFile` převádí na datum jen `startdate`, `enddate`, `lastchange` a `created`. Hodnoty `started` a `finished` zůstávaly text a `asyncpg` je odmítl. Seed teď převádí texty podle typu sloupce `DateTime`.
- Seed padal s chybou `A transaction is already begun`, protože `ImportModels` na jedné session volá `execute()` a pak `begin()`. Dokud byl JSON prázdný, chyba se neprojevila. Otevřená transakce se teď před předáním session commitne.

---

### 2026-10-23 – Stromový číselník typů kontaktů (commit 812430c)

Zadání vyžaduje číselníky jako stromy („typy typů“), proto textové `contact_type` nahradil odkaz na katalog.

```
Kontakt
├── E-mail (Soukromý e-mail, Pracovní e-mail)
├── Telefon (Soukromý telefon, Pracovní telefon)
└── Nouzový kontakt
```

**Co bylo přidáno / změněno:**
- `ContactTypeModel` (tabulka `contacttypes`) – `parent_id` na sebe sama, vazby `parent` a `children`, materializovaná cesta `path`
- `ContactModel.contact_type_id` – cizí klíč na katalog
- balíček přejmenován na `Domain_Personalities2`, sloupec `personality_id` na `user_id`
- DB CLI převádí hodnoty z JSONu podle typu sloupce (`coerce_column_value`)
- seed nahrává tabulky v pořadí podle cizích klíčů (`metadata.sorted_tables`)

**Poznámky:**
- Na tabulku `users` záměrně není cizí klíč ani `relationship()`. Uživatele vlastní subgraf UG, vazba 1:N se vyjádří až v GQL vrstvě přes federaci.
- `create_all` existující tabulky nemění, takže přejmenování a nové sloupce bylo v běžící databázi nutné provést ručně přes `ALTER TABLE`.

---

### 2026-11-09 – Vrstva služeb, atomické mutace a typy zaměstnání (commit d7c8e87)

**Co bylo přidáno:**
- `LoaderMap` – typové dataloadery pro `ContactModel`, `ContactTypeModel`, `EmploymentModel` a `EmploymentTypeModel`
- `src/ServiceDefinitions/Domain_Personalities2` – služby `ContactService`, `ContactTypeService`, `EmploymentService`, `EmploymentTypeService`, registrované v `ServiceRegistry`
- `EmploymentTypeModel` (tabulka `employmenttypes`) – strom forem zaměstnání (pracovní poměr, dohody DPP a DPČ, OSVČ) a `EmploymentModel.employment_type_id`
- `systemdata.json` – RBAC u všech záznamů a dalších 20 kontaktů a 20 zaměstnání; celkem 28 kontaktů, 27 zaměstnání a 14 uživatelů
- RBAC: kontakty a zaměstnání mají `rbacobject_id = user_id`, katalogy používají skupinu `rbacobject` jako ostatní číselníky

**Problémy a řešení:**
- **Mutace nebyly atomické.** `ExecuteServiceMethod` převedl chybu služby na typovou chybu, ale `SessionCommitExtension` o ní nevěděl a částečný zápis commitnul. Chyby se teď přes `ContextVar` `operation_errors` zapisují do chyb operace a celá mutace se vrátí.
- **Service CLI nic neukládalo**, protože loadery dělají jen `flush`. Po úspěšné operaci se teď volá `commit`.
- **`update` v CLI vždy vrátil `null`**, protože `lastchange` přišel jako text a porovnání s `datetime` nikdy neprošlo.
- **`get` v CLI nikdy nic nenašel**, protože loader páruje výsledky podle `UUID` a `id` přicházelo jako text.

---

### 2026-11-23 – Testy domény Personalities2

Přidán `tests/services/test_personalities2_services.py` (31 testů). Běží nad vlastní SQLite v paměti, takže nepotřebuje Docker a nezapisuje do sdílené databáze. Pokrytí modelů a služeb `Domain_Personalities2` je 100 %.

**Co testy hlídají:**
- registraci služeb a loaderů, CRUD všech čtyř služeb a odmítnutí zastaralého `lastchange`
- stromy číselníků včetně dotazu na podstrom přes `path` a odmítnutí neexistujícího rodiče nebo typu
- commit úspěšné mutace a rollback při selhání služby po částečném zápisu
- idempotentní seed s `DEMODATA` i bez něj
- konzistenci demo dat (cesty ve stromech, listové typy, RBAC, jeden preferovaný kontakt, data začátku a konce)
- převod hodnot v `coerce_column_value`

**Co zbývá:**
- GQL vrstva pro Contact a Employment včetně direktivy `Relation` u cizích klíčů
- kontrola `lastchange` v `BaseService.Delete`
- oprava dvou starších selhávajících testů `BaseService`
