# Workflow: original vector illustrations surrounding empirical action evidence.

workflow_inputs <- function(d) {
  section(30,145,340,285,"Local clinical records",C$blue_bg,C$blue)
  rows <- list(c("score","Existing clinical score","Use its intended assessment time"),
               c("action","Recorded activity","Specify action + observation window"),
               c("outcome","Outcome, when available","For score and outcome evaluation"))
  for(i in seq_along(rows)) {
    yy <- 214+(i-1)*68
    icon(rows[[i]][1],49,yy,.75,C$blue,C$blue_bg)
    tlabel(106,yy+4,rows[[i]][2],12,face="bold")
    tlabel(106,yy+29,rows[[i]][3],9.5,C$muted)
  }
}

workflow_checks <- function(d) {
  section(30,460,340,270,"Check inputs",C$input_bg,C$input,"1","MODULE 1 / study design")
  labels <- c("Score direction and completeness","Action definition and timing","Score validity for the intended use")
  for(i in seq_along(labels)) {
    yy <- 558+(i-1)*34
    checkmark(52,yy+3,C$input,.8)
    tlabel(77,yy,labels[i],10.5)
  }
  line(c(52,347),c(659,659),adjustcolor(C$input,.25),.8)
  pill(51,676,125,"Learning data",C$fit,h=30)
  line(c(190,214),c(690,690),C$muted,1.2)
  pill(230,676,118,"Separate test",C$blue,h=30)
}

workflow_references <- function(d) {
  section(400,145,670,585,"Learn behavioral references",C$teal_bg,C$fit,"2",
          "MODULE 2 / relate an existing score to recorded action")
  steps <- c("Supported score bins","Monotone action fit","Probability targets")
  for(i in seq_along(steps)) {
    xx <- 423+(i-1)*211
    box(xx,239,198,37,"white",adjustcolor(C$fit,.25),r=4)
    tlabel(xx+99,257,steps[i],10.5,C$fit,"bold",just=c("center","center"))
    if(i<3) line(c(xx+201,xx+208),c(257,257),C$fit,1.1,arrow=TRUE)
  }
  tlabel(439,298,"MIMIC ILLUSTRATION",9.5,C$muted,"bold")
  p <- chart(475,347,338,208,c(0,80),c(0,1.02),c(0,20,40,60,80),c(0,.5,1),
              ylabel="Action probability",ylab_offset=60)
  # Interpolated line connects the saved isotonic bin coordinates, as in evaluation.
  curve_marks(p,d$clinical,point_r=3.4,lwd=2)
  for(i in 1:3) {
    xx <- c(27,36,51)[i]; cc <- c(C$low,C$mid,C$high)[i]
    fit <- approx(d$clinical$score,d$clinical$isotonic_rate,xout=xx)$y
    line(rep(p$X(xx),2),c(p$Y(0),p$Y(fit)),cc,.9,3)
    dot(p$X(xx),p$Y(fit),5,cc,"white",1)
  }
  tlabel(646,599,"Clinical score",10.5,just=c("center","top"))
  legend_curve(475,627)
  vals <- c("Low 27","Mid 36","High 51")
  details <- c("Local action rate","P(action) = 0.50","P(action) = 0.80")
  targets <- c("Target: about 0.327", "Absolute target", "Absolute target")
  for(i in 1:3) {
    yy <- 316+(i-1)*105; cc <- c(C$low,C$mid,C$high)[i]
    box(848,yy,196,89,"white",adjustcolor(cc,.32),r=6)
    box(849,yy+13,4,61,cc)
    tlabel(866,yy+13,vals[i],17,cc,"bold")
    tlabel(866,yy+44,details[i],10.5)
    tlabel(866,yy+66,targets[i],9.5,C$muted)
  }
  line(c(423,1046),c(665,665),adjustcolor(C$fit,.25),.8)
  tlabel(424,687,"Supported outputs",10.5,face="bold")
  pill(606,680,115,"Full set",C$fit)
  pill(734,680,127,"Partial set",C$fit)
  pill(874,680,170,"Abstention",C$muted)
}

workflow_selection <- function(d) {
  section(1100,145,470,285,"Choose operating cutoffs",C$operating_bg,C$operating,"3",
          "MODULE 3A / capacity    +    MODULE 3B / optional consequences")
  icon("capacity",1123,235,.78,C$operating,C$operating_bg)
  tlabel(1183,235,"K: alert capacity",12,face="bold")
  tlabel(1183,261,"For a defined workflow\nand period",10.5,C$muted)
  icon("balance",1372,235,.78,C$operating,C$operating_bg)
  tlabel(1431,235,"R: relative",12,face="bold")
  tlabel(1431,260,"consequences",10.5,C$muted)
  tlabel(1431,280,"Optional input",9.5,C$operating)
  # Qualitative ruler: locations express separate roles, not estimated cutoffs.
  line(c(1150,1520),c(344,344),C$muted,1.2)
  for(xx in seq(1150,1520,length.out=10)) line(c(xx,xx),c(341,347),C$muted,.8)
  dot(1220,344,8,C$low,"white",1)
  poly(c(1440,1448,1440,1432),c(335,344,353,344),C$operating)
  line(c(1234,1417),c(317,317),C$operating,1.2,arrow=TRUE)
  tlabel(1220,366,"Reference retained",10.5,C$low,"bold",just=c("center","top"))
  tlabel(1440,366,"Operating candidate",10.5,C$operating,"bold",just=c("center","top"))
  tlabel(1335,402,"Select under stated conditions",10.5,C$muted,just=c("center","top"))
}

