import { getDeckStylePreset, styleVars } from '../../styles'

const lockedCopy = {
  title: '三道前置质量门',
  cards: [
    {
      label: '内容审核',
      body: '先确认受众、目标、核心论点和必须删掉的噪音。',
    },
    {
      label: '设计 DNA',
      body: '用设计建议定义视觉语言，再映射到本地 preset。',
    },
    {
      label: '锁定文案',
      body: 'React 阶段只表达 blueprint 里的文字，不重新写作。',
    },
  ],
}

export default function Slide_2() {
  const preset = getDeckStylePreset('bold-signal')

  return (
    <div
      data-ppt-slide="2"
      style={styleVars(preset)}
      className="relative h-[1080px] w-[1920px] overflow-hidden bg-[var(--ppt-bg)] px-[120px] py-[96px] text-[var(--ppt-text)]"
    >
      <div data-ppt-bg className="absolute inset-x-0 top-0 h-4 bg-[var(--ppt-accent)]" />
      <h2 data-ppt-text className="max-w-[1180px] text-[82px] font-black leading-[1.05]">
        {lockedCopy.title}
      </h2>
      <div data-ppt-group="card-grid" className="mt-20 grid grid-cols-3 gap-8">
        {lockedCopy.cards.map((card, index) => (
          <article data-ppt-item key={card.label} className="relative min-h-[430px] p-2">
            <div data-ppt-item-bg className="absolute inset-0 border border-[var(--ppt-border)] bg-[var(--ppt-surface)]" />
            <div className="relative p-10">
              <span data-ppt-bullet className="mb-12 flex h-20 w-20 items-center justify-center bg-[var(--ppt-accent)] text-[34px] font-black text-[var(--ppt-bg)]">
                {index + 1}
              </span>
              <h3 data-ppt-text className="text-[42px] font-extrabold leading-tight">
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
