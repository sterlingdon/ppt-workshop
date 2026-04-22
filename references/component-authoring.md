# Component Authoring Reference

Use this when writing React slide components. Build rich visuals, but keep repeatable units isolatable.

## List Recipe

```tsx
<div data-ppt-group="list" className="space-y-5">
  {items.map((item) => (
    <div data-ppt-item key={item.id} className="p-8 -m-8">
      <div className="relative flex gap-5 rounded-3xl p-6">
        <div data-ppt-item-bg className="absolute inset-0 rounded-3xl bg-white/10 shadow-2xl" />
        <img data-ppt-bullet src={item.icon} className="relative z-10 h-12 w-12" alt="" />
        <div className="relative z-10">
          <h3 data-ppt-text>{item.title}</h3>
          <p data-ppt-text>{item.body}</p>
        </div>
      </div>
    </div>
  ))}
</div>
```

## Timeline Recipe

```tsx
<div data-ppt-group="timeline" className="relative">
  <div data-ppt-track className="absolute left-0 right-0 top-1/2 h-1 rounded-full bg-white/20" />
  {items.map((item, index) => (
    <div data-ppt-item key={item.id} className="relative">
      {index > 0 && <div data-ppt-segment className="absolute -left-12 top-1/2 h-1 w-12 bg-white/40" />}
      <div data-ppt-bullet data-ppt-node className="h-8 w-8 rounded-full bg-white shadow-xl" />
      <h3 data-ppt-text>{item.title}</h3>
      <p data-ppt-text>{item.body}</p>
    </div>
  ))}
</div>
```

## Card Grid Recipe

```tsx
<div data-ppt-group="card-grid" className="grid grid-cols-3 gap-6">
  {cards.map((card) => (
    <div data-ppt-item key={card.id} className="p-8 -m-8">
      <article className="relative rounded-3xl p-8">
        <div data-ppt-item-bg className="absolute inset-0 rounded-3xl bg-white/10 shadow-2xl" />
        <img data-ppt-bullet src={card.iconSrc} alt="" />
        <h3 data-ppt-text>{card.title}</h3>
        <p data-ppt-text>{card.body}</p>
      </article>
    </div>
  ))}
</div>
```

## Detail Label Recipe

Use this for kicker labels, chart tags, badges, and small decorative labels whose exact CSS treatment matters more than text editability.

```tsx
function Kicker({ children }: { children: React.ReactNode }) {
  return (
    <div data-ppt-bg className="inline-flex items-center gap-3 rounded-full border border-white/15 bg-white/5 px-5 py-2 text-sm font-bold uppercase tracking-[0.32em] text-cyan-300">
      <span className="h-2 w-2 rounded-full bg-cyan-300 shadow-[0_0_18px_#22d3ee]" />
      <span data-ppt-text data-ppt-native-text="skip">{children}</span>
    </div>
  )
}
```

Do not export these labels as native PPT text unless the styling is plain. Letter spacing, glow, clipped gradients, blend modes, and tiny uppercase text are usually better kept inside the local raster.

## Authoring Checklist

- Every repeatable structure uses `data-ppt-group`.
- Every repeatable unit uses `data-ppt-item`.
- Item text is nested inside the item.
- Parent background contains only shared atmosphere or tracks.
- Complex labels use `data-ppt-bg` plus `data-ppt-native-text="skip"` on inner text.
- Visual richness is not reduced for editability.
