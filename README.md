# Movie Recommendations

Web-sovellus, jossa käyttäjät voivat jakaa elokuvasuosituksia. Käyttäjät voivat luoda tunnuksen, kirjautua sisään, lisätä elokuvia sekä muokata ja poistaa omia elokuviaan. Etusivulla näkyvät kaikki lisätyt elokuvat, ja niitä voi hakea nimellä.

## Toteutetut toiminnot

-- Käyttäjän rekisteröinti ja kirjautuminen
-- Elokuvien lisääminen (nimi, kuvaus, julkaisuvuosi)
-- Omien elokuvien muokkaaminen ja poistaminen
-- Kaikkien elokuvien listaus etusivulla
-- Elokuvien haku nimellä

## Käynnistäminen

Asenna riippuvuudet:
```
pip install -r requirements.txt
```

3. Käynnistä sovellus:
```
python app.py
```

Tietokanta (`database.db`) luodaan automaattisesti ensimmäisellä käynnistyskerralla `schema.sql`-tiedoston perusteella. Vaihtoehtoisesti tietokannan voi alustaa käsin Pythonilla:

```
python -c "import sqlite3; sqlite3.connect('database.db').executescript(open('schema.sql').read())"
```

Sovellus käynnistyy osoitteeseen `http://127.0.0.1:5000`.

## Testaaminen

1. Avaa sovellus selaimessa.
2. Luo käyttäjätunnus **Rekisteröidy**-sivulla.
3. Kirjaudu sisään ja lisää elokuvia **+ Lisää elokuva** -painikkeella.
4. Kokeile hakutoimintoa etusivulla.
5. Muokkaa tai poista lisäämiäsi elokuvia korttien painikkeilla.

## Tietokannan rakenne

Tietokanta luodaan `schema.sql`-tiedoston perusteella. Taulut:

- **users** -- käyttäjät (id, username, password_hash)
- **movies** -- elokuvat (id, name, description, year, user_id)

Tiedosto `database.db` ei kuulu repositorioon -- se luodaan yllä olevien ohjeiden mukaan.
