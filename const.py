# coding=utf-8

POST_SAVE_DIR = "./post/"
POST_SAVE_TEMP_PDF_DIR = POST_SAVE_DIR + "temp/pdf/"
POST_SAVE_TEMP_HTML_DIR = POST_SAVE_DIR + "temp/html/"

FILE_SUFFIX_PDF = ".pdf"
FILE_SUFFIX_HTML = ".html"
FILE_SUFFIX_MD = ".md"

DIR_SEPARATOR = "/"

POST_SITE_ROOT_PATH = "https://learn.lianglianglee.com/"
POST_SPECIAL_COLUMN_PATH = POST_SITE_ROOT_PATH + "专栏/"

IMG_TAG_RE = r'<img.*?src="(.*?)".*?>'

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
</head>
<body>
{content}
</body>
</html>
"""

AD_TAG = "阿里云2C2G3M 99元/年，老用户也可以哦"

GEEK_TIME_POST_DIR = "~/Documents/Tech/GeekTime/"

