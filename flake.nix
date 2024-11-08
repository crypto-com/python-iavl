{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/release-24.05";
    flake-utils.url = "github:numtide/flake-utils";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.flake-utils.follows = "flake-utils";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      poetry2nix,
    }:
    let
      overrides =
        {
          lib,
          poetry2nix,
          rocksdb,
          leveldb,
        }:
        poetry2nix.overrides.withDefaults (
          lib.composeManyExtensions [
            (
              self: super:
              let
                buildSystems = {
                  rocksdb = [
                    "setuptools"
                    "cython"
                    "pkgconfig"
                  ];
                  cprotobuf = [ "setuptools" ];
                };
              in
              lib.mapAttrs (
                attr: systems:
                super.${attr}.overridePythonAttrs (old: {
                  nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ map (a: self.${a}) systems;
                })
              ) buildSystems
            )
            (self: super: {
              rocksdb = super.rocksdb.overridePythonAttrs (old: {
                buildInputs = (old.buildInputs or [ ]) ++ [ rocksdb ];
              });
              plyvel = super.plyvel.overridePythonAttrs (old: {
                buildInputs = (old.buildInputs or [ ]) ++ [ leveldb ];
              });
            })
          ]
        );

      iavl-env =
        {
          poetry2nix,
          callPackage,
          groups ? [ "rocksdb" ],
        }:
        poetry2nix.mkPoetryEnv {
          projectDir = ./.;
          overrides = callPackage overrides { };
          inherit groups;
        };
      iavl-cli =
        {
          poetry2nix,
          callPackage,
          groups ? [ "rocksdb" ],
        }:
        poetry2nix.mkPoetryApplication {
          projectDir = ./.;
          overrides = callPackage overrides { };
          inherit groups;
        };
    in
    (flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = self.overlays.default;
          config = { };
        };
      in
      rec {
        packages = {
          iavl-env = pkgs.callPackage iavl-env { };
          iavl-env-leveldb = pkgs.callPackage iavl-env { groups = [ "leveldb" ]; };
          iavl-cli = pkgs.callPackage iavl-cli { };
          iavl-cli-leveldb = pkgs.callPackage iavl-cli { groups = [ "leveldb" ]; };
        };
        defaultPackage = packages.iavl-cli;
        apps = {
          default = {
            type = "app";
            program = "${packages.iavl-cli}/bin/iavl";
          };
          iavl-cli-leveldb = {
            type = "app";
            program = "${packages.iavl-cli-leveldb}/bin/iavl";
          };
        };
        devShells = {
          default = pkgs.mkShell {
            buildInputs = [ packages.iavl-env ];
          };
          leveldb = pkgs.mkShell {
            buildInputs = [ packages.iavl-env-leveldb ];
          };
        };
      }
    ))
    // {
      overlays.default = [
        poetry2nix.overlays.default
        (final: prev: {
          rocksdb = final.callPackage ./rocksdb.nix { };
        })
      ];
    };
}
