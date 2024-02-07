# coding=utf-8
import os

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
    return file_path.split("/")[4].split(".")[0]


def gen_html_save_path(chapter_name) -> str:
    simple_name = parse_chapter_name(chapter_name)
    return const.POST_SAVE_TEMP_HTML_DIR + simple_name + const.FILE_SUFFIX_HTML


def gen_pdf_save_path(chapter_name) -> str:
    simple_name = parse_chapter_name(chapter_name)
    return const.POST_SAVE_TEMP_PDF_DIR + simple_name + const.FILE_SUFFIX_PDF


def build_image_tag(img_link):
    return r'<img src="' + img_link + r'" style="width: 60%;"' + r'>'


def gen_special_column_url(column_name) -> str:
    if len(column_name) == 0:
        return const.POST_SITE_ROOT_PATH
    else:
        return const.POST_SPECIAL_COLUMN_PATH + column_name;


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

            def replace_src(match):
                original_src = match.group(1)
                img_link = self.__column_url + const.DIR_SEPARATOR + original_src
                return build_image_tag(img_link)

            html = img_pattern.sub(replace_src, html)
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
            'custom-header': [
                ('Accept-Encoding', 'gzip')
            ],
            'outline-depth': 10,
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
            save_file_name = const.POST_SAVE_DIR + self.__file_name + const.FILE_SUFFIX_PDF
            save_fd = open(save_file_name, "wb")
            file_merge.write(save_fd)
            logger.info("WholePostSaved:postName={}".format(self.__file_name))
            shutil.copyfile(save_file_name, const.GEEK_TIME_POST_DIR + self.__file_name + const.FILE_SUFFIX_PDF)
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
