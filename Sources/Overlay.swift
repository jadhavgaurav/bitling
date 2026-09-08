// A full-screen, click-through stage for the pet's effects.
//
// The pet lives in a small window, which crops anything dramatic. This overlay sits above
// the desktop across the whole screen and draws the things that need room: beetles that
// crawl over your other apps, the laser beams that vaporise them, scorch marks, and the
// rocket that launches on a push.
//
// It never accepts a click (`ignoresMouseEvents`), so it cannot steal input from whatever
// you are working in, and it hides itself entirely whenever there is nothing to draw.

import Cocoa

struct Beetle {
    let id: Int
    var x: CGFloat            // screen coordinates, origin bottom left
    var y: CGFloat
    var vx: CGFloat
    var dart: CGFloat
    var wiggle: CGFloat
    var label: String
    var boss: Bool
    var hp: Int
    var maxHP: Int
    var persistent = false    // a test-backed beetle: it stays until that test passes
    var doomed = false        // the test was fixed, so the pet may now shoot it
    var dead = false          // set once, never unset: a corpse must not become a target again
    var dying: CGFloat        // counts down while the corpse fades
    var born: Date

    var size: CGFloat { boss ? 20 : 11 }
    var alive: Bool { !dead }
}

private struct Beam {
    var from: CGPoint
    var to: CGPoint
    var life: CGFloat
    var style: String = "beam"      // how the current species kills a bug
}

private struct Scorch {
    var at: CGPoint
    var life: CGFloat
    var big: Bool
}

private struct OverlayRocket {
    var x: CGFloat
    var y: CGFloat
    var vy: CGFloat
    var wobble: CGFloat
    var label: String
}

final class OverlayView: NSView {
    var beetles: [Beetle] = []
    fileprivate var beams: [Beam] = []
    fileprivate var scorches: [Scorch] = []
    fileprivate var rocket: OverlayRocket?

    override var isFlipped: Bool { false }
    override func hitTest(_ point: NSPoint) -> NSView? { nil }

    /// Fills the view with one of each entity so the drawing can be checked offscreen.
    /// Used by Tools/renderoverlay.swift; the app never calls it.
    func loadDemoScene() {
        let h = bounds.height, floor = h * 0.22
        beetles = [
            Beetle(id: 1, x: bounds.width * 0.16, y: floor, vx: 70, dart: 1, wiggle: 0.7,
                   label: "test_webhook_signature", boss: false, hp: 1, maxHP: 1, dead: false, dying: 0, born: Date()),
            Beetle(id: 2, x: bounds.width * 0.42, y: floor, vx: -70, dart: 1, wiggle: 2.1,
                   label: "test_invoice_total", boss: false, hp: 1, maxHP: 1, dead: false, dying: 0, born: Date()),
            Beetle(id: 3, x: bounds.width * 0.72, y: floor, vx: 30, dart: 1, wiggle: 0.2,
                   label: "the suite", boss: true, hp: 5, maxHP: 8, dead: false, dying: 0, born: Date()),
            Beetle(id: 4, x: bounds.width * 0.56, y: floor, vx: 0, dart: 1, wiggle: 0,
                   label: "", boss: false, hp: 0, maxHP: 1, dead: true, dying: 0.4, born: Date()),
        ]
        let eyes = CGPoint(x: bounds.width * 0.5, y: floor + 120)
        beams = [
            Beam(from: CGPoint(x: eyes.x - 14, y: eyes.y), to: CGPoint(x: bounds.width * 0.16, y: floor + 7), life: 0.16),
            Beam(from: CGPoint(x: eyes.x + 14, y: eyes.y), to: CGPoint(x: bounds.width * 0.16, y: floor + 7), life: 0.16),
        ]
        scorches = [Scorch(at: CGPoint(x: bounds.width * 0.56, y: floor), life: 2.0, big: false)]
        rocket = OverlayRocket(x: bounds.width * 0.86, y: h * 0.55, vy: 200, wobble: 0.4, label: "shipped main!")
    }

    override func draw(_ dirtyRect: NSRect) {
        guard let ctx = NSGraphicsContext.current?.cgContext else { return }
        ctx.setShouldAntialias(true)
        for s in scorches { drawScorch(ctx, s) }
        for b in beetles { drawBeetle(ctx, b) }
        for b in beams { drawBeam(ctx, b) }
        if let r = rocket { drawRocket(ctx, r) }
    }

    // MARK: drawing

    private func drawScorch(_ ctx: CGContext, _ s: Scorch) {
        let a = max(0, min(1, s.life / 2.5))
        let r: CGFloat = s.big ? 26 : 15
        ctx.setFillColor(NSColor(calibratedWhite: 0.05, alpha: 0.32 * a).cgColor)
        ctx.fillEllipse(in: CGRect(x: s.at.x - r, y: s.at.y - r * 0.32, width: r * 2, height: r * 0.64))
    }

    private func drawBeam(_ ctx: CGContext, _ b: Beam) {
        if b.style == "thunderbolt" { drawThunderbolt(ctx, b); return }
        if b.style == "electroball" { drawElectroBall(ctx, b); return }
        if b.style == "kamehameha" { drawKamehameha(ctx, b); return }
        if b.style == "kiball" || b.style == "energyball" { drawEnergyBall(ctx, b); return }
        if b.style == "flame" { drawFlame(ctx, b, spread: 1); return }
        if b.style == "blaze" { drawFlame(ctx, b, spread: 1.9); return }
        if b.style == "atomic" { drawAtomicBreath(ctx, b); return }
        if b.style == "blast" { drawBlast(ctx, b); return }
        if b.style == "unibeam" { drawUnibeam(ctx, b); return }
        if b.style == "repulsor" { drawRepulsor(ctx, b); return }
        let k = max(0, min(1, b.life / 0.2))
        ctx.saveGState()
        ctx.setBlendMode(.plusLighter)
        ctx.setLineCap(.round)
        ctx.setStrokeColor(NSColor(calibratedRed: 1, green: 0.16, blue: 0.16, alpha: 0.8 * k).cgColor)
        ctx.setLineWidth(7 * k)
        ctx.move(to: b.from); ctx.addLine(to: b.to); ctx.strokePath()
        ctx.setStrokeColor(NSColor(calibratedRed: 1, green: 0.92, blue: 0.88, alpha: 0.95 * k).cgColor)
        ctx.setLineWidth(2.4 * k)
        ctx.move(to: b.from); ctx.addLine(to: b.to); ctx.strokePath()
        let flash = 13 * (1.25 - k)
        ctx.setFillColor(NSColor(calibratedRed: 1, green: 0.72, blue: 0.35, alpha: 0.85 * k).cgColor)
        ctx.fillEllipse(in: CGRect(x: b.to.x - flash, y: b.to.y - flash, width: flash * 2, height: flash * 2))
        ctx.restoreGState()
    }

