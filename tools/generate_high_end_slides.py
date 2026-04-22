import os

out_dir = "output/projects/20260422-132950-presentation/slides"

# RULES:
# 1. Macro & Micro Typography (Super big display + tiny tracking labels)
# 2. Add padded shadows for wrappers: `p-16 -m-16` on `data-ppt-bg` cards.
# 3. Asymmetry & Negative space
# 4. Hairline Borders

S1 = """import { getDeckStylePreset, styleVars } from '../../styles'
import type { CSSProperties } from 'react'

export default function Slide_1() {
  const baseVars = styleVars(getDeckStylePreset('editorial-ink'))
  return (
    <div className="w-[1920px] h-[1080px] bg-[#EBE9E5] relative overflow-hidden" style={baseVars as CSSProperties} data-ppt-slide={1}>
      {/* MACRO BACKGROUND TYPOGRAPHY (Bleeding edges) */}
      <div className="absolute -left-[100px] top-[100px] text-[320px] leading-[0.8] text-[#1C1A17] opacity-5 font-black tracking-tighter mix-blend-multiply pointer-events-none" style={{ fontFamily: 'Georgia, serif' }}>
        WORLD<br/>TODAY.
      </div>

      {/* MICRO LABEL */}
      <div className="absolute top-[80px] left-[120px] text-[12px] tracking-[0.4em] font-mono text-[#D97706] uppercase font-bold">
        [ SEC. 01 // GLOBAL CONTEXT ]
      </div>

      <div className="absolute left-[120px] top-[300px] w-[1px] h-[300px] bg-[#D97706]/50"></div>

      {/* ASYMMETRIC CONTENT BLOCK */}
      <div className="absolute left-[200px] bottom-[200px] w-[1400px]">
        <h1 data-ppt-text="true" className="text-[140px] font-black text-[#1C1917] leading-[1.05] tracking-tight" style={{ fontFamily: 'Georgia, serif' }}>
          为什么小学生<br/>需要每天了解世界
        </h1>

        {/* SHADOW WRAPPED METADATA CARD */}
        <div className="mt-16 inline-flex" data-ppt-bg="true" className="p-8 -m-8 relative z-10">
          <div className="bg-white/80 backdrop-blur-2xl border-l-4 border-l-[#D97706] shadow-[0_20px_60px_rgba(0,0,0,0.05)] pl-12 pr-16 py-8">
            <div className="text-[32px] text-[#57534E] italic font-serif leading-relaxed" data-ppt-text="true">
              "一个不了解世界的孩子，将来会在这个世界里迷路。"
            </div>
            <div className="text-[14px] font-mono tracking-widest text-[#B91C1C] mt-6" data-ppt-text="true">
              WRITTEN BY THE PARENTS // 2026
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
"""

