type NavigationCards = Record<string, { _info?: { nav?: boolean } }>;

/** Resolve a visible content card to a sidebar entry without hiding its content. */
export function getNavigationCard(cards: NavigationCards, cardKey: string): string {
  const keys = Object.keys(cards);
  const index = keys.indexOf(cardKey);
  if (index < 0) return "";
  // Supplemental cards follow their preceding sidebar entry. Keep that entry
  // selected while scrolling through them, otherwise ConfigNav treats the
  // indicator as absent and auto-selects the first task in the open section.
  for (let cursor = index; cursor >= 0; cursor--) {
    if (cards[keys[cursor]]._info?.nav !== false) return keys[cursor];
  }
  // A section may start with an unlisted card. Select its first actual entry;
  // a section with no entries has no sidebar indicator at all.
  return keys.find((key) => cards[key]._info?.nav !== false) || "";
}
