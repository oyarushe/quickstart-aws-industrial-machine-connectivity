
import re
import codecs

split_char = '-'
def parse_file_name(s3_file):
    site_name = 'default'
    server_name = 'default'
    file_name = s3_file.split('/')[-1]

    matched = re.match(".+{}.+{}.+\..+".format(split_char, split_char), file_name)
    if (bool(matched)):
        site_name, server_name = file_name.split(split_char)[:2]

    return site_name, server_name, file_name

def check_for_bom(filename):
    with open(filename, 'rb') as binFile:
        rawData = binFile.read(64)
        if rawData.startswith(codecs.BOM_UTF8):
            return True

    return False
