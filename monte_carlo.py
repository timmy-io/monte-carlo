from random import Random
from pyscript import web

from js import console

with open("wortliste.txt", "r") as file:
    wortliste = file.read().split(" ")

with open("wortliste_richtig.txt", "r") as file:
    wortliste_richtig = file.read().splitlines()

with open("wortliste_historie.txt", "r") as file:
    wortliste_historie = file.read().splitlines()

cache = {}


# Simuliert n Spiele mit den gegebenen Präferenzen, gibt Liste mit den Ergebnissen der einzelnen Simulationen zurück
def wort_analysieren(eroeffnungswoerter: list[str], strategie: str, hilfsmittel: tuple[bool, bool], n: int, seed) -> list[int]:
    print(f"""Starte Simulation mit Eröffnungswörtern {eroeffnungswoerter if len(eroeffnungswoerter) != 0 else "/"},
          Strategie {strategie}, Seed {str(seed)}, Hilfsmitteln {hilfsmittel} und {n} Durchläufen.""")
    geheim_rng = Random(x=seed)
    raten_rng = Random(x=((str(seed) + "2") if seed != None else None))
    daten = []
    naechste_aktualisierung = 0
    for i in range(n):
        prozent = i / n * 100
        if prozent >= naechste_aktualisierung:
            web.page["progress-text"].innerText = str(int(prozent)) + "%"
            web.page["progress"].style["width"] = str(prozent) + "%"
            naechste_aktualisierung += 1
        geheimes_wort = geheim_rng.choice(
            list(set(wortliste_richtig) - set(wortliste_historie)))
        versuche = spiel_simulieren(
            geheimes_wort, raten_rng, eroeffnungswoerter, strategie, hilfsmittel)
        daten.append(versuche)
    global cache
    cache = {}
    web.page["progress-text"].innerText = "100%"
    web.page["progress"].style["width"] = "100%"

    return daten


# Simuliert ein Spiel und gibt die Anzahl der Versuche zurück, die benötigt wurden, um das Wort zu erraten
def spiel_simulieren(geheimes_wort: str, rng: Random, eroeffnungswoerter: list[str], strategie: str, hilfsmittel: tuple[bool, bool]) -> int:
    grau = set()
    gelb = set()
    gruen = set()

    versuche = 0
    versuch_verlauf = []
    while versuche < 7:
        versuche += 1

        # Nächstes Wort zum Raten wählen
        if len(eroeffnungswoerter) >= versuche:
            versuch = eroeffnungswoerter[versuche - 1]
        else:
            versuch = naechstes_wort_erraten(
                rng, versuche, strategie, hilfsmittel, grau, gelb, gruen)
        versuch_verlauf.append(versuch)
        # Wort wurde richtig erraten
        if versuch == geheimes_wort:
            break
        # Neue Information speichern
        farben = versuch_farben(geheimes_wort, versuch)
        for i in range(len(versuch)):
            buchstabe = versuch[i]
            farbe = farben[i]
            match farbe:
                case -1: grau.add((buchstabe, i))
                case 0: gelb.add((buchstabe, i))
                case 1: gruen.add((buchstabe, i))
    return versuche


# Farbliche Markierung der Buchstaben im Versuch: grau => -1, gelb => 0, grün => 1
def versuch_farben(geheim: str, versuch: str) -> list[int]:
    result = []
    for char_index in range(len(versuch)):
        if versuch[char_index] in geheim:
            if versuch[char_index] == geheim[char_index]:
                result.append(1)
            else:
                result.append(0)
        else:
            result.append(-1)
    return result


