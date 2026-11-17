"""
Interface translations for the Road Network Merging and Alignment Toolkit.

The six original, fully populated language blocks are retained unchanged:
English, French, Spanish, Portuguese, Swahili and Arabic. The language
catalogue also includes the 27 additional languages used by the companion
UN-Habitat plugin. Additional translations can be supplied as modules in
translations/<language_code>.py; each module should expose a TEXT dictionary
using the same keys as the English block.

Missing strings always fall back to English. This keeps the interface
functional while additional language packs are being completed.

Placeholders such as {suffix} must be preserved in every translation.
"""

LANGUAGES = [
    ('en', 'English'),
    ('fr', 'Français'),
    ('es', 'Español'),
    ('it', 'Italiano'),
    ('zh', '中文'),
    ('ar', 'العربية'),
    ('pt', 'Português'),
    ('de', 'Deutsch'),
    ('ru', 'Русский'),
    ('ja', '日本語'),
    ('sw', 'Kiswahili'),
    ('sv', 'Svenska'),
    ('nb', 'Norsk (bokmål)'),
    ('da', 'Dansk'),
    ('hi', 'हिन्दी'),
    ('bn', 'বাংলা'),
    ('ur', 'اردو'),
    ('pa', 'ਪੰਜਾਬੀ'),
    ('mr', 'मराठी'),
    ('te', 'తెలుగు'),
    ('ta', 'தமிழ்'),
    ('gu', 'ગુજરાતી'),
    ('id', 'Bahasa Indonesia'),
    ('tr', 'Türkçe'),
    ('ko', '한국어'),
    ('vi', 'Tiếng Việt'),
    ('fa', 'فارسی'),
    ('th', 'ไทย'),
    ('pl', 'Polski'),
    ('nl', 'Nederlands'),
    ('uk', 'Українська'),
    ('am', 'አማርኛ'),
    ('ha', 'Hausa'),
]

# QGIS locale prefixes that map onto supported language codes.
LOCALE_ALIASES = {'no': 'nb', 'nn': 'nb', 'in': 'id'}

# Arabic, Urdu and Persian use right-to-left text direction.
RTL_LANGUAGES = {'ar', 'ur', 'fa'}

SETTINGS_KEY = 'RoadNetworkIntegration/language'

TEXT = {}

# ---------------------------------------------------------------- English
TEXT['en'] = {
    'win_title': 'Road Network Merging and Alignment Toolkit',
    'app_subtitle': 'A QGIS Toolkit for Integrating and Harmonising Road Networks from Multiple Sources',
    'language': 'Language:',

    'grp_input': 'Input data',
    'ph_priority': 'Select the priority road dataset',
    'ph_secondary': 'Select the secondary road dataset',
    'ph_boundary': 'Select the study-area boundary',
    'lbl_priority': 'Priority road network:',
    'lbl_secondary': 'Secondary road network:',
    'lbl_boundary': 'Study area boundary:',
    'hint_input': (
        'Use Browse to choose a vector file or a layer inside a GeoPackage '
        '(.gpkg) or File Geodatabase (.gdb). Only layers with the expected '
        'geometry type (lines for roads, polygons for the boundary) are '
        'offered.'),
    'btn_browse': 'Browse…',
    'tip_path': (
        'This field displays the datasource path. Use Browse to select a '
        'file or a specific feature layer inside a GeoPackage (.gpkg) or '
        'File Geodatabase (.gdb).'),
    'tip_browse': (
        'Browse for a vector file or a feature layer inside a '
        'GeoPackage/File Geodatabase'),
    'menu_vector_file': 'Vector file or GeoPackage…',
    'menu_gdb': 'File Geodatabase (.gdb)…',

    'grp_settings': 'Integration settings',
    'lbl_method': 'Methodology:',
    'meth_1': 'Methodology 1 — Direct Merge',
    'meth_2': 'Methodology 2 — Clip + Snap',
    'meth_3': 'Methodology 3 — Targeted Snap',
    'tip_method': (
        'Methodology 1 directly merges secondary roads classified as '
        'missing_1 to missing_4. Methodology 2 trims secondary roads by '
        'priority-road buffers and snaps their endpoints. Methodology 3 '
        'uses secondary square buffers and targeted centroid/endpoint '
        'snapping.'),
    'lbl_crs': 'Analysis CRS:',
    'tip_crs': (
        'Choose the projected coordinate reference system used for distance '
        'and snapping operations. Select a suitable local projected CRS for '
        'your study area.'),
    'btn_suggest_crs': 'Suggest from study area',
    'tip_suggest_crs': (
        'Select the UTM zone that contains the centre of the study-area '
        'boundary.'),
    'hint_crs': (
        'Choose this the same way you select a CRS in QGIS export or '
        'reprojection tools. A projected CRS with metre units is required '
        'for distance-based processing. When you pick a study-area boundary, '
        'a suitable UTM zone is suggested automatically unless you have '
        'already chosen a CRS yourself.'),

    'grp_advanced': 'Advanced settings',
    'adv_base_buffer': 'Priority road buffer distance',
    'adv_secondary_buffer': 'Secondary road buffer distance',
    'adv_join_gap': 'Maximum snapping distance',
    'adv_mid_gap': 'Midpoint densification interval',
    'adv_centroid_max_dist': 'Maximum centroid adjustment distance',
    'tip_base_buffer': 'Buffer distance for the priority road network.',
    'tip_secondary_buffer': 'Buffer distance for the secondary road network.',
    'tip_join_gap': 'Maximum snapping distance between road features.',
    'tip_mid_gap': 'Midpoint densification interval.',
    'tip_centroid_max_dist': 'Maximum centroid-to-vertex adjustment distance.',
    'hint_advanced': (
        'The displayed values are the workflow defaults, in metres. Tick '
        'Advanced settings to edit them; unticking restores the defaults. '
        'These values are passed to the legacy-compatible processing engine '
        'for buffer, trimming, and snapping operations.'),

    'grp_output': 'Output settings',
    'lbl_output_folder': 'Output folder:',
    'ph_output_folder': 'Select the mandatory output / working folder...',
    'tip_output_folder': (
        'Required. This folder will be used as both the working directory '
        'and the output destination.'),
    'lbl_output_name': 'Output name:',
    'ph_output_name': 'Enter a project or city code, e.g. KE_Nairobi',
    'tip_output_name': (
        "Enter the prefix only. The toolkit adds '{suffix}' automatically."),
    'lbl_output_format': 'Output format:',
    'tip_output_format': (
        'Choose the format for the final harmonized road-network output.'),
    'lbl_output_preview': 'Output preview:',
    'preview_empty': (
        'Enter an output name (e.g. KE_Nairobi) to preview the final '
        'filename.'),
    'chk_add_outputs': (
        'Automatically add successful outputs to the QGIS project'),
    'chk_keep_intermediates': 'Keep intermediate diagnostic layers',

    'panel_log': 'Processing log',
    'status_ready': 'Ready. Select your inputs and run a methodology.',
    'ph_log': 'Validation and processing messages will appear here.',
    'btn_clear_log': 'Clear log',
    'btn_validate': 'Validate Inputs',
    'btn_run': 'Run Integration',
    'tip_run': (
        'Run the selected integration methodology. Inputs and output '
        'settings will be checked before processing.'),
    'btn_cancel': 'Cancel Run',
    'tip_cancel': (
        'Stop the running integration. Processing stops at the next safe '
        'checkpoint, and the final output is not replaced.'),
    'btn_close': 'Close',
}

