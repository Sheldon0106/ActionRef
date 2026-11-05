# Software workflow schematic; no clinical result inputs.
draw_workflow <- function(d) {
  tlabel(20,24,"ActionRef workflow",24,face="bold")
  tlabel(20,69,"Practice-based references and explicit operating comparisons",12,C$muted)
  titles <- c("Prepare inputs","Estimate references","Compare candidates","Evaluate separately")
  rows <- list(
    c("Existing clinical score","Recorded action + window","Outcome, when available"),
    c("Supported score bins","Monotone action curve","Supported Low / Mid / High"),
    c("Workload limit K","Optional ratio R","Reference values retained"),
    c("Fixed thresholds","Alerts and action yield","Outcome coverage"))
  colors <- c(C$input,C$low,C$operating,C$mid)
  fills <- c(C$input_bg,C$blue_bg,C$operating_bg,C$teal_bg)
  for(i in 1:4) {
    x <- 20+(i-1)*250
    box(x,120,210,220,fills[i],adjustcolor(colors[i],.45),r=7)
    pill(x+15,137,27,as.character(i),colors[i],size=11,h=27)
    tlabel(x+15,183,titles[i],13,colors[i],"bold")
    for(j in 1:3) tlabel(x+15,221+(j-1)*31,rows[[i]][j],10.5)
    if(i<4) line(c(x+219,x+241),c(232,232),C$muted,1.2,arrow=TRUE)
  }
  tlabel(20,376,"Estimate on derivation data; evaluate fixed choices on separate data.",12,C$muted)
}
