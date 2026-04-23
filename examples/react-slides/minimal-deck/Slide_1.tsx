import type { CSSProperties } from 'react'

const lockedCopy = {
  eyebrow: '内容策略简报',
  title: '把高质量判断前移到生成之前',
  subtitle: '先锁定受众、论点和视觉方向，再进入 React slide authoring。',
}

const designDnaTheme = {
  '--ppt-bg': '#F7F3EA',
  '--ppt-surface': '#FFFFFF',
  '--ppt-surface-strong': '#EDE6D8',
  '--ppt-primary': '#2D5A4A',
  '--ppt-secondary': '#6C7A62',
  '--ppt-accent': '#C99A2E',
  '--ppt-text': '#18211D',
  '--ppt-muted': '#5D665F',
  '--ppt-border': '#D8CCB8',
  '--ppt-font-display': 'Inter, ui-sans-serif, system-ui, sans-serif',
  '--ppt-font-body': 'Inter, ui-sans-serif, system-ui, sans-serif',
} as CSSProperties

export default function Slide_1() {
  return (
    <div
      data-ppt-slide="1"
      style={designDnaTheme}
      className="relative h-[1080px] w-[1920px] overflow-hidden bg-[var(--ppt-bg)] text-[var(--ppt-text)]"
    >
      <div data-ppt-bg className="absolute inset-0 bg-[linear-gradient(90deg,color-mix(in_srgb,var(--ppt-primary)_7%,transparent)_1px,transparent_1px),linear-gradient(180deg,color-mix(in_srgb,var(--ppt-primary)_6%,transparent)_1px,transparent_1px)] bg-[length:88px_88px]" />
      <div data-ppt-bg className="absolute right-[122px] top-[110px] h-[760px] w-[520px] border-l border-[var(--ppt-border)] bg-[linear-gradient(180deg,color-mix(in_srgb,var(--ppt-primary)_12%,transparent),transparent)]" />
      <div className="absolute left-[140px] top-[142px] w-[1060px]">
        <p data-ppt-text className="mb-10 text-[34px] font-semibold uppercase tracking-[0.14em] text-[var(--ppt-accent)]">
          {lockedCopy.eyebrow}
        </p>
        <h1 data-ppt-text className="text-[104px] font-black leading-[1.03] text-[var(--ppt-text)]">
          {lockedCopy.title}
        </h1>
        <p data-ppt-text className="mt-12 max-w-[940px] text-[40px] leading-[1.28] text-[var(--ppt-muted)]">
          {lockedCopy.subtitle}
        </p>
      </div>
      <div data-ppt-bg className="absolute bottom-[112px] right-[128px] h-[360px] w-[520px] border border-[var(--ppt-border)] bg-[color-mix(in_srgb,var(--ppt-surface)_88%,transparent)] p-10">
        <div className="h-full w-full bg-[linear-gradient(90deg,var(--ppt-accent)_0_18px,transparent_18px),repeating-linear-gradient(180deg,var(--ppt-border)_0_2px,transparent_2px_54px),linear-gradient(90deg,transparent_0_70%,color-mix(in_srgb,var(--ppt-primary)_16%,transparent)_70%_100%)] opacity-90" />
      </div>
    </div>
  )
}
