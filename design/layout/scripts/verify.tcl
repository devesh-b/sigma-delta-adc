# Fresh-process DRC + GDS + extraction of one cell: env(CELL). Run from the output dir.
load $env(CELL)
select top cell
expand
drc euclidean on
drc style drc(full)
drc check
drc catchup
puts "MAGICDRC $env(CELL) [drc listall count total]"
gds write $env(CELL).gds
extract all
ext2spice lvs
ext2spice -o $env(CELL).spice
puts "VERIFY DONE"
quit -noprompt
