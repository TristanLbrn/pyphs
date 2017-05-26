#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon May 15 20:19:21 2017

@author: Falaize
"""

from ..tools import types, simplify
import sympy


def inverse(Mat, dosimplify=False):
    """
    same method for every matrix inversions
    """
    iMat = Mat.inv()
    if dosimplify:
        iMat = simplify(iMat)
    return iMat


def matvecprod(mat, vec):
    """
Safe dot product of a matrix whith shape (m, n) and a vector (list)
    """

    types.matrix_test(mat)
    types.vector_test(vec)

    l = len(vec)
    m, n = mat.shape
    assert l == n
    if l == 0:
        res = sympy.zeros(1, m).tolist()[0]
    else:
        res = mat.dot(vec)
        if m == 1:
            res = [res, ]
    return res
