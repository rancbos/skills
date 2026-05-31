# Frame Effects Reference

CSS-only animation techniques for cinematic presentation moments.

## Glitch Title Effect

Creates a cyberpunk-style glitch on text using `clip-path` and `transform`.

```css
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
```

**Usage**: Add `data-text` attribute with the same text content.

```html
<h1 class="glitch-title" data-text="BREAK THROUGH">BREAK THROUGH</h1>
```

## Liquid Background Hero

Organic morphing blob background.

```css
@keyframes liquid-morph {
  0%, 100% { border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%; }
  25% { border-radius: 30% 60% 70% 40% / 50% 60% 30% 60%; }
  50% { border-radius: 50% 50% 50% 70% / 50% 40% 70% 60%; }
  75% { border-radius: 40% 60% 30% 50% / 70% 40% 60% 50%; }
}

.liquid-bg {
  position: relative;
  overflow: hidden;
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

## Light Leak Cinema Effect

Subtle cinematic light leak overlay.

```css
@keyframes light-leak {
  0%, 90%, 100% { opacity: 0; }
  95% { opacity: 0.08; }
}

.cinema-frame {
  position: relative;
}

.cinema-frame::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    135deg,
    transparent 40%,
    rgba(255, 200, 100, 0.15) 50%,
    transparent 60%
  );
  pointer-events: none;
  animation: light-leak 6s ease-in-out infinite;
}
```

## Entry Animation Utilities

Fade-up entrance with stagger support.

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

## Logo Outro

Reveal animation for logos.

```css
@keyframes logo-reveal {
  0% { clip-path: inset(0 100% 0 0); opacity: 0; }
  50% { clip-path: inset(0 0 0 0); opacity: 1; }
  100% { clip-path: inset(0 0 0 0); opacity: 1; }
}

.logo-outro {
  animation: logo-reveal 1.2s cubic-bezier(0.23, 1, 0.32, 1) forwards;
}
```

## Rules

- Max one Frame Effect per page
- Use sparingly — one dramatic moment beats three mediocre ones
- Test on low-end devices — some effects may cause jank
- Provide `prefers-reduced-motion` fallback:

```css
@media (prefers-reduced-motion: reduce) {
  .glitch-title::before,
  .glitch-title::after {
    animation: none;
  }
  .liquid-bg::before {
    animation: none;
  }
  .cinema-frame::after {
    animation: none;
  }
  .anim-fade-up,
  .anim-stagger > * {
    animation: none;
    opacity: 1;
    transform: none;
  }
}
```
