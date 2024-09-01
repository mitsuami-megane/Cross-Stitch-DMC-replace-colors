#!/usr/bin/env python
# coding=utf-8

# Cross Stitch Rel 15
# Created by Tin Tran
# Comments directed to http://gimplearn.net
#
# License: GPLv3
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY# without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# To view a copy of the GNU General Public License
# visit: http://www.gnu.org/licenses/gpl.html
#
#
# ------------
# | Change Log |
# ------------
# Rel 1: Initial release.
# Rel 2: Save selections to channels so that we can run "Cross Stitch DMC replace colors" script on it after adding DMC code to layer names.
# rel 3: for GIMP 2.10 (tested on Linux Ubuntu using GIMP flatpak installation).
# Rel 4: Added Delta-E color matching method (Superior to other methods).
# Rel 5: Added stitch count to thread info (requested by yellowzip [gimplearn.net])
# Rel 6: UTF-8 instead of UTF-8 BOM (so that it would run on windows)
# Rel 7: Use symbols as stitch identifiers instead of hex.
# Rel 8: Output dimension x by y stitches at bottom of Thread Info Image (for reference).
# Rel 9: Fix total stitch count as image isn't always filled, some blank areas.
# Rel 10: Print real life size at bottom of thread info image {for example on aida 14 count: 7.14" by 7.14"(18.14cm by 18.14cm])}
# Rel 11: Option to change Interpolation for scaling, sometimes using 'None' is better than 'Cubic' depending on image/taste.
# Rel 12: Speed enhancement for GIMP 2.10.X.
# Rel 13: Speed enhancement for GIMP 2.10.X.
# Rel 14: Size estimation bug fixed.
# Rel 15: added characters to blank symbols bug.
# Rel 16: add blend YES/NO option
# Rel 17: limit blending to close colors produces superior results
# Rel 18: Allow for "Third Blend" (1 strand of 1st color and 2 strands of 2nd color)
# Rel 19: added DMC 1-35 (new colors).
# Rel 20: Allow Fourth Blend (4 strands)
# Rel 21: Allow Fifth Blend (5-strand) and Sixth Blend (6-strand)

import math
import string

# import Image
from gimpfu import *
from array import array

stitch_dimension = 30


def rgb2lab(rgb):
    r = rgb[0] / 255.0
    g = rgb[1] / 255.0
    b = rgb[2] / 255.0

    r = ((r + 0.055) / 1.055) ** 2.4 if (r > 0.04045) else (r / 12.92)
    g = ((g + 0.055) / 1.055) ** 2.4 if (g > 0.04045) else (g / 12.92)
    b = ((b + 0.055) / 1.055) ** 2.4 if (b > 0.04045) else (b / 12.92)
    x = (r * 0.4124 + g * 0.3576 + b * 0.1805) / 0.95047
    y = (r * 0.2126 + g * 0.7152 + b * 0.0722) / 1.00000
    z = (r * 0.0193 + g * 0.1192 + b * 0.9505) / 1.08883
    x = x ** (1 / 3.0) if (x > 0.008856) else (7.787 * x) + 16 / 116.0
    y = y ** (1 / 3.0) if (y > 0.008856) else (7.787 * y) + 16 / 116.0
    z = z ** (1 / 3.0) if (z > 0.008856) else (7.787 * z) + 16 / 116.0
    return [(116.0 * y) - 16.0, 500.0 * (x - y), 200.0 * (y - z)]


def deltaE(labA, labB):
    deltaL = labA[0] - labB[0]
    deltaA = labA[1] - labB[1]
    deltaB = labA[2] - labB[2]
    c1 = (labA[1] * labA[1] + labA[2] * labA[2]) ** 0.5
    c2 = (labB[1] * labB[1] + labB[2] * labB[2]) ** 0.5
    deltaC = c1 - c2
    deltaH = deltaA * deltaA + deltaB * deltaB - deltaC * deltaC
    deltaH = 0 if (deltaH < 0) else (deltaH) ** 0.5
    sc = 1.0 + 0.045 * c1
    sh = 1.0 + 0.015 * c1
    deltaLKlsl = deltaL / (1.0)
    deltaCkcsc = deltaC / (sc)
    deltaHkhsh = deltaH / (sh)
    i = deltaLKlsl * deltaLKlsl + deltaCkcsc * deltaCkcsc + deltaHkhsh * deltaHkhsh
    return 0 if (i < 0) else (i) ** 0.5


def indexed_color(arr):
    indexed = []
    for i in range(0, len(arr) / 3):
        indexed.append((arr[i * 3 + 0], arr[i * 3 + 1], arr[i * 3 + 2]))
    return indexed


def flatten_color(ind):
    flat = []
    for i in range(0, len(ind)):
        flat.append(ind[i][0])
        flat.append(ind[i][1])
        flat.append(ind[i][2])
    return flat


