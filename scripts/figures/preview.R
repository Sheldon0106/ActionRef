# Screen-only QA previews. Never used as the published figure exports (300 dpi).
for(name in names(figs))
  render(figs[[name]]$draw,c(0,0,1600,1070),
          file.path(qa,paste0(name,"-preview.png")),"png",dpi=100)
