foreach f [list $::env(ODB1) $::env(ODB2)] {
  read_db $f
  set b [ord::get_db_block]
  puts "== $f"
  foreach n [$b getNets] {
    set drv 0; set ld 0
    foreach it [$n getITerms] { if {[$it isOutputSignal]} {incr drv} else {incr ld} }
    foreach bt [$n getBTerms] { if {[$bt getIoType] eq "INPUT"} {incr drv} else {incr ld} }
    if {$drv == 0 || $ld == 0} { puts "FLOAT? [$n getName] sig=[$n getSigType] special=[$n isSpecial] drv=$drv ld=$ld nIT=[llength [$n getITerms]] nBT=[llength [$n getBTerms]]" }
  }
  ord::close_db
}
