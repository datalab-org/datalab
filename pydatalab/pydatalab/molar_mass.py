#!/usr/bin/env python3
# Joshua Bocarsly

import re
import sys

import pandas as pd

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

raw_data = """Atomic Number,Atomic Mass,Name,Symbol,M.P. (C) ,B.P. (C) ,Density (g/cm3),Earth Crust %,Discovery Year,Group,Electron Configuration,Ionization Energy (eV)
1,1.0079,Hydrogen,H,-259,-253,0.09,0.14,1776,1,1s1,13.5984
2,4.0026,Helium,He,-272,-269,0.18,,1895,18,1s2,24.5874
3,6.941,Lithium,Li,180,1347,0.53,,1817,1,[He] 2s1,5.3917
4,9.0122,Beryllium,Be,1278,2970,1.85,,1797,2,[He] 2s2,9.3227
5,10.811,Boron,B,2300,2550,2.34,,1808,13,[He] 2s2 2p1,8.298
6,12.0107,Carbon,C,3500,4827,2.26,0.094,ancient,14,[He] 2s2 2p2,11.2603
7,14.0067,Nitrogen,N,-210,-196,1.25,,1772,15,[He] 2s2 2p3,14.5341
8,15.9994,Oxygen,O,-218,-183,1.43,46.71,1774,16,[He] 2s2 2p4,13.6181
9,18.9984,Fluorine,F,-220,-188,1.7,0.029,1886,17,[He] 2s2 2p5,17.4228
10,20.1797,Neon,Ne,-249,-246,0.9,,1898,18,[He] 2s2 2p6,21.5645
11,22.9897,Sodium,Na,98,883,0.97,2.75,1807,1,[Ne] 3s1,5.1391
12,24.305,Magnesium,Mg,639,1090,1.74,2.08,1755,2,[Ne] 3s2,7.6462
13,26.9815,Aluminum,Al,660,2467,2.7,8.07,1825,13,[Ne] 3s2 3p1,5.9858
14,28.0855,Silicon,Si,1410,2355,2.33,27.69,1824,14,[Ne] 3s2 3p2,8.1517
15,30.9738,Phosphorus,P,44,280,1.82,0.13,1669,15,[Ne] 3s2 3p3,10.4867
16,32.065,Sulfur,S,113,445,2.07,0.052,ancient,16,[Ne] 3s2 3p4,10.36
17,35.453,Chlorine,Cl,-101,-35,3.21,0.045,1774,17,[Ne] 3s2 3p5,12.9676
18,39.948,Argon,Ar,-189,-186,1.78,,1894,18,[Ne] 3s2 3p6,15.7596
19,39.0983,Potassium,K,64,774,0.86,2.58,1807,1,[Ar] 4s1,4.3407
20,40.078,Calcium,Ca,839,1484,1.55,3.65,1808,2,[Ar] 4s2,6.1132
21,44.9559,Scandium,Sc,1539,2832,2.99,,1879,3,[Ar] 3d1 4s2,6.5615
22,47.867,Titanium,Ti,1660,3287,4.54,0.62,1791,4,[Ar] 3d2 4s2,6.8281
23,50.9415,Vanadium,V,1890,3380,6.11,,1830,5,[Ar] 3d3 4s2,6.7462
24,51.9961,Chromium,Cr,1857,2672,7.19,0.035,1797,6,[Ar] 3d5 4s1,6.7665
25,54.938,Manganese,Mn,1245,1962,7.43,0.09,1774,7,[Ar] 3d5 4s2,7.434
26,55.845,Iron,Fe,1535,2750,7.87,5.05,ancient,8,[Ar] 3d6 4s2,7.9024
27,58.9332,Cobalt,Co,1495,2870,8.9,,1735,9,[Ar] 3d7 4s2,7.881
28,58.6934,Nickel,Ni,1453,2732,8.9,0.019,1751,10,[Ar] 3d8 4s2,7.6398
29,63.546,Copper,Cu,1083,2567,8.96,,ancient,11,[Ar] 3d10 4s1,7.7264
30,65.39,Zinc,Zn,420,907,7.13,,ancient,12,[Ar] 3d10 4s2,9.3942
31,69.723,Gallium,Ga,30,2403,5.91,,1875,13,[Ar] 3d10 4s2 4p1,5.9993
32,72.64,Germanium,Ge,937,2830,5.32,,1886,14,[Ar] 3d10 4s2 4p2,7.8994
33,74.9216,Arsenic,As,81,613,5.72,,ancient,15,[Ar] 3d10 4s2 4p3,9.7886
34,78.96,Selenium,Se,217,685,4.79,,1817,16,[Ar] 3d10 4s2 4p4,9.7524
35,79.904,Bromine,Br,-7,59,3.12,,1826,17,[Ar] 3d10 4s2 4p5,11.8138
36,83.8,Krypton,Kr,-157,-153,3.75,,1898,18,[Ar] 3d10 4s2 4p6,13.9996
37,85.4678,Rubidium,Rb,39,688,1.63,,1861,1,[Kr] 5s1,4.1771
38,87.62,Strontium,Sr,769,1384,2.54,,1790,2,[Kr] 5s2,5.6949
39,88.9059,Yttrium,Y,1523,3337,4.47,,1794,3,[Kr] 4d1 5s2,6.2173
40,91.224,Zirconium,Zr,1852,4377,6.51,0.025,1789,4,[Kr] 4d2 5s2,6.6339
41,92.9064,Niobium,Nb,2468,4927,8.57,,1801,5,[Kr] 4d4 5s1,6.7589
42,95.94,Molybdenum,Mo,2617,4612,10.22,,1781,6,[Kr] 4d5 5s1,7.0924
43,98,Technetium,Tc,2200,4877,11.5,,1937,7,[Kr] 4d5 5s2,7.28
44,101.07,Ruthenium,Ru,2250,3900,12.37,,1844,8,[Kr] 4d7 5s1,7.3605
45,102.9055,Rhodium,Rh,1966,3727,12.41,,1803,9,[Kr] 4d8 5s1,7.4589
46,106.42,Palladium,Pd,1552,2927,12.02,,1803,10,[Kr] 4d10,8.3369
47,107.8682,Silver,Ag,962,2212,10.5,,ancient,11,[Kr] 4d10 5s1,7.5762
48,112.411,Cadmium,Cd,321,765,8.65,,1817,12,[Kr] 4d10 5s2,8.9938
49,114.818,Indium,In,157,2000,7.31,,1863,13,[Kr] 4d10 5s2 5p1,5.7864
50,118.71,Tin,Sn,232,2270,7.31,,ancient,14,[Kr] 4d10 5s2 5p2,7.3439
51,121.76,Antimony,Sb,630,1750,6.68,,ancient,15,[Kr] 4d10 5s2 5p3,8.6084
52,127.6,Tellurium,Te,449,990,6.24,,1783,16,[Kr] 4d10 5s2 5p4,9.0096
53,126.9045,Iodine,I,114,184,4.93,,1811,17,[Kr] 4d10 5s2 5p5,10.4513
54,131.293,Xenon,Xe,-112,-108,5.9,,1898,18,[Kr] 4d10 5s2 5p6,12.1298
55,132.9055,Cesium,Cs,29,678,1.87,,1860,1,[Xe] 6s1,3.8939
56,137.327,Barium,Ba,725,1140,3.59,0.05,1808,2,[Xe] 6s2,5.2117
57,138.9055,Lanthanum,La,920,3469,6.15,,1839,3,[Xe] 5d1 6s2,5.5769
58,140.116,Cerium,Ce,795,3257,6.77,,1803,101,[Xe] 4f1 5d1 6s2,5.5387
59,140.9077,Praseodymium,Pr,935,3127,6.77,,1885,101,[Xe] 4f3 6s2,5.473
60,144.24,Neodymium,Nd,1010,3127,7.01,,1885,101,[Xe] 4f4 6s2,5.525
61,145,Promethium,Pm,1100,3000,7.3,,1945,101,[Xe] 4f5 6s2,5.582
62,150.36,Samarium,Sm,1072,1900,7.52,,1879,101,[Xe] 4f6 6s2,5.6437
63,151.964,Europium,Eu,822,1597,5.24,,1901,101,[Xe] 4f7 6s2,5.6704
64,157.25,Gadolinium,Gd,1311,3233,7.9,,1880,101,[Xe] 4f7 5d1 6s2,6.1501
65,158.9253,Terbium,Tb,1360,3041,8.23,,1843,101,[Xe] 4f9 6s2,5.8638
66,162.5,Dysprosium,Dy,1412,2562,8.55,,1886,101,[Xe] 4f10 6s2,5.9389
67,164.9303,Holmium,Ho,1470,2720,8.8,,1867,101,[Xe] 4f11 6s2,6.0215
68,167.259,Erbium,Er,1522,2510,9.07,,1842,101,[Xe] 4f12 6s2,6.1077
69,168.9342,Thulium,Tm,1545,1727,9.32,,1879,101,[Xe] 4f13 6s2,6.1843
70,173.04,Ytterbium,Yb,824,1466,6.9,,1878,101,[Xe] 4f14 6s2,6.2542
71,174.967,Lutetium,Lu,1656,3315,9.84,,1907,101,[Xe] 4f14 5d1 6s2,5.4259
72,178.49,Hafnium,Hf,2150,5400,13.31,,1923,4,[Xe] 4f14 5d2 6s2,6.8251
73,180.9479,Tantalum,Ta,2996,5425,16.65,,1802,5,[Xe] 4f14 5d3 6s2,7.5496
74,183.84,Tungsten,W,3410,5660,19.35,,1783,6,[Xe] 4f14 5d4 6s2,7.864
75,186.207,Rhenium,Re,3180,5627,21.04,,1925,7,[Xe] 4f14 5d5 6s2,7.8335
76,190.23,Osmium,Os,3045,5027,22.6,,1803,8,[Xe] 4f14 5d6 6s2,8.4382
77,192.217,Iridium,Ir,2410,4527,22.4,,1803,9,[Xe] 4f14 5d7 6s2,8.967
78,195.078,Platinum,Pt,1772,3827,21.45,,1735,10,[Xe] 4f14 5d9 6s1,8.9587
79,196.9665,Gold,Au,1064,2807,19.32,,ancient,11,[Xe] 4f14 5d10 6s1,9.2255
80,200.59,Mercury,Hg,-39,357,13.55,,ancient,12,[Xe] 4f14 5d10 6s2,10.4375
81,204.3833,Thallium,Tl,303,1457,11.85,,1861,13,[Xe] 4f14 5d10 6s2 6p1,6.1082
82,207.2,Lead,Pb,327,1740,11.35,,ancient,14,[Xe] 4f14 5d10 6s2 6p2,7.4167
83,208.9804,Bismuth,Bi,271,1560,9.75,,ancient,15,[Xe] 4f14 5d10 6s2 6p3,7.2856
84,209,Polonium,Po,254,962,9.3,,1898,16,[Xe] 4f14 5d10 6s2 6p4,8.417
85,210,Astatine,At,302,337,,,1940,17,[Xe] 4f14 5d10 6s2 6p5,9.3
86,222,Radon,Rn,-71,-62,9.73,,1900,18,[Xe] 4f14 5d10 6s2 6p6,10.7485
87,223,Francium,Fr,27,677,,,1939,1,[Rn] 7s1,4.0727
88,226,Radium,Ra,700,1737,5.5,,1898,2,[Rn] 7s2,5.2784
89,227,Actinium,Ac,1050,3200,10.07,,1899,3,[Rn] 6d1 7s2,5.17
90,232.0381,Thorium,Th,1750,4790,11.72,,1829,102,[Rn] 6d2 7s2,6.3067
91,231.0359,Protactinium,Pa,1568,,15.4,,1913,102,[Rn] 5f2 6d1 7s2,5.89
92,238.0289,Uranium,U,1132,3818,18.95,,1789,102,[Rn] 5f3 6d1 7s2,6.1941
93,237,Neptunium,Np,640,3902,20.2,,1940,102,[Rn] 5f4 6d1 7s2,6.2657
94,244,Plutonium,Pu,640,3235,19.84,,1940,102,[Rn] 5f6 7s2,6.0262
95,243,Americium,Am,994,2607,13.67,,1944,102,[Rn] 5f7 7s2,5.9738
96,247,Curium,Cm,1340,,13.5,,1944,102,,5.9915
97,247,Berkelium,Bk,986,,14.78,,1949,102,,6.1979
98,251,Californium,Cf,900,,15.1,,1950,102,,6.2817
99,252,Einsteinium,Es,860,,,,1952,102,,6.42
100,257,Fermium,Fm,1527,,,,1952,102,,6.5
101,258,Mendelevium,Md,,,,,1955,102,,6.58
102,259,Nobelium,No,827,,,,1958,102,,6.65
103,262,Lawrencium,Lr,1627,,,,1961,102,,4.9
104,261,Rutherfordium,Rf,,,,,1964,4,,
105,262,Dubnium,Db,,,,,1967,5,,
106,266,Seaborgium,Sg,,,,,1974,6,,
107,264,Bohrium,Bh,,,,,1981,7,,
108,277,Hassium,Hs,,,,,1984,8,,
109,268,Meitnerium,Mt,,,,,1982,9,,"""

