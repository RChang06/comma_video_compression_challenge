# joint_hops

Decoder for the `joint_hops` archive. Run `inflate.sh <archive_dir> <output_dir> <video_names_file>` (needs a CUDA GPU).

Builds on PR #141 (semantic_blocks), PR #140 (semantic_joint_ctxmix) and PR #135 (semantic-pose-HPAC_CPR1_polished).
This folder is #141's decoder. Changes: the archive checksum/size in `inflate.py`, the carrier gray/amp constants in
`cpr1/inflate.py`, and the same gray constant in `runtime/ddm_wc1_advisory_runtime.py` (parallel render path).