MASTER_DMC = [
    ["1", "White Tin", (239, 238, 240), 0],
    ["2", "Tin", (197, 196, 201), 0],
    ["3", "Medium Tin", (176, 176, 181), 0],
    ["4", "Dark Tin", (156, 155, 157), 0],
    ["5", "Light Driftwood", (227, 204, 190), 0],
    ["6", "Medium Light Driftwood", (220, 198, 184), 0],
    ["7", "Driftwood", (204, 184, 170), 0],
    ["8", "Dark Driftwood", (157, 125, 113), 0],
    ["9", "Very Dark Cocoa", (85, 32, 20), 0],
    ["10", "Very Light Tender Green", (237, 254, 217), 0],
    ["11", "Light Tender Green", (226, 237, 181), 0],
    ["12", "Tender Green", (205, 217, 154), 0],
    ["13", "Medium Light Nile Green", (191, 246, 224), 0],
    ["14", "Pale Apple Green", (208, 251, 178), 0],
    ["15", "Apple Green", (209, 237, 164), 0],
    ["16", "Light Chartreuse", (164, 214, 124), 0],
    ["17", "Light Yellow Plum", (229, 226, 114), 0],
    ["18", "Yellow Plum", (217, 213, 109), 0],
    ["19", "Medium Light Autumn Gold", (247, 201, 95), 0],
    ["20", "Shrimp", (247, 175, 147), 0],
    ["21", "Light Alizarian", (215, 153, 130), 0],
    ["22", "Alizarian", (188, 96, 78), 0],
    ["23", "Apple Blossom", (237, 226, 237), 0],
    ["24", "White Lavender", (224, 215, 238), 0],
    ["25", "Ultra Light Lavender", (218, 210, 233), 0],
    ["26", "Pale Lavender", (207, 200, 222), 0],
    ["27", "White Violet", (233, 236, 252), 0],
    ["28", "Medium Light Eggplant", (125, 78, 146), 0],
    ["29", "Eggplant", (103, 64, 118), 0],
    ["30", "Medium Light Blueberry", (109, 84, 211), 0],
    ["31", "Blueberry", (88, 52, 163), 0],
    ["32", "Dark Blueberry", (77, 46, 138), 0],
    ["33", "Fuchsia", (217, 83, 159), 0],
    ["34", "Dark Fuchsia", (174, 66, 128), 0],
    ["35", "Very Dark Fuchsia", (115, 43, 85), 0],
    ["Ecru", "Ecru/off-white", (255, 247, 231), 0],
    ["315", "Antique Mauve - MED DK", (125, 66, 70), 0],
    ["Blanc", "White", (238, 238, 238), 0],
    ["316", "Antique Mauve - MED", (188, 117, 127), 0],
    ["B5200", "Snow White", (252, 252, 255), 0],
    ["317", "Pewter Gray", (109, 100, 105), 0],
    ["White", "White", (255, 255, 255), 0],
    ["318", "Steel Gray - LT", (153, 155, 157), 0],
    ["150", "Red - BRIGHT", (207, 0, 83), 0],
    ["319", "Pistachio Green - VY DK", (58, 85, 59), 0],
    ["151", "Pink", (255, 203, 215), 0],
    ["320", "Pistachio Green - MED", (96, 140, 89), 0],
    ["152", "Tawny - DK", (225, 161, 161), 0],
    ["321", "Red", (189, 17, 54), 0],
    ["153", "Lilac", (234, 197, 235), 0],
    ["322", "Baby Blue", (58, 96, 157), 0],
    ["154", "Red - VY DK", (75, 35, 58), 0],
    ["326", "Rose - VY DK", (172, 28, 55), 0],
    ["155", "Forget-me-not Blue", (151, 116, 182), 0],
    ["327", "Violet", (94, 15, 119), 0],
    ["156", "Blue - MED", (133, 119, 180), 0],
    ["333", "Blue Violet - VY DK", (110, 46, 155), 0],
    ["157", "Blue - LT", (181, 184, 234), 0],
    ["334", "Baby Blue - MED", (96, 133, 184), 0],
    ["158", "Blue - DK", (57, 48, 104), 0],
    ["335", "Rose", (214, 61, 87), 0],
    ["159", "Petrol Blue - LT", (188, 181, 222), 0],
    ["336", "Blue", (12, 39, 94), 0],
    ["160", "Petrol Blue - MED", (129, 120, 169), 0],
    ["340", "Blue Violet - MED", (153, 109, 195), 0],
    ["161", "Petrol Blue - DK", (96, 86, 139), 0],
    ["341", "Blue Violet - LT", (163, 154, 215), 0],
    ["162", "Baby Blue - LT", (202, 231, 240), 0],
    ["347", "Salmon - VY DK", (171, 27, 51), 0],
    ["163", "Green", (85, 122, 96), 0],
    ["349", "Coral - DK", (198, 44, 56), 0],
    ["164", "Green - LT", (186, 228, 182), 0],
    ["350", "Coral - MED", (222, 63, 64), 0],
    ["165", "Green - BRIGHT", (225, 244, 119), 0],
    ["351", "Coral", (237, 98, 91), 0],
    ["166", "Lime Green", (173, 194, 56), 0],
    ["352", "Coral - LT", (247, 131, 114), 0],
    ["167", "Khaki Brown", (133, 93, 49), 0],
    ["353", "Peach", (253, 180, 161), 0],
    ["168", "Silver Gray", (177, 174, 183), 0],
    ["355", "Terra Cotta - DK", (151, 56, 43), 0],
    ["169", "Pewter Gray", (130, 125, 125), 0],
    ["356", "Terra Cotta - MED", (190, 92, 75), 0],
    ["208", "Lavender - VY DK", (148, 66, 167), 0],
    ["367", "Pistachio Green - DK", (68, 107, 69), 0],
    ["209", "Lavender - DK", (186, 114, 198), 0],
    ["368", "Pistachio Green - LT", (127, 198, 109), 0],
    ["210", "Lavender - MED", (212, 159, 225), 0],
    ["369", "Pistachio Green - VY LT", (205, 239, 166), 0],
    ["211", "Lavender - LT", (229, 189, 237), 0],
    ["370", "Mustard - MED", (145, 114, 69), 0],
    ["221", "Shell Pink - VY DK", (121, 38, 49), 0],
    ["371", "Mustard", (159, 131, 82), 0],
    ["223", "Shell Pink - LT", (187, 104, 100), 0],
    ["372", "Mustard - LT", (173, 149, 100), 0],
    ["224", "Shell Pink - VY LT", (226, 165, 152), 0],
    ["400", "Mahogany - DK", (129, 55, 24), 0],
    ["225", "Shell Pink - ULT VY LT", (248, 217, 205), 0],
    ["402", "Mahogany - VY LT", (239, 158, 116), 0],
    ["300", "Mahogany - VY DK", (108, 49, 22), 0],
    ["407", "Desert Sand - DK", (183, 113, 89), 0],
    ["301", "Mahogany - MED", (170, 82, 55), 0],
    ["413", "Pewter Gray - DK", (74, 71, 73), 0],
    ["304", "Red - MED", (161, 12, 57), 0],
    ["414", "Steel Gray - DK", (118, 110, 114), 0],
    ["307", "Lemon", (253, 233, 73), 0],
    ["415", "Pearl Gray", (184, 185, 189), 0],
    ["309", "Rose - DK", (186, 32, 68), 0],
    ["420", "Hazelnut Brown - DK", (133, 90, 48), 0],
    ["310", "Black", (0, 0, 0), 0],
    ["422", "Hazelnut Brown - LT", (201, 154, 103), 0],
    ["311", "Blue - MED", (0, 42, 100), 0],
    ["433", "Brown - MED", (115, 66, 30), 0],
    ["312", "Baby Blue - VY DK", (31, 50, 121), 0],
    ["434", "Brown - LT", (143, 83, 50), 0],
    ["435", "Brown - VY LT", (169, 101, 56), 0],
    ["600", "Cranberry - VY DK", (191, 28, 72), 0],
    ["436", "Tan", (199, 133, 89), 0],
    ["601", "Cranberry - DK", (198, 42, 83), 0],
    ["437", "Tan - LT", (218, 162, 111), 0],
    ["602", "Cranberry - MED", (214, 63, 104), 0],
    ["444", "Lemon - DK", (245, 188, 19), 0],
    ["603", "Cranberry", (237, 93, 132), 0],
    ["445", "Lemon - LT", (252, 249, 153), 0],
    ["604", "Cranberry - LT", (247, 147, 178), 0],
    ["451", "Shell Gray - DK", (136, 119, 115), 0],
    ["605", "Cranberry - VY LT", (251, 172, 196), 0],
    ["452", "Shell Gray - MED", (173, 153, 148), 0],
    ["606", "Orange-red - BRIGHT", (247, 15, 0), 0],
    ["453", "Shell Gray - LT", (204, 184, 170), 0],
    ["608", "Orange - BRIGHT", (253, 72, 12), 0],
    ["469", "Avocado Green", (91, 101, 51), 0],
    ["610", "Drab Brown - DK", (107, 80, 57), 0],
    ["470", "Avocado Green - LT", (114, 129, 62), 0],
    ["611", "Drab Brown", (124, 95, 70), 0],
    ["471", "Avocado Green - VY LT", (158, 179, 87), 0],
    ["612", "Drab Brown - LT", (166, 136, 94), 0],
    ["472", "Avocado Green - ULT LT", (209, 222, 117), 0],
    ["613", "Drab Brown - VY LT", (185, 159, 114), 0],
    ["498", "Red - DK", (151, 11, 44), 0],
    ["632", "Desert Sand - ULT VY DK", (127, 66, 50), 0],
    ["500", "Blue Green - VY DK", (29, 54, 42), 0],
    ["640", "Beige Gray - VY DK", (129, 120, 104), 0],
    ["501", "Blue Green - DK", (47, 84, 70), 0],
    ["642", "Beige Gray - DK", (149, 141, 121), 0],
    ["502", "Blue Green", (87, 130, 110), 0],
    ["644", "Beige Gray - MED", (196, 190, 166), 0],
    ["503", "Blue Green - MED", (137, 184, 159), 0],
    ["645", "Beaver Gray - VY DK", (93, 93, 84), 0],
    ["504", "Blue Green - VY LT", (172, 218, 193), 0],
    ["646", "Beaver Gray - DK", (107, 104, 96), 0],
    ["505", "Grass Green - DK", (206, 221, 193), 0],
    ["647", "Beaver Gray - MED", (144, 142, 133), 0],
    ["517", "Wedgewood - DK", (33, 98, 133), 0],
    ["648", "Beaver Gray - LT", (167, 166, 159), 0],
    ["518", "Wedgewood - LT", (80, 129, 156), 0],
    ["666", "Red - BRIGHT", (206, 27, 51), 0],
    ["519", "Sky Blue", (148, 183, 203), 0],
    ["676", "Old Gold - LT", (236, 191, 125), 0],
    ["520", "Fern Green - DK", (56, 69, 38), 0],
    ["677", "Old Gold - VY LT", (242, 220, 159), 0],
    ["522", "Fern Green", (128, 139, 110), 0],
    ["680", "Old Gold - DK", (176, 123, 70), 0],
    ["523", "Fern Green - LT", (149, 159, 122), 0],
    ["699", "Green", (7, 91, 38), 0],
    ["524", "Fern Green - VY LT", (174, 167, 142), 0],
    ["700", "Green - BRIGHT", (7, 108, 52), 0],
    ["535", "Ash Gray - VY LT", (75, 75, 73), 0],
    ["701", "Green - LT", (33, 124, 54), 0],
    ["543", "Beige Brown - ULT VY LT", (234, 208, 181), 0],
    ["702", "Kelly Green", (55, 145, 48), 0],
    ["550", "Violet - VY DK", (88, 14, 92), 0],
    ["703", "Chartreuse", (99, 179, 48), 0],
    ["552", "Violet - MED", (144, 47, 153), 0],
    ["704", "Chartreuse - BRIGHT", (136, 197, 58), 0],
    ["553", "Violet", (164, 73, 172), 0],
    ["712", "Cream", (246, 239, 218), 0],
    ["554", "Violet - LT", (220, 156, 222), 0],
    ["718", "Plum", (203, 32, 137), 0],
    ["561", "Jade - VY DK", (40, 94, 72), 0],
    ["720", "Orange Spice - DK", (200, 58, 36), 0],
    ["562", "Jade - MED", (59, 140, 90), 0],
    ["721", "Orange Spice - MED", (244, 100, 64), 0],
    ["563", "Jade - LT", (110, 211, 154), 0],
    ["722", "Orange Spice - LT", (249, 135, 86), 0],
    ["564", "Jade - VY LT", (149, 228, 175), 0],
    ["725", "Topaz", (249, 193, 91), 0],
    ["580", "Moss Green - DK", (53, 95, 11), 0],
    ["726", "Topaz - LT", (253, 219, 99), 0],
    ["581", "Moss Green", (131, 138, 41), 0],
    ["727", "Topaz - VY LT", (253, 233, 139), 0],
    ["597", "Turquoise", (82, 173, 171), 0],
    ["728", "Golden Yellow", (242, 174, 63), 0],
    ["598", "Turquoise - LT", (151, 216, 211), 0],
    ["729", "Old Gold - MED", (206, 150, 87), 0],
    ["730", "Olive Green - VY DK", (99, 82, 11), 0],
    ["803", "Blue - DEEP", (32, 39, 84), 0],
    ["731", "Olive Green - DK", (107, 88, 11), 0],
    ["806", "Peacock Blue - DK", (29, 108, 135), 0],
    ["732", "Olive Green", (114, 92, 12), 0],
    ["807", "Peacock Blue", (85, 139, 158), 0],
    ["733", "Olive Green - MED", (167, 138, 68), 0],
    ["809", "Delft Blue", (145, 159, 213), 0],
    ["734", "Olive Green - LT", (187, 156, 84), 0],
    ["813", "Blue - LT", (127, 160, 198), 0],
    ["738", "Tan - VY LT", (226, 183, 131), 0],
    ["814", "Garnet - DK", (113, 16, 51), 0],
    ["739", "Tan - ULT VY LT", (242, 222, 185), 0],
    ["815", "Garnet - MED", (128, 11, 52), 0],
    ["740", "Tangerine", (253, 111, 26), 0],
    ["816", "Garnet", (146, 18, 56), 0],
    ["741", "Tangerine - MED", (252, 139, 16), 0],
    ["817", "Coral Red - VY DK", (187, 22, 48), 0],
    ["742", "Tangerine - LT", (253, 174, 60), 0],
    ["818", "Baby Pink", (254, 222, 221), 0],
    ["743", "Yellow - MED", (253, 215, 105), 0],
    ["819", "Baby Pink - LT", (252, 235, 222), 0],
    ["744", "Yellow - PALE", (254, 232, 141), 0],
    ["820", "Royal Blue - VY DK", (21, 18, 100), 0],
    ["745", "Yellow - LT PALE", (254, 235, 165), 0],
    ["822", "Beige Gray - LT", (232, 223, 199), 0],
    ["746", "Off White", (250, 242, 213), 0],
    ["823", "Blue - DK", (0, 11, 68), 0],
    ["747", "Sky Blue - VY LT", (206, 233, 234), 0],
    ["824", "Blue - VY DK", (40, 71, 121), 0],
    ["754", "Peach - LT", (247, 201, 176), 0],
    ["825", "Blue - DK", (52, 88, 143), 0],
    ["758", "Terra Cotta - VY LT", (233, 159, 131), 0],
    ["826", "Blue - MED", (80, 117, 167), 0],
    ["760", "Salmon", (236, 136, 128), 0],
    ["827", "Blue - VY LT", (164, 193, 222), 0],
    ["761", "Salmon - LT", (248, 180, 173), 0],
    ["828", "Blue - ULT VY LT", (195, 215, 230), 0],
    ["762", "Pearl Gray - VY LT", (209, 208, 210), 0],
    ["829", "Golden Olive - VY DK", (100, 72, 12), 0],
    ["772", "Yellow Green - VY LT", (215, 239, 167), 0],
    ["830", "Golden Olive - DK", (110, 80, 29), 0],
    ["775", "Baby Blue - VY LT", (212, 227, 239), 0],
    ["831", "Golden Olive - MED", (124, 95, 32), 0],
    ["776", "Pink - MED", (252, 168, 173), 0],
    ["832", "Golden Olive", (156, 114, 48), 0],
    ["777", "Red - DEEP", (155, 0, 66), 0],
    ["833", "Golden Olive - LT", (185, 153, 86), 0],
    ["778", "Antique Mauve - VY LT", (220, 166, 164), 0],
    ["834", "Golden Olive - VY LT", (210, 180, 104), 0],
    ["779", "Brown", (83, 51, 45), 0],
    ["838", "Beige Brown - VY DK", (74, 48, 33), 0],
    ["780", "Topaz - ULT VY DK", (148, 80, 38), 0],
    ["839", "Beige Brown - DK", (90, 60, 45), 0],
    ["781", "Topaz - VY DK", (162, 95, 31), 0],
    ["840", "Beige Brown - MED", (122, 89, 57), 0],
    ["782", "Topaz - DK", (178, 105, 35), 0],
    ["841", "Beige Brown - LT", (163, 125, 100), 0],
    ["783", "Topaz - MED", (208, 136, 61), 0],
    ["842", "Beige Brown - VY LT", (203, 176, 148), 0],
    ["791", "Cornflower Blue - VY DK", (45, 32, 104), 0],
    ["844", "Beaver Gray - ULT DK", (73, 72, 66), 0],
    ["792", "Cornflower Blue - DK", (69, 75, 139), 0],
    ["868", "Hazel Nut Brown", (153, 92, 48), 0],
    ["793", "Cornflower Blue - MED", (124, 130, 181), 0],
    ["869", "Hazelnut Brown - VY DK", (120, 76, 40), 0],
    ["794", "Cornflower Blue - LT", (160, 178, 215), 0],
    ["890", "Pistachio Green - ULT DK", (50, 66, 51), 0],
    ["796", "Royal Blue - DK", (39, 34, 118), 0],
    ["891", "Carnation - DK", (238, 50, 70), 0],
    ["797", "Royal Blue", (43, 50, 136), 0],
    ["892", "Carnation - MED", (244, 71, 83), 0],
    ["798", "Delft Blue - DK", (78, 92, 167), 0],
    ["893", "Carnation - LT", (246, 104, 121), 0],
    ["799", "Delft Blue - MED", (107, 127, 192), 0],
    ["894", "Carnation - VY LT", (253, 149, 163), 0],
    ["800", "Delft Blue - PALE", (181, 199, 233), 0],
    ["895", "Hunter Green - VY DK", (52, 75, 46), 0],
    ["801", "Coffee Brown - DK", (96, 57, 29), 0],
    ["898", "Coffee Brown - VY DK", (83, 47, 27), 0],
    ["899", "Rose - MED", (234, 107, 120), 0],
    ["955", "Nile Green - LT", (168, 235, 173), 0],
    ["900", "Burnt Orange - DK", (198, 49, 23), 0],
    ["956", "Geranium", (247, 86, 109), 0],
    ["902", "Garnet - VY DK", (101, 19, 41), 0],
    ["957", "Geranium - PALE", (253, 153, 175), 0],
    ["904", "Parrot Green - VY DK", (56, 99, 36), 0],
    ["958", "Seagreen - DK", (13, 178, 148), 0],
    ["905", "Parrot Green - DK", (70, 121, 36), 0],
    ["959", "Seagreen - MED", (114, 208, 183), 0],
    ["906", "Parrot Green - MED", (108, 158, 41), 0],
    ["961", "Dusty Rose - DK", (222, 88, 108), 0],
    ["907", "Parrot Green - LT", (157, 199, 45), 0],
    ["962", "Dusty Rose - MED", (235, 113, 131), 0],
    ["909", "Emerald Green - VY DK", (16, 107, 67), 0],
    ["963", "Dusty Rose - ULT VY LT", (253, 204, 209), 0],
    ["910", "Emerald Green - DK", (16, 129, 78), 0],
    ["964", "Seagreen - LT", (165, 228, 212), 0],
    ["911", "Emerald Green - MED", (16, 146, 86), 0],
    ["966", "Baby Green - MED", (148, 210, 138), 0],
    ["912", "Emerald Green - LT", (54, 178, 107), 0],
    ["967", "Peach - LT", (255, 194, 172), 0],
    ["913", "Nile Green - MED", (85, 202, 125), 0],
    ["970", "Pumpkin - LT", (251, 103, 33), 0],
    ["915", "Plum - DK", (149, 8, 90), 0],
    ["971", "Pumpkin", (252, 103, 13), 0],
    ["917", "Plum - MED", (172, 16, 113), 0],
    ["972", "Canary - DEEP", (251, 159, 17), 0],
    ["918", "Red Copper - DK", (136, 54, 48), 0],
    ["973", "Canary - BRIGHT", (252, 205, 45), 0],
    ["919", "Red Copper", (155, 55, 27), 0],
    ["975", "Golden Brown - DK", (129, 60, 17), 0],
    ["920", "Copper - MED", (171, 72, 54), 0],
    ["976", "Golden Brown - MED", (207, 117, 50), 0],
    ["921", "Copper", (192, 87, 61), 0],
    ["977", "Golden Brown - LT", (236, 143, 67), 0],
    ["922", "Copper - LT", (221, 110, 76), 0],
    ["986", "Forest Green - VY DK", (46, 82, 48), 0],
    ["924", "Gray Green - VY DK", (56, 74, 74), 0],
    ["987", "Forest Green - DK", (67, 104, 56), 0],
    ["926", "Gray Green - MED", (97, 118, 116), 0],
    ["988", "Forest Green - MED", (102, 146, 74), 0],
    ["927", "Gray Green - LT", (159, 168, 165), 0],
    ["989", "Forest Green", (113, 167, 78), 0],
    ["928", "Gray Green - VY LT", (192, 198, 192), 0],
    ["991", "Aquamarine - DK", (19, 95, 85), 0],
    ["930", "Antique Blue - DK", (73, 92, 107), 0],
    ["992", "Aquamarine - LT", (66, 181, 158), 0],
    ["931", "Antique Blue - MED", (102, 118, 132), 0],
    ["993", "Aquamarine - VY LT", (98, 216, 182), 0],
    ["932", "Antique Blue - LT", (147, 160, 175), 0],
    ["995", "Electric Blue - DK", (0, 97, 176), 0],
    ["934", "Avocado Green - BLACK", (50, 51, 36), 0],
    ["996", "Electric Blue - MED", (73, 168, 235), 0],
    ["935", "Avocado Green - DK", (56, 58, 42), 0],
    ["3011", "Khaki Green - DK", (101, 89, 53), 0],
    ["936", "Avocado Green - VY DK", (63, 66, 39), 0],
    ["3012", "Khaki Green - MED", (139, 123, 78), 0],
    ["937", "Avocado Green - MED", (67, 79, 44), 0],
    ["3013", "Khaki Green - LT", (175, 169, 123), 0],
    ["938", "Coffee Brown - ULT DK", (69, 39, 26), 0],
    ["3021", "Brown Gray - VY DK", (80, 64, 59), 0],
    ["939", "Blue - VY DK", (9, 9, 47), 0],
    ["3022", "Brown Gray - MED", (132, 130, 116), 0],
    ["943", "Aquamarine - MED", (0, 154, 119), 0],
    ["3023", "Brown Gray - LT", (162, 155, 134), 0],
    ["945", "Tawny", (246, 193, 154), 0],
    ["3024", "Brown Gray - VY LT", (190, 184, 172), 0],
    ["946", "Burnt Orange - MED", (237, 65, 21), 0],
    ["3031", "Mocha Brown - VY DK", (66, 48, 20), 0],
    ["947", "Burnt Orange", (252, 79, 22), 0],
    ["3032", "Mocha Brown - MED", (157, 136, 104), 0],
    ["948", "Peach - VY LT", (253, 230, 211), 0],
    ["3033", "Mocha Brown - VY LT", (219, 199, 173), 0],
    ["950", "Desert Sand - LT", (229, 172, 141), 0],
    ["3041", "Antique Violet - MED", (134, 106, 118), 0],
    ["951", "Tawny - LT", (250, 221, 182), 0],
    ["3042", "Antique Violet - LT", (175, 152, 160), 0],
    ["954", "Nile Green", (111, 218, 138), 0],
    ["3045", "Yellow Beige - DK", (175, 129, 82), 0],
    ["3046", "Yellow Beige - MED", (206, 176, 116), 0],
    ["3731", "Dusty Rose - VY DK", (195, 76, 92), 0],
    ["3047", "Yellow Beige - LT", (234, 216, 171), 0],
    ["3733", "Dusty Rose", (234, 126, 134), 0],
    ["3051", "Green Gray - DK", (76, 76, 30), 0],
    ["3740", "Antique Violet - DK", (113, 83, 93), 0],
    ["3052", "Green Gray - MED", (120, 126, 92), 0],
    ["3743", "Antique Violet - VY LT", (207, 194, 201), 0],
    ["3053", "Green Gray", (153, 157, 117), 0],
    ["3746", "Blue Violet - DK", (132, 74, 181), 0],
    ["3064", "Desert Sand", (186, 112, 86), 0],
    ["3747", "Blue Violet - VY LT", (208, 197, 236), 0],
    ["3072", "Beaver Gray - VY LT", (210, 210, 202), 0],
    ["3750", "Antique Blue - VY DK", (29, 69, 82), 0],
    ["3078", "Golden Yellow - VY LT", (252, 246, 182), 0],
    ["3752", "Antique Blue - VY LT", (186, 201, 204), 0],
    ["3325", "Baby Blue - LT", (173, 205, 231), 0],
    ["3753", "Antique Blue - ULT VY LT", (217, 230, 236), 0],
    ["3326", "Rose - LT", (249, 151, 156), 0],
    ["3755", "Baby Blue (?)", (129, 165, 216), 0],
    ["3328", "Salmon - DK", (190, 68, 74), 0],
    ["3756", "Baby Blue", (233, 244, 250), 0],
    ["3340", "Apricot - MED", (253, 107, 79), 0],
    ["3760", "Wedgewood - MED", (70, 114, 147), 0],
    ["3341", "Apricot", (253, 142, 120), 0],
    ["3761", "Sky Blue - LT", (177, 208, 223), 0],
    ["3345", "Hunter Green - DK", (64, 85, 46), 0],
    ["3765", "Peacock Blue - VY DK", (23, 94, 120), 0],
    ["3346", "Hunter Green", (86, 116, 59), 0],
    ["3766", "Peacock Blue - LT", (75, 138, 161), 0],
    ["3347", "Yellow Green - MED", (109, 150, 70), 0],
    ["3768", "Gray Green - DK", (76, 96, 95), 0],
    ["3348", "Yellow Green - LT", (190, 223, 116), 0],
    ["3770", "Tawny - VY LT", (254, 241, 216), 0],
    ["3350", "Dusty Rose - ULT DK", (170, 57, 73), 0],
    ["3771", "Peach - DK", (232, 172, 155), 0],
    ["3354", "Dusty Rose - LT", (239, 165, 172), 0],
    ["3772", "Desert Sand - VY DK", (153, 87, 68), 0],
    ["3362", "Pine Green - DK", (73, 82, 60), 0],
    ["3773", "Desert Sand - MED", (207, 134, 109), 0],
    ["3363", "Pine Green - MED", (97, 116, 81), 0],
    ["3774", "Desert Sand - VY LT", (243, 207, 180), 0],
    ["3364", "Pine Green", (142, 155, 109), 0],
    ["3776", "Mahogany - LT", (201, 100, 68), 0],
    ["3371", "Black Brown", (54, 34, 14), 0],
    ["3777", "Terra Cotta - VY DK", (146, 47, 37), 0],
    ["3607", "Plum - LT", (217, 76, 157), 0],
    ["3778", "Terra Cotta - LT", (210, 112, 92), 0],
    ["3608", "Plum - VY LT", (236, 129, 190), 0],
    ["3779", "Terra Cotta - ULT VY LT", (242, 171, 149), 0],
    ["3609", "Plum - ULT LT", (246, 176, 223), 0],
    ["3781", "Mocha Brown - DK", (89, 63, 43), 0],
    ["3685", "Mauve - VY DK", (121, 38, 59), 0],
    ["3782", "Mocha Brown - LT", (182, 157, 128), 0],
    ["3687", "Mauve", (181, 69, 93), 0],
    ["3787", "Brown Gray - DK", (98, 82, 76), 0],
    ["3688", "Mauve - MED", (220, 124, 134), 0],
    ["3790", "Beige Gray - ULT DK", (109, 90, 75), 0],
    ["3689", "Mauve - LT", (248, 187, 200), 0],
    ["3799", "Pewter Gray - VY DK", (57, 57, 61), 0],
    ["3705", "Melon - DK", (242, 73, 79), 0],
    ["3801", "Melon - VY DK", (228, 53, 61), 0],
    ["3706", "Melon - MED", (253, 110, 112), 0],
    ["3802", "Antique Mauve - VY DK", (103, 42, 51), 0],
    ["3708", "Melon - LT", (253, 160, 174), 0],
    ["3803", "Mauve - DK", (135, 42, 67), 0],
    ["3712", "Salmon - MED", (217, 93, 93), 0],
    ["3804", "Cyclamen Pink - DK", (206, 43, 99), 0],
    ["3713", "Salmon - VY LT", (253, 213, 208), 0],
    ["3805", "Cyclamen Pink", (223, 60, 115), 0],
    ["3716", "Dusty Rose - VY LT", (252, 175, 185), 0],
    ["3806", "Cyclamen Pink - LT", (241, 90, 145), 0],
    ["3721", "Shell Pink - DK", (147, 59, 61), 0],
    ["3807", "Cornflower Blue", (75, 89, 158), 0],
    ["3722", "Shell Pink - MED", (160, 75, 76), 0],
    ["3808", "Turquoise - ULT VY DK", (3, 83, 92), 0],
    ["3726", "Antique Mauve - DK", (149, 86, 92), 0],
    ["3809", "Turquoise - VY DK", (19, 106, 117), 0],
    ["3727", "Antique Mauve - LT", (218, 158, 166), 0],
    ["3810", "Turquoise - DK", (45, 141, 152), 0],
    ["3811", "Turquoise - VY LT", (168, 226, 229), 0],
    ["3839", "Lavender Blue - MED", (122, 126, 197), 0],
    ["3812", "Seagreen - VY DK", (7, 161, 132), 0],
    ["3840", "Lavender Blue - LT", (178, 189, 234), 0],
    ["3813", "Blue Green - LT", (134, 195, 171), 0],
    ["3841", "Baby Blue - PALE", (217, 234, 242), 0],
    ["3814", "Aquamarine", (11, 134, 115), 0],
    ["3842", "Wedgewood - DK", (6, 80, 106), 0],
    ["3815", "Celadon Green - DK", (67, 114, 89), 0],
    ["3843", "Electric Blue", (40, 163, 222), 0],
    ["3816", "Celadon Green", (96, 147, 122), 0],
    ["3844", "Bright Turquoise - DK", (31, 127, 160), 0],
    ["3817", "Celadon Green - LT", (129, 198, 164), 0],
    ["3845", "Bright Turquoise - MED", (43, 173, 209), 0],
    ["3818", "Emerald Green - ULT VY DK", (0, 93, 46), 0],
    ["3846", "Bright Turquoise - LT", (94, 204, 236), 0],
    ["3819", "Moss Green - LT", (204, 201, 89), 0],
    ["3847", "Teal Green - DK", (24, 99, 88), 0],
    ["3820", "Straw - DK", (219, 165, 62), 0],
    ["3848", "Teal Green - MED", (32, 126, 114), 0],
    ["3821", "Straw", (235, 187, 82), 0],
    ["3849", "Teal Green - LT", (53, 177, 147), 0],
    ["3822", "Straw - LT", (247, 209, 105), 0],
    ["3850", "Bright Green - DK", (32, 139, 70), 0],
    ["3823", "Yellow - ULT PALE", (254, 245, 205), 0],
    ["3851", "Bright Green - LT", (97, 187, 132), 0],
    ["3824", "Apricot - LT", (252, 174, 153), 0],
    ["3852", "Straw - VY DK", (227, 167, 48), 0],
    ["3825", "Pumpkin - PALE", (254, 163, 112), 0],
    ["3853", "Autumn Gold - DK", (239, 129, 37), 0],
    ["3826", "Golden Brown", (177, 102, 51), 0],
    ["3854", "Autumn Gold - MED", (251, 172, 86), 0],
    ["3827", "Golden Brown - PALE", (234, 166, 100), 0],
    ["3855", "Autumn Gold - LT", (253, 223, 160), 0],
    ["3828", "Hazelnut Brown", (170, 124, 67), 0],
    ["3856", "Mahogany - ULT VY LT", (253, 190, 142), 0],
    ["3829", "Old Gold - VY DK", (167, 103, 29), 0],
    ["3857", "Rosewood - DK", (106, 47, 38), 0],
    ["3830", "Terra Cotta", (169, 65, 56), 0],
    ["3858", "Rosewood - MED", (128, 58, 50), 0],
    ["3831", "Raspberry - DK", (193, 43, 82), 0],
    ["3859", "Rosewood - LT", (186, 122, 108), 0],
    ["3832", "Raspberry - MED", (227, 99, 112), 0],
    ["3860", "Cocoa", (137, 99, 98), 0],
    ["3833", "Raspberry - LT", (234, 139, 150), 0],
    ["3861", "Cocoa - LT", (172, 133, 131), 0],
    ["3834", "Grape - DK", (106, 34, 88), 0],
    ["3862", "Mocha Beige - DK", (110, 73, 42), 0],
    ["3835", "Grape - MED", (146, 77, 120), 0],
    ["3863", "Mocha Beige - MED", (148, 114, 93), 0],
    ["3836", "Grape - LT", (197, 151, 185), 0],
    ["3864", "Mocha Beige - LT", (201, 170, 146), 0],
    ["3837", "Lavender - ULT DK", (138, 42, 143), 0],
    ["3865", "Winter White", (255, 253, 249), 0],
    ["3838", "Lavender Blue - DK", (96, 107, 173), 0],
    ["3866", "Mocha Brown - ULT VY LT", (240, 230, 215), 0],
    ["3880", "Medium Very Dark Shell Pink", (121, 60, 55), 0],
    ["3881", "Pale Avocado Green", (143, 164, 99), 0],
    ["3882", "Medium Light Cocoa", (103, 71, 50), 0],
    ["3883", "Medium Light Copper", (221, 111, 50), 0],
    ["3884", "Medium Light Pewter", (103, 110, 107), 0],
    ["3885", "Medium Very Dark Blue", (5, 66, 129), 0],
    ["3886", "Very Dark Plum", (108, 13, 83), 0],
    ["3887", "Ultra Very Dark Lavender", (99, 56, 136), 0],
    ["3888", "Medium Dark Antique Violet", (107, 91, 102), 0],
    ["3889", "Medium Light Lemon", (241, 220, 76), 0],
    ["3890", "Very Light Bright Turquoise", (56, 203, 238), 0],
    ["3891", "Very Dark Bright Turquoise", (5, 95, 157), 0],
    ["3892", "Medium Light Orange Spice", (246, 98, 9), 0],
    ["3893", "Very Light Mocha Beige", (203, 173, 151), 0],
    ["3894", "Very Light Parrot Green", (144, 172, 9), 0],
    ["3895", "Medium Dark Beaver Gray", (135, 132, 113), 0],
]