# ----------------------------------------------------------------- French
TEXT['fr'] = {
    'win_title': "Boîte à outils d'intégration des réseaux routiers",
    'app_subtitle': 'Harmoniser les réseaux routiers prioritaire et secondaire',
    'language': 'Langue :',

    'grp_input': "Données d'entrée",
    'ph_priority': 'Sélectionnez le jeu de données du réseau prioritaire',
    'ph_secondary': 'Sélectionnez le jeu de données du réseau secondaire',
    'ph_boundary': "Sélectionnez la limite de la zone d'étude",
    'lbl_priority': 'Réseau routier prioritaire :',
    'lbl_secondary': 'Réseau routier secondaire :',
    'lbl_boundary': "Limite de la zone d'étude :",
    'hint_input': (
        'Utilisez Parcourir pour choisir un fichier vectoriel ou une couche '
        "d'un GeoPackage (.gpkg) ou d'une géodatabase fichier (.gdb). Seules "
        'les couches du type de géométrie attendu (lignes pour les routes, '
        'polygones pour la limite) sont proposées.'),
    'btn_browse': 'Parcourir…',
    'tip_path': (
        'Ce champ affiche le chemin de la source de données. Utilisez '
        'Parcourir pour sélectionner un fichier ou une couche précise '
        "d'un GeoPackage (.gpkg) ou d'une géodatabase fichier (.gdb)."),
    'tip_browse': (
        'Parcourir pour choisir un fichier vectoriel ou une couche '
        "d'un GeoPackage / d'une géodatabase fichier"),
    'menu_vector_file': 'Fichier vectoriel ou GeoPackage…',
    'menu_gdb': 'Géodatabase fichier (.gdb)…',

    'grp_settings': "Paramètres d'intégration",
    'lbl_method': 'Méthodologie :',
    'meth_1': 'Méthodologie 1 — Fusion directe',
    'meth_2': 'Méthodologie 2 — Découpage + accrochage',
    'meth_3': 'Méthodologie 3 — Accrochage ciblé',
    'tip_method': (
        'La méthodologie 1 fusionne directement les routes secondaires '
        'classées de missing_1 à missing_4. La méthodologie 2 découpe les '
        'routes secondaires avec les tampons du réseau prioritaire et accroche '
        'leurs extrémités. La méthodologie 3 utilise des tampons carrés '
        'secondaires et un accrochage ciblé des centroïdes et extrémités.'),
    'lbl_crs': "SCR d'analyse :",
    'tip_crs': (
        'Choisissez le système de coordonnées projeté utilisé pour les '
        "opérations de distance et d'accrochage. Sélectionnez un SCR projeté "
        "local adapté à votre zone d'étude."),
    'btn_suggest_crs': "Suggérer d'après la zone d'étude",
    'tip_suggest_crs': (
        "Sélectionne le fuseau UTM contenant le centre de la limite de la "
        "zone d'étude."),
    'hint_crs': (
        "Choisissez-le comme dans les outils d'exportation ou de "
        'reprojection de QGIS. Un SCR projeté en mètres est requis pour les '
        "traitements basés sur les distances. Lorsque vous choisissez la "
        "limite de la zone d'étude, un fuseau UTM adapté est suggéré "
        "automatiquement, sauf si vous avez déjà choisi un SCR."),

    'grp_advanced': 'Paramètres avancés',
    'adv_base_buffer': 'Distance de tampon du réseau prioritaire',
    'adv_secondary_buffer': 'Distance de tampon du réseau secondaire',
    'adv_join_gap': "Distance d'accrochage maximale",
    'adv_mid_gap': 'Intervalle de densification des points médians',
    'adv_centroid_max_dist': "Distance maximale d'ajustement du centroïde",
    'tip_base_buffer': 'Distance de tampon du réseau routier prioritaire.',
    'tip_secondary_buffer': 'Distance de tampon du réseau routier secondaire.',
    'tip_join_gap': "Distance d'accrochage maximale entre les entités routières.",
    'tip_mid_gap': 'Intervalle de densification des points médians.',
    'tip_centroid_max_dist': (
        "Distance maximale d'ajustement du centroïde vers un sommet."),
    'hint_advanced': (
        'Les valeurs affichées sont les valeurs par défaut du flux de '
        'travail, en mètres. Cochez Paramètres avancés pour les modifier ; '
        'décocher rétablit les valeurs par défaut. Elles sont transmises au '
        'moteur de traitement compatible avec la version historique pour les '
        "opérations de tampon, de découpage et d'accrochage."),

    'grp_output': 'Paramètres de sortie',
    'lbl_output_folder': 'Dossier de sortie :',
    'ph_output_folder': (
        'Sélectionnez le dossier de sortie / de travail obligatoire...'),
    'tip_output_folder': (
        'Obligatoire. Ce dossier sert à la fois de répertoire de travail et '
        'de destination de sortie.'),
    'lbl_output_name': 'Nom de sortie :',
    'ph_output_name': 'Saisissez un code de projet ou de ville, p. ex. KE_Nairobi',
    'tip_output_name': (
        "Saisissez uniquement le préfixe. L'outil ajoute automatiquement "
        "'{suffix}'."),
    'lbl_output_format': 'Format de sortie :',
    'tip_output_format': (
        "Choisissez le format de la sortie finale du réseau routier "
        'harmonisé.'),
    'lbl_output_preview': 'Aperçu de la sortie :',
    'preview_empty': (
        'Saisissez un nom de sortie (p. ex. KE_Nairobi) pour voir le nom de '
        'fichier final.'),
    'chk_add_outputs': (
        'Ajouter automatiquement les sorties réussies au projet QGIS'),
    'chk_keep_intermediates': 'Conserver les couches de diagnostic intermédiaires',

    'panel_log': 'Journal de traitement',
    'status_ready': (
        'Prêt. Sélectionnez vos données et lancez une méthodologie.'),
    'ph_log': 'Les messages de validation et de traitement apparaîtront ici.',
    'btn_clear_log': 'Effacer le journal',
    'btn_validate': 'Valider les entrées',
    'btn_run': "Lancer l'intégration",
    'tip_run': (
        "Lance la méthodologie d'intégration sélectionnée. Les entrées et "
        'les paramètres de sortie sont vérifiés avant le traitement.'),
    'btn_cancel': "Annuler l'exécution",
    'tip_cancel': (
        "Arrête l'intégration en cours. Le traitement s'arrête au prochain "
        "point de contrôle sûr et la sortie finale n'est pas remplacée."),
    'btn_close': 'Fermer',
}

