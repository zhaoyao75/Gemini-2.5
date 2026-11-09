#!/bin/bash
# usage: render_all.sh  (run from lineart/ after lotus_prep.py)  -> ../final/paintings/lotus_<name>.png
O=../final/paintings
r() { node render.js $O/lotus_$1.png "$2"; }
r monet "paint_monet_lotus.html" &
r klimt "paint_flat.html?style=klimt" & r matisse "paint_flat.html?style=matisse" &
r hockney "paint_s3.html?style=hockney" & r kusama_pumpkin "paint_s2.html?style=kusama_pumpkin" &
wait
r vangogh "paint.html" & r lichtenstein "paint_s3.html?style=lichtenstein" & r warhol "paint_s2.html?style=warhol" &
r seurat "paint_s2.html?style=seurat" & r gauguin "paint_s3.html?style=gauguin" &
wait
r picasso "paint_modern.html?style=picasso" & r mondrian "paint_modern.html?style=mondrian" & r kandinsky "paint_more.html?style=kandinsky" &
r pollock "paint_more.html?style=pollock" & r dali "paint_more.html?style=dali" &
wait
# per-style bowl colours (each style's own bowl palette instead of the shared blue)
for n in monet klimt matisse hockney vangogh lichtenstein seurat gauguin picasso dali; do python3 -I ../code/recolor_bowl.py . $O/lotus_$n.png $n; done
