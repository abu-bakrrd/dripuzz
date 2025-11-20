import { useEffect } from "react";
import { useConfig } from "@/hooks/useConfig";

export default function FontLoader() {
  const { config } = useConfig();

  useEffect(() => {
    if (!config?.fonts) return;

    const root = document.documentElement;
    const fonts = config.fonts;

    if (fonts.fontFile) {
      const fontFaceStyle = document.getElementById('custom-font-face');
      if (fontFaceStyle) {
        fontFaceStyle.remove();
      }

      const style = document.createElement('style');
      style.id = 'custom-font-face';
      style.textContent = `
        @font-face {
          font-family: '${fonts.fontFamily}';
          src: url('${fonts.fontFile}') format('truetype');
          font-weight: 100 900;
          font-display: swap;
        }
      `;
      document.head.appendChild(style);
    }

    root.style.setProperty('--font-family-custom', fonts.fontFamily);
    root.style.setProperty('--font-weight-product-name', String(fonts.productName.weight));
    root.style.setProperty('--font-weight-price', String(fonts.price.weight));
    root.style.setProperty('--font-weight-description', String(fonts.description.weight));
  }, [config]);

  return null;
}
