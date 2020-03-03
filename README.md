# keystone
A pipeline shim that compiles maya python project into a single executable mel file

Many teams end up with dedicated launchers — either dedicated applications or just .BAT files — whose job it is to configure maya on startup. For example you might keep parallel userSetup/code combinations in different locations and then launch Maya with an .BAT that manipulates sys.path or PYTHONPATH to get the right version to the top of the list. These kinds of systems work reasonably well, although they also complicate your support structure — when you’re trying to add a new artists to the team you need to train them out of just launching Maya from the applications menu, and if you’re supporting outsources or partner studios you need to distribute the launcher infrastructure as well as the code that does the actual work.

The goal of *Keystone* is to let you distribute a toolkit that’s:

* *Easy to activate* It won’t require me to fire up a different program just to use the one I want to use.
* *A good citizen* It doesn’t force me to reorganize my Maya install (particularly if I’m an outsource who might only be using this toolkit for a few weeks!).
* *Install Free* It doesn’t demand a separate installer or a plugin or anything else I don’t already have.
* *Fully functional*  It doesn’t compromise the depth of what you’re delivering just in order to make it easy to deliver.

The first three are actually surprisingly easy. After all, Maya has always has it’s own dedicated script file type — you can always double-click or drag-and-drop a mel file and it will just work. No installation, not configuration, not even any special rules about where the file has to be. You can mail somebody a MEL file and they can just run it from their downloads folder.

Alas, it works in MEL. Which is to say, it’s going to be an uphill battle to make it hit that last bullet point and be fully functional. And how much power can you really pack into a single MEL file?


## Enter Keystone

Keystone is a command line script that you point at a folder which contains your Python toolkit. It will compile all of the Python files to .pyc for speed and then zip them up into a single archive. Then, it will generate a startup script to find an launch the zipped-up toolkit. Finally it will compile that startup script and the binary data from the zip file into a double-clickable MEL file — a single-source distribution of the whole shebang which doesn’t need any extra infrastructure.

The only ‘complexity’ — it barely deserves the name — is the way in which the zip file data is jammed into the MEL file. This amounts to simply generating a zip file, reading it in as binary bytes, and appended those bytes to the end of the MEL file after a comment mark so that Maya doesn’t try to read them. The offset where the comment begins is encoded into the script so that it’s eay to grab the relevant bits and put them back on the user’s hard drive as ordinary zip files.

The Keystone compiler automatically generates the code to add the zip file onto the Python path (this script is encoded using base64 to avoid syntax issues). When the user runs the MEL file it hands execution over to this startup code. The startup script checks to make see if there’s already a zip that matches the data stuffed into the MEL file. If there’s no script (or if there is a zip which is older than the MEL file) the startup code will extract the hidden binary data from the MEL and save it.  Currently it’s getting stashed in the Maya user directory, in a folder named ".keystones" with subfolders for each Keystone mel file.

The MEL file’s startup code adds the zip to the Python path, launches Maya with the new zip as the first item on the Python path, and then executes any startup code you’ve included in the zip file — you can put any initialization you want into the zip as a __main__.py and it will get fired off in the same way that an ordinary Maya session executes userSetup.py. 

The upshot of all this is, hopefully, a complete Maya Python environment in a single file — as many modules and scripts as you need, but without the need for tools in other languages to get it plugged into a given Maya session. It’s MEL and Python, so it’s cross-platform (no need to translate .BATS into shell scripts for OSX or Linux). You can distribute this file through Perforce or a download link or simply by emailing it to one contractor; no matter how that file lands on their desk it should give them a complete environment. If you need to give them an update you simply replace that one file and the rest follows naturally.

## Compiling a python environment for keystone
See `keystone.py` for the details, but essentially it's this:

```
usage: keystone.py [-h] [--script] melfile project

Compiles a python project into an executable mel file. If the project folder
contains a __main__.py at the root level, it will be executed when the mel is
launched. Any python modules in the project folder will be added to maya's
python path.

positional arguments:
  melfile     path to the output mel file
  project     path to the project folder or script

optional arguments:
  -h, --help  show this help message and exit
  --script    if true, compile a single python file instead of a folder
```

## Launching a keystone environment
These are equivalent:

1. double-click the mel file (assuming your mel files are associated with maya)
2. `path\to\maya.exe` `path\to\keystone.py.mel`
3. `path\to\maya.exe -script path\to\keystone.py.mel`

Note that if you use the `-script` flag you have to pass an absolute path to the file.  

## Future work

Of course, all tech involves tradeoffs and I’m still trying to learn what the tradeoffs in this approach will be. The most obvious issue is that there’s the data in the zip portion of the package ends up getting duplicated. My work toolkit zips up about 25 mb, so the overhead is far from trememndous, but it would be nicer if there were a good way around that. 

A more annoying issue is the need to extract any binary tools (such as the P4Python module) from the zip file — Python currently won’t read compiled extensions out of a zip which is irritating though easy to get around by extracting binaries to the same ".keystones" folder where the zip itself lives.


