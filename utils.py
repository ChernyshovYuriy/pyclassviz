import os
from pathlib import Path


def ensure_directory_exists(path):
    """Ensures a directory exists, creating it and any necessary parents.

    Args:
        path: The path to the directory (string or Path object).
    """
    try:
        if isinstance(path, str):
            os.makedirs(path, exist_ok=True)
        elif isinstance(path, Path):
            path.mkdir(parents=True, exist_ok=True)
        else:
            raise TypeError("path must be a string or a pathlib.Path object")
        print(f"Directory '{path}' created or already exists.")
    except OSError as e:
        print(f"Error creating directory '{path}': {e}")
    except TypeError as e:
        print(e)


def inject_fullscreen_css_js(filename):
    with open(filename, "r") as f:
        html = f.read()

    html = html.replace(
        "<body>",
        """
<body style="margin: 0; overflow: hidden;">
<style type="text/css">
    #mynetwork {
        width: 100vw;
        height: 100vh;
    }
</style>
<script type="text/javascript">
    window.addEventListener('resize', function() {
        var network = document.getElementById('mynetwork');
        network.style.width = window.innerWidth + 'px';
        network.style.height = window.innerHeight + 'px';
    });
</script>
""",
    )

    with open(filename, "w") as f:
        f.write(html)
