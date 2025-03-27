import os
import shutil

import const

file_name = ""
src_file_path = f'{const.POST_SAVE_DIR}{file_name}'
target_file_path = const.GEEK_TIME_POST_DIR + file_name.replace(".pdf", "") + const.FILE_SUFFIX_PDF
os.makedirs(os.path.dirname(const.GEEK_TIME_POST_DIR), exist_ok=True)
shutil.copyfile(src_file_path, target_file_path)