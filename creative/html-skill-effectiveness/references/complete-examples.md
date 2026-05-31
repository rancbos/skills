# Complete Examples

Full HTML files demonstrating each pattern in context.

**Skill**: html-effectiveness by [Yardon](https://github.com/YardonYan) | May 2026
**Based on**: [The Unreasonable Effectiveness of HTML](https://github.com/ThariqS/html-effectiveness)

## Example 1: Side-by-Side Comparison

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Code Approaches Comparison</title>
<style>
:root {
  --accent: #E8654A;
  --fg: #141413;
  --bg: #FEFDFB;
  --muted: #8A8A86;
  --serif: 'Playfair Display', Georgia, serif;
  --mono: 'JetBrains Mono', monospace;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: system-ui, sans-serif; background: var(--bg); color: var(--fg); }
.approaches {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 28px;
  max-width: 1180px;
  margin: 0 auto;
  padding: 40px 24px;
}
@media (max-width: 1100px) {
  .approaches { grid-template-columns: 1fr; }
}
.approach {
  background: #fff;
  border: 1.5px solid #ddd;
  border-radius: 14px;
  padding: 24px;
}
.approach.recommended {
  border-color: var(--fg);
  box-shadow: 0 8px 24px rgba(20,20,19,.08);
}
.tag {
  font-family: var(--mono);
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 999px;
  background: #f5f5f5;
  color: #666;
}
.tag.pro { background: #E8F0E0; color: #4a7c3f; }
.tag.con { background: #F5E8E4; color: #c44; }
</style>
</head>
<body>
<h1>Code Approaches</h1>
<p>Three ways to structure the same feature</p>
<div class="approaches">
  <div class="approach">
    <h3>Client-side Render</h3>
    <ul><li>Fast navigation</li><li>Rich interactions</li></ul>
    <ul><li>Slow first paint</li><li>Poor SEO</li></ul>
    <span class="tag">Good for apps</span>
    <span class="tag pro">Recommended</span>
  </div>
  <div class="approach">
    <h3>Static Generation</h3>
    <ul><li>Fast load</li><li>Great SEO</li><li>Low cost</li></ul>
    <ul><li>Build time</li></ul>
    <span class="tag">Good for content</span>
  </div>
  <div class="approach">
    <h3>Server Components</h3>
    <ul><li>Best of both</li><li>Streaming</li></ul>
    <ul><li>Complex setup</li><li>Framework lock</li></ul>
    <span class="tag con">Complex</span>
  </div>
</div>
</body>
</html>
```

## Example 2: Status Report

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Status Report</title>
<style>
:root {
  --accent: #E8654A;
  --fg: #141413;
  --bg: #FEFDFB;
  --muted: #8A8A86;
  --serif: 'Playfair Display', Georgia, serif;
  --mono: 'JetBrains Mono', monospace;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: system-ui, sans-serif; background: var(--bg); color: var(--fg); }
.container { max-width: 860px; margin: 0 auto; padding: 40px 24px; }
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
.health.on-track { background: #E8F0E0; color: #4a7c3f; }
.health.on-track::before { background: #4a7c3f; }
</style>
</head>
<body>
<div class="container">
  <h1>Project Status</h1>
  <span class="health on-track">On Track</span>
</div>
</body>
</html>
```

## Example 3: Dashboard

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dashboard</title>
<style>
:root {
  --accent: #E8654A;
  --fg: #141413;
  --bg: #FEFDFB;
  --muted: #8A8A86;
  --serif: 'Playfair Display', Georgia, serif;
  --mono: 'JetBrains Mono', monospace;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: system-ui, sans-serif; background: var(--bg); color: var(--fg); }
.dashboard {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  max-width: 1180px;
  margin: 0 auto;
  padding: 40px 24px;
}
@media (max-width: 920px) {
  .dashboard { grid-template-columns: repeat(2, 1fr); }
}
.metric {
  background: #fff;
  border: 1.5px solid #ddd;
  border-radius: 14px;
  padding: 24px;
}
.metric .value {
  font-family: var(--serif);
  font-size: 42px;
  font-weight: 500;
  color: var(--fg);
  letter-spacing: -0.02em;
}
.metric .delta {
  font-family: var(--mono);
  font-size: 13px;
}
.metric .delta.up { color: #4a7c3f; }
.metric .delta.down { color: #c44; }
</style>
</head>
<body>
<div class="dashboard">
  <div class="metric">
    <div class="value">12.5K</div>
    <div class="delta up">↑ 12%</div>
  </div>
</div>
</body>
</html>
```

## Example 4: Glitch Hero (Frame Effect)

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Glitch Hero</title>
<style>
:root {
  --accent: #E8654A;
  --fg: #141413;
  --bg: #FEFDFB;
  --muted: #8A8A86;
  --serif: 'Playfair Display', Georgia, serif;
  --mono: 'JetBrains Mono', monospace;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: system-ui, sans-serif; background: var(--bg); color: var(--fg); }
.hero {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 40px;
}
@keyframes glitch-1 {
  0%, 100% { clip-path: inset(0 0 0 0); transform: translate(0); }
  20% { clip-path: inset(20% 0 60% 0); transform: translate(-3px, 2px); }
  40% { clip-path: inset(40% 0 40% 0); transform: translate(3px, -1px); }
  60% { clip-path: inset(60% 0 20% 0); transform: translate(-2px, 1px); }
  80% { clip-path: inset(10% 0 70% 0); transform: translate(2px, -2px); }
}
@keyframes glitch-2 {
  0%, 100% { clip-path: inset(0 0 0 0); transform: translate(0); }
  25% { clip-path: inset(35% 0 45% 0); transform: translate(2px, -2px); }
  55% { clip-path: inset(55% 0 25% 0); transform: translate(-2px, 1px); }
  85% { clip-path: inset(15% 0 65% 0); transform: translate(3px, -1px); }
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
</style>
</head>
<body>
<div class="hero">
  <p style="font-family:var(--mono);font-size:12px;text-transform:uppercase;letter-spacing:0.1em;color:var(--muted)">Creative Technology</p>
  <h1 class="glitch-title" data-text="BREAK THROUGH">BREAK THROUGH</h1>
  <p style="max-width:60ch;margin-top:24px;font-size:18px;color:var(--muted)">Where design meets engineering. We craft digital experiences that push boundaries.</p>
</div>
</body>
</html>
```
