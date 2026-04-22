import type { CSSProperties } from 'react'
import { getDeckStylePreset, styleVars } from '../../styles'

const lockedCopy = {
  title: '把设计建议落到变量覆盖',
  subtitle: 'preset 只提供结构脚手架；真实颜色、字体和视觉语气来自 design_dna.token_extensions。',
  rows: [
    ['ui-ux-pro-max', '给出暖纸色、深绿色、金色强调和克制线条'],
    ['design_dna.json', '把建议映射到 --ppt-bg、--ppt-primary、--ppt-accent 等变量'],
    ['React slide', '在 styleVars(preset) 之后覆盖变量，所有 className 继续使用 var(--ppt-*)'],
  ],
}

const designDnaTokenExtensions = {
  '--ppt-bg': '#F7F3EA',
  '--ppt-surface': '#FFFFFF',
  '--ppt-surface-strong': '#EDE6D8',
  '--ppt-primary': '#2D5A4A',
  '--ppt-secondary': '#6C7A62',
  '--ppt-accent': '#C99A2E',
  '--ppt-text': '#18211D',
  '--ppt-muted': '#5D665F',
  '--ppt-border': '#D8CCB8',
} as CSSProperties

export default function Slide_3() {
  const preset = getDeckStylePreset('editorial-ink')
  const themeVars = {
    ...styleVars(preset),
    ...designDnaTokenExtensions,
  } as CSSProperties

  return (
    <div
      data-ppt-slide="3"
      style={themeVars}
      className="relative h-[1080px] w-[1920px] overflow-hidden bg-[var(--ppt-bg)] px-[128px] py-[92px] text-[var(--ppt-text)]"
    >
      <div data-ppt-bg className="absolute inset-0 bg-[linear-gradient(90deg,color-mix(in_srgb,var(--ppt-primary)_7%,transparent)_1px,transparent_1px),linear-gradient(180deg,color-mix(in_srgb,var(--ppt-primary)_6%,transparent)_1px,transparent_1px)] bg-[length:80px_80px]" />
      <div className="relative">
        <div data-ppt-bg className="mb-10 h-3 w-48 bg-[var(--ppt-accent)]" />
        <h2 data-ppt-text className="max-w-[1260px] text-[78px] font-black leading-[1.06] text-[var(--ppt-primary)]">
          {lockedCopy.title}
        </h2>
        <p data-ppt-text className="mt-8 max-w-[1140px] text-[34px] leading-[1.34] text-[var(--ppt-muted)]">
          {lockedCopy.subtitle}
        </p>
      </div>
      <div data-ppt-group="list" className="relative mt-20 grid gap-6">
        {lockedCopy.rows.map(([label, body], index) => (
          <article data-ppt-item key={label} className="relative min-h-[150px] p-2">
            <div data-ppt-item-bg className="absolute inset-0 border border-[var(--ppt-border)] bg-[var(--ppt-surface)]" />
            <div className="relative flex items-start gap-8 px-10 py-8">
              <span data-ppt-bullet className="mt-1 h-9 w-9 shrink-0 bg-[var(--ppt-accent)]" />
              <div>
                <h3 data-ppt-text className="text-[34px] font-black text-[var(--ppt-primary)]">
                  {index + 1}. {label}
                </h3>
                <p data-ppt-text className="mt-3 text-[29px] leading-[1.3] text-[var(--ppt-muted)]">
                  {body}
                </p>
              </div>
            </div>
          </article>
        ))}
      </div>
    </div>
  )
}
