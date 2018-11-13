import os
import os.path
import base64
import zipfile
import re

PY_SHIM = '''
import sys
import os
import os.path
location = os.path.dirname(sys.argv[1])
lastmod = os.path.getmtime(location)
zipname = sys.argv[1] + ".zip"

if not (os.path.exists (zipname)) or os.path.getmtime(zipname) < lastmod:
    print "UNZIPPING"
    with open(sys.argv[1], 'rb') as melfile:
        melfile.seek(__keystone_offset)
        with open(zipname, "wb") as output:
            contents = melfile.read(4096)
            while contents:
                output.write(contents)
                contents = melfile.read(4096)
import runpy
sys.path.append(zipname)
if __keystone_main:
    runpy.run_path(zipname)

'''

MEL_SHIM = '''// keystone
python("__keystone_offset = %s; __keystone_main = %i");
python("import base64; __keystone_cmd = base64.urlsafe_b64decode('%s'); exec __keystone_cmd");
'''


def zip_directory(source, zipfilename, ignore=None, include=None):
    archive = zipfile.ZipFile(zipfilename, 'w')
    if ignore:
        ignore = re.compile(ignore)

    if include:
        include = re.compile(include)

    def iter_files():
        for root, dirs, files in os.walk(source):
            for f in files:
                fullpath = os.path.join(root, f).replace("\\", "/")

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

    zipped = zip_directory(folder, 'temp.zip')
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


if __name__ == '__main__':
    generate_mel("fred.mel", "example")
