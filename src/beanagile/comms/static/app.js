// Comms studio screens. Version 1 screens (messages, templates, audiences, calendar) come next.
BA.view("/this-week", {
  title: "This week",
  async render(main) {
    main.innerHTML = `<section class="card"><h2>What I owe people this week</h2>
      <p class="quiet">The shared base is running. Version 1 screens come next: messages, templates, audiences and the comms calendar.</p></section>`;
  },
});
