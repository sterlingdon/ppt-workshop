export default function Slide_2() {
  return (
    <div className="w-[1920px] h-[1080px] bg-zinc-950 flex flex-col p-20" data-ppt-slide="2">
      {/* 头部展示文字 */}
      <div className="mb-12">
        <h2 className="text-5xl font-bold text-white mb-4" data-ppt-text="true">核心指标矩阵展示</h2>
        <p className="text-xl text-zinc-400 font-light" data-ppt-text="true">
          以下图表和卡片的数据展示了组件化自动切割能力的完美结合，复杂布局手到擒来。
        </p>
      </div>

      {/* Bento 便当盒 Grid 布局 */}
      <div className="flex-1 grid grid-cols-3 grid-rows-2 gap-8">
        
        {/* 卡片 1 : 带有透明磨砂和内部边框的巨型状态卡块 */}
        <div 
          className="col-span-2 row-span-1 bg-white/5 backdrop-blur-3xl rounded-[2rem] border border-white/10 p-12 flex flex-col justify-center relative overflow-hidden shadow-[0_0_80px_-20px_rgba(120,0,255,0.4)]"
          data-ppt-bg="true"
        >
           <h3 className="text-2xl text-zinc-300 mb-6" data-ppt-text="true">一季度利润预期涨幅</h3>
           <div className="text-8xl font-black text-transparent bg-clip-text bg-gradient-to-br from-indigo-400 to-cyan-400" data-ppt-text="true">
             + 1,420%
           </div>
        </div>

        {/* 卡片 2 : AI 渲染原生的矢量图表结构 (SVG 直接绘制) */}
        <div 
          className="col-span-1 row-span-2 bg-gradient-to-b from-indigo-900/50 to-zinc-900/50 rounded-[2rem] border border-indigo-500/20 p-10 flex flex-col items-center justify-center relative"
          data-ppt-bg="true"
        >
            <h3 className="text-2xl text-zinc-200 mb-10 w-full text-center" data-ppt-text="true">增长曲线预测</h3>
            {/* 这个 SVG 因为包裹在 ppt-bg 里，会被顺手截取成像素完美还原到 PPT */}
            <svg width="300" height="400" viewBox="0 0 300 400" className="opacity-80">
               <path d="M 20 380 Q 80 320 150 200 T 280 50" fill="none" stroke="url(#cyanGlow)" strokeWidth="8" strokeLinecap="round" />
               <circle cx="280" cy="50" r="12" fill="#22d3ee" />
               <defs>
                 <linearGradient id="cyanGlow" x1="0" y1="1" x2="1" y2="0">
                    <stop offset="0%" stopColor="#4f46e5" />
                    <stop offset="100%" stopColor="#22d3ee" />
                 </linearGradient>
               </defs>
            </svg>
        </div>

        {/* 卡片 3 : 比较常规的信息说明块 */}
        <div 
          className="col-span-1 row-span-1 bg-zinc-900 rounded-[2rem] p-10 flex flex-col justify-center border-l-4 border-l-pink-500"
          data-ppt-bg="true"
        >
            <h4 className="text-xl text-pink-400 font-bold mb-4" data-ppt-text="true">策略优势</h4>
            <ul className="space-y-4 text-zinc-300 text-lg">
                <li data-ppt-text="true">● 无需复杂环境依赖</li>
                <li data-ppt-text="true">● 支持 React 生态任意库</li>
                <li data-ppt-text="true">● Tailwind 神级排版赋能</li>
            </ul>
        </div>

        {/* 卡片 4 : 极简带渐变的块 */}
        <div className="col-span-1 row-span-1 bg-gradient-to-tr from-rose-900/40 to-transparent rounded-[2rem] border border-rose-500/20 p-10 flex flex-col justify-center" data-ppt-bg="true">
            <div className="text-4xl font-bold text-rose-300 mb-2" data-ppt-text="true">3.2M</div>
            <div className="text-rose-200/60" data-ppt-text="true">活跃渲染节点数</div>
        </div>
      </div>

    </div>
  )
}