# create all possible blends
allow_diff_range = 50


def getBlends():
    blends = []
    pdb.gimp_message("Total colors:" + str(len(MASTER_DMC)))
    for x in range(
        0, len(MASTER_DMC)
    ):  # x points to index 1 to blend with y points to index 2
        # add original color no blend
        blends.append(MASTER_DMC[x])
        for y in range(x + 1, len(MASTER_DMC)):
            thread1 = MASTER_DMC[x]
            thread2 = MASTER_DMC[y]
            r = int(round((thread1[2][0] + thread2[2][0]) / 2.0))
            g = int(round((thread1[2][1] + thread2[2][1]) / 2.0))
            b = int(round((thread1[2][2] + thread2[2][2]) / 2.0))
            difr = abs(thread1[2][0] - thread2[2][0])
            difg = abs(thread1[2][1] - thread2[2][1])
            difb = abs(thread1[2][2] - thread2[2][2])
            # only allow to use as blend if colors are somewhat close together.
            if (
                difr <= allow_diff_range
                and difg <= allow_diff_range
                and difb <= allow_diff_range
            ):
                # stack on colors of thread1 and thread2 onto the end after 0 value for processing/drawing later
                thisblend = [
                    thread1[0] + ", " + thread2[0],
                    thread1[1] + ", " + thread2[1],
                    (r, g, b),
                    0,
                    thread1[2],
                    thread2[2],
                ]
                blends.append(thisblend)
    pdb.gimp_message("Total colors after creating blends:" + str(len(blends)))

    return blends