    /// Godzilla's narrow ionized stream, shared in color and silhouette with its Canvas muzzle.
    private func drawAtomicBreath(_ ctx: CGContext, _ beam: Beam) {
        let strength = max(0, min(1, beam.life / 0.2))
        let dx = beam.to.x - beam.from.x, dy = beam.to.y - beam.from.y
        let length = hypot(dx, dy)
        ctx.saveGState()
        ctx.setBlendMode(.plusLighter)
        ctx.translateBy(x: beam.from.x, y: beam.from.y)
        ctx.rotate(by: atan2(dy, dx))
        let layers: [(CGFloat, NSColor)] = [
            (12, NSColor(calibratedRed: 0.09, green: 0.29, blue: 1, alpha: 0.25 * strength)),
            (8, NSColor(calibratedRed: 0, green: 0.92, blue: 1, alpha: 0.65 * strength)),
            (3.5, NSColor(calibratedRed: 0.84, green: 1, blue: 1, alpha: 0.95 * strength)),
        ]
        for (width, color) in layers {
            ctx.setFillColor(color.cgColor)
            ctx.setShadow(offset: .zero, blur: width, color: color.cgColor)
            ctx.beginPath()
            ctx.move(to: CGPoint(x: 0, y: -width * 0.32))
            for index in 1...12 {
                let ripple = 1 + sin(CGFloat(index) * 2.3 - strength * 4.8) * 0.22
                ctx.addLine(to: CGPoint(x: length * CGFloat(index) / 12, y: -width * ripple))
            }
            for index in stride(from: 12, through: 1, by: -1) {
                let ripple = 1 + sin(CGFloat(index) * 2.3 + strength * 4.8) * 0.22
                ctx.addLine(to: CGPoint(x: length * CGFloat(index) / 12, y: width * ripple))
            }
            ctx.addLine(to: CGPoint(x: 0, y: width * 0.32))
            ctx.closePath()
            ctx.fillPath()
        }
        ctx.restoreGState()
    }

    /// DBZ Kamehameha wave: massive azure ki aura, surging cyan beam with electric ripples,
    /// intense white-hot core, giant muzzle bloom at the palms, and an explosive spherical impact burst.
    private func drawKamehameha(_ ctx: CGContext, _ b: Beam) {
        let k = max(0, min(1, b.life / 0.25))
        let dx = b.to.x - b.from.x, dy = b.to.y - b.from.y
        let len = max(1, hypot(dx, dy))
        let angle = atan2(dy, dx)
        ctx.saveGState()
        ctx.setBlendMode(.plusLighter)
        ctx.translateBy(x: b.from.x, y: b.from.y)
        ctx.rotate(by: angle)

        // Outer fluctuating blue ki aura
        let w = 28 * (0.75 + k * 0.5)
        ctx.setFillColor(NSColor(calibratedRed: 0.2, green: 0.65, blue: 1.0, alpha: 0.45 * k).cgColor)
        ctx.fill(CGRect(x: 0, y: -w, width: len, height: w * 2))

        // Vibrant cyan plasma layer with subtle ripple effect
        let wMid = w * 0.62
        ctx.setFillColor(NSColor(calibratedRed: 0.45, green: 0.95, blue: 1.0, alpha: 0.8 * k).cgColor)
        ctx.beginPath()
        ctx.move(to: CGPoint(x: 0, y: -wMid))
        let steps = 14
        for i in 1...steps {
            let x = len * CGFloat(i) / CGFloat(steps)
            let rip = 1.0 + sin(CGFloat(i) * 2.8 + (1 - k) * 12) * 0.15
            ctx.addLine(to: CGPoint(x: x, y: -wMid * rip))
        }
        for i in stride(from: steps, through: 1, by: -1) {
            let x = len * CGFloat(i) / CGFloat(steps)
            let rip = 1.0 + sin(CGFloat(i) * 2.8 - (1 - k) * 12) * 0.15
            ctx.addLine(to: CGPoint(x: x, y: wMid * rip))
        }
        ctx.addLine(to: CGPoint(x: 0, y: wMid))
        ctx.closePath()
        ctx.fillPath()

        // Brilliant pure white laser-hot core
        let wCore = w * 0.26
        ctx.setFillColor(NSColor(white: 1.0, alpha: 0.98 * k).cgColor)
        ctx.fill(CGRect(x: 0, y: -wCore, width: len, height: wCore * 2))

        // Muzzle bloom at Goku's cupped palms
        let bloom = w * 2.4
        ctx.setFillColor(NSColor(calibratedRed: 0.55, green: 0.9, blue: 1.0, alpha: 0.85 * k).cgColor)
        ctx.fillEllipse(in: CGRect(x: -bloom, y: -bloom, width: bloom * 2, height: bloom * 2))
        ctx.setFillColor(NSColor(white: 1.0, alpha: 0.95 * k).cgColor)
        ctx.fillEllipse(in: CGRect(x: -bloom * 0.45, y: -bloom * 0.45, width: bloom * 0.9, height: bloom * 0.9))

        // Electric shock rings along the beam
        ctx.setStrokeColor(NSColor(calibratedRed: 0.8, green: 1.0, blue: 1.0, alpha: 0.7 * k).cgColor)
        ctx.setLineWidth(2.5)
        for i in 1...4 {
            let rx = len * (CGFloat(i) / 4.5)
            let rw = w * 0.9 * (1.1 - k * 0.2)
            ctx.strokeEllipse(in: CGRect(x: rx - rw * 0.35, y: -rw, width: rw * 0.7, height: rw * 2))
        }

        ctx.restoreGState()

        // Devastating impact burst at target
        let flash = 36 * (1.35 - k)
        ctx.saveGState()
        ctx.setBlendMode(.plusLighter)
        ctx.setFillColor(NSColor(calibratedRed: 0.4, green: 0.88, blue: 1.0, alpha: 0.85 * k).cgColor)
        ctx.fillEllipse(in: CGRect(x: b.to.x - flash, y: b.to.y - flash, width: flash * 2, height: flash * 2))
        ctx.setFillColor(NSColor(white: 1.0, alpha: 0.95 * k).cgColor)
        ctx.fillEllipse(in: CGRect(x: b.to.x - flash * 0.5, y: b.to.y - flash * 0.5, width: flash, height: flash))
        ctx.restoreGState()
    }

