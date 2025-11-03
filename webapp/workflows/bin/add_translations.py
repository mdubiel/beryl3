#!/usr/bin/env python
"""
Quick script to add translations to .po files
"""
import re

# Polish translations
pl_translations = {
    "Owned by": "Właściciel",
    "Collection Images": "Zdjęcia kolekcji",
    "Total Items": "Wszystkie przedmioty",
    "In Collection": "W kolekcji",
    "Wanted": "Poszukiwane",
    "Reserved": "Zarezerwowane",
    "Items in this Collection": "Przedmioty w tej kolekcji",
    "Page %(current)s of %(total)s": "Strona %(current)s z %(total)s",
    "10 per page": "10 na stronę",
    "25 per page": "25 na stronę",
    "50 per page": "50 na stronę",
    "100 per page": "100 na stronę",
    "This collection is currently empty.": "Ta kolekcja jest obecnie pusta.",
    "Check back later for new items!": "Sprawdź później, czy są nowe przedmioty!",
    "Close": "Zamknij",
    "Image Preview": "Podgląd obrazu",
    "Public Profile": "Profil publiczny",
    "Joined": "Dołączył",
    "Public Collections": "Publiczne kolekcje",
    "Favorites": "Ulubione",
    "Set up your custom profile URL": "Ustaw własny adres URL profilu",
    "You're currently using your user ID in the URL. Set a nickname in your": "Obecnie używasz swojego identyfikatora użytkownika w adresie URL. Ustaw pseudonim w",
    "account settings": "ustawieniach konta",
    "to get a personalized URL like": "aby otrzymać spersonalizowany adres URL jak",
    "%(name)s hasn't made any collections public yet.": "%(name)s nie udostępnił jeszcze żadnych kolekcji.",
    "Favorite Items": "Ulubione przedmioty",
    "Public": "Publiczne",
    "%(counter)s item": "%(counter)s przedmiot",
}

# German translations
de_translations = {
    "Owned by": "Eigentümer",
    "Collection Images": "Sammlungsbilder",
    "Total Items": "Alle Artikel",
    "In Collection": "In der Sammlung",
    "Wanted": "Gesucht",
    "Reserved": "Reserviert",
    "Items in this Collection": "Artikel in dieser Sammlung",
    "Page %(current)s of %(total)s": "Seite %(current)s von %(total)s",
    "10 per page": "10 pro Seite",
    "25 per page": "25 pro Seite",
    "50 per page": "50 pro Seite",
    "100 per page": "100 pro Seite",
    "This collection is currently empty.": "Diese Sammlung ist derzeit leer.",
    "Check back later for new items!": "Schauen Sie später nach neuen Artikeln!",
    "Close": "Schließen",
    "Image Preview": "Bildvorschau",
    "Public Profile": "Öffentliches Profil",
    "Joined": "Beigetreten",
    "Public Collections": "Öffentliche Sammlungen",
    "Favorites": "Favoriten",
    "Set up your custom profile URL": "Richten Sie Ihre benutzerdefinierte Profil-URL ein",
    "You're currently using your user ID in the URL. Set a nickname in your": "Sie verwenden derzeit Ihre Benutzer-ID in der URL. Legen Sie einen Spitznamen in Ihren",
    "account settings": "Kontoeinstellungen",
    "to get a personalized URL like": "fest, um eine personalisierte URL wie",
    "%(name)s hasn't made any collections public yet.": "%(name)s hat noch keine Sammlungen veröffentlicht.",
    "Favorite Items": "Lieblingsartikel",
    "Public": "Öffentlich",
    "%(counter)s item": "%(counter)s Artikel",
}

def add_translations(po_file, translations):
    with open(po_file, 'r', encoding='utf-8') as f:
        content = f.read()

    for msgid, msgstr in translations.items():
        # Find msgid and replace empty msgstr
        pattern = rf'(msgid "{re.escape(msgid)}"\nmsgstr ")("")'
        replacement = rf'\1{msgstr}"'
        content = re.sub(pattern, replacement, content)

    with open(po_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Updated {po_file} with {len(translations)} translations")

if __name__ == '__main__':
    add_translations('locale/pl/LC_MESSAGES/django.po', pl_translations)
    add_translations('locale/de/LC_MESSAGES/django.po', de_translations)
    print("✅ Translations added successfully!")
