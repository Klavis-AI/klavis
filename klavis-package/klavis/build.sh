#!/bin/bash
set -e

echo "========================================"
echo "🔨 Building Klavis Binaries"
echo "========================================"

mkdir -p bin

echo "📦 Compiling for Linux..."
GOOS=linux   GOARCH=amd64 go build -o bin/klavis-linux
echo "📦 Compiling for macOS..."
GOOS=darwin  GOARCH=amd64 go build -o bin/klavis-darwin
echo "📦 Compiling for Windows..."
GOOS=windows GOARCH=amd64 go build -o bin/klavis-windows.exe

echo ""
echo "========================================"
echo "🚚 Moving Linux binary into Debian package"
echo "========================================"
cp bin/klavis-linux ../klavis-deb/usr/local/bin/klavis

echo ""
echo "========================================"
echo "📝 Generating Completion Scripts"
echo "========================================"
./bin/klavis-linux completion bash > ../klavis-deb/etc/bash_completion.d/klavis.bash
./bin/klavis-linux completion zsh  > ../klavis-deb/usr/share/zsh/vendor-completions/_klavis
echo "✅ Completion scripts created (bash + zsh)"

echo ""
echo "========================================"
echo "📦 Building Debian Package"
echo "========================================"
dpkg-deb --build ../klavis-deb
echo "✅ Debian package built: ../klavis-deb.deb"

echo ""
echo "========================================"
echo "📥 Installing Package"
echo "========================================"
sudo dpkg -i ../klavis-deb.deb || true
echo "✅ Klavis installed!"

echo ""
echo "========================================"
echo "🎉 All Done!"
echo "========================================"
echo "👉 Try running: klavis --help"
echo "👉 Autocompletion available in bash & zsh"
echo ""


klavis
