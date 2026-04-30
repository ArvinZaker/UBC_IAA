{
  description = "PDX-metric development environment";

  inputs = {
    # Specify the Nixpkgs input
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
  };

  outputs = {
    self,
    nixpkgs,
  }: let
    # system = "x86_64-linux";
    system = builtins.currentSystem;
    pkgs = nixpkgs.legacyPackages.${system};
  in {
    devShells.${system} = {
      # x86_64-linux
      default = pkgs.mkShell {
        name = "impurePythonEnv";
        venvDir = "./.venv";

        # Add your package dependencies here
        buildInputs = with pkgs; [
          ########### Python pacakges ############
          python312Packages.colorcet
          python312Packages.datashader
          python312Packages.genanki
          python312Packages.matplotlib
          python312Packages.numpy
          python312Packages.pandas
          python312Packages.python
          python312Packages.requests
          python312Packages.rpy2
          python312Packages.scikit-image
          python312Packages.scikit-learn
          python312Packages.scipy
          python312Packages.seaborn
          python312Packages.statsmodels
          ########### R pacakges ############
          rPackages.AsioHeaders
          rPackages.Biobase
          rPackages.BiocManager
          rPackages.BumpyMatrix
          rPackages.ComplexHeatmap
          rPackages.Cubist
          rPackages.DEGreport
          rPackages.DESeq2
          rPackages.DOSE
          rPackages.DT
          rPackages.GEOquery
          rPackages.GSVA
          rPackages.GenomeInfoDb
          rPackages.Hmisc
          rPackages.ImportExport
          rPackages.LiblineaR
          rPackages.LogicReg
          rPackages.MASS
          rPackages.MetaGxBreast
          rPackages.MultiAssayExperiment
          rPackages.R6
          rPackages.RCircos
          rPackages.RColorBrewer
          rPackages.RRF
          rPackages.RSNNS
          rPackages.Rcpp
          rPackages.Rmisc
          rPackages.TCGAbiolinks
          rPackages.TTR
          rPackages.ada
          rPackages.alluvial
          rPackages.annotate
          rPackages.askpass
          rPackages.bazar
          rPackages.bigmemory
          rPackages.brnn
          rPackages.callr
          rPackages.caret
          rPackages.chromote
          rPackages.circlize
          rPackages.cli
          rPackages.clusterProfiler
          rPackages.concaveman
          rPackages.coop
          rPackages.covr
          rPackages.cowplot
          rPackages.curl
          rPackages.deepnet
          rPackages.dendextend
          rPackages.desc
          rPackages.devtools
          rPackages.digest
          rPackages.dineR
          rPackages.dplyr
          rPackages.e1071
          rPackages.earth
          rPackages.edgeR
          rPackages.elasticnet
          rPackages.ellipsis
          rPackages.enrichplot
          rPackages.evaluate
          rPackages.fansi
          rPackages.fastICA
          rPackages.ff
          rPackages.fgsea
          rPackages.fmsb
          rPackages.foghorn
          rPackages.foreach
          rPackages.frbs
          rPackages.fs
          rPackages.gbm
          rPackages.ggalluvial
          rPackages.ggforce
          rPackages.ggpattern
          rPackages.ggplot2
          rPackages.ggpubr
          rPackages.ggraph
          rPackages.ggrepel
          rPackages.ggridges
          rPackages.ggsci
          rPackages.gh
          rPackages.glmnet
          rPackages.gridExtra
          rPackages.gtable
          rPackages.h2o
          rPackages.hrbrthemes
          rPackages.htmltools
          rPackages.htmlwidgets
          rPackages.httpuv
          rPackages.httr
          rPackages.huge
          rPackages.igraph
          rPackages.importar
          rPackages.inTrees
          rPackages.itertools
          rPackages.kableExtra
          rPackages.keras
          rPackages.kernlab
          rPackages.kknn
          rPackages.knitr
          rPackages.languageserver
          rPackages.languageserversetup
          rPackages.lavaan
          rPackages.lifecycle
          rPackages.limma
          rPackages.lintr
          rPackages.logicFS
          rPackages.lsa
          rPackages.magicaxis
          rPackages.magrittr
          rPackages.markdown
          rPackages.mboost
          rPackages.mda
          rPackages.memoise
          rPackages.mgcv
          rPackages.miniUI
          rPackages.mlbench
          rPackages.monmlp
          rPackages.monomvn
          rPackages.msa
          rPackages.network
          rPackages.networkD3
          rPackages.neuralnet
          rPackages.nlme
          rPackages.nnet
          rPackages.openxlsx
          rPackages.ordinalForest
          rPackages.pROC
          rPackages.pander
          rPackages.parallel
          rPackages.party
          rPackages.paws_developer_tools
          rPackages.pegas
          rPackages.piano
          rPackages.pingr
          rPackages.pkgbuild
          rPackages.pkgdown
          rPackages.pkgload
          rPackages.plotly
          rPackages.pls
          rPackages.plyr
          rPackages.preprocessCore
          rPackages.profvis
          rPackages.progress
          rPackages.qrnn
          rPackages.quantregForest
          rPackages.rBayesianOptimization
          rPackages.rTorch
          rPackages.randomForest
          rPackages.ranger
          rPackages.rattle
          rPackages.rayshader
          rPackages.rcmdcheck
          rPackages.readr
          rPackages.readxl
          rPackages.rematch
          rPackages.rematch2
          rPackages.remotes
          rPackages.renv
          rPackages.rhub
          rPackages.rio
          rPackages.rlang
          rPackages.rmarkdown
          rPackages.roxygen2
          rPackages.rpart
          rPackages.rpart_plot
          rPackages.rpart_utils
          rPackages.rqdatatable
          rPackages.rstatix
          rPackages.rstudioapi
          rPackages.rversions
          rPackages.sass
          rPackages.scales
          rPackages.seqinr
          rPackages.sesame
          rPackages.sesameData
          rPackages.sessioninfo
          rPackages.shiny
          rPackages.shinyWidgets
          rPackages.shinytest2
          rPackages.smooth
          rPackages.smoothie
          rPackages.sna
          rPackages.spelling
          rPackages.stringi
          rPackages.stringr
          rPackages.styler
          rPackages.superpc
          rPackages.survival
          rPackages.survminer
          rPackages.sva
          rPackages.sys
          rPackages.tensorflow
          rPackages.testthat
          rPackages.threejs
          rPackages.tibble
          rPackages.tidyquant
          rPackages.tidyr
          rPackages.tidyverse
          rPackages.tinytex
          rPackages.torch
          rPackages.torchdatasets
          rPackages.torchopt
          rPackages.torchvision
          rPackages.torchvisionlib
          rPackages.umap
          rPackages.urlchecker
          rPackages.usethis
          rPackages.utf8
          rPackages.verification
          rPackages.vip
          rPackages.viridis
          rPackages.visNetwork
          rPackages.waldo
          rPackages.websocket
          rPackages.whisker
          rPackages.withr
          rPackages.writexl
          rPackages.xfun
          rPackages.xgboost
          rPackages.xopen
          rPackages.xtable
          rPackages.yaml
          rPackages.yardstick
          rPackages.zip
          ########### System pacakges ############
          taglib
          liblinear
          openssl
          git
          libxml2
          libxslt
          libzip
          zlib
          stdenv.cc.cc.lib
          bash
          wget
          zlib
        ];

        LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib";

        # Run this command, only after creating the virtual environment
        postVenvCreation = ''
          unset SOURCE_DATE_EPOCH
          # uncomment if you have packages not in nixos repository
          # pip install -r requirements.txt
          LD_LIBRARY_PATH=${pkgs.stdenv.cc.cc.lib}/lib/
        '';

        # Now we can execute any commands within the virtual environment.
        # This is optional and can be left out to run pip manually.
        postShellHook = ''
          # allow pip to install wheels
          unset SOURCE_DATE_EPOCH
          # fixes libstdc++ issues and libgl.so issues
          LD_LIBRARY_PATH=${pkgs.stdenv.cc.cc.lib}/lib/
        '';
      };
    };
  };
}
