# Shared vector drawing vocabulary for the ActionRef documentation figures.
# Coordinate units are 1/100 inch. All artwork and plots are drawn in R/grid.
library(grid)

palette <- jsonlite::fromJSON("configs/figure_palette.json")
C <- list(ink="#183E50", muted="#536D7A", faint="#D9E4E9",
          observed="#667D8B", fit=palette$Low, low=palette$Low, mid=palette$Mid,
          high=palette$High, operating=palette[["Operating candidate"]], blue=palette$Mid,
          teal_bg="#EDF7F4", blue_bg="#EEF4FB", purple_bg="#F4F0F8",
          amber_bg="#FFF5E7", operating_bg="#F4F0F8", input="#536D7A", input_bg="#F2F5F6",
          cyan_bg="#EEF8FA", white="#FFFFFF")

apply_figure_style <- function(preferred_family="Arial") {
  # Explicit role-mapped typography; SVG retains text, PDF embeds the fonts.
  available <- unique(systemfonts::system_fonts()$family)
  candidates <- unique(c(preferred_family,"Liberation Sans","DejaVu Sans"))
  family <- candidates[candidates %in% available][1]
  if(is.na(family)) stop("Install Arial, Liberation Sans or DejaVu Sans before drawing.")
  options(actionref.font=family, actionref.dpi=300)
  invisible(list(title=26, panel=16, body=12, axis=11, note=10, floor=9))
}

tlabel <- function(x, y, label, size=12, color=C$ink, face="plain",
                   just=c("left", "top"), rot=0) {
  grid.text(label, x=unit(x,"native"), y=unit(y,"native"), just=just, rot=rot,
            gp=gpar(fontfamily=getOption("actionref.font"), fontsize=size,
                    col=color, fontface=face, lineheight=1.18))
}

box <- function(x,y,w,h,fill="white",color=NA,lwd=.9,r=0,lty=1) {
  args <- list(x=unit(x+w/2,"native"), y=unit(y+h/2,"native"),
               width=unit(abs(convertWidth(unit(w,"native"),"in",valueOnly=TRUE)),"in"),
               height=unit(abs(convertHeight(unit(h,"native"),"in",valueOnly=TRUE)),"in"),
               gp=gpar(fill=fill,col=color,lwd=lwd,lty=lty))
  # Lengths must be positive: the native coordinate system has a downward y axis.
  radius <- unit(abs(convertWidth(unit(r,"native"),"in",valueOnly=TRUE)),"in")
  if(r>0) do.call(grid.roundrect,c(args,list(r=radius)))
  else do.call(grid.rect,args)
}

line <- function(x,y,color=C$muted,lwd=1,lty=1,arrow=FALSE) {
  grid.lines(x=unit(x,"native"),y=unit(y,"native"),
             gp=gpar(col=color,lwd=lwd,lty=lty,lineend="round",linejoin="round"),
             arrow=if(arrow) grid::arrow(length=unit(6,"pt"),type="closed") else NULL)
}

dot <- function(x,y,r=4,fill=C$fit,color=fill,lwd=1) {
  grid.circle(x=unit(x,"native"),y=unit(y,"native"),r=unit(r,"native"),
              gp=gpar(fill=fill,col=color,lwd=lwd))
}

poly <- function(x,y,fill,color=NA,lwd=1) {
  grid.polygon(x=unit(x,"native"),y=unit(y,"native"),
               gp=gpar(fill=fill,col=color,lwd=lwd,linejoin="round"))
}

checkmark <- function(x,y,color=C$fit,s=1) {
  line(x+c(0,5,14)*s,y+c(5,10,-3)*s,color,1.7)
}

section <- function(x,y,w,h,title,fill,accent,tag=NULL,subtitle=NULL) {
  box(x,y,w,h,fill=fill,color=adjustcolor(accent,alpha.f=.38),r=9)
  box(x+1,y+16,4,30,fill=accent)
  offset <- if(is.null(tag)) 22 else 54
  if(!is.null(tag)) {
    dot(x+27,y+31,14,fill=accent)
    tlabel(x+27,y+30,tag,12,"white","bold",just=c("center","center"))
  }
  tlabel(x+offset,y+20,title,16,face="bold")
  if(!is.null(subtitle)) tlabel(x+22,y+58,subtitle,10.5,C$muted)
}

pill <- function(x,y,w,label,color,fill="white",size=10.5,h=29) {
  box(x,y,w,h,fill=fill,color=adjustcolor(color,.35),r=h/2)
  tlabel(x+w/2,y+h/2,label,size,color,"bold",just=c("center","center"))
}

header <- function(title,subtitle,kicker="ACTIONREF") {
  # Small original mark: a step-shaped action curve inside an open coordinate frame.
  line(c(31,31,80),c(77,32,32),C$faint,1.2)
  line(c(36,47,47,62,62,78),c(72,72,58,58,41,41),C$fit,3)
  dot(78,41,3,C$fit)
  tlabel(100,27,kicker,10,C$fit,"bold")
  tlabel(100,52,title,26,face="bold")
  tlabel(100,99,subtitle,12,C$muted)
}

