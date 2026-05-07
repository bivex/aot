#!/bin/bash

# Configuration
export RML="$(pwd)"
BUILD_DIR="${RML}/build_fast"

# Ensure tools are installed (Homebrew for macOS)
if ! command -v ninja &> /dev/null || ! command -v ccache &> /dev/null; then
    echo "Installing Ninja and ccache for fast builds..."
    brew install ninja ccache
fi

echo "Cleaning old fast build dir (optional, ccache will handle caching)..."
# rm -rf "$BUILD_DIR" # Uncomment to force a clean build, but ccache makes it unnecessary
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR" || exit 1

# Configure CMake to use Ninja, ccache, and Unity Builds
# We also disable BUILD_TESTING if it's not needed
echo "Configuring with CMake + Ninja + ccache..."
cmake .. -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER_LAUNCHER=ccache \
  -DCMAKE_CXX_COMPILER_LAUNCHER=ccache \
  -DCMAKE_UNITY_BUILD=OFF \
  -DBUILD_DICTS=OFF \
  -DCMAKE_UNITY_BUILD_BATCH_SIZE=16 \
  -DZLIB_LIBRARY=/opt/homebrew/Cellar/zlib/1.3.2/lib/libz.a \
  -DZLIB_INCLUDE_DIR=/opt/homebrew/Cellar/zlib/1.3.2/include

# Build using Ninja
echo "Building with Ninja..."
# Ninja automatically uses all available CPU cores, no need for -j$(sysctl -n hw.ncpu)
ninja

echo "Copying binaries to Bin/..."
cp Source/www/SynanDaemon/SynanDaemon "$RML/Bin/"
cp Source/www/SemanDaemon/SemanDaemon "$RML/Bin/"

echo "Build complete! Check ccache stats with 'ccache -s'"