# ---------------------------------------------------------------- Spanish
TEXT['es'] = {
    'win_title': 'Herramienta de integración de redes viales',
    'app_subtitle': 'Armonizar las redes viales prioritaria y secundaria',
    'language': 'Idioma:',

    'grp_input': 'Datos de entrada',
    'ph_priority': 'Seleccione el conjunto de datos de la red prioritaria',
    'ph_secondary': 'Seleccione el conjunto de datos de la red secundaria',
    'ph_boundary': 'Seleccione el límite del área de estudio',
    'lbl_priority': 'Red vial prioritaria:',
    'lbl_secondary': 'Red vial secundaria:',
    'lbl_boundary': 'Límite del área de estudio:',
    'hint_input': (
        'Use Examinar para elegir un archivo vectorial o una capa dentro de '
        'un GeoPackage (.gpkg) o una geodatabase de archivos (.gdb). Solo se '
        'ofrecen capas con el tipo de geometría esperado (líneas para las '
        'vías, polígonos para el límite).'),
    'btn_browse': 'Examinar…',
    'tip_path': (
        'Este campo muestra la ruta de la fuente de datos. Use Examinar para '
        'seleccionar un archivo o una capa concreta dentro de un GeoPackage '
        '(.gpkg) o una geodatabase de archivos (.gdb).'),
    'tip_browse': (
        'Examinar un archivo vectorial o una capa dentro de un GeoPackage / '
        'geodatabase de archivos'),
    'menu_vector_file': 'Archivo vectorial o GeoPackage…',
    'menu_gdb': 'Geodatabase de archivos (.gdb)…',

    'grp_settings': 'Configuración de la integración',
    'lbl_method': 'Metodología:',
    'meth_1': 'Metodología 1 — Fusión directa',
    'meth_2': 'Metodología 2 — Recorte + ajuste',
    'meth_3': 'Metodología 3 — Ajuste dirigido',
    'tip_method': (
        'La metodología 1 fusiona directamente las vías secundarias '
        'clasificadas de missing_1 a missing_4. La metodología 2 recorta las '
        'vías secundarias con los búferes de la red prioritaria y ajusta sus '
        'extremos. La metodología 3 usa búferes cuadrados secundarios y un '
        'ajuste dirigido de centroides y extremos.'),
    'lbl_crs': 'SRC de análisis:',
    'tip_crs': (
        'Elija el sistema de referencia de coordenadas proyectado usado para '
        'las operaciones de distancia y ajuste. Seleccione un SRC proyectado '
        'local adecuado para su área de estudio.'),
    'btn_suggest_crs': 'Sugerir según el área de estudio',
    'tip_suggest_crs': (
        'Selecciona la zona UTM que contiene el centro del límite del área '
        'de estudio.'),
    'hint_crs': (
        'Elíjalo igual que en las herramientas de exportación o '
        'reproyección de QGIS. Se requiere un SRC proyectado en metros para '
        'el procesamiento basado en distancias. Al elegir el límite del área '
        'de estudio se sugiere automáticamente una zona UTM adecuada, salvo '
        'que ya haya elegido un SRC.'),

    'grp_advanced': 'Configuración avanzada',
    'adv_base_buffer': 'Distancia de búfer de la red prioritaria',
    'adv_secondary_buffer': 'Distancia de búfer de la red secundaria',
    'adv_join_gap': 'Distancia máxima de ajuste',
    'adv_mid_gap': 'Intervalo de densificación de puntos medios',
    'adv_centroid_max_dist': 'Distancia máxima de ajuste del centroide',
    'tip_base_buffer': 'Distancia de búfer de la red vial prioritaria.',
    'tip_secondary_buffer': 'Distancia de búfer de la red vial secundaria.',
    'tip_join_gap': 'Distancia máxima de ajuste entre entidades viales.',
    'tip_mid_gap': 'Intervalo de densificación de puntos medios.',
    'tip_centroid_max_dist': (
        'Distancia máxima de ajuste del centroide al vértice.'),
    'hint_advanced': (
        'Los valores mostrados son los predeterminados del flujo de trabajo, '
        'en metros. Marque Configuración avanzada para editarlos; al '
        'desmarcarla se restauran los valores predeterminados. Se pasan al '
        'motor de procesamiento compatible con la versión anterior para las '
        'operaciones de búfer, recorte y ajuste.'),

    'grp_output': 'Configuración de salida',
    'lbl_output_folder': 'Carpeta de salida:',
    'ph_output_folder': (
        'Seleccione la carpeta de salida / trabajo obligatoria...'),
    'tip_output_folder': (
        'Obligatorio. Esta carpeta se usará como directorio de trabajo y '
        'como destino de salida.'),
    'lbl_output_name': 'Nombre de salida:',
    'ph_output_name': 'Introduzca un código de proyecto o ciudad, p. ej. KE_Nairobi',
    'tip_output_name': (
        "Introduzca solo el prefijo. La herramienta añade '{suffix}' "
        'automáticamente.'),
    'lbl_output_format': 'Formato de salida:',
    'tip_output_format': (
        'Elija el formato de la salida final de la red vial armonizada.'),
    'lbl_output_preview': 'Vista previa de la salida:',
    'preview_empty': (
        'Introduzca un nombre de salida (p. ej. KE_Nairobi) para ver el '
        'nombre de archivo final.'),
    'chk_add_outputs': (
        'Añadir automáticamente las salidas correctas al proyecto de QGIS'),
    'chk_keep_intermediates': 'Conservar las capas de diagnóstico intermedias',

    'panel_log': 'Registro de procesamiento',
    'status_ready': (
        'Listo. Seleccione sus entradas y ejecute una metodología.'),
    'ph_log': 'Los mensajes de validación y procesamiento aparecerán aquí.',
    'btn_clear_log': 'Borrar registro',
    'btn_validate': 'Validar entradas',
    'btn_run': 'Ejecutar integración',
    'tip_run': (
        'Ejecuta la metodología de integración seleccionada. Las entradas y '
        'la configuración de salida se comprobarán antes del procesamiento.'),
    'btn_cancel': 'Cancelar ejecución',
    'tip_cancel': (
        'Detiene la integración en curso. El procesamiento se detiene en el '
        'siguiente punto de control seguro y la salida final no se '
        'reemplaza.'),
    'btn_close': 'Cerrar',
}

