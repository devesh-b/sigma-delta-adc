# klayout -b -r bbox.py -rd gds=<file> : print the top-cell bounding box (um) and area
import pya
ly = pya.Layout(); ly.read(gds)
for c in ly.top_cells():
    b = c.dbbox(); print(f"BBOX {c.name} {b.width():.2f} x {b.height():.2f} um = {b.width()*b.height():.0f} um2")
