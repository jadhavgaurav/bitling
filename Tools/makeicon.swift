// Draws the Bitling app icon (a small robot with a screen face) at every size an .iconset needs.
// Usage: makeicon <output.iconset directory>
import Cocoa

let args = CommandLine.arguments
guard args.count == 2 else {
    FileHandle.standardError.write("usage: makeicon <output.iconset>\n".data(using: .utf8)!)
    exit(2)
}
let outDir = URL(fileURLWithPath: args[1])
try FileManager.default.createDirectory(at: outDir, withIntermediateDirectories: true)

func rgb(_ r: CGFloat, _ g: CGFloat, _ b: CGFloat, _ a: CGFloat = 1) -> NSColor {
    NSColor(calibratedRed: r / 255, green: g / 255, blue: b / 255, alpha: a)
}

func rounded(_ rect: NSRect, _ radius: CGFloat) -> NSBezierPath {
    NSBezierPath(roundedRect: rect, xRadius: radius, yRadius: radius)
}

func render(pixels: Int) -> Data {
    guard let rep = NSBitmapImageRep(
        bitmapDataPlanes: nil, pixelsWide: pixels, pixelsHigh: pixels, bitsPerSample: 8,
        samplesPerPixel: 4, hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB,
        bytesPerRow: 0, bitsPerPixel: 0
    ) else { fatalError("bitmap allocation failed") }
    NSGraphicsContext.saveGraphicsState()
    defer { NSGraphicsContext.restoreGraphicsState() }
    guard let gc = NSGraphicsContext(bitmapImageRep: rep) else { fatalError("graphics context failed") }
    NSGraphicsContext.current = gc
    gc.imageInterpolation = .high
    let s = CGFloat(pixels)

    // Tile: deep navy to indigo, the colour of the robot's screen.
    let inset = s * 0.05
    let tile = rounded(NSRect(x: inset, y: inset, width: s - 2 * inset, height: s - 2 * inset), s * 0.22)
    NSGradient(starting: rgb(29, 33, 64), ending: rgb(58, 52, 110))!.draw(in: tile, angle: 90)
    tile.addClip()

    let outline = rgb(110, 104, 150)
    let shellTop = rgb(240, 238, 250)
    let shellBottom = rgb(200, 196, 228)
    let lineWidth = max(1, s * 0.018)

    // Body.
    let body = rounded(NSRect(x: s * 0.33, y: s * 0.12, width: s * 0.34, height: s * 0.22), s * 0.07)
    NSGradient(starting: shellBottom, ending: shellTop)!.draw(in: body, angle: 90)
    outline.setStroke(); body.lineWidth = lineWidth; body.stroke()
    // Chest LEDs.
    for (i, colour) in [rgb(90, 214, 150), rgb(90, 214, 150), rgb(250, 190, 80)].enumerated() {
        colour.setFill()
        NSBezierPath(ovalIn: NSRect(x: s * (0.44 + CGFloat(i) * 0.05), y: s * 0.2, width: s * 0.03, height: s * 0.03)).fill()
    }
    // Arms.
    for x in [s * 0.27, s * 0.69] {
        let arm = rounded(NSRect(x: x, y: s * 0.14, width: s * 0.05, height: s * 0.16), s * 0.025)
        shellBottom.setFill(); arm.fill(); outline.setStroke(); arm.lineWidth = lineWidth; arm.stroke()
    }
    // Neck.
    rgb(150, 145, 190).setFill()
    NSRect(x: s * 0.46, y: s * 0.33, width: s * 0.08, height: s * 0.05).fill()

    // Antenna.
    let stem = NSBezierPath()
    stem.move(to: NSPoint(x: s * 0.5, y: s * 0.79))
    stem.line(to: NSPoint(x: s * 0.5, y: s * 0.86))
    stem.lineWidth = max(1, s * 0.02)
    outline.setStroke(); stem.stroke()
    let tipRect = NSRect(x: s * 0.46, y: s * 0.85, width: s * 0.08, height: s * 0.08)
    let glow = NSShadow()
    glow.shadowColor = rgb(126, 245, 230, 0.9)
    glow.shadowBlurRadius = s * 0.04
    NSGraphicsContext.saveGraphicsState()
    glow.set()
    rgb(126, 245, 230).setFill()
    NSBezierPath(ovalIn: tipRect).fill()
    NSGraphicsContext.restoreGraphicsState()

    // Head.
    let head = rounded(NSRect(x: s * 0.2, y: s * 0.38, width: s * 0.6, height: s * 0.42), s * 0.11)
    NSGradient(starting: shellBottom, ending: shellTop)!.draw(in: head, angle: 90)
    outline.setStroke(); head.lineWidth = lineWidth; head.stroke()
    // Ear caps.
    for x in [s * 0.165, s * 0.775] {
        let cap = rounded(NSRect(x: x, y: s * 0.52, width: s * 0.06, height: s * 0.14), s * 0.02)
        rgb(176, 170, 214).setFill(); cap.fill(); outline.setStroke(); cap.lineWidth = lineWidth; cap.stroke()
    }
    // Screen.
    let screen = rounded(NSRect(x: s * 0.26, y: s * 0.44, width: s * 0.48, height: s * 0.3), s * 0.07)
    rgb(29, 33, 64).setFill(); screen.fill()
    outline.setStroke(); screen.lineWidth = lineWidth; screen.stroke()

    // Face, glowing cyan.
    NSGraphicsContext.saveGraphicsState()
    let faceGlow = NSShadow()
    faceGlow.shadowColor = rgb(126, 245, 230, 0.8)
    faceGlow.shadowBlurRadius = s * 0.03
    faceGlow.set()
    let cyan = rgb(126, 245, 230)
    cyan.setFill(); cyan.setStroke()
    for x in [s * 0.36, s * 0.56] {
        rounded(NSRect(x: x, y: s * 0.57, width: s * 0.08, height: s * 0.09), s * 0.02).fill()
    }
    let smile = NSBezierPath()
    smile.lineWidth = max(1.5, s * 0.022)
    smile.lineCapStyle = .round
    smile.move(to: NSPoint(x: s * 0.43, y: s * 0.52))
    smile.curve(to: NSPoint(x: s * 0.57, y: s * 0.52), controlPoint1: NSPoint(x: s * 0.47, y: s * 0.47), controlPoint2: NSPoint(x: s * 0.53, y: s * 0.47))
    smile.stroke()
    NSGraphicsContext.restoreGraphicsState()

    guard let png = rep.representation(using: .png, properties: [:]) else { fatalError("png encode failed") }
    return png
}

let sizes: [(String, Int)] = [
    ("icon_16x16", 16), ("icon_16x16@2x", 32), ("icon_32x32", 32), ("icon_32x32@2x", 64),
    ("icon_128x128", 128), ("icon_128x128@2x", 256), ("icon_256x256", 256), ("icon_256x256@2x", 512),
    ("icon_512x512", 512), ("icon_512x512@2x", 1024),
]
for (name, px) in sizes {
    try render(pixels: px).write(to: outDir.appendingPathComponent("\(name).png"))
}
print("icon set written to \(outDir.path)")