# ------------------------------------------------------------- Portuguese
TEXT['pt'] = {
    'win_title': 'Ferramenta de integração de redes viárias',
    'app_subtitle': 'Harmonizar as redes viárias prioritária e secundária',
    'language': 'Idioma:',

    'grp_input': 'Dados de entrada',
    'ph_priority': 'Selecione o conjunto de dados da rede prioritária',
    'ph_secondary': 'Selecione o conjunto de dados da rede secundária',
    'ph_boundary': 'Selecione o limite da área de estudo',
    'lbl_priority': 'Rede viária prioritária:',
    'lbl_secondary': 'Rede viária secundária:',
    'lbl_boundary': 'Limite da área de estudo:',
    'hint_input': (
        'Use Procurar para escolher um ficheiro vetorial ou uma camada dentro '
        'de um GeoPackage (.gpkg) ou de uma geodatabase de ficheiros (.gdb). '
        'Só são oferecidas camadas com o tipo de geometria esperado (linhas '
        'para as vias, polígonos para o limite).'),
    'btn_browse': 'Procurar…',
    'tip_path': (
        'Este campo mostra o caminho da fonte de dados. Use Procurar para '
        'selecionar um ficheiro ou uma camada específica dentro de um '
        'GeoPackage (.gpkg) ou de uma geodatabase de ficheiros (.gdb).'),
    'tip_browse': (
        'Procurar um ficheiro vetorial ou uma camada dentro de um GeoPackage '
        '/ geodatabase de ficheiros'),
    'menu_vector_file': 'Ficheiro vetorial ou GeoPackage…',
    'menu_gdb': 'Geodatabase de ficheiros (.gdb)…',

    'grp_settings': 'Definições de integração',
    'lbl_method': 'Metodologia:',
    'meth_1': 'Metodologia 1 — Fusão direta',
    'meth_2': 'Metodologia 2 — Recorte + ajuste',
    'meth_3': 'Metodologia 3 — Ajuste dirigido',
    'tip_method': (
        'A metodologia 1 funde diretamente as vias secundárias classificadas '
        'de missing_1 a missing_4. A metodologia 2 recorta as vias '
        'secundárias com os buffers da rede prioritária e ajusta as suas '
        'extremidades. A metodologia 3 usa buffers quadrados secundários e '
        'ajuste dirigido de centroides e extremidades.'),
    'lbl_crs': 'SRC de análise:',
    'tip_crs': (
        'Escolha o sistema de referência de coordenadas projetado usado nas '
        'operações de distância e ajuste. Selecione um SRC projetado local '
        'adequado à sua área de estudo.'),
    'btn_suggest_crs': 'Sugerir a partir da área de estudo',
    'tip_suggest_crs': (
        'Seleciona a zona UTM que contém o centro do limite da área de '
        'estudo.'),
    'hint_crs': (
        'Escolha-o como nas ferramentas de exportação ou reprojeção do QGIS. '
        'É necessário um SRC projetado em metros para o processamento '
        'baseado em distâncias. Ao escolher o limite da área de estudo, é '
        'sugerida automaticamente uma zona UTM adequada, a menos que já tenha '
        'escolhido um SRC.'),

    'grp_advanced': 'Definições avançadas',
    'adv_base_buffer': 'Distância de buffer da rede prioritária',
    'adv_secondary_buffer': 'Distância de buffer da rede secundária',
    'adv_join_gap': 'Distância máxima de ajuste',
    'adv_mid_gap': 'Intervalo de densificação de pontos médios',
    'adv_centroid_max_dist': 'Distância máxima de ajuste do centroide',
    'tip_base_buffer': 'Distância de buffer da rede viária prioritária.',
    'tip_secondary_buffer': 'Distância de buffer da rede viária secundária.',
    'tip_join_gap': 'Distância máxima de ajuste entre elementos viários.',
    'tip_mid_gap': 'Intervalo de densificação de pontos médios.',
    'tip_centroid_max_dist': (
        'Distância máxima de ajuste do centroide ao vértice.'),
    'hint_advanced': (
        'Os valores apresentados são os predefinidos do fluxo de trabalho, em '
        'metros. Assinale Definições avançadas para os editar; desassinalar '
        'repõe os valores predefinidos. São passados ao motor de '
        'processamento compatível com a versão anterior para as operações de '
        'buffer, recorte e ajuste.'),

    'grp_output': 'Definições de saída',
    'lbl_output_folder': 'Pasta de saída:',
    'ph_output_folder': (
        'Selecione a pasta de saída / trabalho obrigatória...'),
    'tip_output_folder': (
        'Obrigatório. Esta pasta será usada como diretório de trabalho e '
        'como destino de saída.'),
    'lbl_output_name': 'Nome de saída:',
    'ph_output_name': 'Introduza um código de projeto ou cidade, p. ex. KE_Nairobi',
    'tip_output_name': (
        "Introduza apenas o prefixo. A ferramenta adiciona '{suffix}' "
        'automaticamente.'),
    'lbl_output_format': 'Formato de saída:',
    'tip_output_format': (
        'Escolha o formato da saída final da rede viária harmonizada.'),
    'lbl_output_preview': 'Pré-visualização da saída:',
    'preview_empty': (
        'Introduza um nome de saída (p. ex. KE_Nairobi) para pré-visualizar '
        'o nome de ficheiro final.'),
    'chk_add_outputs': (
        'Adicionar automaticamente as saídas bem-sucedidas ao projeto QGIS'),
    'chk_keep_intermediates': 'Manter as camadas de diagnóstico intermédias',

    'panel_log': 'Registo de processamento',
    'status_ready': (
        'Pronto. Selecione as entradas e execute uma metodologia.'),
    'ph_log': 'As mensagens de validação e processamento aparecerão aqui.',
    'btn_clear_log': 'Limpar registo',
    'btn_validate': 'Validar entradas',
    'btn_run': 'Executar integração',
    'tip_run': (
        'Executa a metodologia de integração selecionada. As entradas e as '
        'definições de saída serão verificadas antes do processamento.'),
    'btn_cancel': 'Cancelar execução',
    'tip_cancel': (
        'Para a integração em curso. O processamento pára no próximo ponto '
        'de controlo seguro e a saída final não é substituída.'),
    'btn_close': 'Fechar',
}

