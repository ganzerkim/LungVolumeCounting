# -*- coding: utf-8 -*-
"""
Created on Tue Sep 27 13:10:39 2022

@author: User
"""

# data load

import pandas as pd
import pydicom, numpy as np
from os import listdir
from os.path import isfile, join

import matplotlib.pylab as plt
import os


images_path = 'C:\\Users\\User\\Desktop\\NTM_Chest\\001'

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

#msk_img = np.transpose(msk_imgs[0], (1, 2, 0))

#HU Correction

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


seg_list_left = []
hu_corrected_left = []
seg_list_right = []
hu_corrected_right = []

pix_count_left = []
pix_count_right = []
        
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

HU_low = -1000
HU_high = 1000
gap = 1

for aa in range(len(msk_dicom)):
    msk_zero = np.count_nonzero(msk_imgs[aa] == 0)
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



# np.count_nonzero(msk_img == 0)

# zzz = np.array(seg_list_left)

# np.count_nonzero(zzz == 168)
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
  


