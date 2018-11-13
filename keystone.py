"""
Copyright 2018 Steve Theodore

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import os
import os.path
import base64
import zipfile
import re
import compileall
import argparse


PY_SHIM = '''
import sys
import os
import os.path
import runpy
import maya.cmds

try:
    melfile = os.path.abspath(sys.argv[1])
    lastmod = os.path.getmtime(melfile)
    zipfolder = maya.cmds.about(pd=True) + "/.keystone"
    zipname = zipfolder + "/" + os.path.basename(sys.argv[1]) + ".zip"
    
    print "// starting keystone launcher"

    should_update = not os.path.exists(zipname)
    if not should_update:
        should_update = os.path.getmtime(zipname) < lastmod

    if should_update:
        if not os.path.exists(zipfolder):
            os.makedirs(zipfolder)
            print "// created keystone directory"
        with open(melfile, 'rb') as binary_blob:
            print "// extracting environment from ", melfile
            binary_blob.seek(__keystone_offset)
            with open(zipname, "wb") as output:
                print "//  copy to ", zipname
                contents = binary_blob.read(40960)
                while contents:
                    output.write(contents)
                    contents = binary_blob.read(40960)
    
    sys.path.insert(0, zipname)
    print "// path inserted"
    
    if __keystone_main:
        print "// launch startup"
        runpy.run_path(zipname)

except Exception:
    import traceback
    print traceback.format_exc()
    cmds.error("Keystone boostrap failed")
'''

MEL_SHIM = '''// keystone
python("__keystone_offset = %s; __keystone_main = %i");
python("import base64; __keystone_cmd = base64.urlsafe_b64decode('%s'); exec __keystone_cmd");
'''


def zip_directory(source, zipfilename, ignore=None, include=None):

    compileall.compile_dir(source, maxlevels=24)

    archive = zipfile.ZipFile(zipfilename, 'w')

    py_re = re.compile(".py$")

    if ignore:
        ignore = re.compile(ignore)

    if include:
        include = re.compile(include)

    def iter_files():
        for root, dirs, files in os.walk(source):
            for f in files:
                fullpath = os.path.join(root, f).replace("\\", "/")
                if any(py_re.findall(fullpath)):
                    continue
                if include is not None and any(include.findall(fullpath)):
                    yield fullpath
                    continue
                if ignore is None or not ignore.findall(fullpath):
                    yield fullpath

    offset = len(source)
    try:
        for each_file in iter_files():
            archive.write(each_file, each_file[offset:])
    finally:
        archive.close()

    return zipfilename


def generate_mel(melname, folder):

    zipped = zip_directory(folder, 'keystone_temp.zip')
    encoded = base64.urlsafe_b64encode(PY_SHIM)
    has_main = os.path.exists(folder + "/__main__.py")
    mel_text = MEL_SHIM % ("%s", has_main, encoded)
    offset = len(mel_text) + 3  # get pass the
    offset += len(str(offset))
    mel_text = mel_text % str(offset)
    with open(melname, 'wt') as output:
        output.write(mel_text)
        output.write('//')

    with open(zipped, 'rb') as zipper:
        with open(melname, 'ab') as mel:
            mel.write(zipper.read())

    os.remove(zipped)


desc = '''
Compiles a python project into an executable mel file.  If the project folder
contains a __main__.py at the root level, it will be executed when the mel is launched. Any
python modules in the project folder will be added to maya's python path.
'''
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('melfile', action='store', help="path to the output mel file")
    parser.add_argument('project', action='store', help="path to the project folder")

    args = parser.parse_args()

    melfile = os.path.abspath(os.path.normpath(args.melfile))
    if not melfile.endswith(".mel"):
        melfile += ".mel"
    project = os.path.abspath(os.path.normpath(args.project))

    if not os.path.isdir(project):
        raise ValueError("'%s' is not a directory" % project)

    generate_mel(melfile, project)
