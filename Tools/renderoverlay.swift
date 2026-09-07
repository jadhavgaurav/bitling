// Renders the overlay's Core Graphics art to a PNG so it can be checked without a screenshot.
// Usage: renderoverlay <out.png>
import Cocoa

let args = CommandLine.arguments
guard args.count == 2 else { exit(2) }
let size = NSSize(width: 900, height: 420)
let view = OverlayView(frame: NSRect(origin: .zero, size: size))
view.loadDemoScene()

guard let rep = view.bitmapImageRepForCachingDisplay(in: view.bounds) else { exit(1) }
// A dark ground so the light art is legible, standing in for a desktop behind it.
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
NSColor(calibratedRed: 0.10, green: 0.11, blue: 0.14, alpha: 1).setFill()
NSRect(origin: .zero, size: size).fill()
NSGraphicsContext.restoreGraphicsState()
view.cacheDisplay(in: view.bounds, to: rep)
guard let png = rep.representation(using: .png, properties: [:]) else { exit(1) }
try png.write(to: URL(fileURLWithPath: args[1]))
print("wrote \(args[1])")
