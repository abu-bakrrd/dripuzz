import { useEffect } from "react";
import { useConfig } from "@/hooks/useConfig";

function hexToHSL(hex: string): string {
  hex = hex.replace(/^#/, '');
  
  const r = parseInt(hex.substring(0, 2), 16) / 255;
  const g = parseInt(hex.substring(2, 4), 16) / 255;
  const b = parseInt(hex.substring(4, 6), 16) / 255;
  
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h = 0, s = 0, l = (max + min) / 2;
  
  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    
    switch (max) {
      case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
      case g: h = ((b - r) / d + 2) / 6; break;
      case b: h = ((r - g) / d + 4) / 6; break;
    }
  }
  
  h = Math.round(h * 360);
  s = Math.round(s * 100);
  l = Math.round(l * 100);
  
  return `${h} ${s}% ${l}%`;
}

export default function ThemeApplier() {
  const { config } = useConfig();

  useEffect(() => {
    if (!config?.colorScheme) return;

    const root = document.documentElement;
    const scheme = config.colorScheme;

    root.style.setProperty('--background', hexToHSL(scheme.background));
    root.style.setProperty('--foreground', hexToHSL(scheme.foreground));
    root.style.setProperty('--card', hexToHSL(scheme.card));
    root.style.setProperty('--card-foreground', hexToHSL(scheme.cardForeground));
    root.style.setProperty('--primary', hexToHSL(scheme.primary));
    root.style.setProperty('--primary-foreground', hexToHSL(scheme.primaryForeground));
    root.style.setProperty('--secondary', hexToHSL(scheme.secondary));
    root.style.setProperty('--secondary-foreground', hexToHSL(scheme.secondaryForeground));
    root.style.setProperty('--muted', hexToHSL(scheme.muted));
    root.style.setProperty('--muted-foreground', hexToHSL(scheme.mutedForeground));
    root.style.setProperty('--accent', hexToHSL(scheme.accent));
    root.style.setProperty('--accent-foreground', hexToHSL(scheme.accentForeground));
    root.style.setProperty('--border', hexToHSL(scheme.border));
    root.style.setProperty('--input', hexToHSL(scheme.input));
    root.style.setProperty('--ring', hexToHSL(scheme.ring));

    root.style.setProperty('--card-border', hexToHSL(scheme.border));
    root.style.setProperty('--sidebar', hexToHSL(scheme.card));
    root.style.setProperty('--sidebar-foreground', hexToHSL(scheme.cardForeground));
    root.style.setProperty('--sidebar-border', hexToHSL(scheme.border));
    root.style.setProperty('--sidebar-primary', hexToHSL(scheme.primary));
    root.style.setProperty('--sidebar-primary-foreground', hexToHSL(scheme.primaryForeground));
    root.style.setProperty('--sidebar-accent', hexToHSL(scheme.accent));
    root.style.setProperty('--sidebar-accent-foreground', hexToHSL(scheme.accentForeground));
    root.style.setProperty('--sidebar-ring', hexToHSL(scheme.ring));
  }, [config]);

  return null;
}
