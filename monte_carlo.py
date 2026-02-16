from random import Random
from pyscript import web

from js import console

with open("wortliste.txt", "r") as file:
    wortliste = file.read().split(" ")

with open("wortliste_richtig.txt", "r") as file:
    wortliste_richtig = file.read().splitlines()

seed = 0
rng = Random(x=seed)


# Simuliert n Spiele mit den gegebenen Präferenzen, gibt Liste mit den Ergebnissen der einzelnen Simulationen zurück
def wort_analysieren(eroeffnungswoerter: list[str], strategie: str, n: int, seed) -> list[int]:
    print(
        f"Starte Simulation mit Eröffnungswörtern {eroeffnungswoerter}, Strategie {strategie}, Seed {str(seed)} und {n} Durchläufen.")
    # TODO Strategie und Seed implementieren
    daten = []
    naechste_aktualisierung = 0
    for i in range(n):
        prozent = i / n * 100
        if prozent >= naechste_aktualisierung:
            web.page["progress-text"].innerText = str(int(prozent)) + "%"
            web.page["progress"].style["width"] = str(prozent) + "%"
            naechste_aktualisierung += 1
        versuche = spiel_simulieren(eroeffnungswoerter)
        daten.append(versuche)
    web.page["progress-text"].innerText = "100%"
    web.page["progress"].style["width"] = "100%"

    return daten


# Simuliert ein Spiel und gibt die Anzahl der Versuche zurück, die benötigt wurden, um das Wort zu erraten
def spiel_simulieren(eroeffnungswoerter: list[str]) -> int:
    grau = set()
    gelb = set()
    gruen = set()

    korrektes_wort = rng.choice(wortliste_richtig)
    versuche = 0
    versuch_verlauf = []
    while versuche < 7:
        versuche += 1

        # Nächstes Wort zum Raten wählen
        if len(eroeffnungswoerter) >= versuche:
            versuch = eroeffnungswoerter[versuche - 1]
        else:
            versuch = naechstes_wort_erraten(grau, gelb, gruen)
        versuch_verlauf.append(versuch)
        # Wort wurde richtig erraten
        if versuch == korrektes_wort:
            break
        # Neue Information speichern
        farben = versuch_farben(korrektes_wort, versuch)
        for i in range(len(versuch)):
            buchstabe = versuch[i]
            farbe = farben[i]
            match farbe:
                case -1: grau.add((buchstabe, i))
                case 0: gelb.add((buchstabe, i))
                case 1: gruen.add((buchstabe, i))
    # if versuche == 7:
    #     print(f"Versuche: {versuch_verlauf}, Richtiges Wort: {korrektes_wort}")
    return versuche


# Farbliche Markierung der Buchstaben im Versuch: grau => -1, gelb => 0, grün => 1
def versuch_farben(korrekt: str, versuch: str) -> list[int]:
    result = []
    for char_index in range(len(versuch)):
        if versuch[char_index] in korrekt:
            if versuch[char_index] == korrekt[char_index]:
                result.append(1)
            else:
                result.append(0)
        else:
            result.append(-1)
    return result


def naechstes_wort_erraten(grau: set[tuple[str, int]], gelb: set[tuple[str, int]], gruen: set[tuple[str, int]]) -> str:
    moegliche_woerter_set = sorted(moegliche_woerter(grau, gelb, gruen))
    # TODO: Probewörter
    # if len(moegliche_woerter_set) > 3:
    #     alle_buchstaben = {}
    #     for wort in moegliche_woerter_set:
    #         for buchstabe in wort:
    #             if buchstabe not in alle_buchstaben:
    #                 alle_buchstaben[buchstabe] = 0
    #             alle_buchstaben[buchstabe] += 1
    #     for buchstabe, _ in gruen:
    #         alle_buchstaben.pop(buchstabe, None)
    #     for buchstabe, _ in gelb:
    #         alle_buchstaben.pop(buchstabe, None)
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
