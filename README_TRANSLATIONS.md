# Road Network Integration Toolkit — multilingual build

This package is the uploaded QGIS plugin with its translation subsystem repaired
and expanded.

## What was fixed

- The 33-language selector now has a corresponding importable language module
  for every additional language.
- The loader imports packs relative to the plugin package, so it works when QGIS
  loads the plugin as a package (the normal installation path).
- Every loaded language dictionary is completed against the English key set.
  Missing values therefore fall back safely to English rather than raising
  `KeyError` or leaving controls blank.
- Locale tags such as `fr_FR`, `zh-CN`, `no_NO`, `nn_NO`, and `in_ID` are
  normalised to supported language codes.
- Saved language preferences are validated before use.
- RTL layout metadata is provided for Arabic, Urdu and Persian.
- Added translation coverage diagnostics and automated tests.
- Existing plugin processing code and algorithms were retained.

## Translation status — important

The language framework is functional for all 33 languages, but the source
plugin did not contain reviewed translations for 27 of them. This build does
not invent complete translations or pretend that English fallback is a
translation.

- English, French, Spanish, Portuguese, Swahili and Arabic retain the
  original source dictionaries (62 interface keys each).
- Italian, Simplified Chinese, German, Russian, Japanese, Swedish, Norwegian
  Bokmål, Danish, Hindi, Bengali, Urdu, Punjabi, Marathi, Telugu, Tamil,
  Gujarati, Indonesian, Turkish, Korean, Vietnamese, Persian, Thai, Polish,
  Dutch, Ukrainian, Amharic and Hausa now have complete 62-key dictionaries.
  Their main interface labels and controls are translated; detailed help and
  tooltip text that has not yet been translated falls back to English.
- Some processing-log and validation messages are still hard-coded in the
  processing/UI code and therefore remain English.

Use `i18n.translation_coverage('de')` to inspect how many values differ from
the English source. This measures translated values, not translation quality.

## Install

1. Close QGIS.
2. Back up the existing plugin folder.
3. Replace the plugin files with the contents of this ZIP, keeping the folder
   structure intact.
4. Reopen QGIS and open the plugin.
5. Change the language from the selector in the plugin header. The choice is
   saved for the next session.

## Adding or correcting translations

Edit `translations/<code>.py`. Each module exposes a `TEXT` dictionary keyed
with the same names as `i18n.TEXT['en']`. Preserve format placeholders such as
`{suffix}` exactly. The loader merges missing keys from English, so a partial
translation module is safe.

The six original language dictionaries are in `i18n.py`. The additional packs
are in `translations/`.

## Validation

The build was syntax-compiled and tested with the included QGIS stubs. The
translation tests verify all 33 language modules, all 62 keys per language,
locale aliases, English fallback, and RTL metadata.
