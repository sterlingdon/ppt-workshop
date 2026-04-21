import { createElement, useEffect, useState } from 'react'
import type { FC } from 'react'
import slidesExport from './slides'

function App() {
  const [slides, setSlides] = useState<FC[]>([])
  const [currentIdx, setCurrentIdx] = useState(0)
  const isExtract = new URLSearchParams(window.location.search).get('extract') === '1'

  useEffect(() => {
    if (slidesExport && Array.isArray(slidesExport)) {
      setSlides(slidesExport)
    }
  }, [])

  useEffect(() => {
    if (isExtract) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight' || e.key === 'Space' || e.key === 'ArrowDown') {
        setCurrentIdx(p => Math.min(slides.length - 1, p + 1))
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        setCurrentIdx(p => Math.max(0, p - 1))
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [slides.length, isExtract])

  // Extract Mode: Render all slides strictly unscaled and stacked for Playwright
  if (isExtract) {
    return (
      <div className="flex flex-col bg-transparent w-[1920px]">
        {slides.map((SlideComponent, index) => (
          <div key={index} className="relative w-[1920px] h-[1080px] overflow-hidden">
             <SlideComponent />
          </div>
        ))}
      </div>
    )
  }

  // Presentation Mode: Scale to fit window + Pagination
  return (
    <div className="flex flex-col bg-black items-center justify-center h-screen w-full overflow-hidden relative">
      {slides.length === 0 && <div className="text-white p-10">等待生成幻灯片...</div>}
      
      {slides.length > 0 && (
        <div 
          className="relative transition-transform duration-500 ease-out shadow-2xl" 
          style={{ 
            width: '1920px', 
            height: '1080px', 
            transform: `scale(Math.min(window.innerWidth / 1920, window.innerHeight / 1080) * 0.95) scale(${Math.min(window.innerWidth / 1920, window.innerHeight / 1080) * 0.95})`, 
            zoom: Math.min(window.innerWidth / 1920, window.innerHeight / 1080) * 0.95 
          }}
        >
           {createElement(slides[currentIdx])}
        </div>
      )}
      
      {/* PPT 页面指示器 */}
      {!isExtract && slides.length > 0 && (
        <div className="absolute bottom-6 text-white/50 text-sm tracking-widest font-mono">
           {currentIdx + 1} / {slides.length}
        </div>
      )}
    </div>
  )
}

export default App
