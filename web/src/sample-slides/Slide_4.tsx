import { getDeckStylePreset, styleVars } from '../styles'

const steps = [
  { id: 'one', title: 'Mark', body: 'Use group and item markers.' },
  { id: 'two', title: 'Slice', body: 'Capture each item independently.' },
  { id: 'three', title: 'Export', body: 'Place item rasters and native text.' },
]

export default function Slide_4() {
  const preset = getDeckStylePreset('aurora-borealis')

  return (
    <div
      className="w-[1920px] h-[1080px] bg-[var(--ppt-bg)] p-24"
      style={styleVars(preset)}
      data-ppt-slide="4"
    >
      <h2 data-ppt-text className="mb-24 text-6xl font-black text-[var(--ppt-text)]">
        Item-aware timeline
      </h2>
      <div data-ppt-group="timeline" className="relative grid grid-cols-3 gap-16">
        <div data-ppt-track className="absolute left-24 right-24 top-8 h-1 rounded-full bg-[var(--ppt-border)]" />
        {steps.map((step, index) => (
          <div data-ppt-item key={step.id} className="relative rounded-3xl p-8">
            {index > 0 && (
              <div data-ppt-segment className="absolute -left-16 top-8 h-1 w-16 bg-[var(--ppt-secondary)]" />
            )}
            <div data-ppt-bullet data-ppt-node className="relative z-10 mb-8 h-16 w-16 rounded-full bg-[var(--ppt-secondary)] shadow-2xl" />
            <div data-ppt-item-bg className="absolute inset-0 rounded-3xl bg-[var(--ppt-surface)] shadow-2xl" />
            <h3 data-ppt-text className="relative z-10 text-3xl font-bold text-[var(--ppt-text)]">
              {step.title}
            </h3>
            <p data-ppt-text className="relative z-10 text-xl text-[var(--ppt-muted)]">
              {step.body}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
