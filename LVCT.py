# -*- coding: utf-8 -*-
"""
Created on Fri Sep 30 10:53:41 2022

@author: Mingeon Kim, CT/MI Research Collaboration Scientist, SIEMENS Healthineers, Korea
"""

import pandas as pd
import pydicom, numpy as np
from os import listdir
from os.path import isfile, join

import hmac
import binascii
import hashlib


import os
import tkinter.ttk as ttk
import tkinter.messagebox as msgbox
from tkinter import * # __all__
from tkinter import filedialog
from PIL import Image
import shutil


root = Tk()
root.title("SIEMENS ChestCT Lung Voxel Counting Tool")

def add_file():
    files = filedialog.askdirectory(title="추가할 파일경로를 선택하세요", \
        initialdir=r".\Desktop")
        # 최초에 사용자가 지정한 경로를 보여줌

    # 사용자가 선택한 파일 목록
    list_file.insert(END, files)

# 선택 삭제
def del_file():
    #print(list_file.curselection())
    for index in reversed(list_file.curselection()):
        list_file.delete(index)


# 추사 경로 (폴더)
def browse_dest_loadpath():
    folder_selected = filedialog.askdirectory()
    if folder_selected == "": # 사용자가 취소를 누를 때
        # print("폴더 선택 취소")
        return
    #print(folder_selected)
    txt_dest_loadpath.delete(0, END)
    txt_dest_loadpath.insert(0, folder_selected)


# 저장 경로 (폴더)
def browse_dest_savepath():
    folder_selected = filedialog.askdirectory()
    if folder_selected == "": # 사용자가 취소를 누를 때
        # print("폴더 선택 취소")
        return
    #print(folder_selected)
    txt_dest_savepath.delete(0, END)
    txt_dest_savepath.insert(0, folder_selected)
    
    
def hash_acc(num, length, sideID):
   try:
       siteID = str.encode(sideID)
       num = str.encode(num)
                              # hash
       m = hmac.new(siteID, num, hashlib.sha256).digest()
                              #convert to dec
       m = str(int(binascii.hexlify(m),16))
                              #split till length
       m=m[:length]
       return m
   except Exception as e:
          print("Something went wrong hashing a value :(")
          return
      
def hu_correction(dcm, img):
    image = img.astype(np.int16)
    
    intercept = dcm.RescaleIntercept
    slope = dcm.RescaleSlope
    
        # Convert to Hounsfield units (HU)
    if slope != 1:
        image = slope * image.astype(np.float64)
        image = image.astype(np.int16)
            
    image += np.int16(intercept)
    
    image[image < np.min(image)] = np.min(image)
    image[image > np.max(image)] = np.max(image)
    
    return np.array(image, dtype=np.int16)


