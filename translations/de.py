"""Interface language pack for de. Missing reviewed text uses English fallback."""

# -----------------------------------------------------------------
# German
TEXT = {
    'win_title': 'Werkzeug zur Integration von Straßennetzen',
    'app_subtitle': 'Harmonisierung des übergeordneten und nachgeordneten Straßennetzes',
    'language': 'Sprache:',

    'grp_input': 'Eingabedaten',
    'ph_priority': 'Datensatz des übergeordneten Straßennetzes auswählen',
    'ph_secondary': 'Datensatz des nachgeordneten Straßennetzes auswählen',
    'ph_boundary': 'Grenze des Untersuchungsgebiets auswählen',
    'lbl_priority': 'Übergeordnetes Straßennetz:',
    'lbl_secondary': 'Nachgeordnetes Straßennetz:',
    'lbl_boundary': 'Grenze des Untersuchungsgebiets:',
    'hint_input': (
        'Verwenden Sie „Durchsuchen“, um eine Vektordatei oder einen Layer '
        'aus einem GeoPackage (.gpkg) oder einer File-Geodatabase (.gdb) '
        'auszuwählen. Es werden nur Layer mit dem erwarteten Geometrietyp '
        'angeboten (Linien für Straßen, Polygone für Gebietsgrenzen).'),
    'btn_browse': 'Durchsuchen…',
    'tip_path': (
        'Dieses Feld zeigt den Pfad zur Datenquelle an. Verwenden Sie '
        '„Durchsuchen“, um eine Datei oder einen bestimmten Layer aus einem '
        'GeoPackage (.gpkg) oder einer File-Geodatabase (.gdb) auszuwählen.'),
    'tip_browse': (
        'Durchsuchen, um eine Vektordatei oder einen Layer aus einem '
        'GeoPackage / einer File-Geodatabase auszuwählen'),
    'menu_vector_file': 'Vektordatei oder GeoPackage…',
    'menu_gdb': 'File-Geodatabase (.gdb)…',

    'grp_settings': 'Integrationseinstellungen',
    'lbl_method': 'Methode:',
    'meth_1': 'Methode 1 — Direkte Zusammenführung',
    'meth_2': 'Methode 2 — Zuschneiden + Fangen',
    'meth_3': 'Methode 3 — Gezieltes Fangen',
    'tip_method': (
        'Methode 1 führt die als missing_1 bis missing_4 klassifizierten '
        'nachgeordneten Straßen direkt zusammen. Methode 2 schneidet die '
        'nachgeordneten Straßen mithilfe der Puffer des übergeordneten '
        'Straßennetzes zu und fängt deren Endpunkte. Methode 3 verwendet '
        'quadratische Puffer für nachgeordnete Straßen sowie ein gezieltes '
        'Fangen von Schwerpunkten und Endpunkten.'),
    'lbl_crs': 'Koordinatenreferenzsystem für die Analyse:',
    'tip_crs': (
        'Wählen Sie das projizierte Koordinatenreferenzsystem, das für '
        'Entfernungsberechnungen und Fangoperationen verwendet wird. '
        'Wählen Sie ein lokales projiziertes KBS, das für Ihr '
        'Untersuchungsgebiet geeignet ist.'),
    'btn_suggest_crs': 'Anhand des Untersuchungsgebiets vorschlagen',
    'tip_suggest_crs': (
        'Wählt die UTM-Zone aus, die den Mittelpunkt der Grenze des '
        'Untersuchungsgebiets enthält.'),
    'hint_crs': (
        'Wählen Sie das Koordinatenreferenzsystem wie in den QGIS-Werkzeugen '
        'zum Exportieren oder Transformieren aus. Für entfernungsbasierte '
        'Verarbeitung ist ein projiziertes KBS mit Metern als Einheit '
        'erforderlich. Nach Auswahl der Grenze des Untersuchungsgebiets '
        'wird automatisch eine geeignete UTM-Zone vorgeschlagen, sofern '
        'Sie nicht bereits ein KBS ausgewählt haben.'),

    'grp_advanced': 'Erweiterte Einstellungen',
    'adv_base_buffer': 'Pufferabstand des übergeordneten Straßennetzes',
    'adv_secondary_buffer': 'Pufferabstand des nachgeordneten Straßennetzes',
    'adv_join_gap': 'Maximaler Fangabstand',
    'adv_mid_gap': 'Verdichtungsintervall der Zwischenpunkte',
    'adv_centroid_max_dist': 'Maximaler Anpassungsabstand des Schwerpunkts',
    'tip_base_buffer': 'Pufferabstand des übergeordneten Straßennetzes.',
    'tip_secondary_buffer': 'Pufferabstand des nachgeordneten Straßennetzes.',
    'tip_join_gap': 'Maximaler Fangabstand zwischen Straßenobjekten.',
    'tip_mid_gap': 'Verdichtungsintervall für Zwischenpunkte.',
    'tip_centroid_max_dist': (
        'Maximaler Abstand für die Verschiebung eines Schwerpunkts zu einem Stützpunkt.'),
    'hint_advanced': (
        'Die angezeigten Werte sind die Standardwerte des Arbeitsablaufs '
        'und werden in Metern angegeben. Aktivieren Sie „Erweiterte '
        'Einstellungen“, um sie zu ändern. Durch Deaktivieren werden die '
        'Standardwerte wiederhergestellt. Die Werte werden an die mit der '
        'historischen Version kompatible Verarbeitungs-Engine für '
        'Puffer-, Zuschneide- und Fangoperationen übergeben.'),

    'grp_output': 'Ausgabeeinstellungen',
    'lbl_output_folder': 'Ausgabeordner:',
    'ph_output_folder': 'Wählen Sie den erforderlichen Ausgabe- / Arbeitsordner aus...',
    'tip_output_folder': (
        'Erforderlich. Dieser Ordner dient sowohl als Arbeitsverzeichnis '
        'als auch als Speicherort für die Ausgabedateien.'),
    'lbl_output_name': 'Ausgabename:',
    'ph_output_name': 'Projekt- oder Stadtkürzel eingeben, z. B. KE_Nairobi',
    'tip_output_name': (
        'Geben Sie nur das Präfix ein. Das Werkzeug fügt automatisch '
        "'{suffix}' hinzu."),
    'lbl_output_format': 'Ausgabeformat:',
    'tip_output_format': (
        'Wählen Sie das Dateiformat für das endgültig harmonisierte '
        'Straßennetz aus.'),
    'lbl_output_preview': 'Ausgabevorschau:',
    'preview_empty': (
        'Geben Sie einen Ausgabenamen ein (z. B. KE_Nairobi), um den '
        'endgültigen Dateinamen anzuzeigen.'),
    'chk_add_outputs': (
        'Erfolgreich erstellte Ausgaben automatisch zum QGIS-Projekt hinzufügen'),
    'chk_keep_intermediates': 'Zwischenliegende Diagnose-Layer beibehalten',

    'panel_log': 'Verarbeitungsprotokoll',
    'status_ready': (
        'Bereit. Wählen Sie Ihre Daten aus und starten Sie eine Methode.'),
    'ph_log': 'Validierungs- und Verarbeitungsmeldungen werden hier angezeigt.',
    'btn_clear_log': 'Protokoll löschen',
    'btn_validate': 'Eingabedaten überprüfen',
    'btn_run': 'Integration starten',
    'tip_run': (
        'Startet die ausgewählte Integrationsmethode. Die Eingabedaten und '
        'Ausgabeparameter werden vor der Verarbeitung überprüft.'),
    'btn_cancel': 'Verarbeitung abbrechen',
    'tip_cancel': (
        'Bricht die laufende Integration ab. Die Verarbeitung wird am '
        'nächsten sicheren Kontrollpunkt gestoppt, und die endgültige '
        'Ausgabedatei wird nicht überschrieben.'),
    'btn_close': 'Schließen',
}