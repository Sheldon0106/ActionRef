# Clinical action evaluation: plot only the provided learning / held-out aggregates.

clinical_learning <- function(d) {
  section(30,152,780,632,"Learning curve and sample support",C$teal_bg,C$fit,"a",
          "MIMIC / 26 retained bins / 294,659 encounters represented")
  legend_curve(137,247)
  p <- chart(139,315,610,265,c(0,80),c(0,1.02),numeric(0),c(0,.25,.5,.75,1),
              ylabel="Recorded-action probability",ylab_offset=69)
  for(i in 1:3) {
    xx <- c(27,36,51)[i]; cc <- c(C$low,C$mid,C$high)[i]
    rate <- approx(d$clinical$score,d$clinical$isotonic_rate,xout=xx)$y
    line(rep(p$X(xx),2),c(p$Y(0),p$Y(rate)),cc,1,3)
  }
  curve_marks(p,d$clinical,point_r=4.1)
  # Probability target labels, below and separate from the curve legend.
  for(i in 1:3) {
    xx <- c(27,36,51)[i]; cc <- c(C$low,C$mid,C$high)[i]
    rate <- approx(d$clinical$score,d$clinical$isotonic_rate,xout=xx)$y
    dot(p$X(xx),p$Y(rate),5.6,cc,"white",1)
    pill(c(324,453,587)[i],278,116,c("Low 27","Mid 36","High 51")[i],cc,size=10.5,h=27)
  }
  q <- chart(139,618,610,74,c(0,80),c(0,52000),seq(0,80,20),c(0,25000,50000),
              "Clinical score","Bin count",ylabels=c("0","25,000","50,000"),
              labsize=9.5,ylab_offset=81,xlab_offset=36)
  for(i in seq_len(nrow(d$clinical)))
    box(q$X(d$clinical$score[i])-8,q$Y(d$clinical$count[i]),16,
        q$Y(0)-q$Y(d$clinical$count[i]),"#93B4B7",r=.5)
}

clinical_reliability <- function(d) {
  section(840,152,730,632,"Held-out action probability",C$blue_bg,C$blue,"b",
          "MIMIC / 126,332 encounters / learning curve held fixed")
  tlabel(947,246,"Probability bins of width 0.1; area reflects bin count",10.5,C$muted)
  p <- chart(972,307,440,360,c(0,1),c(0,1),c(0,.25,.5,.75,1),c(0,.25,.5,.75,1),
              "Mean predicted action probability","Observed action proportion",
              labsize=10,ylab_offset=68,xlab_offset=39)
  # Keep boundary markers within the plot: all nonempty bins are interior.
  reliability_marks(p,d$reliability,max_radius=17)
  line(c(1040,1085),c(336,336),"#AABBC6",1.1,2)
  tlabel(1096,329,"Agreement line",10,C$muted)
  # Sample-size legend uses exactly the same area mapping as the data.
  tlabel(1455,387,"Bin N",10,C$muted,"bold",just=c("center","top"))
  for(i in 1:3) {
    nn <- c(5000,20000,40000)[i]; yy <- c(433,502,580)[i]
    dot(1455,yy,17*sqrt(nn/max(d$reliability$N)),adjustcolor(C$fit,.83),"white",.8)
    tlabel(1455,yy+24,format(nn,big.mark=","),9.5,C$muted,just=c("center","top"))
  }
  tlabel(947,749,"Descriptive bins; no confidence intervals shown",10,C$muted)
}

clinical_metrics <- function(d) {
  section(30,815,1540,165,"Read the probabilities in context",C$cyan_bg,C$fit)
  tlabel(54,875,"REFERENCE TARGETS",9.5,C$muted,"bold")
  tlabel(54,904,"Low: local action frequency\nMid: 0.50   /   High: 0.80",11)
  line(c(415,415),c(874,957),C$faint,1)
  tlabel(443,875,"OVERALL HELD-OUT ACTION RATE",9.5,C$muted,"bold")
  tlabel(443,904,sprintf("Observed %.2f%%",d$metrics$action_rate*100),13,C$fit,"bold")
  tlabel(443,933,sprintf("Mean prediction %.2f%%",d$metrics$mean_predicted*100),11)
  line(c(850,850),c(874,957),C$faint,1)
  tlabel(878,875,"BRIER SCORE / LOWER IS BETTER",9.5,C$muted,"bold")
  tlabel(878,904,sprintf("Fixed curve  %.4f",d$metrics$action_Brier),13,C$fit,"bold")
  tlabel(878,933,sprintf("Constant learning rate  %.4f",d$metrics$constant_development_rate_Brier),11)
  line(c(1260,1260),c(874,957),C$faint,1)
  tlabel(1288,875,"MEANING",9.5,C$muted,"bold")
  tlabel(1288,904,"Recorded assessment\nand treatment activity",11)
}

clinical_parts <- list(
  learning=list(draw=clinical_learning,bounds=c(30,152,780,632)),
  reliability=list(draw=clinical_reliability,bounds=c(840,152,730,632)),
  context=list(draw=clinical_metrics,bounds=c(30,815,1540,165)))

draw_clinical <- function(d) {
  header("Examine the action curve, then evaluate it separately",
          "Clinical illustration / empirical support and held-out evaluation of recorded action probability")
  for(part in clinical_parts) part$draw(d)
  line(c(811,835),c(455,455),C$blue,1.6,arrow=TRUE)
  tlabel(30,1003,"Source windows vary across actions. Predictions use continuous interpolation with endpoint clipping; empty reliability bins are omitted.",10,C$muted)
  tlabel(30,1028,"Action probability describes recorded practice. It is distinct from outcome risk and from the proportion with action among all alerts.",10,C$muted)
}
