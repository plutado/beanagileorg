// Toolkit screens. Version 1 screens (people, listening tour, rollup, my development) come next.
BA.view("/today", {
  title: "Today",
  async render(main) {
    main.innerHTML = `<section class="card"><h2>What needs me today</h2>
      <p class="quiet">The shared base is running. Version 1 screens come next: people, listening tour, day-30 rollup and my development.</p></section>`;
  },
});