# ---------------------------------------------------------------- Swahili
TEXT['sw'] = {
    'win_title': 'Zana ya Kuunganisha Mitandao ya Barabara',
    'app_subtitle': 'Oanisha mitandao ya barabara za kipaumbele na za pili',
    'language': 'Lugha:',

    'grp_input': 'Data ya kuingiza',
    'ph_priority': 'Chagua seti ya data ya barabara za kipaumbele',
    'ph_secondary': 'Chagua seti ya data ya barabara za pili',
    'ph_boundary': 'Chagua mpaka wa eneo la utafiti',
    'lbl_priority': 'Mtandao wa barabara za kipaumbele:',
    'lbl_secondary': 'Mtandao wa barabara za pili:',
    'lbl_boundary': 'Mpaka wa eneo la utafiti:',
    'hint_input': (
        'Tumia Vinjari kuchagua faili ya vekta au safu ndani ya GeoPackage '
        '(.gpkg) au File Geodatabase (.gdb). Safu zenye aina ya jiometri '
        'inayotarajiwa pekee ndizo zinazotolewa (mistari kwa barabara, '
        'poligoni kwa mpaka).'),
    'btn_browse': 'Vinjari…',
    'tip_path': (
        'Sehemu hii inaonyesha njia ya chanzo cha data. Tumia Vinjari '
        'kuchagua faili au safu mahususi ndani ya GeoPackage (.gpkg) au '
        'File Geodatabase (.gdb).'),
    'tip_browse': (
        'Vinjari faili ya vekta au safu ndani ya GeoPackage / File '
        'Geodatabase'),
    'menu_vector_file': 'Faili ya vekta au GeoPackage…',
    'menu_gdb': 'File Geodatabase (.gdb)…',

    'grp_settings': 'Mipangilio ya uunganishaji',
    'lbl_method': 'Mbinu:',
    'meth_1': 'Mbinu 1 — Kuunganisha moja kwa moja',
    'meth_2': 'Mbinu 2 — Kukata + Kuambatanisha',
    'meth_3': 'Mbinu 3 — Kuambatanisha kulengwa',
    'tip_method': (
        'Mbinu 1 huunganisha moja kwa moja barabara za pili zilizoainishwa '
        'kama missing_1 hadi missing_4. Mbinu 2 hukata barabara za pili kwa '
        'bafa za barabara za kipaumbele na kuambatanisha ncha zake. Mbinu 3 '
        'hutumia bafa za mraba za barabara za pili na kuambatanisha kwa '
        'kulenga sentroidi na ncha.'),
    'lbl_crs': 'CRS ya uchambuzi:',
    'tip_crs': (
        'Chagua mfumo wa kuratibu uliotarajiwa unaotumika kwa shughuli za '
        'umbali na kuambatanisha. Chagua CRS ya ndani inayofaa eneo lako la '
        'utafiti.'),
    'btn_suggest_crs': 'Pendekeza kutoka eneo la utafiti',
    'tip_suggest_crs': (
        'Huchagua ukanda wa UTM unaojumuisha kitovu cha mpaka wa eneo la '
        'utafiti.'),
    'hint_crs': (
        'Chagua kama unavyochagua CRS katika zana za kusafirisha au '
        'kuprojekti upya za QGIS. CRS iliyoprojektiwa yenye vipimo vya mita '
        'inahitajika kwa uchakataji unaotegemea umbali. Ukichagua mpaka wa '
        'eneo la utafiti, ukanda wa UTM unaofaa hupendekezwa kiotomatiki '
        'isipokuwa tayari umechagua CRS mwenyewe.'),

    'grp_advanced': 'Mipangilio ya hali ya juu',
    'adv_base_buffer': 'Umbali wa bafa ya barabara za kipaumbele',
    'adv_secondary_buffer': 'Umbali wa bafa ya barabara za pili',
    'adv_join_gap': 'Umbali wa juu zaidi wa kuambatanisha',
    'adv_mid_gap': 'Muda wa kuongeza vertisi za kati',
    'adv_centroid_max_dist': 'Umbali wa juu zaidi wa kurekebisha sentroidi',
    'tip_base_buffer': 'Umbali wa bafa kwa mtandao wa barabara za kipaumbele.',
    'tip_secondary_buffer': 'Umbali wa bafa kwa mtandao wa barabara za pili.',
    'tip_join_gap': 'Umbali wa juu zaidi wa kuambatanisha kati ya vipengele vya barabara.',
    'tip_mid_gap': 'Muda wa kuongeza vertisi za kati.',
    'tip_centroid_max_dist': (
        'Umbali wa juu zaidi wa kurekebisha kutoka sentroidi hadi vertisi.'),
    'hint_advanced': (
        'Thamani zinazoonyeshwa ni chaguo-msingi za mtiririko wa kazi, kwa '
        'mita. Weka tiki kwenye Mipangilio ya hali ya juu ili kuzihariri; '
        'kuondoa tiki hurejesha chaguo-msingi. Thamani hizi hupitishwa kwa '
        'injini ya uchakataji inayooana na toleo la awali kwa shughuli za '
        'bafa, kukata na kuambatanisha.'),

    'grp_output': 'Mipangilio ya matokeo',
    'lbl_output_folder': 'Folda ya matokeo:',
    'ph_output_folder': 'Chagua folda ya matokeo / kazi inayohitajika...',
    'tip_output_folder': (
        'Inahitajika. Folda hii itatumika kama saraka ya kazi na mahali '
        'pa matokeo.'),
    'lbl_output_name': 'Jina la matokeo:',
    'ph_output_name': 'Weka msimbo wa mradi au jiji, mf. KE_Nairobi',
    'tip_output_name': (
        "Weka kiambishi awali pekee. Zana huongeza '{suffix}' kiotomatiki."),
    'lbl_output_format': 'Muundo wa matokeo:',
    'tip_output_format': (
        'Chagua muundo wa matokeo ya mwisho ya mtandao wa barabara '
        'uliooanishwa.'),
    'lbl_output_preview': 'Onyesho la awali la matokeo:',
    'preview_empty': (
        'Weka jina la matokeo (mf. KE_Nairobi) ili kuona jina la mwisho la '
        'faili.'),
    'chk_add_outputs': (
        'Ongeza kiotomatiki matokeo yaliyofanikiwa kwenye mradi wa QGIS'),
    'chk_keep_intermediates': 'Hifadhi safu za uchunguzi za kati',

    'panel_log': 'Kumbukumbu ya uchakataji',
    'status_ready': 'Tayari. Chagua data yako na uendeshe mbinu.',
    'ph_log': 'Ujumbe wa uhakiki na uchakataji utaonekana hapa.',
    'btn_clear_log': 'Futa kumbukumbu',
    'btn_validate': 'Hakiki data',
    'btn_run': 'Endesha uunganishaji',
    'tip_run': (
        'Huendesha mbinu ya uunganishaji iliyochaguliwa. Data ya kuingiza na '
        'mipangilio ya matokeo vitakaguliwa kabla ya uchakataji.'),
    'btn_cancel': 'Katisha uendeshaji',
    'tip_cancel': (
        'Husimamisha uunganishaji unaoendelea. Uchakataji husimama kwenye '
        'kituo salama kinachofuata, na matokeo ya mwisho hayabadilishwi.'),
    'btn_close': 'Funga',
}

