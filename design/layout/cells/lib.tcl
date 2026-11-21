# Shared Magic Tcl helpers for the WO-96 cell generators (coordinates in um).
proc rect {layer x1 y1 x2 y2} {
    box ${x1}um ${y1}um ${x2}um ${y2}um
    paint $layer
}
# via between lo/hi metals at (x,y): metal pads first, then the contact (contact paint wins over metal)
proc via {lo hi cut x y} {
    set p 0.35; set c 0.2
    rect $lo [expr {$x-$p}] [expr {$y-$p}] [expr {$x+$p}] [expr {$y+$p}]
    rect $hi [expr {$x-$p}] [expr {$y-$p}] [expr {$x+$p}] [expr {$y+$p}]
    rect $cut [expr {$x-$c}] [expr {$y-$c}] [expr {$x+$c}] [expr {$y+$c}]
}
proc pin {name layer x1 y1 x2 y2} {
    box ${x1}um ${y1}um ${x2}um ${y2}um
    label $name FreeSans 0.3u -$layer
    port make
}
