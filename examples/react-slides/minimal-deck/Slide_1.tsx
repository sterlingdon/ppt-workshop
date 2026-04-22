import { getDeckStylePreset, styleVars } from '../../styles'

const lockedCopy = {
  eyebrow: '内容策略简报',
  title: '把高质量判断前移到生成之前',
  subtitle: '先锁定受众、论点和视觉方向，再进入 React slide authoring。',
}

export default function Slide_1() {
  const preset = getDeckStylePreset('bold-signal')

  return (
    <div
      data-ppt-slide="1"
      style={styleVars(preset)}
      className="relative h-[1080px] w-[1920px] overflow-hidden bg-[var(--ppt-bg)] text-[var(--ppt-text)]"
    >
      <div data-ppt-bg className="absolute inset-0 bg-[radial-gradient(circle_at_78%_24%,rgba(245,158,11,0.24),transparent_28%),linear-gradient(135deg,var(--ppt-bg),var(--ppt-surface))]" />
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
      <div data-ppt-bg className="absolute bottom-[112px] right-[128px] h-[360px] w-[520px] border border-[var(--ppt-border)] bg-[color-mix(in_srgb,var(--ppt-surface)_82%,transparent)] p-10">
        <div className="h-full w-full bg-[linear-gradient(90deg,var(--ppt-accent)_0_18px,transparent_18px),repeating-linear-gradient(180deg,var(--ppt-border)_0_2px,transparent_2px_54px)] opacity-80" />
      </div>
    </div>
  )
}
