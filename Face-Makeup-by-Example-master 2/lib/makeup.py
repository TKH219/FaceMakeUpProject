import cv2
import numpy as np
import imutils
from lib import face_parts, lip, warp, overlay_blur


def decompose(img):
    base = cv2.bilateralFilter(img, 9, 75,75)
    return base, img-base

def warp_target(subject, target):

    if(target.shape[0]>subject.shape[0]):
        print('bigger target')
        new_subject = np.zeros((target.shape[0]-subject.shape[0],subject.shape[1],3), dtype=subject.dtype)
        subject = np.vstack((subject, new_subject))
    else:
        print('bigger subject')
        #resizing target
        new_target = np.zeros((subject.shape[0]-target.shape[0],target.shape[1],3), dtype=target.dtype)
        target = np.vstack((target, new_target))

    if(subject.shape[0]%2!=0):
        zero_layer = np.zeros((1, target.shape[1],3), dtype=target.dtype)
        target = np.vstack((target, zero_layer))
        subject = np.vstack((subject, zero_layer))

    #cv2.imshow('s', subject)
    #cv2.imshow('t', target)
    #cv2.waitKey(0)

    warped_target = warp.warp(target, subject)
    # cv2.imshow('new', warped_target)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    return subject, warped_target

def apply_makeup(subject, warped_target):
    zeros = np.zeros(warped_target.shape, dtype=warped_target.dtype)
    ones = np.ones(warped_target.shape, dtype=warped_target.dtype)
    face_mask = np.where(warped_target==[0,0,0], zeros, ones*255)
    cv2.imshow('mask', face_mask)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    sub_lab = cv2.cvtColor(subject, cv2.COLOR_BGR2LAB)
    tar_lab = cv2.cvtColor(warped_target, cv2.COLOR_BGR2LAB)

    sl, sa, sb = cv2.split(sub_lab)
    tl, ta, tb = cv2.split(tar_lab)

    face_struct_s, skin_detail_s = decompose(sl)
    face_struct_t, skin_detail_t = decompose(tl)

    #color transfer
    gamma = .8
    '''
    type = sa.dtype
    sa.dtype = float
    ta.dtype = float
    sb.dtype = float
    tb.dtype = float
    '''
    type = sa.dtype
    ra = np.where(True, sa*(1-gamma)+ta*gamma, zeros[:,:,0])
    rb = np.where(True, sb*(1-gamma)+tb*gamma, zeros[:,:,0])
    ra = ra.astype(type)
    rb = rb.astype(type)
    #print(ra.shape)
    ra = cv2.bitwise_and(ra,ra,mask = face_mask[:,:,0])
    rb = cv2.bitwise_and(rb,rb,mask = face_mask[:,:,0])



    #skin-detail transfer
    gammaI = 0
    gammaE = 1
    skin_detail_r = np.where(True, skin_detail_s*gammaI + skin_detail_t*gammaE, zeros[:,:,0])
    skin_detail_r = skin_detail_r.astype(type)


    #Work on the base layer
    fp_mask = face_parts.find_mask(subject, True)
    src_gauss = cv2.pyrDown(face_struct_s)
    src_lapla = face_struct_s - cv2.pyrUp(src_gauss)
    dst_gauss = cv2.pyrDown(face_struct_t)
    dst_lapla = face_struct_t - cv2.pyrUp(dst_gauss)
    face_struct_r = np.where(face_mask[:,:,0]==0, face_struct_s, dst_lapla + cv2.pyrUp(src_gauss))
    cv2.imshow('transfering target', face_struct_r)
    cv2.waitKey(0)
    face_struct_r = np.where(fp_mask[:,:,0]==255, face_struct_s, face_struct_r)

    cv2.imshow('mask', fp_mask)
    cv2.imshow('transfering target', face_struct_r)
    cv2.imshow('keeping src', face_struct_s)
    cv2.imshow('diff', face_struct_s - face_struct_r)
    cv2.waitKey(0)

    rl = face_struct_r+skin_detail_r
    rl = cv2.bitwise_and(rl,rl,mask = face_mask[:,:,0])

    res_lab = cv2.merge((rl, ra, rb))
    res = cv2.cvtColor(res_lab, cv2.COLOR_LAB2BGR)

    fp_mask = face_parts.find_mask(subject, False)
    res = cv2.bitwise_and(res,res,mask = face_mask[:,:,0])
    res = np.where(face_mask==[0,0,0], subject, res)
    res = np.where(fp_mask==[255,255,255], subject, res)


    #apply lip makeup
    M, lip_map = lip.lip_makeup(subject, warped_target)
    res = np.where(lip_map==[255,255,255], M, res)

    cv2.imshow('old', res)
    cv2.waitKey(0)

    res = overlay_blur.overlay(subject, res, face_mask[:, :, 0])
    
    cv2.imshow('res', res)
    cv2.imwrite('../res.jpg', res)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == '__main__':
    # subject = cv2.imread('IMG_0739.jpeg', 1)
    subject = cv2.imread('../bluelip2.jpg', 1)
    target = cv2.imread('../target.jpg', 1)
    subject = imutils.resize(subject, width=500)
    target = imutils.resize(target, width=500)
    sub, warped_tar = warp_target(subject, target)
    apply_makeup(sub, warped_tar)