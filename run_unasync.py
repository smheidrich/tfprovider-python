from pathlib import Path

from unasync import Rule, unasync_files

async_dirs = [p for p in Path("tfprovider/").glob("**/_async") if p.is_dir()]
print(async_dirs)

unasync_files(
    [str(p) for p in Path("tfprovider/").glob("**/_async/**/*.py")],
    [Rule(str(p), str(p.parent / "_sync")) for p in async_dirs],
)
