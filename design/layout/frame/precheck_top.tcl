# WO-109 item 3: TT precheck project GDS/LEF for the frame (D98): tt_um_sd_adc_fp (floorplan.tcl output, in the cwd)
# with the C9 macro GDS (env C9GDS) placed as in c9_place.tcl (mirrored at 4, 72). Analog blocks are not placed (OTA1
# does not fit its slot yet; C2/C3/C4/C6 on hold, D100). env PROJ = project dir (gds/, lef/ written here);
# env BROKEN = met5 adds one met5 rect (precheck must fail on the forbidden layer).
gds readonly true
gds read $env(C9GDS)
load tt_um_sd_adc_fp
box 4um 72um 4um 72um
getcell sd_adc_c9
sideways
select top cell
if {[info exists env(BROKEN)] && $env(BROKEN) eq "met5"} {
    box 250um 150um 260um 160um
    paint metal5
}
gds write $env(PROJ)/gds/tt_um_sd_adc_fp.gds
lef write $env(PROJ)/lef/tt_um_sd_adc_fp.lef -hide -pinonly
puts "PRECHECK_TOP written $env(PROJ)"
quit -noprompt
