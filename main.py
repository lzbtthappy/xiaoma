#2023-2-16 对原批卷软件进行修改。
# 1--原来批1页改为批多页。
# 2--原来需要把练习纸正反面整理好，再进行扫描，改为不需要整理练习纸正反面和上下头，直接扫描，并打印。
# 3--改进原来的条码信息中包含某次练习信息，改为只包含学生学籍号，这样条码可以用不同的练习纸上。
# 4--对于识别不到的练习纸进行标注张次，并显示扫描稿，人工输入学号等方法解放困难，不成功的并标注张次
# 5--把轮廓线文件存储在mysql里。
# 6--增加练习纸内容标注。

import PySimpleGUI as psg   # 导入PySimpleGUI模块
import lzbfun
import os
import cv2 as cv
import numpy as np
from PIL import Image, ImageWin, ImageDraw, ImageFont
import win32print   #打印用
import win32ui      #打印用
#from PIL import Image, ImageWin  打印用
import time
import global_var       #用于公共变量
# from multiprocessing import Pool,Manager,cpu_count
import multiprocessing
#Pool用于进程池,Manager用于共享数据,cpu_count 用于获取计算机CPU核数
import pandas as pd

#多进程回调函数，把数据写入df对象中().
#返回的数据情况如果img_a和img_b都存在返回((student_code,exam_page,tt_info),(student_code,exam_page,tt_info))
#如果img_a或img_b存在返回(student_code,exam_page,tt_info)
#img_a和img_b都不存在返回False
#df=pandas.DataFrame(columns=['stu_code','page','tt_info'])
#用df.loc[df.shape[0]] = list(result)
#用df.shape[0]) 获取索引
def workercallback(return_data):
    #return_data中'stu_code' is str ,'page' is num,'tt_info' is str
    print("workercallback......return_data==", return_data)
    if   len(return_data)==2:     #有2条记录
        df_data.loc[df_data.shape[0]] = list(return_data[0])
        df_data.loc[df_data.shape[0]] = list(return_data[1])
    elif  len(return_data)==3:    #有1条记录
        df_data.loc[df_data.shape[0]] = list(return_data)
    elif  return_data==False:     #是空白页,无记录
        pass

global_var._init()      #已放弃

