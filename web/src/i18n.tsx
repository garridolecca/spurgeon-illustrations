import type { ItemRow, Lang, Meta } from "./types";

/** Interface text in English and Spanish. */
const S = {
  en: {
    brand: "Spurgeon Illustrations",
    tagline: (n: string) => <>Search {n} sermon illustrations from C. H. Spurgeon and the Puritans by <em>meaning</em>, with each one quoted and cited to its sermon, book and page.</>,
    searchLabel: "Search illustrations",
    placeholder: "Search by meaning: “the love of God”, “compassion”, Romans 8:28 …",
    clear: "Clear",
    modelLoading: "Preparing meaning search… (word search works meanwhile)",
    modelFailed: "Meaning search could not load on this device; using word search.",
    similarTo: "Illustrations similar to",
    back: "back",
    tiedTo: (r: string) => <>Illustrations tied to <b>{r}</b> (their Scripture or the sermon's text)</>,
    bestMatches: "best matches",
    illustrations: "illustrations",
    relatedTopics: "Related topics:",
    noMatch: "No illustrations matched. Try different words, or clear a filter.",
    showMore: "Show more",
    footer: (v: string) => <>Illustrations were found and summarized by an AI model reading public-domain sermon volumes and works; always check the original passage before preaching it. Data version {v}. <a href="https://github.com/garridolecca/spurgeon-illustrations">Source &amp; data on GitHub</a>.</>,
    loadingHint: "The first visit downloads the library (about 30 MB); meaning search keeps loading in the background (about 150 MB more); later visits load instantly from your browser's cache.",
    starting: "Starting",
    category: "Category", topic: "Topic", author: "Author", all: "All", kind: "Kind", clearFilters: "Clear filters",
    tryLabel: "Try:",
    browseTitle: "Browse by topic",
    fewer: "fewer", more: (n: number) => `+${n} more`,
    illustrates: "Illustrates",
    text: "text",
    page: "p.",
    nearest: " (nearest matching passage on the page)",
    noPassage: "The original passage could not be located; see the book at the page cited.",
    loading: "Loading…",
    readOriginal: "Read original", hideOriginal: "Hide original",
    copyCitation: "Copy citation", copyForSermon: "Copy for sermon", moreLike: "More like this", link: "Link",
    openLogos: "Open in Logos",
    copied: (w: string) => `${w} copied`, wCitation: "Citation", wIllustration: "Illustration and citation", wLink: "Link",
    translationNote: "", showEnglish: "", showSpanish: "",
    myList: "My list", addToList: "Add to my list", inList: "In my list", removeFromList: "Remove",
    listTitle: "My list", listEmpty: "Your list is empty. Use “Add to my list” on any illustration to collect it here for your sermon.",
    listNote: "Saved in this browser only.", copyAll: "Copy all", printList: "Print", downloadWord: "Download Word", clearList: "Clear list",
    random: "Random illustration", dayTitle: "Illustration of the day", openIt: "Open",
    byBible: "Browse by Bible book", book: "Book", chapter: "Chapter", wholeBook: "Whole book", go: "Show",
    length: "Length", short: "Short", medium: "Medium", long: "Long",
    vectorsLoading: "Preparing meaning search… (word search works meanwhile)", backToBrowse: "Back to browsing",
    langName: "English",
    howTo: "How to use", support: "Support", close: "Close",
    helpTitle: "How to use this app",
    help: [
      ["Search by meaning", "Type an idea, not just words: “God's care in suffering” finds illustrations about providence even when they never use those words. Exact words and names work too."],
      ["Search by Scripture", "Type a reference such as Romans 8:28 or Psalm 23 to see illustrations tied to that passage, either in their Scripture or in the sermon's text."],
      ["Browse and filter", "Pick a topic from Browse by topic, or narrow any search by category, topic, author, or kind (analogy, story, historical, image)."],
      ["Use an illustration", "Read original shows the quoted passage from the book; Copy for sermon copies the illustration with its citation; Copy citation gives a Turabian footnote; More like this finds similar illustrations; Open in Logos opens the page if you own the book."],
      ["Build your sermon list", "Press Add to my list on each illustration you want; open My list at the top to copy them all with their citations, print them, or download a Word file. The list stays in your browser."],
      ["Explore", "Browse by Bible book and chapter, or try Random illustration and the Illustration of the day."],
      ["English or Spanish", "Switch the language with EN / ES at the top. Spanish summaries are machine translations; the original passage stays in English."],
      ["Private and fast", "Everything runs in your browser. The first visit downloads the library (about 30 MB, then about 150 MB more for meaning search in the background); later visits load from cache, and nothing you search is sent anywhere."],
    ] as [string, string][],
    helpCheck: "The illustrations were found and summarized by an AI model; always read the original passage before preaching it.",
    donateTitle: "Support this project",
    donateText: "This library was built to help pastors and teachers find faithful illustrations from Spurgeon and the Puritans. If it serves your preaching, consider supporting the project.",
    donateButton: "Donate", donateQr: "Or scan this QR code (Venmo):", donateEmailLabel: "Feedback or questions?",
    examples: ["the love of God", "compassion for sinners", "God's faithfulness in trials", "the danger of delay", "Romans 8:28", "Psalm 23", "pride before a fall", "assurance of salvation"],
    stages: {} as Record<string, string>,
  },
  es: {
    brand: "Ilustraciones de Spurgeon",
    tagline: (n: string) => <>Busque entre {n} ilustraciones para sermones de C. H. Spurgeon y los puritanos por su <em>significado</em>; cada una citada con su sermón, libro y página.</>,
    searchLabel: "Buscar ilustraciones",
    placeholder: "Busque por significado: “el amor de Dios”, “compasión”, Romanos 8:28 …",
    clear: "Borrar",
    modelLoading: "Preparando la búsqueda por significado… (la búsqueda por palabras ya funciona)",
    modelFailed: "La búsqueda por significado no pudo cargarse en este dispositivo; se usa la búsqueda por palabras.",
    similarTo: "Ilustraciones parecidas a",
    back: "volver",
    tiedTo: (r: string) => <>Ilustraciones relacionadas con <b>{r}</b> (por su pasaje bíblico o el texto del sermón)</>,
    bestMatches: "mejores resultados",
    illustrations: "ilustraciones",
    relatedTopics: "Temas relacionados:",
    noMatch: "Ninguna ilustración coincide. Pruebe con otras palabras o quite un filtro.",
    showMore: "Ver más",
    footer: (v: string) => <>Las ilustraciones fueron halladas y resumidas por un modelo de IA que leyó sermones y obras de dominio público, y las traducciones al español son automáticas; verifique siempre el pasaje original antes de predicarlo. Versión de los datos {v}. <a href="https://github.com/garridolecca/spurgeon-illustrations">Código y datos en GitHub</a>.</>,
    loadingHint: "La primera visita descarga la biblioteca (unos 30 MB); la búsqueda por significado sigue cargándose en segundo plano (unos 150 MB más); las siguientes visitas cargan al instante desde la caché del navegador.",
    starting: "Iniciando",
    category: "Categoría", topic: "Tema", author: "Autor", all: "Todos", kind: "Tipo", clearFilters: "Quitar filtros",
    tryLabel: "Pruebe:",
    browseTitle: "Explorar por tema",
    fewer: "menos", more: (n: number) => `+${n} más`,
    illustrates: "Ilustra",
    text: "texto",
    page: "p.",
    nearest: " (pasaje más cercano en la página)",
    noPassage: "No se encontró el pasaje original; consulte el libro en la página citada.",
    loading: "Cargando…",
    readOriginal: "Leer el pasaje", hideOriginal: "Ocultar el pasaje",
    copyCitation: "Copiar cita", copyForSermon: "Copiar para el sermón", moreLike: "Más como esta", link: "Enlace",
    openLogos: "Abrir en Logos",
    copied: (w: string) => `${w} copiado`, wCitation: "Cita", wIllustration: "Ilustración y cita", wLink: "Enlace",
    translationNote: "Traducción automática del original en inglés.", showEnglish: "Ver el original en inglés", showSpanish: "Ver la traducción",
    myList: "Mi lista", addToList: "Agregar a mi lista", inList: "En mi lista", removeFromList: "Quitar",
    listTitle: "Mi lista", listEmpty: "Su lista está vacía. Use «Agregar a mi lista» en cualquier ilustración para reunirla aquí para su sermón.",
    listNote: "Se guarda solo en este navegador.", copyAll: "Copiar todo", printList: "Imprimir", downloadWord: "Descargar Word", clearList: "Vaciar lista",
    random: "Ilustración al azar", dayTitle: "Ilustración del día", openIt: "Abrir",
    byBible: "Explorar por libro de la Biblia", book: "Libro", chapter: "Capítulo", wholeBook: "Libro completo", go: "Ver",
    length: "Extensión", short: "Corta", medium: "Media", long: "Larga",
    vectorsLoading: "Preparando la búsqueda por significado… (la búsqueda por palabras ya funciona)", backToBrowse: "Volver a explorar",
    langName: "Español",
    howTo: "Cómo usar", support: "Apoyar", close: "Cerrar",
    helpTitle: "Cómo usar esta aplicación",
    help: [
      ["Busque por significado", "Escriba una idea, no solo palabras: «el cuidado de Dios en el sufrimiento» encuentra ilustraciones sobre la providencia aunque no usen esas palabras. También funcionan palabras exactas y nombres."],
      ["Busque por la Escritura", "Escriba una cita como Romanos 8:28 o Salmo 23 para ver las ilustraciones ligadas a ese pasaje, ya sea por su referencia bíblica o por el texto del sermón."],
      ["Explore y filtre", "Elija un tema en Explorar por tema, o afine cualquier búsqueda por categoría, tema, autor o tipo (analogía, relato, histórica, imagen)."],
      ["Use una ilustración", "Leer el pasaje muestra el texto original del libro; Copiar para el sermón copia la ilustración con su cita; Copiar cita da una nota al pie estilo Turabian; Más como esta busca ilustraciones parecidas; Abrir en Logos abre la página si tiene el libro."],
      ["Arme su lista para el sermón", "Pulse Agregar a mi lista en cada ilustración que desee; abra Mi lista arriba para copiarlas todas con sus citas, imprimirlas o descargar un archivo de Word. La lista se queda en su navegador."],
      ["Explore", "Explore por libro y capítulo de la Biblia, o pruebe Ilustración al azar y la Ilustración del día."],
      ["Inglés o español", "Cambie el idioma con EN / ES en la parte superior. Los resúmenes en español son traducciones automáticas; el pasaje original se mantiene en inglés."],
      ["Privado y rápido", "Todo funciona en su navegador. La primera visita descarga la biblioteca (unos 30 MB, y luego unos 150 MB más en segundo plano para la búsqueda por significado); las siguientes cargan desde la caché, y nada de lo que busca se envía a ningún lugar."],
    ] as [string, string][],
    helpCheck: "Las ilustraciones fueron encontradas y resumidas por un modelo de IA; lea siempre el pasaje original antes de predicarlo.",
    donateTitle: "Apoye este proyecto",
    donateText: "Esta biblioteca fue creada para ayudar a pastores y maestros a encontrar ilustraciones fieles de Spurgeon y los puritanos. Si le sirve en su predicación, considere apoyar el proyecto.",
    donateButton: "Donar", donateQr: "O escanee este código QR (Venmo):", donateEmailLabel: "¿Comentarios o preguntas?",
    examples: ["el amor de Dios", "compasión por los pecadores", "la fidelidad de Dios en la prueba", "el peligro de postergar", "Romanos 8:28", "Salmo 23", "el orgullo antes de la caída", "la seguridad de la salvación"],
    stages: {
      "Loading illustrations": "Cargando ilustraciones", "Loading meaning vectors": "Cargando vectores de significado",
      "Indexing": "Indexando", "Loading meaning model": "Cargando el modelo de significado", "Starting": "Iniciando",
    } as Record<string, string>,
  },
};

export type Strings = typeof S.en;
export const strings = (l: Lang): Strings => S[l] as Strings;

export function initialLang(): Lang {
  const p = new URLSearchParams(location.search).get("lang");
  if (p === "es" || p === "en") return p;
  try {
    const s = localStorage.getItem("lang");
    if (s === "es" || s === "en") return s;
  } catch { /* storage unavailable */ }
  return (navigator.language || "").toLowerCase().startsWith("es") ? "es" : "en";
}

export function rememberLang(l: Lang) {
  try { localStorage.setItem("lang", l); } catch { /* storage unavailable */ }
  document.documentElement.lang = l;
}

// ---------- content in the reader's language (Spanish falls back to English where untranslated) ----------
export const topicName = (m: Meta, t: number, l: Lang) => (l === "es" && m.topics_es?.[t]) || m.topics[t][0];
export const categoryName = (m: Meta, c: number, l: Lang) => (l === "es" && m.categories_es?.[c]) || m.categories[c];
export const kindName = (m: Meta, k: string, l: Lang) => (l === "es" && m.kinds_es?.[k]) || k;
export const title = (it: ItemRow, l: Lang) => (l === "es" && it[15]) || it[1];
export const summary = (it: ItemRow, l: Lang) => (l === "es" && it[16]) || it[3];
export const point = (it: ItemRow, l: Lang) => (l === "es" && it[17]) || it[4];

const MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const MONTHS_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
/** "May 30, 1875" -> "30 de mayo de 1875" */
export function dateEs(d: string): string {
  const m = /^([A-Z][a-z]+) (\d{1,2}), (\d{4})$/.exec(d.trim());
  if (!m) return d;
  const k = MONTHS_EN.indexOf(m[1]);
  return k < 0 ? d : `${m[2]} de ${MONTHS_ES[k]} de ${m[3]}`;
}