# ----------------------------------------------------------------- Arabic
TEXT['ar'] = {
    'win_title': 'أداة دمج شبكات الطرق',
    'app_subtitle': 'مواءمة شبكتي الطرق ذات الأولوية والثانوية',
    'language': 'اللغة:',

    'grp_input': 'بيانات الإدخال',
    'ph_priority': 'اختر مجموعة بيانات الطرق ذات الأولوية',
    'ph_secondary': 'اختر مجموعة بيانات الطرق الثانوية',
    'ph_boundary': 'اختر حدود منطقة الدراسة',
    'lbl_priority': 'شبكة الطرق ذات الأولوية:',
    'lbl_secondary': 'شبكة الطرق الثانوية:',
    'lbl_boundary': 'حدود منطقة الدراسة:',
    'hint_input': (
        'استخدم «استعراض» لاختيار ملف متجهي أو طبقة داخل GeoPackage (.gpkg) '
        'أو File Geodatabase (.gdb). تُعرض فقط الطبقات ذات نوع الهندسة '
        'المتوقع (خطوط للطرق، ومضلعات للحدود).'),
    'btn_browse': 'استعراض…',
    'tip_path': (
        'يعرض هذا الحقل مسار مصدر البيانات. استخدم «استعراض» لاختيار ملف '
        'أو طبقة محددة داخل GeoPackage (.gpkg) أو File Geodatabase (.gdb).'),
    'tip_browse': (
        'استعرض للعثور على ملف متجهي أو طبقة داخل GeoPackage أو '
        'File Geodatabase.'),
    'menu_vector_file': 'ملف متجهي أو GeoPackage…',
    'menu_gdb': 'File Geodatabase (.gdb)…',

    'grp_settings': 'إعدادات الدمج',
    'lbl_method': 'المنهجية:',
    'meth_1': 'المنهجية 1 — الدمج المباشر',
    'meth_2': 'المنهجية 2 — القص + الالتقاط',
    'meth_3': 'المنهجية 3 — الالتقاط الموجّه',
    'tip_method': (
        'تدمج المنهجية 1 مباشرةً الطرق الثانوية المصنفة من missing_1 إلى '
        'missing_4. وتقص المنهجية 2 الطرق الثانوية بمناطق عازلة للطرق ذات '
        'الأولوية وتلتقط نهاياتها. وتستخدم المنهجية 3 مناطق عازلة مربعة '
        'للطرق الثانوية مع التقاط موجّه للمراكز الهندسية والنهايات.'),
    'lbl_crs': 'نظام الإحداثيات للتحليل:',
    'tip_crs': (
        'اختر نظام الإحداثيات المسقط المستخدم في عمليات المسافة والالتقاط. '
        'اختر نظام إحداثيات مسقطًا محليًا مناسبًا لمنطقة دراستك.'),
    'btn_suggest_crs': 'اقتراح من منطقة الدراسة',
    'tip_suggest_crs': (
        'يختار نطاق UTM الذي يحتوي على مركز حدود منطقة الدراسة.'),
    'hint_crs': (
        'اختره بالطريقة نفسها التي تختار بها نظام الإحداثيات في أدوات '
        'التصدير أو إعادة الإسقاط في QGIS. يلزم نظام إحداثيات مسقط بوحدة '
        'المتر للمعالجة المعتمدة على المسافات. عند اختيار حدود منطقة '
        'الدراسة يُقترح نطاق UTM مناسب تلقائيًا ما لم تكن قد اخترت نظام '
        'إحداثيات بنفسك.'),

    'grp_advanced': 'إعدادات متقدمة',
    'adv_base_buffer': 'مسافة المنطقة العازلة للطرق ذات الأولوية',
    'adv_secondary_buffer': 'مسافة المنطقة العازلة للطرق الثانوية',
    'adv_join_gap': 'أقصى مسافة التقاط',
    'adv_mid_gap': 'فترة تكثيف النقاط الوسطى',
    'adv_centroid_max_dist': 'أقصى مسافة لتعديل المركز الهندسي',
    'tip_base_buffer': 'مسافة المنطقة العازلة لشبكة الطرق ذات الأولوية.',
    'tip_secondary_buffer': 'مسافة المنطقة العازلة لشبكة الطرق الثانوية.',
    'tip_join_gap': 'أقصى مسافة التقاط بين عناصر الطرق.',
    'tip_mid_gap': 'فترة تكثيف النقاط الوسطى.',
    'tip_centroid_max_dist': 'أقصى مسافة لتعديل المركز الهندسي إلى الرأس.',
    'hint_advanced': (
        'القيم المعروضة هي القيم الافتراضية لسير العمل، بالمتر. فعّل '
        '«إعدادات متقدمة» لتعديلها؛ وإلغاء التفعيل يعيد القيم الافتراضية. '
        'تُمرَّر هذه القيم إلى محرك المعالجة المتوافق مع الإصدار السابق '
        'لعمليات المنطقة العازلة والقص والالتقاط.'),

    'grp_output': 'إعدادات المخرجات',
    'lbl_output_folder': 'مجلد المخرجات:',
    'ph_output_folder': 'اختر مجلد المخرجات / العمل الإلزامي...',
    'tip_output_folder': (
        'مطلوب. سيُستخدم هذا المجلد دليلَ عمل ووجهةَ للمخرجات معًا.'),
    'lbl_output_name': 'اسم المخرجات:',
    'ph_output_name': 'أدخل رمز المشروع أو المدينة، مثل KE_Nairobi',
    'tip_output_name': 'أدخل البادئة فقط. تضيف الأداة «{suffix}» تلقائيًا.',
    'lbl_output_format': 'صيغة المخرجات:',
    'tip_output_format': 'اختر صيغة المخرج النهائي لشبكة الطرق المتوائمة.',
    'lbl_output_preview': 'معاينة المخرجات:',
    'preview_empty': (
        'أدخل اسم المخرجات (مثل KE_Nairobi) لمعاينة اسم الملف النهائي.'),
    'chk_add_outputs': (
        'إضافة المخرجات الناجحة تلقائيًا إلى مشروع QGIS'),
    'chk_keep_intermediates': 'الاحتفاظ بطبقات التشخيص الوسيطة',

    'panel_log': 'سجل المعالجة',
    'status_ready': 'جاهز. اختر المدخلات وشغّل إحدى المنهجيات.',
    'ph_log': 'ستظهر هنا رسائل التحقق والمعالجة.',
    'btn_clear_log': 'مسح السجل',
    'btn_validate': 'التحقق من المدخلات',
    'btn_run': 'تشغيل الدمج',
    'tip_run': (
        'يشغّل منهجية الدمج المحددة. ستُفحص المدخلات وإعدادات المخرجات '
        'قبل المعالجة.'),
    'btn_cancel': 'إلغاء التشغيل',
    'tip_cancel': (
        'يوقف عملية الدمج الجارية. تتوقف المعالجة عند نقطة التحقق الآمنة '
        'التالية ولا يُستبدل المخرج النهائي.'),
    'btn_close': 'إغلاق',
}


