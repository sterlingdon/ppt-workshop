export default function Slide_1() {
  return (
    // 幻灯片根节点
    <div className="w-[1920px] h-[1080px] bg-[#0A0A0A] flex flex-col items-center justify-center relative overflow-hidden" data-ppt-slide="1">
      {/* 装饰性背景流光 */}
      <div className="absolute top-1/4 left-1/4 w-[600px] h-[600px] bg-purple-600/30 rounded-full blur-[120px]"></div>
      <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-cyan-600/30 rounded-full blur-[100px]"></div>

      {/* PPT 局部截图组件：毛玻璃卡片 */}
      <div 
        className="z-10 relative backdrop-blur-2xl bg-white/5 ring-1 ring-white/10 rounded-[3rem] p-24 shadow-2xl flex flex-col items-center" 
        data-ppt-bg="true"
      >
         {/* PPT 字体劫持文本 */}
         <h1 
            className="text-8xl font-black font-sans text-transparent bg-clip-text bg-gradient-to-br from-white to-white/50 mb-8" 
            data-ppt-text="true"
         >
           山寨季的黎明
         </h1>
         
         <p 
            className="text-3xl text-zinc-300 font-light font-sans max-w-2xl text-center leading-relaxed" 
            data-ppt-text="true"
         >
           通过极简的 TailwindCSS 还原史诗级视觉排版引擎，我们将打造真正工业级可编辑幻灯片。
         </p>
      </div>
    </div>
  )
}
