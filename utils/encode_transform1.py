#encoding:utf-8
# http://www.cnblogs.com/WeyneChen/p/6339962.html
import chardet
import sys
import codecs


def findEncoding(s):
    file = open(s, mode='rb')
    buf = file.read()
    result = chardet.detect(buf)
    file.close()
    return result['encoding']


def convertEncoding(s):
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


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("error filename")
    else:
        convertEncoding(sys.argv[1])