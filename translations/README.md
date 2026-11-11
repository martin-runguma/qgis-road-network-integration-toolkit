# Translation packs

Each `<language_code>.py` module must expose a dictionary named `TEXT`.
Use the exact keys from `i18n.TEXT['en']`. The loader merges missing keys from
English, so partial packs are safe. Preserve all `{placeholder}` tokens.

Run the translation tests from the plugin's `tests` directory:

```bash
PYTHONPATH=..:. python -m unittest test_i18n
```

The current extra-language packs localise the main labels and controls.
Detailed help/tooltips and some processing messages still need human-reviewed
translations; those strings intentionally use the English fallback.
