# The Light Adjustable Lens (LAL) — Presentation

An ~8-minute [Slidev](https://github.com/slidevjs/slidev) presentation on the
Light Adjustable Lens, built from the source manuscript and four supporting
clinical papers.

## Run it

```bash
cd presentation
npm install      # first time only
npm run dev      # opens http://localhost:3030
```

Edit [`slides.md`](./slides.md) and the browser hot-reloads.

Press <kbd>F</kbd> for fullscreen, <kbd>O</kbd> for the slide overview, and
<kbd>P</kbd> / the presenter view (`/presenter`) to read the speaker notes —
each slide carries notes pacing it to roughly 40 seconds for an 8-minute talk.

## Export

```bash
npm run build            # static site → dist/
npm run export           # PDF (installs Playwright Chromium on first run)
```

## Outline (14 slides)

1. Title
2. The clinical problem — residual refractive error
3. What is the LAL? (concept + history, FDA 2017)
4. How it works — photochemistry + diffusion
5. Lock-in & UV protection (ActivShield)
6. Lens specifications
7. The surgical workflow (+ dilation requirement)
8. Indications & contraindications
9. Advantage — post-refractive-surgery eyes
10. Clinical outcomes vs. other IOLs (+ monovision, LAL+)
11. Limitations & safety
12. Key takeaways
13. Thank you / sources

## Sources

- **Primary:** Word manuscript (`LAL_ingilizce.docx`)
- Jun JH, Lieu A, Afshari NA. *Light adjustable intraocular lenses in cataract surgery: considerations.* Curr Opin Ophthalmol 2024;35:44–49.
- Doane J, et al. *Clinical data registry comparing outcomes of two light adjustable lenses.* J Cataract Refract Surg 2025;51:948–954.
- Wong JR, Folden DV, et al. *Visual outcomes of a second-generation, enhanced UV protected light adjustable lens in cataract patients with previous LASIK and/or PRK.* Clin Ophthalmol 2023;17:3379–3387.
- Nakagama M, Nagesh D, Doane J. *Comparative analysis of postoperative visual outcomes of light-adjustable lens, toric monofocal, and spherical monofocal IOLs.* Missouri Medicine 2025;122(5):417–422.
