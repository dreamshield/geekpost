# coding=utf-8
import os
from PIL import Image

import pdfkit
from PyPDF2 import PdfReader, PdfMerger
from bs4 import BeautifulSoup
from loguru import logger

import network_tool
import const
import re
import shutil


def simplify_column_name(src_name) -> str:
    # /专栏/12步通关求职面试-完
    return src_name.split("/")[2]


def parse_chapter_name(src_name) -> str:
    # /专栏/Redis 核心原理与实战/01 Redis 是如何执行的.md
    return src_name.split("/")[3].split(".")[0]


def parse_chapter_name_from_file_path(file_path) -> str:
    # ./post/temp/pdf/03 Redis 持久化——RDB.pdf
    parts = file_path.split("/")
    file_name = parts[-1]
    return file_name.split(".", 1)[0]


def gen_html_save_path(chapter_name) -> str:
    simple_name = parse_chapter_name(chapter_name)
    return const.POST_SAVE_TEMP_HTML_DIR + simple_name + const.FILE_SUFFIX_HTML


def gen_pdf_save_path(chapter_name) -> str:
    simple_name = parse_chapter_name(chapter_name)
    return const.POST_SAVE_TEMP_PDF_DIR + simple_name + const.FILE_SUFFIX_PDF


def build_image_tag(img_link):
    return r'<img src="' + img_link + r'" style="width: 60%;"' + r'>'


def download_img(img_link, save_path):
    try:
        response = network_tool.get_request(img_link)
        with open(save_path, 'wb') as f:
            f.write(response.content)
    except Exception as e:
        logger.error("DownloadImgFail: imgLink={},exp={}", img_link, e)


def build_save_img_path(img_name) -> str:
    # img_name格式：assets/0d2070e8f84c4801adbfa03bda1f98d9.png
    convert_name = img_name.split("/")[1]
    simplified_name = convert_name.replace("-", "")
    return const.POST_SAVE_TEMP_IMG_DIR + simplified_name


def is_webp_image(image_path):
    try:
        img = Image.open(image_path)
        return img.format == 'WEBP'
    except Exception:
        logger.error("IsWebpImageFail: imgPath={}", image_path)
        return False


def convert_webp_to_jpeg(input_path, output_path):
    try:
        img = Image.open(input_path)
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            img = img.convert('RGB')
        img.save(output_path, 'JPEG')
        return True
    except Exception as e:
        logger.error("ConvertWebpToJpegFail: imgPath={},exp={}", input_path, e)
        return False


def gen_special_column_url(column_name) -> str:
    if len(column_name) == 0:
        return const.POST_SITE_ROOT_PATH
    else:
        return const.POST_SPECIAL_COLUMN_PATH + column_name


