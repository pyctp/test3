#encoding:utf-8
#http://www.cnblogs.com/WeyneChen/p/6339962.html
import chardet
import sys
import codecs
import os


def findEncoding(s):
    file = open(s, mode='rb')
    buf = file.read()
    result = chardet.detect(buf)
    file.close()
    return result['encoding']


def convertEncoding(s):
    if  os.access(s,os.W_OK):
        encoding = findEncoding(s)
        if encoding != 'utf-8' and encoding != 'ascii':
            print("convert %s%s to utf-8" % (s, encoding))
            contents = ''
            with codecs.open(s, "r", encoding) as sourceFile:
                contents = sourceFile.read()

            with codecs.open(s, "w", "utf-8") as targetFile:
                targetFile.write(contents)

        else:
            print("%s encoding is %s ,there is no need to convert" % (s, encoding))
    else:
        print("%s read only" %s)


def getAllFile(path, suffix='.'):
    "recursive is enable"
    f = os.walk(path)
    fpath = []

    for root, dir, fname in f:
        for name in fname:
            if name.endswith(suffix):
                fpath.append(os.path.join(root, name))

    return fpath


def convertAll(path):
    fclist = getAllFile(path, ".c")
    fhlist = getAllFile(path, ".h")
    fplist = getAllFile(path, ".py")
    flist = fclist + fhlist + fplist
    for fname in flist:
        convertEncoding(fname)


if __name__ == "__main__":
    # 可以指定目录，也可以在当前目录下用，递归遍历。
    path = ''
    if len(sys.argv) == 1:
        path = os.getcwd()

    elif len(sys.argv) == 2:
        path = sys.argv[1]
    else:
        print("error parameter")
        exit()

    convertAll(path)