    /// Iron Man Chest Arc Reactor Unibeam: massive blinding cyan photon beam with white-hot core,
    /// concentric pulse rings, Arc Reactor muzzle bloom, and huge target impact shockwave.
    private func drawUnibeam(_ ctx: CGContext, _ b: Beam) {
        let k = max(0, min(1, b.life / 0.30))
        let dx = b.to.x - b.from.x, dy = b.to.y - b.from.y
        let len = max(1, hypot(dx, dy))
        let angle = atan2(dy, dx)
        ctx.saveGState()
        ctx.setBlendMode(.plusLighter)
        ctx.translateBy(x: b.from.x, y: b.from.y)
        ctx.rotate(by: angle)

        // Outer fluctuating cyan plasma beam
        let w = 26 * (0.8 + k * 0.5)
        ctx.setFillColor(NSColor(calibratedRed: 0.0, green: 0.85, blue: 1.0, alpha: 0.55 * k).cgColor)
        ctx.fill(CGRect(x: 0, y: -w, width: len, height: w * 2))

        // Intense core white photon laser
        let wCore = w * 0.35
        ctx.setFillColor(NSColor(white: 1.0, alpha: 0.98 * k).cgColor)
        ctx.fill(CGRect(x: 0, y: -wCore, width: len, height: wCore * 2))

        // Arc Reactor muzzle bloom at chest
        let bloom = w * 2.2
        ctx.setFillColor(NSColor(calibratedRed: 0.0, green: 0.94, blue: 1.0, alpha: 0.9 * k).cgColor)
        ctx.fillEllipse(in: CGRect(x: -bloom, y: -bloom, width: bloom * 2, height: bloom * 2))
        ctx.setFillColor(NSColor(white: 1.0, alpha: 0.98 * k).cgColor)
        ctx.fillEllipse(in: CGRect(x: -bloom * 0.45, y: -bloom * 0.45, width: bloom * 0.9, height: bloom * 0.9))

        // Concentric high-tech pulse rings traveling along beam
        ctx.setStrokeColor(NSColor(calibratedRed: 0.7, green: 0.96, blue: 1.0, alpha: 0.85 * k).cgColor)
        ctx.setLineWidth(2.4)
        for i in 1...4 {
            let rx = len * (CGFloat(i) / 4.5)
            let rw = w * 0.85 * (1.1 - k * 0.2)
            ctx.strokeEllipse(in: CGRect(x: rx - rw * 0.35, y: -rw, width: rw * 0.7, height: rw * 2))
        }

        ctx.restoreGState()

        // Devastating spherical impact burst at target
        let flash = 34 * (1.35 - k)
        ctx.saveGState()
        ctx.setBlendMode(.plusLighter)
        ctx.setFillColor(NSColor(calibratedRed: 0.0, green: 0.9, blue: 1.0, alpha: 0.88 * k).cgColor)
        ctx.fillEllipse(in: CGRect(x: b.to.x - flash, y: b.to.y - flash, width: flash * 2, height: flash * 2))
        ctx.setFillColor(NSColor(white: 1.0, alpha: 0.98 * k).cgColor)
        ctx.fillEllipse(in: CGRect(x: b.to.x - flash * 0.5, y: b.to.y - flash * 0.5, width: flash, height: flash))
        ctx.restoreGState()
    }

    /// Iron Man Palm Repulsor Blast: focused high-velocity cyan particle ray,
    /// traveling plasma ring, palm muzzle flare, and electric impact spark burst.
    private func drawRepulsor(_ ctx: CGContext, _ b: Beam) {
        let k = max(0, min(1, b.life / 0.2))
        let dx = b.to.x - b.from.x, dy = b.to.y - b.from.y
        let len = max(1, hypot(dx, dy))
        let angle = atan2(dy, dx)
        ctx.saveGState()
        ctx.setBlendMode(.plusLighter)
        ctx.translateBy(x: b.from.x, y: b.from.y)
        ctx.rotate(by: angle)

        // Focused cyan repulsor ray
        ctx.setLineCap(.round)
        ctx.setStrokeColor(NSColor(calibratedRed: 0.0, green: 0.92, blue: 1.0, alpha: 0.92 * k).cgColor)
        ctx.setLineWidth(9 * k)
        ctx.move(to: .zero); ctx.addLine(to: CGPoint(x: len, y: 0)); ctx.strokePath()

        // Pure white core ray
        ctx.setStrokeColor(NSColor(white: 1.0, alpha: 0.98 * k).cgColor)
        ctx.setLineWidth(3 * k)
        ctx.move(to: .zero); ctx.addLine(to: CGPoint(x: len, y: 0)); ctx.strokePath()

        // Palm muzzle flare
        let flare: CGFloat = 16 * k
        ctx.setFillColor(NSColor(calibratedRed: 0.0, green: 0.94, blue: 1.0, alpha: 0.95 * k).cgColor)
        ctx.fillEllipse(in: CGRect(x: -flare, y: -flare, width: flare * 2, height: flare * 2))
        ctx.setFillColor(NSColor(white: 1.0, alpha: 0.98 * k).cgColor)
        ctx.fillEllipse(in: CGRect(x: -flare * 0.45, y: -flare * 0.45, width: flare * 0.9, height: flare * 0.9))

        // Traveling plasma ring
        let prog = CGFloat(1.0 - k)
        let ringX = len * (0.3 + 0.7 * prog)
        let ringR: CGFloat = 12 * (0.8 + 0.4 * k)
        ctx.setStrokeColor(NSColor(calibratedRed: 0.6, green: 0.96, blue: 1.0, alpha: 0.9 * k).cgColor)
        ctx.setLineWidth(2.0)
        ctx.strokeEllipse(in: CGRect(x: ringX - ringR * 0.4, y: -ringR, width: ringR * 0.8, height: ringR * 2))

        ctx.restoreGState()

        // Electric impact spark burst at target
        let flash = 20 * (1.25 - k)
        ctx.saveGState()
        ctx.setBlendMode(.plusLighter)
        ctx.setFillColor(NSColor(calibratedRed: 0.0, green: 0.9, blue: 1.0, alpha: 0.85 * k).cgColor)
        ctx.fillEllipse(in: CGRect(x: b.to.x - flash, y: b.to.y - flash, width: flash * 2, height: flash * 2))
        ctx.setFillColor(NSColor(white: 1.0, alpha: 0.95 * k).cgColor)
        ctx.fillEllipse(in: CGRect(x: b.to.x - flash * 0.45, y: b.to.y - flash * 0.45, width: flash * 0.9, height: flash * 0.9))
        ctx.restoreGState()
    }

