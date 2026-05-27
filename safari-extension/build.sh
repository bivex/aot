#!/bin/bash
# Build Safari Web Extension from this directory.
# Requires: Xcode 14+, macOS 13+ (Ventura), Safari 16.4+
#
# Usage:
#   cd safari-extension
#   ./build.sh          # Convert + open in Xcode
#   ./build.sh build    # Convert + build release
#   ./build.sh run      # Convert + build + run

set -e
cd "$(dirname "$0")"

EXT_DIR="$(pwd)"
BUILD_DIR="$EXT_DIR/build"
APP_NAME="AOT Syntax Analyzer"

echo "=== AOT Safari Web Extension Builder ==="
echo ""

# Check Xcode
if ! xcodebuild -version &>/dev/null; then
  echo "Error: Xcode not found. Install from App Store."
  exit 1
fi

# Check converter tool
if ! xcrun --find safari-web-extension-converter &>/dev/null; then
  echo "Error: safari-web-extension-converter not found."
  echo "Install Xcode command line tools: xcode-select --install"
  exit 1
fi

# Clean previous build
if [ -d "$BUILD_DIR" ]; then
  echo "Cleaning previous build..."
  rm -rf "$BUILD_DIR"
fi

# Convert WebExtension to Safari extension Xcode project
echo "Converting WebExtension to Safari extension..."
xcrun safari-web-extension-converter "$EXT_DIR" \
  --project-location "$BUILD_DIR" \
  --app-name "$APP_NAME" \
  --bundle-identifier com.aot.syntaxanalyzer

echo ""
echo "Converted successfully. Project at: $BUILD_DIR/$APP_NAME"

# Handle subcommand
CMD="${1:-open}"

case "$CMD" in
  open)
    echo "Opening in Xcode..."
    open "$BUILD_DIR/$APP_NAME.xcodeproj"
    echo ""
    echo "In Xcode:"
    echo "  1. Select the '$APP_NAME' scheme (macOS target)"
    echo "  2. Build & Run (Cmd+R)"
    echo "  3. Safari > Settings > Extensions > enable '$APP_NAME'"
    ;;
  build)
    echo "Building release..."
    cd "$BUILD_DIR"
    xcodebuild -project "$APP_NAME.xcodeproj" \
      -scheme "$APP_NAME (macOS)" \
      -configuration Release \
      CONFIGURATION_BUILD_DIR="$BUILD_DIR/output"
    echo ""
    echo "Built to: $BUILD_DIR/output/"
    echo "Run the app to install the extension into Safari."
    ;;
  run)
    echo "Building and running..."
    cd "$BUILD_DIR"
    xcodebuild -project "$APP_NAME.xcodeproj" \
      -scheme "$APP_NAME (macOS)" \
      -configuration Debug \
      build 2>&1 | tail -5
    echo ""
    echo "Launching..."
    open "$BUILD_DIR/build/Debug/$APP_NAME.app"
    echo ""
    echo "Safari > Settings > Extensions > enable '$APP_NAME'"
    ;;
  *)
    echo "Usage: $0 [open|build|run]"
    exit 1
    ;;
esac
