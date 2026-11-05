#!/usr/bin/env Rscript
# Software workflow and synthetic tutorial illustrations, drawn in R/grid.
# Run from the repository root. Use --workflow-only to redraw just the schematic.
args <- commandArgs(trailingOnly=FALSE)
this_file <- sub("^--file=", "", args[grepl("^--file=", args)])
root <- normalizePath(file.path(dirname(this_file),".."),winslash="/",mustWork=TRUE)
setwd(root)
for(pkg in c("jsonlite","svglite","ragg"))
  if(!requireNamespace(pkg,quietly=TRUE)) stop("Missing R dependency: ",pkg)
source("scripts/figures/style.R",encoding="UTF-8")
source("scripts/figures/workflow.R",encoding="UTF-8")
source("scripts/figures/synthetic.R",encoding="UTF-8")
apply_figure_style(preferred_family="Arial")
csv <- function(name) read.csv(file.path("docs/assets/data",name),check.names=FALSE)
d <- list(synthetic_curve=csv("synthetic_learning_curve.csv"),
          alert_curve=csv("synthetic_alert_curve.csv"),
          synthetic_heldout=csv("synthetic_heldout.csv"))
stopifnot(d$alert_curve$alert_count[d$alert_curve$threshold==81]==1643,
          min(d$alert_curve$threshold[d$alert_curve$alert_count<=1680])==81,
          identical(as.numeric(d$synthetic_heldout$evaluated_threshold[1:3]),c(45,45,60)),
          all(d$synthetic_heldout$policy_N==3600))
render <- function(draw,bounds,path,ext) {
  w <- bounds[3]/100; h <- bounds[4]/100
  if(ext=="svg") svglite::svglite(path,width=w,height=h,bg="white",
                                    system_fonts=list(sans=getOption("actionref.font")))
  else if(ext=="pdf") grDevices::cairo_pdf(path,width=w,height=h,
                                         family=getOption("actionref.font"),bg="white")
  else ragg::agg_png(path,width=w,height=h,units="in",res=300,background="white")
  on.exit(dev.off(),add=TRUE)
  grid.newpage()
  pushViewport(viewport(xscale=c(bounds[1],bounds[1]+bounds[3]),
                        yscale=c(bounds[2]+bounds[4],bounds[2]),clip="on"))
  draw(d)
  popViewport()
}
figs <- list(workflow=list(draw=draw_workflow,bounds=c(0,0,1000,430)),
             `synthetic-example`=list(draw=draw_synthetic,bounds=c(0,0,1600,1070)))
if("--workflow-only" %in% commandArgs(trailingOnly=TRUE)) figs <- figs["workflow"]
for(name in names(figs)) {
  f <- figs[[name]]
  for(ext in c("svg","pdf","png"))
    render(f$draw,f$bounds,file.path("docs/assets/figures",paste0(name,".",ext)),ext)
  message("Exported ",name)
}
