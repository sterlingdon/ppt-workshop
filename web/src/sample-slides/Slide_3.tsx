import type { CSSProperties } from 'react'

const items = [
  { id: 'a', title: 'Item-level capture', body: 'Each row can be copied or removed.' },
  { id: 'b', title: 'Native text overlay', body: 'Text remains editable when safe.' },
  { id: 'c', title: 'Visual fallback', body: 'Complex visuals remain rasterized.' },
]

const designDnaTheme = {
  '--ppt-bg': '#080A14',
  '--ppt-surface': 'rgba(255,255,255,0.06)',
  '--ppt-secondary': '#22D3EE',
  '--ppt-text': '#F8FAFC',
  '--ppt-muted': '#A1A1AA',
  '--ppt-border': 'rgba(255,255,255,0.14)',
} as CSSProperties

export default function Slide_3() {
  return (
    <div
      className="w-[1920px] h-[1080px] bg-[var(--ppt-bg)] p-24"
      style={designDnaTheme}
      data-ppt-slide="3"
    >
      <h2 data-ppt-text className="mb-12 text-6xl font-black text-[var(--ppt-text)]">
        Item-aware list
      </h2>
      <div data-ppt-group="list" className="space-y-5">
        {items.map((item) => (
          <div data-ppt-item key={item.id} className="relative rounded-3xl p-8">
            <div data-ppt-item-bg className="absolute inset-0 rounded-3xl bg-[var(--ppt-surface)] shadow-2xl" />
            <span data-ppt-bullet className="relative z-10 mr-5 inline-block h-4 w-4 rounded-full bg-[var(--ppt-secondary)]" />
            <h3 data-ppt-text className="relative z-10 text-3xl font-bold text-[var(--ppt-text)]">
              {item.title}
            </h3>
            <p data-ppt-text className="relative z-10 text-xl text-[var(--ppt-muted)]">
              {item.body}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
