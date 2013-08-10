import wx.tools.img2py as img2py
import getopt
import sys
import os
import os.path

def usage():
    print """
%s [-d directory][-h] -o outputfile files
""" % sys.argv[0]

def main():
    if len(sys.argv) == 1:
        usage()
        sys.exit(1)
    try:
        opts, fileArgs = getopt.getopt(sys.argv[1:], "d:o:h")
    except getopt.GetoptError:
        usage()
        sys.exit(1)

    imagedir = ''
    outputfile = ''
    for opt, val in opts:
        if opt == "-h":
            usage()
            sys.exit(1)
        elif opt == "-d":
            imagedir = val
        elif opt == "-o":
            outputfile = val

    convert(outputfile, imagedir, fileArgs)

def isImageFile(filename):
    f, ext = os.path.splitext(filename)
    if os.path.isfile(filename) and ext.lower() in ('.gif', '.png', '.bmp', '.jpg', '.ico'):
        return True
    else:
        return False
            
def convert(outputfile, dir='', imagefiles=[]):
    files = []
    files.extend(imagefiles)
    if dir:
        f = [os.path.join(dir, x) for x in os.listdir(dir) if os.path.isfile(os.path.join(dir, x))]
        files.extend(f)
    files = list(set([x for x in files if isImageFile(x)]))
    for i, x in enumerate(files):
        name = os.path.splitext(os.path.basename(x))[0].lower()
        cmd =[]
        if i != 0:
            cmd.append('-a')
        cmd.append('-n')
        cmd.append(name.capitalize())
        cmd.append(x)
        cmd.append(outputfile)
        os.system("python e:\\devtools\img2py.py %s" % " ".join(cmd)) 
        print name.capitalize(), outputfile
        img2py.img2py(x, outputfile)
if __name__ == '__main__':
    main()

