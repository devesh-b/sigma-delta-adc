# Fresh-process DRC + GDS + extraction of one cell: env(CELL). Run from the output dir.
load $env(CELL)
select top cell
expand
drc euclidean on
drc style drc(full)
drc check
drc catchup
foreach {why boxes} [drc listall why] { puts "DRCWHY $env(CELL) [llength $boxes] $why" }
puts "MAGICDRC $env(CELL) [drc listall count total]"
# WO-107: per-cell counts (listall why reports the top cell only; count total includes every subcell)
foreach {c n} [join [drc listall count]] { if {$n > 0} { puts "DRCCELL $env(CELL) $c $n" } }
gds write $env(CELL).gds
extract do local
extract all
ext2spice lvs
ext2spice -o $env(CELL).spice
puts "VERIFY DONE"
quit -noprompt
