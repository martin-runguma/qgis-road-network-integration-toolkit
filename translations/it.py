"""Interface language pack for it. Missing reviewed text uses English fallback."""

# -----------------------------------------------------------------
# Italian
TEXT = {
    'win_title': "Strumento di integrazione delle reti stradali",
    'app_subtitle': 'Armonizzazione delle reti stradali prioritarie e secondarie',
    'language': 'Lingua:',

    'grp_input': 'Dati di input',
    'ph_priority': 'Seleziona il dataset della rete stradale prioritaria',
    'ph_secondary': 'Seleziona il dataset della rete stradale secondaria',
    'ph_boundary': "Seleziona il confine dell'area di studio",
    'lbl_priority': 'Rete stradale prioritaria:',
    'lbl_secondary': 'Rete stradale secondaria:',
    'lbl_boundary': "Confine dell'area di studio:",
    'hint_input': (
        'Utilizza Sfoglia per selezionare un file vettoriale o un layer '
        'di un GeoPackage (.gpkg) o di un File Geodatabase (.gdb). Vengono '
        'proposti solo i layer con il tipo di geometria previsto '
        '(linee per le strade, poligoni per il confine).'),
    'btn_browse': 'Sfoglia…',
    'tip_path': (
        'Questo campo mostra il percorso della sorgente dati. Utilizza '
        'Sfoglia per selezionare un file o uno specifico layer '
        'di un GeoPackage (.gpkg) o di un File Geodatabase (.gdb).'),
    'tip_browse': (
        'Sfoglia per selezionare un file vettoriale o un layer '
        'di un GeoPackage / File Geodatabase'),
    'menu_vector_file': 'File vettoriale o GeoPackage…',
    'menu_gdb': 'File Geodatabase (.gdb)…',

    'grp_settings': "Impostazioni di integrazione",
    'lbl_method': 'Metodologia:',
    'meth_1': 'Metodologia 1 — Fusione diretta',
    'meth_2': 'Metodologia 2 — Ritaglio + aggancio',
    'meth_3': 'Metodologia 3 — Aggancio mirato',
    'tip_method': (
        'La Metodologia 1 unisce direttamente le strade secondarie '
        'classificate da missing_1 a missing_4. La Metodologia 2 ritaglia '
        'le strade secondarie utilizzando i buffer della rete prioritaria '
        'e aggancia i relativi estremi. La Metodologia 3 utilizza buffer '
        'quadrati secondari e un aggancio mirato dei centroidi e degli estremi.'),
    'lbl_crs': 'CRS di analisi:',
    'tip_crs': (
        'Seleziona il sistema di riferimento delle coordinate proiettato '
        'utilizzato per le operazioni di distanza e aggancio. Scegli un CRS '
        'proiettato locale adatto alla tua area di studio.'),
    'btn_suggest_crs': "Suggerisci in base all'area di studio",
    'tip_suggest_crs': (
        "Seleziona la zona UTM che contiene il centro del confine "
        "dell'area di studio."),
    'hint_crs': (
        'Selezionalo come negli strumenti di esportazione o riproiezione '
        'di QGIS. È necessario un CRS proiettato in metri per le elaborazioni '
        'basate sulle distanze. Quando selezioni il confine dell’area di '
        'studio, viene suggerita automaticamente una zona UTM appropriata, '
        'a meno che tu non abbia già selezionato un CRS.'),

    'grp_advanced': 'Impostazioni avanzate',
    'adv_base_buffer': 'Distanza del buffer della rete prioritaria',
    'adv_secondary_buffer': 'Distanza del buffer della rete secondaria',
    'adv_join_gap': 'Distanza massima di aggancio',
    'adv_mid_gap': 'Intervallo di densificazione dei punti intermedi',
    'adv_centroid_max_dist': 'Distanza massima di spostamento del centroide',
    'tip_base_buffer': 'Distanza del buffer della rete stradale prioritaria.',
    'tip_secondary_buffer': 'Distanza del buffer della rete stradale secondaria.',
    'tip_join_gap': 'Distanza massima di aggancio tra gli elementi stradali.',
    'tip_mid_gap': 'Intervallo di densificazione dei punti intermedi.',
    'tip_centroid_max_dist': (
        'Distanza massima di spostamento del centroide verso un vertice.'),
    'hint_advanced': (
        'I valori visualizzati sono i valori predefiniti del flusso di '
        'lavoro, espressi in metri. Seleziona Impostazioni avanzate per '
        'modificarli; deselezionandole vengono ripristinati i valori '
        'predefiniti. I valori vengono trasmessi al motore di elaborazione '
        'compatibile con la versione precedente per le operazioni di buffer, '
        'ritaglio e aggancio.'),

    'grp_output': 'Impostazioni di output',
    'lbl_output_folder': 'Cartella di output:',
    'ph_output_folder': (
        'Seleziona la cartella di output / di lavoro obbligatoria...'),
    'tip_output_folder': (
        'Obbligatorio. Questa cartella viene utilizzata sia come directory '
        'di lavoro sia come destinazione dei risultati.'),
    'lbl_output_name': 'Nome output:',
    'ph_output_name': 'Inserisci un codice di progetto o città, ad es. KE_Nairobi',
    'tip_output_name': (
        "Inserisci solo il prefisso. Lo strumento aggiungerà automaticamente "
        "'{suffix}'."),
    'lbl_output_format': 'Formato di output:',
    'tip_output_format': (
        'Seleziona il formato del risultato finale della rete stradale '
        'armonizzata.'),
    'lbl_output_preview': 'Anteprima output:',
    'preview_empty': (
        'Inserisci un nome per l’output (ad es. KE_Nairobi) per visualizzare '
        'il nome del file finale.'),
    'chk_add_outputs': (
        'Aggiungi automaticamente al progetto QGIS gli output elaborati con successo'),
    'chk_keep_intermediates': 'Mantieni i layer diagnostici intermedi',

    'panel_log': 'Registro di elaborazione',
    'status_ready': (
        'Pronto. Seleziona i dati e avvia una metodologia.'),
    'ph_log': 'Qui verranno visualizzati i messaggi di convalida e di elaborazione.',
    'btn_clear_log': 'Cancella registro',
    'btn_validate': 'Convalida input',
    'btn_run': "Avvia integrazione",
    'tip_run': (
        'Avvia la metodologia di integrazione selezionata. Gli input e '
        'i parametri di output vengono verificati prima dell’elaborazione.'),
    'btn_cancel': "Annulla elaborazione",
    'tip_cancel': (
        'Interrompe l’integrazione in corso. L’elaborazione si arresta '
        'al successivo punto di controllo sicuro e l’output finale non '
        'viene sovrascritto.'),
    'btn_close': 'Chiudi',
}