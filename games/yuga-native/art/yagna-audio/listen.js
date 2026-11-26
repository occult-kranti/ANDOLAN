/* One shared transport gives every audition the same volume and stops the preceding take. */
const media = document.querySelector("#sound");
const title = document.querySelector("#track");
const download = document.querySelector("#download");
const transcript = document.querySelector("#transcript");
const notice = document.querySelector("#notice");
const language = document.querySelector("#lang");
const phases = [...document.querySelectorAll("[data-at]")];
const takes = [...document.querySelectorAll("[data-file], [data-line]")];
const lines = {
  ignite: { en: "The ritual fire is lit.", hi: "यज्ञ की अग्नि जल उठी।" },
  quench: { en: "The fire is out.", hi: "अग्नि बुझ गई।" },
};
let chosen = null;
let take = 0;
let seekWhenReady = null;

function markPhase() {
  const phase = chosen ? -1 : Math.min(3, Math.floor(media.currentTime / 10));
  phases.forEach((button, i) => {
    if (i === phase) button.setAttribute("aria-current", "true");
    else button.removeAttribute("aria-current");
  });
}
function start(button, time = 0) {
  const id = ++take;
  const line = button?.dataset.line;
  const locale = language.value;
  chosen = button;
  const file = line
    ? `voice-guide/${line}-${locale}.wav`
    : (button?.dataset.file ?? "ritual-mix.flac");
  if (seekWhenReady) media.removeEventListener("loadedmetadata", seekWhenReady);
  notice.hidden = true;
  title.textContent = line
    ? `${button.textContent} · ${language.selectedOptions[0].textContent}`
    : (button?.dataset.title ?? "Full ritual mix");
  transcript.hidden = !line;
  transcript.textContent = line ? lines[line][locale] : "";
  transcript.lang = line ? locale : "";
  download.href = file;
  for (const t of takes) t.setAttribute("aria-pressed", t === button);
  if (media.getAttribute("src") !== file) {
    media.src = file;
    media.load();
  }
  const setTime = () => {
    if (take === id) {
      media.currentTime = time;
      markPhase();
    }
  };
  if (media.readyState >= HTMLMediaElement.HAVE_METADATA) setTime();
  else {
    seekWhenReady = setTime;
    media.addEventListener("loadedmetadata", setTime, { once: true });
  }
  media.play().catch((error) => {
    if (id !== take || error.name === "AbortError") return;
    notice.textContent =
      "Playback is unavailable here. Use Download recording to open this take.";
    notice.hidden = false;
  });
}
for (const p of phases)
  p.addEventListener("click", () => start(null, Number(p.dataset.at)));
for (const t of takes) {
  t.setAttribute("aria-pressed", false);
  t.addEventListener("click", () => start(t));
}
language.addEventListener("change", () => {
  if (chosen?.dataset.line) start(chosen);
});
media.addEventListener("timeupdate", markPhase);
media.addEventListener("error", () => {
  notice.textContent =
    "This recording could not load. Use the download link to open it directly.";
  notice.hidden = false;
});
document.addEventListener("visibilitychange", () => {
  if (document.hidden) media.pause();
});
window.addEventListener("pagehide", () => media.pause());
markPhase();