# NOTE: The data is read in here and can be accessed as data and all_data if this is run
# in an ipython console: e.g 'run molar_mass.py' (even if it gives an error...)
all_data = pd.read_csv(StringIO(raw_data), index_col="Symbol")  # df of all atom data
data = all_data["Atomic Mass"]  # series of just the mass indexed by the symbol
regex = r"([A-Z][a-z]?)((?:\d+\.?\d*)?)"  # regex to split into symbols and stoichiometries


def stoich_cleaner(string):
    """Takes a string like '', '2' or '0.11' and turns it into the proper number"""
    if string == "":
        return 1.0
    else:
        return float(string)


def calc_molar_mass(string):
    "takes a chemical formula as a string, e.g. 'In0.11WO3', and returns the molar mass as float"

    matches = re.findall(regex, string)
    matches = [(sym, stoich_cleaner(stoich)) for (sym, stoich) in matches]
    # print(matches)
    masses = (data[sym] * stoich for sym, stoich in matches)
    return sum(masses)  # summing a generator expression whoah how efficient


def molar_mass_from_list(formula_in_list_form):
    """formula should be in the form, e.g. "[('In',0.33),('W',1),('O',3)]"""
    masses = (data[sym] * stoich for sym, stoich in formula_in_list_form)
    return sum(masses)


def main():
    if len(sys.argv) != 2:
        print("Example usage: python molar_mass.py In0.33WO3")
        sys.exit(1)

    formula = sys.argv[1]

    print(calc_molar_mass(formula))


if __name__ == "__main__":
    main()
