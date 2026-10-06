#!/usr/bin/env Rscript
# Rebuild all documentation figures entirely in R. Run from the repository root:
#   Rscript scripts/build_figures.R
# Optional: --preview also writes 100-dpi previews to ignored output/figures/.
# Dependencies: grid (base R), jsonlite, svglite, ragg.
# Sources and figure roles: docs/figures.md. No clinical models are refitted here.

args <- commandArgs(trailingOnly=FALSE)
this_file <- sub("^--file=", "", args[grepl("^--file=", args)])
root <- normalizePath(file.path(dirname(this_file),".."),winslash="/",mustWork=TRUE)
setwd(root)
for(pkg in c("jsonlite","svglite","ragg"))
  if(!requireNamespace(pkg,quietly=TRUE)) stop("Missing R dependency: ",pkg)
source("scripts/figures/style.R",encoding="UTF-8")
source("scripts/figures/workflow.R",encoding="UTF-8")
source("scripts/figures/synthetic.R",encoding="UTF-8")
source("scripts/figures/clinical.R",encoding="UTF-8")
apply_figure_style(preferred_family="Arial")

data_dir <- "docs/assets/data"
csv <- function(name) read.csv(file.path(data_dir,name),check.names=FALSE)
js <- function(name) jsonlite::fromJSON(file.path(data_dir,name))
metrics <- js("sepsis_action_points.json")
d <- list(clinical=csv("sepsis_learning_curve.csv"),
          reliability=subset(js("sepsis_action_reliability.json"),N>0),
          metrics=subset(metrics,prediction=="continuous_interpolation"),
          synthetic_curve=csv("synthetic_learning_curve.csv"),
          alert_curve=csv("synthetic_alert_curve.csv"),
          synthetic_heldout=csv("synthetic_heldout.csv"))
# Assertions tie visual annotations to saved evidence and fail on stale data.
stopifnot(nrow(d$clinical)==26,sum(d$clinical$count)==294659,
          sum(d$reliability$N)==126332,d$metrics$N==126332,
          all(c(27,36,51) %in% d$clinical$score),
          d$alert_curve$alert_count[d$alert_curve$threshold==81]==1643,
          min(d$alert_curve$threshold[d$alert_curve$alert_count<=1680])==81,
          identical(as.numeric(d$synthetic_heldout$evaluated_threshold[1:3]),c(45,45,60)),
          all(d$synthetic_heldout$policy_N==3600))

out <- "docs/assets/figures"
qa <- "output/figures"
dir.create(out,recursive=TRUE,showWarnings=FALSE)
dir.create(qa,recursive=TRUE,showWarnings=FALSE)

render <- function(draw,bounds,path,ext,dpi=300) {
  w <- bounds[3]/100; h <- bounds[4]/100
  if(ext=="svg") svglite::svglite(path,width=w,height=h,bg="white",
                                    system_fonts=list(sans=getOption("actionref.font")))
  else if(ext=="pdf") grDevices::cairo_pdf(path,width=w,height=h,family=getOption("actionref.font"),bg="white")
  else ragg::agg_png(path,width=w,height=h,units="in",res=dpi,background="white")
  on.exit(dev.off(),add=TRUE)
  grid.newpage()
  pushViewport(viewport(xscale=c(bounds[1],bounds[1]+bounds[3]),
                        yscale=c(bounds[2]+bounds[4],bounds[2]),clip="on"))
  draw(d)
  popViewport()
}

figs <- list(workflow=list(draw=draw_workflow,parts=workflow_parts),
             `synthetic-example`=list(draw=draw_synthetic,parts=synthetic_parts),
             `clinical-action`=list(draw=draw_clinical,parts=clinical_parts))
for(name in names(figs)) {
  f <- figs[[name]]
  # Each scientific region is also exported separately at its final physical size.
  part_dir <- file.path(qa,name)
  dir.create(part_dir,recursive=TRUE,showWarnings=FALSE)
  for(part_name in names(f$parts)) {
    part <- f$parts[[part_name]]
    for(ext in c("svg","pdf","png"))
      render(part$draw,part$bounds,file.path(part_dir,paste0(part_name,".",ext)),ext)
  }
  for(ext in c("svg","pdf","png"))
    render(f$draw,c(0,0,1600,1070),file.path(out,paste0(name,".",ext)),ext)
  message("Exported ",name," (R / SVG, PDF, 300-dpi PNG + separate panels)")
}
source("scripts/figures/layout.R",encoding="UTF-8")
if("--preview" %in% commandArgs(trailingOnly=TRUE))
  source("scripts/figures/preview.R",encoding="UTF-8")
writeLines(capture.output(sessionInfo()),file.path(qa,"R-session-info.txt"))
