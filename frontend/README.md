# Lumen frontend

React + Vite interface for the autonomous analytics agent in this repository.

## Local development

```bash
npm install
npm run dev
```

The interface currently uses the repository's sample analysis as a complete interactive demo. File selection, provider selection, pipeline progress, navigation, report tabs, theme switching, and report exports are functional in the browser.

## Backend handoff

The Python project currently exposes a CLI rather than an HTTP API. To connect live runs, expose the existing `app.stream(initial_state)` workflow through a small API and map its node events to the six activity stages shown in the interface:

1. `minification`
2. `intent_plan`
3. `code_generation`
4. `isolated_execution`
5. `self_correction`
6. `output_synthesis`

Set `VITE_AGENT_API_URL` in a local `.env` file to the deployed API origin when that endpoint is available. Keep LLM keys on the server; never add them to Vite environment variables.

## Firebase Hosting

The included `firebase.json` is configured for a Vite single-page app.

```bash
npm run build
firebase use --add
firebase deploy --only hosting
```

Copy `.firebaserc.example` to `.firebaserc` or let the Firebase CLI create it. The API itself will need a separate runtime such as Cloud Run or Cloud Functions because Firebase Hosting only serves the built frontend.

## Liquid glass

`src/lib/liquid-glass.js` is an ES module adaptation of `deepika-builds/liquid-glass`. It provides Chromium refraction with an automatic frosted fallback in Safari and Firefox. The effect is limited to small surfaces to keep text legible and GPU cost low.
