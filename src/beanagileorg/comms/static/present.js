// Full-screen presenting with reveal.js. Press S for the speaker view (notes, next slide, timer), F for full screen.
(async function () {
  const res = await fetch(`/api/decks/${window.DECK_ID}/full`, { credentials: "same-origin" });
  if (res.status === 401) {
    location.href = "/login";
    return;
  }
  if (!res.ok) {
    document.body.textContent = "That deck wasn't found.";
    return;
  }
  const data = await res.json();
  document.title = data.deck.title;
  document.getElementById("slides").innerHTML = BADeck.render(data.slides, data.media);
  const deck = new Reveal(document.querySelector(".reveal"), {
    hash: true,
    center: false,
    width: 1280,
    height: 720,
    margin: 0.04,
    transition: data.deck.transition,
    plugins: [RevealNotes],
  });
  BADeck.attach(deck);
  deck.initialize();
})();
