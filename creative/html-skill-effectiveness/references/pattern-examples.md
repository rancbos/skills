# Pattern Examples

Real code snippets extracted from the reference collection, organized by pattern.

**Skill**: html-effectiveness by [Yardon](https://github.com/YardonYan) | May 2026
**Based on**: [The Unreasonable Effectiveness of HTML](https://github.com/ThariqS/html-effectiveness)

## 1. Side-by-Side Comparison

Three approaches in a grid:

```css
.approaches {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 28px;
}
@media (max-width: 1100px) {
  .approaches { grid-template-columns: 1fr; }
}
.approach {
  background: var(--white);
  border: 1.5px solid var(--gray-300);
  border-radius: 14px;
  padding: 24px;
  display: flex;
  flex-direction: column;
}
.approach.recommended {
  border-color: var(--slate);
  box-shadow: 0 8px 24px rgba(20,20,19,.08);
}
```

Trade-off tags:

```css
.tag {
  font-family: var(--mono);
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 999px;
  background: var(--gray-100);
  color: var(--gray-700);
}
.tag.pro { background: #E8F0E0; color: var(--olive); }
.tag.con { background: #F5E8E4; color: var(--rust); }
```

## 2. Annotated Diff

Diff block with margin notes:

```css
.diff-block {
  background: var(--white);
  border: 1.5px solid var(--gray-300);
  border-radius: 12px;
  overflow: hidden;
}
.diff-line {
  display: flex;
  font-family: var(--mono);
  font-size: 13px;
  line-height: 1.6;
  padding: 2px 16px;
}
.diff-line.add {
  background: #F0F7EC;
  border-left: 3px solid var(--olive);
}
.diff-line.del {
  background: #FDF2F0;
  border-left: 3px solid var(--rust);
}
```

## 5. Slide Deck

Scroll-snap slides:

```css
body {
  scroll-snap-type: y mandatory;
  overflow-x: hidden;
}
.slide {
  width: 100vw;
  height: 100vh;
  scroll-snap-align: start;
  scroll-snap-stop: always;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8vh 6vw;
}
.slide.invert {
  background: var(--slate);
  color: var(--ivory);
}
```

## 6. Interactive Explainer

Collapsible sections:

```css
details.deep-dive {
  border: 1.5px solid var(--gray-300);
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 12px;
}
details.deep-dive summary {
  font-weight: 500;
  cursor: pointer;
  list-style: none;
}
details.deep-dive summary::before {
  content: "▸";
  margin-right: 8px;
  color: var(--clay);
  display: inline-block;
  transition: transform 150ms;
}
details[open] summary::before {
  transform: rotate(90deg);
}
```

## 7. Status Report

Health pills:

```css
.health {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: var(--mono);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 4px 10px;
  border-radius: 999px;
}
.health::before {
  content: "";
  width: 6px; height: 6px;
  border-radius: 50%;
}
.health.on-track { background: #E8F0E0; color: var(--olive); }
.health.on-track::before { background: var(--olive); }
.health.at-risk { background: #F5E8E4; color: var(--clay-d); }
.health.at-risk::before { background: var(--clay); }
.health.blocked { background: #F5E8E4; color: var(--rust); }
.health.blocked::before { background: var(--rust); }
```

## 11. Dashboard

Metric card with sparkline:

```css
.metric {
  background: var(--white);
  border: var(--border);
  border-radius: var(--radius-panel);
  padding: 24px;
}
.metric .value {
  font-family: var(--serif);
  font-size: 42px;
  font-weight: 500;
  color: var(--slate);
  letter-spacing: -0.02em;
}
.metric .delta {
  font-family: var(--mono);
  font-size: 13px;
}
.metric .delta.up { color: var(--olive); }
.metric .delta.down { color: var(--rust); }
```

## 12. Live Artifact / Refreshable Dashboard

Data injection with template binding:

```javascript
const data = {
  revenue: { label: "Monthly Revenue", value: "$128,430", delta: "+12.4%", trend: "up" },
  users: { label: "Active Users", value: "8,249", delta: "+3.2%", trend: "up" },
  churn: { label: "Churn Rate", value: "2.1%", delta: "-0.3%", trend: "down" }
};

document.querySelectorAll('[data-bind]').forEach(el => {
  const path = el.dataset.bind.split('.');
  let val = data;
  path.forEach(k => val = val[k]);
  if (el.classList.contains('delta')) {
    el.className = `delta ${data[path[0]].trend}`;
  }
  el.textContent = val;
});
```

## 13. Frame Effects

Glitch Title Effect:

```css
@keyframes glitch-1 {
  0%, 100% { clip-path: inset(0 0 0 0); transform: translate(0); }
  20% { clip-path: inset(20% 0 60% 0); transform: translate(-3px, 2px); }
  40% { clip-path: inset(40% 0 40% 0); transform: translate(3px, -1px); }
  60% { clip-path: inset(60% 0 20% 0); transform: translate(-2px, 1px); }
  80% { clip-path: inset(10% 0 70% 0); transform: translate(2px, -2px); }
}
.glitch-title {
  position: relative;
  font-family: var(--serif);
  font-size: clamp(48px, 8vw, 96px);
  font-weight: 700;
}
.glitch-title::before,
.glitch-title::after {
  content: attr(data-text);
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
}
.glitch-title::before {
  color: #ff6b6b;
  z-index: -1;
  animation: glitch-1 3s infinite linear alternate-reverse;
}
.glitch-title::after {
  color: #4ecdc4;
  z-index: -2;
  animation: glitch-2 2.5s infinite linear alternate-reverse;
}
```

Liquid Background Hero:

```css
@keyframes liquid-morph {
  0%, 100% { border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%; }
  25% { border-radius: 30% 60% 70% 40% / 50% 60% 30% 60%; }
  50% { border-radius: 50% 50% 50% 70% / 50% 40% 70% 60%; }
  75% { border-radius: 40% 60% 30% 50% / 70% 40% 60% 50%; }
}
.liquid-bg::before {
  content: '';
  position: absolute;
  width: 140%;
  height: 140%;
  top: -20%;
  left: -20%;
  background: linear-gradient(135deg, var(--accent), var(--olive), var(--oat));
  opacity: 0.15;
  animation: liquid-morph 8s ease-in-out infinite;
  z-index: 0;
}
```

Entry Animation Utilities:

```css
.anim-fade-up {
  opacity: 0;
  transform: translateY(24px);
  animation: fade-up 0.6s cubic-bezier(0.23, 1, 0.32, 1) forwards;
}
@keyframes fade-up {
  to { opacity: 1; transform: translateY(0); }
}
.anim-stagger > * {
  opacity: 0;
  animation: fade-up 0.5s cubic-bezier(0.23, 1, 0.32, 1) forwards;
}
.anim-stagger > *:nth-child(1) { animation-delay: 0s; }
.anim-stagger > *:nth-child(2) { animation-delay: 0.1s; }
.anim-stagger > *:nth-child(3) { animation-delay: 0.2s; }
.anim-stagger > *:nth-child(4) { animation-delay: 0.3s; }
.anim-stagger > *:nth-child(5) { animation-delay: 0.4s; }
```
