// Draws the Jellykin app icon at every size an .iconset needs.
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

    // Habitat tile: sky gradient in a macOS-style rounded square.
    let inset = s * 0.05
    let tile = NSBezierPath(
        roundedRect: NSRect(x: inset, y: inset, width: s - 2 * inset, height: s - 2 * inset),
        xRadius: s * 0.22, yRadius: s * 0.22
    )
    NSGradient(starting: rgb(234, 245, 242), ending: rgb(163, 213, 234))!.draw(in: tile, angle: 90)

    // Two soft hills.
    tile.addClip()
    rgb(191, 216, 201).setFill()
    let hillA = NSBezierPath()
    hillA.move(to: NSPoint(x: -s * 0.1, y: s * 0.22))
    hillA.curve(to: NSPoint(x: s * 0.6, y: s * 0.22), controlPoint1: NSPoint(x: s * 0.12, y: s * 0.42), controlPoint2: NSPoint(x: s * 0.4, y: s * 0.42))
    hillA.line(to: NSPoint(x: -s * 0.1, y: -s * 0.1))
    hillA.close()
    hillA.fill()
    let hillB = NSBezierPath()
    hillB.move(to: NSPoint(x: s * 0.45, y: s * 0.22))
    hillB.curve(to: NSPoint(x: s * 1.1, y: s * 0.22), controlPoint1: NSPoint(x: s * 0.7, y: s * 0.46), controlPoint2: NSPoint(x: s * 0.95, y: s * 0.46))
    hillB.line(to: NSPoint(x: s * 1.1, y: -s * 0.1))
    hillB.close()
    hillB.fill()
    rgb(207, 227, 214).setFill()
    NSRect(x: 0, y: 0, width: s, height: s * 0.22).fill()

    // Shadow.
    rgb(34, 72, 77, 0.18).setFill()
    NSBezierPath(ovalIn: NSRect(x: s * 0.28, y: s * 0.17, width: s * 0.44, height: s * 0.08)).fill()

    // Body: a slightly squashed jelly blob.
    let body = NSBezierPath(ovalIn: NSRect(x: s * 0.2, y: s * 0.2, width: s * 0.6, height: s * 0.54))
    NSGradient(starting: rgb(255, 224, 232), ending: rgb(240, 120, 154))!.draw(in: body, angle: -60)

    // Belly highlight.
    rgb(255, 240, 244, 0.5).setFill()
    NSBezierPath(ovalIn: NSRect(x: s * 0.34, y: s * 0.24, width: s * 0.32, height: s * 0.2)).fill()

    // Cheeks.
    rgb(255, 127, 163, 0.55).setFill()
    NSBezierPath(ovalIn: NSRect(x: s * 0.245, y: s * 0.43, width: s * 0.1, height: s * 0.06)).fill()
    NSBezierPath(ovalIn: NSRect(x: s * 0.655, y: s * 0.43, width: s * 0.1, height: s * 0.06)).fill()

    // Eyes.
    let ink = rgb(84, 32, 49)
    for cx in [s * 0.4, s * 0.6] {
        NSColor.white.setFill()
        NSBezierPath(ovalIn: NSRect(x: cx - s * 0.065, y: s * 0.47, width: s * 0.13, height: s * 0.15)).fill()
        ink.setFill()
        NSBezierPath(ovalIn: NSRect(x: cx - s * 0.037, y: s * 0.485, width: s * 0.074, height: s * 0.09)).fill()
        NSColor.white.setFill()
        NSBezierPath(ovalIn: NSRect(x: cx - s * 0.03, y: s * 0.54, width: s * 0.025, height: s * 0.025)).fill()
    }

    // Smile.
    ink.setStroke()
    let mouth = NSBezierPath()
    mouth.lineWidth = max(1, s * 0.022)
    mouth.lineCapStyle = .round
    mouth.move(to: NSPoint(x: s * 0.45, y: s * 0.41))
    mouth.curve(to: NSPoint(x: s * 0.55, y: s * 0.41), controlPoint1: NSPoint(x: s * 0.48, y: s * 0.365), controlPoint2: NSPoint(x: s * 0.52, y: s * 0.365))
    mouth.stroke()

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