def getTriBlends():
    blends = []
    pdb.gimp_message("Total colors:" + str(len(MASTER_DMC)))
    for x in range(
        0, len(MASTER_DMC)
    ):  # x points to index 1 to blend with y points to index 2
        # add original color no blend
        blends.append(MASTER_DMC[x])
        for y in range(x + 1, len(MASTER_DMC)):
            thread1 = MASTER_DMC[x]
            thread2 = MASTER_DMC[y]
            difr = abs(thread1[2][0] - thread2[2][0])
            difg = abs(thread1[2][1] - thread2[2][1])
            difb = abs(thread1[2][2] - thread2[2][2])
            # only allow to use as blend if colors are somewhat close together.
            if (
                difr <= allow_diff_range
                and difg <= allow_diff_range
                and difb <= allow_diff_range
            ):
                r = int(round((thread1[2][0] + (thread2[2][0]) * 2) / 3.0))
                g = int(round((thread1[2][1] + (thread2[2][1]) * 2) / 3.0))
                b = int(round((thread1[2][2] + (thread2[2][2]) * 2) / 3.0))
                # stack on colors of thread1 and thread2 onto the end after 0 value for processing/drawing later
                thisblend = [
                    thread1[0] + ", " + thread2[0],
                    thread1[1] + ", " + thread2[1],
                    (r, g, b),
                    0,
                    thread1[2],
                    thread2[2],
                ]
                blends.append(thisblend)
                r = int(round(((thread1[2][0] * 2) + thread2[2][0]) / 3.0))
                g = int(round(((thread1[2][1] * 2) + thread2[2][1]) / 3.0))
                b = int(round(((thread1[2][2] * 2) + thread2[2][2]) / 3.0))
                # stack on colors of thread1 and thread2 onto the end after 0 value for processing/drawing later
                thisblend = [
                    thread2[0] + ", " + thread1[0],
                    thread2[1] + ", " + thread1[1],
                    (r, g, b),
                    0,
                    thread2[2],
                    thread1[2],
                ]
                blends.append(thisblend)
    pdb.gimp_message("Total colors after creating blends:" + str(len(blends)))

    return blends


