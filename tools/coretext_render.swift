// Render text with CoreText, antialiasing off, to a PNG.
//
//     swift tools/coretext_render.swift FONT.ttf SIZE TEXT OUT.png [SCALE]
//
// The image is one line tall (SIZE*SCALE px) and SIZE*SCALE/2 px per
// character, with the baseline at the font's descent, so each character lands
// in its own cell. SCALE (default 1) works like a Retina backing scale: the
// font is SIZE points drawn through a SCALE-times CTM.
import CoreGraphics
import CoreText
import Foundation
import ImageIO
import UniformTypeIdentifiers

let args = CommandLine.arguments
guard args.count == 5 || args.count == 6, let size = Double(args[2]) else {
    FileHandle.standardError.write("usage: coretext_render.swift FONT SIZE TEXT OUT.png [SCALE]\n".data(using: .utf8)!)
    exit(2)
}
let fontURL = URL(fileURLWithPath: args[1])
let text = args[3]
let outURL = URL(fileURLWithPath: args[4])
let scale = args.count == 6 ? Double(args[5])! : 1

guard let descriptors = CTFontManagerCreateFontDescriptorsFromURL(fontURL as CFURL) as? [CTFontDescriptor],
      let descriptor = descriptors.first else {
    FileHandle.standardError.write("could not load \(fontURL.path)\n".data(using: .utf8)!)
    exit(1)
}
let font = CTFontCreateWithFontDescriptor(descriptor, CGFloat(size), nil)

let count = text.count
let width = Int(size * scale / 2) * count
let height = Int(size * scale)
let context = CGContext(data: nil, width: width, height: height, bitsPerComponent: 8, bytesPerRow: 0,
                        space: CGColorSpaceCreateDeviceGray(), bitmapInfo: CGImageAlphaInfo.none.rawValue)!
context.setFillColor(gray: 1, alpha: 1)
context.fill(CGRect(x: 0, y: 0, width: width, height: height))
context.scaleBy(x: CGFloat(scale), y: CGFloat(scale))
context.setShouldAntialias(false)
context.setAllowsAntialiasing(false)
context.setShouldSmoothFonts(false)
context.setAllowsFontSmoothing(false)
context.setShouldSubpixelPositionFonts(false)
context.setAllowsFontSubpixelPositioning(false)

let attributes: [NSAttributedString.Key: Any] = [
    NSAttributedString.Key(kCTFontAttributeName as String): font,
    NSAttributedString.Key(kCTForegroundColorAttributeName as String): CGColor(gray: 0, alpha: 1),
]
let line = CTLineCreateWithAttributedString(NSAttributedString(string: text, attributes: attributes))
context.textPosition = CGPoint(x: 0, y: CTFontGetDescent(font).rounded())
CTLineDraw(line, context)

let image = context.makeImage()!
let destination = CGImageDestinationCreateWithURL(outURL as CFURL, UTType.png.identifier as CFString, 1, nil)!
CGImageDestinationAddImage(destination, image, nil)
CGImageDestinationFinalize(destination)
