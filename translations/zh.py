"""Interface language pack for zh. Missing reviewed text uses English fallback."""


# -----------------------------------------------------------------
# Simplified Chinese (简体中文)
TEXT = {
    'win_title': '道路网络整合工具箱',
    'app_subtitle': '统一主要道路网络与次要道路网络',
    'language': '语言：',

    'grp_input': '输入数据',
    'ph_priority': '选择主要道路网络数据集',
    'ph_secondary': '选择次要道路网络数据集',
    'ph_boundary': '选择研究区域边界',
    'lbl_priority': '主要道路网络：',
    'lbl_secondary': '次要道路网络：',
    'lbl_boundary': '研究区域边界：',
    'hint_input': (
        '使用“浏览”选择矢量文件，或 GeoPackage (.gpkg) / '
        '文件地理数据库 (.gdb) 中的图层。仅显示符合预期几何类型的图层'
        '（道路使用线几何，边界使用面几何）。'),
    'btn_browse': '浏览…',
    'tip_path': (
        '此字段显示数据源路径。使用“浏览”选择文件，或选择 '
        'GeoPackage (.gpkg) / 文件地理数据库 (.gdb) 中的特定图层。'),
    'tip_browse': (
        '浏览并选择矢量文件，或 GeoPackage / 文件地理数据库中的图层'),
    'menu_vector_file': '矢量文件或 GeoPackage…',
    'menu_gdb': '文件地理数据库 (.gdb)…',

    'grp_settings': '整合设置',
    'lbl_method': '处理方法：',
    'meth_1': '方法 1 — 直接合并',
    'meth_2': '方法 2 — 裁剪 + 捕捉',
    'meth_3': '方法 3 — 定向捕捉',
    'tip_method': (
        '方法 1 直接合并分类为 missing_1 至 missing_4 的次要道路。'
        '方法 2 使用主要道路网络的缓冲区裁剪次要道路，并捕捉其端点。'
        '方法 3 使用次要道路的正方形缓冲区，并对质心和端点进行定向捕捉。'),
    'lbl_crs': '分析坐标参考系：',
    'tip_crs': (
        '选择用于距离计算和捕捉操作的投影坐标参考系。'
        '请选择适合研究区域的本地投影坐标参考系。'),
    'btn_suggest_crs': '根据研究区域推荐',
    'tip_suggest_crs': (
        '自动选择包含研究区域边界中心点的 UTM 分带。'),
    'hint_crs': (
        '请按照 QGIS 导出或重投影工具中的方式选择坐标参考系。'
        '基于距离的处理需要使用以米为单位的投影坐标参考系。'
        '选择研究区域边界后，系统将自动推荐合适的 UTM 分带，'
        '除非您已经手动选择了坐标参考系。'),

    'grp_advanced': '高级设置',
    'adv_base_buffer': '主要道路网络缓冲距离',
    'adv_secondary_buffer': '次要道路网络缓冲距离',
    'adv_join_gap': '最大捕捉距离',
    'adv_mid_gap': '中间点加密间隔',
    'adv_centroid_max_dist': '质心最大调整距离',
    'tip_base_buffer': '主要道路网络的缓冲距离。',
    'tip_secondary_buffer': '次要道路网络的缓冲距离。',
    'tip_join_gap': '道路要素之间允许的最大捕捉距离。',
    'tip_mid_gap': '中间点加密的间隔距离。',
    'tip_centroid_max_dist': '质心向顶点移动的最大允许距离。',
    'hint_advanced': (
        '显示的数值为工作流程的默认参数，单位为米。'
        '勾选“高级设置”可修改这些参数；取消勾选后将恢复默认值。'
        '这些参数将传递给与历史版本兼容的处理引擎，'
        '用于缓冲区、裁剪和捕捉操作。'),

    'grp_output': '输出设置',
    'lbl_output_folder': '输出文件夹：',
    'ph_output_folder': '请选择必需的输出 / 工作文件夹...',
    'tip_output_folder': (
        '必填。此文件夹同时用作工作目录和输出文件保存位置。'),
    'lbl_output_name': '输出名称：',
    'ph_output_name': '输入项目或城市代码，例如 KE_Nairobi',
    'tip_output_name': (
        '仅输入文件名前缀。工具将自动添加 '
        "'{suffix}'。"),
    'lbl_output_format': '输出格式：',
    'tip_output_format': (
        '选择最终整合道路网络的输出文件格式。'),
    'lbl_output_preview': '输出预览：',
    'preview_empty': (
        '请输入输出名称（例如 KE_Nairobi），以预览最终文件名。'),
    'chk_add_outputs': '自动将成功生成的输出添加到 QGIS 项目',
    'chk_keep_intermediates': '保留中间诊断图层',

    'panel_log': '处理日志',
    'status_ready': (
        '就绪。请选择输入数据并启动一种处理方法。'),
    'ph_log': '验证和处理消息将在此处显示。',
    'btn_clear_log': '清除日志',
    'btn_validate': '验证输入数据',
    'btn_run': '开始整合',
    'tip_run': (
        '启动所选的道路网络整合方法。处理开始前，'
        '系统将验证输入数据和输出参数。'),
    'btn_cancel': '取消处理',
    'tip_cancel': (
        '停止当前正在进行的整合任务。处理将在下一个安全检查点停止，'
        '且不会覆盖最终输出文件。'),
    'btn_close': '关闭',
}