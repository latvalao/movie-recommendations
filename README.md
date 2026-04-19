# Movie Recommendations

Web-sovellus, jossa käyttäjät voivat jakaa elokuvasuosituksia. Käyttäjät voivat luoda tunnuksen, kirjautua sisään, lisätä elokuvia sekä muokata ja poistaa omia elokuviaan. Elokuville voi valita genrejä ja muut käyttäjät voivat kirjoittaa arvosteluja.

## Toteutetut toiminnot

* Käyttäjän rekisteröinti ja kirjautuminen
* Elokuvien lisääminen (nimi, kuvaus, julkaisuvuosi, genret)
* Omien elokuvien muokkaaminen ja poistaminen
* Kaikkien elokuvien listaus etusivulla
* Elokuvien haku nimellä ja genren perusteella
* Elokuvan yksityiskohtasivu arvosteluineen
* Arvostelut: käyttäjä voi antaa arvosanan (1–5) ja kommentin toisen käyttäjän elokuvaan
* Käyttäjäsivut, jotka näyttävät tilastoja (lisätyt elokuvat, annetut arvostelut, keskiarvot) ja käyttäjän lisäämät elokuvat
* Genreluokittelu: elokuville voi valita yhden tai useamman genren (tietokannassa 10 genreä)
* CSRF-suojaus kaikissa lomakkeissa

## Tietokohteet

* **Pääasiallinen tietokohde:** Elokuva (nimi, kuvaus, julkaisuvuosi, genret)
* **Toissijainen tietokohde:** Arvostelu (arvosana 1–5 ja kommentti, liitetään elokuvaan)

## Käynnistäminen

1. Asenna riippuvuudet:

```
pip install -r requirements.txt 
(Tähän käy pip install flask, mutta periaatteen vuoksi aina tykkään käyttää tekstitiedostoa :) )
```

2. Käynnistä sovellus:

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
3. Kirjaudu sisään ja lisää elokuvia **+ Lisää elokuva** -painikkeella. Valitse elokuvalle genrejä.
4. Kokeile hakutoimintoa etusivulla: voit hakea nimellä ja suodattaa genren mukaan.
5. Klikkaa elokuvan nimeä nähdäksesi yksityiskohtasivun.
6. Luo toinen käyttäjätunnus ja kirjoita arvostelu toisen käyttäjän elokuvaan.
7. Klikkaa käyttäjänimeä nähdäksesi käyttäjäsivun tilastoineen.
8. Muokkaa tai poista lisäämiäsi elokuvia korttien painikkeilla.

## Tietokannan rakenne

Tietokanta luodaan `schema.sql`-tiedoston perusteella. Taulut:

* **users** -- käyttäjät (id, username, password_hash)
* **movies** -- elokuvat (id, name, description, year, user_id)
* **genres** -- genret (id, name) -- esitäytetty 10 genrellä
* **movie_genres** -- elokuvien genreliitokset (movie_id, genre_id)
* **reviews** -- arvostelut (id, movie_id, user_id, rating, comment, created_at)

Tiedosto `database.db` ei kuulu repositorioon -- se luodaan yllä olevien ohjeiden mukaan.
