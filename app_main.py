# coding=utf-8
import time

import craw_kit
import display
import log_config
from loguru import logger

if __name__ == '__main__':
    log_config.log_config()
    # 展示所有专栏文章
    column_list = display.column_display()
    if len(column_list) != 0:
        # 选择对应的专栏，并生成pdf文件
        column_num = input("输入想要生成本地文档的专栏编号:")
        index = int(column_num) - 1
        column_name = column_list[index]
        print("输入的专栏编号是：{}，专栏名称是：{}".format(column_num, column_name))
        choice = input("请确认(Y/N)：")
        if choice == "N":
            print("已退出，Bye!")
        else:
            print("专栏文章:{}处理中请稍后...".format(column_name))
            try:
                html_tool = craw_kit.ColumnTool(column_name)
                pdf_tool = craw_kit.PdfTool(column_name)
                html_tool.gen_all_chapter_names()
                chapter_names = html_tool.get_all_chapter_names()
                if len(chapter_names) > 0:
                    for chapter_name in chapter_names:
                        chapter_html_file = html_tool.parse_url_to_html(chapter_name)
                        pdf_tool.save_chapter(chapter_html_file, chapter_name)
                        time.sleep(5)
                    pdf_tool.merge_post()
                    logger.info("专栏文章:{}处理完成.".format(column_name))
                    print("专栏文章:{}处理完成.".format(column_name))
            except Exception as e:
                print("专栏文章:{}处理异常且已退出,exp={}.".format(column_name, e))
    else:
        print("已退出!")
