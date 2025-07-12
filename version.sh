#!/bin/bash

# Skript pro inkrementaci verze a vytvoření git tagu
# Použití: ./version.sh [major|minor|patch]

set -e

# Funkce pro zobrazení nápovědy
show_help() {
    echo "Použití: $0 [major|minor|patch]"
    echo ""
    echo "  major  - zvýší major verzi (1.2.3 -> 2.0.0)"
    echo "  minor  - zvýší minor verzi (1.2.3 -> 1.3.0)" 
    echo "  patch  - zvýší patch verzi (1.2.3 -> 1.2.4)"
    echo ""
    echo "Skript automaticky:"
    echo "  - Zkontroluje, že je git repozitář čistý"
    echo "  - Aktualizuje verzi v VERSION a manifest.json"
    echo "  - Commitne změny"
    echo "  - Vytvoří git tag"
    echo "  - Pushne změny a tag"
}

# Kontrola parametrů
if [ $# -ne 1 ]; then
    echo "Chyba: Je potřeba zadat typ inkrementace!"
    show_help
    exit 1
fi

VERSION_TYPE="$1"

if [[ ! "$VERSION_TYPE" =~ ^(major|minor|patch)$ ]]; then
    echo "Chyba: Neplatný typ verze! Použijte major, minor nebo patch."
    show_help
    exit 1
fi

# Kontrola, že jsme v git repozitáři
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Chyba: Nejste v git repozitáři!"
    exit 1
fi

# Kontrola, že je repozitář čistý
if ! git diff-index --quiet HEAD --; then
    echo "Chyba: Git repozitář není čistý! Nejdříve commitněte nebo stashněte změny."
    echo ""
    echo "Necommitované změny:"
    git status --porcelain
    exit 1
fi

# Cesty k souborům s verzí
VERSION_FILE="VERSION"
MANIFEST_FILE="custom_components/iqr23/manifest.json"

# Kontrola existence souborů
if [ ! -f "$VERSION_FILE" ]; then
    echo "Chyba: Soubor $VERSION_FILE neexistuje!"
    exit 1
fi

if [ ! -f "$MANIFEST_FILE" ]; then
    echo "Chyba: Soubor $MANIFEST_FILE neexistuje!"
    exit 1
fi

# Načtení aktuální verze
CURRENT_VERSION=$(cat "$VERSION_FILE" | tr -d '[:space:]')

if [[ ! "$CURRENT_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Chyba: Neplatný formát verze v $VERSION_FILE: $CURRENT_VERSION"
    echo "Očekávaný formát: X.Y.Z (např. 1.2.3)"
    exit 1
fi

# Rozložení verze na komponenty
IFS='.' read -r -a version_parts <<< "$CURRENT_VERSION"
MAJOR=${version_parts[0]}
MINOR=${version_parts[1]}
PATCH=${version_parts[2]}

echo "Aktuální verze: $CURRENT_VERSION"

# Inkrementace podle typu
case $VERSION_TYPE in
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    patch)
        PATCH=$((PATCH + 1))
        ;;
esac

NEW_VERSION="$MAJOR.$MINOR.$PATCH"
echo "Nová verze: $NEW_VERSION"

# Potvrzení od uživatele
read -p "Pokračovat s verzí $NEW_VERSION? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Zrušeno uživatelem."
    exit 1
fi

# Aktualizace VERSION souboru
echo "$NEW_VERSION" > "$VERSION_FILE"
echo "✓ Aktualizován $VERSION_FILE"

# Aktualizace manifest.json pomocí sed
sed -i "s/\"version\": \"$CURRENT_VERSION\"/\"version\": \"$NEW_VERSION\"/" "$MANIFEST_FILE"
echo "✓ Aktualizován $MANIFEST_FILE"

# Kontrola, že se verze skutečně změnila v manifest.json
if ! grep -q "\"version\": \"$NEW_VERSION\"" "$MANIFEST_FILE"; then
    echo "Chyba: Nepodařilo se aktualizovat verzi v $MANIFEST_FILE"
    # Vrácení změn
    echo "$CURRENT_VERSION" > "$VERSION_FILE"
    exit 1
fi

# Git operace
echo "Přidávám změny do gitu..."
git add "$VERSION_FILE" "$MANIFEST_FILE"

echo "Commitování změn..."
git commit -m "Bump version to $NEW_VERSION"

echo "Vytvářím git tag v$NEW_VERSION..."
git tag "v$NEW_VERSION"

echo "Pushování změn a tagu..."
git push origin HEAD
git push origin "v$NEW_VERSION"

echo ""
echo "🎉 Úspěšně dokončeno!"
echo "   Verze: $CURRENT_VERSION → $NEW_VERSION"
echo "   Tag: v$NEW_VERSION"
echo "   Změny byly pushnuty do repozitáře."
