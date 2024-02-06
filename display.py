# coding=utf-8
import craw_kit
from craw_kit import ColumnTool


def column_display() -> list:
    # 获取专栏列表并展示
    column_tool = ColumnTool("")
    column_tool.gen_all_chapter_names()
    column_list = column_tool.get_all_chapter_names()
    print("*********************文章列表*********************")
    simple_column_list = []
    if len(column_list) == 0:
        print("不存在专栏文章!!!")
        return
    else:
        print("{:<10}{:<30}".format("专栏编号", "文章名称"))
        for i in range(len(column_list)):
            column_name = craw_kit.simplify_column_name(column_list[i])
            simple_column_list.append(column_name)
            print("{:<10}{:<30}".format(i + 1, column_name))
    print("************************************************")
    return simple_column_list