if __name__ == '__main__':
    psg.theme('BluePurple')  # 首先设置窗口样式
    # 1)菜单
    menu_def1 =['初始化', ['名单维护',["名单导入","名单删除","名单修改"], '扫描特征设置','Exit']]
    menu_def2 =['新建练习',['新建练习','删除练习', '修改练习'] ]
    menu_def3 =['批阅作业', ['打印批阅结果']]
    menu_def4 =['查看作业信息',['查看基本信息', '查看学生成绩']]
    menu_def5 =['help',['使用手册', 'About...']]
    layout= [
     [psg.ButtonMenu('初始化',menu_def1,key='-BMENU1-',border_width="3",size=(6, 1),tearoff=False,font=("微软雅黑", 22)),
     psg.ButtonMenu('新建练习', menu_def2, key='-BMENU2-',border_width="3",size=(8, 1),font=("微软雅黑", 22)),
      psg.ButtonMenu('批阅作业', menu_def3, key='-BMENU3-',border_width="3",size=(8, 1),font=("微软雅黑", 22)),
      psg.ButtonMenu('查看作业信息', menu_def4, key='-BMENU4-',border_width="3",size=(11, 1),font=("微软雅黑", 22)),
      psg.ButtonMenu('help', menu_def5, key='-BMENU5-',border_width="3",size=(5, 1),font=("微软雅黑", 22))
      ],]
    # 2) 定义布局，确定菜单， 以及每个菜单下面界面
    exam_title_id=lzbfun.download_exam_title_id()
    exam_title_list = [item[0] for item in exam_title_id]
    window = psg.Window('小马批作业', layout, size=(1200, 800),font=("微软雅黑", 22),
                        grab_anywhere=True, resizable=True)

    # 4) 添加事件处理，事件循环
    while True:
        event, values = window.read()
        if event == None:  # 窗口关闭事件
            break  # 退出循环
        if event == '-BMENU2-' and values['-BMENU2-'] == '新建练习':
            print('你点击了', event, '菜单', values[event])
            folder_path = psg.popup_get_folder('请选择练习扫描稿所在文件夹', title='新建练习', font=("微软雅黑", 20))
            # 如果按确定键继续下面，如果按“conle”键退回到主菜单，需改进
            # print(folder_path)
            # Folder_path = lzbfun.Folder_path(folder_path)
            # Folder_path.del_Null_file()  # 删除空白页
            # exam_total_page = Folder_path.get_total_page()  # 总页数
            #删除空白文档，并按页脚从小到大排序文件名（带URL)
            exam_file_list = lzbfun.sort_foot_files(folder_path)
            exam_total_page=len(exam_file_list)
            #生成学生代码区域轮廓组
            # stu_code_cnts=lzbfun.get_stu_code_mask(exam_file_list)
            exam_title = lzbfun.get_exam_title(exam_file_list)  # 获取练习标题
            # 练习的正确答案
            layout1 = [[psg.Text('本次练习名称为'), psg.In(default_text=exam_title, key='-input-1-1-'),
                        psg.Text('共 ' + str(exam_total_page) + ' 页')],
                       [psg.Text('输入练习的正确答案'), psg.In(key='-input-1-2-')],
                       [psg.Button("确定", key='-button-1-1-', enable_events=True, visible=True),
                        psg.Button("取消", key='-button-1-2-', enable_events=True, visible=True)]
                       ]
            window1 = psg.Window('新建练习', layout1, finalize=True, font=("微软雅黑", 22),return_keyboard_events=True)
            window1['-input-1-2-'].set_focus()
            window1_active = True
            window.Hide()
            psg_ENTER_KEY1 = 'special 16777220'
            psg_ENTER_KEY2 = 'special 16777221'
            while True:
                event1, values1 = window1.read()
                if event1 == psg.WIN_CLOSED or event1 == 'Exit' or event1 == '-button-1-2-':
                    window1.close()
                    window1_active = False
                    window.UnHide()
                    break
                if event1 == '-button-1-1-' or  event in ('\r', psg_ENTER_KEY1, psg_ENTER_KEY2):  # 按下确定键或回车键
                    exam_name = values1['-input-1-1-']  # 练习名称
                    correct_answer = values1['-input-1-2-']  # 正确答案
                    # correct_answer=lzbfun.to_H_answer(correct_answer)
                    # print(exam_name, correct_answer)

                    # 把数据上传练习标题、总页数、答案二进制到数据表exam_conc_info中
                    lzbfun.upload_exam_conc_data(exam_title, exam_total_page, correct_answer)
                    window1.close()
                    window1_active = False
                    # 显示各填涂选项的轮廓线，并确认,23-7-6
                    # exam_file_list = Folder_path.get_url_file()
                    # 存储page_num,foot_text,cnt的字典
                    page_num_foot_img_cnt = {}
                    for filename in exam_file_list:
                        # 获取图像image
                        exam_file = lzbfun.Imgfile(filename)
                        page_img, page_alpha, _, _ = exam_file.get_img_and_alpha_and_xy_ba()
                        # 获取页脚文本，页数，确认后的轮廓线
                        page_num, page_foot = exam_file.get_exam_page_and_foot()
                        cnts = exam_file.mark_option_cnts()
                        lzbfun.upload_exam_detail_data(page_num, filename, page_foot, cnts)
                    window.UnHide()
                    lzbfun.update_page_answ()
                    break
        if event=='-BMENU3-' and values['-BMENU3-'] == '打印批阅结果':
            print('你点击了', event, '菜单', values[event])
            print('---------开始打印----------')
            time_a = time.time()
            # 设置共享数据字典，变量名shared_id_page_cnt_answ，用于id为键
            # 设置共享数据列表，shared_id_stucode_page_ttinfo,用于存储每页批改为的信息,
            # 2023-12-26改为由df对象存储
            # df对象由文件名\id\stucode\page\ttinfo组成
            lzbfun.delete_temp_file()
            # 获取文件夹路径
            folder_path = psg.popup_get_folder('请选择学生练习扫描稿所在文件夹', title='批阅作业', font=("微软雅黑", 20))
            exam_file_list = lzbfun.get_url_file(folder_path)  # 获取排序后的文件名,带URL
            # 创建df对象,列标签需要考虑2024-1-11
            # (img_a_filename,exam_id,student_code,img_a_page,img_a_tt_info,img_a_right_num)
            df_data = pd.DataFrame(columns=['stu_code', 'page', 'tt_info'])
            # 创建共享数据字典
            manager = multiprocessing.Manager()
            # print('main144行代码已执行')
            exam_id = lzbfun.get_this_exam_id(exam_file_list)
            print('main145行代码已执行，exam_id=', exam_id)
            page_cnt_answ = lzbfun.generate_page_cnt_answ(exam_id)
            # print('page_cnt_answ类型=',type(page_cnt_answ))
            print(page_cnt_answ[0][0],page_cnt_answ[0][2])
            print(page_cnt_answ[1][0], page_cnt_answ[1][2])
            print(page_cnt_answ[2][0], page_cnt_answ[2][2])
            d = {exam_id: page_cnt_answ}
            shared_data_dict = manager.dict(d)
            # 创建子进程
            # with multiprocessing.Pool(processes=5) as pool:
            #     for i in range(0, len(exam_file_list), 2):
            #         # Pool().apply_async(要调用的目标,(传递给目标的参数元祖,))
            #         # 每次循环将会用空闲出来的子进程去调用目标
            #         pool.apply_async(lzbfun.worker,
            #                          args=(exam_file_list[i], exam_file_list[i + 1], shared_data_dict),
            #                          callback=lzbfun.workercallback)
            #         # print("进程", os.getpid(), "开始参数is", exam_file_list[i], exam_file_list[i + 1],  )
            #     # 关闭进程池并等待所有任务完成
            #     pool.close()
            #     pool.join()
            pool = multiprocessing.Pool(processes=5)
            print('main160行代码已执行')
            for i in range(0, len(exam_file_list), 2):
                pool.apply_async(lzbfun.worker, args=(exam_file_list[i], exam_file_list[i + 1], shared_data_dict),
                                 callback=workercallback)
            # print("进程", os.getpid(), "开始参数is", exam_file_list[i], exam_file_list[i + 1],  )
            # 关闭进程池并等待所有任务完成
            pool.close()
            pool.join()
            print("所有子进程已完成。")
            print(df_data)

            # 子进程结束，对(".\\printdoc")文件夹中带pri的文件进行处理
            # 根据文件名中的stu_code，统计df中个数是否==totle_page,Yes,计算总分；
            # No，则从数据库中查找，返回后查找结果，合并，计算总分。
            # 总分添加到打印文稿中
            # 设置字体和字号
            font = cv.FONT_HERSHEY_SIMPLEX
            font_size = 4
            printdoc_file_list = os.listdir(".\\printdoc")
            for file in printdoc_file_list:
                if file.startswith("pri"):
                    img = cv.imread('.\\printdoc\\' + file)
                    split_file_name = file.split("_")
                    if split_file_name[1] == "alpha":
                        file_stu_code = split_file_name[2]
                        alpha = 1
                        img = cv.rotate(img, cv.ROTATE_180)
                        stare_cut = len(split_file_name[0] + split_file_name[1] + split_file_name[2]) + 3
                    else:
                        file_stu_code = split_file_name[1]
                        alpha = 0
                        stare_cut = len(split_file_name[0] + split_file_name[1]) + 2
                    print_filename = file[stare_cut:]
                    # 在df中获取列标签'stu_code'=file_stu_code
                    # df=pandas.DataFrame(columns=['stu_code','page','tt_info'])
                    if df_data[df_data.stu_code == file_stu_code].stu_code.count() == len(page_cnt_answ):
                        # 计算总分
                        # 获取page_cnt_answ中的正确答案
                        correct_answ = ''.join(map(lambda x: x[2], page_cnt_answ))
                        df_data1 = df_data[df_data.stu_code == file_stu_code].sort_values(by='page')

                        # print(df1)
                        my_tt_info = ''.join(df_data1['tt_info'].apply(lambda x: str(x)))
                        # print(my_tt_info)
                        count = sum(1 for a, b in zip(my_tt_info, correct_answ) if a == b)
                        score = int(count / len(correct_answ) * 100 + 0.5)
                    else:  # 如果数据不健全，去数据库中找

                        pass
                    # 添加文字
                    cv.putText(img, str(score), (1900, 400), font, font_size, (0, 0, 255), 3)
                    if alpha == 1:
                        img = cv.rotate(img, cv.ROTATE_180)
                    cv.imwrite('.//printdoc//' + print_filename, img)

            # 如果按确定键继续下面，如果按“conle”键退回到主菜单，需改进
            # print(folder_path)
            # std_folder_path=lzbfun.Folder_path(folder_path)
            # exam_total_page=Folder_path.get_total_page()   #总页数
            # if global_var.get_value("exam_id") == False:
            #     exam_id = lzbfun.get_this_exam_id(exam_file_list)
            #     global_var.set_value("exam_id", exam_id)
            # 获取exam_id
            # 获取相应的page_cnt_answ
            # if global_var.get_value(exam_id) == False:
            #     exam_id = lzbfun.get_this_exam_id(exam_file_list)
            #     page_cnt_answ = lzbfun.generate_page_cnt_answ(exam_id)
            #     global_var.set_value(exam_id, page_cnt_answ)
            # page_cnt_answ = global_var.get_value(exam_id)
            # total_page=len(page_cnt_answ)   #1个练习的总页数

            # exam_id = lzbfun.get_this_exam_id(exam_file_list)
            # page_cnt_answ = lzbfun.generate_page_cnt_answ(exam_id)
            # print("main中page_cnt_answ长度",len(page_cnt_answ))
            # shared_id_page_cnt_answ[exam_id]=page_cnt_answ
            # print("main中shared_id_page_cnt_answ长度",len(shared_id_page_cnt_answ))
            # #return (img_a.self, exam_id, student_code, img_a_page, img_a_tt_info, img_a_right_num)
            # df=pandas.DataFrame(columns=['filename', 'exam_id', 'stu_code', 'exam_page','tt_info','correct_num'])

            # 多进程编程begin
            # 排序后的文件序列开始
            # print(exam_file_list)
            # # multiprocessing.cpu_count()
            # pool = Pool(cpu_count())    #此处cpu_count()需核实
            # for i in range(0, len(exam_file_list),2):
            #     # Pool().apply_async(要调用的目标,(传递给目标的参数元祖,))
            #     # 每次循环将会用空闲出来的子进程去调用目标
            #     pool.apply_async(lzbfun.worker, args=(exam_file_list[i],exam_file_list[i+1],shared_id_page_cnt_answ),callback=lzbfun.workercallback)
            #     # print("进程", os.getpid(), "开始参数is", exam_file_list[i], exam_file_list[i + 1],  )
            #
            # # 关闭进程池，关闭后pool不再接收新的请求
            # pool.close()
            # pool.join()
            # print('子进程结束==')

            # 把df中数据上传到数据库
            # df中数据 ['filename', 'exam_id', 'stu_code', 'exam_page', 'tt_info', 'correct_num']
            # 上传数据库需要的数据，stu_code,exam_id,tt_info,choice,score,date
            # 合并数据，

            # exam_file_list原来的练习扫描稿文件，带有URL,
            # 去除URL,把文件扩展名改为jpg
            stare_index = exam_file_list[0].rfind("//")
            last_index = exam_file_list[0].rfind(".")

            new_file_list = [s[stare_index + 2:last_index] + ".jpg" for s in exam_file_list]
            # 只有文件名，不带URL
            list_a = [x for x in range(0, len(new_file_list), 2)]
            list_b = [x for x in range(1, len(new_file_list), 2)]
            # 开始打印0，2，4页文稿,1，3，5页文稿
            # time.sleep(100)
            # for i in list_a + list_b:
            # lzbfun.image_printout(i)   #该函数不需要路径

            time_b = time.time()
            print("打印耗时：", time_b - time_a)
            print('---------打印完成----------')
            # 打印完成后，上传exam_id,stu_code,tt_info数据到数据库，并计算总分
            lzbfun.upload_stu_exam_info(df_data, exam_id)

        if event=='-BMENU4-' and values['-BMENU4-'] == '查看基本信息':
            # 弹击一个窗口window2
            # 获取所有练习的标题，以列表框的形式展示，以复选框的形式展示班级，默认选择所有班级
            # 在它下面出现四个按钮，《查看基本信息》、《查看成绩》 、《打印》、《导出到文件》
            # 在exam_info中获取最近一次的练习的exam_id,以班级为单位显示该次练习的基本信息，
            print('你点击了', event, '菜单',values[event])
            last_exam_id = lzbfun.download_last_exam_id()
            # 根据last_exam_id，获取练习标题
            # exam_title = lzbfun.download_exam_title(last_exam_id)
            # exam_title_id_data=download_exam_title_id()
            # 返回的data是一个列表,其中每个元素都是一个元组,元组中的元素是数据库查询结果中的每一行数据。
            # (('3.2 节Python 语言基础(一）', 25), ('3.2 节Python 语言基础(一）', 24), ('32节[Pthon 迈言其础（一)', 23), ('32节[Pthon 迈言其础（一)', 22), ('3.2 节Pvthon 语言基础', 21), ('3.2 节Pvthon 语言基础(-)', 20), ('3.2 节Pvthon 语言基础(-)', 19))

            #根据last_exam_id，在数据表stu_exam_info中查寻到stu_code,推算出班级代号，并赋班级名称
            class_code=lzbfun.get_class_code(last_exam_id)
            if "211" in class_code:

                lzbfun.get_exam_basic_info(last_exam_id, "211")

                # 根据推算出的班级代号，每班分别统计出本次练习的最高分及名单、最低分、平均分、未交作业人数及名单
                #显示获取的函数
                #to_excel

            if "212" in class_code:
                lzbfun.get_exam_basic_info(last_exam_id, "212")

            #根据推算出的班级代号，每班分别统计出本次练习的最高分及名单、最低分、平均分、未交作业人数及名单

            #出现图各小题的正确率
            #表格，各小题的正确选项、ABCD选项的百分比和个数，低于10%的还出现名单。
            #生成

        if event == '-BMENU4-' and values['-BMENU4-'] == '查看学生成绩':
            #查看学生成绩生成EXCEL文档把最近1次的练习，基本信息，加上 交作业的班级按学号每小题选项，总分
            pass


    window.close()


    # layout = [  [psg.Menu(menu)],
    # [psg.Frame(title='选择练习和班级',  title_color='red', visible=False, key='-frame-3-1-',
     #                      relief=psg.RELIEF_SUNKEN, )],
    # [psg.Checkbox('21级2班', key='-checkbox-3-1-', visible=True,font=('微软雅黑', 24),default=True),
    #  psg.Checkbox('21级4班', key='-checkbox-3-2-', visible=True,font=('微软雅黑', 24),default=True),
    #  psg.Checkbox('21级6班', key='-checkbox-3-3-', visible=True,font=('微软雅黑', 24),default=True)],
    # [psg.Listbox(exam_title_list, default_values=exam_title_list[0], select_mode='single', change_submits=False,
    #             size=(30, 6),   disabled=False, auto_size_text=False,
    #             font=('微软雅黑', 24), no_scrollbar=False,
    #             key='-listbox-3-1-', pad=None,  tooltip=None,
    #             right_click_menu=None,visible=True, metadata=None)]
    #          ]
        # 界面
        # one--新建练习

        # [psg.Text('请输入练习的名称', key='-text-1-1-', visible=False), psg.In(key='-input-1-1-', visible=False)],
        # [psg.Text('请输入练习的编码', key='-text-1-2-', visible=False), psg.In(key='-input-1-2-', visible=False)],
        # [psg.FolderBrowse(button_text="选择练习扫描稿文件夹", key='-folderbrowse-1-1-', target='-input-1-3-', visible=False),
        #  psg.InputText(key='-input-1-3-', visible=False)],
        # [psg.Text('依次输入选择题的正确答案', key='-text-1-3-', visible=False),
        #  psg.In(key='-input-1-4-', visible=False)],
        # [psg.Button("确定", key='-button-1-1-', enable_events=True, visible=False)],

        # two--打印练习
        # [psg.Frame(
        #     title='最近5次练习', layout=layout_three, title_color='red', visible=False, key='-frame-2-1-',
        #     relief=psg.RELIEF_SUNKEN, )],
        # [psg.Checkbox('21级2班', key='-checkbox-2-1-', visible=False),
        #  psg.Checkbox('21级4班', key='-checkbox-2-2-', visible=False),
        #  psg.Checkbox('21级6班', key='-checkbox-2-3-', visible=False),
        #  ],
        # [psg.Text('请输入学号', key='-text-2-1-', visible=False), psg.In(key='-input-2-1-', visible=False)],
        # [psg.Button("确定", key='-button-2-1-', enable_events=True, visible=False)],

        # three--上传作业
        # [psg.Frame(
        #     title='最近5次练习', layout=layout_three, title_color='red', visible=False, key='-examframe-three-',
        #     relief=psg.RELIEF_SUNKEN, )],
        # [psg.Checkbox('21级2班', key='-CHECKBOX1-three-', visible=False),
        #  psg.Checkbox('21级4班', key='-CHECKBOX2-three--', visible=False),
        #  psg.Checkbox('21级6班', key='-CHECKBOX3-three--', visible=False),
        #  ],
        # [psg.Text('请输入学号', key='-std-code-text-three-', visible=False), psg.In(key='-std-code-three-', visible=False)],
        # [psg.FolderBrowse(button_text="选择学生练习扫描稿文件夹", key='-folderbrowse-3-1-', target='-input-3-1-', visible=False),
        #  psg.InputText(key='-input-3-1-', visible=False)],
        # [psg.Button("确定", key='-button-3-1-', enable_events=True, visible=False)],

        # three--打印阅卷结果
        # 借用two--选择练习，选择班级，输入学号
        # [psg.Frame(title='选择练习和班级', layout=layout_three, title_color='red', visible=False, key='-frame-3-1-',
        #     relief=psg.RELIEF_SUNKEN, )],
        # [psg.Checkbox('21级2班', key='-checkbox-3-1-', visible=False),
        #  psg.Checkbox('21级4班', key='-checkbox-3-2-', visible=False),
        #  psg.Checkbox('21级6班', key='-checkbox-3-3-', visible=False),
        #  ],
        # [psg.Text('请输入学号', key='-text-3-1-', visible=False), psg.In(key='-input-3-2-', visible=False)],
        # [psg.Button("确定打印", key='-button-3-2-', enable_events=True, visible=False),
        #  psg.Button("查看打印顺序", key='-button-3-3-', enable_events=True, visible=False)],

        # Four--查看练习信息
        # 分'基本信息::basic_info','答题详情::exam_info'
        # 选择练习（显示所有练习），按“基本信息"确定键，弹出练习的基本信息；按”答题详情“确定键，弹出练习的详细信息，
        # 列表框，列出所有练习名称
        # 2个确定按钮
        # values=['1 XXexam','2XXexam','3xxexam','4xxexam','5xxexam','6xxexam','7xxexam','8eeexam','9sdddexam','10fdfdfsexam']
    #     [psg.Listbox(
    #         ['1 XXexam', '2XXexam', '3xxexam', '4xxexam', '5xxexam', '6xxexam', '7xxexam', '8eeexam', '9sdddexam',
    #          '10fdfdfsexam'],
    #         default_values='1 XXexam',
    #         select_mode='single',
    #         change_submits=False,
    #         enable_events=True,
    #         bind_return_key=False,
    #         size=(30, 10),
    #         disabled=False,
    #         auto_size_text=False,
    #         font=('微软雅黑', 28),
    #         no_scrollbar=False,
    #         background_color=None,
    #         text_color=None,
    #         key='-listbox-4-1-',
    #         pad=None,
    #         tooltip=None,
    #         right_click_menu=None,
    #         visible=False,
    #         metadata=None)],
    #     [psg.Button("基本信息", key='-button-4-1-', enable_events=True, visible=False),
    #      psg.Button("答题详情", key='-button-4-2-', enable_events=True, visible=False)],
    # ]



    #3) 创建窗口
    # window = psg.Window('小马批作业', layout, font=("微软雅黑", 22), size=(1200,800),
    #                  grab_anywhere=True,  #窗口可移动,
    #                  resizable=True,  #界面生成后可以调整大小
    #                  default_element_size=(42,2),
    #                  )
    #4) 添加事件处理，事件循环
    # while True:
    #     event, values = window.read() # 用于读取页面上的事件和输入的数据。
    #     # 其返回值为('事件', {0: '输入控件1接收的值', 1: '输入控件2接受的值'})
    #     print("event, values",event, values)
    #     if event == None:  #窗口关闭事件
    #         break  # 退出循环
    #     #新建练习
    #     if event=='新建练习::new':
    #         folder_path = psg.popup_get_folder('请选择练习扫描稿所在文件夹', title='新建练习', font=("微软雅黑", 20))
    #         #如果按确定键继续下面，如果按“conle”键退回到主菜单，需改进
    #         print(folder_path)
    #         Folder_path=lzbfun.Folder_path(folder_path)
    #         Folder_path.del_Null_file() #删除空白页
    #         exam_total_page=Folder_path.get_total_page()   #总页数
    #         exam_file_list=Folder_path.get_url_file()       #获取文件夹内所有文件的URL
    #         exam_title=lzbfun.get_exam_title(folder_path)   #获取练习标题
    #         #练习的正确答案
    #         layout1 = [[psg.Text('本次练习名称为'), psg.In(default_text=exam_title, key='-input-1-1-'),
    #                    psg.Text('共 ' + str(exam_total_page) + ' 页')],
    #                   [psg.Text('输入练习的正确答案'), psg.In(key='-input-1-2-')],
    #                   [psg.Button("确定", key='-button-1-1-', enable_events=True, visible=True),
    #                    psg.Button("取消", key='-button-1-2-', enable_events=True, visible=True)]
    #                   ]
    #         window1=psg.Window('新建练习', layout1, finalize=True, font=("微软雅黑", 22))
    #         window1_active = True
    #         window.Hide()
    #         while True:
    #             event1, values1 = window1.read()
    #             if event1 == psg.WIN_CLOSED or event1 == 'Exit' or  event1=='-button-1-2-':
    #                 window1.close()
    #                 window1_active = False
    #                 window.UnHide()
    #                 break
    #             if event1 == '-button-1-1-':  #按下确定键
    #                 exam_name = values1['-input-1-1-']  # 练习名称
    #                 correct_answer = values1['-input-1-2-']  # 正确答案
    #                 # correct_answer=lzbfun.to_H_answer(correct_answer)
    #                 # print(exam_name, correct_answer)
    #                 #把数据上传练习标题、总页数、答案到数据表exam_conc_info中
    #                 lzbfun.upload_exam_conc_data(exam_title,exam_total_page,correct_answer)
    #                 window1.close()
    #                 window1_active = False
    #                 # 显示各填涂选项的轮廓线，并确认,23-7-6
    #                 # exam_file_list = Folder_path.get_url_file()
    #                 #存储page_num,foot_text,cnt的字典
    #                 page_num_foot_img_cnt={}
    #                 #这里最好让第1页、第2页。。。依次获取轮廓参数
    #                 for filename in exam_file_list:
    #                     #获取图像image
    #                     exam_file=lzbfun.Imgfile(filename)
    #                     page_img,page_alpha,_,_=exam_file.get_img_and_alpha_and_xy_ba()
    #                     #获取页脚文本，页数，确认后的轮廓线
    #                     page_num,exam_id,page_foot=exam_file.get_exam_page_and_exam_id_foot_text()
    #                     cnt_num=exam_file.mark_cnts_and_get_cnts_num()
    #                     lzbfun.upload_exam_detail_data(page_num, filename, page_foot, cnt_num)
    #                 window.UnHide()
    #                 lzbfun.update_page_answ()
    #                 break
    #
    #
    #     if event=='批阅作业::marking':
    #         print('---------开始打印----------')
    #         time_a= time.time()
    #         #设置共享数据字典，变量名shared_id_page_cnt_answ，用于id为键
    #         #设置共享数据列表，shared_id_stucode_page_ttinfo,用于存储每页批改为的信息,
    #         # 2023-12-26改为由df对象存储
    #         #df对象由文件名\id\stucode\page\ttinfo组成
    #         lzbfun.delete_temp_file()
    #         # 获取文件夹路径
    #         folder_path = psg.popup_get_folder('请选择学生练习扫描稿所在文件夹', title='批阅作业', font=("微软雅黑", 20))
    #         exam_file_list = lzbfun.get_url_file(folder_path)  # 获取排序后的文件名,带URL
    #         #创建df对象,列标签需要考虑2024-1-11
    #         #(img_a_filename,exam_id,student_code,img_a_page,img_a_tt_info,img_a_right_num)
    #         df_data=pd.DataFrame(columns=['stu_code','page','tt_info'])
    #         #创建共享数据字典
    #         manager = multiprocessing.Manager()
    #         exam_id = lzbfun.get_this_exam_id(exam_file_list)
    #         page_cnt_answ = lzbfun.generate_page_cnt_answ(exam_id)
    #         d={exam_id:page_cnt_answ}
    #         shared_data_dict = manager.dict(d)
    #         # 创建子进程
    #         # with multiprocessing.Pool(processes=5) as pool:
    #         #     for i in range(0, len(exam_file_list), 2):
    #         #         # Pool().apply_async(要调用的目标,(传递给目标的参数元祖,))
    #         #         # 每次循环将会用空闲出来的子进程去调用目标
    #         #         pool.apply_async(lzbfun.worker,
    #         #                          args=(exam_file_list[i], exam_file_list[i + 1], shared_data_dict),
    #         #                          callback=lzbfun.workercallback)
    #         #         # print("进程", os.getpid(), "开始参数is", exam_file_list[i], exam_file_list[i + 1],  )
    #         #     # 关闭进程池并等待所有任务完成
    #         #     pool.close()
    #         #     pool.join()
    #         pool = multiprocessing.Pool(processes=5)
    #         for i in range(0, len(exam_file_list), 2):
    #             pool.apply_async(lzbfun.worker,args=(exam_file_list[i], exam_file_list[i + 1], shared_data_dict),
    #                     callback=workercallback)
    #         # print("进程", os.getpid(), "开始参数is", exam_file_list[i], exam_file_list[i + 1],  )
    #         # 关闭进程池并等待所有任务完成
    #         pool.close()
    #         pool.join()
    #         print("所有子进程已完成。")
    #         print(df_data)
    #
    #         #子进程结束，对(".\\printdoc")文件夹中带pri的文件进行处理
    #         #根据文件名中的stu_code，统计df中个数是否==totle_page,Yes,计算总分；
    #         #No，则从数据库中查找，返回后查找结果，合并，计算总分。
    #         #总分添加到打印文稿中
    #         # 设置字体和字号
    #         font = cv.FONT_HERSHEY_SIMPLEX
    #         font_size = 4
    #         printdoc_file_list = os.listdir(".\\printdoc")
    #         for file in printdoc_file_list:
    #             if file.startswith("pri"):
    #                 img = cv.imread('.\\printdoc\\' + file)
    #                 split_file_name = file.split("_")
    #                 if split_file_name[1]== "alpha":
    #                     file_stu_code=split_file_name[2]
    #                     alpha=1
    #                     img = cv.rotate(img, cv.ROTATE_180)
    #                     stare_cut=len(split_file_name[0]+ split_file_name[1]+split_file_name[2])+3
    #                 else:
    #                     file_stu_code = split_file_name[1]
    #                     alpha = 0
    #                     stare_cut = len(split_file_name[0] + split_file_name[1]) + 2
    #                 print_filename = file[stare_cut:]
    #                 #在df中获取列标签'stu_code'=file_stu_code
    #                 # df=pandas.DataFrame(columns=['stu_code','page','tt_info'])
    #                 if df_data[df_data.stu_code==file_stu_code].stu_code.count()==len(page_cnt_answ):
    #                     # 计算总分
    #                     # 获取page_cnt_answ中的正确答案
    #                     correct_answ = ''.join(map(lambda x: x[2], page_cnt_answ))
    #                     df_data1 = df_data[df_data.stu_code ==file_stu_code].sort_values(by='page')
    #
    #                     # print(df1)
    #                     my_tt_info = ''.join(df_data1['tt_info'].apply(lambda x: str(x)))
    #                     # print(my_tt_info)
    #                     count = sum(1 for a, b in zip(my_tt_info, correct_answ) if a == b)
    #                     score = int(count / len(correct_answ) * 100 + 0.5)
    #                 else:  #如果数据不健全，去数据库中找
    #
    #                     pass
    #                 # 添加文字
    #                 cv.putText(img, str(score), (1900, 400), font, font_size, (0, 0, 255), 3)
    #                 if alpha == 1:
    #                     img = cv.rotate(img, cv.ROTATE_180)
    #                 cv.imwrite('.//printdoc//'+print_filename, img)
    #
    #         #如果按确定键继续下面，如果按“conle”键退回到主菜单，需改进
    #         # print(folder_path)
    #         # std_folder_path=lzbfun.Folder_path(folder_path)
    #         # exam_total_page=Folder_path.get_total_page()   #总页数
    #         # if global_var.get_value("exam_id") == False:
    #         #     exam_id = lzbfun.get_this_exam_id(exam_file_list)
    #         #     global_var.set_value("exam_id", exam_id)
    #         #获取exam_id
    #         #获取相应的page_cnt_answ
    #         # if global_var.get_value(exam_id) == False:
    #         #     exam_id = lzbfun.get_this_exam_id(exam_file_list)
    #         #     page_cnt_answ = lzbfun.generate_page_cnt_answ(exam_id)
    #         #     global_var.set_value(exam_id, page_cnt_answ)
    #         # page_cnt_answ = global_var.get_value(exam_id)
    #         # total_page=len(page_cnt_answ)   #1个练习的总页数
    #
    #         # exam_id = lzbfun.get_this_exam_id(exam_file_list)
    #         # page_cnt_answ = lzbfun.generate_page_cnt_answ(exam_id)
    #         # print("main中page_cnt_answ长度",len(page_cnt_answ))
    #         # shared_id_page_cnt_answ[exam_id]=page_cnt_answ
    #         # print("main中shared_id_page_cnt_answ长度",len(shared_id_page_cnt_answ))
    #         # #return (img_a.self, exam_id, student_code, img_a_page, img_a_tt_info, img_a_right_num)
    #         # df=pandas.DataFrame(columns=['filename', 'exam_id', 'stu_code', 'exam_page','tt_info','correct_num'])
    #
    #         #多进程编程begin
    #         #排序后的文件序列开始
    #         # print(exam_file_list)
    #         # # multiprocessing.cpu_count()
    #         # pool = Pool(cpu_count())    #此处cpu_count()需核实
    #         # for i in range(0, len(exam_file_list),2):
    #         #     # Pool().apply_async(要调用的目标,(传递给目标的参数元祖,))
    #         #     # 每次循环将会用空闲出来的子进程去调用目标
    #         #     pool.apply_async(lzbfun.worker, args=(exam_file_list[i],exam_file_list[i+1],shared_id_page_cnt_answ),callback=lzbfun.workercallback)
    #         #     # print("进程", os.getpid(), "开始参数is", exam_file_list[i], exam_file_list[i + 1],  )
    #         #
    #         # # 关闭进程池，关闭后pool不再接收新的请求
    #         # pool.close()
    #         # pool.join()
    #         # print('子进程结束==')
    #
    #
    #
    #
    #
    #
    #         #把df中数据上传到数据库
    #         #df中数据 ['filename', 'exam_id', 'stu_code', 'exam_page', 'tt_info', 'correct_num']
    #         # 上传数据库需要的数据，stu_code,exam_id,tt_info,choice,score,date
    #         #合并数据，
    #
    #
    #         #exam_file_list原来的练习扫描稿文件，带有URL,
    #         #去除URL,把文件扩展名改为jpg
    #         stare_index = exam_file_list[0].rfind("//")
    #         last_index = exam_file_list[0].rfind(".")
    #
    #         new_file_list = [s[stare_index + 2:last_index] + ".jpg" for s in exam_file_list]
    #         #只有文件名，不带URL
    #         list_a=[x for x in range(0,len(new_file_list),2)]
    #         list_b = [x for x in range(1, len(new_file_list), 2)]
    #         # 开始打印0，2，4页文稿,1，3，5页文稿
    #         # time.sleep(100)
    #         # for i in list_a + list_b:
    #             # lzbfun.image_printout(i)   #该函数不需要路径
    #
    #         time_b = time.time()
    #         print("打印耗时：", time_b - time_a)
    #         print('---------打印完成----------')
    #         #打印完成后，上传exam_id,stu_code,tt_info数据到数据库
    #         lzbfun.upload_stu_exam_info(df_data, exam_id)
    #
    #
    #     if event=='Three--查看作业信息':
    #         #出现对话框，双标签，基本信息、详细信息
    #         # 基本信息中直接列出最近一次批阅的各个班级的基本信息，
    #         # 1、班级名称；2、班级人数；3、练习名称
    #         # 3、班级最高分；4、班级最低分；5、班级平均分；6、年段平均分
    #         # 7、未交作业学生人数、名单
    #         # 8、最高分学生人数、名单
    #         #按打印，则输出到打印机
    #         #详细信息中，有各个班级名称的按钮，按相应按钮，出现按题号为行标签，并包括正确选项，正确率。列标签分别为ABCD各选项选择的人数
    #         #对于错误率在15%以内的显示学生名单 。
    #         #exam_list = lzbfun.download_exam_name()  # 获取所有练习名称，是一个元祖
    #
    #         # 更新界面，显示练习名称列表框，显示班级复选框
    #         print("一级菜单 查看作业信息")
    #         exam_list=["练习一","练习二","练习三"]
    #         window['-listbox-3-1-'].update(exam_list,visible=True)
    #
    #         window['-checkbox-3-1-'].update(visible=True)
    #         window['-checkbox-3-2-'].update(visible=True)
    #         window['-checkbox-3-3-'].update(visible=True)
    #
    #
    #
    #
    #
    #         #
    #         # window['-text-3-1-'].Update(visible=True)
    #         # window['-input-3-2-'].Update(visible=True)
    #         # window['-button-3-2-'].Update(visible=True)
    #         #获取所有练习的名称
    #     #     data = lzbexam.get_exam_name()
    #     #     exam_name=[]
    #     #     for i in range(len(data)):
    #     #         exam_name.append(data[i][0])
    #     #     window.Element('-listbox-4-1-').Update(values=exam_name)
    #     #     # exam_name_clk = window['-listbox-4-1-'].get()
    #     #     #查看练习基本信息
    #     #     if event == '-button-4-1-':  # 按钮事件，练习基本信息
    #     #         #获取点击练习事件
    #     #         # print('exam_name',exam_name)
    #     #         exam_name_clk=window['-listbox-4-1-'].get()
    #     #         # print('exam_name',exam_name_clk)
    #     #         # print(type(exam_name_clk))
    #     #         #显示图片有关练习基本信息
    #     #         lzbexam.view_exam_basic_info(exam_name_clk)
    #     #
    #     #     if event == '-button-4-2-':  # 按钮事件，答题详情
    #     #         #获取点击答题详情
    #     #         # print('exam_name',exam_name)
    #     #         exam_name_clk=window['-listbox-4-1-'].get()
    #     #         # print('exam_name',exam_name_clk)
    #     #         # print(type(exam_name_clk))
    #     #         #显示图片有关练习基本信息
    #     #         lzbexam.view_exam_detail_info(exam_name_clk)
    #     #
    #     # #查看答题详情




    # window.close() # 关闭窗口界面