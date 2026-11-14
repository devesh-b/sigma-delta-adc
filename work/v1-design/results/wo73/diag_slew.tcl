# WO-73 item 1: estimated vs routed slew on the worst ss_1v40 nets of the WO-72 final ODB (same netlist in all modes).
# Fixes WO-72 diag.tcl: report_net takes a net NAME (STA-0232 with get_nets -of_objects).
# Run in IIC-OSIC-TOOLS: env ODB SDC MODE=placement|grt|spef [SPEF] openroad -exit diag_slew.tcl
#  placement: estimate_parasitics -placement (post-GPL repair view); grt: global_route + -global_routing (post-GRT repair view);
#  spef: read_spef of signoff RCX (STAPostPNR view). Wire RC for estimates: LibreLane sky130 per-layer values via set_layer_rc
#  is not reproduced here; set_wire_rc met2 signal / met3 clock is used as in WO-72 diag (approximation, stated in README).
set L /foss/pdks-tt/sky130A/libs.ref/sky130_fd_sc_hd/lib
read_db $::env(ODB)
read_liberty $L/sky130_fd_sc_hd__ss_100C_1v40.lib
read_sdc $::env(SDC)
set mode $::env(MODE)
if {$mode eq "spef"} {
  read_spef $::env(SPEF)
} else {
  set_wire_rc -signal -layer met2
  set_wire_rc -clock  -layer met3
  if {$mode eq "grt"} {
    set_routing_layers -signal met1-met4 -clock met1-met4
    global_route -allow_congestion
    estimate_parasitics -global_routing
  } else {
    estimate_parasitics -placement
  }
}
puts "=== MODE $mode"
foreach dp {fanout116/X fanout68/X fanout57/X _1110_/Y} {
  set n [get_full_name [get_nets -of_objects [get_pins $dp]]]
  puts "--- driver $dp net $n"
  if {[catch {report_net -digits 3 $n} e]} { puts "report_net err: $e" }
  set worst 0.0; set wp ""
  foreach p [get_pins -quiet -of_objects [get_nets $n]] {
    if {[catch {set s [get_property $p slew_max]} e]} { puts "prop err: $e"; break }
    if {$s > $worst} { set worst $s; set wp [get_full_name $p] }
  }
  puts [format "WORST_SLEW mode=%s net=%s(drv) slew=%.4f pin=%s" $mode $n $worst $wp]
}
report_check_types -max_slew -violators -digits 3
