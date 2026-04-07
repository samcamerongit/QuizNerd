#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="QuizNerd"
BUNDLE_DIR="$ROOT_DIR/$APP_NAME.app"
CONTENTS_DIR="$BUNDLE_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"

rm -rf "$BUNDLE_DIR"
mkdir -p "$MACOS_DIR" "$RESOURCES_DIR"

cp "$ROOT_DIR/quiznerd.py" "$RESOURCES_DIR/quiznerd.py"
cp "$ROOT_DIR/quiznerd_data.py" "$RESOURCES_DIR/quiznerd_data.py"

cat > "$CONTENTS_DIR/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDevelopmentRegion</key>
  <string>English</string>
  <key>CFBundleExecutable</key>
  <string>QuizNerd</string>
  <key>CFBundleIdentifier</key>
  <string>com.samcameron.quiznerd</string>
  <key>CFBundleInfoDictionaryVersion</key>
  <string>6.0</string>
  <key>CFBundleName</key>
  <string>QuizNerd</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>1.0</string>
  <key>CFBundleVersion</key>
  <string>1</string>
  <key>LSMinimumSystemVersion</key>
  <string>12.0</string>
  <key>NSHighResolutionCapable</key>
  <true/>
  <key>NSPrincipalClass</key>
  <string>NSApplication</string>
</dict>
</plist>
PLIST

cat > "$MACOS_DIR/QuizNerd" <<'SCRIPT'
#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RESOURCES_DIR="$SCRIPT_DIR/../Resources"
PYTHON_GUI="/Library/Frameworks/Python.framework/Versions/3.13/Resources/Python.app/Contents/MacOS/Python"

if [[ ! -x "$PYTHON_GUI" ]]; then
  PYTHON_GUI="$(command -v python3)"
fi

exec "$PYTHON_GUI" "$RESOURCES_DIR/quiznerd.py"
SCRIPT

printf 'APPL' > "$CONTENTS_DIR/PkgInfo"
chmod +x "$MACOS_DIR/QuizNerd"

echo "Built $BUNDLE_DIR"