S2 = """import { getDeckStylePreset, styleVars } from '../../styles'
import type { CSSProperties } from 'react'

export default function Slide_2() {
  const baseVars = styleVars(getDeckStylePreset('editorial-ink'))
  return (
    <div className="w-[1920px] h-[1080px] bg-[#1C1A17] relative overflow-hidden" style={baseVars as CSSProperties} data-ppt-slide={2}>
      {/* DARK MODE HIGH CONTRAST */}

      {/* MICRO LABEL */}
      <div className="absolute top-[80px] right-[120px] text-[12px] tracking-[0.4em] font-mono text-[#EBE9E5]/40 uppercase text-right">
        [ SEC. 02 // THE COST OF IGNORANCE ]
      </div>

      <div className="flex h-full w-full">
        {/* LEFT COLLUMN: NEGATIVE SPACE & HUGE TITLE */}
        <div className="flex-1 px-[160px] pt-[240px] border-r border-[#EBE9E5]/10">
          <h2 data-ppt-text="true" className="text-[100px] font-black text-[#EBE9E5] leading-[1.1]" style={{ fontFamily: 'Georgia, serif' }}>
            不了解世界<br/>
            <span className="text-[#D97706]">的代价是什么</span>
          </h2>
          <div className="mt-24 text-[24px] text-[#A8A29E] max-w-[500px] leading-relaxed font-light" data-ppt-text="true">
            他们将面对的，不是一个稳定的、可以按照既有路径行走的世界。而是一个剧烈变化、充斥不确定性、需要快速理解新事物的全新生态。
          </div>
        </div>

        {/* RIGHT COLLUMN: BENTO GRID WITH PADDING WRAPPERS */}
        <div className="w-[880px] bg-[#141210] p-[100px] flex flex-col justify-center relative shadow-[inset_40px_0_100px_rgba(0,0,0,0.5)]">
           <div data-ppt-group="list" className="grid grid-cols-1 gap-12 relative z-10 w-full">
            {[
              { num: "01", t: "缺乏适应力", b: "无法理解不在课本内的新形态危机" },
              { num: "02", t: "认知封闭", b: "用旧的标准答案评判高度复杂的社会运作" },
              { num: "03", t: "同理心真空", b: "沉浸在自我叙事，无法共情他人的苦难" }
            ].map((item, i) => (
              <div data-ppt-item key={i} className="p-12 -m-12 relative">
                <div className="bg-[#1C1A17] border border-[#EBE9E5]/10 shadow-[0_32px_64px_rgba(0,0,0,0.6)] p-12 flex items-start gap-12 group transition-all">
                  <div data-ppt-item-bg className="hidden"/>
                  <div className="text-[80px] font-light text-[#D97706]/40 leading-none font-mono" data-ppt-bullet="true">
                    {item.num}
                  </div>
                  <div>
                    <h3 data-ppt-text="true" className="text-[40px] font-bold text-[#EBE9E5] mb-4" style={{ fontFamily: 'Georgia, serif' }}>{item.t}</h3>
                    <p data-ppt-text="true" className="text-[22px] text-[#A8A29E] leading-relaxed">{item.b}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
"""

S3 = """import { getDeckStylePreset, styleVars } from '../../styles'
import type { CSSProperties } from 'react'

export default function Slide_3() {
  const baseVars = styleVars(getDeckStylePreset('editorial-ink'))
  return (
    <div className="w-[1920px] h-[1080px] bg-[#EBE9E5] relative overflow-hidden flex items-center" style={baseVars as CSSProperties} data-ppt-slide={3}>
      <div className="absolute top-[80px] left-[120px] text-[12px] tracking-[0.4em] font-mono text-[#D97706] uppercase">
        [ SEC. 03 // STATISTICS & TRENDS ]
      </div>

      {/* HAIRLINE GRID SYSTEM */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-[0.03]">
        <pattern id="grid" width="80" height="80" patternUnits="userSpaceOnUse">
          <path d="M 80 0 L 0 0 0 80" fill="none" stroke="#1C1A17" strokeWidth="1"/>
        </pattern>
        <rect width="1920" height="1080" fill="url(#grid)" />
      </svg>

      <div className="w-full flex items-center px-[160px] gap-[120px]">

        {/* MASSIVE NUMBER CALLOUT */}
        <div data-ppt-bg="true" className="p-20 -m-20 shrink-0">
          <div className="relative border border-[#D97706]/20 bg-white/40 shadow-[0_40px_100px_rgba(0,0,0,0.03)] backdrop-blur-xl rounded-[40px] p-24 flex items-center justify-center">
            {/* GLOW ORB */}
            <div className="absolute w-[400px] h-[400px] rounded-full bg-[#D97706]/20 mix-blend-multiply filter blur-[80px]"></div>

            <div className="text-center relative z-10">
              <span className="text-[260px] font-black text-[#B91C1C] leading-[0.8]" style={{ fontFamily: 'Georgia, serif' }} data-ppt-text="true">
                60%
              </span>
              <div className="mt-8 text-[14px] font-mono tracking-[0.4em] text-[#57534E]">OF FUTURE JOBS</div>
            </div>
          </div>
        </div>

        {/* RIGHT TEXT BLOCK */}
        <div className="max-w-[700px]">
          <h2 data-ppt-text="true" className="text-[80px] font-black text-[#1C1A17] leading-[1.1] mb-12" style={{ fontFamily: 'Georgia, serif' }}>
            未来的工作<br/>
            今天还不存在
          </h2>
          <div className="w-[120px] h-[2px] bg-[#D97706] mb-12"></div>
          <p data-ppt-text="true" className="text-[32px] font-light text-[#57534E] leading-relaxed">
            2035年他们进入职场时，面对的世界将由 AI 全面改写。最高级的竞争力，是<span className="font-bold text-[#1C1A17]">迅速理解陌生事物的能力</span>，而不是死记背熟已有知识。
          </p>
        </div>

      </div>
    </div>
  )
}
"""