    /// DBZ Ki Blast / Energy Ball: a fast, searing sphere of condensed ki flying across the screen,
    /// trailed by golden/cyan plasma flames and exploding on impact into bright ki sparks.
    private func drawEnergyBall(_ ctx: CGContext, _ b: Beam) {
        let k = max(0, min(1, b.life / 0.2))
        let prog = 1.0 - k // 0 to 1 as life drops
        let currX = b.from.x + (b.to.x - b.from.x) * prog
        let currY = b.from.y + (b.to.y - b.from.y) * prog
        let dx = b.to.x - b.from.x, dy = b.to.y - b.from.y
        let angle = atan2(dy, dx)

        ctx.saveGState()
        ctx.setBlendMode(.plusLighter)

        // Trailing ki streak behind the projectile
        let tailLen: CGFloat = 32
        let tx = currX - cos(angle) * tailLen
        let ty = currY - sin(angle) * tailLen
        ctx.setLineCap(.round)
        ctx.setStrokeColor(NSColor(calibratedRed: 1.0, green: 0.82, blue: 0.2, alpha: 0.6 * k).cgColor)
        ctx.setLineWidth(14)
        ctx.move(to: CGPoint(x: tx, y: ty)); ctx.addLine(to: CGPoint(x: currX, y: currY)); ctx.strokePath()

        ctx.setStrokeColor(NSColor(white: 1.0, alpha: 0.9 * k).cgColor)
        ctx.setLineWidth(6)
        ctx.move(to: CGPoint(x: tx * 0.5 + currX * 0.5, y: ty * 0.5 + currY * 0.5)); ctx.addLine(to: CGPoint(x: currX, y: currY)); ctx.strokePath()

        // Glowing outer ki orb
        let r: CGFloat = 16
        ctx.setFillColor(NSColor(calibratedRed: 1.0, green: 0.85, blue: 0.25, alpha: 0.75 * k).cgColor)
        ctx.fillEllipse(in: CGRect(x: currX - r, y: currY - r, width: r * 2, height: r * 2))

        // Electric cyan/gold halo ring
        let rAura = r * 1.5
        ctx.setFillColor(NSColor(calibratedRed: 0.35, green: 0.9, blue: 1.0, alpha: 0.45 * k).cgColor)
        ctx.fillEllipse(in: CGRect(x: currX - rAura, y: currY - rAura, width: rAura * 2, height: rAura * 2))

        // Incandescent white core
        let rCore: CGFloat = 8
        ctx.setFillColor(NSColor(white: 1.0, alpha: 0.98 * k).cgColor)
        ctx.fillEllipse(in: CGRect(x: currX - rCore, y: currY - rCore, width: rCore * 2, height: rCore * 2))

        // Impact explosion at the beetle
        if prog > 0.45 {
            let burstK = (prog - 0.45) / 0.55
            let burstR = 24 * burstK
            ctx.setFillColor(NSColor(calibratedRed: 1.0, green: 0.88, blue: 0.3, alpha: 0.9 * (1.0 - burstK)).cgColor)
            ctx.fillEllipse(in: CGRect(x: b.to.x - burstR, y: b.to.y - burstR, width: burstR * 2, height: burstR * 2))
            ctx.setFillColor(NSColor(white: 1.0, alpha: 0.95 * (1.0 - burstK)).cgColor)
            ctx.fillEllipse(in: CGRect(x: b.to.x - burstR * 0.5, y: b.to.y - burstR * 0.5, width: burstR, height: burstR))
        }

        ctx.restoreGState()
    }

    /// Pikachu's 100,000-Volt Thunderbolt: a multi-layered jagged lightning bolt crashing
    /// down from the sky directly onto the boss bug, triggering ground shockwaves and dancing electric arcs.
    private func drawThunderbolt(_ ctx: CGContext, _ b: Beam) {
        let k = max(0, min(1, b.life / 0.25))
        ctx.saveGState()
        ctx.setBlendMode(.plusLighter)

        let target = b.to
        let skyY: CGFloat = max(target.y + 700, 1000)
        let totalH = skyY - target.y
        let segs = 8

        // Deterministic pseudo-random jitter based on coordinates and life
        func jitter(_ idx: Int) -> CGFloat {
            let s = sin(Double(idx) * 4.3 + Double(b.life) * 40.0)
            return CGFloat(s) * 35.0
        }

        var points: [CGPoint] = []
        points.append(CGPoint(x: target.x + jitter(0) * 0.4, y: skyY))
        for i in 1..<segs {
            let frac = CGFloat(i) / CGFloat(segs)
            let py = skyY - totalH * frac
            let px = target.x + jitter(i) * (1.0 - frac * 0.5)
            points.append(CGPoint(x: px, y: py))
        }
        points.append(target)

        // 1. Broad outer golden-electric aura
        ctx.setLineCap(.round)
        ctx.setLineJoin(.round)
        ctx.setStrokeColor(NSColor(calibratedRed: 1.0, green: 0.85, blue: 0.1, alpha: 0.65 * k).cgColor)
        ctx.setLineWidth(24 * k)
        ctx.beginPath()
        ctx.move(to: points[0])
        for pt in points.dropFirst() { ctx.addLine(to: pt) }
        ctx.strokePath()

        // 2. High-voltage electric yellow sheath
        ctx.setStrokeColor(NSColor(calibratedRed: 1.0, green: 0.95, blue: 0.35, alpha: 0.88 * k).cgColor)
        ctx.setLineWidth(11 * k)
        ctx.beginPath()
        ctx.move(to: points[0])
        for pt in points.dropFirst() { ctx.addLine(to: pt) }
        ctx.strokePath()

        // 3. Blinding white-hot core
        ctx.setStrokeColor(NSColor(white: 1.0, alpha: 0.98 * k).cgColor)
        ctx.setLineWidth(3.8 * k)
        ctx.beginPath()
        ctx.move(to: points[0])
        for pt in points.dropFirst() { ctx.addLine(to: pt) }
        ctx.strokePath()

        // Secondary fork lightning
        if segs >= 5 {
            let forkStart = points[segs / 2]
            ctx.setStrokeColor(NSColor(calibratedRed: 1.0, green: 0.92, blue: 0.4, alpha: 0.75 * k).cgColor)
            ctx.setLineWidth(4.0 * k)
            ctx.beginPath()
            ctx.move(to: forkStart)
            ctx.addLine(to: CGPoint(x: forkStart.x + 42, y: forkStart.y - 30))
            ctx.addLine(to: CGPoint(x: forkStart.x + 65, y: forkStart.y - 50))
            ctx.strokePath()
        }

        // Ground shockwave impact ring
        let impactR = 48.0 * (1.4 - k * 0.4)
        ctx.setFillColor(NSColor(calibratedRed: 1.0, green: 0.9, blue: 0.2, alpha: 0.7 * k).cgColor)
        ctx.fillEllipse(in: CGRect(x: target.x - impactR, y: target.y - impactR * 0.45, width: impactR * 2, height: impactR * 0.9))
        ctx.setFillColor(NSColor(white: 1.0, alpha: 0.9 * k).cgColor)
        ctx.fillEllipse(in: CGRect(x: target.x - impactR * 0.45, y: target.y - impactR * 0.22, width: impactR * 0.9, height: impactR * 0.44))

        // Dancing electric ground arcs
        ctx.setStrokeColor(NSColor(white: 1.0, alpha: 0.85 * k).cgColor)
        ctx.setLineWidth(2.0)
        for a in 0..<6 {
            let ang = (Double(a) / 6.0) * .pi * 2
            let dist = impactR * (0.8 + 0.3 * sin(Double(a) * 2.1 + Double(b.life) * 25.0))
            ctx.beginPath()
            ctx.move(to: target)
            ctx.addLine(to: CGPoint(x: target.x + CGFloat(cos(ang)) * dist, y: target.y + CGFloat(sin(ang)) * dist * 0.4))
            ctx.strokePath()
        }

        ctx.restoreGState()
    }

