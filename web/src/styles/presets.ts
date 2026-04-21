import type { CSSProperties } from 'react'

export type DeckStyleId = 'aurora-borealis' | 'bold-signal' | 'editorial-ink'

export type DeckStylePreset = {
  id: DeckStyleId
  label: string
  summary: string
  tokens: {
    bg: string
    surface: string
    surfaceStrong: string
    primary: string
    secondary: string
    accent: string
    text: string
    muted: string
    border: string
    fontDisplay: string
    fontBody: string
  }
  layoutRules: string[]
  componentRecipes: string[]
  slidePatterns: Array<{
    id: string
    useFor: string
    layout: string
    requiredMarkers: string[]
  }>
  avoid: string[]
}

export const deckStylePresets: Record<DeckStyleId, DeckStylePreset> = {
  'aurora-borealis': {
    id: 'aurora-borealis',
    label: 'Aurora Borealis',
    summary: 'Dark technical deck with cyan-purple light, glass panels, and high-contrast metrics.',
    tokens: {
      bg: '#080A14',
      surface: 'rgba(255,255,255,0.06)',
      surfaceStrong: 'rgba(18,24,43,0.88)',
      primary: '#8B5CF6',
      secondary: '#22D3EE',
      accent: '#F472B6',
      text: '#F8FAFC',
      muted: '#A1A1AA',
      border: 'rgba(255,255,255,0.14)',
      fontDisplay: 'Inter, ui-sans-serif, system-ui, sans-serif',
      fontBody: 'Inter, ui-sans-serif, system-ui, sans-serif',
    },
    layoutRules: [
      'Use one dominant focal object per slide, surrounded by two or three secondary panels.',
      'Keep dark negative space visible; avoid filling every grid cell.',
      'Use large numeric callouts and thin supporting labels.',
    ],
    componentRecipes: [
      'Glass metric card: bg-white/5 backdrop-blur-2xl border-white/10 shadow-[0_0_80px_-24px_var(--ppt-primary)].',
      'Technical diagram: rounded nodes on a subtle grid with cyan connector lines.',
      'Title slide: centered glass panel with gradient heading and two blurred background glows.',
    ],
    slidePatterns: [
      {
        id: 'aurora-title-glass',
        useFor: 'Opening slide, chapter opener, high-energy summary.',
        layout: 'Full dark canvas, two blurred glows, centered glass container, one gradient headline, one short subtitle.',
        requiredMarkers: ['root:data-ppt-slide', 'glass-panel:data-ppt-bg', 'headline:data-ppt-text', 'subtitle:data-ppt-text'],
      },
      {
        id: 'aurora-metric-bento',
        useFor: 'KPI summary, market data, performance comparison.',
        layout: 'Three-column bento grid with one wide metric card, one tall chart card, and two compact evidence cards.',
        requiredMarkers: ['root:data-ppt-slide', 'each-card:data-ppt-bg', 'all-copy:data-ppt-text'],
      },
      {
        id: 'aurora-system-map',
        useFor: 'Architecture, workflow, cause-effect graph.',
        layout: 'Subtle grid background, 4-7 rounded nodes, cyan connectors, short labels only.',
        requiredMarkers: ['root:data-ppt-slide', 'diagram-shell:data-ppt-bg', 'title:data-ppt-text'],
      },
    ],
    avoid: [
      'Flat white cards on dark background.',
      'More than three saturated colors in one slide.',
      'Long paragraphs inside glass cards.',
    ],
  },
  'bold-signal': {
    id: 'bold-signal',
    label: 'Bold Signal',
    summary: 'Business/startup deck with sharp contrast, orange signal accents, and dense but readable panels.',
    tokens: {
      bg: '#111111',
      surface: '#1D1D1D',
      surfaceStrong: '#262626',
      primary: '#F97316',
      secondary: '#FBBF24',
      accent: '#FFFFFF',
      text: '#FAFAFA',
      muted: '#A3A3A3',
      border: '#404040',
      fontDisplay: 'Inter, ui-sans-serif, system-ui, sans-serif',
      fontBody: 'Inter, ui-sans-serif, system-ui, sans-serif',
    },
    layoutRules: [
      'Use strong left alignment and compact information density.',
      'Prefer hard edges, accent bars, and large section numbers.',
      'Make comparison slides feel like decision documents, not marketing pages.',
    ],
    componentRecipes: [
      'Signal card: dark solid panel, 4px orange left border, compact title, short evidence line.',
      'Executive summary: orange rail on the left with three numbered claims.',
      'Market matrix: black background, neutral grid, orange highlights only for selected cells.',
    ],
    slidePatterns: [
      {
        id: 'signal-exec-brief',
        useFor: 'Executive summary and recommendation pages.',
        layout: 'Left orange rail, large direct heading, three numbered claims in dense dark panels.',
        requiredMarkers: ['root:data-ppt-slide', 'claim-panels:data-ppt-bg', 'all-copy:data-ppt-text'],
      },
      {
        id: 'signal-decision-matrix',
        useFor: 'Option comparison, prioritization, tradeoff analysis.',
        layout: 'Compact table-like grid, neutral cells, orange highlight for selected recommendation.',
        requiredMarkers: ['root:data-ppt-slide', 'matrix:data-ppt-bg', 'headers:data-ppt-text', 'cell-labels:data-ppt-text'],
      },
      {
        id: 'signal-market-snapshot',
        useFor: 'Business metrics, market sizing, investor-style updates.',
        layout: 'Top title band, four compact metric tiles, bottom evidence strip.',
        requiredMarkers: ['root:data-ppt-slide', 'metric-tiles:data-ppt-bg', 'metrics:data-ppt-text'],
      },
    ],
    avoid: [
      'Soft glassmorphism.',
      'Decorative blobs.',
      'Pastel gradients.',
    ],
  },
  'editorial-ink': {
    id: 'editorial-ink',
    label: 'Editorial Ink',
    summary: 'Light editorial deck with print-like hierarchy, restrained color, and strong typographic rhythm.',
    tokens: {
      bg: '#F8F5F0',
      surface: '#FFFFFF',
      surfaceStrong: '#F1ECE4',
      primary: '#B91C1C',
      secondary: '#1F2937',
      accent: '#D97706',
      text: '#1C1917',
      muted: '#57534E',
      border: '#D6D3D1',
      fontDisplay: 'Georgia, ui-serif, serif',
      fontBody: 'Inter, ui-sans-serif, system-ui, sans-serif',
    },
    layoutRules: [
      'Use generous margins, strong headings, and smaller body text.',
      'Prefer columns, pull quotes, captions, and rule lines.',
      'Keep decorative elements flat and print-inspired.',
    ],
    componentRecipes: [
      'Editorial quote: red vertical rule, serif quote text, small sans-serif attribution.',
      'Fact list: two-column text blocks with thin dividing lines.',
      'Title slide: oversized serif title, small subtitle, one restrained accent line.',
    ],
    slidePatterns: [
      {
        id: 'ink-feature-story',
        useFor: 'Narrative section, report lead, context-setting slide.',
        layout: 'Large serif headline, narrow dek paragraph, one thin red rule, optional captioned image area.',
        requiredMarkers: ['root:data-ppt-slide', 'headline:data-ppt-text', 'dek:data-ppt-text'],
      },
      {
        id: 'ink-pull-quote',
        useFor: 'Important quote, expert opinion, editorial emphasis.',
        layout: 'Left red rule, oversized serif quote, small attribution, wide whitespace.',
        requiredMarkers: ['root:data-ppt-slide', 'quote-rule:data-ppt-bg', 'quote:data-ppt-text', 'attribution:data-ppt-text'],
      },
      {
        id: 'ink-two-column-brief',
        useFor: 'Fact list, lesson summary, balanced argument.',
        layout: 'Two text columns, thin dividers, small labels, restrained accent numbers.',
        requiredMarkers: ['root:data-ppt-slide', 'divider-lines:data-ppt-bg', 'all-copy:data-ppt-text'],
      },
    ],
    avoid: [
      'Neon colors.',
      'Heavy shadows.',
      'Glass or blurred panels.',
    ],
  },
}

export function getDeckStylePreset(id: DeckStyleId = 'aurora-borealis'): DeckStylePreset {
  return deckStylePresets[id]
}

export function styleVars(preset: DeckStylePreset): CSSProperties {
  return {
    '--ppt-bg': preset.tokens.bg,
    '--ppt-surface': preset.tokens.surface,
    '--ppt-surface-strong': preset.tokens.surfaceStrong,
    '--ppt-primary': preset.tokens.primary,
    '--ppt-secondary': preset.tokens.secondary,
    '--ppt-accent': preset.tokens.accent,
    '--ppt-text': preset.tokens.text,
    '--ppt-muted': preset.tokens.muted,
    '--ppt-border': preset.tokens.border,
    '--ppt-font-display': preset.tokens.fontDisplay,
    '--ppt-font-body': preset.tokens.fontBody,
  } as CSSProperties
}
