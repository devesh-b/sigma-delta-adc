# WO-100 item 2d: the C9 macro from its real GDS (env C9GDS), placed mirrored at (4, 72) as in the floorplan.
# Checks that the WO-96 nwell.4 errors came from the LEF abstract (OBS nwell), not from the macro.
# WO-100: readonly, so the macro cells are copied verbatim on GDS write. Without it magic regenerated the hd cells
# (implants from its own CIF rules) and KLayout found 217 hvtp/psdm/nsdm/npc items that are not in the source GDS.
gds readonly true
gds read $env(C9GDS)
cellname create c9_place
load c9_place
box 4um 72um 4um 72um
getcell sd_adc_c9
sideways
select top cell
puts "FP C9GDS bbox [box values] (internal units)"
writeall force
puts "FP C9 PLACE DONE"
quit -noprompt