    /// Pikachu's crackling Electro Ball: high-speed electric plasma sphere with trailing sparks.
    private func drawElectroBall(_ ctx: CGContext, _ b: Beam) {
        let k = max(0, min(1, b.life / 0.2))
        let prog = 1.0 - k
        let currX = b.from.x + (b.to.x - b.from.x) * prog
        let currY = b.from.y + (b.to.y - b.from.y) * prog
        let dx = b.to.x - b.from.x, dy = b.to.y - b.from.y
        let angle = atan2(dy, dx)

        ctx.saveGState()
        ctx.setBlendMode(.plusLighter)

        // Fast electric plasma trail
        let tailLen: CGFloat = 28
        let tx = currX - cos(angle) * tailLen
        let ty = currY - sin(angle) * tailLen
        ctx.setLineCap(.round)
        ctx.setStrokeColor(NSColor(calibratedRed: 1.0, green: 0.9, blue: 0.2, alpha: 0.7 * k).cgColor)
        ctx.setLineWidth(10 * k)
        ctx.move(to: CGPoint(x: tx, y: ty)); ctx.addLine(to: CGPoint(x: currX, y: currY)); ctx.strokePath()

        ctx.setStrokeColor(NSColor(white: 1.0, alpha: 0.95 * k).cgColor)
        ctx.setLineWidth(3.5 * k)
        ctx.move(to: CGPoint(x: tx * 0.4 + currX * 0.6, y: ty * 0.4 + currY * 0.6)); ctx.addLine(to: CGPoint(x: currX, y: currY)); ctx.strokePath()

        // Concentrated electric orb
        let r: CGFloat = 14
        ctx.setFillColor(NSColor(calibratedRed: 1.0, green: 0.92, blue: 0.1, alpha: 0.85 * k).cgColor)
        ctx.fillEllipse(in: CGRect(x: currX - r, y: currY - r, width: r * 2, height: r * 2))

        // Intense white core
        let rCore: CGFloat = 6.5
        ctx.setFillColor(NSColor(white: 1.0, alpha: 0.98 * k).cgColor)
        ctx.fillEllipse(in: CGRect(x: currX - rCore, y: currY - rCore, width: rCore * 2, height: rCore * 2))

        // Crackling electric arcs around ball
        ctx.setStrokeColor(NSColor(white: 1.0, alpha: 0.9 * k).cgColor)
        ctx.setLineWidth(1.6)
        for i in 0..<4 {
            let spAng = (Double(i) / 4.0) * .pi * 2 + Double(b.life) * 30.0
            let dist = r * 1.45
            ctx.beginPath()
            ctx.move(to: CGPoint(x: currX, y: currY))
            ctx.addLine(to: CGPoint(x: currX + CGFloat(cos(spAng)) * dist, y: currY + CGFloat(sin(spAng)) * dist))
            ctx.strokePath()
        }

        // Impact spark explosion at the bug
        if prog > 0.4 {
            let burstK = (prog - 0.4) / 0.6
            let burstR = 26 * burstK
            ctx.setFillColor(NSColor(calibratedRed: 1.0, green: 0.9, blue: 0.25, alpha: 0.9 * (1.0 - burstK)).cgColor)
            ctx.fillEllipse(in: CGRect(x: b.to.x - burstR, y: b.to.y - burstR, width: burstR * 2, height: burstR * 2))
            ctx.setFillColor(NSColor(white: 1.0, alpha: 0.98 * (1.0 - burstK)).cgColor)
            ctx.fillEllipse(in: CGRect(x: b.to.x - burstR * 0.45, y: b.to.y - burstR * 0.45, width: burstR * 0.9, height: burstR * 0.9))
        }

        ctx.restoreGState()
    }

    /// A two handed energy beam: a wide soft bar with a hard white core, a bloom at the
    /// hands and a burst where it lands.
    private func drawBlast(_ ctx: CGContext, _ b: Beam) {
        let k = max(0, min(1, b.life / 0.2))
        let dx = b.to.x - b.from.x, dy = b.to.y - b.from.y
        let len = max(1, hypot(dx, dy))
        let angle = atan2(dy, dx)
        ctx.saveGState()
        ctx.setBlendMode(.plusLighter)
        ctx.translateBy(x: b.from.x, y: b.from.y)
        ctx.rotate(by: angle)
        let width = 17 * (0.65 + k * 0.55)
        ctx.setFillColor(NSColor(calibratedRed: 0.55, green: 0.92, blue: 1, alpha: 0.55 * k).cgColor)
        ctx.fill(CGRect(x: 0, y: -width, width: len, height: width * 2))
        ctx.setFillColor(NSColor(calibratedRed: 0.85, green: 0.99, blue: 1, alpha: 0.75 * k).cgColor)
        ctx.fill(CGRect(x: 0, y: -width * 0.55, width: len, height: width * 1.1))
        ctx.setFillColor(NSColor(white: 1, alpha: 0.95 * k).cgColor)
        ctx.fill(CGRect(x: 0, y: -width * 0.22, width: len, height: width * 0.44))
        let bloom = width * 1.9
        ctx.setFillColor(NSColor(calibratedRed: 0.7, green: 0.96, blue: 1, alpha: 0.7 * k).cgColor)
        ctx.fillEllipse(in: CGRect(x: -bloom, y: -bloom, width: bloom * 2, height: bloom * 2))
        ctx.restoreGState()
        let flash = 20 * (1.3 - k)
        ctx.saveGState()
        ctx.setBlendMode(.plusLighter)
        ctx.setFillColor(NSColor(calibratedRed: 0.85, green: 0.99, blue: 1, alpha: 0.9 * k).cgColor)
        ctx.fillEllipse(in: CGRect(x: b.to.x - flash, y: b.to.y - flash, width: flash * 2, height: flash * 2))
        ctx.restoreGState()
    }

    /// A breath of fire: a widening cone rather than a straight line, three layers
    /// from a dull red edge to a white core.
    private func drawFlame(_ ctx: CGContext, _ b: Beam, spread multiplier: CGFloat) {
        let k = max(0, min(1, b.life / 0.2))
        let dx = b.to.x - b.from.x, dy = b.to.y - b.from.y
        let len = max(1, hypot(dx, dy))
        let nx = -dy / len, ny = dx / len
        ctx.saveGState()
        ctx.setBlendMode(.plusLighter)
        let layers: [(CGFloat, NSColor)] = [
            (30, NSColor(calibratedRed: 1, green: 0.30, blue: 0.04, alpha: 0.40 * k)),
            (18, NSColor(calibratedRed: 1, green: 0.60, blue: 0.14, alpha: 0.58 * k)),
            (8, NSColor(calibratedRed: 1, green: 0.95, blue: 0.76, alpha: 0.92 * k)),
        ]
        for (width, colour) in layers {
            let spread = width * multiplier * (1.3 - k * 0.5)
            let midX = b.from.x + dx * 0.45, midY = b.from.y + dy * 0.45
            ctx.setFillColor(colour.cgColor)
            ctx.beginPath()
            ctx.move(to: b.from)
            ctx.addQuadCurve(
                to: CGPoint(x: b.to.x + nx * spread * 0.5, y: b.to.y + ny * spread * 0.5),
                control: CGPoint(x: midX + nx * spread, y: midY + ny * spread)
            )
            ctx.addLine(to: CGPoint(x: b.to.x - nx * spread * 0.5, y: b.to.y - ny * spread * 0.5))
            ctx.addQuadCurve(to: b.from, control: CGPoint(x: midX - nx * spread, y: midY - ny * spread))
            ctx.closePath()
            ctx.fillPath()
        }
        let flash = 15 * (1.25 - k)
        ctx.setFillColor(NSColor(calibratedRed: 1, green: 0.78, blue: 0.42, alpha: 0.9 * k).cgColor)
        ctx.fillEllipse(in: CGRect(x: b.to.x - flash, y: b.to.y - flash, width: flash * 2, height: flash * 2))
        ctx.restoreGState()
    }

