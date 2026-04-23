import type { CSSProperties } from 'react'

const lockedCopy = {
  title: '三道前置质量门',
  cards: [
    {
      label: '内容审核',
      body: '先确认受众、目标、核心论点和必须删掉的噪音。',
    },
    {
      label: '设计 DNA',
      body: '用设计建议直接定义完整视觉系统，再落实为画面变量和构图动作。',
    },
    {
      label: '锁定文案',
      body: 'React 阶段只表达 blueprint 里的文字，不重新写作。',
    },
  ],
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

export default function Slide_2() {
  return (
    <div
      data-ppt-slide="2"
      style={designDnaTheme}
      className="relative h-[1080px] w-[1920px] overflow-hidden bg-[var(--ppt-bg)] px-[120px] py-[96px] text-[var(--ppt-text)]"
    >
      <div data-ppt-bg className="absolute left-[120px] right-[120px] top-[82px] h-3 bg-[var(--ppt-accent)]" />
      <h2 data-ppt-text className="mt-12 max-w-[1180px] text-[82px] font-black leading-[1.05] text-[var(--ppt-primary)]">
        {lockedCopy.title}
      </h2>
      <div data-ppt-group="card-grid" className="mt-20 grid grid-cols-3 gap-8">
        {lockedCopy.cards.map((card, index) => (
          <article data-ppt-item key={card.label} className="relative min-h-[430px] p-3">
            <div data-ppt-item-bg className="absolute inset-0 border border-[var(--ppt-border)] bg-[var(--ppt-surface)] shadow-[18px_18px_0_color-mix(in_srgb,var(--ppt-primary)_8%,transparent)]" />
            <div className="relative p-10">
              <span data-ppt-bullet className="mb-12 flex h-20 w-20 items-center justify-center bg-[var(--ppt-primary)] text-[34px] font-black text-[var(--ppt-bg)]">
                {index + 1}
              </span>
              <h3 data-ppt-text className="text-[42px] font-extrabold leading-tight text-[var(--ppt-primary)]">
                {card.label}
              </h3>
              <p data-ppt-text className="mt-8 text-[31px] leading-[1.32] text-[var(--ppt-muted)]">
                {card.body}
              </p>
            </div>
          </article>
        ))}
      </div>
    </div>
  )
}
