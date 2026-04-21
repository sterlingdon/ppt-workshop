import { getDeckStylePreset, styleVars } from '../styles'

export default function Slide_1() {
  const preset = getDeckStylePreset('aurora-borealis')

  return (
    // 幻灯片根节点
    <div
      className="w-[1920px] h-[1080px] bg-[var(--ppt-bg)] flex flex-col items-center justify-center relative overflow-hidden"
      style={styleVars(preset)}
      data-ppt-slide="1"
    >
      {/* 装饰性背景流光 */}
      <div className="absolute top-1/4 left-1/4 w-[600px] h-[600px] bg-[var(--ppt-primary)]/30 rounded-full blur-[120px]"></div>
      <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-[var(--ppt-secondary)]/30 rounded-full blur-[100px]"></div>

      {/* PPT 局部截图组件：毛玻璃卡片 */}
      <div
        className="z-10 relative backdrop-blur-2xl bg-[var(--ppt-surface)] ring-1 ring-[var(--ppt-border)] rounded-[3rem] p-24 shadow-2xl flex flex-col items-center"
        data-ppt-bg="true"
      >
         {/* PPT 字体劫持文本 */}
         <h1
            className="text-8xl font-black text-transparent bg-clip-text bg-gradient-to-br from-[var(--ppt-text)] to-[var(--ppt-muted)] mb-8"
            style={{ fontFamily: 'var(--ppt-font-display)' }}
            data-ppt-text="true"
         >
           山寨季的黎明
         </h1>

         <p
            className="text-3xl text-[var(--ppt-muted)] font-light max-w-2xl text-center leading-relaxed"
            style={{ fontFamily: 'var(--ppt-font-body)' }}
            data-ppt-text="true"
         >
           通过极简的 TailwindCSS 还原史诗级视觉排版引擎，我们将打造真正工业级可编辑幻灯片。
         </p>
      </div>
    </div>
  )
}