class ColumnTool:
    __special_column_name = ""
    __column_url = ""
    __chapter_names = []
    __html_files = []

    def __init__(self, special_column_name) -> None:
        if not os.path.exists(const.POST_SAVE_TEMP_HTML_DIR):
            os.makedirs(const.POST_SAVE_TEMP_HTML_DIR)
        self.__special_column_name = special_column_name
        self.__column_url = gen_special_column_url(special_column_name)
        self.__chapter_names = []
        self.__html_files = []
        self.__img_files = []

    def gen_all_chapter_names(self) -> None:
        # step1：爬取专题主页
        response = network_tool.get_request(self.__column_url)
        # step2：解析专题主页中的章节列表,并保存
        soup = BeautifulSoup(response.content, 'html.parser')
        ul_content = soup.find('div', class_='book-post').find('ul')
        for a in ul_content.find_all('a'):
            self.__chapter_names.append(a['href'])

    def gen_chapter_url(self, chapter_name) -> str:
        return const.POST_SITE_ROOT_PATH + chapter_name

    def get_all_chapter_names(self):
        return self.__chapter_names

    def __del__(self):
        if len(self.__html_files) > 0:
            for path in self.__html_files:
                os.remove(path)
                logger.info("PostChapterTempHtmlFileRemoved:path={}".format(path))

        if len(self.__img_files) > 0:
            for path in self.__img_files:
                os.remove(path)
                logger.info("PostChapterTempImgFileRemoved:path={}".format(path))

    def replace_src(self, chapter_name, match):
        original_src = match.group(1)

        # 边界条件检查
        if not original_src or not isinstance(original_src, str):
            logger.error("Invalid original_src: {}", original_src)
            return ""

        img_link = f"{self.__column_url}{const.DIR_SEPARATOR}{original_src}"
        # encoded_link = urllib.parse.quote(img_link, safe=":/")
        # encoded_link = img_link.replace(" ", "%20")
        # 下载图片
        img_save_path = build_save_img_path(original_src)
        if os.path.exists(img_save_path):
            logger.info("PostChapterImgExists:name={},imgLink={}", chapter_name, img_link)
        else:
            download_img(img_link, img_save_path)

        if is_webp_image(img_save_path):
            logger.info("PostChapterImgIsWebp:name={},imgLink={}", chapter_name, img_save_path)
            if convert_webp_to_jpeg(img_save_path, img_save_path):
                logger.info("PostChapterImgConvertSuccess:name={},imgLink={}", chapter_name, img_save_path)
            else:
                logger.error("PostChapterImgConvertFail:name={},imgLink={}", chapter_name, img_save_path)
        self.__img_files.append(img_save_path)
        return build_image_tag(img_save_path)

    def parse_url_to_html(self, chapter_name) -> str:
        chapter_url = self.gen_chapter_url(chapter_name)
        try:
            response = network_tool.get_request(chapter_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            # 删除广告标签
            a_tags = soup.find_all('a', text=const.AD_TAG)
            for a_tag in a_tags:
                a_tag.extract()
            # 正文
            body = soup.find_all(class_="book-post")[0]
            # 标题
            title = soup.find(class_="title").get_text()
            # 标题加入到正文的最前面，居中显示
            center_tag = soup.new_tag("center")
            title_tag = soup.new_tag('h1')
            title_tag.string = title
            center_tag.insert(1, title_tag)
            body.insert(1, center_tag)
            html = str(body)
            # body中的img标签的src相对路径的改成绝对路径
            img_pattern = re.compile(const.IMG_TAG_RE)
            html = img_pattern.sub(lambda match: self.replace_src(chapter_name, match), html)
            html = const.HTML_TEMPLATE.format(content=html)
            html = html.encode("utf-8")
            html_file_path = gen_html_save_path(chapter_name)
            with open(html_file_path, 'wb') as f:
                f.write(html)
            self.__html_files.append(html_file_path)
            print("章节:{},Html解析完成".format(parse_chapter_name(chapter_name)))
            logger.info("PostChapterHtmlSaved:name={}".format(chapter_name))
            return html_file_path
        except Exception as e:
            logger.error("HtmlParseFail: column={},chapterName={},exp={}", self.__special_column_name, chapter_name, e)


class PdfTool:
    __file_name = ""
    __chapter_pdfs = []

    def __init__(self, file_name) -> None:
        if not os.path.exists(const.POST_SAVE_DIR):
            os.makedirs(const.POST_SAVE_DIR)

        if not os.path.exists(const.POST_SAVE_TEMP_PDF_DIR):
            os.makedirs(const.POST_SAVE_TEMP_PDF_DIR)

        if not os.path.exists(const.POST_SAVE_TEMP_IMG_DIR):
            os.makedirs(const.POST_SAVE_TEMP_IMG_DIR)

        self.__file_name = file_name
        self.__chapter_pdfs = []

    def save_chapter(self, chapter_html, chapter_name) -> None:
        """
        把指定章节的html文件保存到pdf文件
        :param self:
        :param chapter_html:  指定章节html文件
        :param chapter_name: 章节名称
        :return: 对应章节pdf文件全路径
        """
        options = {
            'page-size': 'Letter',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'custom-header': [('User-Agent',
                               'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')],
            'outline-depth': 10,
            'enable-local-file-access': '',
            'no-stop-slow-scripts': '',
            'load-error-handling': 'ignore',
            'load-media-error-handling': 'ignore'
        }

        chapter_full_path = gen_pdf_save_path(chapter_name)
        pdfkit.from_file(chapter_html, chapter_full_path, options=options)
        self.__chapter_pdfs.append(chapter_full_path)
        print("章节:{},Pdf保存完成".format(parse_chapter_name(chapter_name)))
        logger.info("PostChapterPdfSaved:name={}".format(chapter_name))

    def merge_post(self) -> None:
        """
        各个章节生成的pdf文件合并为一个完整的pdf文件
        :return:None
        """
        try:
            file_merge = PdfMerger()
            for pdf in self.__chapter_pdfs:
                tag_name = parse_chapter_name_from_file_path(pdf)
                file_merge.append(PdfReader(pdf, 'rb'), outline_item=tag_name, import_outline=True)
            src_file_name = const.POST_SAVE_DIR + self.__file_name + const.FILE_SUFFIX_PDF
            with open(src_file_name, "wb") as save_fd:
                file_merge.write(save_fd)
            logger.info("WholePostSaved:postName={}".format(self.__file_name))
            target_file_name = const.GEEK_TIME_POST_DIR + self.__file_name + const.FILE_SUFFIX_PDF
            os.makedirs(os.path.dirname(const.GEEK_TIME_POST_DIR), exist_ok=True)
            shutil.copyfile(src_file_name, target_file_name)
            # 删除源文件
            os.remove(src_file_name)
        except Exception as e:
            raise Exception("MergePdfException: exception={}".format(e))

    def __del__(self) -> None:
        """
        移除章节pdf临时文件
        :return:None
        """
        if len(self.__chapter_pdfs) > 0:
            for path in self.__chapter_pdfs:
                os.remove(path)
                logger.info("PostChapterTempPdfFileRemoved:path={}".format(path))