# Original clinical / workflow line illustrations. Each is a 60 x 60 native-unit icon.
icon <- function(kind,x,y,s=1,color=C$blue,fill=C$blue_bg) {
  pushViewport(viewport(x=unit(x,"native"),y=unit(y,"native"),
                        width=unit(.6*s,"in"),height=unit(.6*s,"in"),
                        just=c("left","top"),xscale=c(0,60),yscale=c(60,0)))
  if(kind=="score") {
    box(6,5,46,49,"white",color,1.4,5)
    line(c(16,43),c(17,17),color,1.4)
    for(i in 0:2) {
      box(16,27+7*i,27,4,fill=C$faint,r=1)
      box(16,27+7*i,c(12,21,27)[i+1],4,fill=color,r=1)
    }
  } else if(kind=="action") {
    box(8,6,37,45,"white",color,1.4,4)
    box(19,2,16,9,fill,color,1.2,2)
    checkmark(16,23,color,.65); line(c(28,37),c(25,25),color)
    checkmark(16,34,color,.65); line(c(28,37),c(36,36),color)
    dot(46,45,12,"white",color,1.4)
    line(c(46,46,51),c(37,45,48),color,1.2)
  } else if(kind=="outcome") {
    dot(29,28,23,fill,color,1.2); dot(29,28,14,"white",color,1)
    line(c(9,22,27,33,39,50),c(31,31,20,39,27,27),color,1.6)
  } else if(kind=="hospital") {
    box(5,21,49,34,"white",color,1.4,2)
    box(19,6,21,49,fill,color,1.4,2)
    box(24,14,11,3,color); box(28,10,3,11,color)
    box(26,40,8,15,"white",color)
    for(xx in c(10,44)) for(yy in c(29,40)) box(xx,yy,5,5,fill,color,.8)
  } else if(kind=="capacity") {
    box(5,10,50,42,"white",color,1.4,4)
    line(c(5,55),c(23,23),color,1.1)
    for(xx in c(16,43)) line(c(xx,xx),c(5,16),color,2)
    for(i in 0:2) for(j in 0:1)
      box(13+i*13,29+j*11,7,6,if(i+j<2) color else fill,color,.8,1)
  } else if(kind=="balance") {
    line(c(30,30),c(8,51),color,1.6); line(c(17,43),c(52,52),color,1.6)
    line(c(10,50),c(16,16),color,1.6); dot(30,16,3,color)
    for(cx in c(13,47)) {
      line(c(cx-8,cx,cx+8),c(36,18,36),color,1)
      poly(c(cx-9,cx+9,cx+5,cx-5),c(36,36,41,41),fill,color,1.3)
    }
  } else if(kind=="team") {
    for(cx in c(12,47)) {
      dot(cx,13,7,fill,color,1.2)
      box(cx-10,24,20,27,"white",color,1.2,7)
    }
    dot(30,13,9,fill,color,1.4)
    poly(c(17,22,38,43,43,17),c(54,29,29,54,57,57),"white",color,1.4)
    line(c(24,30,36),c(30,40,30),color,1)
    line(c(30,30),c(40,53),color,1)
    dot(39,43,3,fill,color,1)
  } else if(kind=="compare") {
    box(4,8,52,44,"white",color,1.3,4)
    line(c(12,12,48),c(17,44,44),color,1)
    for(i in 0:2) box(18+i*10,44-c(15,23,30)[i+1],6,c(15,23,30)[i+1],
                       c(C$low,C$high,C$operating)[i+1],r=1)
  } else if(kind=="policy") {
    box(8,3,38,51,"white",color,1.3,4)
    box(18,1,18,8,fill,color,1,2)
    for(i in 0:2) { checkmark(15,21+i*11,color,.6); line(c(28,38),c(23+i*11,23+i*11),color) }
  }
  popViewport()
}

chart <- function(x,y,w,h,xlim,ylim,xticks,yticks,xlabel=NULL,ylabel=NULL,
                  xlabels=xticks,ylabels=yticks,grid=TRUE,labsize=10,
                  xlab_offset=37,ylab_offset=59) {
  X <- function(a) x+(a-xlim[1])/diff(xlim)*w
  Y <- function(a) y+h-(a-ylim[1])/diff(ylim)*h
  if(grid) for(v in yticks) line(c(x,x+w),rep(Y(v),2),"#DEE8ED",.6)
  line(c(x,x,x+w),c(y,y+h,y+h),C$muted,.9)
  for(i in seq_along(xticks)) {
    line(rep(X(xticks[i]),2),c(y+h,y+h+5),C$muted,.9)
    tlabel(X(xticks[i]),y+h+12,as.character(xlabels[i]),labsize,C$muted,just=c("center","top"))
  }
  for(i in seq_along(yticks)) {
    line(c(x-5,x),rep(Y(yticks[i]),2),C$muted,.9)
    tlabel(x-11,Y(yticks[i]),as.character(ylabels[i]),labsize,C$muted,just=c("right","center"))
  }
  if(!is.null(xlabel)) tlabel(x+w/2,y+h+xlab_offset,xlabel,11,C$ink,just=c("center","top"))
  if(!is.null(ylabel)) tlabel(x-ylab_offset,y+h/2,ylabel,11,C$ink,just=c("center","center"),rot=90)
  list(X=X,Y=Y,x=x,y=y,w=w,h=h)
}

curve_marks <- function(p,df,observed=TRUE,point_r=4,lwd=2.1) {
  line(p$X(df$score),p$Y(df$isotonic_rate),C$fit,lwd)
  if(observed) for(i in seq_len(nrow(df)))
    dot(p$X(df$score[i]),p$Y(df$observed_rate[i]),point_r,"white",C$observed,1.1)
}

reliability_marks <- function(p,df,max_radius=14) {
  line(p$X(c(0,1)),p$Y(c(0,1)),"#AABBC6",1.1,2)
  for(i in seq_len(nrow(df)))
    dot(p$X(df$predicted[i]),p$Y(df$observed[i]),
        max_radius*sqrt(df$N[i]/max(df$N)),adjustcolor(C$fit,.83),"white",.8)
}

legend_curve <- function(x,y) {
  dot(x,y+6,3.5,"white",C$observed,1)
  tlabel(x+11,y,"Observed bins",10,C$muted)
  line(c(x+135,x+162),c(y+6,y+6),C$fit,2)
  tlabel(x+171,y,"Fitted action curve",10,C$muted)
}
