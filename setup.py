import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "include_files": [
		("icons", "icons"),
		("LICENSE", "LICENSE"),
		("README.md", "README.md"),
    ],
    "optimize": 1,
}

# base="Win32GUI" should be used only for Windows GUI app
base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="LaserCameraViewer",
    version="0.1",
    description="Beam Alignment System",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base=base)],
)
