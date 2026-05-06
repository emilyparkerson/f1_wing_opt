#this is just a test for my specific functions (do not upload to main branch)

from scoring import scoring_p1
from design_vars import AeroResult

#cl_cand = -2.0
#cd_cand = 0.15

cand_result = AeroResult(cl=-2.0, cd=0.15)

score = scoring_p1(cand_result)

print("Phase 1 score:", score)