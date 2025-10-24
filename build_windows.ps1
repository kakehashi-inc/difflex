# difflex / src\difflex\main.py / assets\app.ico
python -m nuitka `
  --onefile `
  --windows-console-mode=disable `
  --windows-icon-from-ico="assets\app.ico" `
  --output-filename="difflex" `
  "src\difflex\main.py"
