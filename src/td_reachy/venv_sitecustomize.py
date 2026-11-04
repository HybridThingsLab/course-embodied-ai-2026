"""Python skips a .pth file that carries the system's "hidden" flag; this reads it anyway.

The setups copy this file into the project's .venv as sitecustomize.py:

    .venv/bin/python src/td_reachy/venv_sitecustomize.py

(again whenever this file has changed; it also says when the project folder looks synced).
Python imports sitecustomize at every start, right after it has read the .pth files of
site-packages, and a module is imported whatever its flags say.

Why: on a Mac, iCloud Drive sets the hidden flag on everything inside a folder whose name
begins with a dot - .venv - when the project folder is in iCloud Drive or in a Desktop or
Documents folder that iCloud keeps (GitHub Desktop clones into Documents/GitHub). It does
so within seconds of a file being made, and again after the flag is cleared. Python's site
skips hidden .pth files (python/cpython#113659; the .venv's 3.12 does), and two of them
matter here: gstreamer_bundle.pth puts GStreamer's Python bindings on the path and sets its
variables - without it the daemon stops with "No module named 'gi'" - and the editable
install's _editable_impl_sense_think_move.pth puts src/ on the path - without it "No module
named 'td_reachy'". So each hidden .pth file of site-packages is read here, as site would
have read it.

No td_reachy imports: as sitecustomize this runs before td_reachy can be found.
"""

import io
import os
import stat
import sys

# Marks a sitecustomize.py as this file (an older copy may be replaced, another one not).
ORIGIN = "src/td_reachy/venv_sitecustomize.py"

# What the setups say when iCloud keeps the project folder: by its path, or by the flags.
IN_DRIVE = "Note: this project folder is in iCloud Drive, which marks the files in .venv hidden."
MARKED = ("Note: the files in .venv are marked hidden. iCloud Drive does that to a folder it "
          "syncs, and it syncs Desktop and Documents when it keeps them.")
ADVICE = (" Python leaves some of them out then; sitecustomize.py in .venv reads them anyway. "
          "But iCloud also uploads .venv (more than 1 GB): better keep the project folder "
          "where iCloud does not sync it - docs/getting-started.md, step 2.")


def hidden(path):
    """Whether site leaves this .pth file out for its flags (as site.addpackage asks)."""
    try:
        st = os.lstat(path)
    except OSError:
        return False
    return bool(
        getattr(st, "st_flags", 0) & stat.UF_HIDDEN
        or getattr(st, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_HIDDEN
    )


def hidden_pth(sitedir):
    """The .pth files of sitedir that site left out for their flags, in site's order. Names
    that begin with a dot (macOS's ._ files) site leaves out by name, and so does this."""
    try:
        names = os.listdir(sitedir)
    except OSError:
        return []
    return sorted(
        name for name in names
        if name.endswith(".pth") and not name.startswith(".")
        and hidden(os.path.join(sitedir, name))
    )


def read_pth(sitedir, name):
    """What site.addpackage does with one .pth file, without looking at its flags: a line
    that begins with "import" is run, any other names a folder to add to sys.path."""
    fullname = os.path.join(sitedir, name)
    try:
        with io.open_code(fullname) as f:
            content = f.read()
    except OSError:
        return
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return  # site tries the locale's encoding then; none of the files here needs it
    known = {os.path.normcase(os.path.abspath(p)) for p in sys.path if p}
    for n, line in enumerate(text.splitlines(), 1):
        if line.startswith("#") or not line.strip():
            continue
        try:
            if line.startswith(("import ", "import\t")):
                exec(line)
                continue
            folder = os.path.abspath(os.path.join(sitedir, line.rstrip()))
            if os.path.normcase(folder) not in known and os.path.exists(folder):
                sys.path.append(folder)
                known.add(os.path.normcase(folder))
        except Exception as exc:  # as site reports it, and the rest of the file is left out
            print(f"Error processing line {n:d} of {fullname}:\n\n  {exc!r}\n\n"
                  "Remainder of file ignored", file=sys.stderr)
            break


def rescue(sitedir):
    """Read every .pth file of sitedir that site left out for its flags; their names."""
    names = hidden_pth(sitedir)
    for name in names:
        read_pth(sitedir, name)
    return names


def install(source, dest):
    """Copy source to dest: "added", "updated", "in place", or "other" when dest is a
    sitecustomize.py that is not this file's (it is left as it is)."""
    with open(source, "rb") as f:
        new = f.read()
    try:
        with open(dest, "rb") as f:
            old = f.read()
    except FileNotFoundError:
        old = None
    if old == new:
        return "in place"
    if old is not None and ORIGIN.encode() not in old:
        return "other"
    part = os.fspath(dest) + ".part"
    with open(part, "wb") as f:
        f.write(new)
    os.replace(part, dest)
    return "added" if old is None else "updated"


def in_icloud(folder, home):
    """Whether the folder is in iCloud Drive itself, by its real path. (A Desktop or
    Documents folder that iCloud keeps shows only through the flags.)"""
    drive = os.path.join(os.path.realpath(home), "Library", "Mobile Documents")
    return os.path.realpath(folder).startswith(drive + os.sep)


def main():
    import sysconfig

    if sys.prefix == sys.base_prefix:
        print("error: run this with the project's own Python: "
              ".venv/bin/python src/td_reachy/venv_sitecustomize.py", file=sys.stderr)
        return 1
    here = os.path.abspath(__file__)
    project = os.path.dirname(os.path.dirname(os.path.dirname(here)))
    sitedir = sysconfig.get_paths()["purelib"]
    done = install(here, os.path.join(sitedir, "sitecustomize.py"))
    if done == "other":
        print(f"Note: {sitedir}/sitecustomize.py is not this project's, so it was left as it "
              "is. If iCloud syncs this folder, Python may leave files of .venv out.")
    elif done == "added":
        print("Added sitecustomize.py to .venv: Python reads the .pth files there even when "
              "they are marked hidden")
    elif done == "updated":
        print("Updated sitecustomize.py in .venv")
    if in_icloud(project, os.path.expanduser("~")):
        print(IN_DRIVE + ADVICE)
    elif hidden_pth(sitedir):
        print(MARKED + ADVICE)
    return 0


if __name__ == "sitecustomize":
    try:
        rescue(os.path.dirname(os.path.abspath(__file__)))
    except Exception:  # a start of Python must not fail here
        pass
elif __name__ == "__main__":
    sys.exit(main())