def get4Blends():
    blends = []
    pdb.gimp_message("Total colors:" + str(len(MASTER_DMC)))
    for x in range(
        0, len(MASTER_DMC)
    ):  # x points to index 1 to blend with y points to index 2
        # add original color no blend
        blends.append(MASTER_DMC[x])
        for y in range(x + 1, len(MASTER_DMC)):
            thread1 = MASTER_DMC[x]
            thread2 = MASTER_DMC[y]
            difr = abs(thread1[2][0] - thread2[2][0])
            difg = abs(thread1[2][1] - thread2[2][1])
            difb = abs(thread1[2][2] - thread2[2][2])
            # only allow to use as blend if colors are somewhat close together.
            if (
                difr <= allow_diff_range
                and difg <= allow_diff_range
                and difb <= allow_diff_range
            ):
                r = int(round((thread1[2][0] * 2 + (thread2[2][0]) * 2) / 4.0))
                g = int(round((thread1[2][1] * 2 + (thread2[2][1]) * 2) / 4.0))
                b = int(round((thread1[2][2] * 2 + (thread2[2][2]) * 2) / 4.0))
                # stack on colors of thread1 and thread2 onto the end after 0 value for processing/drawing later
                thisblend = [
                    thread1[0] + ", " + thread2[0],
                    thread1[1] + ", " + thread2[1],
                    (r, g, b),
                    0,
                    thread1[2],
                    thread2[2],
                    2,
                ]
                blends.append(thisblend)

                r = int(round((thread1[2][0] + (thread2[2][0]) * 3) / 4.0))
                g = int(round((thread1[2][1] + (thread2[2][1]) * 3) / 4.0))
                b = int(round((thread1[2][2] + (thread2[2][2]) * 3) / 4.0))
                # stack on colors of thread1 and thread2 onto the end after 0 value for processing/drawing later
                thisblend = [
                    thread1[0] + ", " + thread2[0],
                    thread1[1] + ", " + thread2[1],
                    (r, g, b),
                    0,
                    thread1[2],
                    thread2[2],
                    1,
                ]
                blends.append(thisblend)

                r = int(round((thread1[2][0] * 3 + (thread2[2][0])) / 4.0))
                g = int(round((thread1[2][1] * 3 + (thread2[2][1])) / 4.0))
                b = int(round((thread1[2][2] * 3 + (thread2[2][2])) / 4.0))
                # stack on colors of thread1 and thread2 onto the end after 0 value for processing/drawing later
                thisblend = [
                    thread1[0] + ", " + thread2[0],
                    thread1[1] + ", " + thread2[1],
                    (r, g, b),
                    0,
                    thread2[2],
                    thread1[2],
                    1,
                ]
                blends.append(thisblend)
    pdb.gimp_message("Total colors after creating blends:" + str(len(blends)))

    return blends


def get5Blends():
    blends = []
    pdb.gimp_message("Total colors:" + str(len(MASTER_DMC)))
    for x in range(
        0, len(MASTER_DMC)
    ):  # x points to index 1 to blend with y points to index 2
        # add original color no blend
        blends.append(MASTER_DMC[x])
        for y in range(x + 1, len(MASTER_DMC)):
            thread1 = MASTER_DMC[x]
            thread2 = MASTER_DMC[y]
            difr = abs(thread1[2][0] - thread2[2][0])
            difg = abs(thread1[2][1] - thread2[2][1])
            difb = abs(thread1[2][2] - thread2[2][2])
            # only allow to use as blend if colors are somewhat close together.
            if (
                difr <= allow_diff_range
                and difg <= allow_diff_range
                and difb <= allow_diff_range
            ):
                r = int(round((thread1[2][0] + (thread2[2][0]) * 4) / 5.0))
                g = int(round((thread1[2][1] + (thread2[2][1]) * 4) / 5.0))
                b = int(round((thread1[2][2] + (thread2[2][2]) * 4) / 5.0))
                # stack on colors of thread1 and thread2 onto the end after 0 value for processing/drawing later
                thisblend = [
                    thread1[0] + ", " + thread2[0],
                    thread1[1] + ", " + thread2[1],
                    (r, g, b),
                    0,
                    thread1[2],
                    thread2[2],
                    1,
                ]
                blends.append(thisblend)

                r = int(round((thread1[2][0] * 4 + (thread2[2][0])) / 5.0))
                g = int(round((thread1[2][1] * 4 + (thread2[2][1])) / 5.0))
                b = int(round((thread1[2][2] * 4 + (thread2[2][2])) / 5.0))
                # stack on colors of thread1 and thread2 onto the end after 0 value for processing/drawing later
                thisblend = [
                    thread1[0] + ", " + thread2[0],
                    thread1[1] + ", " + thread2[1],
                    (r, g, b),
                    0,
                    thread2[2],
                    thread1[2],
                    1,
                ]
                blends.append(thisblend)

                r = int(round((thread1[2][0] * 2 + (thread2[2][0]) * 3) / 5.0))
                g = int(round((thread1[2][1] * 2 + (thread2[2][1]) * 3) / 5.0))
                b = int(round((thread1[2][2] * 2 + (thread2[2][2]) * 3) / 5.0))
                # stack on colors of thread1 and thread2 onto the end after 0 value for processing/drawing later
                thisblend = [
                    thread1[0] + ", " + thread2[0],
                    thread1[1] + ", " + thread2[1],
                    (r, g, b),
                    0,
                    thread1[2],
                    thread2[2],
                    2,
                ]
                blends.append(thisblend)

                r = int(round((thread1[2][0] * 3 + (thread2[2][0]) * 2) / 5.0))
                g = int(round((thread1[2][1] * 3 + (thread2[2][1]) * 2) / 5.0))
                b = int(round((thread1[2][2] * 3 + (thread2[2][2]) * 2) / 5.0))
                # stack on colors of thread1 and thread2 onto the end after 0 value for processing/drawing later
                thisblend = [
                    thread1[0] + ", " + thread2[0],
                    thread1[1] + ", " + thread2[1],
                    (r, g, b),
                    0,
                    thread2[2],
                    thread1[2],
                    2,
                ]
                blends.append(thisblend)
    pdb.gimp_message("Total colors after creating blends:" + str(len(blends)))

    return blends


def get6Blends():
    blends = []
    pdb.gimp_message("Total colors:" + str(len(MASTER_DMC)))
    for x in range(
        0, len(MASTER_DMC)
    ):  # x points to index 1 to blend with y points to index 2
        # add original color no blend
        blends.append(MASTER_DMC[x])
        for y in range(x + 1, len(MASTER_DMC)):
            thread1 = MASTER_DMC[x]
            thread2 = MASTER_DMC[y]
            difr = abs(thread1[2][0] - thread2[2][0])
            difg = abs(thread1[2][1] - thread2[2][1])
            difb = abs(thread1[2][2] - thread2[2][2])
            # only allow to use as blend if colors are somewhat close together.
            if (
                difr <= allow_diff_range
                and difg <= allow_diff_range
                and difb <= allow_diff_range
            ):
                r = int(round((thread1[2][0] + (thread2[2][0]) * 5) / 6.0))
                g = int(round((thread1[2][1] + (thread2[2][1]) * 5) / 6.0))
                b = int(round((thread1[2][2] + (thread2[2][2]) * 5) / 6.0))
                # stack on colors of thread1 and thread2 onto the end after 0 value for processing/drawing later
                thisblend = [
                    thread1[0] + ", " + thread2[0],
                    thread1[1] + ", " + thread2[1],
                    (r, g, b),
                    0,
                    thread1[2],
                    thread2[2],
                    1,
                ]
                blends.append(thisblend)

                r = int(round((thread1[2][0] * 5 + (thread2[2][0])) / 6.0))
                g = int(round((thread1[2][1] * 5 + (thread2[2][1])) / 6.0))
                b = int(round((thread1[2][2] * 5 + (thread2[2][2])) / 6.0))
                # stack on colors of thread1 and thread2 onto the end after 0 value for processing/drawing later
                thisblend = [
                    thread1[0] + ", " + thread2[0],
                    thread1[1] + ", " + thread2[1],
                    (r, g, b),
                    0,
                    thread2[2],
                    thread1[2],
                    1,
                ]
                blends.append(thisblend)

                r = int(round((thread1[2][0] * 2 + (thread2[2][0]) * 4) / 6.0))
                g = int(round((thread1[2][1] * 2 + (thread2[2][1]) * 4) / 6.0))
                b = int(round((thread1[2][2] * 2 + (thread2[2][2]) * 4) / 6.0))
                # stack on colors of thread1 and thread2 onto the end after 0 value for processing/drawing later
                thisblend = [
                    thread1[0] + ", " + thread2[0],
                    thread1[1] + ", " + thread2[1],
                    (r, g, b),
                    0,
                    thread1[2],
                    thread2[2],
                    2,
                ]
                blends.append(thisblend)

                r = int(round((thread1[2][0] * 4 + (thread2[2][0]) * 2) / 6.0))
                g = int(round((thread1[2][1] * 4 + (thread2[2][1]) * 2) / 6.0))
                b = int(round((thread1[2][2] * 4 + (thread2[2][2]) * 2) / 6.0))
                # stack on colors of thread1 and thread2 onto the end after 0 value for processing/drawing later
                thisblend = [
                    thread1[0] + ", " + thread2[0],
                    thread1[1] + ", " + thread2[1],
                    (r, g, b),
                    0,
                    thread2[2],
                    thread1[2],
                    2,
                ]
                blends.append(thisblend)

                r = int(round((thread1[2][0] * 3 + (thread2[2][0]) * 3) / 6.0))
                g = int(round((thread1[2][1] * 3 + (thread2[2][1]) * 3) / 6.0))
                b = int(round((thread1[2][2] * 3 + (thread2[2][2]) * 3) / 6.0))
                # stack on colors of thread1 and thread2 onto the end after 0 value for processing/drawing later
                thisblend = [
                    thread1[0] + ", " + thread2[0],
                    thread1[1] + ", " + thread2[1],
                    (r, g, b),
                    0,
                    thread1[2],
                    thread2[2],
                    3,
                ]
                blends.append(thisblend)

    pdb.gimp_message("Total colors after creating blends:" + str(len(blends)))

    return blends


