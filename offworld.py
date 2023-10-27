#!/usr/bin/env python3
"""
Offworld manages git repositories where the files are dispursed across a filesystem. Useful for
storing configs without accidently leaking secrets
"""
import json
import os
import sys
import shutil
import subprocess

# Not currently changeable
OFFFILE = ".offworld"

# user is expecting git (alias or other) and offworld is running instead
_, f = os.path.split(sys.argv[0])
GITMODE = f == "git"

HOME_DIR = os.path.expanduser("~")

class File:
    """
    A basic class that represents a file tracked by offworld
    """
    def __init__(self, src):
        # Name - What the file is called in offworld
        # DiskName - Where the file is stored on disk
        # RepoName - Where the file is stored in the repo
        if src.startswith(HOME_DIR):
            self.Name = src.replace(HOME_DIR, "~")
        elif src.startswith("~/"):
            self.Name = src
        else:
            self.Name = os.path.abspath(src)

        if self.Name.startswith("~/"):
            self.RepoName = self.Name.replace("~", "offworld/_home_", 1)
        else:
            self.RepoName = os.path.join("offworld", self.DiskName().lstrip(os.path.sep))

    def DiskName(self) -> str:
        if self.Name.startswith("~/"):
            return os.path.join(HOME_DIR, self.Name[2:])
        return os.path.abspath(self.Name)

    def Save(self):
        """Save the file to disk"""
        dst = self.DiskName()
        dst_dir, _ = os.path.split(dst)
        os.makedirs(dst_dir, exist_ok=True)
        with open(dst, "wb") as f:
            with open(self.RepoName, "rb") as inf:
                f.write(inf.read())

    def Load(self):
        """Load the file into the repo"""
        src = self.DiskName()
        dst_dir, _ = os.path.split(self.RepoName)
        os.makedirs(dst_dir, exist_ok=True)
        shutil.copy2(src, self.RepoName)
        run(["git", "add", self.RepoName])

    def Protected(self) -> bool:
        return not os.access(self.DiskName(), os.W_OK)
    
    def Exists(self) -> bool:
        f = self.DiskName()
        if not os.path.isfile(f):
            return False
        if not os.access(f, os.R_OK):
            return False
        return True
    
def run(args, shell=False, **kwargs):
    global GITMODE
    # Find the actual git installation incase we are running as git
    if GITMODE:
        pth = os.environ.get("PATH")
        if pth:
            for p in pth.split(":"):
                actual_git = os.path.join(p, "git")
                if os.path.exists(actual_git) and not actual_git == __file__:
                    args[0] = actual_git
    my_args = {
        "shell": shell,
        "stdin": sys.stdin,
        "stdout":sys.stdout,
        "stderr":sys.stderr,
    }
    my_args.update(kwargs)
    return subprocess.call(args, **my_args)

def save(s):
    with open(OFFFILE, "w") as f:
        json.dump(s, f, indent=2)
    run(["git", "add", OFFFILE])

def usage():
    if GITMODE:
        run(["git"])
        print("\nOffworld commands:")
    else:
        print("usage: offworld <command> or pass any git commands")
        print("\nCOMMANDS")
    print("  track <files>\t\tTrack the files using offworld")
    print("  status\t\tShow status off offworld files")
    print("  sync\t\t\tSync all the files to their on-disk location")

def parse():
    global GITMODE

    if len(sys.argv) == 1:
        usage()
        exit(0)
    
    SOURCES = {}
    if os.path.exists(OFFFILE):
        with open(OFFFILE) as f:
            SOURCES = json.load(f)

    if not os.path.isdir(".git") and sys.argv[1] in ("track", "sync"):
        # Calling an offroad command but not in a git directory
        print("not in a git directory", file=sys.stderr)
        GITMODE = False
        usage()
        exit(1)
    
    # TRACK - Add a file to offworld
    if sys.argv[1] == "track":
        if len(sys.argv) < 3:
            usage()
            exit(1)
        
        # Make sure files exist
        for f in sys.argv[2:]:
            if not os.path.isfile(f):
                print("ERROR cannot track non-existent file: " + f, file=sys.stderr)
                exit(1)
            if not os.access(f, os.R_OK):
                print("ERROR cannot track non-readable file: " + f, file=sys.stderr)
                exit(1)

        # Add the following files to the git repo
        print("tracking files in offworld:", sys.argv[2:])
        for f in sys.argv[2:]:
            f = File(f)
            if f.Protected():
                print("WARNING file cannot be written to, offworld will not attempt to write")
            
            SOURCES[f.Name] = f.Protected()
            f.Load()
            run(["git", "add", f.RepoName])
        save(SOURCES)
        return

    # SYNC - Save the files back to the source on system
    if sys.argv[1] == "sync":
        # force the files back into the system
        for f, protected in SOURCES.items():
            f = File(f)
            if not protected:
                try:
                    f.Save()
                    print(f"synced {f.RepoName} -> {f.Name}")
                except Exception as e:
                    print(f"ERROR writing {f.Name}: {e}")
                    exit(1)
        return
    
    # STATUS - more of a psuedo command, we were going to sync either way, just force
    # git to be called if not
    if sys.argv[1] == "status":
        GITMODE = True
        sys.argv[0] = "git"

    # If we made it here, we are in an offworld dir. Refresh the files in the repo
    for f in SOURCES.keys():
        f = File(f)
        f.Load()

    # Call git?
    if GITMODE:
        exit(run(sys.argv))

if __name__ == '__main__':
    parse()