# Phase 2: secondary-dialog and output-format labels.
# These keys are deliberately separate from provider/layer names, which must
# remain exactly as supplied by QGIS.
_PHASE2_TEXT = {
    'en': {
        'dlg_choose_layer': 'Choose feature layer',
        'dlg_available_layers': 'Available feature layers',
        'dlg_select_layer': 'Select layer',
        'dlg_cancel': 'Cancel',
        'dlg_selected': 'Selected: {name}',
        'fmt_gpkg': 'GeoPackage (.gpkg)',
        'fmt_shp': 'Shapefile (.shp)',
        'fmt_gdb': 'File Geodatabase (.gdb)',
        'prompt_select_layer': 'Select the feature layer for {name}:',
    },
    'fr': {
        'dlg_choose_layer': 'Choisir une couche d’entités',
        'dlg_available_layers': 'Couches d’entités disponibles',
        'dlg_select_layer': 'Sélectionner la couche', 'dlg_cancel': 'Annuler',
        'dlg_selected': 'Sélectionnée : {name}',
        'fmt_gpkg': 'GeoPackage (.gpkg)', 'fmt_shp': 'Shapefile (.shp)',
        'fmt_gdb': 'Géodatabase fichier (.gdb)',
        'prompt_select_layer': 'Sélectionnez la couche d’entités pour {name} :',
    },
    'es': {
        'dlg_choose_layer': 'Elegir capa de entidades',
        'dlg_available_layers': 'Capas de entidades disponibles',
        'dlg_select_layer': 'Seleccionar capa', 'dlg_cancel': 'Cancelar',
        'dlg_selected': 'Seleccionada: {name}',
        'fmt_gpkg': 'GeoPackage (.gpkg)', 'fmt_shp': 'Shapefile (.shp)',
        'fmt_gdb': 'Geodatabase de archivos (.gdb)',
        'prompt_select_layer': 'Seleccione la capa de entidades para {name}:',
    },
    'pt': {
        'dlg_choose_layer': 'Escolher camada de elementos',
        'dlg_available_layers': 'Camadas de elementos disponíveis',
        'dlg_select_layer': 'Selecionar camada', 'dlg_cancel': 'Cancelar',
        'dlg_selected': 'Selecionada: {name}',
        'fmt_gpkg': 'GeoPackage (.gpkg)', 'fmt_shp': 'Shapefile (.shp)',
        'fmt_gdb': 'Geodatabase de arquivos (.gdb)',
        'prompt_select_layer': 'Selecione a camada de elementos para {name}:',
    },
    'sw': {
        'dlg_choose_layer': 'Chagua tabaka la vipengele',
        'dlg_available_layers': 'Tabaka za vipengele zinazopatikana',
        'dlg_select_layer': 'Chagua tabaka', 'dlg_cancel': 'Ghairi',
        'dlg_selected': 'Lililochaguliwa: {name}',
        'fmt_gpkg': 'GeoPackage (.gpkg)', 'fmt_shp': 'Shapefile (.shp)',
        'fmt_gdb': 'Hifadhidata ya faili (.gdb)',
        'prompt_select_layer': 'Chagua tabaka la vipengele kwa {name}:',
    },
    'ar': {
        'dlg_choose_layer': 'اختيار طبقة المعالم',
        'dlg_available_layers': 'طبقات المعالم المتاحة',
        'dlg_select_layer': 'اختيار الطبقة', 'dlg_cancel': 'إلغاء',
        'dlg_selected': 'المحدد: {name}',
        'fmt_gpkg': 'GeoPackage (.gpkg)', 'fmt_shp': 'Shapefile (.shp)',
        'fmt_gdb': 'قاعدة بيانات جغرافية ملفية (.gdb)',
        'prompt_select_layer': 'اختر طبقة المعالم لـ {name}:',
    },
}
for _code, _entries in _PHASE2_TEXT.items():
    TEXT.setdefault(_code, dict(TEXT['en'])).update(_entries)

