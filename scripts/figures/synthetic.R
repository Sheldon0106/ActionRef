# Learning and evaluation are separate; every plotted value is a saved aggregate.

synthetic_learning <- function(d) {
  section(30,153,755,446,"Learn the practice references",C$teal_bg,C$fit,"a",
          "LEARNING DATA / 8,400 synthetic encounters")
  legend_curve(133,245)
  p <- chart(135,306,584,201,c(-2,102),c(0,1.02),seq(0,100,20),c(0,.5,1),
              "Score","Recorded-action probability",ylab_offset=66)
  curve_marks(p,d$synthetic_curve,point_r=3.7)
  for(i in 1:2) {
    xx <- c(45,60)[i]; cc <- c(C$low,C$high)[i]
    rate <- approx(d$synthetic_curve$score,d$synthetic_curve$isotonic_rate,xout=xx)$y
    line(rep(p$X(xx),2),c(p$Y(0),p$Y(rate)),cc,1,3)
    dot(p$X(xx),p$Y(rate),5,cc,"white",1)
  }
  pill(421,272,150,"Low + Mid: 45",C$low,h=28)
  pill(586,272,122,"High: 60",C$high,h=28)
}

synthetic_capacity <- function(d) {
  section(815,153,755,446,"Apply an alert budget",C$operating_bg,C$operating,"b",
          "SAME LEARNING DATA / capacity K = 1,680 alerts (20%)")
  p <- chart(925,306,584,201,c(-2,102),c(0,8600),seq(0,100,20),c(0,2000,4000,6000,8000),
              "Candidate cutoff","Alerts in learning data",ylabels=c("0","2,000","4,000","6,000","8,000"),
              ylab_offset=82)
  # The filled region denotes alert counts at or below K, not a confidence band.
  box(p$x,p$Y(1680),p$w,p$Y(0)-p$Y(1680),adjustcolor(C$operating,.09))
  v <- d$alert_curve[order(d$alert_curve$threshold),]
  line(p$X(v$threshold),p$Y(v$alert_count),C$observed,2)
  line(c(p$x,p$x+p$w),rep(p$Y(1680),2),C$operating,1.3,2)
  line(rep(p$X(81),2),c(p$Y(0),p$Y(1643)),C$operating,1,3)
  dot(p$X(81),p$Y(1643),6,C$operating,"white",1)
  tlabel(940,433,"K = 1,680",11,C$operating,"bold")
  tlabel(1240,323,"Operating cutoff 81",14,C$operating,"bold")
  tlabel(1240,347,"1,643 learning alerts",11,C$muted)
  line(c(1380,1391,p$X(81)),c(380,402,p$Y(1643)-11),C$operating,1.1,arrow=TRUE)
}

synthetic_evaluation <- function(d) {
  section(30,659,1540,344,"Evaluate the fixed choices on separate data",C$blue_bg,C$blue,"c",
          "HELD-OUT DATA / 3,600 synthetic encounters / no cutoff reselection")
  tab <- d$synthetic_heldout[match(c("Low","High","Low capacity"),d$synthetic_heldout$level),]
  colors <- c(C$low,C$high,C$operating)
  yy <- c(820,879,938)
  tlabel(65,763,"Cutoff and role",11,C$muted,"bold")
  tlabel(610,763,"Alerts per 1,000 encounters",12,face="bold",just=c("center","top"))
  tlabel(1060,763,"Outcome coverage (recall)",12,face="bold",just=c("center","top"))
  tlabel(1441,754,"Recorded-action\nyield among alerts",10.5,C$muted,"bold",just=c("center","top"))
  for(i in 1:3) {
    cc <- colors[i]
    pill(63,yy[i]-18,66,as.character(tab$evaluated_threshold[i]),cc,size=14,h=34)
    tlabel(147,yy[i],c("Low + Mid reference","High reference","Capacity candidate")[i],11,cc,
            "bold",just=c("left","center"))
    # Both comparisons have zero origins, stable row colors, and a common data split.
    box(395,yy[i]-10,385,20,"white",r=3)
    box(395,yy[i]-10,385*tab$alerts_per_1000[i]/600,20,cc,r=3)
    tlabel(800,yy[i],sprintf("%.1f",tab$alerts_per_1000[i]),12,cc,"bold",just=c("left","center"))
    line(c(965,1250),rep(yy[i],2),"#CFDDE4",2)
    dot(965+285*tab$recall[i],yy[i],7,cc,"white",1)
    tlabel(1280,yy[i],sprintf("%.1f%%",100*tab$recall[i]),12,cc,"bold",just=c("left","center"))
    tlabel(1441,yy[i],sprintf("%.1f%%",100*tab$response_yield[i]),12,C$muted,
            just=c("center","center"))
  }
  for(v in c(0,200,400,600)) tlabel(395+385*v/600,971,v,9.5,C$muted,just=c("center","top"))
  for(v in c(0,50,100)) tlabel(965+285*v/100,971,paste0(v,"%"),9.5,C$muted,just=c("center","top"))
}

synthetic_parts <- list(
  learning=list(draw=synthetic_learning,bounds=c(30,153,755,446)),
  capacity=list(draw=synthetic_capacity,bounds=c(815,153,755,446)),
  evaluation=list(draw=synthetic_evaluation,bounds=c(30,659,1540,344)))

draw_synthetic <- function(d) {
  header("An alert budget changes the operating cutoff",
          "Synthetic walkthrough / learning references, choosing a candidate, and seeing the tradeoff")
  for(part in synthetic_parts) part$draw(d)
  line(c(786,811),c(376,376),C$operating,1.6,arrow=TRUE)
  line(c(407,407),c(600,655),C$fit,1.6,arrow=TRUE)
  line(c(1192,1192),c(600,655),C$operating,1.6,arrow=TRUE)
  tlabel(800,621,"References stay unchanged; operating choices are evaluated alongside them.",10.5,C$muted,
          just=c("center","center"))
  tlabel(30,1028,"All observations are synthetic. A tighter alert budget reduces alerts and outcome coverage in this example.",10.5,C$muted)
}