def voxelcounting():
    try:
        images_path = txt_dest_savepath.get()

        path_tmp = []
        name_tmp = []
        img_tmp = []

        for (path, dir, files) in os.walk(images_path):
            for filename in files:
                ext = os.path.splitext(filename)[-1]
                
                if ext == '.dcm' or '.IMA':
                    print("%s/%s" % (path, filename))
                    path_tmp.append(path)
                    name_tmp.append(filename)
        
        msk_dicom=[]
        msk_imgs = []
        img_dicom=[]
        img_imgs = []


        for i in range(len(path_tmp)):
            dcm_p = pydicom.dcmread(path_tmp[i] + '/' + name_tmp[i], force = True)
            if dcm_p.Modality == 'SEG':
                msk_dicom.append(dcm_p)
                ccc = dcm_p.pixel_array
                msk_imgs.append(ccc)
            else:
                img_dicom.append(dcm_p)
                ccc = dcm_p.pixel_array
                img_imgs.append(ccc)
                
                
        seg_list_left = []
        hu_corrected_left = []
        seg_list_right = []
        hu_corrected_right = []

                
        for m in range(len(msk_dicom)):
            for i in range(len(img_imgs)):
                img = hu_correction(msk_dicom[m], img_imgs[i])
                if msk_dicom[m].SegmentSequence[0].SegmentDescription == 'Left lung':
                    hu_corrected_left.append(img)
                    msk_img = np.transpose(msk_imgs[m], (1, 2, 0))
                    seg= img * msk_img[:, :, len(img_imgs)- 1 - i]
                    seg_list_left.append(seg)
                         
                elif msk_dicom[m].SegmentSequence[0].SegmentDescription == 'Right lung':
                    hu_corrected_right.append(img)
                    msk_img = np.transpose(msk_imgs[m], (1, 2, 0))
                    seg = img * msk_img[:, :, len(img_imgs)- 1 - i]
                    seg_list_right.append(seg)

        # slice_num = 0
        # plt.figure(figsize = (12, 3))
        # plt.subplot(121)
        # aaa = plt.hist(img_imgs[slice_num].flatten(), 100, [-1024, 1324], color = 'r')
        # plt.xlim([-1024, 1324])
        # plt.legend('histogram', loc = 'upper right')
        # plt.subplot(122)
        # plt.hist(hu_corrected_right[slice_num].flatten(), 100, [-1024, 1324], color = 'g')
        # plt.xlim([-1024, 1324])
        # plt.legend('histogram', loc = 'upper right')
        # plt.show()
        # print("------------Hu correction completed-------------")
        # print("------------segmentation completed--------------")

        pixel_count_left = []
        pixel_count_right = []
        HU_count = []

        HU_low = int(txt_lowhu.get())
        HU_high = int(txt_highhu.get())
        gap = int(txt_gaphu.get())
        inii = HU_low
   

        for aa in range(len(msk_dicom)):
            # msk_zero = np.count_nonzero(msk_imgs[aa] == 0)
            if msk_dicom[aa].SegmentSequence[0].SegmentDescription == 'Left lung':
                for ini in range(HU_low, HU_high + 1, gap):
                    print(ini)
                    if ini == 0:
                        pix = np.count_nonzero(np.array(seg_list_left) == ini)
                        pix = pix - np.count_nonzero(msk_imgs[aa] == 0)
                        pixel_count_left.append(pix)
                    
                    else:
                        pix = np.count_nonzero(np.array(seg_list_left) == ini)
                        pixel_count_left.append(pix)
                    HU_count.append(ini)
                    
                    progress = (ini + inii + HU_high + HU_high + 1) / ((HU_high + 1 - HU_low) * 2) * 100 # 실제 percent 정보를 계산
                    p_var.set(progress)
                    progress_bar.update()
            
            elif msk_dicom[aa].SegmentSequence[0].SegmentDescription == 'Right lung':
                for inii in range(HU_low, HU_high + 1, gap):
                    print(inii)
                    if inii == 0:
                        pix = np.count_nonzero(np.array(seg_list_right) == inii)
                        pix = pix - np.count_nonzero(msk_imgs[aa] == 0)
                        pixel_count_right.append(pix)
                    
                    else:
                        pix = np.count_nonzero(np.array(seg_list_right) == inii)
                        pixel_count_right.append(pix)
                    
                    progress = (ini + inii + HU_high*2 + 1) / ((HU_high + 1 - HU_low) * 2) * 100 # 실제 percent 정보를 계산
                    p_var.set(progress)
                    progress_bar.update()
        
        
        total_count = np.array(pixel_count_left) + np.array(pixel_count_right)

        # vox = {'HU value': HU_count, 'Left lung Voxel count': pixel_count_left, 'Right lung Voxel count': pixel_count_right, 'Total lung Voxel count': pixel_count_left + pixel_count_right, 'PixelSpacing': dcm_p.PixelSpacing, 'SliceThickness': dcm_p.SliceThickness}
        vox = {'HU value': HU_count, 'Left lung Voxel count': pixel_count_left, 'Right lung Voxel count': pixel_count_right, 'Total lung Voxel count': total_count}
        info = {'PixelSpacing': dcm_p.PixelSpacing, 'SliceThickness': dcm_p.SliceThickness}
        df = pd.DataFrame(vox)
        df_info = pd.DataFrame(info)
        new_df = pd.concat([df, df_info], ignore_index = True)
          # .to_csv 
          # 최초 생성 이후 mode는 append
        if not os.path.exists(images_path + '/voxel_count.csv'):
             new_df.to_csv(images_path + '/voxel_count.csv', index=False, mode='w', encoding='utf-8-sig')
        else:
             new_df.to_csv(images_path + '/voxel_count.csv', index=False, mode='a', encoding='utf-8-sig', header=False) 
        
        msgbox.showinfo("알림", "Volume counting이 완료되었습니다~ 폴더안 csv 파일을 확인해주세요.")
            
    except Exception as err: # 예외처리
        msgbox.showerror("에러", err + ", Research Scientist에게 문의해주세요!")
        
        
        
'''
shutil.rmtree(r"path")
'''      

# 시작
def start():
    # 각 옵션들 값을 확인
    # print("가로넓이 : ", cmb_width.get())
    # print("간격 : ", cmb_space.get())
    # print("포맷 : ", cmb_format.get())

    # 파일 목록 확인
    # if list_file.size() == 0:
    #     msgbox.showwarning("경고", "폴더 경로를 추가해주세요")
    #     return

    # 저장 경로 확인
    if len(txt_dest_savepath.get()) == 0:
        msgbox.showwarning("경고", "파일이 포함된 폴더를 추가해주세요")
        return

    # 이미지 통합 작업
    voxelcounting()



