# Geometry manifest: native-unit bounds are exactly those sent to R/grid.
# Scale is 100 native units/inch = 0.72 PDF points/native unit.
panel <- function(id,b) list(id=id,bbox_pt=unname(c(b[1],1070-b[2]-b[4],b[1]+b[3],1070-b[2])*.72))
exempt <- function(ids,why) list(panels=ids,checks=c("row","column"),reason=why)
save_layout <- function(name,panels,rows=list(),columns=list(),exemptions=list()) {
  jsonlite::write_json(list(schema_version=1,backend="R/grid",figure=list(width_pt=1152,height_pt=770.4),
                      panels=panels,row_groups=rows,column_groups=columns,exemptions=exemptions),
                      file.path(qa,paste0(name,"-layout.json")),auto_unbox=TRUE,pretty=TRUE)
}
save_layout("workflow",lapply(names(workflow_parts),function(n) panel(n,workflow_parts[[n]]$bounds)),
            rows=list(c("inputs","selection"),c("checks","evaluation")),
            columns=list(c("inputs","checks"),c("selection","evaluation")),
            exemptions=list(exempt("references","Central empirical illustration spans both schematic rows."),
                            exempt("clinical_use","Clinical-use band spans the full figure width.")))
save_layout("synthetic-example",
            list(panel("learning",c(135,306,584,201)),panel("capacity",c(925,306,584,201)),
                 panel("evaluation",synthetic_parts$evaluation$bounds)),
            rows=list(c("learning","capacity")),
            exemptions=list(exempt("evaluation","Evaluation comparison spans both learning panels.")))
save_layout("clinical-action",
            list(panel("curve",c(139,315,610,265)),panel("counts",c(139,618,610,74)),
                 panel("reliability",c(972,307,440,360)),panel("context",clinical_parts$context$bounds)),
            columns=list(c("curve","counts")),
            exemptions=list(exempt("reliability","Reliability plot spans the learning curve and support strip."),
                            exempt("context","Context band spans the full figure width.")))
