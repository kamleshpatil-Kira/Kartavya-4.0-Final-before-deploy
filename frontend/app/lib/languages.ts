export const COURSE_LANGUAGES = [
  "English",
  "Hindi",
  "Spanish",
  "French",
  "German",
  "Portuguese",
  "Italian",
  "Dutch",
  "Russian",
  "Chinese (Simplified)",
  "Chinese (Traditional)",
  "Japanese",
  "Korean",
  "Arabic",
  "Turkish",
  "Vietnamese",
  "Thai",
  "Indonesian",
] as const;

const LANGUAGE_TO_TTS_ACCENT: Record<string, string> = {
  english: "english",
  hindi: "hindi",
  spanish: "spanish",
  french: "french",
  german: "german",
  portuguese: "portuguese",
  italian: "italian",
  dutch: "dutch",
  russian: "russian",
  "chinese (simplified)": "chinese",
  "chinese (traditional)": "chinese",
  japanese: "japanese",
  korean: "korean",
  arabic: "arabic",
  turkish: "turkish",
  vietnamese: "vietnamese",
  thai: "thai",
  indonesian: "indonesian",
};

const LANGUAGE_TO_PREVIEW_TEXT: Record<string, string> = {
  english: "Hello, this is a preview of the selected voice settings for your course.",
  hindi: "नमस्ते, यह आपके कोर्स के लिए चयनित वॉइस सेटिंग्स का पूर्वावलोकन है।",
  spanish: "Hola, esta es una vista previa de la configuracion de voz seleccionada para tu curso.",
  french: "Bonjour, ceci est un apercu des parametres vocaux selectionnes pour votre cours.",
  german: "Hallo, dies ist eine Vorschau der ausgewahlten Spracheinstellungen fur Ihren Kurs.",
  portuguese: "Ola, esta e uma previa das configuracoes de voz selecionadas para o seu curso.",
  italian: "Ciao, questa e un'anteprima delle impostazioni vocali selezionate per il tuo corso.",
  dutch: "Hallo, dit is een voorbeeld van de geselecteerde steminstellingen voor uw cursus.",
  russian: "Здравствуйте, это предварительный просмотр выбранных голосовых настроек для вашего курса.",
  "chinese (simplified)": "你好，这是您课程所选语音设置的预览。",
  "chinese (traditional)": "你好，這是您課程所選語音設定的預覽。",
  japanese: "こんにちは、これはコースの選択した音声設定のプレビューです。",
  korean: "안녕하세요, 이것은 코스의 선택된 음성 설정의 미리보기입니다.",
  arabic: "مرحبًا، هذه معاينة لإعدادات الصوت المحددة لدورتك.",
  turkish: "Merhaba, bu kursunuz icin secilen ses ayarlarinin bir onizlemesidir.",
  vietnamese: "Xin chao, day la ban xem truoc cai dat giong noi da chon cho khoa hoc cua ban.",
  thai: "สวัสดี นี่คือตัวอย่างการตั้งค่าเสียงที่เลือกสำหรับหลักสูตรของคุณ",
  indonesian: "Halo, ini adalah pratinjau pengaturan suara yang dipilih untuk kursus Anda.",
};

export function toTtsAccent(language: string): string {
  const key = (language || "").trim().toLowerCase();
  return LANGUAGE_TO_TTS_ACCENT[key] || "english";
}

export function getVoicePreviewText(language: string): string {
  const key = (language || "").trim().toLowerCase();
  return LANGUAGE_TO_PREVIEW_TEXT[key] || LANGUAGE_TO_PREVIEW_TEXT.english;
}
