![Offworld](./logo.png)

_Manage out-of-repo files with git_  


Offworld lets you add files to git that are "not in the repo". Offworld wil reach out
and collect the files from the system and push them back if needed.

## Installation
Offworld is a single python script which is _best_ installed overtop of `git`. This will allow
offworld to sync the files every time a git command is run. You may use Offworld as an independent tool as well but ymmv.

### Method 1
```bash
git clone git@github.com:micahjmartin/Offworld.git
cp Offworld/offworld.py ~/.local/bin/git
```

### Method 2
```bash
git clone git@github.com:micahjmartin/Offworld.git
cp Offworld/offworld.py ~/.local/bin/offworld
echo "alias git=offworld" >> ~/.bashrc
```

## Usage
For any files that you want to track, add them to offworld
```
git track /etc/ssh/sshd_config
# Now call git commands as normal. Offworld will add and track the files as they are updated
git status
```

To push repo changes back to the origin directory, run a `sync` command

```bash
git sync
# OR
sudo git sync # CAREFUL WHAT YOU OVERWRITE
```

## Reasoning
Why does offworld exist? I wanted to manage system and local configs in a single repo without having to worry about symlinks, information leakage, or manually copying files around.