photo = PhotoImage(file="./pics/LVCT.png")
label2 = Label(root, image=photo)
label2.pack()

# 파일 프레임 (파일 추가, 선택 삭제)
# file_frame = Frame(root)
# file_frame.pack(fill="x", padx=5, pady=5) # 간격 띄우기

# btn_add_file = Button(file_frame, padx=5, pady=5, width=12, text="폴더추가", command=add_file)
# btn_add_file.pack(side="left")

# btn_del_file = Button(file_frame, padx=5, pady=5, width=12, text="선택삭제", command=del_file)
# btn_del_file.pack(side="right")

# # 리스트 프레임
# list_frame = Frame(root)
# list_frame.pack(fill="both", padx=5, pady=5)

# scrollbar = Scrollbar(list_frame)
# scrollbar.pack(side="right", fill="y")

# list_file = Listbox(list_frame, selectmode="extended", height=5, yscrollcommand=scrollbar.set)
# list_file.pack(side="left", fill="both", expand=True)
# scrollbar.config(command=list_file.yview)

# # 추가 경로 프레임
# loadpath_frame = LabelFrame(root, text="Source data 경로")
# loadpath_frame.pack(fill="x", padx=5, pady=5, ipady=5)

# txt_dest_loadpath = Entry(loadpath_frame)
# txt_dest_loadpath.pack(side="left", fill="x", expand=True, padx=5, pady=5, ipady=4) # 높이 변경

# btn_dest_loadpath = Button(loadpath_frame, text="찾아보기", width=10, command=browse_dest_loadpath)
# btn_dest_loadpath.pack(side="right", padx=5, pady=5)

# 저장 경로 프레임
savepath_frame = LabelFrame(root, text="폴더 내에 반드시 원본 DICOM과 Mask DICOM 포함되어 있는지 확인 필요!!!")
savepath_frame.pack(fill="x", padx=5, pady=5, ipady=5)

txt_dest_savepath = Entry(savepath_frame)
txt_dest_savepath.pack(side="left", fill="x", expand=True, padx=5, pady=5, ipady=4) # 높이 변경

btn_dest_savepath = Button(savepath_frame, text="찾아보기", width=10, command=browse_dest_savepath)
btn_dest_savepath.pack(side="right", padx=5, pady=5)

# 옵션 프레임
frame_option = LabelFrame(root, text="*Counting 하실 HU 값 범위를 지정해주세요*")
frame_option.pack(padx=15, pady=15, ipady=1)
################################################################

# 실행할 옵션 선택
lbl_lowhu = Label(frame_option, text="Low HU", width=10)
lbl_lowhu.pack(side="top", padx=5, pady=5, fill = "both", expand = True)

txt_lowhu = Entry(frame_option, width = 5)
txt_lowhu.pack(pady = 5)
txt_lowhu.insert(END, "-1000")


# Study number 옵션
lbl_highhu = Label(frame_option, text="High HU", width = 10)
lbl_highhu.pack(side="top", padx = 5, pady = 0, fill="both", expand=True)

txt_highhu = Entry(frame_option, width=5)
txt_highhu.pack(pady = 5)
txt_highhu.insert(END, "1000")

# 익명화 이름 옵션
lbl_gaphu = Label(frame_option, text="Gap", width = 10)
lbl_gaphu.pack(side="top", padx = 5, pady = 0, ipadx = 5, fill="both", expand=True)

txt_gaphu = Entry(frame_option, width=5)
txt_gaphu.pack(pady = 5)
txt_gaphu.insert(END, "1")


##################################################################
# 진행 상황 Progress Bar
frame_progress = LabelFrame(root, text="진행상황")
frame_progress.pack(fill="x", padx=5, pady=5, ipady=5)

p_var = DoubleVar()
progress_bar = ttk.Progressbar(frame_progress, maximum=100, variable=p_var)
progress_bar.pack(fill="x", padx=5, pady=5)

# 실행 프레임
frame_run = Frame(root)
frame_run.pack(fill="x", padx=5, pady=5)

btn_close = Button(frame_run, padx=5, pady=5, text="닫기", width=12, command=root.quit)
btn_close.pack(side="right", padx=5, pady=5)

btn_start = Button(frame_run, padx=5, pady=5, text="시작", width=12, command=start)
btn_start.pack(side="right", padx=5, pady=5)

root.resizable(True, True)
root.mainloop()