SUPPORTED = [code for code, _ in LANGUAGES]


def _normalise_language(lang):
    """Normalise QGIS language codes and locales (for example fr_FR, zh-CN)."""
    value = str(lang or 'en').strip().replace('-', '_').lower()
    code = value.split('_', 1)[0]
    code = LOCALE_ALIASES.get(code, code)
    return code if code in SUPPORTED else 'en'


def _load_optional_language_packs():
    """Load language modules relative to this plugin package.

    This works whether QGIS imports the plugin as a package (normal operation)
    or the module is loaded directly during development/tests.
    """
    import importlib

    package = __package__
    for code in SUPPORTED:
        if code in TEXT:
            continue

        module = None
        candidates = (
            (package + '.translations.' + code) if package else None,
            'translations.' + code,
        )
        for module_name in candidates:
            if not module_name:
                continue
            try:
                module = importlib.import_module(module_name)
                break
            except Exception:
                module = None

        if module is None:
            continue

        block = getattr(module, 'TEXT', None)
        if isinstance(block, dict):
            # Make every language dictionary complete. Untranslated long-form
            # help falls back to the English source rather than disappearing.
            merged = dict(TEXT['en'])
            merged.update({k: v for k, v in block.items()
                           if k in TEXT['en'] and isinstance(v, str) and v})
            TEXT[code] = merged


_load_optional_language_packs()


def tr(key, lang='en'):
    """Return a translated string, falling back to English and then the key."""
    code = _normalise_language(lang)
    value = TEXT.get(code, {}).get(key)
    if value is None or value == '':
        value = TEXT['en'].get(key, key)
    return value


def default_language():
    """Saved language, then the QGIS interface locale, then English."""
    try:
        from qgis.PyQt.QtCore import QSettings
        settings = QSettings()
        saved = settings.value(SETTINGS_KEY, '', type=str)
        if saved:
            saved_code = _normalise_language(saved)
            if saved_code != 'en' or str(saved).lower().startswith('en'):
                return saved_code

        locale = settings.value('locale/userLocale', '', type=str) or ''
        return _normalise_language(locale)
    except (ImportError, TypeError, AttributeError):
        return 'en'


def save_language(lang):
    """Save a supported language code and return the normalised code."""
    code = _normalise_language(lang)
    try:
        from qgis.PyQt.QtCore import QSettings
        QSettings().setValue(SETTINGS_KEY, code)
    except ImportError:
        pass
    return code


def translation_coverage(lang):
    """Return (translated, total) key counts for a language pack.

    English fallback values are excluded from the translated count.
    """
    code = _normalise_language(lang)
    block = TEXT.get(code, {})
    translated = sum(
        1 for key, value in block.items()
        if key in TEXT['en'] and value != TEXT['en'][key]
    )
    return translated, len(TEXT['en'])