def naechstes_wort_erraten(rng: Random, versuch: int, strategie: str, hilfsmittel: tuple[bool, bool],
                           grau: set[tuple[str, int]], gelb: set[tuple[str, int]], gruen: set[tuple[str, int]]) -> str:
    match strategie:
        case "random":
            moegliche_woerter_set = moegliche_woerter(grau, gelb, gruen)
            return rng.choice(sorted(hilfsmittel_anwenden(moegliche_woerter_set, hilfsmittel)))
        case "random-alles":
            return rng.choice(sorted(hilfsmittel_anwenden(set(wortliste), hilfsmittel)))
        case "probe":
            moegliche_woerter_set = moegliche_woerter(grau, gelb, gruen)
            moegliche_woerter_set = sorted(
                hilfsmittel_anwenden(moegliche_woerter_set, hilfsmittel))
            global cache
            if len(moegliche_woerter_set) > 2 and versuch != 6:
                key = (
                    (hilfsmittel[0], hilfsmittel[1]),
                    frozenset(grau),
                    frozenset(gelb),
                    frozenset(gruen),
                )
                if key in cache:
                    return cache[key]

                kandidaten = set(wortliste)
                for grauer_buchstabe, index in grau:
                    grau_set = set()
                    for x in alphabet_liste[grauer_buchstabe]:
                        grau_set = grau_set.union(x)
                    kandidaten = kandidaten - grau_set

                for wort in kandidaten.copy():
                    for gelber_buchstabe, index in gelb:
                        if wort[index] == gelber_buchstabe:
                            kandidaten.remove(wort)
                            break

                alle_buchstaben = {}
                for wort in moegliche_woerter_set:
                    for buchstabe in wort:
                        if buchstabe not in alle_buchstaben:
                            alle_buchstaben[buchstabe] = 0
                        alle_buchstaben[buchstabe] += 1
                for buchstabe, _ in gruen:
                    alle_buchstaben.pop(buchstabe, None)

                max_punkte = -9999999
                max_wort = "xxxxx"
                for wort in kandidaten.copy():
                    punkte = 0
                    buchstaben = ""
                    for buchstabe in wort:
                        if buchstabe not in alle_buchstaben.keys():
                            punkte -= 10
                        elif buchstabe not in buchstaben:
                            punkte += alle_buchstaben[buchstabe]
                        if buchstabe in buchstaben:
                            punkte -= 100
                        buchstaben += buchstabe
                    if punkte > max_punkte:
                        max_wort = wort
                        max_punkte = punkte

                cache[key] = max_wort
                return max_wort

            return rng.choice(moegliche_woerter_set)


def moegliche_woerter(grau: set[tuple[str, int]], gelb: set[tuple[str, int]], gruen: set[tuple[str, int]]) -> set[str]:
    moeglich_set = None

    # Nur Wörter, die an den jeweiligen Positionen die grünen Buchstaben haben
    for gruener_buchstabe, index in gruen:
        gruen_set = alphabet_liste[gruener_buchstabe][index]
        if moeglich_set is None:
            moeglich_set = gruen_set
        else:
            moeglich_set = moeglich_set.intersection(gruen_set)

    # Die oberen Wörter filtern, sodass jedes Wort, irgendwo die gelben Buchstaben hat
    for gelber_buchstabe, index in gelb:
        gelb_set = set()
        for i, x in enumerate(alphabet_liste[gelber_buchstabe]):
            # Wird eigentlich eh später rausgefiltert, aber lieber noch ein wenig Performance rausholen
            if i == index:
                continue
            gelb_set = gelb_set.union(x)
        if moeglich_set is None:
            moeglich_set = gelb_set
        else:
            moeglich_set = moeglich_set.intersection(gelb_set)

    # Falls nichts gefunden wurde, erstmal alle Wörter, die man eingeben kann, nehmen
    if moeglich_set is None:
        moeglich_set = set(wortliste)

    # Alle Wörter, die im Wort nicht die grauen Buchstaben haben, von oben entfernen
    for grauer_buchstabe, index in grau:
        grau_set = set()
        for x in alphabet_liste[grauer_buchstabe]:
            grau_set = grau_set.union(x)
        moeglich_set = moeglich_set - grau_set

    # Wörter entfernen, die an den gelben Stellen den gelben Buchstaben haben
    for wort in moeglich_set.copy():
        for gelber_buchstabe, index in gelb:
            if wort[index] == gelber_buchstabe:
                moeglich_set.remove(wort)
                break

    return moeglich_set


def hilfsmittel_anwenden(moeglich: set[str], hilfsmittel: tuple[bool, bool]) -> set[str]:
    geheime_woerter_erlaubt = hilfsmittel[0]
    historie_erlaubt = hilfsmittel[1]
    mit_hilfsmitteln = set(moeglich)
    if geheime_woerter_erlaubt:
        mit_hilfsmitteln = mit_hilfsmitteln.intersection(wortliste_richtig)
    if historie_erlaubt:
        mit_hilfsmitteln = mit_hilfsmitteln - set(wortliste_historie)
    return mit_hilfsmitteln


# Erstellt fünf Listen für jeden Buchstaben mit Wörtern, die den Buchstaben an der 1./2./3./4./5. Position haben
def alphabet_listen_erstellen() -> dict[str, list[set[str]]]:
    alphabet_wortliste = {}
    for wort in wortliste:
        for index, buchstabe in enumerate(wort):
            if buchstabe not in alphabet_wortliste:
                alphabet_wortliste[buchstabe] = [set() for _ in range(5)]
            alphabet_wortliste[buchstabe][index].add(wort)

    return alphabet_wortliste


alphabet_liste = alphabet_listen_erstellen()
# Methode wort_analysieren main.py zur Verfügung stellen
__export__ = ["wort_analysieren"]
