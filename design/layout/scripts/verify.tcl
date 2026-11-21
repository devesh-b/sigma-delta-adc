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
# WO-107: flat DRC, the geometry the TT precheck sees (flattened GDS). Gencell/std-cell subcells checked alone report
# errors that their parent geometry resolves (e.g. the gencell gate-contact met1 below met1.6 until the escape lands).
flatten $env(CELL)_flat
load $env(CELL)_flat
select top cell
drc check
drc catchup
foreach {why boxes} [drc listall why] { puts "DRCWHYFLAT $env(CELL) [llength $boxes] $why [lrange $boxes 0 1]" }
puts "MAGICDRCFLAT $env(CELL) [drc listall count total]"
load $env(CELL)
gds write $env(CELL).gds
extract do local
extract all
ext2spice lvs
ext2spice -o $env(CELL).spice
puts "VERIFY DONE"
quit -noprompt
