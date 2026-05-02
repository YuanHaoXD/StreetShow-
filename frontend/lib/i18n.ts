export type Lang = "zh" | "en";

export const translations = {
  zh: {
    // header
    tagline: "上传人物图与衣物图，生成时尚建议与试衣效果图。",
    langToggle: "EN",
    // sidebar modes
    modesTitle: "Modes",
    modeBasicLabel: "标准试衣",
    modeBasicDesc: "单张稳定换衣",
    modeLookbookLabel: "Lookbook",
    modeLookbookDesc: "多场景风格展示",
    modePoseLabel: "Pose Lab",
    modePoseDesc: "根据服装推荐动作",
    modeMultiLabel: "Multi-Fit",
    modeMultiDesc: "多物件同时上身",
    // sidebar controls
    styleHintTitle: "用户偏好",
    styleHintPlaceholder: "更街头 / 更高级 / 夜景霓虹...",
    showPlanJson: "显示计划 JSON",
    historyBtn: "历史记录",
    // upload
    subjectLabel: "Subject（你）",
    subjectHint: "上传人物图",
    garmentLabel: "Garment（衣物）",
    garmentHint: "上传衣物图",
    // action
    igniting: "IGNITING...",
    igniteStyle: "IGNITE STYLE",
    dismiss: "取消",
    // results
    generating: "生成中...",
    viewDetails: "点击查看详情",
    tryonGenerating: "试衣图生成中...",
    lookbookResults: "Lookbook Results",
    tryonResult: "Try-on Result",
    // advice labels
    advicePerson: "👤 人物特征",
    adviceGarment: "👕 衣物分析",
    adviceStyling: "✨ 搭配建议",
    adviceQuality: "📸 品质约束",
    styleDnaTitle: "🧬 风格 DNA",
    fitsLabel: "适合：",
    // modal
    close: "关闭",
    // history panel
    historyTitle: "生成记录",
    historyClearAll: "清空",
    historyClose: "关闭",
    historyEmpty: "暂无历史记录",
    historyTapView: "点击查看",
    modeBasicShort: "标准试衣",
  },
  en: {
    // header
    tagline: "Upload a model photo and garment image to get styling advice and try-on results.",
    langToggle: "中文",
    // sidebar modes
    modesTitle: "Modes",
    modeBasicLabel: "Basic Try-On",
    modeBasicDesc: "Single stable swap",
    modeLookbookLabel: "Lookbook",
    modeLookbookDesc: "Multi-scene editorial",
    modePoseLabel: "Pose Lab",
    modePoseDesc: "Poses matched to garment",
    modeMultiLabel: "Multi-Fit",
    modeMultiDesc: "Multiple items at once",
    // sidebar controls
    styleHintTitle: "Style Hint",
    styleHintPlaceholder: "More street / More formal / Neon night...",
    showPlanJson: "Show Plan JSON",
    historyBtn: "History",
    // upload
    subjectLabel: "Subject (You)",
    subjectHint: "Upload model photo",
    garmentLabel: "Garment",
    garmentHint: "Upload garment photo",
    // action
    igniting: "IGNITING...",
    igniteStyle: "IGNITE STYLE",
    dismiss: "Dismiss",
    // results
    generating: "Generating...",
    viewDetails: "View details",
    tryonGenerating: "Generating try-on...",
    lookbookResults: "Lookbook Results",
    tryonResult: "Try-on Result",
    // advice labels
    advicePerson: "👤 Model Profile",
    adviceGarment: "👕 Garment Analysis",
    adviceStyling: "✨ Styling Advice",
    adviceQuality: "📸 Quality Guide",
    styleDnaTitle: "🧬 Style DNA",
    fitsLabel: "Fits: ",
    // modal
    close: "Close",
    // history panel
    historyTitle: "History",
    historyClearAll: "Clear All",
    historyClose: "Close",
    historyEmpty: "No history yet",
    historyTapView: "Tap to view",
    modeBasicShort: "Basic",
  },
} as const;

export type TranslationKey = keyof typeof translations.zh;