    private func drawBeetle(_ ctx: CGContext, _ b: Beetle) {
        let u = b.size
        ctx.saveGState()
        ctx.translateBy(x: b.x, y: b.y)

        if !b.alive {
            let a = max(0, min(1, b.dying / 0.5))
            ctx.setFillColor(NSColor(calibratedWhite: 0.15, alpha: 0.5 * a).cgColor)
            ctx.fillEllipse(in: CGRect(x: -u * 2, y: 0, width: u * 4, height: u * 0.9))
            ctx.restoreGState()
            return
        }

        let facing: CGFloat = b.vx < 0 ? -1 : 1
        ctx.scaleBy(x: facing, y: 1)
        let wig = sin(b.wiggle)

        // legs
        ctx.setStrokeColor(NSColor(calibratedRed: 0.23, green: 0.16, blue: 0.2, alpha: 1).cgColor)
        ctx.setLineWidth(max(1, u * 0.18))
        ctx.setLineCap(.round)
        for k in -1...1 {
            let swing = wig * (k == 0 ? -1 : 1) * u * 0.35
            ctx.move(to: CGPoint(x: CGFloat(k) * u * 0.7, y: u * 0.6))
            ctx.addLine(to: CGPoint(x: CGFloat(k) * u * 0.7 + swing - u * 0.2, y: 0))
        }
        ctx.strokePath()

        // shell
        ctx.setFillColor(NSColor(calibratedRed: 0.85, green: 0.33, blue: 0.31, alpha: 1).cgColor)
        ctx.fillEllipse(in: CGRect(x: -u * 1.35, y: u * 0.1, width: u * 2.7, height: u * 1.7))
        ctx.setStrokeColor(NSColor(calibratedRed: 0.23, green: 0.16, blue: 0.2, alpha: 1).cgColor)
        ctx.setLineWidth(max(1, u * 0.15))
        ctx.move(to: CGPoint(x: 0, y: u * 0.15)); ctx.addLine(to: CGPoint(x: 0, y: u * 1.75)); ctx.strokePath()
        ctx.setFillColor(NSColor(calibratedRed: 0.23, green: 0.16, blue: 0.2, alpha: 1).cgColor)
        for (dx, dy) in [(-0.6, 1.15), (0.35, 1.25), (-0.2, 0.6), (0.7, 0.7)] {
            ctx.fillEllipse(in: CGRect(x: dx * u - u * 0.18, y: dy * u - u * 0.18, width: u * 0.36, height: u * 0.36))
        }
        // head and antennae
        ctx.fillEllipse(in: CGRect(x: u * 0.8, y: u * 0.45, width: u, height: u))
        ctx.setLineWidth(max(1, u * 0.13))
        ctx.move(to: CGPoint(x: u * 1.5, y: u * 1.3)); ctx.addLine(to: CGPoint(x: u * 2.0, y: u * 2.0 + wig * u * 0.2))
        ctx.move(to: CGPoint(x: u * 1.6, y: u * 1.2)); ctx.addLine(to: CGPoint(x: u * 2.3, y: u * 1.5 - wig * u * 0.2))
        ctx.strokePath()
        ctx.setFillColor(NSColor.white.cgColor)
        ctx.fillEllipse(in: CGRect(x: u * 1.34, y: u * 0.89, width: u * 0.32, height: u * 0.32))
        ctx.restoreGState()

        // boss health bar
        if b.boss, b.maxHP > 1 {
            let w: CGFloat = 76, h: CGFloat = 6
            let frac = max(0, min(1, CGFloat(b.hp) / CGFloat(b.maxHP)))
            let barY = b.y + u * 2.9
            ctx.setFillColor(NSColor(calibratedWhite: 0, alpha: 0.35).cgColor)
            ctx.fill(CGRect(x: b.x - w / 2, y: barY, width: w, height: h))
            ctx.setFillColor(NSColor(calibratedRed: 0.95, green: 0.3, blue: 0.28, alpha: 0.95).cgColor)
            ctx.fill(CGRect(x: b.x - w / 2, y: barY, width: w * frac, height: h))
        }

        // label
        if !b.label.isEmpty {
            let text = b.label as NSString
            let attrs: [NSAttributedString.Key: Any] = [
                .font: NSFont.monospacedSystemFont(ofSize: b.boss ? 13 : 11, weight: .medium),
                .foregroundColor: NSColor(calibratedWhite: 1, alpha: 0.92),
            ]
            let size = text.size(withAttributes: attrs)
            let pad: CGFloat = 5
            let labelY = max(4, b.y - size.height - 8)
            let box = CGRect(x: b.x - size.width / 2 - pad, y: labelY - 2,
                             width: size.width + pad * 2, height: size.height + 4)
            let path = CGPath(roundedRect: box, cornerWidth: 5, cornerHeight: 5, transform: nil)
            ctx.setFillColor(NSColor(calibratedRed: 0.09, green: 0.07, blue: 0.11, alpha: 0.8).cgColor)
            ctx.addPath(path); ctx.fillPath()
            text.draw(at: CGPoint(x: b.x - size.width / 2, y: labelY), withAttributes: attrs)
        }
    }

