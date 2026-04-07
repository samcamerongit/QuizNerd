#!/bin/zsh
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

LOG_FILE="$SCRIPT_DIR/quiznerd-launch.log"
rm -f "$LOG_FILE"

PYTHON_GUI="/Library/Frameworks/Python.framework/Versions/3.13/Resources/Python.app/Contents/MacOS/Python"

if [[ ! -x "$PYTHON_GUI" ]]; then
  PYTHON_GUI="$(command -v python3)"
fi

nohup "$PYTHON_GUI" "$SCRIPT_DIR/quiznerd.py" >>"$LOG_FILE" 2>&1 &
APP_PID=$!
disown
sleep 1

if kill -0 "$APP_PID" >/dev/null 2>&1; then
  exit 0
fi

STATUS=1
if [[ $STATUS -ne 0 ]]; then
  echo
  echo "QuizNerd couldn't open."
  if [[ -f "$LOG_FILE" ]]; then
    echo
    cat "$LOG_FILE"
  fi
  echo
  echo "Press Enter to close this window."
  read
fi

exit $STATUS
