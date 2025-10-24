# difflex

Smart file and directory comparison tool with 3-way diff, similarity detection, and external tool integration

## For Developers

### Install dependencies

Create and activate a virtual environment:

```bash
python -m venv venv

# On Windows
.\venv\Scripts\Activate.ps1

# On Linux/macOS
source venv/bin/activate

pip install -e ".[dev]"
```

### Create Windows Icon

```exec
magick assets/app.png -define icon:auto-resize=256,128,96,64,48,32,24,16 assets/app.ico
```
