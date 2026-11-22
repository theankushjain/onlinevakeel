import React from "react";

/*
 * Flat vector portrait of an Indian advocate: black coat, white neck bands,
 * thin glasses, brass scales pin. Pure SVG, no images to load.
 * variant="full" = shoulders-up portrait, variant="bust" = tight face crop for small avatars.
 */
const COAT = "#13232F";
const COAT_LAPEL = "#1D3342";
const SKIN = "#C48B62";
const SKIN_SHADE = "#A9714B";
const HAIR = "#231F20";
const BRASS = "#B07D1F";

export default function AdvocateAvatar({
  variant = "full",
  className,
}: {
  variant?: "full" | "bust";
  className?: string;
}) {
  const viewBox = variant === "bust" ? "100 84 120 150" : "0 60 320 320";

  return (
    <svg
      className={className}
      viewBox={viewBox}
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      focusable="false"
    >
      {/* Coat / shoulders */}
      <path d="M30 380 C30 300 66 262 120 250 L200 250 C254 262 290 300 290 380 Z" fill={COAT} />
      {/* Lapels */}
      <path d="M120 250 L150 340 L128 380 L84 380 C84 320 98 276 120 250 Z" fill={COAT_LAPEL} />
      <path d="M200 250 L170 340 L192 380 L236 380 C236 320 222 276 200 250 Z" fill={COAT_LAPEL} />

      {/* Neck */}
      <path d="M143 214 H177 V252 C177 262 168 270 160 270 C152 270 143 262 143 252 Z" fill={SKIN_SHADE} />

      {/* Shirt V and collar */}
      <path d="M128 252 L160 312 L192 252 L176 246 L160 262 L144 246 Z" fill="#FFFFFF" />

      {/* Neck bands: the two white strips of an advocate's attire */}
      <rect x="149" y="268" width="10" height="46" rx="1.5" fill="#FFFFFF" stroke="#CBD3DC" strokeWidth="1" />
      <rect x="161" y="268" width="10" height="46" rx="1.5" fill="#FFFFFF" stroke="#CBD3DC" strokeWidth="1" />

      {/* Brass scales pin */}
      <circle cx="222" cy="304" r="9" fill={BRASS} />
      <path d="M222 297 V311 M215 301 H229 M215 301 L213 306 H217 Z M229 301 L227 306 H231 Z" stroke={COAT} strokeWidth="1.3" fill="none" strokeLinecap="round" strokeLinejoin="round" />

      {/* Ears */}
      <circle cx="112" cy="174" r="9" fill={SKIN} />
      <circle cx="208" cy="174" r="9" fill={SKIN} />
      {/* Head */}
      <ellipse cx="160" cy="170" rx="48" ry="57" fill={SKIN} />
      {/* Hair */}
      <path d="M111 164 C104 108 138 94 160 94 C184 94 216 108 209 164 C202 140 186 128 160 128 C134 128 118 140 111 164 Z" fill={HAIR} />

      {/* Brows */}
      <path d="M133 157 Q143 150 154 156" stroke={HAIR} strokeWidth="3.2" strokeLinecap="round" fill="none" />
      <path d="M166 156 Q177 150 187 157" stroke={HAIR} strokeWidth="3.2" strokeLinecap="round" fill="none" />
      {/* Eyes */}
      <circle cx="144" cy="171" r="3.6" fill={HAIR} />
      <circle cx="176" cy="171" r="3.6" fill={HAIR} />
      {/* Glasses */}
      <rect x="128" y="160" width="32" height="24" rx="10" fill="none" stroke="#2B3A47" strokeWidth="2.6" />
      <rect x="160" y="160" width="32" height="24" rx="10" fill="none" stroke="#2B3A47" strokeWidth="2.6" />
      <path d="M158 168 H162" stroke="#2B3A47" strokeWidth="2.6" strokeLinecap="round" />
      {/* Nose */}
      <path d="M160 174 Q155 190 162 192" stroke={SKIN_SHADE} strokeWidth="2.4" strokeLinecap="round" fill="none" />
      {/* Warm smile */}
      <path d="M145 203 Q160 217 175 203" stroke="#6E3B2A" strokeWidth="3.2" strokeLinecap="round" fill="none" />
    </svg>
  );
}
