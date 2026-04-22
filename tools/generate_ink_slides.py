import os

out_dir = "output/projects/20260422-132950-presentation/slides"

S1 = """import { getDeckStylePreset, styleVars } from '../../styles'
import type { CSSProperties } from 'react'

const extendedTokens: CSSProperties = {}

export default function Slide_1() {
  const baseVars = styleVars(getDeckStylePreset('editorial-ink'))
  return (
    <div className="w-[1920px] h-[1080px] bg-[#F8F5F0] relative overflow-hidden flex flex-col justify-center items-center" style={baseVars as CSSProperties} data-ppt-slide={1}>
      {/* ⚠️ Shadow Wrapper Contract applied */}
      <div data-ppt-bg="true" className="p-16 -m-16 z-10 relative">
        <div className="bg-white border border-[#D6D3D1] shadow-[0_24px_60px_rgba(0,0,0,0.06)] rounded-3xl p-24 w-[1400px] flex flex-col items-center relative">
          <div className="absolute top-0 w-[200px] h-2 bg-[#B91C1C]"></div>
          <h1 data-ppt-text="true" className="text-[110px] font-black text-[#1C1917] mt-12 text-center leading-tight" style={{fontFamily: "'Playfair Display', serif"}}>
            为什么小学生需要<br/>每天了解世界
          </h1>
          <div className="text-[36px] text-[#57534E] mt-16 text-center italic font-serif" data-ppt-text="true">
            ——写给每一位想要培养孩子全球视野的家长
          </div>
        </div>
      </div>
      {/* 装饰线 */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-20">
        <line x1="160" y1="0" x2="160" y2="1080" stroke="#1C1917" strokeWidth="1" />
        <line x1="1760" y1="0" x2="1760" y2="1080" stroke="#1C1917" strokeWidth="1" />
      </svg>
    </div>
  )
}
"""

