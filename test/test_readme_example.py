from segmenter._HS_lite.homogeneous_segmentation import homogenous_segmentation
import pandas as pd
from io import StringIO

data = """road,slk_from,slk_to,cwy,deflection,dirn
H001,0.00,0.01,L,179.37,L
H001,0.01,0.02,L,177.12,L
H001,0.02,0.03,L,179.06,L
H001,0.03,0.04,L,212.65,L
H001,0.04,0.05,L,175.35,L
H001,0.05,0.06,L,188.66,L
H001,0.06,0.07,L,188.31,L
H001,0.07,0.08,L,174.48,L
H001,0.08,0.09,L,210.28,L
H001,0.09,0.10,L,260.05,L
H001,0.10,0.11,L,228.83,L
H001,0.11,0.12,L,226.33,L
H001,0.12,0.13,L,245.53,L
H001,0.13,0.14,L,315.77,L
H001,0.14,0.15,L,373.86,L
H001,0.15,0.16,L,333.56,L"""


expected_output = """road,slk_from,slk_to,cwy,deflection,dirn,length,seg.id,seg.point
H001,0.00,0.01,L,179.37,L,0.01,1,1
H001,0.01,0.02,L,177.12,L,0.01,1,0
H001,0.02,0.03,L,179.06,L,0.01,1,0
H001,0.03,0.04,L,212.65,L,0.01,1,0
H001,0.04,0.05,L,175.35,L,0.01,2,1
H001,0.05,0.06,L,188.66,L,0.01,2,0
H001,0.06,0.07,L,188.31,L,0.01,2,0
H001,0.07,0.08,L,174.48,L,0.01,2,0
H001,0.08,0.09,L,210.28,L,0.01,2,0
H001,0.09,0.10,L,260.05,L,0.01,3,1
H001,0.10,0.11,L,228.83,L,0.01,3,0
H001,0.11,0.12,L,226.33,L,0.01,3,0
H001,0.12,0.13,L,245.53,L,0.01,3,0
H001,0.13,0.14,L,315.77,L,0.01,3,0
H001,0.14,0.15,L,373.86,L,0.01,3,0
H001,0.15,0.16,L,333.56,L,0.01,3,0
"""

def test_readme_example():
	df = pd.read_csv(StringIO(data))

	df = homogenous_segmentation(
		data                        =df,
		measure                     =("slk_from","slk_to"),
		variables                   =["deflection"],
		allowed_segment_length_range=(0.030, 0.080)
	)

	df_expected = pd.read_csv(StringIO(expected_output))

	assert df.compare(df_expected).empty

	assert (df.groupby("seg.id")["length"].sum() >= 0.030).all()
	assert (df.groupby("seg.id")["length"].sum() <= 0.080).all()

