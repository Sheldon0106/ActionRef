# One claim: COPD returns a valid Low/Mid pair and an unavailable High.
# All coordinates come from corrected aggregates. Export: editable SVG/PDF,
# 8.5 x 5.5 inches, 300-dpi PNG, and a 12/10/9-pt type hierarchy.
draw_copd <- function(d) {
  curve <- d$copd_curve
  a <- d$copd_anchors
  lo <- subset(a,level=="Low")
  mi <- subset(a,level=="Mid")
  hi <- subset(a,level=="High")
  stopifnot(nrow(curve)==28,
            abs(lo$selected_threshold-17.779760509763356)<1e-10,
            abs(mi$selected_threshold-55.07187581853598)<1e-10,
            is.na(hi$selected_threshold),
            hi$attainability_status=="unavailable_ordering",
            hi$semantic_threshold_raw==50, mi$semantic_threshold_raw==55)
  tlabel(58,26,"COPD: retain Low and Mid; leave High unavailable",12)
  x <- function(s) 94+s/100*676
  y <- function(p) 430-p/.60*310
  for(pp in seq(0,.6,.1)) {
    line(c(80,770),rep(y(pp),2),C$faint,.7)
    tlabel(67,y(pp),sprintf("%.1f",pp),9,C$muted,just=c("right","center"))
  }
  line(c(80,80,770),c(120,430,430),C$muted,.9)
  for(ss in seq(0,100,20)) {
    line(rep(x(ss),2),c(430,435),C$muted,.9)
    tlabel(x(ss),444,as.character(ss),9,C$muted,just=c("center","top"))
  }
  tlabel(425,471,"Supplied COPD score",12,just=c("center","top"))
  tlabel(22,275,"Recorded-action probability",12,rot=90,just=c("center","center"))
  line(x(curve$score),y(curve$isotonic_rate),C$ink,1.8)
  for(i in seq_len(nrow(curve)))
    dot(x(curve$score[i]),y(curve$observed_rate[i]),
        2+6*sqrt(curve$count[i]/max(curve$count)),
        adjustcolor(C$observed,.65),"white",.7)
  line(c(80,108),c(77,77),C$ink,1.8)
  tlabel(117,77,"Isotonic fit",10,just=c("left","center"))
  dot(284,77,4,C$observed,"white",.7)
  tlabel(296,77,"Observed bin rate (area follows N)",10,just=c("left","center"))
  low_p <- approx(curve$score,curve$isotonic_rate,xout=lo$selected_threshold,rule=2)$y
  mid_p <- approx(curve$score,curve$isotonic_rate,xout=mi$selected_threshold,rule=2)$y
  for(z in list(list(t=lo$selected_threshold,p=low_p,col=C$low),
                list(t=mi$selected_threshold,p=mid_p,col=C$mid))) {
    line(rep(x(z$t),2),c(y(z$p),430),z$col,1.2,2)
    dot(x(z$t),y(z$p),4,"white",z$col,1.2)
  }
  tlabel(x(lo$selected_threshold)+13,405,"Low 17.78",10,C$low)
  tlabel(x(mi$selected_threshold)+13,128,"Mid 55.07",10,C$mid)
  line(c(x(mi$selected_threshold)+9,x(mi$selected_threshold)),c(148,y(mid_p)),C$mid,.8)
  high_p <- curve$isotonic_rate[match(hi$semantic_threshold_raw,curve$score)]
  stopifnot(is.finite(high_p),high_p>=hi$target_probability,
            hi$semantic_threshold_raw<mi$semantic_threshold_raw)
  line(c(80,770),rep(y(hi$target_probability),2),C$high,.8,3)
  xx <- x(hi$semantic_threshold_raw); yy <- y(high_p)
  line(xx+c(-5,5),yy+c(-5,5),C$high,1.6)
  line(xx+c(-5,5),yy+c(5,-5),C$high,1.6)
  tlabel(104,131,"Relative High rejected",10,C$high)
  tlabel(104,150,"Target 0.4278; bin 50 < Mid bin 55",10,C$high)
  line(c(321,xx-7),c(163,yy-3),C$high,.8)
  tlabel(80,509,sprintf("28 supported learning bins / %s encounters",
         format(sum(curve$count),big.mark=",",scientific=FALSE)),9,C$muted)
  tlabel(80,528,"Documented bronchodilator administration/start OR legacy Pyxis steroid-record proxy",9,C$muted)
}
copd_parts <- list(curve=list(draw=draw_copd,bounds=c(0,0,850,550)))