def python_cross_stitch_tt(
    image,
    layer,
    allow_blend,
    num_colors,
    color_dithering,
    interpolation,
    match_method,
    hor_stitches,
    stitches_per_square,
    square_grid_color,
    stitch_grid_color,
):
    # allow_blend = 1
    # DMC information [DMC,Name,RGB,distance] distance is to be determined/calculated later and used to sort for closest match color
    if allow_blend == 1:
        DMC = getBlends()
    elif allow_blend == 2:
        DMC = getTriBlends()  # 3 strand blend.
    elif allow_blend == 3:
        DMC = get4Blends()
    elif allow_blend == 4:
        DMC = get5Blends()
    elif allow_blend == 5:
        DMC = get6Blends()
    else:
        DMC = MASTER_DMC

    SYM2 = [
        "0",
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "A",
        "B",
        "C",
        "D",
        "E",
        "F",
        "10",
        "11",
        "12",
        "13",
        "14",
        "15",
        "16",
        "17",
        "18",
        "19",
        "1A",
        "1B",
        "1C",
        "1D",
        "1E",
        "1F",
        "20",
        "21",
        "22",
        "23",
        "24",
        "25",
        "26",
        "27",
        "28",
        "29",
        "2A",
        "2B",
        "2C",
        "2D",
        "2E",
        "2F",
        "30",
        "31",
        "32",
        "33",
        "34",
        "35",
        "36",
        "37",
        "38",
        "39",
        "3A",
        "3B",
        "3C",
        "3D",
        "3E",
        "3F",
        "40",
        "41",
        "42",
        "43",
        "44",
        "45",
        "46",
        "47",
        "48",
        "49",
        "4A",
        "4B",
        "4C",
        "4D",
        "4E",
        "4F",
        "50",
        "51",
        "52",
        "53",
        "54",
        "55",
        "56",
        "57",
        "58",
        "59",
        "5A",
        "5B",
        "5C",
        "5D",
        "5E",
        "5F",
        "60",
        "61",
        "62",
        "63",
        "64",
        "65",
        "66",
        "67",
        "68",
        "69",
        "6A",
        "6B",
        "6C",
        "6D",
        "6E",
        "6F",
        "70",
        "71",
        "72",
        "73",
        "74",
        "75",
        "76",
        "77",
        "78",
        "79",
        "7A",
        "7B",
        "7C",
        "7D",
        "7E",
        "7F",
        "80",
        "81",
        "82",
        "83",
        "84",
        "85",
        "86",
        "87",
        "88",
        "89",
        "8A",
        "8B",
        "8C",
        "8D",
        "8E",
        "8F",
        "90",
        "91",
        "92",
        "93",
        "94",
        "95",
        "96",
        "97",
        "98",
        "99",
        "9A",
        "9B",
        "9C",
        "9D",
        "9E",
        "9F",
        "A0",
        "A1",
        "A2",
        "A3",
        "A4",
        "A5",
        "A6",
        "A7",
        "A8",
        "A9",
        "AA",
        "AB",
        "AC",
        "AD",
        "AE",
        "AF",
        "B0",
        "B1",
        "B2",
        "B3",
        "B4",
        "B5",
        "B6",
        "B7",
        "B8",
        "B9",
        "BA",
        "BB",
        "BC",
        "BD",
        "BE",
        "BF",
        "C0",
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "CA",
        "CB",
        "CC",
        "CD",
        "CE",
        "CF",
        "D0",
        "D1",
        "D2",
        "D3",
        "D4",
        "D5",
        "D6",
        "D7",
        "D8",
        "D9",
        "DA",
        "DB",
        "DC",
        "DD",
        "DE",
        "DF",
        "E0",
        "E1",
        "E2",
        "E3",
        "E4",
        "E5",
        "E6",
        "E7",
        "E8",
        "E9",
        "EA",
        "EB",
        "EC",
        "ED",
        "EE",
        "EF",
        "F0",
        "F1",
        "F2",
        "F3",
        "F4",
        "F5",
        "F6",
        "F7",
        "F8",
        "F9",
        "FA",
        "FB",
        "FC",
        "FD",
        "FE",
        "FF",
    ]
    SYM = [
        "☀",
        "☁",
        "☂",
        "★",
        "☆",
        "☇",
        "☈",
        "☉",
        "☊",
        "☋",
        "☌",
        "☍",
        "☎",
        "☏",
        "☐",
        "☑",
        "☒",
        "☓",
        "☔",
        "☕",
        "☖",
        "☗",
        "☘",
        "☚",
        "☛",
        "☜",
        "☝",
        "☞",
        "☟",
        "G",
        "☠",
        "☡",
        "☢",
        "☣",
        "☤",
        "☥",
        "☦",
        "☧",
        "☨",
        "☩",
        "☪",
        "☫",
        "☬",
        "☭",
        "☮",
        "☯",
        "S",
        "☰",
        "☸",
        "☹",
        "☺",
        "☻",
        "☼",
        "☽",
        "☾",
        "☿",
        "H",
        "♀",
        "♁",
        "♂",
        "♃",
        "♄",
        "♅",
        "♆",
        "♇",
        "♈",
        "♉",
        "♊",
        "♋",
        "♌",
        "♍",
        "♎",
        "♏",
        "I",
        "♐",
        "♑",
        "♒",
        "♓",
        "♔",
        "♕",
        "♖",
        "♗",
        "♘",
        "♙",
        "♚",
        "♛",
        "♜",
        "♝",
        "♞",
        "♟",
        "J",
        "♠",
        "♡",
        "♢",
        "♣",
        "♤",
        "♥",
        "♦",
        "♧",
        "♨",
        "♩",
        "♪",
        "♫",
        "♬",
        "♭",
        "♮",
        "♯",
        "K",
        "♰",
        "♱",
        "♲",
        "♳",
        "♺",
        "♻",
        "♼",
        "♽",
        "♾",
        "♿",
        "L",
        "⚀",
        "⚁",
        "⚂",
        "⚃",
        "⚄",
        "⚅",
        "⚆",
        "⚇",
        "⚈",
        "⚉",
        "⚌",
        "⚏",
        "M",
        "⚐",
        "⚑",
        "⚒",
        "⚓",
        "⚔",
        "⚕",
        "⚖",
        "⚗",
        "⚘",
        "⚙",
        "⚚",
        "⚛",
        "⚜",
        "⚝",
        "⚞",
        "⚟",
        "N",
        "⚠",
        "⚡",
        "⚢",
        "⚣",
        "⚤",
        "⚥",
        "⚦",
        "⚧",
        "⚨",
        "⚩",
        "⚪",
        "⚫",
        "⚬",
        "⚭",
        "⚮",
        "⚯",
        "P",
        "⚰",
        "⚱",
        "⚲",
        "⚳",
        "⚴",
        "⚵",
        "⚶",
        "⚷",
        "⚸",
        "⚹",
        "⚺",
        "⚻",
        "⚼",
        "⚽",
        "⚾",
        "⚿",
        "R",
        "⛀",
        "⛁",
        "⛂",
        "⛃",
        "⛄",
        "⛅",
        "⛆",
        "⛇",
        "⛈",
        "⛉",
        "⛊",
        "⛋",
        "⛌",
        "⛍",
        "⛎",
        "⛏",
        "T",
        "⛐",
        "⛑",
        "⛒",
        "⛓",
        "⛔",
        "⛕",
        "⛖",
        "⛗",
        "⛘",
        "⛙",
        "⛚",
        "⛛",
        "⛜",
        "⛝",
        "⛞",
        "⛟",
        "U",
        "⛠",
        "⛡",
        "⛢",
        "⛣",
        "⛤",
        "⛨",
        "⛩",
        "⛪",
        "⛫",
        "⛬",
        "⛭",
        "⛮",
        "⛯",
        "V",
        "⛰",
        "⛱",
        "⛲",
        "⛳",
        "⛴",
        "⛵",
        "⛶",
        "⛷",
        "⛸",
        "⛹",
        "⛺",
        "⛻",
        "⛼",
        "⛽",
        "⛾",
        "⛿",
    ]
    SYM = SYM + SYM2
    pdb.gimp_image_undo_group_start(image)
    pdb.gimp_context_push()
    # make a new image of active layer
    new_image = pdb.gimp_image_new(layer.width, layer.height, RGB)
    new_display = pdb.gimp_display_new(new_image)
    # copy layer to new image
    layer_copy = pdb.gimp_layer_new_from_drawable(layer, new_image)
    pdb.gimp_image_insert_layer(new_image, layer_copy, None, 0)

    # scale it down based on horizontal stitches
    scale = float(hor_stitches) / layer.width
    hor_stitches = int(hor_stitches)
    vert_stitches = int(layer.height * scale)
    total_cells = int(hor_stitches) * int(vert_stitches)
    total_stitches = 0
    pdb.gimp_context_set_interpolation(
        interpolation
    )  # possible TODO: this could be an option, Done set as option now
    pdb.gimp_image_scale(new_image, hor_stitches, vert_stitches)
    # reduce number of colors
    pdb.gimp_convert_indexed(
        new_image, color_dithering, MAKE_PALETTE, num_colors, FALSE, FALSE, ""
    )

    # get color map
    num_bytes, colormap = pdb.gimp_image_get_colormap(new_image)
    # converts it to indexed tuples
    colormap = indexed_color(colormap)

    dmcmap = []
    # match color to DMCs
    for c in range(0, len(colormap)):
        # grab RGB info to calculate distance.
        R = colormap[c][0]
        G = colormap[c][1]
        B = colormap[c][2]
        for d in range(0, len(DMC)):
            if match_method == 0:  # Perceptive distance calculation
                DMC[d][3] = (
                    ((R - DMC[d][2][0]) * 0.3) ** 2
                    + ((G - DMC[d][2][1]) * 0.59) ** 2
                    + ((B - DMC[d][2][2]) * 0.11) ** 2
                )
            elif match_method == 1:  # Regular distance calculation
                DMC[d][3] = (
                    (R - DMC[d][2][0]) ** 2
                    + (G - DMC[d][2][1]) ** 2
                    + (B - DMC[d][2][2]) ** 2
                )
            elif match_method == 2:  # Delta-E0
                DMC[d][3] = deltaE(rgb2lab((R, G, B)), rgb2lab(DMC[d][2]))

        DMC.sort(key=lambda x: x[3])
        # add first DMC (closest match) to dmcmap.
        dmcmap.append(DMC[0][2])
    # get unique colors to go through to pick later.
    uniquecolors = list(set(dmcmap))
    dmcmap = flatten_color(dmcmap)
    pdb.gimp_image_set_colormap(new_image, len(dmcmap), dmcmap)

    # scale our image so that each stitch is stitch_dimension large
    new_width = new_image.width * stitch_dimension
    new_height = new_image.height * stitch_dimension
    pdb.gimp_context_set_interpolation(
        INTERPOLATION_NONE
    )  # possible TODO: this could be an option.
    pdb.gimp_image_scale(new_image, new_width, new_height)

    # converts back to RGB so we can work with other colors.
    pdb.gimp_image_convert_rgb(new_image)
    # add white layer with opacity so that black stitch layers would stand out above.
    white_layer = pdb.gimp_layer_new(
        new_image,
        new_image.width,
        new_image.height,
        RGBA_IMAGE,
        "White overlay",
        30,
        NORMAL_MODE,
    )
    pdb.gimp_image_insert_layer(new_image, white_layer, None, 0)
    # pdb.gimp_drawable_edit_fill(white_layer,WHITE_FILL)
    # do below instead of above edit fill for speed
    save_background_color = pdb.gimp_context_get_background()
    save_foreground_color = pdb.gimp_context_get_foreground()
    pdb.gimp_context_set_background((255, 255, 255))
    pdb.gimp_context_set_foreground((255, 255, 255))
    x1, y1, x2, y2 = 0, 0, 2, 2
    pdb.gimp_edit_blend(
        white_layer,
        BLEND_FG_BG_RGB,
        LAYER_MODE_NORMAL,
        GRADIENT_LINEAR,
        100,
        0,
        REPEAT_NONE,
        FALSE,
        FALSE,
        3,
        0.2,
        FALSE,
        x1,
        y1,
        x2,
        y2,
    )
    pdb.gimp_context_set_background(save_background_color)
    pdb.gimp_context_set_foreground(save_foreground_color)
    # add stitch grid
    stitchgrid_layer = pdb.gimp_layer_new(
        new_image,
        new_image.width,
        new_image.height,
        RGBA_IMAGE,
        "Stitch grid",
        100,
        NORMAL_MODE,
    )
    pdb.gimp_image_insert_layer(new_image, stitchgrid_layer, None, 0)
    pdb.plug_in_grid(
        new_image,
        stitchgrid_layer,
        1,
        stitch_dimension,
        0,
        stitch_grid_color,
        255,
        1,
        stitch_dimension,
        0,
        stitch_grid_color,
        255,
        0,
        0,
        0,
        stitch_grid_color,
        255,
    )
    # add square grid
    squaregrid_layer = pdb.gimp_layer_new(
        new_image,
        new_image.width,
        new_image.height,
        RGBA_IMAGE,
        "Square grid",
        100,
        NORMAL_MODE,
    )
    pdb.gimp_image_insert_layer(new_image, squaregrid_layer, None, 0)
    pdb.plug_in_grid(
        new_image,
        squaregrid_layer,
        2,
        stitch_dimension * stitches_per_square,
        0,
        square_grid_color,
        255,
        2,
        stitch_dimension * stitches_per_square,
        0,
        square_grid_color,
        255,
        0,
        0,
        0,
        square_grid_color,
        255,
    )

    # pdb.gimp_context_set_pattern("Clipboard") #below calls set pattern to "Clipboard" even in different languages where it's not called "Clipboard"
    pdb.gimp_context_set_pattern(pdb.gimp_patterns_list("")[1][0])
    pdb.gimp_context_set_opacity(100)
    pdb.gimp_context_set_paint_mode(LAYER_MODE_NORMAL)
    pdb.gimp_context_set_antialias(True)
    pdb.gimp_context_set_sample_merged(False)
    pdb.gimp_context_set_sample_criterion(SELECT_CRITERION_COMPOSITE)
    pdb.gimp_context_set_sample_threshold(0)
    pdb.gimp_context_set_sample_transparent(True)
    # pdb.gimp_drawable_fill(wavy_layer,PATTERN_FILL)

    # settings to set before using select_color
    """pdb.gimp_context_set_antialias(True)
	pdb.gimp_context_set_feather(False)
	pdb.gimp_context_set_feather_radius(0,0)
	pdb.gimp_context_set_sample_merged(False)
	pdb.gimp_context_set_sample_criterion(SELECT_CRITERION_COMPOSITE)
	pdb.gimp_context_set_sample_threshold(0)
	pdb.gimp_context_set_sample_transparent(True)
	"""
    # 2.10 hack
    pdb.gimp_context_set_sample_merged(
        1
    )  # later we'll be using threshold of a visible layer
    pdb.gimp_context_set_sample_threshold(0)

    # make a new image of active layer
    thread_image = pdb.gimp_image_new(
        1200, stitch_dimension * (len(uniquecolors) + 5), RGB
    )  # +5 lines 1 for dimension in stitches 3 or aida counts and 1 blank line at bottom.
    new_display = pdb.gimp_display_new(thread_image)
    # copy layer to new image
    thread_layer = pdb.gimp_layer_new(
        thread_image,
        thread_image.width,
        thread_image.height,
        RGBA_IMAGE,
        "Thread Info",
        100,
        NORMAL_MODE,
    )
    pdb.gimp_image_insert_layer(thread_image, thread_layer, None, 0)
    # pdb.gimp_drawable_edit_fill(thread_layer,WHITE_FILL)
    save_background_color = pdb.gimp_context_get_background()
    save_foreground_color = pdb.gimp_context_get_foreground()
    pdb.gimp_context_set_background((255, 255, 255))
    pdb.gimp_context_set_foreground((255, 255, 255))
    pdb.gimp_edit_blend(
        thread_layer,
        BLEND_FG_BG_RGB,
        LAYER_MODE_NORMAL,
        GRADIENT_LINEAR,
        100,
        0,
        REPEAT_NONE,
        FALSE,
        FALSE,
        3,
        0.2,
        FALSE,
        x1,
        y1,
        x2,
        y2,
    )
    pdb.gimp_context_set_background(save_background_color)
    pdb.gimp_context_set_foreground(save_foreground_color)

    gimp.progress_init("Rendering stich patterns...")
    layerid = 0
    for u in range(0, len(uniquecolors)):
        layerid += 1
        # find the DMC color info
        DMC_index = 0
        # pdb.gimp_message("find DMC color")
        for i in range(0, len(DMC)):
            if (
                (DMC[i][2][0] == uniquecolors[u][0])
                and (DMC[i][2][1] == uniquecolors[u][1])
                and (DMC[i][2][2] == uniquecolors[u][2])
            ):
                DMC_index = i  # save the index found at
                break
        pdb.gimp_context_set_default_colors()
        # create a font layer for each color
        # pdb.gimp_message("running text")
        floating_text = pdb.gimp_text_fontname(
            new_image, white_layer, 0, 0, SYM[u], 0, True, 21, 0, "Tahoma"
        )
        pdb.gimp_floating_sel_to_layer(floating_text)
        pdb.plug_in_autocrop_layer(new_image, floating_text)
        # center text on its layer and resize to stitch dimension
        offsetx = int(float(stitch_dimension - floating_text.width) / 2)
        offsety = int(float(stitch_dimension - floating_text.height) / 2)
        pdb.gimp_layer_resize(
            floating_text, stitch_dimension, stitch_dimension, offsetx, offsety
        )
        pdb.gimp_layer_set_offsets(floating_text, 0, 0)
        pdb.gimp_selection_all(new_image)
        pdb.gimp_edit_copy(floating_text)

        # reset the layer size to use it instead of creating a new one
        pdb.gimp_layer_resize(
            floating_text, white_layer.width, white_layer.height, 0, 0
        )
        pdb.gimp_drawable_edit_fill(floating_text, PATTERN_FILL)
        # pdb.gimp_drawable_edit_bucket_fill(floating_text,FILL_PATTERN,0,0)
        # select the color, invert then clear area to reveal just this layer
        # pdb.gimp_image_select_color(new_image,CHANNEL_OP_REPLACE,layer_copy,uniquecolors[u])

        # use old method instead of HACK BELOW which is too slow.
        pdb.gimp_by_color_select(
            layer_copy, uniquecolors[u], 0, CHANNEL_OP_REPLACE, TRUE, FALSE, 0, FALSE
        )
        # BEGIN of 2.10 HACK
        # select the color, invert then clear area to reveal just this laye
        """pdb.gimp_selection_none(new_image)
		pdb.gimp_context_set_foreground(uniquecolors[u])
		# in 2.10 select colors seem to not select the one color
		# fix 
		
		# turn off visibility and select by difference hack.
		
		for l in range(0,len(new_image.layers)-1):
			new_image.layers[l].visible = 0
		#pdb.gimp_message("create diff layer")	
		diff_layer = pdb.gimp_layer_new(new_image,new_image.width,new_image.height,RGBA_IMAGE,"diff",100,LAYER_MODE_DIFFERENCE_LEGACY)
		pdb.gimp_image_insert_layer(new_image,diff_layer,None,0)
		#pdb.gimp_drawable_edit_fill(diff_layer,FILL_FOREGROUND)
		#pdb.gimp_message("fill diff layer with unique color")
		save_background_color = pdb.gimp_context_get_background()
		save_foreground_color = pdb.gimp_context_get_foreground()
		pdb.gimp_context_set_background(uniquecolors[u])
		pdb.gimp_context_set_foreground(uniquecolors[u])
		pdb.gimp_edit_blend(diff_layer,BLEND_FG_BG_RGB,LAYER_MODE_NORMAL,GRADIENT_LINEAR,100,0,REPEAT_NONE,FALSE,FALSE,3,0.2,FALSE,x1,y1,x2,y2)
		pdb.gimp_context_set_background(save_background_color)
		pdb.gimp_context_set_foreground(save_foreground_color)
		#pdb.gimp_message("visible layer")
		visible_layer = pdb.gimp_layer_new_from_visible(new_image,new_image,"visible")
		pdb.gimp_image_insert_layer(new_image,visible_layer,None,0)
		#pdb.gimp_message("threshold")
		pdb.gimp_drawable_threshold(visible_layer,HISTOGRAM_VALUE,1.0/255,1.0)
		#pdb.gimp_message("select color")
		#pdb.gimp_image_select_color(new_image,CHANNEL_OP_REPLACE,layer_copy,(0,0,0))
		pdb.gimp_by_color_select(visible_layer,(0,0,0),1,CHANNEL_OP_REPLACE,TRUE,FALSE,0,FALSE)
		"""
        # get stitch count
        # pdb.gimp_message("historgram")
        _mean, _std_dev, _median, _pixels, _count, _percentile = (
            pdb.gimp_drawable_histogram(layer_copy, HISTOGRAM_VALUE, 0, 1.0)
        )
        stitch_count = int(_count / (stitch_dimension * stitch_dimension))
        total_stitches += stitch_count

        """pdb.gimp_image_remove_layer(new_image,diff_layer)
		pdb.gimp_image_remove_layer(new_image,visible_layer)
		"""
        # END of 2.10 HACK

        # saves to channel for replace DMC colors script to be able to run multiple times.
        # channel = pdb.gimp_selection_save(new_image)
        # pdb.gimp_item_set_name(channel,"[" + SYM[u] + "]")
        # pdb.gimp_message("selection invert")
        pdb.gimp_selection_invert(new_image)
        pdb.gimp_edit_clear(floating_text)
        DMC_name = (
            str(layerid)
            + "."
            + "["
            + SYM[u]
            + "] "
            + DMC[DMC_index][0]
            + " "
            + DMC[DMC_index][1]
        )
        pdb.gimp_item_set_name(
            floating_text,
            str(layerid) + "." + "[" + SYM[u] + "] " + str(uniquecolors[u]),
        )

        # show thread info
        pdb.gimp_context_set_foreground(uniquecolors[u])
        pdb.gimp_image_select_rectangle(
            thread_image,
            CHANNEL_OP_REPLACE,
            10,
            u * stitch_dimension,
            100,
            stitch_dimension,
        )
        # pdb.gimp_drawable_edit_fill(thread_layer,FOREGROUND_FILL)
        # pdb.gimp_message("thread layer blend")
        save_background_color = pdb.gimp_context_get_background()
        save_foreground_color = pdb.gimp_context_get_foreground()
        pdb.gimp_context_set_background(uniquecolors[u])
        pdb.gimp_context_set_foreground(uniquecolors[u])
        pdb.gimp_edit_blend(
            thread_layer,
            BLEND_FG_BG_RGB,
            LAYER_MODE_NORMAL,
            GRADIENT_LINEAR,
            100,
            0,
            REPEAT_NONE,
            FALSE,
            FALSE,
            3,
            0.2,
            FALSE,
            x1,
            y1,
            x2,
            y2,
        )
        strandinfo = ""  # default as showing nothing

        if (
            len(DMC[DMC_index]) > 6
        ):  # if it has more than 6 elements it means it's a 4,5 or 6 blend we show strand info
            firststrands = DMC[DMC_index][6]
            secondstrands = (allow_blend + 1) - firststrands
            strandinfo = " [" + str(firststrands) + "+" + str(secondstrands) + "]"

        if (
            len(DMC[DMC_index]) >= 6
        ):  # it's a blend color redraw rectangle with 2 colors
            thread1color = DMC[DMC_index][4]
            thread2color = DMC[DMC_index][5]
            if (allow_blend == 1) or (
                allow_blend == 3 and DMC[DMC_index][6] == 2
            ):  # 50/50 blend or 4thblend of 2+2
                # draw whole rectangle with thread1color
                pdb.gimp_image_select_rectangle(
                    thread_image,
                    CHANNEL_OP_REPLACE,
                    10,
                    u * stitch_dimension,
                    100,
                    stitch_dimension,
                )
                pdb.gimp_context_set_background(thread1color)
                pdb.gimp_context_set_foreground(thread1color)
                pdb.gimp_edit_blend(
                    thread_layer,
                    BLEND_FG_BG_RGB,
                    LAYER_MODE_NORMAL,
                    GRADIENT_LINEAR,
                    100,
                    0,
                    REPEAT_NONE,
                    FALSE,
                    FALSE,
                    3,
                    0.2,
                    FALSE,
                    x1,
                    y1,
                    x2,
                    y2,
                )
                # draw half rectangle with thread2color
                pdb.gimp_image_select_rectangle(
                    thread_image,
                    CHANNEL_OP_REPLACE,
                    60,
                    u * stitch_dimension,
                    50,
                    stitch_dimension,
                )
                pdb.gimp_context_set_background(thread2color)
                pdb.gimp_context_set_foreground(thread2color)
                pdb.gimp_edit_blend(
                    thread_layer,
                    BLEND_FG_BG_RGB,
                    LAYER_MODE_NORMAL,
                    GRADIENT_LINEAR,
                    100,
                    0,
                    REPEAT_NONE,
                    FALSE,
                    FALSE,
                    3,
                    0.2,
                    FALSE,
                    x1,
                    y1,
                    x2,
                    y2,
                )
            elif allow_blend == 2:  # Third blend
                # draw whole rectangle with thread2color
                pdb.gimp_image_select_rectangle(
                    thread_image,
                    CHANNEL_OP_REPLACE,
                    10,
                    u * stitch_dimension,
                    100,
                    stitch_dimension,
                )
                pdb.gimp_context_set_background(thread2color)
                pdb.gimp_context_set_foreground(thread2color)
                pdb.gimp_edit_blend(
                    thread_layer,
                    BLEND_FG_BG_RGB,
                    LAYER_MODE_NORMAL,
                    GRADIENT_LINEAR,
                    100,
                    0,
                    REPEAT_NONE,
                    FALSE,
                    FALSE,
                    3,
                    0.2,
                    FALSE,
                    x1,
                    y1,
                    x2,
                    y2,
                )
                # draw 1/3 rectangle with thread1color
                pdb.gimp_image_select_rectangle(
                    thread_image,
                    CHANNEL_OP_REPLACE,
                    10,
                    u * stitch_dimension,
                    33,
                    stitch_dimension,
                )
                pdb.gimp_context_set_background(thread1color)
                pdb.gimp_context_set_foreground(thread1color)
                pdb.gimp_edit_blend(
                    thread_layer,
                    BLEND_FG_BG_RGB,
                    LAYER_MODE_NORMAL,
                    GRADIENT_LINEAR,
                    100,
                    0,
                    REPEAT_NONE,
                    FALSE,
                    FALSE,
                    3,
                    0.2,
                    FALSE,
                    x1,
                    y1,
                    x2,
                    y2,
                )
            elif (allow_blend == 3) and (DMC[DMC_index][6] == 1):
                # draw whole rectangle with thread2color
                pdb.gimp_image_select_rectangle(
                    thread_image,
                    CHANNEL_OP_REPLACE,
                    10,
                    u * stitch_dimension,
                    100,
                    stitch_dimension,
                )
                pdb.gimp_context_set_background(thread2color)
                pdb.gimp_context_set_foreground(thread2color)
                pdb.gimp_edit_blend(
                    thread_layer,
                    BLEND_FG_BG_RGB,
                    LAYER_MODE_NORMAL,
                    GRADIENT_LINEAR,
                    100,
                    0,
                    REPEAT_NONE,
                    FALSE,
                    FALSE,
                    3,
                    0.2,
                    FALSE,
                    x1,
                    y1,
                    x2,
                    y2,
                )
                # draw 1/4 rectangle with thread1color
                pdb.gimp_image_select_rectangle(
                    thread_image,
                    CHANNEL_OP_REPLACE,
                    10,
                    u * stitch_dimension,
                    25,
                    stitch_dimension,
                )
                pdb.gimp_context_set_background(thread1color)
                pdb.gimp_context_set_foreground(thread1color)
                pdb.gimp_edit_blend(
                    thread_layer,
                    BLEND_FG_BG_RGB,
                    LAYER_MODE_NORMAL,
                    GRADIENT_LINEAR,
                    100,
                    0,
                    REPEAT_NONE,
                    FALSE,
                    FALSE,
                    3,
                    0.2,
                    FALSE,
                    x1,
                    y1,
                    x2,
                    y2,
                )
            elif (allow_blend == 4) or (allow_blend == 5):  # 5-strand or 6 strand
                # draw whole rectangle with thread2color
                pdb.gimp_image_select_rectangle(
                    thread_image,
                    CHANNEL_OP_REPLACE,
                    10,
                    u * stitch_dimension,
                    100,
                    stitch_dimension,
                )
                pdb.gimp_context_set_background(thread2color)
                pdb.gimp_context_set_foreground(thread2color)
                pdb.gimp_edit_blend(
                    thread_layer,
                    BLEND_FG_BG_RGB,
                    LAYER_MODE_NORMAL,
                    GRADIENT_LINEAR,
                    100,
                    0,
                    REPEAT_NONE,
                    FALSE,
                    FALSE,
                    3,
                    0.2,
                    FALSE,
                    x1,
                    y1,
                    x2,
                    y2,
                )
                # draw (strands/(allow_blend+1)) rectangle with thread1color
                pdb.gimp_image_select_rectangle(
                    thread_image,
                    CHANNEL_OP_REPLACE,
                    10,
                    u * stitch_dimension,
                    100.0 / (allow_blend + 1) * DMC[DMC_index][6],
                    stitch_dimension,
                )
                pdb.gimp_context_set_background(thread1color)
                pdb.gimp_context_set_foreground(thread1color)
                pdb.gimp_edit_blend(
                    thread_layer,
                    BLEND_FG_BG_RGB,
                    LAYER_MODE_NORMAL,
                    GRADIENT_LINEAR,
                    100,
                    0,
                    REPEAT_NONE,
                    FALSE,
                    FALSE,
                    3,
                    0.2,
                    FALSE,
                    x1,
                    y1,
                    x2,
                    y2,
                )

        pdb.gimp_context_set_background(save_background_color)
        pdb.gimp_context_set_foreground(save_foreground_color)
        # pdb.gimp_message("fontname thread layer")
        pdb.gimp_context_set_default_colors()
        floating_text = pdb.gimp_text_fontname(
            thread_image,
            thread_layer,
            120,
            u * stitch_dimension,
            DMC_name + strandinfo + " [" + str(stitch_count) + " stitches]",
            0,
            True,
            21,
            0,
            "Tahoma",
        )
        pdb.gimp_floating_sel_anchor(floating_text)
        # update progress bar.
        gimp.progress_update(1.0 * u / len(uniquecolors))
    # output dimensions at the end like how many stitches X how many stitches
    floating_text = pdb.gimp_text_fontname(
        thread_image,
        thread_layer,
        120,
        (u + 1) * stitch_dimension,
        "Dimension:"
        + str(int(hor_stitches))
        + " by "
        + str(int(vert_stitches))
        + " ["
        + str(total_stitches)
        + " stitches/"
        + str(total_cells)
        + " cells]",
        0,
        True,
        21,
        0,
        "Tahoma",
    )
    pdb.gimp_floating_sel_anchor(floating_text)
    # output aida lines
    # "{:.2f}".format(3.1415926)

    inchx = hor_stitches / 14.0
    inchy = vert_stitches / 14.0
    cmx = inchx * 2.54
    cmy = inchy * 2.54
    inchx = "{:.2f}".format(inchx) + '"'
    inchy = "{:.2f}".format(inchy) + '"'
    cmx = "{:.2f}".format(cmx) + "cm"
    cmy = "{:.2f}".format(cmy) + "cm"
    floating_text = pdb.gimp_text_fontname(
        thread_image,
        thread_layer,
        120,
        (u + 2) * stitch_dimension,
        "Aida 14 count: " + inchx + " by " + inchy + ", " + cmx + " by " + cmy,
        0,
        True,
        18,
        0,
        "Tahoma",
    )
    pdb.gimp_floating_sel_anchor(floating_text)
    inchx = hor_stitches / 16.0
    inchy = vert_stitches / 16.0
    cmx = inchx * 2.54
    cmy = inchy * 2.54
    inchx = "{:.2f}".format(inchx) + '"'
    inchy = "{:.2f}".format(inchy) + '"'
    cmx = "{:.2f}".format(cmx) + "cm"
    cmy = "{:.2f}".format(cmy) + "cm"
    floating_text = pdb.gimp_text_fontname(
        thread_image,
        thread_layer,
        120,
        (u + 3) * stitch_dimension,
        "Aida 16 count: " + inchx + " by " + inchy + ", " + cmx + " by " + cmy,
        0,
        True,
        18,
        0,
        "Tahoma",
    )
    pdb.gimp_floating_sel_anchor(floating_text)
    inchx = hor_stitches / 18.0
    inchy = vert_stitches / 18.0
    cmx = inchx * 2.54
    cmy = inchy * 2.54
    inchx = "{:.2f}".format(inchx) + '"'
    inchy = "{:.2f}".format(inchy) + '"'
    cmx = "{:.2f}".format(cmx) + "cm"
    cmy = "{:.2f}".format(cmy) + "cm"
    floating_text = pdb.gimp_text_fontname(
        thread_image,
        thread_layer,
        120,
        (u + 4) * stitch_dimension,
        "Aida 18 count: " + inchx + " by " + inchy + ", " + cmx + " by " + cmy,
        0,
        True,
        18,
        0,
        "Tahoma",
    )
    pdb.gimp_floating_sel_anchor(floating_text)

    # Turn layers on to see
    for l in range(0, len(new_image.layers) - 1):
        new_image.layers[l].visible = 1
    pdb.gimp_selection_none(new_image)

    pdb.gimp_context_pop()
    pdb.gimp_image_undo_group_end(image)
    pdb.gimp_displays_flush()
    # return