    private func drawRocket(_ ctx: CGContext, _ r: OverlayRocket) {
        let u: CGFloat = 14
        ctx.saveGState()
        ctx.translateBy(x: r.x, y: r.y)
        ctx.rotate(by: sin(r.wobble) * 0.12)

        // Flame: two tapered tongues, solid colour so it reads on any wallpaper.
        let flicker = 1 + 0.18 * sin(r.wobble * 9)
        ctx.setFillColor(NSColor(calibratedRed: 1, green: 0.45, blue: 0.08, alpha: 0.95).cgColor)
        ctx.move(to: CGPoint(x: -u * 0.5, y: -u * 1.15))
        ctx.addQuadCurve(to: CGPoint(x: 0, y: -u * 3.6 * flicker), control: CGPoint(x: -u * 0.55, y: -u * 2.3))
        ctx.addQuadCurve(to: CGPoint(x: u * 0.5, y: -u * 1.15), control: CGPoint(x: u * 0.55, y: -u * 2.3))
        ctx.closePath(); ctx.fillPath()
        ctx.setFillColor(NSColor(calibratedRed: 1, green: 0.86, blue: 0.35, alpha: 0.98).cgColor)
        ctx.move(to: CGPoint(x: -u * 0.26, y: -u * 1.15))
        ctx.addQuadCurve(to: CGPoint(x: 0, y: -u * 2.3 * flicker), control: CGPoint(x: -u * 0.3, y: -u * 1.7))
        ctx.addQuadCurve(to: CGPoint(x: u * 0.26, y: -u * 1.15), control: CGPoint(x: u * 0.3, y: -u * 1.7))
        ctx.closePath(); ctx.fillPath()

        // Body
        ctx.setFillColor(NSColor(calibratedWhite: 0.97, alpha: 1).cgColor)
        ctx.move(to: CGPoint(x: 0, y: u * 2.2))
        ctx.addCurve(to: CGPoint(x: u * 0.8, y: -u * 1.2), control1: CGPoint(x: u * 1.1, y: u * 0.6), control2: CGPoint(x: u * 0.8, y: -u * 0.2))
        ctx.addLine(to: CGPoint(x: -u * 0.8, y: -u * 1.2))
        ctx.addCurve(to: CGPoint(x: 0, y: u * 2.2), control1: CGPoint(x: -u * 0.8, y: -u * 0.2), control2: CGPoint(x: -u * 1.1, y: u * 0.6))
        ctx.fillPath()
        ctx.setFillColor(NSColor(calibratedRed: 0.88, green: 0.32, blue: 0.31, alpha: 1).cgColor)
        ctx.move(to: CGPoint(x: -u * 0.8, y: -u * 0.3)); ctx.addLine(to: CGPoint(x: -u * 1.6, y: -u * 1.6)); ctx.addLine(to: CGPoint(x: -u * 0.7, y: -u * 1.2)); ctx.fillPath()
        ctx.move(to: CGPoint(x: u * 0.8, y: -u * 0.3)); ctx.addLine(to: CGPoint(x: u * 1.6, y: -u * 1.6)); ctx.addLine(to: CGPoint(x: u * 0.7, y: -u * 1.2)); ctx.fillPath()
        ctx.move(to: CGPoint(x: 0, y: u * 2.2)); ctx.addCurve(to: CGPoint(x: u * 0.55, y: u * 0.9), control1: CGPoint(x: u * 0.6, y: u * 1.4), control2: CGPoint(x: u * 0.55, y: u * 1.1))
        ctx.addLine(to: CGPoint(x: -u * 0.55, y: u * 0.9))
        ctx.addCurve(to: CGPoint(x: 0, y: u * 2.2), control1: CGPoint(x: -u * 0.55, y: u * 1.1), control2: CGPoint(x: -u * 0.6, y: u * 1.4))
        ctx.fillPath()
        ctx.setFillColor(NSColor(calibratedRed: 0.37, green: 0.69, blue: 0.85, alpha: 1).cgColor)
        ctx.fillEllipse(in: CGRect(x: -u * 0.38, y: u * 0.1 - u * 0.38, width: u * 0.76, height: u * 0.76))
        ctx.restoreGState()

        if !r.label.isEmpty {
            let text = r.label as NSString
            let attrs: [NSAttributedString.Key: Any] = [
                .font: NSFont.systemFont(ofSize: 12, weight: .semibold),
                .foregroundColor: NSColor(calibratedWhite: 1, alpha: 0.9),
            ]
            let size = text.size(withAttributes: attrs)
            text.draw(at: CGPoint(x: r.x - size.width / 2, y: r.y - u * 4.6), withAttributes: attrs)
        }
    }
}

final class Overlay {
    private var window: NSWindow?
    private var view = OverlayView()
    private var timer: Timer?
    private var nextID = 1
    private var lastScreen: NSScreen?

    /// Where the pet stands, in screen coordinates, refreshed by the host each tick.
    var petAnchor: () -> CGPoint = { .zero }
    /// Called when the pet should aim and fire at a target, with the target in screen coords.
    var onTarget: ((CGPoint, CGFloat) -> Void)?
    /// Called when a beetle dies, so the pet can react and the counters can move.
    var onKill: ((Beetle) -> Void)?

    private(set) var floorY: CGFloat = 0
    var isBusy: Bool { !view.beetles.isEmpty || view.rocket != nil }

    // MARK: window

    private func ensureWindow(on screen: NSScreen) {
        if let w = window, lastScreen === screen { w.orderFrontRegardless(); return }
        window?.orderOut(nil)
        let frame = screen.frame
        let w = NSWindow(contentRect: frame, styleMask: [.borderless], backing: .buffered, defer: false)
        w.isOpaque = false
        w.backgroundColor = .clear
        w.hasShadow = false
        w.ignoresMouseEvents = true
        w.level = .floating
        w.collectionBehavior = [.canJoinAllSpaces, .stationary, .fullScreenAuxiliary, .ignoresCycle]
        w.isReleasedWhenClosed = false
        view.frame = NSRect(origin: .zero, size: frame.size)
        view.autoresizingMask = [.width, .height]
        w.contentView = view
        w.setFrame(frame, display: false)
        w.orderFrontRegardless()
        window = w
        lastScreen = screen
    }

    private func screenPoint(_ p: CGPoint) -> CGPoint {
        guard let f = window?.frame else { return p }
        return CGPoint(x: p.x - f.minX, y: p.y - f.minY)
    }

    private func hideIfIdle() {
        guard !isBusy, view.beams.isEmpty, view.scorches.isEmpty else { return }
        window?.orderOut(nil)
        timer?.invalidate()
        timer = nil
    }

    private func startTicking() {
        guard timer == nil else { return }
        let t = Timer(timeInterval: 1.0 / 60.0, repeats: true) { [weak self] _ in self?.tick() }
        RunLoop.main.add(t, forMode: .common)
        timer = t
    }

    // MARK: spawning

    func release(count: Int, labels: [String], persistent: Bool = false, on screen: NSScreen, floorScreenY: CGFloat, fromScreenX x: CGFloat) {
        ensureWindow(on: screen)
        guard let frame = window?.frame else { return }
        floorY = floorScreenY
        let localFloor = floorScreenY - frame.minY
        let localX = x - frame.minX
        for i in 0..<max(0, count) {
            guard view.beetles.count < 14 else { break }
            let side: CGFloat = Bool.random() ? -1 : 1
            let spread = CGFloat.random(in: 110...max(160, frame.width * 0.42))
            let sx = min(max(30, localX + side * spread), frame.width - 30)
            view.beetles.append(Beetle(
                id: nextID, x: sx, y: localFloor,
                vx: CGFloat.random(in: 45...95) * (Bool.random() ? -1 : 1),
                dart: CGFloat.random(in: 0.5...2), wiggle: CGFloat.random(in: 0...6),
                label: i < labels.count ? labels[i] : "", boss: false, hp: 1, maxHP: 1,
                persistent: persistent, doomed: false, dead: false, dying: 0, born: Date()
            ))
            nextID += 1
        }
        startTicking()
    }

