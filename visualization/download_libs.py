import urllib.request
import os
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

libs_dir = "visualization/libs"
if not os.path.exists(libs_dir):
    os.makedirs(libs_dir)

libs = [
    ("https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.28.1/cytoscape.min.js", "visualization/libs/cytoscape.min.js"),
    ("https://cdnjs.cloudflare.com/ajax/libs/dagre/0.8.5/dagre.min.js", "visualization/libs/dagre.min.js"),
]

# Try to download first two
for url, path in libs:
    print(f"Downloading {url} to {path}...")
    try:
        with urllib.request.urlopen(url, context=ctx) as response, open(path, 'wb') as out_file:
            out_file.write(response.read())
        print(f"Saved {path}")
    except Exception as e:
        print(f"Failed: {e}")

# Try fallbacks for cytoscape-dagre
dagre_urls = [
    "https://unpkg.com/cytoscape-dagre@2.5.0/dist/cytoscape-dagre.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/cytoscape-dagre/2.3.2/cytoscape-dagre.min.js",
    "https://cdn.jsdelivr.net/npm/cytoscape-dagre@2.3.2/cytoscape-dagre.min.js"
]
dagre_path = "visualization/libs/cytoscape-dagre.min.js"

print("Downloading cytoscape-dagre...")
success = False
for url in dagre_urls:
    print(f"Trying {url}...")
    try:
        with urllib.request.urlopen(url, context=ctx) as response, open(dagre_path, 'wb') as out_file:
            out_file.write(response.read())
        print(f"Saved {dagre_path}")
        success = True
        break
    except Exception as e:
        print(f"Failed {url}: {e}")

if not success:
    print("Could not download cytoscape-dagre from any source.")
