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
          python312Packages.pillow
          python312Packages.genanki
          python312Packages.reportlab
          python312Packages.matplotlib
          python312Packages.numpy
          python312Packages.pandas
          python312Packages.python
          python312Packages.scikit-image
          python312Packages.scikit-learn
          python312Packages.scipy
          python312Packages.seaborn
          python312Packages.statsmodels
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