    func releaseBoss(hp: Int, label: String, on screen: NSScreen, floorScreenY: CGFloat, fromScreenX x: CGFloat) {
        ensureWindow(on: screen)
        guard let frame = window?.frame else { return }
        floorY = floorScreenY
        let localX = x - frame.minX
        let sx = min(max(70, localX + CGFloat.random(in: 180...300) * (Bool.random() ? -1 : 1)), frame.width - 70)
        view.beetles.append(Beetle(
            id: nextID, x: sx, y: floorScreenY - frame.minY,
            vx: CGFloat.random(in: 26...44) * (Bool.random() ? -1 : 1),
            dart: 1.4, wiggle: 0, label: label, boss: true, hp: max(1, hp), maxHP: max(1, hp),
            persistent: true, doomed: false, dead: false, dying: 0, born: Date()
        ))
        nextID += 1
        startTicking()
    }

    func launchRocket(label: String, on screen: NSScreen, fromScreen point: CGPoint) {
        ensureWindow(on: screen)
        guard let frame = window?.frame else { return }
        view.rocket = OverlayRocket(x: point.x - frame.minX, y: point.y - frame.minY, vy: 90, wobble: 0, label: label)
        startTicking()
    }

    /// Line the swarm up against the tests that are still failing: anything that has been
    /// fixed becomes fair game for the pet, and anything newly broken crawls out.
    func reconcile(failing: [String], on screen: NSScreen, floorScreenY: CGFloat, fromScreenX x: CGFloat) {
        let stillFailing = Set(failing)
        var present = Set<String>()
        for i in view.beetles.indices where view.beetles[i].persistent && view.beetles[i].alive {
            if view.beetles[i].boss { continue }
            if stillFailing.contains(view.beetles[i].label) { present.insert(view.beetles[i].label) }
            else { view.beetles[i].doomed = true }
        }
        let fresh = failing.filter { !present.contains($0) }
        if !fresh.isEmpty {
            release(count: fresh.count, labels: fresh, persistent: true,
                    on: screen, floorScreenY: floorScreenY, fromScreenX: x)
        }
        view.needsDisplay = true
    }

    /// Everything passed: the whole swarm is fair game.
    func doomAll() {
        for i in view.beetles.indices where view.beetles[i].alive { view.beetles[i].doomed = true }
        view.needsDisplay = true
    }

    /// Keep a boss's health in step with the number of failures still outstanding.
    func syncBoss(failures: Int) {
        for i in view.beetles.indices where view.beetles[i].boss && view.beetles[i].alive {
            if failures <= 0 { view.beetles[i].doomed = true; view.beetles[i].hp = 1 }
            else { view.beetles[i].hp = min(view.beetles[i].hp, max(1, failures)) }
        }
        view.needsDisplay = true
    }

    func clearBeetles() {
        for i in view.beetles.indices where view.beetles[i].alive {
            view.beetles[i].dead = true
            view.beetles[i].dying = 0.5
            view.beetles[i].hp = 0
        }
        view.needsDisplay = true
    }

    /// Fire from the pet's eyes (screen coordinates) at a beetle. True when it died.
    @discardableResult
    func fire(at id: Int, fromEyes eyes: [CGPoint], style: String = "beam") -> Bool {
        guard let index = view.beetles.firstIndex(where: { $0.id == id && $0.alive }) else { return false }
        let target = CGPoint(x: view.beetles[index].x, y: view.beetles[index].y + view.beetles[index].size)
        let beamLife: CGFloat = (style == "kamehameha" || style == "unibeam") ? 0.35 : 0.2
        for eye in eyes {
            view.beams.append(Beam(from: screenPoint(eye), to: target, life: beamLife, style: style))
        }
        view.beetles[index].hp -= 1
        var died = false
        if view.beetles[index].hp <= 0 {
            view.beetles[index].dead = true
            view.beetles[index].dying = 0.5
            view.scorches.append(Scorch(at: target, life: 2.5, big: view.beetles[index].boss))
            onKill?(view.beetles[index])
            died = true
        }
        startTicking()
        view.needsDisplay = true
        return died
    }

    /// Beetles as the pet sees them: window-local coordinates for the pet's page.
    func swarm(relativeTo petFrame: NSRect) -> [[String: Any]] {
        guard let f = window?.frame else { return [] }
        return view.beetles.filter { $0.alive }.map { b in
            let sx = b.x + f.minX, sy = b.y + f.minY
            return ["id": b.id,
                    "x": Double(sx - petFrame.minX),
                    "y": Double(petFrame.maxY - sy),
                    "boss": b.boss,
                    "huntable": b.doomed || !b.persistent] as [String: Any]
        }
    }

    // MARK: simulation

    private func tick() {
        let dt: CGFloat = 1.0 / 60.0
        let w = view.bounds.width
        var changed = false

        for i in view.beetles.indices {
            if !view.beetles[i].alive {
                view.beetles[i].dying -= dt
                changed = true
                continue
            }
            view.beetles[i].wiggle += dt * 26
            view.beetles[i].dart -= dt
            if view.beetles[i].dart <= 0 {
                view.beetles[i].dart = CGFloat.random(in: 0.5...2.2)
                let speed = view.beetles[i].boss ? CGFloat.random(in: 22...40) : CGFloat.random(in: 40...110)
                view.beetles[i].vx = speed * (Bool.random() ? -1 : 1)
            }
            view.beetles[i].x += view.beetles[i].vx * dt
            let edge: CGFloat = 24
            if view.beetles[i].x < edge { view.beetles[i].x = edge; view.beetles[i].vx = abs(view.beetles[i].vx) }
            if view.beetles[i].x > w - edge { view.beetles[i].x = w - edge; view.beetles[i].vx = -abs(view.beetles[i].vx) }
            // A beetle that outlives its welcome wanders off rather than staying for ever.
            if Date().timeIntervalSince(view.beetles[i].born) > 150 { view.beetles[i].dead = true; view.beetles[i].dying = 0.5 }
            changed = true
        }
        view.beetles.removeAll { $0.dead && $0.dying <= 0 }

        for i in view.beams.indices { view.beams[i].life -= dt }
        if !view.beams.isEmpty { changed = true }
        view.beams.removeAll { $0.life <= 0 }

        for i in view.scorches.indices { view.scorches[i].life -= dt }
        view.scorches.removeAll { $0.life <= 0 }

        if var r = view.rocket {
            r.vy += 340 * dt
            r.y += r.vy * dt
            r.wobble += dt * 7
            r.x += sin(r.wobble) * 14 * dt
            view.rocket = r.y > view.bounds.height + 90 ? nil : r
            changed = true
        }

        if changed { view.needsDisplay = true }
        if !isBusy && view.beams.isEmpty && view.scorches.isEmpty { hideIfIdle() }
    }
}
