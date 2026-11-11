import unittest

import i18n


class TranslationTests(unittest.TestCase):
    def test_language_catalogue_has_33_languages(self):
        self.assertEqual(len(i18n.LANGUAGES), 33)
        self.assertEqual(len(i18n.SUPPORTED), 33)

    def test_all_languages_have_all_interface_keys(self):
        expected = set(i18n.TEXT["en"])
        for code in i18n.SUPPORTED:
            self.assertTrue(code in i18n.TEXT, "missing language block: " + code)
            self.assertEqual(
                expected - set(i18n.TEXT[code]),
                set(),
                "missing keys for " + code,
            )

    def test_locale_normalisation(self):
        self.assertEqual(i18n._normalise_language("fr_FR"), "fr")
        self.assertEqual(i18n._normalise_language("zh-CN"), "zh")
        self.assertEqual(i18n._normalise_language("no_NO"), "nb")
        self.assertEqual(i18n._normalise_language("nn_NO"), "nb")
        self.assertEqual(i18n._normalise_language("in_ID"), "id")
        self.assertEqual(i18n._normalise_language("xx_XX"), "en")

    def test_translated_text_and_fallback(self):
        self.assertEqual(i18n.tr("grp_input", "de"), "Eingabedaten")
        self.assertEqual(i18n.tr("win_title", "fr"), i18n.TEXT["fr"]["win_title"])
        self.assertEqual(i18n.tr("not_a_real_key", "de"), "not_a_real_key")

    def test_phase2_layer_chooser_labels(self):
        self.assertEqual(i18n.tr("dlg_choose_layer", "fr"), "Choisir une couche d’entités")
        self.assertEqual(i18n.tr("dlg_select_layer", "sw"), "Chagua tabaka")
        self.assertEqual(i18n.tr("dlg_cancel", "ar"), "إلغاء")
        self.assertEqual(i18n.tr("fmt_gpkg", "en"), "GeoPackage (.gpkg)")
        self.assertEqual(i18n.tr("dlg_selected", "fr").format(name="roads"), "Sélectionnée : roads")

    def test_rtl_languages(self):
        self.assertEqual(i18n.RTL_LANGUAGES, {"ar", "ur", "fa"})


if __name__ == "__main__":
    unittest.main()
