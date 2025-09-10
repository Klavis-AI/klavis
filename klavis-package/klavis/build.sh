mkdir -p ../klavis-package/klavis/bin

echo "Creating Compiled Files"

GOOS=linux   GOARCH=amd64 go build -o bin/klavis-linux
GOOS=darwin  GOARCH=amd64 go build -o bin/klavis-darwin
GOOS=windows GOARCH=amd64 go build -o bin/klavis-windows.exe

echo "Moving to klavis-linux to klavis-deb/usr/local/bin/ by name klavis"

cp bin/klavis-linux ../klavis-deb/usr/local/bin/klavis

echo "creating 'klavis.bash' and '_klavis'"

./bin/klavis-linux completion bash > ../klavis-deb/etc/bash_completion.d/klavis.bash
./bin/klavis-linux completion zsh > ../klavis-deb/usr/share/zsh/vendor-completions/_klavis

echo "building klavis-deb"

dpkg-deb --build ../klavis-deb

echo "Installing klavis-deb.deb"

sudo dpkg -i ../klavis-deb.deb

echo "✅ Klavis package built and installed!"
echo "Try running: klavis --help"
echo "Auto-completion should work in both bash and zsh"

