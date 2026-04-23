import type { CSSProperties } from 'react'

const designDnaTheme = {
  '--ppt-bg': '#080A14',
  '--ppt-surface': 'rgba(255,255,255,0.06)',
  '--ppt-surface-strong': 'rgba(18,24,43,0.88)',
  '--ppt-primary': '#8B5CF6',
  '--ppt-secondary': '#22D3EE',
  '--ppt-accent': '#F472B6',
  '--ppt-text': '#F8FAFC',
  '--ppt-muted': '#A1A1AA',
  '--ppt-border': 'rgba(255,255,255,0.14)',
  '--ppt-font-display': 'Inter, ui-sans-serif, system-ui, sans-serif',
  '--ppt-font-body': 'Inter, ui-sans-serif, system-ui, sans-serif',
} as CSSProperties

export default function Slide_2() {
  return (
    <div
      className="w-[1920px] h-[1080px] bg-[var(--ppt-bg)] flex flex-col p-20"
      style={designDnaTheme}
      data-ppt-slide="2"
    >
      <div className="mb-12">
        <h2 className="text-5xl font-bold text-[var(--ppt-text)] mb-4" style={{ fontFamily: 'var(--ppt-font-display)' }} data-ppt-text="true">核心指标矩阵展示</h2>
        <p className="text-xl text-[var(--ppt-muted)] font-light" style={{ fontFamily: 'var(--ppt-font-body)' }} data-ppt-text="true">
          以下图表和卡片的数据展示了组件化自动切割能力的完美结合，复杂布局手到擒来。
        </p>
      </div>

      <div className="flex-1 grid grid-cols-3 grid-rows-2 gap-8">
        <div
          className="col-span-2 row-span-1 bg-[var(--ppt-surface)] backdrop-blur-3xl rounded-[2rem] border border-[var(--ppt-border)] p-12 flex flex-col justify-center relative overflow-hidden shadow-[0_0_80px_-20px_var(--ppt-primary)]"
          data-ppt-bg="true"
        >
           <h3 className="text-2xl text-[var(--ppt-muted)] mb-6" style={{ fontFamily: 'var(--ppt-font-body)' }} data-ppt-text="true">一季度利润预期涨幅</h3>
           <div className="text-8xl font-black text-transparent bg-clip-text bg-gradient-to-br from-[var(--ppt-primary)] to-[var(--ppt-secondary)]" style={{ fontFamily: 'var(--ppt-font-display)' }} data-ppt-text="true">
             + 1,420%
           </div>
        </div>

        <div
          className="col-span-1 row-span-2 bg-gradient-to-b from-[var(--ppt-surface-strong)] to-[var(--ppt-bg)] rounded-[2rem] border border-[var(--ppt-border)] p-10 flex flex-col items-center justify-center relative"
          data-ppt-bg="true"
        >
            <h3 className="text-2xl text-[var(--ppt-text)] mb-10 w-full text-center" style={{ fontFamily: 'var(--ppt-font-body)' }} data-ppt-text="true">增长曲线预测</h3>
            <svg width="300" height="400" viewBox="0 0 300 400" className="opacity-80">
               <path d="M 20 380 Q 80 320 150 200 T 280 50" fill="none" stroke="url(#cyanGlow)" strokeWidth="8" strokeLinecap="round" />
               <circle cx="280" cy="50" r="12" fill="var(--ppt-secondary)" />
               <defs>
                 <linearGradient id="cyanGlow" x1="0" y1="1" x2="1" y2="0">
                    <stop offset="0%" stopColor="var(--ppt-primary)" />
                    <stop offset="100%" stopColor="var(--ppt-secondary)" />
                 </linearGradient>
               </defs>
            </svg>
        </div>

        <div
          className="col-span-1 row-span-1 bg-[var(--ppt-surface-strong)] rounded-[2rem] p-10 flex flex-col justify-center border-l-4 border-l-[var(--ppt-accent)]"
          data-ppt-bg="true"
        >
            <h4 className="text-xl text-[var(--ppt-accent)] font-bold mb-4" style={{ fontFamily: 'var(--ppt-font-body)' }} data-ppt-text="true">策略优势</h4>
            <ul className="space-y-4 text-[var(--ppt-muted)] text-lg" style={{ fontFamily: 'var(--ppt-font-body)' }}>
                <li data-ppt-text="true">● 无需复杂环境依赖</li>
                <li data-ppt-text="true">● 支持 React 生态任意库</li>
                <li data-ppt-text="true">● Tailwind 神级排版赋能</li>
            </ul>
        </div>

        <div className="col-span-1 row-span-1 bg-gradient-to-tr from-[var(--ppt-accent)]/30 to-transparent rounded-[2rem] border border-[var(--ppt-border)] p-10 flex flex-col justify-center" data-ppt-bg="true">
            <div className="text-4xl font-bold text-[var(--ppt-accent)] mb-2" style={{ fontFamily: 'var(--ppt-font-display)' }} data-ppt-text="true">3.2M</div>
            <div className="text-[var(--ppt-muted)]" style={{ fontFamily: 'var(--ppt-font-body)' }} data-ppt-text="true">活跃渲染节点数</div>
        </div>
      </div>
    </div>
  )
}