workflow_evaluation <- function(d) {
  section(1100,460,470,270,"Evaluate independently",C$blue_bg,C$blue,"4",
          "Fixed curve and cutoffs / held-out or external data")
  # Genuine held-out reliability inset, not an illustrative performance curve.
  p <- chart(1159,573,126,103,c(0,1),c(0,1),c(0,1),c(0,1),
              xlabels=c("0","1"),ylabels=c("0","1"),grid=FALSE,labsize=9)
  reliability_marks(p,d$reliability,max_radius=5)
  tlabel(1222,550,"MIMIC held-out",9.5,C$blue,just=c("center","top"))
  tlabel(1222,707,"Predicted",9,C$muted,just=c("center","top"))
  tlabel(1120,624,"Observed",9,C$muted,just=c("center","center"),rot=90)
  items <- c("Action probability","Alert burden","Recorded-action yield","Outcome coverage")
  for(i in seq_along(items)) {
    yy <- 560+(i-1)*37
    checkmark(1325,yy+5,C$blue,.7)
    tlabel(1348,yy,items[i],10.5)
  }
}

workflow_use <- function(d) {
  section(30,787,1540,226,"Support local policy review",C$cyan_bg,C$fit,
          subtitle="Interpret the practice reference, examine tradeoffs, and decide what needs clinical evaluation.")
  icon("team",59,881,1.55,C$blue,C$cyan_bg)
  tlabel(106,987,"Clinical team",10.5,C$blue,"bold",just=c("center","top"))
  line(c(168,205),c(930,930),C$muted,1.5,arrow=TRUE)
  # Three clinical questions, each with a distinct small vector illustration.
  icon("hospital",229,894,1.0,C$blue,C$blue_bg)
  tlabel(308,893,"Understand local practice",14,face="bold")
  tlabel(308,924,"Where does recorded activity occur\nalong the clinical score?",11,C$muted)
  line(c(687,687),c(880,984),C$faint,1)
  icon("compare",712,894,1.0,C$fit,C$teal_bg)
  tlabel(791,893,"Compare proposed policies",14,face="bold")
  tlabel(791,924,"What changes in workload, action\nyield and outcome coverage?",11,C$muted)
  line(c(1172,1172),c(880,984),C$faint,1)
  icon("policy",1195,894,1.0,C$operating,C$operating_bg)
  tlabel(1274,893,"Plan evaluation",14,face="bold")
  tlabel(1274,924,"Review workflow fit\nand implementation needs.",11,C$muted)
}

workflow_parts <- list(
  inputs=list(draw=workflow_inputs,bounds=c(30,145,340,285)),
  checks=list(draw=workflow_checks,bounds=c(30,460,340,270)),
  references=list(draw=workflow_references,bounds=c(400,145,670,585)),
  selection=list(draw=workflow_selection,bounds=c(1100,145,470,285)),
  evaluation=list(draw=workflow_evaluation,bounds=c(1100,460,470,270)),
  clinical_use=list(draw=workflow_use,bounds=c(30,787,1540,226)))

draw_workflow <- function(d) {
  header("Behavioral references for clinical score cutoffs",
         "Learn from recorded practice. Compare operating choices. Evaluate their consequences.")
  for(part in workflow_parts) part$draw(d)
  # Connectors occupy dedicated gutters, never the text or plot areas.
  line(c(200,200),c(431,456),C$blue,1.6,arrow=TRUE)
  line(c(371,396),c(288,288),C$blue,1.6,arrow=TRUE)
  line(c(371,396),c(595,595),C$input,1.6,arrow=TRUE)
  line(c(1071,1096),c(288,288),C$operating,1.6,arrow=TRUE)
  line(c(1335,1335),c(431,456),C$operating,1.6,arrow=TRUE)
  line(c(1071,1096),c(595,595),C$blue,1.6,arrow=TRUE)
  line(c(736,736),c(731,783),C$fit,1.6,arrow=TRUE)
  line(c(1335,1335),c(731,783),C$blue,1.6,arrow=TRUE)
  tlabel(30,1034,"Recorded action probability describes practice; it is distinct from disease risk.",10.5,C$muted)
}
