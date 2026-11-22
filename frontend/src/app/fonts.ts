import { Source_Serif_4, Mukta, Noto_Serif_Devanagari } from "next/font/google";

/* Headlines: a sturdy, book-like serif with real legal gravitas. */
export const serif = Source_Serif_4({
  subsets: ["latin"],
  variable: "--font-serif",
  display: "swap",
});

/* Body and UI: friendly humanist sans that has Latin AND Devanagari in one family,
   so English and Hindi text look consistent. */
export const body = Mukta({
  subsets: ["latin", "devanagari"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-body",
  display: "swap",
});

/* Hindi headlines: serif Devanagari to pair with Source Serif 4. */
export const serifHi = Noto_Serif_Devanagari({
  subsets: ["devanagari"],
  weight: ["600", "700"],
  variable: "--font-serif-hi",
  display: "swap",
});