S4 = """import { getDeckStylePreset, styleVars } from '../../styles'
import type { CSSProperties } from 'react'

export default function Slide_4() {
  const baseVars = styleVars(getDeckStylePreset('editorial-ink'))
  return (
    <div className="w-[1920px] h-[1080px] bg-[#1C1A17] relative overflow-hidden flex flex-col items-center justify-center" style={baseVars as CSSProperties} data-ppt-slide={4}>

      {/* MASSIVE BLEEDING QUOTE MARKS AS BACKGROUND */}
      <div className="absolute top-[-200px] left-[-100px] text-[1200px] text-[#EBE9E5] opacity-[0.02] font-serif leading-none" data-ppt-bg="true">
        “
      </div>

      {/* FINELY BORDERED CONTENT BOX */}
      <div data-ppt-bg="true" className="p-20 -m-20 z-10">
        <div className="border border-[#EBE9E5]/10 bg-black/40 backdrop-blur-3xl shadow-[0_40px_100px_rgba(0,0,0,0.6)] px-[140px] py-[100px] max-w-[1400px] mx-auto text-center relative">

          <div className="absolute -top-[1px] left-1/2 -translate-x-1/2 w-[200px] h-[2px] bg-gradient-to-r from-transparent via-[#D97706] to-transparent"></div>

          <h2 data-ppt-text="true" className="text-[72px] font-light text-[#EBE9E5] leading-[1.4] tracking-wide" style={{ fontFamily: 'Georgia, serif' }}>
            新闻，本质上是世界的实时教材。<br/>
            每一条新闻背后，都有科学、地理、<br/>历史与人性的交织。
          </h2>

          <div className="mt-20 pt-16 border-t border-[#EBE9E5]/10 inline-block px-24">
            <p data-ppt-text="true" className="text-[20px] font-mono tracking-[0.3em] text-[#D97706] uppercase">
              US News Literacy Project
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
"""

S5 = """import { getDeckStylePreset, styleVars } from '../../styles'
import type { CSSProperties } from 'react'

export default function Slide_5() {
  const baseVars = styleVars(getDeckStylePreset('editorial-ink'))
  return (
    <div className="w-[1920px] h-[1080px] bg-[#EBE9E5] relative overflow-hidden py-[120px] px-[160px] flex flex-col" style={baseVars as CSSProperties} data-ppt-slide={5}>
      <div className="absolute top-[80px] left-[160px] text-[12px] tracking-[0.4em] font-mono text-[#D97706] uppercase">
        [ SEC. 04 // THE FRAMEWORK ]
      </div>

      <div className="mt-[60px] mb-[100px]">
        <h2 data-ppt-text="true" className="text-[72px] font-black text-[#1C1A17]" style={{ fontFamily: 'Georgia, serif' }}>
          建立认知的四个基石
        </h2>
      </div>

      {/* OVERLAPPING CARDS WITH NEGATIVE SPACE */}
      <div data-ppt-group="list" className="flex-1 flex gap-[40px] relative">
        {[
          { num: "01", t: "适龄过滤", b: "剥离宏大叙事与权力博弈，聚焦科技与人文故事。" },
          { num: "02", t: "降维转译", b: "用【芯片变少导致游戏机贵了】替代【半导体周期性缺货】。" },
          { num: "03", t: "启发重于灌输", b: "永远以提问结束。不要给标准答案，问：“你觉得呢？”" },
          { num: "04", t: "仪式感固定", b: "每天晚上睡前的10分钟，将看世界固化为家庭习惯。" }
        ].map((item, i) => (
          <div data-ppt-item key={i} className="flex-1 p-10 -m-10 group relative mt-[*]">
            {/* STAGGERED HEIGHTS FOR ASYMMETRY */}
            <div className={`h-full bg-white border border-[#1C1A17]/10 shadow-[0_20px_60px_rgba(0,0,0,0.04)] rounded-[20px] p-[60px] flex flex-col relative transition-transform duration-500 hover:-translate-y-4`} style={{ marginTop: `${i * 40}px` }}>
              <div data-ppt-item-bg className="hidden"/>
              <div className="mb-auto pb-12 border-b border-[#1C1A17]/10">
                <div className="text-[64px] font-black text-[#B91C1C]" style={{ fontFamily: 'Georgia, serif' }} data-ppt-bullet="true">
                  {item.num}
                </div>
              </div>
              <div className="mt-12">
                <h3 data-ppt-text="true" className="text-[32px] font-bold text-[#1C1A17] mb-6" style={{ fontFamily: 'Georgia, serif' }}>{item.t}</h3>
                <p data-ppt-text="true" className="text-[20px] text-[#57534E] leading-[1.8]">{item.b}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
"""