S2 = """import { getDeckStylePreset, styleVars } from '../../styles'
import type { CSSProperties } from 'react'

export default function Slide_2() {
  const baseVars = styleVars(getDeckStylePreset('editorial-ink'))
  return (
    <div className="w-[1920px] h-[1080px] bg-[#F8F5F0] relative overflow-hidden px-[160px] py-[120px]" style={baseVars as CSSProperties} data-ppt-slide={2}>
      <h2 data-ppt-text="true" className="text-[80px] font-black text-[#1C1917] mb-[80px]" style={{fontFamily: "'Playfair Display', serif"}}>
        这个时代，不了解世界的代价
      </h2>
      <div data-ppt-group="list" className="grid grid-cols-2 gap-16">
        {[
          {"t": "缺乏适应力", "b": "60%以上的工作今天还不存在，无法预见未来。"},
          {"t": "认知封闭", "b": "极易被耸人听闻的标题裹挟，缺乏独立思考体系。"},
          {"t": "缺乏共情力", "b": "不了解社会的参差，容易陷入自我中心的盲区。"},
          {"t": "失去竞争力", "b": "习惯于单一的标准答案，丧失应对复杂世界的能力。"}
        ].map((item, i) => (
          /* ⚠️ Shadow Wrapper Contract applied */
          <div data-ppt-item key={i} className="p-8 -m-8">
            <div className="bg-white border border-[#D6D3D1] shadow-[0_12px_40px_rgba(0,0,0,0.05)] rounded-2xl p-12 flex items-start gap-8">
              <div data-ppt-item-bg className="hidden"/>
              <div className="w-16 h-16 rounded-full bg-[#18181B] flex items-center justify-center shrink-0" data-ppt-bullet="true">
                <span className="text-white text-2xl font-bold font-serif">{i+1}</span>
              </div>
              <div>
                <h3 data-ppt-text="true" className="text-[40px] font-bold text-[#1C1917] mb-4" style={{fontFamily: "'Playfair Display', serif"}}>{item.t}</h3>
                <p data-ppt-text="true" className="text-[28px] text-[#57534E] leading-relaxed">{item.b}</p>
              </div>
            </div>
          </div>
        ))}
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
    <div className="w-[1920px] h-[1080px] bg-[#F8F5F0] relative overflow-hidden flex items-center justify-center" style={baseVars as CSSProperties} data-ppt-slide={3}>
      <div className="absolute left-[160px] top-0 bottom-0 w-[1px] bg-[#D6D3D1]"></div>

      <div className="w-full px-[240px] flex gap-[120px] items-center relative z-10">
         <div className="flex-1">
           <div className="w-16 h-2 bg-[#B91C1C] mb-12"></div>
           <h2 data-ppt-text="true" className="text-[100px] font-black text-[#1C1917] leading-[1.1] mb-8" style={{fontFamily: "'Playfair Display', serif"}}>
             剧烈变化<br/>与不确定性
           </h2>
           <p data-ppt-text="true" className="text-[36px] text-[#57534E] leading-relaxed">
             今天小学生将在 2035 年之后进入职场。<br/>在那个世界里，绝大部分日常工作将被 AI 彻底重塑。能力比知识更重要。
           </p>
         </div>
         {/* ⚠️ Shadow Wrapper Contract applied */}
         <div data-ppt-bg="true" className="p-16 -m-16 shrink-0">
            <div className="bg-white border border-[#D6D3D1] shadow-[0_20px_80px_rgba(0,0,0,0.08)] rounded-3xl p-24 flex flex-col items-center justify-center text-center w-[640px]">
              <span data-ppt-text="true" className="text-[240px] font-black leading-none text-[#B91C1C]" style={{fontFamily: "'Playfair Display', serif"}}>
                60%
              </span>
              <p data-ppt-text="true" className="text-[36px] text-[#1C1917] font-bold mt-12">
                以上的工作今天还不存在
              </p>
            </div>
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
    <div className="w-[1920px] h-[1080px] bg-[#F8F5F0] relative overflow-hidden flex items-center justify-center px-[200px]" style={baseVars as CSSProperties} data-ppt-slide={4}>
      <div className="w-full flex items-center gap-[100px]">
         <div className="relative text-[300px] text-[#D6D3D1] leading-none font-serif opacity-40 shrink-0" data-ppt-bg="true">
           “
         </div>
         <div className="flex-1">
           <h2 data-ppt-text="true" className="text-[72px] font-black text-[#1C1917] leading-[1.3]" style={{fontFamily: "'Playfair Display', serif"}}>
             新闻，本质上是世界的实时教材。每一条新闻背后，都有科学、地理、历史、经济、人性的交织。用新闻教孩子，是最生动、最有时代感的教育。
           </h2>
           <div className="mt-16 text-[32px] font-bold text-[#B91C1C] flex items-center gap-6" data-ppt-text="true">
             <div className="w-12 h-[2px] bg-[#B91C1C]"></div>美国新闻素养项目 (News Literacy Project)
           </div>
         </div>
         <div className="relative text-[300px] text-[#D6D3D1] leading-none font-serif opacity-40 shrink-0 self-end mt-48" data-ppt-bg="true">
           ”
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
    <div className="w-[1920px] h-[1080px] bg-[#F8F5F0] relative overflow-hidden px-[160px] py-[120px]" style={baseVars as CSSProperties} data-ppt-slide={5}>
      <h2 data-ppt-text="true" className="text-[80px] font-black text-[#1C1917] mb-[80px]" style={{fontFamily: "'Playfair Display', serif"}}>
        给孩子讲新闻的四个步骤
      </h2>
      <div data-ppt-group="list" className="grid grid-cols-4 gap-8">
        {[
          {"step": "Step 1", "t": "选择适龄的", "b": "摒弃纯粹血腥暴力、政治博弈。选择科技发现、社会温情、动植物及他国文化等孩子感兴趣的话题。"},
          {"step": "Step 2", "t": "翻译成童言", "b": "半导体短缺难懂，但“游戏机里的芯片变贵了”易懂。用具体的周边事物做类比，解释复杂概念。"},
          {"step": "Step 3", "t": "以提问结束", "b": "讲完不要抛出绝对的真理，而是问“你觉得呢”。鼓励其自己得出结论，远胜过单向灌输。"},
          {"step": "Step 4", "t": "建立仪式感", "b": "每天固定睡前10分钟或上学路上，让交流新闻变成习惯，传递“关心世界”的家庭底色。"}
        ].map((item, i) => (
          /* ⚠️ Shadow Wrapper Contract applied */
          <div data-ppt-item key={i} className="p-8 -m-8">
            <div className="bg-white border border-[#D6D3D1] shadow-[0_8px_32px_rgba(0,0,0,0.06)] rounded-2xl p-10 h-full flex flex-col relative overflow-hidden">
               <div data-ppt-item-bg className="hidden"/>
               <div className="text-[20px] font-bold text-[#B91C1C] mb-8 uppercase tracking-widest font-serif" data-ppt-text="true">{item.step}</div>
               <h3 data-ppt-text="true" className="text-[36px] font-bold text-[#1C1917] mb-6" style={{fontFamily: "'Playfair Display', serif"}}>{item.t}</h3>
               <p data-ppt-text="true" className="text-[24px] text-[#57534E] leading-relaxed flex-1">{item.b}</p>
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
    <div className="w-[1920px] h-[1080px] bg-[#F8F5F0] relative overflow-hidden flex flex-col justify-center items-center" style={baseVars as CSSProperties} data-ppt-slide={6}>
      <svg className="absolute top-0 w-full h-[400px] pointer-events-none">
        <line x1="0" y1="200" x2="1920" y2="200" stroke="#D6D3D1" strokeWidth="1" opacity="0.5" />
      </svg>
      {/* ⚠️ Shadow Wrapper Contract applied */}
      <div data-ppt-bg="true" className="p-16 -m-16 z-10 relative">
        <div className="bg-white border-t-8 border-t-[#B91C1C] shadow-[0_24px_80px_rgba(0,0,0,0.08)] rounded-b-3xl p-24 w-[1200px] flex flex-col items-center">
          <h2 data-ppt-text="true" className="text-[64px] font-black text-[#1C1917] mb-12 text-center" style={{fontFamily: "'Playfair Display', serif"}}>
            给家长的一句话
          </h2>
          <p data-ppt-text="true" className="text-[36px] text-[#57534E] text-center leading-relaxed">
            你不需要懂政治，不需要懂经济，不需要懂科技。<br/><br/>
            你只需要每天和孩子说一件发生在这个星球上的事，然后问他：“你觉得呢？”<br/><br/>
            这一句话，比任何课外班都更有价值。
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

print("All Editorial Ink slides created.")
