import json
import os

project_dir = "output/projects/20260422-171208-test-shadow-wrapper"
with open(f"{project_dir}/outline.json", "r") as f:
    outline = json.load(f)

slides_dir = f"{project_dir}/slides"
os.makedirs(slides_dir, exist_ok=True)

slide_template = """import { getDeckStylePreset, styleVars } from '../../styles'
import type { CSSProperties } from 'react'

const extendedTokens: CSSProperties = {
  '--ppt-pixel-green': '#00FF41',
  '--ppt-pixel-cyan': '#00FFFF',
  '--ppt-pixel-pink': '#FF00FF',
  '--ppt-pixel-yellow': '#FFFF00',
  '--ppt-bg-dark': '#0D0D0D'
}

export default function Slide_%(index)d() {
  const preset = getDeckStylePreset('aurora-borealis')
  const baseVars = styleVars(preset)

  return (
    <div
      className="w-[1920px] h-[1080px] bg-[var(--ppt-bg-dark)] relative overflow-hidden"
      style={{ ...baseVars, ...extendedTokens } as CSSProperties}
      data-ppt-slide="%(index)d"
    >
      <div className="absolute inset-x-0 inset-y-0 opacity-10" style={{ backgroundImage: 'radial-gradient(#00FF41 1px, transparent 1px)', backgroundSize: '16px 16px' }} />
      <div className="p-20 relative z-10 w-full h-full flex flex-col justify-center items-center">
        {/* IMPORTANT SHADOW WRAPPER PATTERN */}
        <div data-ppt-bg="true" className="p-16 -m-16">
          <div className="bg-black border-4 border-[#00FFFF] shadow-[0_0_40px_#00FFFF] p-12">
            <h1 data-ppt-text="true" className="text-6xl text-[#00FFFF] font-bold">%(title)s</h1>
            <p data-ppt-text="true" className="text-3xl text-white mt-8 opacity-70">%(notes)s</p>
          </div>
        </div>
      </div>
    </div>
  )
}
"""

index_lines = []
export_lines = []

for s in outline["slides"]:
    idx = s["index"]
    title = s["title"].replace('"', '\\"')
    notes = s.get("notes", "").replace('"', '\\"')

    with open(f"{slides_dir}/Slide_{idx}.tsx", "w") as f:
        f.write(slide_template % {"index": idx, "title": title, "notes": notes})

    index_lines.append(f"import Slide_{idx} from './Slide_{idx}'")
    export_lines.append(f"Slide_{idx}")

with open(f"{slides_dir}/index.ts", "w") as f:
    f.write("\n".join(index_lines) + "\n\nexport default [" + ", ".join(export_lines) + "]\n")

print("Generated all React components successfully!")