register(
    "python_fu_cross_stitch_tt",
    "Generates a cross stitch pattern",
    "Generates a cross stitch pattern",
    "Tin Tran",
    "Tin Tran",
    "March 2017",
    "<Image>/Python-Fu/Cross Stitch...",  # Menu path
    "RGB*, GRAY*",
    [
        (
            PF_OPTION,
            "blend",
            "Blend Type:",
            0,
            [
                "None - Only pure DMC color",
                "50% Blend - 2 strands blend",
                "Third Blend - 1 strand of 1st color and 2 strands of 2nd color",
                "Fourth Blend - 4 strands of 2 color-combination",
                "Fifth Blend - 5 strands of 2 color-combination",
                "Sixth Blend = 6 strands of 2 color-combination",
            ],
        ),
        (PF_SPINNER, "num_colors", "# of Colors:", 8, (2, 256, 1)),
        (
            PF_OPTION,
            "color_dithering",
            "Color _dithering:",
            0,
            [
                "None",
                "Floyd-Steinberg(Normal)",
                "Floyd-Steinberg(Reduce color bleeding)",
                "Positioned",
            ],
        ),  # initially 0th is choice
        (
            PF_OPTION,
            "interpolation",
            "Interpolation (Used for Scaling):",
            2,
            ["None", "Linear", "Cubic", "NoHalo", "LoHalo"],
        ),
        (
            PF_OPTION,
            "match_method",
            "Color Match method:",
            0,
            ["Perceptive", "Regular", "Delta-E"],
        ),  # initially 0th is choice
        (
            PF_SPINNER,
            "hor_stitches",
            "# of Stitches (Horizontally):",
            100,
            (1, 20000, 10),
        ),
        (
            PF_SPINNER,
            "stitches_per_square",
            "# of Stitches per Square(used to create dark grid):",
            10,
            (1, 20000, 1),
        ),
        (PF_COLOR, "square_grid_color", "Square grid color(Dark grid):", (0, 0, 0)),
        (
            PF_COLOR,
            "stitch_grid_color",
            "Stitch grid color(Light grid):",
            (128, 128, 128),
        ),
    ],
    [],
    python_cross_stitch_tt,
)

main()