S6 = """import { getDeckStylePreset, styleVars } from '../../styles'
import type { CSSProperties } from 'react'

export default function Slide_6() {
  const baseVars = styleVars(getDeckStylePreset('editorial-ink'))
  return (
    <div className="w-[1920px] h-[1080px] bg-[#1C1A17] relative overflow-hidden flex flex-col justify-center items-center" style={baseVars as CSSProperties} data-ppt-slide={6}>
      <div className="absolute top-[80px] left-[120px] text-[12px] tracking-[0.4em] font-mono text-[#D97706] uppercase">
        [ CONCLUSION ]
      </div>

      {/* HAIRLINE HORIZONTAL RULES */}
      <svg className="absolute w-full h-[600px] top-1/2 -translate-y-1/2 pointer-events-none opacity-20">
        <line x1="0" y1="0" x2="1920" y2="0" stroke="#EBE9E5" strokeWidth="1" />
        <line x1="0" y1="600" x2="1920" y2="600" stroke="#EBE9E5" strokeWidth="1" />
      </svg>

      <div data-ppt-bg="true" className="p-16 -m-16 z-10 w-full">
        <div className="max-w-[1200px] mx-auto text-center px-24 py-32">
          <p data-ppt-text="true" className="text-[48px] font-light text-[#A8A29E] leading-[1.8]" style={{ fontFamily: 'Georgia, serif' }}>
            你只需要每天和孩子说一件发生的事情<br/>
            然后问他：<span className="text-[#EBE9E5] font-normal tracking-wide">“你觉得呢？”</span>
          </p>
          <div className="w-[80px] h-[2px] bg-[#D97706] mx-auto mt-24 mb-16"></div>
          <p data-ppt-text="true" className="text-[20px] font-mono tracking-[0.2em] text-[#A8A29E]/60 uppercase">
            世界值得被认真对待，你的想法也同样重要。
          </p>
        </div>
      </div>
    </div>
  )
}
"""

with open(f"{out_dir}/Slide_1.tsx", "w") as f: f.write(S1)
with open(f"{out_dir}/Slide_2.tsx", "w") as f: f.write(S2)
with open(f"{out_dir}/Slide_3.tsx", "w") as f: f.write(S3)
with open(f"{out_dir}/Slide_4.tsx", "w") as f: f.write(S4)
with open(f"{out_dir}/Slide_5.tsx", "w") as f: f.write(S5)
with open(f"{out_dir}/Slide_6.tsx", "w") as f: f.write(S6)

with open(f"{out_dir}/index.ts", "w") as f:
    f.write('''import Slide_1 from './Slide_1'
import Slide_2 from './Slide_2'
import Slide_3 from './Slide_3'
import Slide_4 from './Slide_4'
import Slide_5 from './Slide_5'
import Slide_6 from './Slide_6'

export default [Slide_1, Slide_2, Slide_3, Slide_4, Slide_5, Slide_6]
''')

print("All High-End slides generated.")
